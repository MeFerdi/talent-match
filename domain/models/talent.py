from pydantic import BaseModel, Field

class Talent(BaseModel):
    talent_id: str
    available: bool = True
    rating: float = Field(ge=0, le=5)