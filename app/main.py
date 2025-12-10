from __future__ import annotations

from typing import Any, Dict, Optional
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

# Support running both as a package (uvicorn app.main:app) and as a script (python app/main.py)
try:  # package-relative imports (preferred when loaded as app.main)
    from .schemas import CalcForm
    from .calculator import (
        Inputs,
        calculate_all,
        format_money,
        format_percent,
    )
except ImportError:  # fallback for direct script execution
    import sys as _sys
    # Add the project root (parent of this file's directory) to sys.path
    _sys.path.append(str(Path(__file__).resolve().parent.parent))
    from app.schemas import CalcForm  # type: ignore
    from app.calculator import (  # type: ignore
        Inputs,
        calculate_all,
        format_money,
        format_percent,
    )


app = FastAPI(title="Калькулятор налоговой нагрузки UPPETIT")

# Resolve absolute paths for static and templates to work regardless of CWD
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
templates.env.filters["money"] = format_money
templates.env.filters["percent"] = format_percent


def _to_inputs(data: CalcForm) -> Inputs:
    return Inputs(
        turnover_total=data.turnover_total,
        gross_profit=data.gross_profit,
        turnover_aggregator=data.turnover_aggregator,
        rent=data.rent,
        subrent=data.subrent,
        electricity=data.electricity,
        other_utilities=data.other_utilities,
        payroll_total=data.payroll_total,
        white_payroll_override=data.white_payroll_override,
        office_supplies=data.office_supplies,
        other_purchases_outside_opticom=data.other_purchases_outside_opticom,
        write_offs=data.write_offs,
        meal_compensation=data.meal_compensation,
        other_write_offs=data.other_write_offs,
        security=data.security,
        internet=data.internet,
        maintenance=data.maintenance,
        other_repairs=data.other_repairs,
        cash_service=data.cash_service,
        mobile_connection=data.mobile_connection,
        bank_services=data.bank_services,
        uniform=data.uniform,
        fiscal_device=data.fiscal_device,
        neo_service=data.neo_service,
        garbage_cleaning=data.garbage_cleaning,
        disinfection=data.disinfection,
        promo_materials=data.promo_materials,
        inventory_result=data.inventory_result,
    )


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    context: Dict[str, Any] = {
        "request": request,
        "data": {},
        "errors": {},
        "results": None,
    }
    return templates.TemplateResponse("index.html", context)


@app.post("/", response_class=HTMLResponse)
async def calculate(request: Request):
    form = await request.form()

    # Convert empty strings to None for optional fields
    def parse_optional_float(value: Optional[str]) -> Optional[float]:
        if value is None:
            return None
        s = str(value).strip()
        if s == "":
            return None
        try:
            return float(s.replace(" ", "").replace(",", "."))
        except ValueError:
            return float("nan")  # will trigger pydantic validation error

    # Prepare raw payload: try to pass strings; Pydantic will coerce and validate
    payload: Dict[str, Any] = {}
    for key in CalcForm.model_fields.keys():
        raw = form.get(key)
        if key == "white_payroll_override":
            payload[key] = parse_optional_float(raw)
        else:
            if raw is None or str(raw).strip() == "":
                # Missing -> use default 0 for optional fields; for required keep None
                if key in ("turnover_total", "gross_profit", "turnover_aggregator"):
                    payload[key] = None
                else:
                    payload[key] = 0
            else:
                try:
                    payload[key] = float(str(raw).replace(" ", "").replace(",", "."))
                except ValueError:
                    payload[key] = raw  # let pydantic raise a clear error

    errors: Dict[str, str] = {}
    data_out: Dict[str, Any] = payload.copy()
    results = None

    try:
        data = CalcForm(**payload)
        inputs = _to_inputs(data)
        results = calculate_all(inputs)
    except ValidationError as ve:
        for err in ve.errors():
            loc = err.get("loc", [])
            if loc:
                field = loc[-1]
                msg = err.get("msg", "Некорректное значение")
                errors[str(field)] = msg

    context: Dict[str, Any] = {
        "request": request,
        "data": data_out,
        "errors": errors,
        "results": results,
    }
    return templates.TemplateResponse("index.html", context)


# Uvicorn entrypoint hint: uvicorn app.main:app

if __name__ == "__main__":
    # Allow running via: python app/main.py
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
