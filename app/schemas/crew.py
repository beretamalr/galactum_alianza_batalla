from pydantic import BaseModel

class CrewAssignRequest(BaseModel):
    slot_id: int

class CrewSpecializeRequest(BaseModel):
    specialization_id: int

class AcquireCrewRequest(BaseModel):
    crew_template_id: str

class UpgradeCrewRequest(BaseModel):
    crew_instance_id: int
