#################################################################################
# Eclipse Tractus-X - Industry Core Hub Backend
#
# Copyright (c) 2025 DRÄXLMAIER Group
# (represented by Lisa Dräxlmaier GmbH)
# Copyright (c) 2025 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License, Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the
# License for the specific language govern in permissions and limitations
# under the License.
#
# SPDX-License-Identifier: Apache-2.0
#################################################################################

from pydantic import BaseModel, Field

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

class DataExchangeAgreement(BaseModel):
    """A contractual (or other) relationship to a partner where specific data is exchange or a specific Catena-X use-case is performed"""
    
    partner_name: str = Field(alias='partnerName')
    """The name of the business partner"""

    agreement_name: str = Field(alias='agreementName')
    """The name of the Data Exchange Agreement with the partner"""

class CatalogPart(BaseModel):
    """Represents details about a twin/part of type 'catalog part'"""

    manufacturer_part_id: str = Field(alias='manufacturerPartId')
    """The manufacturer part id of the related part"""

    customer_part_id: Optional[str] = Field(default=None, alias='customerPartId')
    """The optional customer part id of the related part"""

class SerialPart(CatalogPart):
    """Represents details about a twin/part of type 'serial part'"""

    part_instance_id: str = Field(alias='partInstanceId')
    """The part instance id of the serial part"""

    van: Optional[str]
    """The optional VAN if the serial part represents a vehicle"""

class BatchPart(CatalogPart):
    """Represents details about a twin/part of type 'batch part'"""

    batch_id: str = Field(alias='batchId')
    """The batch id of the part batch"""

class JISPart(CatalogPart):
    """Represents details about a twin/part of type 'JIS part'"""

    jis_order_number: str
    """The JIS number id of the part"""

    parent_order_number: Optional[str]
    """The optional parent order number of the part"""

    jis_call_date: Optional[datetime]
    """The optional JIS call date related to the part"""

class CreateShellInput(BaseModel):
    """Input data for the 'create shell' API call"""

    agreement: DataExchangeAgreement
    """Details about the Data Exchange Agreement that the twin/shell should be associated with"""

    # Part data - exactly one of the following 4 needed
    # TODO: how to express with Pydanctic?
    catalog_part: Optional[CatalogPart] = Field(default=None, alias='catalogPart')
    """If this is a catalog part details go here"""

    serial_part: Optional[SerialPart] = Field(default=None, alias='serialPart')
    """If this is a serial part details go here"""

    batch_part: Optional[BatchPart] = Field(default=None, alias='batchPart')
    """If this is a batch part details go here"""

    jis_part: Optional[JISPart] = Field(default=None, alias='jisPart')
    """If this is a JIS part details go here"""


    catenax_id: Optional[UUID] = Field(default_factory = uuid4, alias = 'catenaXId')
    """The Catena-X ID of the new twin/shell

    If not provided a new one will be automatically generated"""

    semantic_ids: Optional[List[str]] = Field(default=None, alias = "semanticIds")
    """Optional preview of semantic IDs to be assigned to the twin later (needed for proper scheduling of UID push)"""

    # Flags for UID push logic
    push: Optional[bool] = Field(default=False)
    """Should this shell/twin be marked as a push candidate"""

    push_retry: Optional[bool] = Field(default=False)
    """Flag to retry UID push for identified twin"""

    custom_data: Optional[Dict[str, Any]] = Field(default=None)
    """Schema-less custom data that can be attached to the twin (provided/process by consuming apps)"""

class CreateShellConfig(BaseModel):
    stack: str
    """Name of the Enablement Service Stack where to register the twin/shell"""

    fail_on_duplicate: Optional[bool] = Field(default=False)

class CreateShellOutputStatus(str, Enum):
    NEW = 'NEW'
    NEW_STACK = 'NEW-STACK'
    RE_REGISTER = 'RE-REGISTER'
    ERROR = 'ERROR'

class CreateShellOutputAspectStatus(str, Enum):
    CREATED = 'CREATED'
    CREATED_NEW_STACK = 'CREATED-NEW-STACK'
    SKIPPED = 'SKIPPED'

class CreateShellOutputPushStatus(str, Enum):
    CREATED = 'CREATED'
    SKIPPED = 'SKIPPED'
    RESET = 'RESET'
    ERROR = 'ERROR'

class CreateShellOutputPushStatusStruct(BaseModel):
    status: CreateShellOutputPushStatus
    statusMessage: Optional[str]

class CreateShellOutput(BaseModel):
    catenax_id: UUID # Catena-X ID ("Global ID") of the generated or existing twin
    dtr_aas_id: Optional[UUID] # DTR AAS ID of the generated or existing twin (if applicable)
    
    status: CreateShellOutputStatus
    statusMessage: Optional[str]

    aspectStatus: Optional[Dict[str, CreateShellOutputAspectStatus]]
    
    push: Optional[CreateShellOutputPushStatusStruct]

class DeleteShellInput(BaseModel):
    catenax_id: UUID

class DeleteShellConfig(BaseModel):
    stack: str
    """Name of the Enablement Service Stack from where to unregister the twin/shell"""

    cascade_submodels: Optional[bool] = Field(default=False)
    clean_storage: Optional[bool] = Field(default=False)

class DeleteShellOutput(BaseModel):
    pass

class CreateSubmodelInput(BaseModel):
    catenax_id: UUID
    semantic_id: str

    # Content of the submodel (as JSON)
    content: Optional[Dict[str, Any]] = Field(default=None)

    # Alternative to content: use templating
    # => semantic-id determines a template which just needs to be filled with params
    params: Optional[Dict[str, Any]] = Field(default=None)

class CreateSubmodelConfig(BaseModel):
    # Where to register
    stack: str

    fail_on_duplicate: Optional[bool] = Field(default=False)
    overwrite_storage: Optional[bool] = Field(default=False)

    # DRÄXLMAIER has implemented a tiny data ingestion transformation framework that can be disabled here
    skip_transformers: Optional[bool] = Field(default=False) # Skip transformers for the submodel
    
    pretty_print: Optional[bool] = Field(default=False) # Pretty-print the JSON content before storing

class CreateSubmodelOutput(BaseModel):
    pass

class DeleteSubmodelInput(BaseModel):
    catenax_id: UUID
    semantic_id: str

class DeleteSubmodeConfig(BaseModel):
    stack: str

class DeleteSubmodelOutput(BaseModel):
    pass