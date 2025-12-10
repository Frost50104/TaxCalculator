# Калькулятор налоговой нагрузки

Мини-веб-сервис на FastAPI для расчёта налоговой нагрузки по заданной модели.

Стек: Python 3.10+, FastAPI, Jinja2. Приложение stateless — каждый расчёт выполняется в отдельном HTTP‑запросе, данные не сохраняются в памяти и не записываются в сессии. Подходит для десятков одновременных пользователей (особенно при запуске uvicorn с несколькими воркерами).

## Запуск

1. Установить зависимости:

```
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2. Запустить сервер:

```
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Откройте http://localhost:8000 в браузере.

Для нагрузки используйте несколько воркеров, например:

```
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Структура проекта

- app/main.py — точка входа FastAPI и роуты (GET форма, POST расчёт)
- app/schemas.py — Pydantic‑схемы и валидация формы
- app/calculator.py — чистые функции с формулами, без зависимостей от FastAPI
- app/templates/ — Jinja2‑шаблоны (base.html, index.html)
- app/static/ — статические файлы (CSS)
- tests/test_calculator.py — юнит‑тесты для расчётных функций (pytest)
- requirements.txt — зависимости

## Валидация и интерфейс

- Все поля — числовые. Разрешены отрицательные значения только для субаренды (subrent) и итога инвентаризации (inventory_result) и для валовой прибыли (может быть отрицательной).
- Поле «Белый ФОТ» (white_payroll_override) — необязательное. Если пусто, используется 33% от ФОТ.
- При ошибках ввода под полями отображаются понятные сообщения.

## Бизнес‑логика (кратко)

Обозначения: T — оборот (turnover_total), GP — валовая прибыль (gross_profit).

Константы и производные:
- Роялти: royalty = T * 0.04
- Белый ФОТ: white_payroll = white_payroll_override > 0 ? override : payroll_total * 0.33
- Комиссия агрегаторов: aggregator_commission = turnover_aggregator * 0.35
- Фиксированный страховой взнос: fixed_insurance = 2900
- Эквайринг: acquiring = (T − turnover_aggregator) * 0.01 * 0.95

Затраты (expenses): сумма всех расходов согласно ТЗ (включая производные: royalty, aggregator_commission, fixed_insurance, acquiring).

Прибыль до налогообложения: profit_before_tax = GP − expenses.

Маржа: margin = T > 0 ? GP / T : None.

Рентабельность: profitability = T > 0 ? profit_before_tax / T : None.

Налогооблагаемая прибыль (taxable_profit):

```
taxable_profit = GP
  - (rent + subrent + electricity + other_utilities + royalty)
  - (white_payroll + aggregator_commission + fixed_insurance + acquiring
     + office_supplies + other_purchases_outside_opticom + write_offs
     + meal_compensation + other_write_offs)
  - (security + internet + maintenance + other_repairs + cash_service
     + mobile_connection + bank_services + uniform + fiscal_device
     + neo_service + garbage_cleaning + disinfection + promo_materials
     + inventory_result)
```

Налоги:
- АУСН: ausn_tax = max(taxable_profit * 0.20, T * 0.03)
- НДФЛ: ndfl_tax = white_payroll * 0.13
- Сумма налогов: total_tax = ausn_tax + ndfl_tax + fixed_insurance
- Нагрузка к обороту: tax_burden_vs_turnover = T > 0 ? total_tax / T : None
- Нагрузка к прибыли: tax_burden_vs_profit = profit_before_tax > 0 ? total_tax / profit_before_tax : None

Форматирование сумм — с разделителем тысяч, 0–2 знака после запятой.

## Примеры и тесты

Запустить тесты:

```
pytest -q
```

Пример входных данных (JSON для иллюстрации; веб‑форма соответствует этим полям):

```json
{
  "turnover_total": 1000000,
  "gross_profit": 300000,
  "turnover_aggregator": 200000,
  "rent": 100000,
  "subrent": 0,
  "electricity": 10000,
  "other_utilities": 5000,
  "payroll_total": 200000,
  "white_payroll_override": null,
  "office_supplies": 3000,
  "other_purchases_outside_opticom": 20000,
  "write_offs": 2000,
  "meal_compensation": 1000,
  "other_write_offs": 1000,
  "security": 5000,
  "internet": 1000,
  "maintenance": 2000,
  "other_repairs": 0,
  "cash_service": 1000,
  "mobile_connection": 1000,
  "bank_services": 2000,
  "uniform": 1000,
  "fiscal_device": 500,
  "neo_service": 0,
  "garbage_cleaning": 1000,
  "disinfection": 500,
  "promo_materials": 2000,
  "inventory_result": 0
}
```

Ожидаемые ключевые результаты (сверены тестами):
- royalty = 40 000; white_payroll = 66 000; aggregator_commission = 70 000; acquiring = 7 600
- expenses = 479 500; profit_before_tax = −179 500
- taxable_profit = −45 500; ausn_tax = 30 000; ndfl_tax = 8 580; total_tax = 41 480
- tax_burden_vs_turnover ≈ 4.148%; tax_burden_vs_profit — не рассчитывается (убыток)

## Примечание о stateless

Приложение не хранит пользовательские данные в памяти (без сессий, без глобальных переменных). Каждый расчёт — отдельный HTTP‑запрос. При использовании uvicorn с несколькими воркерами сервис обслуживает десятки одновременных пользователей.
