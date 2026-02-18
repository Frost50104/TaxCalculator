"""
Pure calculation functions for UPPETIT tax burden calculator.

All functions are stateless and contain no framework-specific dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Any

# Annual and monthly fixed insurance contributions
# Business rule update: 2900 RUB per year -> use monthly share
ANNUAL_FIXED_INSURANCE_RUB = 2900.0
FIXED_INSURANCE_RUB = ANNUAL_FIXED_INSURANCE_RUB / 12.0


@dataclass(frozen=True)
class Inputs:
    # Revenue and profit
    turnover_total: float
    gross_profit: float
    turnover_aggregator: float

    # Expenses entered by user
    rent: float
    subrent: float  # may be negative
    electricity: float
    other_utilities: float
    payroll_total: float
    white_payroll_override: float | None
    office_supplies: float
    other_purchases_outside_opticom: float
    write_offs: float
    meal_compensation: float
    other_write_offs: float
    security: float
    internet: float
    maintenance: float
    other_repairs: float
    cash_service: float
    mobile_connection: float
    bank_services: float
    uniform: float
    fiscal_device: float
    neo_service: float
    garbage_cleaning: float
    disinfection: float
    promo_materials: float
    inventory_result: float  # may be negative


@dataclass(frozen=True)
class Derived:
    royalty: float
    white_payroll: float
    aggregator_commission: float
    fixed_insurance: float
    acquiring: float


@dataclass(frozen=True)
class Results:
    # Inputs echo
    inputs: Inputs

    # Derived values
    derived: Derived

    # Intermediates
    expenses: float
    profit_before_tax: float
    margin: Optional[float]
    profitability: Optional[float]

    # Tax base
    taxable_profit: float

    # Taxes
    ausn_tax: float
    ndfl_tax: float
    total_tax: float

    # Burden
    tax_burden_vs_turnover: Optional[float]
    tax_burden_vs_profit: Optional[float]


def compute_white_payroll(payroll_total: float, white_payroll_override: Optional[float]) -> float:
    """Compute "Белый ФОТ": override if > 0 else 0.33 * payroll_total.
    Negative override is treated as 0 (ignored).
    """
    if white_payroll_override is not None and white_payroll_override > 0:
        return float(white_payroll_override)
    return float(payroll_total) * 0.33


def derive_values(inp: Inputs) -> Derived:
    royalty = inp.turnover_total * 0.04
    white_payroll = compute_white_payroll(inp.payroll_total, inp.white_payroll_override)
    aggregator_commission = inp.turnover_aggregator * 0.35
    fixed_insurance = FIXED_INSURANCE_RUB
    acquiring = (inp.turnover_total - inp.turnover_aggregator) * 0.01 * 0.95
    return Derived(
        royalty=royalty,
        white_payroll=white_payroll,
        aggregator_commission=aggregator_commission,
        fixed_insurance=fixed_insurance,
        acquiring=acquiring,
    )


def calculate_expenses(inp: Inputs, d: Derived) -> float:
    # Sum according to specification (mapping of ranges)
    return (
        inp.rent
        + inp.subrent
        + inp.electricity
        + inp.other_utilities
        + inp.payroll_total
        + d.royalty
        + d.aggregator_commission
        + d.fixed_insurance
        + d.acquiring
        + inp.office_supplies
        + inp.other_purchases_outside_opticom
        + inp.write_offs
        + inp.meal_compensation
        + inp.other_write_offs
        + inp.security
        + inp.internet
        + inp.maintenance
        + inp.other_repairs
        + inp.cash_service
        + inp.mobile_connection
        + inp.bank_services
        + inp.uniform
        + inp.fiscal_device
        + inp.neo_service
        + inp.garbage_cleaning
        + inp.disinfection
        + inp.promo_materials
        + inp.inventory_result
    )


def calculate_taxable_profit(inp: Inputs, d: Derived) -> float:
    gp = inp.gross_profit

    group_a = inp.rent + inp.subrent + inp.electricity + inp.other_utilities + d.royalty
    group_b = (
        d.white_payroll
        + d.aggregator_commission
        + d.fixed_insurance
        + d.acquiring
        + inp.office_supplies
        + inp.other_purchases_outside_opticom
        + inp.write_offs
        + inp.meal_compensation
        + inp.other_write_offs
    )
    group_c = (
        inp.security
        + inp.internet
        + inp.maintenance
        + inp.other_repairs
        + inp.cash_service
        + inp.mobile_connection
        + inp.bank_services
        + inp.uniform
        + inp.fiscal_device
        + inp.neo_service
        + inp.garbage_cleaning
        + inp.disinfection
        + inp.promo_materials
        + inp.inventory_result
    )

    return gp - group_a - group_b - group_c


def calculate_all(inp: Inputs) -> Results:
    d = derive_values(inp)
    expenses = calculate_expenses(inp, d)
    profit_before_tax = inp.gross_profit - expenses
    margin = (inp.gross_profit / inp.turnover_total) if inp.turnover_total > 0 else None
    profitability = (profit_before_tax / inp.turnover_total) if inp.turnover_total > 0 else None
    taxable_profit = calculate_taxable_profit(inp, d)
    ausn_tax = max(taxable_profit * 0.20, inp.turnover_total * 0.03)
    ndfl_tax = d.white_payroll * 0.13
    total_tax = ausn_tax + ndfl_tax + d.fixed_insurance
    tax_burden_vs_turnover = (total_tax / inp.turnover_total) if inp.turnover_total > 0 else None
    tax_burden_vs_profit = (total_tax / profit_before_tax) if profit_before_tax > 0 else None

    return Results(
        inputs=inp,
        derived=d,
        expenses=expenses,
        profit_before_tax=profit_before_tax,
        margin=margin,
        profitability=profitability,
        taxable_profit=taxable_profit,
        ausn_tax=ausn_tax,
        ndfl_tax=ndfl_tax,
        total_tax=total_tax,
        tax_burden_vs_turnover=tax_burden_vs_turnover,
        tax_burden_vs_profit=tax_burden_vs_profit,
    )


def format_money(value: Optional[float]) -> str:
    """Format number with thousand separator and 0–2 decimals (trim trailing zeros).
    Uses space as thousands separator. If value is None, returns '-'.
    """
    if value is None:
        return "-"
    rounded = f"{value:,.2f}"  # uses comma for thousands, dot for decimal
    # Replace comma thousands with space
    rounded = rounded.replace(",", " ")
    # Trim trailing zeros and dot
    if "." in rounded:
        rounded = rounded.rstrip("0").rstrip(".")
    return rounded


def format_percent(value: Optional[float]) -> str:
    if value is None:
        return "-"
    percent = value * 100.0
    txt = f"{percent:,.2f}".replace(",", " ")
    txt = txt.rstrip("0").rstrip(".")
    return f"{txt}%"


def as_dict(results: Results) -> Dict[str, Any]:
    """Convenience conversion for templates/tests if needed."""
    return {
        "expenses": results.expenses,
        "profit_before_tax": results.profit_before_tax,
        "margin": results.margin,
        "profitability": results.profitability,
        "taxable_profit": results.taxable_profit,
        "ausn_tax": results.ausn_tax,
        "ndfl_tax": results.ndfl_tax,
        "total_tax": results.total_tax,
        "tax_burden_vs_turnover": results.tax_burden_vs_turnover,
        "tax_burden_vs_profit": results.tax_burden_vs_profit,
        "derived": {
            "royalty": results.derived.royalty,
            "white_payroll": results.derived.white_payroll,
            "aggregator_commission": results.derived.aggregator_commission,
            "fixed_insurance": results.derived.fixed_insurance,
            "acquiring": results.derived.acquiring,
        },
    }
