from pydantic import BaseModel
from typing import List, Optional


class TravelerState(BaseModel):
    name: Optional[str] = None
    nationality: Optional[str] = None
    budget: Optional[float] = None
    currency: Optional[str] = 'INR'
    trip_duration: Optional[int] = None
    travelers: int = 1
    interests: List[str] = []
    preferred_region: Optional[str] = None
    last_destination: Optional[str] = None
    travel_dates: Optional[str] = None
