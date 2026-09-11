from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class IndicatorThresholdUpsert(BaseModel):
    line_id: int = Field(gt=0)
    product_id: int | None = Field(default=None, gt=0)
    availability_warning: Decimal = Field(ge=0, le=100)
    availability_critical: Decimal = Field(ge=0, le=100)
    performance_warning: Decimal = Field(ge=0, le=100)
    performance_critical: Decimal = Field(ge=0, le=100)
    quality_warning: Decimal = Field(ge=0, le=100)
    quality_critical: Decimal = Field(ge=0, le=100)
    oee_warning: Decimal = Field(ge=0, le=100)
    oee_critical: Decimal = Field(ge=0, le=100)

    @model_validator(mode="after")
    def validate_ranges(self):
        pairs = [
            (self.availability_critical, self.availability_warning, "Disponibilidade"),
            (self.performance_critical, self.performance_warning, "Performance"),
            (self.quality_critical, self.quality_warning, "Qualidade"),
            (self.oee_critical, self.oee_warning, "OEE"),
        ]
        for critical, warning, label in pairs:
            if critical > warning:
                raise ValueError(f"Limite crítico de {label} deve ser menor ou igual ao limite de atenção")
        return self


class IndicatorThresholdRead(IndicatorThresholdUpsert):
    id: int
    active: bool
    valid_from: datetime
    valid_until: datetime | None
    model_config = ConfigDict(from_attributes=True)
