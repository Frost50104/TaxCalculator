from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class CalcForm(BaseModel):
    # Revenue and profit
    turnover_total: float = Field(..., ge=0, description="Оборот (в т.ч. агрегатор)")
    gross_profit: float = Field(..., description="Валовая прибыль (выручка - закупка)")
    # Not required in the form: default to 0 if not provided
    turnover_aggregator: float = Field(0, ge=0, description="Оборот агрегаторы")

    # Expenses
    rent: float = Field(0, ge=0)
    subrent: float = Field(0)  # may be negative
    electricity: float = Field(0, ge=0)
    other_utilities: float = Field(0, ge=0)
    payroll_total: float = Field(0, ge=0)
    white_payroll_override: Optional[float] = Field(None, ge=0)
    office_supplies: float = Field(0, ge=0)
    other_purchases_outside_opticom: float = Field(0, ge=0)
    write_offs: float = Field(0, ge=0)
    meal_compensation: float = Field(0, ge=0)
    other_write_offs: float = Field(0, ge=0)
    security: float = Field(0, ge=0)
    internet: float = Field(0, ge=0)
    maintenance: float = Field(0, ge=0)
    other_repairs: float = Field(0, ge=0)
    cash_service: float = Field(0, ge=0)
    mobile_connection: float = Field(0, ge=0)
    bank_services: float = Field(0, ge=0)
    uniform: float = Field(0, ge=0)
    fiscal_device: float = Field(0, ge=0)
    neo_service: float = Field(0, ge=0)
    garbage_cleaning: float = Field(0, ge=0)
    disinfection: float = Field(0, ge=0)
    promo_materials: float = Field(0, ge=0)
    inventory_result: float = Field(0)  # may be negative

    @field_validator("turnover_aggregator")
    @classmethod
    def _aggregator_not_negative(cls, v: float) -> float:
        # Field has ge=0 already; keep for custom message example
        if v < 0:
            raise ValueError("Оборот агрегатора не может быть отрицательным")
        return v

    @field_validator("turnover_total")
    @classmethod
    def _turnover_non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Оборот не может быть отрицательным")
        return v

    @field_validator("gross_profit")
    @classmethod
    def _gross_profit_number(cls, v: float) -> float:
        # Allow any float (может быть отрицательной), just ensure it's a number
        return float(v)

    @field_validator("turnover_aggregator")
    @classmethod
    def _aggregator_not_more_than_total(cls, v: float, info):
        data = info.data
        total = data.get("turnover_total")
        try:
            # total may be None when validating field order; skip in that case
            if total is not None and v > total:
                raise ValueError("Оборот агрегатора не должен превышать общий оборот")
        except Exception:
            pass
        return v
