"""
Task definitions and graders for the Data Cleaning environment.

Each task contains:
- name: unique task identifier
- description: human-readable description of issues to fix
- dirty_data: the messy input data (list of dicts)
- max_steps: maximum steps allowed
- grader: function(current_data) -> float score in [0, 1]
"""

import copy
import re
from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# Task 1: fix_types (Easy)
# ---------------------------------------------------------------------------

TASK_FIX_TYPES_DATA = [
    {"id": "1.0", "name": "Alice Smith", "age": "28", "salary": "75000", "hire_date": "2023/01/15"},
    {"id": "2.0", "name": "Bob Jones", "age": "thirty-five", "salary": "82000", "hire_date": "2022-03-20"},
    {"id": "3.0", "name": "Carol White", "age": "42", "salary": "ninety thousand", "hire_date": "2021/06/01"},
    {"id": "4.0", "name": "David Brown", "age": "31", "salary": "68000", "hire_date": "01-15-2024"},
    {"id": "5.0", "name": "Eve Davis", "age": "29", "salary": "71000", "hire_date": "2023/11/30"},
]

TASK_FIX_TYPES_DESC = """Fix data type errors in this employee dataset.

Current data has these issues:
- 'id' column contains float strings like '1.0' — should be integers (1, 2, 3...)
- 'age' column has string values — should be integers. Note: 'thirty-five' = 35
- 'salary' column has string values — should be integers. Note: 'ninety thousand' = 90000
- 'hire_date' column has inconsistent date formats — standardize ALL to YYYY-MM-DD

Available actions: replace_value, convert_type, fill_missing, remove_duplicates, drop_rows, standardize, parse_date

Hints:
1. First use replace_value to fix text values (e.g. 'thirty-five' -> '35', 'ninety thousand' -> '90000')
2. Then use convert_type to convert string columns to int
3. Use parse_date on the 'hire_date' column to automatically standardize dates
"""

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _grade_fix_types(data: List[Dict[str, Any]]) -> float:
    """Grade the fix_types task. 9 checks."""
    checks = []

    # 1. All id values are int
    checks.append(all(isinstance(r.get("id"), int) for r in data))

    # 2. All age values are int
    checks.append(all(isinstance(r.get("age"), int) for r in data))

    # 3. Bob's age is 35
    bob = [r for r in data if r.get("name") == "Bob Jones"]
    checks.append(len(bob) == 1 and bob[0].get("age") == 35)

    # 4. All salary values are int
    checks.append(all(isinstance(r.get("salary"), int) for r in data))

    # 5. Carol's salary is 90000
    carol = [r for r in data if r.get("name") == "Carol White"]
    checks.append(len(carol) == 1 and carol[0].get("salary") == 90000)

    # 6. All dates match YYYY-MM-DD
    checks.append(all(
        isinstance(r.get("hire_date"), str) and _DATE_RE.match(r["hire_date"])
        for r in data
    ))

    # 7. Alice's date
    alice = [r for r in data if r.get("name") == "Alice Smith"]
    checks.append(len(alice) == 1 and alice[0].get("hire_date") == "2023-01-15")

    # 8. David's date
    david = [r for r in data if r.get("name") == "David Brown"]
    checks.append(len(david) == 1 and david[0].get("hire_date") == "2024-01-15")

    # 9. Eve's date
    eve = [r for r in data if r.get("name") == "Eve Davis"]
    checks.append(len(eve) == 1 and eve[0].get("hire_date") == "2023-11-30")

    return sum(checks) / len(checks)


# ---------------------------------------------------------------------------
# Task 2: handle_missing (Medium)
# ---------------------------------------------------------------------------

TASK_HANDLE_MISSING_DATA = [
    {"product_id": 101, "name": "Widget A", "price": 19.99, "stock": 50, "category": "electronics", "description": "A useful widget"},
    {"product_id": 102, "name": "Widget B", "price": None, "stock": 30, "category": "Electronics", "description": "Another widget"},
    {"product_id": 103, "name": "Gadget C", "price": 39.99, "stock": None, "category": "ELECTRONICS", "description": ""},
    {"product_id": 104, "name": "Tool D", "price": 15.00, "stock": 100, "category": "tools", "description": "A handy tool"},
    {"product_id": 105, "name": "Part E", "price": None, "stock": None, "category": "Parts", "description": "Replacement part"},
    {"product_id": 101, "name": "Widget A", "price": 19.99, "stock": 50, "category": "electronics", "description": "A useful widget"},
    {"product_id": 106, "name": "Supply F", "price": 9.99, "stock": 200, "category": "SUPPLIES", "description": ""},
    {"product_id": 107, "name": "Item G", "price": 49.99, "stock": 10, "category": "electronics", "description": "Premium item"},
    {"product_id": 104, "name": "Tool D", "price": 15.00, "stock": 100, "category": "tools", "description": "A handy tool"},
    {"product_id": 108, "name": "Component H", "price": 25.50, "stock": None, "category": "Parts", "description": "Essential component"},
]

TASK_HANDLE_MISSING_DESC = """Clean this product inventory dataset.

Current data has these issues:
- 'price' column has missing (None) values — fill with 29.99
- 'stock' column has missing (None) values — fill with 0
- 'category' column has inconsistent casing (electronics, Electronics, ELECTRONICS) — standardize to title case
- There are duplicate rows (same product_id) — remove them
- 'description' column has empty strings — fill with 'No description'

Available actions: replace_value, convert_type, fill_missing, remove_duplicates, drop_rows, standardize, parse_date

Hints:
1. Use remove_duplicates with subset_columns ['product_id'] to remove duplicate rows
2. Use fill_missing to fill None values in price and stock columns
3. Use replace_value to replace empty strings in description
4. Use standardize with method 'title_case' on category column
"""


def _grade_handle_missing(data: List[Dict[str, Any]]) -> float:
    """Grade the handle_missing task. 6 checks."""
    checks = []

    # 1. No None values in price
    checks.append(all(r.get("price") is not None for r in data))

    # 2. No None values in stock
    checks.append(all(r.get("stock") is not None for r in data))

    # 3. No duplicate product_ids
    pids = [r["product_id"] for r in data]
    checks.append(len(pids) == len(set(pids)))

    # 4. Row count is 8 (10 - 2 duplicates)
    checks.append(len(data) == 8)

    # 5. All category values are title case
    checks.append(all(
        isinstance(r.get("category"), str) and r["category"] == r["category"].strip().title()
        for r in data
    ))

    # 6. No empty strings in description
    checks.append(all(
        r.get("description") not in (None, "")
        for r in data
    ))

    return sum(checks) / len(checks)


# ---------------------------------------------------------------------------
# Task 3: full_pipeline (Hard)
# ---------------------------------------------------------------------------

TASK_FULL_PIPELINE_DATA = [
    {"order_id": "1001.0", "customer_name": "John Doe", "customer_email": "JOHN@EMAIL.COM", "amount": "150.50", "status": "shipped", "order_date": "2024/01/10"},
    {"order_id": "1002.0", "customer_name": "Jane Smith", "customer_email": "Jane@Email.com", "amount": "200.00", "status": "PENDING", "order_date": "2024-01-15"},
    {"order_id": "1003.0", "customer_name": "Bob Wilson", "customer_email": None, "amount": "fifty", "status": "delivered", "order_date": "01/20/2024"},
    {"order_id": "1004.0", "customer_name": "Alice Brown", "customer_email": "alice@email.com", "amount": None, "status": "Shipped", "order_date": "2024/02/01"},
    {"order_id": "1005.0", "customer_name": "Charlie Davis", "customer_email": "CHARLIE@EMAIL.COM", "amount": "75.25", "status": "cancelled", "order_date": "2024-02-10"},
    {"order_id": "1001.0", "customer_name": "John Doe", "customer_email": "JOHN@EMAIL.COM", "amount": "150.50", "status": "shipped", "order_date": "2024/01/10"},
    {"order_id": "1006.0", "customer_name": "Diana Lee", "customer_email": "diana@email.com", "amount": "-25.00", "status": "pending", "order_date": "2024/02/15"},
    {"order_id": "1007.0", "customer_name": "Edward Kim", "customer_email": "ED@EMAIL.COM", "amount": "300.00", "status": "DELIVERED", "order_date": "03-01-2024"},
    {"order_id": "1008.0", "customer_name": "Fiona Chen", "customer_email": "fiona@email.com", "amount": "125.75", "status": "Pending", "order_date": "2024/03/05"},
    {"order_id": "1009.0", "customer_name": "George Martinez", "customer_email": "GEORGE@EMAIL.COM", "amount": None, "status": "shipped", "order_date": "2024-03-10"},
    {"order_id": "1010.0", "customer_name": "Helen Park", "customer_email": "Helen@Email.com", "amount": "89.99", "status": "CANCELLED", "order_date": "03/15/2024"},
    {"order_id": "1005.0", "customer_name": "Charlie Davis", "customer_email": "CHARLIE@EMAIL.COM", "amount": "75.25", "status": "cancelled", "order_date": "2024-02-10"},
    {"order_id": "1011.0", "customer_name": "Ivan Petrov", "customer_email": None, "amount": "450.00", "status": "Delivered", "order_date": "2024/03/20"},
    {"order_id": "1012.0", "customer_name": "Julia Adams", "customer_email": "julia@email.com", "amount": "60.00", "status": "pending", "order_date": "2024/03/25"},
    {"order_id": "1013.0", "customer_name": "Kevin O'Brien", "customer_email": "kevin@email.com", "amount": "175.00", "status": "SHIPPED", "order_date": "04-01-2024"},
]

TASK_FULL_PIPELINE_DESC = """Clean this customer orders dataset. Multiple issues need fixing:

- 'order_id' has string floats ('1001.0') — convert to int
- 'amount' has string values and one text value ('fifty') — fix and convert to float. 'fifty' = 50.0
- 'amount' has None values — fill with 0.0
- 'customer_email' has inconsistent casing — standardize to lowercase
- 'customer_email' has None values — fill with 'unknown@example.com'
- 'status' has inconsistent casing — standardize to title case (Shipped, Pending, Delivered, Cancelled)
- 'order_date' has mixed formats — standardize ALL to YYYY-MM-DD
- There are duplicate orders (same order_id) — remove them
- Row with negative amount (order_id 1006, amount -25.00) should be dropped

Available actions: replace_value, convert_type, fill_missing, remove_duplicates, drop_rows, standardize, parse_date

Hints:
1. First remove duplicates with subset_columns ['order_id']
2. Fix text values: replace_value 'fifty' -> '50.0' in amount
3. Fill missing values in amount and customer_email
4. Convert types: order_id to int, amount to float
5. Standardize: customer_email to lowercase, status to title_case
6. Use parse_date on the 'order_date' column to standardize all dates at once
7. Drop rows with negative amounts (find the row index after dedup)
"""


def _grade_full_pipeline(data: List[Dict[str, Any]]) -> float:
    """Grade the full_pipeline task. 12 checks."""
    checks = []

    # 1. All order_id values are int
    checks.append(all(isinstance(r.get("order_id"), int) for r in data))

    # 2. All amount values are numeric
    checks.append(all(
        isinstance(r.get("amount"), (int, float))
        for r in data
    ))

    # 3. Bob Wilson's amount is 50.0
    bob = [r for r in data if r.get("customer_name") == "Bob Wilson"]
    checks.append(len(bob) == 1 and isinstance(bob[0].get("amount"), (int, float)) and abs(bob[0]["amount"] - 50.0) < 0.01)

    # 4. No None values in amount
    checks.append(all(r.get("amount") is not None for r in data))

    # 5. No None values in customer_email
    checks.append(all(r.get("customer_email") is not None for r in data))

    # 6. All customer_email values are lowercase
    checks.append(all(
        isinstance(r.get("customer_email"), str) and r["customer_email"] == r["customer_email"].lower()
        for r in data
    ))

    # 7. All status values are title case
    checks.append(all(
        isinstance(r.get("status"), str) and r["status"] == r["status"].strip().title()
        for r in data
    ))

    # 8. Valid status values only
    valid_statuses = {"Shipped", "Pending", "Delivered", "Cancelled"}
    checks.append(all(r.get("status") in valid_statuses for r in data))

    # 9. All dates match YYYY-MM-DD
    checks.append(all(
        isinstance(r.get("order_date"), str) and _DATE_RE.match(r["order_date"])
        for r in data
    ))

    # 10. No duplicate order_ids
    oids = [r["order_id"] for r in data]
    checks.append(len(oids) == len(set(oids)))

    # 11. No negative amounts
    checks.append(all(
        isinstance(r.get("amount"), (int, float)) and r["amount"] >= 0
        for r in data
    ))

    # 12. Row count is 12 (15 - 2 dupes - 1 negative)
    checks.append(len(data) == 12)

    return sum(checks) / len(checks)


# ---------------------------------------------------------------------------
# Task 4: outlier_cleanup (Medium-Hard)
# ---------------------------------------------------------------------------

TASK_OUTLIER_DATA = [
    {"txn_id": 1, "product": "  Laptop  ", "price": 999.99, "quantity": 1, "currency": "USD", "region": "North America"},
    {"txn_id": 2, "product": "Mouse", "price": 25.00, "quantity": 3, "currency": "usd", "region": "north america"},
    {"txn_id": 3, "product": "keyboard", "price": 75.50, "quantity": -2, "currency": "USD", "region": "Europe"},
    {"txn_id": 4, "product": "Monitor", "price": 50000.00, "quantity": 1, "currency": "EUR", "region": "europe"},
    {"txn_id": 5, "product": "  Headset ", "price": 150.00, "quantity": 10, "currency": "Usd", "region": "Asia"},
    {"txn_id": 6, "product": "Webcam", "price": 89.99, "quantity": 0, "currency": "USD", "region": "North America"},
    {"txn_id": 7, "product": "Cable", "price": 0.00, "quantity": 5, "currency": "eur", "region": "Europe"},
    {"txn_id": 8, "product": "laptop", "price": 1050.00, "quantity": 1, "currency": "USD", "region": "NORTH AMERICA"},
    {"txn_id": 9, "product": "Dock", "price": -199.99, "quantity": 2, "currency": "USD", "region": "Asia"},
    {"txn_id": 10, "product": "SSD", "price": 120.00, "quantity": 100000, "currency": "EUR", "region": "Europe"},
]

TASK_OUTLIER_DESC = """Clean this sales transactions dataset.

Current data has these issues:
- 'product' has leading/trailing whitespace and inconsistent casing — standardize: trim then title case
- 'price' has an outlier (50000.00 for a Monitor, should be 500.00) — replace with correct value
- 'price' has negative values (txn_id 9) — drop that row
- 'quantity' has a negative value (txn_id 3) — replace with 0
- 'quantity' has an extreme outlier (100000 for txn_id 10) — replace with 100
- 'currency' has inconsistent casing — standardize to uppercase
- 'region' has inconsistent casing — standardize to title case
- 'price' of 0.00 for Cable (txn_id 7) — replace with 12.99

Available actions: replace_value, convert_type, fill_missing, remove_duplicates, drop_rows, standardize, parse_date

Hints:
1. Trim and title_case the product column
2. Fix outlier prices: replace '50000.0' with '500.0', '0.0' with '12.99' in price
3. Fix quantities: replace '-2' with '0', '100000' with '100'
4. Drop the row with negative price (find row index of txn_id 9)
5. Standardize currency to uppercase, region to title case
"""


def _grade_outlier_cleanup(data: List[Dict[str, Any]]) -> float:
    """Grade the outlier_cleanup task. 10 checks."""
    checks = []

    # 1. All product values are trimmed (no leading/trailing whitespace)
    checks.append(all(
        isinstance(r.get("product"), str) and r["product"] == r["product"].strip()
        for r in data
    ))

    # 2. All product values are title case
    checks.append(all(
        isinstance(r.get("product"), str) and r["product"] == r["product"].strip().title()
        for r in data
    ))

    # 3. Monitor price is 500.00 (not 50000)
    monitor = [r for r in data if isinstance(r.get("product"), str) and r["product"].strip().title() == "Monitor"]
    checks.append(len(monitor) == 1 and isinstance(monitor[0].get("price"), (int, float)) and abs(monitor[0]["price"] - 500.0) < 0.01)

    # 4. No negative prices
    checks.append(all(
        isinstance(r.get("price"), (int, float)) and r["price"] >= 0
        for r in data
    ))

    # 5. No negative quantities
    checks.append(all(
        isinstance(r.get("quantity"), (int, float)) and r["quantity"] >= 0
        for r in data
    ))

    # 6. No extreme quantity outliers (max reasonable = 1000)
    checks.append(all(
        isinstance(r.get("quantity"), (int, float)) and r["quantity"] <= 1000
        for r in data
    ))

    # 7. All currency values are uppercase
    checks.append(all(
        isinstance(r.get("currency"), str) and r["currency"] == r["currency"].upper()
        for r in data
    ))

    # 8. All region values are title case
    checks.append(all(
        isinstance(r.get("region"), str) and r["region"] == r["region"].strip().title()
        for r in data
    ))

    # 9. Row with negative price (txn_id 9) is removed — expect 9 rows
    checks.append(len(data) == 9)

    # 10. Cable price is 12.99 (not 0.00)
    cable = [r for r in data if isinstance(r.get("product"), str) and r["product"].strip().title() == "Cable"]
    checks.append(len(cable) == 1 and isinstance(cable[0].get("price"), (int, float)) and abs(cable[0]["price"] - 12.99) < 0.01)

    return sum(checks) / len(checks)


# ---------------------------------------------------------------------------
# Task registry
# ---------------------------------------------------------------------------

TASKS = {
    "fix_types": {
        "name": "fix_types",
        "description": TASK_FIX_TYPES_DESC,
        "dirty_data": TASK_FIX_TYPES_DATA,
        "max_steps": 15,
        "grader": _grade_fix_types,
        "total_checks": 9,
    },
    "handle_missing": {
        "name": "handle_missing",
        "description": TASK_HANDLE_MISSING_DESC,
        "dirty_data": TASK_HANDLE_MISSING_DATA,
        "max_steps": 20,
        "grader": _grade_handle_missing,
        "total_checks": 6,
    },
    "full_pipeline": {
        "name": "full_pipeline",
        "description": TASK_FULL_PIPELINE_DESC,
        "dirty_data": TASK_FULL_PIPELINE_DATA,
        "max_steps": 25,
        "grader": _grade_full_pipeline,
        "total_checks": 12,
    },
    "outlier_cleanup": {
        "name": "outlier_cleanup",
        "description": TASK_OUTLIER_DESC,
        "dirty_data": TASK_OUTLIER_DATA,
        "max_steps": 20,
        "grader": _grade_outlier_cleanup,
        "total_checks": 10,
    },
}

DEFAULT_TASK = "fix_types"


def list_tasks() -> List[str]:
    """Return list of available task names."""
    return list(TASKS.keys())


def get_task(task_name: str) -> Dict[str, Any]:
    """Get task config by name. Returns a deep copy of the dirty data."""
    if task_name not in TASKS:
        raise ValueError(f"Unknown task '{task_name}'. Available: {list_tasks()}")
    task = TASKS[task_name]
    return {
        **task,
        "dirty_data": copy.deepcopy(task["dirty_data"]),
    }


def grade_task(task_name: str, current_data: List[Dict[str, Any]]) -> float:
    """Grade current data state for a task. Returns score in [0, 1]."""
    if task_name not in TASKS:
        raise ValueError(f"Unknown task '{task_name}'. Available: {list_tasks()}")
    return TASKS[task_name]["grader"](current_data)
