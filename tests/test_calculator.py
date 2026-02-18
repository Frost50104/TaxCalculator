import math

from app.calculator import Inputs, calculate_all, compute_white_payroll, FIXED_INSURANCE_RUB


def approx(a, b, tol=1e-6):
    return abs(a - b) <= tol


def test_compute_white_payroll_override_and_default():
    assert compute_white_payroll(100_000, None) == 33_000
    assert compute_white_payroll(120_000, 50_000) == 50_000
    # Negative override ignored -> default 33%
    assert compute_white_payroll(90_000, -1) == 29_700


def test_full_calculation_normal_case():
    inp = Inputs(
        turnover_total=1_000_000.0,
        gross_profit=300_000.0,
        turnover_aggregator=200_000.0,
        rent=100_000.0,
        subrent=0.0,
        electricity=10_000.0,
        other_utilities=5_000.0,
        payroll_total=200_000.0,
        white_payroll_override=None,
        office_supplies=3_000.0,
        other_purchases_outside_opticom=20_000.0,
        write_offs=2_000.0,
        meal_compensation=1_000.0,
        other_write_offs=1_000.0,
        security=5_000.0,
        internet=1_000.0,
        maintenance=2_000.0,
        other_repairs=0.0,
        cash_service=1_000.0,
        mobile_connection=1_000.0,
        bank_services=2_000.0,
        uniform=1_000.0,
        fiscal_device=500.0,
        neo_service=0.0,
        garbage_cleaning=1_000.0,
        disinfection=500.0,
        promo_materials=2_000.0,
        inventory_result=0.0,
    )

    res = calculate_all(inp)

    # Derived checks
    assert approx(res.derived.royalty, 40_000.0)
    assert approx(res.derived.white_payroll, 66_000.0)
    assert approx(res.derived.aggregator_commission, 70_000.0)
    assert approx(res.derived.fixed_insurance, FIXED_INSURANCE_RUB)
    assert approx(res.derived.acquiring, 7_600.0)

    # Intermediates
    assert approx(res.expenses, 476_841.6666666667)
    assert approx(res.profit_before_tax, -176_841.6666666667)
    assert approx(res.margin or 0, 0.3)
    assert approx(res.profitability or -0.17684166666666667, -0.17684166666666667)

    # Tax base and taxes
    assert approx(res.taxable_profit, -42_841.666666666664)
    assert approx(res.ausn_tax, 30_000.0)
    assert approx(res.ndfl_tax, 8_580.0)
    assert approx(res.total_tax, 38_821.666666666664)

    # Burden
    assert approx(res.tax_burden_vs_turnover or 0, 0.03882166666666666)
    assert res.tax_burden_vs_profit is None


def test_zero_turnover_edge_cases():
    inp = Inputs(
        turnover_total=0.0,
        gross_profit=10_000.0,
        turnover_aggregator=0.0,
        rent=0.0,
        subrent=0.0,
        electricity=0.0,
        other_utilities=0.0,
        payroll_total=0.0,
        white_payroll_override=None,
        office_supplies=0.0,
        other_purchases_outside_opticom=0.0,
        write_offs=0.0,
        meal_compensation=0.0,
        other_write_offs=0.0,
        security=0.0,
        internet=0.0,
        maintenance=0.0,
        other_repairs=0.0,
        cash_service=0.0,
        mobile_connection=0.0,
        bank_services=0.0,
        uniform=0.0,
        fiscal_device=0.0,
        neo_service=0.0,
        garbage_cleaning=0.0,
        disinfection=0.0,
        promo_materials=0.0,
        inventory_result=0.0,
    )
    res = calculate_all(inp)
    # No division by zero
    assert res.margin is None
    assert res.profitability is None
    # Taxable profit = GP - fixed_insurance (в формуле налоговой базы он вычитается)
    assert approx(res.taxable_profit, 9758.333333333332)
    # AUSN = max(9758.33*20%, 0) = 1 951.6666...
    assert approx(res.ausn_tax, 1951.6666666666665)
    # Total tax = AUSN + NDFL (0) + fixed_insurance
    assert approx(res.total_tax, 1951.6666666666665 + 0.0 + FIXED_INSURANCE_RUB)
    # No turnover -> burden vs turnover is None
    assert res.tax_burden_vs_turnover is None
