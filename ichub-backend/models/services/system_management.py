from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class EnablementServiceStackBase(BaseModel):
    name: str = Field(..., description="Name of the enablement service stack")
    legal_entity_id: int = Field(..., description="ID of the associated legal entity")
    # Add other fields as needed

class EnablementServiceStackCreate(EnablementServiceStackBase):
    pass

class EnablementServiceStackUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Name of the enablement service stack")
    # Add other updatable fields as needed

class EnablementServiceStackRead(EnablementServiceStackBase):
    id: int
    class Config:
        from_attributes = True

class EdcServiceBase(BaseModel):
    name: str = Field(..., description="Name of the EDC service")
    connection_settings: Optional[Dict[str, Any]] = Field(None, description="Connection settings as JSON")
    legal_entity_id: int = Field(..., description="ID of the associated legal entity")

class EdcServiceCreate(EdcServiceBase):
    pass

class EdcServiceUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Name of the EDC service")
    connection_settings: Optional[Dict[str, Any]] = Field(None, description="Connection settings as JSON")

class EdcServiceRead(EdcServiceBase):
    id: int
    class Config:
        from_attributes = True

class DtrServiceBase(BaseModel):
    name: str = Field(..., description="Name of the DTR service")
    connection_settings: Optional[Dict[str, Any]] = Field(None, description="Connection settings as JSON")

class DtrServiceCreate(DtrServiceBase):
    pass

class DtrServiceUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Name of the DTR service")
    connection_settings: Optional[Dict[str, Any]] = Field(None, description="Connection settings as JSON")

class DtrServiceRead(DtrServiceBase):
    id: int
    class Config:
        from_attributes = True
