from typing import Dict, List, Any, Optional
from bson import ObjectId
from bson.errors import InvalidId
from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator, model_serializer
from beanie import Document
from datetime import datetime


class IDataConnector(BaseModel):
    id: str
    name: str
    description: str
    parent_folder: str
    type: str
    file_path: str
    file: bytes
    uri: str
    database: str
    collection: str
    host: str
    user: str
    password: str
    table: str
    url: str
    revision: str

class ISocket(BaseModel):
    name: str

class INodePort(BaseModel):
    id: str
    label: Optional[str] = None
    socket: ISocket
    
class NodeControl(BaseModel):
    type: Any  
    id: str
    readonly: bool
    value: Any
    __type: Any    

class INode(BaseModel):
    id: str
    type: str
    label: str
    inputs: dict[str, INodePort]
    outputs: dict[str, INodePort]
    controls: dict[str, NodeControl | None]
    revision: Optional[str] = None
    position: Optional[dict[str, float]] = None
    data: Any

class INodeConnection(BaseModel):
    id: str
    sourceNode: str
    targetNode: str
    sourcePort: str
    targetPort: str

class ISchema(BaseModel):
    nodes: List[INode]
    connections: List[INodeConnection]
    revision: Optional[str] = None

# Nouveau modèle Beanie pour MongoDB
class IProject(Document):
    id: Optional[str] = Field(default=None, alias="_id")
    name: str
    revision: Optional[str] = None
    dataConnectors: Optional[List[str]] = []
    pschema: Optional[ISchema] = Field(default_factory=lambda: ISchema(nodes=[], connections=[]), alias='schema')
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # User ownership and sharing
    owner_id: Optional[str] = Field(default=None, description="ID of the user who owns this workflow")
    shared_with: List[str] = Field(default_factory=list, description="List of user IDs this workflow is shared with")
    

    @field_validator('id', mode='before')
    @classmethod
    def prevent_auto_objectid(cls, v):
        """Empêcher Pydantic de générer automatiquement un ObjectId"""
        # Si c'est un ObjectId auto-généré, le supprimer
        if isinstance(v, ObjectId):
            return None
        # Si c'est une string ObjectId, la garder seulement si elle vient de l'utilisateur
        if isinstance(v, str) and len(v) == 24:
            try:
                ObjectId(v)  # Vérifier si c'est un ObjectId valide
                return v  # Garder les ObjectId valides fournis par l'utilisateur
            except InvalidId:
                return None
        return v

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        validate_assignment=True
    )
    
    class Settings:
        name = "workflows"  # Collection name in MongoDB
        indexes = [
            "name",
            "created_at",
            "updated_at",
            "owner_id"
        ]
        
    @model_serializer(mode='wrap')
    def serialize_model(self, serializer, info) -> Dict[str, Any]:
        data = serializer(self)
        if '_id' in data:
            data['id'] = str(data.pop('_id'))
        elif 'id' in data and data['id']:
            data['id'] = str(data['id'])
        
        return data
# Alias pour compatibilité
Workflow = IProject
