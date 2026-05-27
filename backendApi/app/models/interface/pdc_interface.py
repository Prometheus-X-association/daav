from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, model_validator
from datetime import datetime



class Constraint(BaseModel):
    leftOperand: str
    operator: str
    rightOperand: str | int | bool


class Permission(BaseModel):
    action: str
    target: str
    constraint: List[Constraint] = []
    duty: List[Dict[str, Any]] = []


class Policy(BaseModel):
    description: str
    permission: List[Permission] = []
    prohibition: List[Dict[str, Any]] = []


class ServiceOffering(BaseModel):
    participant: str
    serviceOffering: str
    policies: List[Policy] = []
    id: str = Field(alias="_id")


class Member(BaseModel):
    participant: str
    role: str
    signature: str
    date: datetime


class Service(BaseModel):
    participant: str
    service: str
    params: str = ""
    configuration: str = ""
    pre: List[List[Dict[str, str]]] = []


class ServiceChain(BaseModel):
    catalogId: str
    services: List[Service]
    status: str | None = None
    id: str | None = Field(alias="_id", default=None)

    @model_validator(mode="before")
    @classmethod
    def validate_id(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        for key in ["_id", "serviceChainId", "service_chain_id", "id"]:
            if key in data:
                data["id"] = data.pop(key)
                return data

        data["id"] = None
        return data

class Negotiator(BaseModel):
    did: str
    id: str = Field(alias="_id")

class Signature(BaseModel):
    date: datetime
    did: str
    party: str
    value: str

class PdcContract(BaseModel):
    id: str = Field(alias="_id")
    ecosystem: str | None = Field(default=None)
    orchestrator: str | None = Field(default=None)
    dataProvider: str | None = Field(default=None)
    dataConsumer: str | None = Field(default=None)
    serviceOffering: str | None = Field(default=None)
    rolesAndObligations: List[Any] = []
    status: str
    serviceOfferings: List[ServiceOffering] | None = Field(default=None)
    purpose: List[Any] = []
    members: List[Member] | None = Field(default=None)
    revokedMembers: List[Any] = []
    createdAt: datetime
    updatedAt: datetime
    v: int = Field(alias="__v")
    dataProcessings: List[Any] = []
    serviceChains: List[ServiceChain] | None = Field(default=None)
    examples: List[Any] = []
    model_config = ConfigDict(extra="allow") 
    dataProviders: List[Any] = []
    purposes: List[Any] = [] 

class PdcContractBilateral(BaseModel):
    id: str = Field(alias="_id")
    dataProvider: str | None = Field(default=None)
    dataConsumer: str | None = Field(default=None)
    negotiators: List[Negotiator] = []
    policy: List[Policy] = []
    purpose: List[Any] = []
    revokedSignatures: List[Any] = []
    serviceOffering: str
    signatures: List[Signature] = []
    status: str
    createdAt: datetime
    updatedAt: datetime
    v: int = Field(alias="__v")
    model_config = ConfigDict(extra="allow") 


class Address(BaseModel):
    countryCode: str = ""


class LegalPerson(BaseModel):
    headquartersAddress: Address
    legalAddress: Address
    registrationNumber: str = ""
    parentOrganization: List[str] = []
    subOrganization: List[str] = []


class PdcParticipant(BaseModel):
    context: str | None = Field(default=None, alias="@context")
    type: str = Field(alias="@type", default="Participant")
    id: str = Field(alias="_id")
    did: str | None = None
    legalName: str
    legalPerson: LegalPerson
    termsAndConditions: str = ""
    associatedOrganisation: str
    schema_version: str
    createdAt: datetime
    updatedAt: datetime
    v: int = Field(alias="__v")
    dataspaceConnectorAppKey: str
    dataspaceEndpoint: str
    logo: str = ""


class PolicyRule(BaseModel):
    ruleId: str
    values: Dict[str, str | int | bool]
    id: str = Field(alias="_id")


class Pricing(BaseModel):
    pricingModel: List[str] = []
    costPerAPICall: float = 0
    setupFee: int = 0


class Offering(BaseModel):
    serviceOffering: str
    policy: List[PolicyRule] = []
    pricing: Pricing
    id: str = Field(alias="_id")


class EcosystemParticipant(BaseModel):
    organization: str
    participant: str
    roles: List[str]
    offerings: List[Offering] = []
    id: str = Field(alias="_id")


class BusinessLogic(BaseModel):
    businessModel: List[str] = []
    roles: List[Any] = []


class PdcEcosystem(BaseModel):
    context: str = Field(alias="@context")
    type: str = Field(alias="@type", default="Ecosystem")
    id: str = Field(alias="_id")
    administrator: str
    orchestrator: str
    name: str
    description: str
    detailedDescription: str
    country_or_region: str = ""
    target_audience: str = ""
    main_functionalities_needed: List[str] = []
    logo: str = ""
    useCases: List[Any] = []
    participants: List[EcosystemParticipant]
    searchedDatatypes: List[Any] = []
    searchedServices: List[Any] = []
    searchedDataCategories: List[Any] = []
    searchedServiceCategories: List[Any] = []
    searchedCategoriesDetails: List[Any] = []
    provides: List[Any] = []
    contract: str
    location: str = ""
    businessLogic: BusinessLogic
    status: str
    schema_version: str
    context_list: List[str] = Field(alias="context")
    joinRequests: List[Any] = []
    infrastructureServices: List[Any] = []
    dataProcessingChains: List[Any] = []
    invitations: List[Any] = []
    rolesAndObligations: List[Any] = []
    buildingBlocks: List[Any] = []
    createdAt: datetime
    updatedAt: datetime
    v: int = Field(alias="__v")
    searchedInfrastructureCategories: List[Any] = []
    serviceChains: List[Any] = []


class PolicyPermission(BaseModel):
    action: str
    target: str
    constraint: List[Any] = []

class PolicyDefinition(BaseModel):
    permission: List[PolicyPermission] = []

class PolicyContext(BaseModel):
    xsd: str = ""
    description: Dict[str, Any] = {}

class PolicyTitle(BaseModel):
    type: str = Field(alias="@type")
    value: str = Field(alias="@value")

class PolicyDescription(BaseModel):
    value: str = Field(alias="@value")
    language: str = Field(alias="@language")

class DetailedPolicy(BaseModel):
    context: PolicyContext = Field(alias="@context")
    id: str = Field(alias="@id")
    title: PolicyTitle
    uid: str
    name: str
    description: List[PolicyDescription] = []
    policy: PolicyDefinition
    requestedFields: List[str] = []

class PdcServiceOffering(BaseModel):
    context: str = Field(alias="@context")
    type: str = Field(alias="@type", default="ServiceOffering")
    id: str = Field(alias="_id")
    name: str
    providedBy: str
    aggregationOf: List[str] = []
    dependsOn: List[str] = []
    policy: List[DetailedPolicy] = []
    termsAndConditions: str = ""
    dataProtectionRegime: List[str] = []
    location: str = ""
    description: str = ""
    detailedDescription: str = ""
    image: str = ""
    keywords: List[str] = []
    dataResources: List[str] = []
    softwareResources: List[str] = []
    archived: bool = False
    visible: bool = True
    pricing: float = 0
    pricingModel: List[str] = []
    businessModel: List[str] = []
    maximumConsumption: str = ""
    maximumPerformance: str = ""
    pricingDescription: str = ""
    b2cDescription: List[str] = []
    purpose: str = ""
    status: str = "published"
    currency: str = "EUR"
    billingPeriod: str = "One shot"
    costPerAPICall: float = 0
    setupFee: float = 0
    compliantServiceOfferingVC: str = ""
    serviceOfferingVC: str = ""
    category: List[str] = []
    schema_version: str = ""
    dataAccountExport: List[Any] = []
    createdAt: datetime
    updatedAt: datetime
    v: int = Field(alias="__v")
    userInteraction: bool = False
class LocationAddress(BaseModel):
    countryCode: str
    id: str = Field(alias="_id")
class Input(BaseModel):
    format: str = ""
    description: str = ""
    snippet: str = ""
    size: str = ""
class Output(BaseModel):
    format: str = ""
    description: str = ""
    snippet: str = ""

class Representation(BaseModel):
    id: str = Field(alias="_id")
    resourceID: str
    type: str
    url: str
    fileType: str = ""  
    sqlQuery: str = ""
    className: str = ""
    method: str
    credential: str
    queryParams: List[Any] = []
    input: Input = None
    output: Output = None
    processingTime: str = ""
    createdAt: datetime
    updatedAt: datetime
    v: int = Field(alias="__v")
class PdcSoftwareResource(BaseModel):
    context: str = Field(alias="@context")
    type: str = Field(alias="@type", default="SoftwareResource")
    id: str = Field(alias="_id")
    name: str
    description: str = ""
    aggregationOf: List[Any] = []
    copyrightOwnedBy: List[str] = []
    license: List[str] = []
    policy: List[str] = []
    category: str = ""
    locationAddress: List[LocationAddress] = []
    users_clients: int = 0
    demo_link: str = ""
    relevant_project_link: str = ""
    schema_version: str = ""
    usePII: bool = False
    isAPI: bool = False
    b2cDescription: List[Any] = []
    jurisdiction: str = ""
    retention_period: str = ""
    recipient_third_parties: List[Any] = []
    createdAt: datetime
    updatedAt: datetime
    v: int = Field(alias="__v")
    representation: Optional[Representation] = None

class B2CDescription(BaseModel):
    language: str = Field(alias="@language")
    value: str = Field(alias="@value")


class PdcDataResource(BaseModel):
    context: Optional[str] = Field(alias="@context", default=None)
    type: str = Field(alias="@type", default="DataResource")
    id: str = Field(alias="_id")
    aggregationOf: List[Any] = []
    name: str = ""
    description: str = ""
    copyrightOwnedBy: List[str] = []
    license: List[Any] = []
    policy: List[Any] = []
    producedBy: str = ""
    exposedThrough: List[Any] = []
    obsoleteDateTime: Optional[str] = ""
    expirationDateTime: Optional[str] = ""
    containsPII: bool = False
    anonymized_extract: Optional[str] = ""
    archived: bool = False
    attributes: List[Any]
    category: Union[str, dict, List[Any]] = None
    isPayloadForAPI: bool = False
    country_or_region: str = ""
    entries: int = 0
    subCategories: List[Any] = []
    schema_version: str = ""
    b2cDescription: Union[str, List[B2CDescription]]  = None
    createdAt: datetime 
    updatedAt: datetime 
    __v: int = 0
    representation: Optional[Representation] = None
    apiResponseRepresentation: Optional[Representation] = None
