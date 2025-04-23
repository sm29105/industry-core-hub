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

from typing import Dict, List, Optional
from models.services.part_management import BatchCreate, BatchRead, CatalogPartCreate, CatalogPartDelete, CatalogPartRead, JISPartCreate, JISPartDelete, JISPartRead, PartnerCatalogPartBase, PartnerCatalogPartCreate, PartnerCatalogPartDelete, SerializedPartCreate, SerializedPartDelete, SerializedPartRead
from models.services.partner_management import BusinessPartner
from managers.metadata_database.repositories import CatalogPartRepository, BusinessPartnerRepository, LegalEntityRepository, PartnerCatalogPartRepository
from managers.metadata_database.manager import RepositoryManager, RepositoryManagerFactory
from models.metadata_database.models import CatalogPart, Batch, SerializedPart, JISPart

class PartManagementService():
    """
    Service class for managing parts and their relationships in the system.
    """

    def __init__(self, ):
        self.repositories = RepositoryManagerFactory.create()

    def create_catalog_part(self, catalog_part_create: CatalogPartCreate) -> CatalogPartRead:
        """
        Create a new catalog part in the system.
        Optionally also create attached partner catalog parts - i.e. partner specific mappings of the catalog part.
        """
        with self.repositories as repos:
            
            # First check if the legal entity exists for the given manufacturer ID
            db_legal_entity = repos.legal_entity_repository.get_by_bpnl(catalog_part_create.manufacturer_id)
            if not db_legal_entity:
                raise ValueError(f"Legal Entity with manufacturer BPNL '{catalog_part_create.manufacturer_id}' does not exist. Please create it first.")

            # Check if the catalog part already exists
            db_catalog_part = repos.catalog_part_repository.get_by_manufacturer_id_manufacturer_part_id(
                catalog_part_create.manufacturer_id, catalog_part_create.manufacturer_part_id
            )
            if db_catalog_part:
                raise ValueError("Catalog part already exists.")
            else:
                # Create the catalog part in the metadata database
                db_catalog_part = CatalogPart(
                    manufacturer_part_id=catalog_part_create.manufacturer_part_id,
                    legal_entity=db_legal_entity
                )
                repos.catalog_part_repository.create(db_catalog_part)

            # Prepare the result object
            result = CatalogPartRead(
                manufacturerId=catalog_part_create.manufacturer_id,
                manufacturerPartId=catalog_part_create.manufacturer_part_id)

            # Check if we already should create some customer part IDs for the given catalog part
            if catalog_part_create.customer_part_ids:
                for partner_catalog_part_create in catalog_part_create.customer_part_ids:
                    
                    # We need both the customer part ID and the name of the business partner
                    if not partner_catalog_part_create.customer_part_id:
                        raise ValueError("Customer part ID is required for a customer part mapping.")
                    
                    if not partner_catalog_part_create.business_partner_name:
                        raise ValueError("Business partner name is required for a customer part mapping.")
                    
                    # Resolve the business partner by name from the metadata database
                    db_business_partner = repos.business_partner_repository.get_by_name(partner_catalog_part_create.business_partner_name)
                    if not db_business_partner:
                        raise ValueError(f"Business partner '{partner_catalog_part_create.business_partner_name}' does not exist. Please create it first.")

                    # Create the partner catalog part entry in the metadata database
                    repos.partner_catalog_part_repository.create(db_catalog_part, db_business_partner, partner_catalog_part_create.customer_part_id)
                    # TODO: error handling (issue: if one customer part ID fails, all should fail???)

                    result.customer_part_ids[partner_catalog_part_create.customer_part_id] = BusinessPartner(name = db_business_partner.name, bpnl = db_business_partner.bpnl)  

            return result

    def create_catalog_part_by_ids(self, manufacturer_id: str, manufacturer_part_id: str, customer_parts: Optional[List[PartnerCatalogPartBase]]) -> CatalogPartRead:
        """Convenience method to create a catalog part by its IDs."""

        partner_catalog_parts = []
        for partner_catalog_part in customer_parts:
            partner_catalog_part = PartnerCatalogPartBase(
                customer_part_id=partner_catalog_part.customer_part_id,
                business_partner_name=partner_catalog_part.business_partner_name
            )
            partner_catalog_parts.append(partner_catalog_part)

        catalog_part_create = CatalogPartCreate(
            manufacturer_id=manufacturer_id,
            manufacturer_part_id=manufacturer_part_id,
            customer_part_ids=partner_catalog_parts
        )

        self.create_catalog_part(catalog_part_create)


    def delete_catalog_part(self, catlog_part: CatalogPartDelete) -> None:
        """
        Delete a catalog part from the system.
        """
        # Logic to delete a catalog part
        pass

    def get_catalog_part(self, manufacturer_id: str, manufacturer_part_id: str) -> Optional[CatalogPartRead]:
        with self.repositories as repos:
            db_catalog_part: Optional[CatalogPart] = repos.catalog_part_repository.get_by_manufacturer_id_manufacturer_part_id(
                manufacturer_id, manufacturer_part_id
            )
            
            if not db_catalog_part:
                return None
            else:
                customer_parts: Dict[str, BusinessPartner] = {}

                if db_catalog_part.partner_catalog_parts:
                    for db_partner_catalog_part in db_catalog_part.partner_catalog_parts:
                        customer_parts[db_partner_catalog_part.customer_part_id] = BusinessPartner(
                            name=db_partner_catalog_part.business_partner.name,
                            bpnl=db_partner_catalog_part.business_partner.bpnl
                        )

                return CatalogPartRead(
                    legal_entity_bpnl=db_catalog_part.legal_entity.bpnl,
                    manufacturer_part_id=db_catalog_part.manufacturer_part_id,
                    customer_part_ids=customer_parts
                )
            

    def get_catalog_parts(self, manufacturer_id: str = None, manufacturer_part_id: str = None) -> List[CatalogPartRead]:
        """
        Retrieves catalog parts from the system according to given parameters.
        """
        
        # Logic to retrieve all catalog parts
        pass

    def create_batch(self, batch_create: BatchCreate) -> BatchRead:
        """
        Create a new batch in the system.
        """
        
        # Logic to create a batch
        pass

    def delete_batch(self, batch: BatchRead) -> None:
        """
        Delete a batch from the system.
        """
        
        # Logic to delete a batch
        pass

    def get_batch(self, manufacturer_id: str, manufacturer_part_id: str, batch_id: str) -> BatchRead:
        """
        Retrieve a batch from the system.
        """
        
        # Logic to retrieve a batch
        pass

    def get_batches(self, manufacturer_id: str = None, manufacturer_part_id = None, batch_id: str = None) -> List[BatchRead]:
        """
        Retrieves batches from the system according to given parameters.
        """

        pass

    def create_serialized_part(self, serialized_part_create: SerializedPartCreate) -> SerializedPartRead:
        """
        Create a new serialized part in the system.
        """
        
        # Logic to create a serialized part
        pass

    def delete_serialized_part(self, serialized_part: SerializedPartDelete) -> None:
        """
        Delete a serialized part from the system.
        """
        
        # Logic to delete a serialized part
        pass

    def get_serialized_part(self, manufacturer_id: str, manufacturer_part_id: str, part_instance_id: str) -> SerializedPartRead:
        """
        Retrieve a serialized part from the system.
        """
        
        # Logic to retrieve a serialized part
        pass

    def get_serialized_parts(self, manufacturer_id: str = None, manufacturer_part_id: str = None, part_instance_id: str = None) -> List[SerializedPartRead]:
        """
        Retrieves serialized parts from the system according to given parameters.
        """
        
        # Logic to retrieve all serialized parts
        pass

    def create_jis_part(self, jis_part_create: JISPartCreate) -> JISPartRead:
        """
        Create a new JIS part in the system.
        """
        
        # Logic to create a JIS part
        pass

    def delete_jis_part(self, jis_part: JISPartDelete) -> None:
        """
        Delete a JIS part from the system.
        """
        
        # Logic to delete a JIS part
        pass

    def get_jis_part(self, manufacturer_id: str, manufacturer_part_id: str, jis_number: str) -> JISPartRead:
        """
        Retrieve a JIS part from the system.
        """
        
        # Logic to retrieve a JIS part
        pass

    def get_jis_parts(self, manufacturer_id: str = None, manufacturer_part_id: str = None, jis_number: str = None) -> List[JISPartRead]:
        """
        Retrieves JIS parts from the system according to given parameters.
        """
        
        # Logic to retrieve all JIS parts
        pass

    def create_partner_catalog_part_mapping(self, partner_catalog_part_create: PartnerCatalogPartCreate) -> CatalogPartRead:
        """
        Create a new partner catalog part in the system.
        """
        
        # Logic to create a partner catalog part
        pass

    def delete_partner_catalog_part_mapping(self, partner_catalog_part: PartnerCatalogPartDelete) -> CatalogPartRead:
        """
        Delete a partner catalog part from the system.
        """
        
        # Logic to delete a partner catalog part
        pass