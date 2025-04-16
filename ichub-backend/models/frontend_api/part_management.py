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

from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, Field

from models.frontend_api.partner_management import BusinessPartner

class CatalogPart(BaseModel):
    manufacturer_id: str = Field(alias="manufacturerId", description="The BPNL (manufactuer ID) of the part to register.")
    manufacturer_part_id: str = Field(alias="manufacturerPartId", description="The manufacturer part ID of the part.")

class CatalogPartRead(CatalogPart):
    customer_part_ids: Optional[Dict[str, BusinessPartner]] = Field(alias="customerPartIds", description="The list of customer part IDs mapped to the respective Business Partners.", default={})

class CatalogPartCreate(CatalogPart):
    customer_part_ids: Optional[Dict[str, str]] = Field(alias="customerPartIds", description="An optional map of customer part IDs to the respective business partner names.", default={})

class PartnerCatalogPartCreate(BaseModel):
    manufacturer_part_id: str = Field(alias="manufacturerPartId", description="The manufacturer part ID of the part to create a partner entry.")
    customer_part_id: str = Field(alias="customerPartId", description="The customer part ID for partner specific mapping of the catalog part.")
    business_partner_name: str = Field(alias="businessPartnerName", description="The unique name of the business partner to map the catalog part to.")

class BatchRead(CatalogPartRead):
    batch_id: str = Field(alias="batchId", description="The batch ID of the part.")

class BatchCreate(CatalogPartCreate):  
    batch_id: str = Field(alias="batchId", description="The batch ID of the part.")

class SerializedPartRead(CatalogPart):
    part_instance_id: str = Field(alias="partInstanceId", description="The part instance ID of the serialized part.")
    customer_part_id: str = Field(alias="customerPartId", description="The customer part ID of the part.")
    business_partner: BusinessPartner = Field(alias="businessPartner", description="The business partner to whom the part is being offered.")

class SerializedPartCreate(CatalogPart):
    part_instance_id: str = Field(alias="partInstanceId", description="The part instance ID of the serialized part.")
    customer_part_id: str = Field(alias="customerPartId", description="The customer part ID of the part.")
    business_partner_name: str = Field(alias="businessPartnerName", description="The unique name of the business partner to map the catalog part to.")

class JISPartRead(CatalogPart):
    jis_number: str = Field(alias="jisNumber", description="The JIS number of the JIS part.")
    parent_order_number: Optional[str] = Field(alias="parentOrderNumber", description="The parent order number of the JIS part.", default=None)
    jis_call_date: Optional[datetime] = Field(alias="jisCallDate", description="The JIS call date of the JIS part.", default=None)
    customer_part_id: str = Field(alias="customerPartId", description="The customer part ID of the part.")
    business_partner: BusinessPartner = Field(alias="businessPartner", description="The business partner to whom the part is being offered.")

class JISPartCreate(CatalogPart):
    jis_number: str = Field(description="The JIS number of the JIS part.")
    parent_order_number: Optional[str] = Field(description="The parent order number of the JIS part.", default=None)
    jis_call_date: Optional[datetime] = Field(description="The JIS call date of the JIS part.", default=None)
    customer_part_id: str = Field(alias="customerPartId", description="The customer part ID of the part.")
    business_partner_name: str = Field(alias="businessPartnerName", description="The unique name of the business partner to map the catalog part to.")