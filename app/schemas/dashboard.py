from pydantic import BaseModel, Field
from typing import Optional, List

class DashboardData(BaseModel):
    # Placeholder schema
    pass

class FilterDashboardRequest(BaseModel):
    token: str
    body_type: Optional[str] = Field(None, alias="Bodytype")
    demand_level: Optional[str] = Field(None, alias="Demand level")
    vin: Optional[str] = Field(None, alias="VIN number")
    store: Optional[str] = Field(None, alias="Store")
    leads_per_day: Optional[str] = Field(None, alias="leads per day")

    class Config:
        allow_population_by_field_name = True

