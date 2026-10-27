from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from beanie import Document
from pydantic import BaseModel, Field
from pymongo import ASCENDING, IndexModel

# Service chain data not retrieved/deleted by the frontend expires after this delay
SERVICE_CHAIN_DATA_TTL_SECONDS = 24 * 3600


class EndpointDataProvider(BaseModel):
    id: str
    workflowId: str
    nodeId: str
    authToken: str
    endpoint: str
    method: str
    src:str
    lastUpdated: str

class Participant(BaseModel):
    name: str
    connectorUrl: str
    id: str

class AdditionalDataItem(BaseModel):
    participant: Participant
    params: Dict[str, Any]
    data: Dict[str, Any]

class PdcChainRequestData(BaseModel):
    additionalData: Optional[List[AdditionalDataItem]] = None
    origin: Dict[str, Any]


class PdcChainRequest(BaseModel):
    data: Union[PdcChainRequestData, str, List[Any],Dict[str, Any]]
    contract: Optional[str] = None
    params: Optional[Dict[str, Any]] = None

class PdcChainResponse(BaseModel):
    chainId: str | None
    targetId: str |None
    data: Dict | List | None
    params: Optional[Dict[str, Any]] = None

class PdcChainHeaders(BaseModel):
    Authorization: str
    x_ptx_service_chain_id: str | None = None
    x_ptx_target_id: str | None = None


class ServiceChainData(Document):
    """Data received from a PDC service chain, shared by all backend workers"""
    id: Optional[str] = Field(default=None, alias="_id", description="Service chain ID")
    data: Any = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "service_chain_data"
        indexes = [
            IndexModel([("created_at", ASCENDING)], expireAfterSeconds=SERVICE_CHAIN_DATA_TTL_SECONDS)
        ]
