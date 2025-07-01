from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

class AvailabilityStatus(str, Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    ON_LEAVE = "on_leave"

class Employee(BaseModel):
    id: int
    name: str
    skills: List[str]
    experience_years: int
    projects: List[str]
    availability: AvailabilityStatus
    department: Optional[str] = None
    location: Optional[str] = None
    specializations: Optional[List[str]] = None

class ChatQuery(BaseModel):
    query: str
    max_results: Optional[int] = 5

class ChatResponse(BaseModel):
    response: str
    matched_employees: List[Employee]
    confidence_score: float

class SearchFilters(BaseModel):
    skills: Optional[List[str]] = None
    min_experience: Optional[int] = None
    max_experience: Optional[int] = None
    availability: Optional[AvailabilityStatus] = None
    department: Optional[str] = None
