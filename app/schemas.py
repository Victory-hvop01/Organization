from pydantic import BaseModel
from typing import List, Optional


class PhoneBase(BaseModel):
    number: str


class ActivityBase(BaseModel):
    name: str


class Activity(ActivityBase):
    id: int

    class Config:
        from_attributes = True


class BuildingBase(BaseModel):
    address: str
    latitude: float
    longitude: float


class Building(BuildingBase):
    id: int

    class Config:
        from_attributes = True


class OrganizationBase(BaseModel):
    name: str
    building_id: int


class OrganizationCreate(OrganizationBase):
    phones: List[PhoneBase] = []
    activity_ids: List[int] = []


class Organization(OrganizationBase):
    id: int
    phones: List[PhoneBase] = []
    activities: List[Activity] = []
    building: Building

    class Config:
        from_attributes = True