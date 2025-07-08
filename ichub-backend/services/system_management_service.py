from typing import List, Optional
from models.services.system_management import (
    DtrServiceCreate,
    DtrServiceRead,
    DtrServiceUpdate,
    EdcServiceCreate,
    EdcServiceRead,
    EdcServiceUpdate,
    EnablementServiceStackCreate,
    EnablementServiceStackRead,
    EnablementServiceStackUpdate,
)
from managers.metadata_database.manager import RepositoryManagerFactory
from models.metadata_database.models import (
    DtrService,
    EdcService,
    EnablementServiceStack,
)

class SystemManagementService:
    """
    Service class for managing EnablementServiceStack entities.
    """
    def create_enablement_service_stack(self, stack_create: EnablementServiceStackCreate) -> EnablementServiceStackRead:
        with RepositoryManagerFactory.create() as repo:
            db_stack = EnablementServiceStack(**stack_create.model_dump(by_alias=False))
            repo.enablement_service_stack_repository.create(db_stack)
            repo.commit()
            return EnablementServiceStackRead.model_validate(db_stack)

    def get_enablement_service_stack(self, stack_id: int) -> Optional[EnablementServiceStackRead]:
        with RepositoryManagerFactory.create() as repo:
            db_stack = repo.enablement_service_stack_repository.find_by_id(stack_id)
            if db_stack:
                return EnablementServiceStackRead.model_validate(db_stack)
            return None

    def get_enablement_service_stacks(self) -> List[EnablementServiceStackRead]:
        with RepositoryManagerFactory.create() as repo:
            db_stacks = repo.enablement_service_stack_repository.find_all()
            return [EnablementServiceStackRead.model_validate(stack) for stack in db_stacks]

    def update_enablement_service_stack(self, stack_id: int, stack_update: EnablementServiceStackUpdate) -> Optional[EnablementServiceStackRead]:
        with RepositoryManagerFactory.create() as repo:
            db_stack = repo.enablement_service_stack_repository.find_by_id(stack_id)
            if not db_stack:
                return None
            for field, value in stack_update.model_dump(exclude_unset=True).items():
                setattr(db_stack, field, value)
            repo.commit()
            return EnablementServiceStackRead.model_validate(db_stack)

    def delete_enablement_service_stack(self, stack_id: int) -> bool:
        with RepositoryManagerFactory.create() as repo:
            try:
                repo.enablement_service_stack_repository.delete(stack_id)
                repo.commit()
                return True
            except ValueError:
                return False

    def create_edc_service(self, edc_create: EdcServiceCreate) -> EdcServiceRead:
        with RepositoryManagerFactory.create() as repo:
            db_edc = EdcService(**edc_create.model_dump(by_alias=False))
            repo.edc_service_repository.create(db_edc)
            repo.commit()
            return EdcServiceRead.model_validate(db_edc)

    def get_edc_service(self, edc_id: int) -> Optional[EdcServiceRead]:
        with RepositoryManagerFactory.create() as repo:
            db_edc = repo.edc_service_repository.find_by_id(edc_id)
            if db_edc:
                return EdcServiceRead.model_validate(db_edc)
            return None

    def get_edc_services(self) -> List[EdcServiceRead]:
        with RepositoryManagerFactory.create() as repo:
            db_edcs = repo.edc_service_repository.find_all()
            return [EdcServiceRead.model_validate(edc) for edc in db_edcs]

    def update_edc_service(self, edc_id: int, edc_update: EdcServiceUpdate) -> Optional[EdcServiceRead]:
        with RepositoryManagerFactory.create() as repo:
            db_edc = repo.edc_service_repository.find_by_id(edc_id)
            if not db_edc:
                return None
            for field, value in edc_update.model_dump(exclude_unset=True).items():
                setattr(db_edc, field, value)
            repo.commit()
            return EdcServiceRead.model_validate(db_edc)

    def delete_edc_service(self, edc_id: int) -> bool:
        with RepositoryManagerFactory.create() as repo:
            try:
                repo.edc_service_repository.delete(edc_id)
                repo.commit()
                return True
            except ValueError:
                return False

    def create_dtr_service(self, dtr_create: DtrServiceCreate) -> DtrServiceRead:
        with RepositoryManagerFactory.create() as repo:
            db_dtr = DtrService(**dtr_create.model_dump(by_alias=False))
            repo.dtr_service_repository.create(db_dtr)
            repo.commit()
            return DtrServiceRead.model_validate(db_dtr)

    def get_dtr_service(self, dtr_id: int) -> Optional[DtrServiceRead]:
        with RepositoryManagerFactory.create() as repo:
            db_dtr = repo.dtr_service_repository.find_by_id(dtr_id)
            if db_dtr:
                return DtrServiceRead.model_validate(db_dtr)
            return None

    def get_dtr_services(self) -> List[DtrServiceRead]:
        with RepositoryManagerFactory.create() as repo:
            db_dtrs = repo.dtr_service_repository.find_all()
            return [DtrServiceRead.model_validate(dtr) for dtr in db_dtrs]

    def update_dtr_service(self, dtr_id: int, dtr_update: DtrServiceUpdate) -> Optional[DtrServiceRead]:
        with RepositoryManagerFactory.create() as repo:
            db_dtr = repo.dtr_service_repository.find_by_id(dtr_id)
            if not db_dtr:
                return None
            for field, value in dtr_update.model_dump(exclude_unset=True).items():
                setattr(db_dtr, field, value)
            repo.commit()
            return DtrServiceRead.model_validate(db_dtr)

    def delete_dtr_service(self, dtr_id: int) -> bool:
        with RepositoryManagerFactory.create() as repo:
            try:
                repo.dtr_service_repository.delete(dtr_id)
                repo.commit()
                return True
            except ValueError:
                return False
