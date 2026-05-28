import base64
from datetime import timedelta, datetime
import json
import os
from pathlib import Path
import re
import time
import traceback
from typing import List
from fastapi import APIRouter, BackgroundTasks, Header, status, Request, Response , HTTPException, Query
from app.models.interface.dataset_interface import *
import requests
import logging
import httpx
import asyncio
import pyarrow as pa
import pyarrow.parquet as pq
import xml.etree.ElementTree as ET

from app.models.interface.pdc_chain_interface import PdcChainHeaders, PdcChainRequest, PdcChainResponse
from app.models.interface.pdc_interface import PdcContract, PdcEcosystem, PdcParticipant, PdcServiceOffering, PdcContractBilateral, PdcDataResource
from app.models.interface.pdc_data_exchange_interface import PdcDataExchangeHeaders
from app.models.interface.workflow_interface import IProject
from app.routes.workflows import import_and_execute_workflow
from app.services.dataset_service import DatasetService
from app.services.pdc_service import PdcService
from typing import Annotated, List, Optional
from collections import defaultdict
from app.services.user_service import UserService
from app.services.workflow_service import WorkflowService
from app.utils.utils import decodeDictionary
from app.utils.auth_utils import authenticate_m2m_credentials, AuthenticatedUser
from app.middleware.auth import CurrentUser
from app.config.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ptx", tags=["prometheus-x"])

logging.basicConfig(filename = 'app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

dataset_service = DatasetService()
workflow_service = WorkflowService()
user_service = UserService()
pdc_service = PdcService(timeout=settings.vision_api_timeout_seconds)

_config_cache = {}
_config_timestamp = {}


def _resolve_timeout(timeout_seconds: Optional[int]) -> int:
    """Resolve effective timeout with a hard minimum of 30s."""
    resolved = timeout_seconds if timeout_seconds is not None else settings.vision_api_timeout_seconds
    return max(30, int(resolved))



@router.get("/{id}")
async def get_ptx_data(
    id: str,
    current_user: CurrentUser,
    timeout_seconds: Annotated[Optional[int], Query(ge=30, description="Visions API timeout in seconds")] = None,
):
    timeout = _resolve_timeout(timeout_seconds)
    connection = await dataset_service.get_dataset(id, current_user)
    config = await get_private_configuration(connection)
    catalog_uri = config.get("catalogUri")
    pdc_data = await pdc_get_request(connection, "/", timeout_seconds=timeout)

    async def fetch_catalog_item(client: httpx.AsyncClient, content: dict):
        response = await client.get(content["@id"], timeout=timeout)
        res = response.json()
        participant_id = None
        owner_name = "Unknown"
        owner_logo = None

        if content["@type"] in ["ptx:serviceofferings", "ptx:softwareresources"]:
            participant_id = res.get("providedBy")
        elif content["@type"] == "ptx:dataresources":
            participant_id = res.get("producedBy")

        if participant_id and catalog_uri:
            try:
                participant_response = await client.get(f"{catalog_uri}participants/{participant_id}", timeout=timeout)
                participant = participant_response.json()
                owner_name = participant.get("legalName")
                owner_logo = participant.get("logo")
            except Exception:
                pass

        return {
            "type": content["@type"],
            "name": res["name"],
            "owner": {
                "name": owner_name,
                "logo": owner_logo
            }
        }

    catalog = []
    if "content" in pdc_data and "ptx:catalog" in pdc_data["content"]:
        async with httpx.AsyncClient(timeout=timeout) as client:
            tasks = [fetch_catalog_item(client, content) 
                    for content in pdc_data["content"]["ptx:catalog"]]
            catalog = await asyncio.gather(*tasks)

    return {"catalog": catalog}

@router.put("/dataResources/{connection_id}")
async def update_data_resource(
    connection_id: str,
    request: Request,
    current_user: CurrentUser,
    timeout_seconds: Annotated[Optional[int], Query(ge=30, description="Visions API timeout in seconds")] = None,
):
    """
    Update a data resource in a PDC connection.
    """
    try:
        timeout = _resolve_timeout(timeout_seconds)
        connection = await dataset_service.get_dataset(connection_id, current_user)
        if (not isinstance (connection,PTXDataset)):
            raise HTTPException(status_code=400, detail="Invalid connection type. Expected PTXDataset.")

        config = await get_private_configuration(connection)
        
        body = await request.json()
        dataResourcesId = body.get("dataResourceId")
        newUrl = body.get("newUrl")

        headers = {
            'Authorization': f'Bearer {connection.token}',
            'Content-Type': 'application/json'
        }

        dataResource_url = f"{config.get('catalogUri')}dataresources/{dataResourcesId}"
        dataResources = pdc_service.fetch_dataResource(dataResource_url, headers, timeout=timeout)
        representation = dataResources.representation
        representation.url = newUrl

        payload = representation.model_dump_json()

        api_url = f"{config.get('catalogUri')}datarepresentations/{representation.id}"
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.put(api_url, data=payload, headers=headers, timeout=timeout)
            if response.status_code == 200:
                return {
                    "response": response.json()
                }
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Url update failed: {response.text}"
            )
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/dataResources/{connection_id}")
async def get_data_resources(
    connection_id: str,
    current_user: CurrentUser,
    timeout_seconds: Annotated[Optional[int], Query(ge=30, description="Visions API timeout in seconds")] = None,
):
    """
    Get data resources from a PDC connection.
    """
    try:
        timeout = _resolve_timeout(timeout_seconds)
        connection = await dataset_service.get_dataset(connection_id, current_user)
        pdc_data = await pdc_get_request(connection, "/", timeout_seconds=timeout)
        
        data_resources = []
        if "content" in pdc_data and "ptx:catalog" in pdc_data["content"]:
            for content in pdc_data["content"]["ptx:catalog"]:
                if content["@type"] == "ptx:dataresources":
                    res = requests.get(content["@id"], timeout=timeout).json()
                    data = PdcDataResource.model_validate(res)
                    data_resources.append(data)
        
        return {"dataResources": data_resources}
    
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/executeChainService", status_code=status.HTTP_200_OK)
async def executeChainService(
    background_tasks: BackgroundTasks,
    payload: PdcChainRequest,
    request: Request,
    x_ptx_service_chain_id: Annotated[str | None, Header(alias="x-ptx-service-chain-id")] = None,
    x_ptx_target_id: Annotated[str | None, Header(alias="x-ptx-target-id")] = None,
    Authorization: Annotated[str, Header()] = None,
):  

    all_users = await user_service.get_all_users()
    authenticated_users: List[AuthenticatedUser] = await authenticate_m2m_credentials(request.headers, all_users)
    if not authenticated_users:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No valid credentials found in headers"
        )

    requestjson = await request.json()
    service_chain_id = re.search(r"@supervisor:([a-f0-9]{24})", x_ptx_service_chain_id).group(1)
    pdc_service.store_servicechain_data(
        service_chain_id=service_chain_id,
        data=payload.data
    )
    pdc_headers = PdcChainHeaders(
        Authorization=Authorization if Authorization is not None else "",
        x_ptx_service_chain_id=x_ptx_service_chain_id,
        x_ptx_target_id=x_ptx_target_id,
    )
    logger.info(f"requestjson {pdc_service.get_servicechain_data(service_chain_id)}...")

    dataset_service.pdcChainData = payload.data
    print(requestjson)
    dataset_service.pdcChainHeaders = pdc_headers
    workflow_id = payload.params["workflowId"] if "workflowId" in payload.params else "e492c405-300f-4bf3-967e-c3db614e18f6"
    workflow_data = await workflow_service.get_workflow(workflow_id)
    print(type(workflow_data))
    
    # Only execute workflow for users who possess (own or have access to) the workflow
    executed_users = []
    for auth_user_data in authenticated_users:
        user_obj = auth_user_data['user']
        # Check if user owns or has access to the workflow
        if hasattr(user_obj, 'owned_workflows') and workflow_id in getattr(user_obj, 'owned_workflows', []):
            background_tasks.add_task(import_and_execute_workflow, workflow_data, current_user=user_obj)
            executed_users.append(user_obj.username)
        elif hasattr(user_obj, 'accessible_workflows') and workflow_id in getattr(user_obj, 'accessible_workflows', []):
            background_tasks.add_task(import_and_execute_workflow, workflow_data, current_user=user_obj)
            executed_users.append(user_obj.username)

    logger.info(f"Workflow {workflow_id} executed for users: {executed_users}")
    return True

@router.get("/serviceChain/data/{service_chain_id}")
async def get_servicechain_data(service_chain_id: str):
    """retrieve service chain data by its ID"""
    return pdc_service.get_servicechain_data(service_chain_id)


@router.delete("/serviceChain/data/remove/{service_chain_id}")
async def delete_service_chain_data(service_chain_id: str):
    """delete service chain data  in pdc_service"""
    status =  pdc_service.delete_servicechain_data(service_chain_id)
    if status:
        logger.info(f"{service_chain_id} deleted in pdc service")
        return True
    return False

@router.post("/pdcInput")
async def read_input(request: Request, response: Response, headers: Annotated[PdcDataExchangeHeaders, Header()]):
    """ pdc input endpoint to handle PDC data exchange.
    This endpoint processes the input data and headers, fetches the PDC contract,
    retrieves the data provider or ecosystem information, and writes the data to a file.
    
    Uses M2M authentication by matching request headers against user credentials.
    """
    
    # M2M Authentication: Get all users and check credentials against user config
    all_users = await user_service.get_all_users()
    authenticated_users: List[AuthenticatedUser] = await authenticate_m2m_credentials(request.headers, all_users)
    if not authenticated_users:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No valid credentials found in headers"
        )
    fileFormat ="text"
    if (request.headers.get("Content-Type") == "application/json"):
        try:
            data = await request.json()
            fileFormat ="json"
        except : 
            form  = await request.body()
    elif (request.headers.get("Content-Type") == "application/x-www-form-urlencoded"):
        try:
            #data = await request.form() 
            #for now process this  like a raw text
            form  = await request.body()
            data = form.decode()
            fileFormat ="xml"
        except : 
            data = await request.body()
    else:
        #byte with encode or raw text
        form  = await request.body()
        data = form.decode()
    data = decodeDictionary(data)
    #print(f"Received data: {data}")
    
    # Fetch PDC Contract and extract provider name using the service
    pdc_contract = pdc_service.fetch_contract(headers.x_ptx_contracturl)
    provider_name = pdc_service.get_provider_name_from_contract(pdc_contract)
    print(f"Provider name: {provider_name}")
    
    serialized_data = serialize_data(data, fileFormat)
    file_ext = ".json" if fileFormat == "json" else ".xml" if fileFormat == "xml" else ".txt"
    
    # Create datasets for each authenticated user only
    user_datasets = []
    
    for auth_user_data in authenticated_users:
        user_obj = auth_user_data['user']  # TypedDict still uses dict access
        matched_creds = auth_user_data['matched_credentials']
        user_id = str(user_obj.id)
        
        try:
            
            # Create user-specific folder in upload_dir: /upload_dir/userid/
            user_folder = os.path.join(settings.upload_dir, user_id)
            os.makedirs(user_folder, exist_ok=True)
            
            # Dataset name: provider_contract_id
            user_dataset_name = f"{provider_name}_{pdc_contract.id}" if provider_name else str(pdc_contract.id)
            
            # Create file path in user's folder
            user_filename_prefix = f"{pdc_contract.id}_"
            user_complete_filepath = os.path.join(user_folder, f"{user_filename_prefix}{str(time.time())}{file_ext}")
            
            # Check for existing dataset by searching user's owned datasets
            existing_dataset = None
            for owned_dataset_id in user_obj.owned_datasets or []:
                try:
                    existing = await dataset_service.get_dataset(owned_dataset_id, user_obj)
                    if (isinstance(existing, FileDataset) and 
                        existing.name == user_dataset_name and 
                        hasattr(existing, 'folder') and 
                        os.path.normpath(existing.folder) == os.path.normpath(user_folder)):
                        existing_dataset = existing
                        break
                except:
                    continue
            
            if existing_dataset and existing_dataset.ifExist == "append" and existing_dataset.filePath and os.path.exists(existing_dataset.filePath):
                # Mode append: ajouter au fichier existant
                write_input_append(existing_dataset.filePath, serialized_data)
                logger.info(f"Appended data to existing user dataset: {existing_dataset.filePath} for user {user_obj.username}")
                dataset_result = existing_dataset
            elif existing_dataset:
                # Dataset existe mais pas en mode append: remplacer le fichier et mettre à jour
                if existing_dataset.filePath and os.path.exists(existing_dataset.filePath):
                    try:
                        os.remove(existing_dataset.filePath)
                        logger.info(f"Removed old user file: {existing_dataset.filePath}")
                    except OSError as e:
                        logger.error(f"Error removing old user file {existing_dataset.filePath}: {e}")
                
                # Mettre à jour le dataset existant
                write_input(user_complete_filepath, serialized_data)
                existing_dataset.filePath = user_complete_filepath
                existing_dataset.ifExist = 'replace'
                await dataset_service.edit_dataset(existing_dataset, user_obj)
                dataset_result = existing_dataset
                logger.info(f"Updated existing user dataset: {user_complete_filepath} for user {user_obj.username}")
            else:
                # Aucun dataset existant: en créer un nouveau
                write_input(user_complete_filepath, serialized_data)
                
                # Create FileDataset with proper user ownership
                new_dataset = FileDataset(
                    name=user_dataset_name,
                    type='file',
                    folder=user_folder,
                    filePath=user_complete_filepath,
                    inputType='file',
                    ifExist='replace'
                )
                
                # Use add_connection for proper user association
                await dataset_service.add_connection(new_dataset, user_obj)
                dataset_result = new_dataset
                logger.info(f"Created new user dataset: {user_complete_filepath} for user {user_obj.username}")
            
            user_datasets.append({
                'user': user_obj.username,
                'dataset_id': dataset_result.id,
                'auth_method': 'm2m_credentials',
                'credentials_count': len(matched_creds),
                'filepath': dataset_result.filePath
            })
            
        except Exception as e:
            logger.error(f"Error creating dataset for user {user_obj.username}: {str(e)}")
            continue
   
    return {
        "data": data, 
        "path": "user_datasets",
        "contract_id": pdc_contract.id,
        "provider_name": provider_name,
        "authenticated_users": len(authenticated_users),
        "user_datasets": user_datasets
    }

@router.get("/participants_id/{connection_id}")
async def get_participants_id_from_connection(
    connection_id: str,
    current_user: CurrentUser,
    timeout_seconds: Annotated[Optional[int], Query(ge=30, description="Visions API timeout in seconds")] = None,
) -> List[str]:
    """
    Extract unique participants from a connection's catalog
    """
    timeout = _resolve_timeout(timeout_seconds)
    connection = await dataset_service.get_dataset(connection_id, current_user)
    pdc_data = await pdc_get_request(connection, "/", timeout_seconds=timeout)
    participants_id = set()

    if "content" in pdc_data and "ptx:catalog" in pdc_data["content"]:
        async with httpx.AsyncClient(timeout=timeout) as client:
            tasks = [fetch_participant_id(client, content) 
                    for content in pdc_data["content"]["ptx:catalog"]]
            results = await asyncio.gather(*tasks)
            participants_id.update(pid for pid in results if pid)

        if participants_id:
            return list(participants_id)

async def fetch_participant_id(client: httpx.AsyncClient, content: dict) -> Optional[str]:
    """Fetch participant ID from content URL"""
    try:
        response = await client.get(content["@id"], timeout=client.timeout)
        if response.status_code == 200:
            res = response.json()
            
            if content["@type"] in ["ptx:serviceofferings", "ptx:softwareresources"]:
                return res.get("providedBy")
            elif content["@type"] == "ptx:dataresources":
                return res.get("producedBy")
                
    except Exception as e:
        print(f"Error fetching {content['@id']}: {e}")
    return None

@router.get("/contracts/use-case/{connection_id}")
async def get_use_case_contract(
    connection_id: str,
    current_user: CurrentUser,
    hasSigned: Optional[bool] = None,
    timeout_seconds: Annotated[Optional[int], Query(ge=30, description="Visions API timeout in seconds")] = None,
):
    #URI pointing to your participant in the catalog, encode it in base64
    timeout = _resolve_timeout(timeout_seconds)
    connection = await dataset_service.get_dataset(connection_id, current_user)
    config = await get_private_configuration(connection)
    catalog_uri = config.get("catalogUri")
    contract_uri = config.get("contractUri")
    participants_id = await get_participants_id_from_connection(connection_id, current_user, timeout_seconds=timeout)

    all_use_case_contracts = []
    
    # create a new async client for making requests
    async with httpx.AsyncClient(timeout=timeout) as client:
        for participant_id in participants_id:
            participant_url = f"{catalog_uri}catalog/participants/{participant_id}"
            encoded_url = b64_encode(participant_url)
            contract_url = f"{contract_uri}contracts/for/{encoded_url}"
            
            params = {}
            if hasSigned is not None:
                params["hasSigned"] = "true" if hasSigned else "false"

            # use the async client to fetch contracts
            response = await client.get(contract_url, params=params, timeout=timeout)

            if response.status_code == 200:
                contracts_data = response.json()
                for contract in contracts_data.get("contracts"):
                    try:
                        contract = PdcContract.model_validate(contract)
                        
                        # Fetch ecosystem
                        ecosystem = await pdc_service.fetch_ecosystem_async(client, contract.ecosystem, timeout=timeout) if contract.ecosystem else None
                        
                        if participant_id == ecosystem.orchestrator:
                            contract.name = ecosystem.name
                            
                            # Fetch orchestrator
                            if contract.orchestrator:
                                orchestrator = await pdc_service.fetch_participant_async(client, contract.orchestrator, timeout=timeout)
                                contract.logo = orchestrator.get("logo", "") if orchestrator else ""
                            
                            all_use_case_contracts.append(contract)

                            signed_participants = {
                                invitation.get("participant") 
                                for invitation in ecosystem.invitations 
                                if invitation.get("status") == "Signed"
                            }

                            # Fetch all service offerings in parallel for data providers
                            data_provider_tasks = []
                            for participant in ecosystem.participants:
                                has_data_provider_role = (
                                    not participant.roles or 
                                    "Data provider for Organisational Data" in participant.roles or
                                    "https://registry.visionstrust.com/static/references/roles/dataProviderForOrganisationalData.json" in participant.roles
                                )
                                if (participant.participant in signed_participants and 
                                    participant_id != participant.participant and 
                                    has_data_provider_role):
                                    for service in participant.offerings:
                                        url = f"{catalog_uri}catalog/serviceofferings/{service.serviceOffering}"
                                        data_provider_tasks.append(pdc_service.fetch_service_offering_async(client, url, timeout=timeout))

                            data_provider_services = await asyncio.gather(*data_provider_tasks)
                            contract.dataProviders.extend([
                                service for service in data_provider_services 
                                if service and service.dataResources and len(service.dataResources) > 0
                            ])

                            # Fetch all service offerings in parallel for purposes
                            purpose_tasks = []
                            for participant in ecosystem.participants:
                                if participant_id == participant.participant:
                                    for service in participant.offerings:
                                        url = f"{catalog_uri}catalog/serviceofferings/{service.serviceOffering}"
                                        purpose_tasks.append(pdc_service.fetch_service_offering_async(client, url, timeout=timeout))

                            purpose_services = await asyncio.gather(*purpose_tasks)
                            contract.purposes.extend([
                                service for service in purpose_services 
                                if service and service.softwareResources and len(service.softwareResources) > 0
                            ])

                    except Exception as e:
                        logger.error(f"Error processing contract data: {str(e)}")
                        traceback.print_exc()
            else:
                print("Failed to get bilateral contracts for participants")

    return all_use_case_contracts

@router.get("/serviceChain/{connection_id}")
async def get_service_Chain(
    connection_id: str,
    current_user: CurrentUser,
    timeout_seconds: Annotated[Optional[int], Query(ge=30, description="Visions API timeout in seconds")] = None,
):
    timeout = _resolve_timeout(timeout_seconds)
    connection = await dataset_service.get_dataset(connection_id, current_user)
    config = await get_private_configuration(connection)
    catalog_uri = config.get("catalogUri")
    contract_uri = config.get("contractUri")
    participants_id = await get_participants_id_from_connection(connection_id, current_user, timeout_seconds=timeout)
    
    result = []
    for participant_id in participants_id:
        participant_url = f"{catalog_uri}catalog/participants/{participant_id}"
        encoded_url = b64_encode(participant_url)
        contract_url = f"{contract_uri}contracts/for/{encoded_url}"

        response = requests.get(contract_url, timeout=timeout)

        if response.status_code == 200:
            contracts_data = response.json()
            for contract in contracts_data.get("contracts"):
                try:
                    contract = PdcContract.model_validate(contract)
                    ecosystem = pdc_service.fetch_ecosystem(contract.ecosystem, timeout=timeout) if contract.ecosystem else None
                    if participant_id == ecosystem.orchestrator	: 
                        result.append({
                            "contract_id": contract.id,
                            "service_chains": ecosystem.serviceChains
                        })

                except Exception as e:
                    print(f"Error processing contract data: {e}")
                    traceback.print_exc()
        else:
            print("Failed to get bilateral contracts for participants")

    return result


@router.get("/dataExchanges/{connection_id}")
async def get_data_exchanges(
    connection_id: str,
    request: Request,
    current_user: CurrentUser,
    timeout_seconds: Annotated[Optional[int], Query(ge=30, description="Visions API timeout in seconds")] = None,
):
    """
    Retrieve successful data exchange history for a given connection
    For each exchange with status "IMPORT_SUCCESS", fetch details of associated resources

    Returns:
        A Json object containing grouped and detailed data exchanges history
    
    Example JSON response:
    {
        "dataExchanges": [
            {
                "resources": [
                    {
                        "id": "resource-id-1",
                        "name": "Resource Name 1",
                        "description": "Description of Resource 1",
                        "owner": {
                            "id": "owner-id-1",
                            "name": "Owner Name 1"
                        }
                    },
                    ...
                ],
                "contract": "contract-url",
                "providerEndpoint": "provider-endpoint-url",
                "consumerEndpoint": "consumer-endpoint-url",
                "executions": [
                    {
                        "id": "exchange-id-1",
                        "createdAt": "2023-10-01T12:00:00Z"
                    },
                    ...
                ]
            },
            ...
        ]
    }

    Query parameter: timeout_seconds (>=30) can override the default Visions API timeout for this request.
    """
    try:
        timeout = _resolve_timeout(timeout_seconds)
        connection = await dataset_service.get_dataset(connection_id, current_user)
        config = await get_private_configuration(connection)
        pdc_endpoint = config.get("endpoint")
        data_exchanges_url = f"{pdc_endpoint}dataexchanges"
        participant_url = f"{config.get('catalogUri')}participants/"
        
        response = requests.get(data_exchanges_url, timeout=timeout)
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Can't retrieve data exchange history: {response.text}"
            )
            
        data_exchanges_data = response.json()
        content = data_exchanges_data.get("content", [])
        
        # Cache to avoid redundant requests for the same resource
        resource_cache = {}
        
        # Helper function to fetch detailed resource information
        def get_resource_details(resource_url):
            if resource_url in resource_cache:
                return resource_cache[resource_url]
            
            try:
                resource_response = requests.get(resource_url, timeout=timeout)
                if resource_response.status_code == 200:
                    resource_data = PdcDataResource.model_validate(resource_response.json())
                    owner_url =  f"{participant_url}{resource_data.producedBy}" if resource_data.producedBy else None
                    owner_details = pdc_service.fetch_participant(owner_url, timeout=timeout) if owner_url else {}
                    details = {
                        "id": resource_data.id,
                        "name": resource_data.name,
                        "description": resource_data.description,
                        "owner": {
                            "id": owner_details.id,
                            "name": owner_details.legalName 
                         } 
                    }
                    resource_cache[resource_url] = details
                    return details
                else:
                    print(f"Error fetching resource {resource_url}: {resource_response.status_code}")
                    return None
            except Exception as e:
                print(f"Exception while fetching resource {resource_url}: {str(e)}")
                return None
        
        # Group exchanges by resources, contract, and endpoint
        grouped_exchanges = defaultdict(lambda: {"executions": []})
        
        for item in content:
            if item.get("status") != "IMPORT_SUCCESS":
                continue
                
            resources = item.get("resources", [])
            contract = item.get("contract")
            provider_endpoint = item.get("providerEndpoint")
            consumer_endpoint = item.get("consumerEndpoint")
            item_id = item.get("_id")
            created_at = item.get("createdAt")
            
            detailed_resources = []
            for res in resources:
                resource_url = res.get("resource", "")
                resource_details = get_resource_details(resource_url)
                
                if resource_details:
                    detailed_resources.append(resource_details)
            
            # Generate a key for grouping
            resources_ids = tuple(sorted(res["id"] for res in detailed_resources))
            endpoint = provider_endpoint or consumer_endpoint
            group_key = (resources_ids, contract, endpoint)
            
            group = grouped_exchanges[group_key]
            if not group["executions"]:  
                group.update({
                    "resources": detailed_resources,  
                    "contract": contract
                })
                if provider_endpoint:
                    group["providerEndpoint"] = provider_endpoint
                elif consumer_endpoint:
                    group["consumerEndpoint"] = consumer_endpoint
            
            execution = {"id": item_id}
            if created_at is not None:
                execution["createdAt"] = created_at
            group["executions"].append(execution)
        
        data_exchanges = []
        for group in grouped_exchanges.values():
            group["executions"].sort(
                key=lambda x: x.get("createdAt") or "",
                reverse=True
            )
            data_exchanges.append(group)
            
        return {"dataExchanges": data_exchanges}
        
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
@router.post("/trigger-data-exchange/{connection_id}")
async def trigger_data_exchange(
    connection_id: str,
    request: Request,
    current_user: CurrentUser,
    timeout_seconds: Annotated[Optional[int], Query(ge=30, description="Visions API timeout in seconds")] = None,
):
    try:
        timeout = _resolve_timeout(timeout_seconds)
        connection = await dataset_service.get_dataset(connection_id, current_user)
        
        config = await get_private_configuration(connection)
        pdc_endpoint = config.get("endpoint")
        contract_uri = config.get("contractUri")
        
        body = await request.json()
        contract_id = body.get("contract")
        

        contract_url = f"{contract_uri}contracts/{contract_id}"
        
        payload = {
            "contract": contract_url,
            "purposeId": body.get("purposeId"),
            "resourceId": body.get("resourceId"),
        }
        
        exchange_url = f"{pdc_endpoint}exchange"
        headers = {
            'Authorization': f'Bearer {connection.token}',
            'Content-Type': 'application/json'
        }
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(exchange_url, json=payload, headers=headers, timeout=timeout)
        
        if response.status_code == 200:
            return {
                "success": True,
                "response": response.json()
            }
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Data exchange failed: {response.text}"
            )
            
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/triggerServiceChain/{connection_id}")
async def trigger_service_chain(
    connection_id: str,
    request: Request,
    current_user: CurrentUser,
    timeout_seconds: Annotated[Optional[int], Query(ge=30, description="Visions API timeout in seconds")] = None,
):
    try:
        timeout = _resolve_timeout(timeout_seconds)
        connection = await dataset_service.get_dataset(connection_id, current_user)
        
        config = await get_private_configuration(connection)
        pdc_endpoint = config.get("endpoint")
        contract_uri = config.get("contractUri")
        
        body = await request.json()
        contract_id = body.get("contractId")
        

        contract_url = f"{contract_uri}contracts/{contract_id}"
        
        payload = {
            "contract": contract_url,
            "serviceChainId": body.get("serviceChainId")
        }
        
        exchange_url = f"{pdc_endpoint}exchange"
        headers = {
            'Authorization': f'Bearer {connection.token}',
            'Content-Type': 'application/json'
        }
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(exchange_url, json=payload, headers=headers, timeout=timeout)
        
        if response.status_code == 200:
            return {
                "success": True,
                "response": response.json()
            }
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Data exchange failed: {response.text}"
            )
            
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/contracts/bilaterals/{connection_id}")
async def get_billateral_contract(
    connection_id: str,
    current_user: CurrentUser,
    timeout_seconds: Annotated[Optional[int], Query(ge=30, description="Visions API timeout in seconds")] = None,
):
    #URI pointing to your participant in the catalog, encode it in base64
    try:
        connection = await dataset_service.get_dataset(connection_id, current_user)
        if not connection:
            raise HTTPException(status_code=404, detail="Connection not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finding connection: {str(e)}")
    
    try:
        config = await get_private_configuration(connection)
        catalog_uri = config.get("catalogUri")
        contract_uri = config.get("contractUri")
        endpoint = config.get("endpoint")
        if not catalog_uri or not contract_uri:
            raise ValueError("Missing catalogUri or contractUri in config")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading private configuration: {str(e)}")
    
    try:
        timeout = _resolve_timeout(timeout_seconds)
        participants_id = await get_participants_id_from_connection(connection_id, current_user)
        if not participants_id:
            raise ValueError("No participants found for this connection")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving participants: {str(e)}")

    all_bilateral_contracts = []
    for participant_id in participants_id:
        participant_url = f"{catalog_uri}catalog/participants/{participant_id}"
        encoded_url = b64_encode(participant_url)
        bilateral_url = f"{contract_uri}/bilaterals/for/{encoded_url}"

        response = requests.get(bilateral_url, timeout=timeout)

        if response.status_code == 200:
            contracts_data = response.json()

            for contract in contracts_data.get("contracts"):
                try:
                    contract = PdcContractBilateral.model_validate(contract)
                    contract_info = pdc_service.get_provider_name_and_img_from_contract(contract)
                    contract.name = contract_info.get("name") if contract_info.get("name") else "Unknown"
                    contract.img = contract_info.get("img") if contract_info.get("img") else ""
                    all_bilateral_contracts.append(contract)
                except Exception as e:
                    print(f"Error processing contract data: {e}")
        else:
            print("Failed to get bilateral contracts for participants")

    return {
        "contracts": all_bilateral_contracts,
        "endpoint": endpoint,
        "contractUri": contract_uri
    }

def b64_encode(url: str):
    encoded_url = base64.b64encode(url.encode('utf-8')).decode('utf-8')
    return encoded_url

async def pdc_get_request(connection: Dataset, url, timeout_seconds: Optional[int] = None):
    timeout = _resolve_timeout(timeout_seconds)

    def _request_with_token() -> requests.Response:
        return requests.get(
            connection.url + url,
            headers={"Authorization": "Bearer " + connection.token},
            timeout=timeout,
        )

    r = _request_with_token()

    if r.status_code in (401, 403) and isinstance(connection, PTXDataset):
        renewed = await dataset_service.ensure_runtime_ptx_tokens(connection)
        if renewed and connection.token:
            r = _request_with_token()

    if r.status_code in (401, 403):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "PTX token invalid or expired for this connection. "
                "Refresh/relogin attempt failed. Update PTX credentials."
            ),
        )

    if r.status_code >= 400:
        raise HTTPException(
            status_code=r.status_code,
            detail=f"PTX request failed: {r.text}",
        )

    content_type = r.headers.get("Content-Type", "")
    if "json" in content_type.lower():
        return r.json()
    return r.content

def write_input_append(file: str, data: str):
    """Append data to existing file with proper JSON merging."""
    try:
        
        new_data = json.loads(data)
        
        if os.path.exists(file):
            print(f"Appending data to file: {file}")
            # Read existing data
            with open(file, 'r') as f:
                content = f.read().strip()
            
            if content:
                # Parse existing JSON
                existing_data = json.loads(content)
                print(f"Existing data type: {type(existing_data)}")
                print(f"New data type: {type(new_data)}")

                if isinstance(existing_data, list) and not isinstance(new_data, list):
                    print("Merging existing list with new data")
                    merged_data = existing_data + [new_data]

                elif not isinstance(existing_data, list) and not isinstance(new_data, list):
                    print("Merging existing data with new data")
                    merged_data = [existing_data, new_data]

                elif isinstance(existing_data, list) and isinstance(new_data, list):
                    print("Merging two lists")
                    merged_data = existing_data + new_data    

                else:
                    print("Merging existing data with new data")
                    merged_data = [existing_data] + new_data
                with open(file, 'w') as f:
                    f.write(json.dumps(merged_data, indent=2))
            else:
                with open(file, 'w') as f:
                    f.write(json.dumps(new_data, indent=2))
        else:
            print(f"Creating new file: {file}")
            # Create new file
            with open(file, 'w') as f:
                f.write(json.dumps(new_data, indent=2))
                
    except json.JSONDecodeError:
        # If not valid JSON, append as tezzzxt
        with open(file, 'a') as f:
            f.write('\n' + data)

def write_input(file: str, data: str):
    """ Write data to file (overwrite).
    """
    with open(file, 'w') as f:
        f.write(data)


async def get_private_configuration(connection):
    """Get private configuration with caching"""
    cache_key = f"{connection.id}"
    
    # check if the configuration is already cached and not expired
    now = datetime.now()
    if (cache_key in _config_cache and 
        cache_key in _config_timestamp and
        now - _config_timestamp[cache_key] < timedelta(minutes=5)):
        return _config_cache[cache_key]
    
    # if not cached, fetch the configuration
    res = await pdc_get_request(connection, "/private/configuration/")
    if "content" in res:
        config = {
            "endpoint": res["content"].get("endpoint"),
            "catalogUri": res["content"].get("catalogUri"),
            "contractUri": res["content"].get("contractUri"),
            "consentUri": res["content"].get("consentUri"),
        }
        # store in cache
        _config_cache[cache_key] = config
        _config_timestamp[cache_key] = now
        return config
    else:
        raise ValueError("Error retrieving configuration")

async def get_serviceoffering_by_id(id: str, connection):
    conf = await get_private_configuration(connection)
    url = conf["catalogUri"] + "catalog/serviceofferings/" + id
    return pdc_service.fetch_service_offering(url)

def serialize_data(data, fileFormat):
    if fileFormat == "json":
        return json.dumps(data, indent=2)
    elif fileFormat == "xml":
        # if XML string return or convert
        if isinstance(data, str):
            return data
        elif isinstance(data, dict):
            # Simple dict to XML conversion
            root = ET.Element("root")
            for k, v in data.items():
                child = ET.SubElement(root, k)
                child.text = str(v)
            return ET.tostring(root, encoding="unicode")
        else:
            return str(data)
    else:
        # raw text
        return data.decode() if isinstance(data, bytes) else str(data)
