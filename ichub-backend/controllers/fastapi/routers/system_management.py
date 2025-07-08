from fastapi import APIRouter
from typing import List
from services.system_management_service import SystemManagementService
from tools.exceptions import NotFoundError
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

router = APIRouter(prefix="/system-management", tags=["System Management"])
system_management_service = SystemManagementService()

@router.post("/enablement-service-stack", response_model=EnablementServiceStackRead)
def create_enablement_service_stack(stack_create: EnablementServiceStackCreate):
    return system_management_service.create_enablement_service_stack(stack_create)

@router.get("/enablement-service-stack", response_model=List[EnablementServiceStackRead])
def get_enablement_service_stacks():
    return system_management_service.get_enablement_service_stacks()

@router.get("/enablement-service-stack/{stack_id}", response_model=EnablementServiceStackRead)
def get_enablement_service_stack(stack_id: int):
    return system_management_service.get_enablement_service_stack(stack_id)

@router.put("/enablement-service-stack/{stack_id}", response_model=EnablementServiceStackRead)
def update_enablement_service_stack(stack_id: int, stack_update: EnablementServiceStackUpdate):
    return system_management_service.update_enablement_service_stack(stack_id, stack_update)

@router.delete("/enablement-service-stack/{stack_id}", response_model=bool)
def delete_enablement_service_stack(stack_id: int):
    return system_management_service.delete_enablement_service_stack(stack_id)

# EDC Service endpoints
@router.post("/edc-service", response_model=EdcServiceRead)
def create_edc_service(edc_create: EdcServiceCreate):
    return system_management_service.create_edc_service(edc_create)

@router.get("/edc-service", response_model=List[EdcServiceRead])
def get_edc_services():
    return system_management_service.get_edc_services()

@router.get("/edc-service/{edc_id}", response_model=EdcServiceRead)
def get_edc_service(edc_id: int):
    return system_management_service.get_edc_service(edc_id)

@router.put("/edc-service/{edc_id}", response_model=EdcServiceRead)
def update_edc_service(edc_id: int, edc_update: EdcServiceUpdate):
    return system_management_service.update_edc_service(edc_id, edc_update)

@router.delete("/edc-service/{edc_id}", response_model=bool)
def delete_edc_service(edc_id: int):
    return system_management_service.delete_edc_service(edc_id)

# DTR Service endpoints
@router.post("/dtr-service", response_model=DtrServiceRead)
def create_dtr_service(dtr_create: DtrServiceCreate):
    return system_management_service.create_dtr_service(dtr_create)

@router.get("/dtr-service", response_model=List[DtrServiceRead])
def get_dtr_services():
    return system_management_service.get_dtr_services()

@router.get("/dtr-service/{dtr_id}", response_model=DtrServiceRead)
def get_dtr_service(dtr_id: int):
    return system_management_service.get_dtr_service(dtr_id)

@router.put("/dtr-service/{dtr_id}", response_model=DtrServiceRead)
def update_dtr_service(dtr_id: int, dtr_update: DtrServiceUpdate):
    return system_management_service.update_dtr_service(dtr_id, dtr_update)

@router.delete("/dtr-service/{dtr_id}", response_model=bool)
def delete_dtr_service(dtr_id: int):
    return system_management_service.delete_dtr_service(dtr_id)

