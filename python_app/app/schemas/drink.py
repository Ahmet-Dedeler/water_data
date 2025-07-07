from pydantic import BaseModel
from typing import Optional

class DrinkTypeBase(BaseModel):
    name: str
    hydration_multiplier: float = 1.0

class DrinkTypeCreate(DrinkTypeBase):
    pass

class DrinkType(DrinkTypeBase):
    id: int

    class Config:
        orm_mode = True 