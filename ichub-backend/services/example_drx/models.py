#################################################################################
# Eclipse Tractus-X - Industry Core Hub Backend
#
# Copyright (c) Lisa Dräxlmaier GmbH
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
from typing import Any, Dict, List, Optional
from uuid import UUID

class DataExchangeAgreement(BaseModel):
    partner_name: str
    agreement_name: str

class CatalogPart(BaseModel):
    manufacturer_part_id: str
    customer_part_id: Optional[str]

class SerialPart(CatalogPart):
    part_instance_id: str
    van: Optional[str]

class BatchPart(CatalogPart):
    batch_id: str

class JISPart(CatalogPart):
    jis_order_number: str
    parent_order_number: Optional[str]
    jis_call_date: Optional[datetime]

class CreateShellInput(BaseModel):
    # Business Partner agreement
    agreement: DataExchangeAgreement

    # Part data - one of the following needed
    # TODO: how to express with Pydanctic?
    catalog_part: Optional[CatalogPart]
    serial_part: Optional[SerialPart]
    batch_part: Optional[BatchPart]
    serial_part: Optional[SerialPart]

    catenax_id: Optional[UUID] # if not given, will be generated automatically

    # Optional preview of semantic IDs to be assigned to the twin later (needed for proper scheduling of UID push)
    semantic_ids: Optional[List[str]] = Field(default=None)

    # Flags for UID push logic
    push: Optional[bool] = Field(default=False) # Mark twin as a push candidate
    push_retry: Optional[bool] = Field(default=False) # Flag to retry UID push for identified twin

    # Schema-less custom data that can be attached to the twin (provided/process by consuming apps)
    custom_data: Optional[Dict[str, Any]] = Field(default=None)

class CreateShellConfig(BaseModel):
    # Where to register
    stack: str

    fail_on_duplicate: Optional[bool] = Field(default=False)

class CreateShellOutput(BaseModel):
    catenax_id: UUID # Catena-X ID ("Global ID") of the generated or existing twin
    dtr_aas_id: Optional[UUID] # DTR AAS ID of the generated or existing twin (if applicable)
    # TODO

class DeleteShellInput(BaseModel):
    catenax_id: UUID

class DeleteShellConfig(BaseModel):
    stack: str

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