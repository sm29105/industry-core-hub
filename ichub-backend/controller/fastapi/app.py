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

from typing import List, Optional

from fastapi import FastAPI

from services.part_management_service import PartManagementService
from models.services.part_management import CatalogPartRead, CatalogPartCreate, PartnerCatalogPartBase

app = FastAPI(root_path="/frontend")

part_management_service = PartManagementService()

@app.get("/part-management/catalog-part/{manufacturer_id}/{manufacturer_part_id}", response_model=CatalogPartRead)
async def part_management_get_catalog_part(manufacturer_id: str, manufacturer_part_id: str) -> CatalogPartRead:
    return part_management_service.get_catalog_part(manufacturer_id, manufacturer_part_id)

@app.get("/part-management/catalog-part", response_model=List[CatalogPartRead])
async def part_management_get_catalog_parts() -> List[CatalogPartRead]:
    return part_management_service.get_catalog_parts()

@app.post("/part-management/catalog-part/{manufacturer_id}/{manufacturer_part_id}", response_model=CatalogPartRead)
async def part_management_create_catalog_part(manufacturer_id: str, manufacturer_part_id: str, customer_parts: Optional[List[PartnerCatalogPartBase]]) -> CatalogPartRead:
    return part_management_service.create_catalog_part_by_ids(manufacturer_id, manufacturer_part_id, customer_parts)

