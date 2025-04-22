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

from sqlmodel import SQLModel, Session, select
from typing import TypeVar, Type, List, Optional, Generic

from models.metadata_database.models import BusinessPartner, CatalogPart, LegalEntity, PartnerCatalogPart

ModelType = TypeVar("ModelType", bound=SQLModel)

class BaseRepository(Generic[ModelType]):
    def __init__(self, session: Session):
        self._session = session

    def __init_subclass__(cls) -> None:
        # Fetch the model type from the first argument of the generic class

        # pylint: disable=no-member
        cls._type = cls.__orig_bases__[0].__args__[0]  # type: ignore

    @classmethod
    def get_type(cls) -> Type[ModelType]:
        return cls._type  # type: ignore

    def create(self, obj_in: ModelType) -> ModelType:
        pass
    
    def find_by_id(self, obj_id: int) -> Optional[ModelType]:
        stmt = select(self.get_type()).where(
            self.get_type().id == obj_id)  # type: ignore
        return self._session.scalars(stmt).first()

    def find_all(self, offset: Optional[int] = None, limit: Optional[int] = 100) -> List[ModelType]:
        stmt = select(self.get_type())  # select(Author)
        if offset is not None:
            stmt = stmt.offset(offset)

        if limit is not None:
            stmt = stmt.limit(limit)

        result = self._session.scalars(stmt).unique()
        return list(result)

    def update(self, id: int, obj_in: dict) -> Optional[ModelType]:
        pass

    def commit(self) -> None:
        self._session.commit()

    def add(self, obj: ModelType, *, commit: bool = False) -> ModelType:
        self._session.add(obj)

        if commit:
            self._session.commit()
            self._session.refresh(obj)
        return obj
    
    def delete(self, obj_id: int, *, commit: bool = False) -> None:
        obj = self._session.get(self.get_type(), obj_id)
        if obj is None:
            err_msg = f'Object not found with id {obj_id}'
            raise ValueError(err_msg)
        self._session.delete(obj)
        if commit:
            self._session.commit()

class BusinessPartnerRepository(BaseRepository[BusinessPartner]):

    def get_by_name(self, name: str) -> Optional[BusinessPartner]:
        """
        Retrieve a business partner by its name.
        """
        # Logic to retrieve a business partner by name
        pass

    def get_by_bpnl(self, bpnl: str) -> Optional[BusinessPartner]:
        """
        Retrieve a business partner by its BPNL / Manufacturer ID.
        """
        # Logic to retrieve a business partner by BPNL
        pass

class CatalogPartRepository(BaseRepository[CatalogPart]):

    def get_by_manufacturer_id_manufacturer_part_id(self, manufacturer_id: str, manufacturer_part_id: str) -> Optional[CatalogPart]:
        """
        Retrieve a catalog part by its manufacturer ID and manufacturer part ID.
        """
        # Logic to retrieve a catalog part by manufacturer ID
        pass

class LegalEntityRepository(BaseRepository[LegalEntity]):

    def get_by_bpnl(self, bpnl: str) -> Optional[LegalEntity]:
        """
        Retrieve a legal entity by its BPNL.
        """
        # Logic to retrieve a legal entity by BPNL
        pass

class PartnerCatalogPartRepository(BaseRepository[PartnerCatalogPart]):

    def create(self, catalog_part: CatalogPart, business_partner: BusinessPartner, customer_part_id: str) -> PartnerCatalogPart:
        """
        Create a new partner catalog part.
        """
        # Logic to create a new partner catalog part
        pass
