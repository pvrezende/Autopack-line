from pydantic import BaseModel, ConfigDict, Field


class ProductionLineCreate(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=255)
    active: bool = True


class ProductionLineRead(ProductionLineCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)
