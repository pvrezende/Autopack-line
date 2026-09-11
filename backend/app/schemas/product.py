from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    sku: str = Field(min_length=1, max_length=100)
    ean: str | None = Field(default=None, max_length=14)
    model: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=150)
    capacity_btu: int | None = Field(default=None, gt=0)
    active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    sku: str | None = Field(default=None, min_length=1, max_length=100)
    ean: str | None = Field(default=None, max_length=14)
    model: str | None = Field(default=None, min_length=1, max_length=100)
    name: str | None = Field(default=None, min_length=1, max_length=150)
    capacity_btu: int | None = Field(default=None, gt=0)
    active: bool | None = None


class ProductRead(ProductBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
