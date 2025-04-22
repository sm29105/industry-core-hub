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

from sqlmodel import SQLModel
from typing import TypeVar, Type, List, Optional, Generic

from models.metadata_database.models import BusinessPartner, CatalogPart, LegalEntity, PartnerCatalogPart

ModelType = TypeVar("ModelType", bound=SQLModel)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def create(self, obj_in: ModelType) -> ModelType:
        pass
    
    async def get(self, id: int) -> Optional[ModelType]:
        pass

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        pass

    async def update(self, id: int, obj_in: dict) -> Optional[ModelType]:
        pass

    async def delete(self, id: int) -> bool:
        pass

class BusinessPartnerRepository(BaseRepository[BusinessPartner]):
    def __init__(self):
        super().__init__(BusinessPartner)

    async def get_by_name(self, name: str) -> Optional[BusinessPartner]:
        """
        Retrieve a business partner by its name.
        """
        # Logic to retrieve a business partner by name
        pass

    async def get_by_bpnl(self, bpnl: str) -> Optional[BusinessPartner]:
        """
        Retrieve a business partner by its BPNL / Manufacturer ID.
        """
        # Logic to retrieve a business partner by BPNL
        pass

class CatalogPartRepository(BaseRepository[CatalogPart]):
    def __init__(self):
        super().__init__(CatalogPart)

    async def get_by_manufacturer_id_manufactuer_part_id(self, manufacturer_id: str, manufacturer_part_id: str) -> Optional[CatalogPart]:
        """
        Retrieve a catalog part by its manufacturer ID and manufacturer part ID.
        """
        # Logic to retrieve a catalog part by manufacturer ID
        pass

class LegalEntityRepository(BaseRepository[LegalEntity]):
    def __init__(self):
        super().__init__(LegalEntity)

    async def get_by_bpnl(self, bpnl: str) -> Optional[LegalEntity]:
        """
        Retrieve a legal entity by its BPNL.
        """
        # Logic to retrieve a legal entity by BPNL
        pass

class PartnerCatalogPartRepository(BaseRepository[PartnerCatalogPart]):
    def __init__(self):
        super().__init__(PartnerCatalogPart)

    async def create(self, catalog_part: CatalogPart, business_partner: BusinessPartner, customer_part_id: str) -> PartnerCatalogPart:
        """
        Create a new partner catalog part.
        """
        # Logic to create a new partner catalog part
        pass
