"""Tests for task graders — verify scoring correctness."""

import copy
from tasks.task_data import (
    TASKS,
    grade_task,
    list_tasks,
    get_task,
    _grade_fix_types,
    _grade_handle_missing,
    _grade_full_pipeline,
    _grade_outlier_cleanup,
    TASK_FIX_TYPES_DATA,
    TASK_HANDLE_MISSING_DATA,
    TASK_FULL_PIPELINE_DATA,
    TASK_OUTLIER_DATA,
)


class TestGraderBasics:
    """Every grader must return float in [0, 1] and dirty data must not score 1.0."""

    def test_all_tasks_registered(self):
        tasks = list_tasks()
        assert len(tasks) >= 3, "Spec requires at least 3 tasks"
        assert set(tasks) == {"fix_types", "handle_missing", "full_pipeline", "outlier_cleanup"}

    def test_dirty_data_scores_below_one(self):
        for name in list_tasks():
            task = get_task(name)
            score = grade_task(name, task["dirty_data"])
            assert score < 1.0, f"Task '{name}' dirty data should score < 1.0, got {score}"

    def test_grader_returns_float_in_range(self):
        for name in list_tasks():
            task = get_task(name)
            score = grade_task(name, task["dirty_data"])
            assert isinstance(score, float), f"Task '{name}' grader must return float"
            assert 0.0 <= score <= 1.0, f"Task '{name}' score out of range: {score}"

    def test_total_checks_matches_grader(self):
        """Verify total_checks field matches actual number of checks in grader."""
        assert TASKS["fix_types"]["total_checks"] == 9
        assert TASKS["handle_missing"]["total_checks"] == 6
        assert TASKS["full_pipeline"]["total_checks"] == 12
        assert TASKS["outlier_cleanup"]["total_checks"] == 10

    def test_empty_data_does_not_crash(self):
        """Graders should handle empty data without exceptions."""
        for name in list_tasks():
            score = grade_task(name, [])
            assert 0.0 <= score <= 1.0


class TestFixTypesGrader:
    """Specific tests for fix_types grader."""

    def test_dirty_data_initial_score(self):
        score = _grade_fix_types(copy.deepcopy(TASK_FIX_TYPES_DATA))
        assert 0.0 <= score < 1.0

    def test_perfect_clean_data(self):
        clean = [
            {"id": 1, "name": "Alice Smith", "age": 28, "salary": 75000, "hire_date": "2023-01-15"},
            {"id": 2, "name": "Bob Jones", "age": 35, "salary": 82000, "hire_date": "2022-03-20"},
            {"id": 3, "name": "Carol White", "age": 42, "salary": 90000, "hire_date": "2021-06-01"},
            {"id": 4, "name": "David Brown", "age": 31, "salary": 68000, "hire_date": "2024-01-15"},
            {"id": 5, "name": "Eve Davis", "age": 29, "salary": 71000, "hire_date": "2023-11-30"},
        ]
        score = _grade_fix_types(clean)
        assert score == 1.0, f"Perfect clean data should score 1.0, got {score}"

    def test_wrong_bob_age_fails(self):
        """Bob's age must be exactly 35."""
        data = [
            {"id": 1, "name": "Alice Smith", "age": 28, "salary": 75000, "hire_date": "2023-01-15"},
            {"id": 2, "name": "Bob Jones", "age": 30, "salary": 82000, "hire_date": "2022-03-20"},
            {"id": 3, "name": "Carol White", "age": 42, "salary": 90000, "hire_date": "2021-06-01"},
            {"id": 4, "name": "David Brown", "age": 31, "salary": 68000, "hire_date": "2024-01-15"},
            {"id": 5, "name": "Eve Davis", "age": 29, "salary": 71000, "hire_date": "2023-11-30"},
        ]
        score = _grade_fix_types(data)
        assert score < 1.0, "Wrong Bob age should score < 1.0"

    def test_string_ids_fail(self):
        """id must be int, not string."""
        data = [
            {"id": "1", "name": "Alice Smith", "age": 28, "salary": 75000, "hire_date": "2023-01-15"},
            {"id": "2", "name": "Bob Jones", "age": 35, "salary": 82000, "hire_date": "2022-03-20"},
            {"id": "3", "name": "Carol White", "age": 42, "salary": 90000, "hire_date": "2021-06-01"},
            {"id": "4", "name": "David Brown", "age": 31, "salary": 68000, "hire_date": "2024-01-15"},
            {"id": "5", "name": "Eve Davis", "age": 29, "salary": 71000, "hire_date": "2023-11-30"},
        ]
        score = _grade_fix_types(data)
        assert score < 1.0, "String ids should score < 1.0"

    def test_wrong_date_format_fails(self):
        """Dates must be YYYY-MM-DD format."""
        data = [
            {"id": 1, "name": "Alice Smith", "age": 28, "salary": 75000, "hire_date": "2023/01/15"},
            {"id": 2, "name": "Bob Jones", "age": 35, "salary": 82000, "hire_date": "2022-03-20"},
            {"id": 3, "name": "Carol White", "age": 42, "salary": 90000, "hire_date": "2021-06-01"},
            {"id": 4, "name": "David Brown", "age": 31, "salary": 68000, "hire_date": "2024-01-15"},
            {"id": 5, "name": "Eve Davis", "age": 29, "salary": 71000, "hire_date": "2023-11-30"},
        ]
        score = _grade_fix_types(data)
        assert score < 1.0, "Wrong date format should score < 1.0"


class TestHandleMissingGrader:
    """Specific tests for handle_missing grader."""

    def test_dirty_data_initial_score(self):
        score = _grade_handle_missing(copy.deepcopy(TASK_HANDLE_MISSING_DATA))
        assert 0.0 <= score < 1.0

    def test_perfect_clean_data(self):
        clean = [
            {"product_id": 101, "name": "Widget A", "price": 19.99, "stock": 50, "category": "Electronics", "description": "A useful widget"},
            {"product_id": 102, "name": "Widget B", "price": 29.99, "stock": 30, "category": "Electronics", "description": "Another widget"},
            {"product_id": 103, "name": "Gadget C", "price": 39.99, "stock": 0, "category": "Electronics", "description": "A gadget"},
            {"product_id": 104, "name": "Tool D", "price": 15.00, "stock": 100, "category": "Tools", "description": "A handy tool"},
            {"product_id": 105, "name": "Part E", "price": 29.99, "stock": 0, "category": "Parts", "description": "Replacement part"},
            {"product_id": 106, "name": "Supply F", "price": 9.99, "stock": 200, "category": "Supplies", "description": "A supply"},
            {"product_id": 107, "name": "Item G", "price": 49.99, "stock": 10, "category": "Electronics", "description": "Premium item"},
            {"product_id": 108, "name": "Component H", "price": 25.50, "stock": 0, "category": "Parts", "description": "Essential component"},
        ]
        score = _grade_handle_missing(clean)
        assert score == 1.0, f"Perfect clean data should score 1.0, got {score}"

    def test_none_price_fails(self):
        """None price should fail check 1."""
        data = [
            {"product_id": 101, "name": "Widget A", "price": None, "stock": 50, "category": "Electronics", "description": "A widget"},
            {"product_id": 102, "name": "Widget B", "price": 29.99, "stock": 30, "category": "Electronics", "description": "Another widget"},
            {"product_id": 103, "name": "Gadget C", "price": 39.99, "stock": 0, "category": "Electronics", "description": "A gadget"},
            {"product_id": 104, "name": "Tool D", "price": 15.00, "stock": 100, "category": "Tools", "description": "A tool"},
            {"product_id": 105, "name": "Part E", "price": 29.99, "stock": 0, "category": "Parts", "description": "A part"},
            {"product_id": 106, "name": "Supply F", "price": 9.99, "stock": 200, "category": "Supplies", "description": "A supply"},
            {"product_id": 107, "name": "Item G", "price": 49.99, "stock": 10, "category": "Electronics", "description": "An item"},
            {"product_id": 108, "name": "Component H", "price": 25.50, "stock": 0, "category": "Parts", "description": "A component"},
        ]
        score = _grade_handle_missing(data)
        assert score < 1.0, "None price should score < 1.0"

    def test_duplicate_product_ids_fail(self):
        """Duplicate product_ids should fail checks 3 and 4."""
        data = [
            {"product_id": 101, "name": "Widget A", "price": 19.99, "stock": 50, "category": "Electronics", "description": "A widget"},
            {"product_id": 101, "name": "Widget A", "price": 19.99, "stock": 50, "category": "Electronics", "description": "A widget"},
            {"product_id": 103, "name": "Gadget C", "price": 39.99, "stock": 0, "category": "Electronics", "description": "A gadget"},
            {"product_id": 104, "name": "Tool D", "price": 15.00, "stock": 100, "category": "Tools", "description": "A tool"},
            {"product_id": 105, "name": "Part E", "price": 29.99, "stock": 0, "category": "Parts", "description": "A part"},
            {"product_id": 106, "name": "Supply F", "price": 9.99, "stock": 200, "category": "Supplies", "description": "A supply"},
            {"product_id": 107, "name": "Item G", "price": 49.99, "stock": 10, "category": "Electronics", "description": "An item"},
            {"product_id": 108, "name": "Component H", "price": 25.50, "stock": 0, "category": "Parts", "description": "A component"},
        ]
        score = _grade_handle_missing(data)
        assert score < 1.0, "Duplicate product_ids should score < 1.0"

    def test_wrong_row_count_fails(self):
        """Row count must be exactly 8."""
        data = [
            {"product_id": 101, "name": "Widget A", "price": 19.99, "stock": 50, "category": "Electronics", "description": "A widget"},
            {"product_id": 102, "name": "Widget B", "price": 29.99, "stock": 30, "category": "Electronics", "description": "Another widget"},
            {"product_id": 103, "name": "Gadget C", "price": 39.99, "stock": 0, "category": "Electronics", "description": "A gadget"},
            {"product_id": 104, "name": "Tool D", "price": 15.00, "stock": 100, "category": "Tools", "description": "A tool"},
            {"product_id": 105, "name": "Part E", "price": 29.99, "stock": 0, "category": "Parts", "description": "A part"},
            {"product_id": 106, "name": "Supply F", "price": 9.99, "stock": 200, "category": "Supplies", "description": "A supply"},
            {"product_id": 107, "name": "Item G", "price": 49.99, "stock": 10, "category": "Electronics", "description": "An item"},
            # missing row 108 → only 7 rows
        ]
        score = _grade_handle_missing(data)
        assert score < 1.0, "Wrong row count (7 instead of 8) should score < 1.0"

    def test_lowercase_category_fails(self):
        """Category must be title case."""
        data = [
            {"product_id": 101, "name": "Widget A", "price": 19.99, "stock": 50, "category": "electronics", "description": "A widget"},
            {"product_id": 102, "name": "Widget B", "price": 29.99, "stock": 30, "category": "Electronics", "description": "Another widget"},
            {"product_id": 103, "name": "Gadget C", "price": 39.99, "stock": 0, "category": "Electronics", "description": "A gadget"},
            {"product_id": 104, "name": "Tool D", "price": 15.00, "stock": 100, "category": "Tools", "description": "A tool"},
            {"product_id": 105, "name": "Part E", "price": 29.99, "stock": 0, "category": "Parts", "description": "A part"},
            {"product_id": 106, "name": "Supply F", "price": 9.99, "stock": 200, "category": "Supplies", "description": "A supply"},
            {"product_id": 107, "name": "Item G", "price": 49.99, "stock": 10, "category": "Electronics", "description": "An item"},
            {"product_id": 108, "name": "Component H", "price": 25.50, "stock": 0, "category": "Parts", "description": "A component"},
        ]
        score = _grade_handle_missing(data)
        assert score < 1.0, "Lowercase category should score < 1.0"

    def test_empty_description_fails(self):
        """Empty string description should fail check 6."""
        data = [
            {"product_id": 101, "name": "Widget A", "price": 19.99, "stock": 50, "category": "Electronics", "description": ""},
            {"product_id": 102, "name": "Widget B", "price": 29.99, "stock": 30, "category": "Electronics", "description": "Another widget"},
            {"product_id": 103, "name": "Gadget C", "price": 39.99, "stock": 0, "category": "Electronics", "description": "A gadget"},
            {"product_id": 104, "name": "Tool D", "price": 15.00, "stock": 100, "category": "Tools", "description": "A tool"},
            {"product_id": 105, "name": "Part E", "price": 29.99, "stock": 0, "category": "Parts", "description": "A part"},
            {"product_id": 106, "name": "Supply F", "price": 9.99, "stock": 200, "category": "Supplies", "description": "A supply"},
            {"product_id": 107, "name": "Item G", "price": 49.99, "stock": 10, "category": "Electronics", "description": "An item"},
            {"product_id": 108, "name": "Component H", "price": 25.50, "stock": 0, "category": "Parts", "description": "A component"},
        ]
        score = _grade_handle_missing(data)
        assert score < 1.0, "Empty description should score < 1.0"


class TestFullPipelineGrader:
    """Specific tests for full_pipeline grader."""

    def test_dirty_data_initial_score(self):
        score = _grade_full_pipeline(copy.deepcopy(TASK_FULL_PIPELINE_DATA))
        assert 0.0 <= score < 1.0

    def test_perfect_clean_data(self):
        # 12 rows: 15 original - 2 duplicates (1001, 1005) - 1 negative amount (1006)
        clean = [
            {"order_id": 1001, "customer_name": "John Doe", "customer_email": "john@email.com", "amount": 150.50, "status": "Shipped", "order_date": "2024-01-10"},
            {"order_id": 1002, "customer_name": "Jane Smith", "customer_email": "jane@email.com", "amount": 200.00, "status": "Pending", "order_date": "2024-01-15"},
            {"order_id": 1003, "customer_name": "Bob Wilson", "customer_email": "unknown@example.com", "amount": 50.0, "status": "Delivered", "order_date": "2024-01-20"},
            {"order_id": 1004, "customer_name": "Alice Brown", "customer_email": "alice@email.com", "amount": 0.0, "status": "Shipped", "order_date": "2024-02-01"},
            {"order_id": 1005, "customer_name": "Charlie Davis", "customer_email": "charlie@email.com", "amount": 75.25, "status": "Cancelled", "order_date": "2024-02-10"},
            {"order_id": 1007, "customer_name": "Edward Kim", "customer_email": "ed@email.com", "amount": 300.00, "status": "Delivered", "order_date": "2024-03-01"},
            {"order_id": 1008, "customer_name": "Fiona Chen", "customer_email": "fiona@email.com", "amount": 125.75, "status": "Pending", "order_date": "2024-03-05"},
            {"order_id": 1009, "customer_name": "George Martinez", "customer_email": "george@email.com", "amount": 0.0, "status": "Shipped", "order_date": "2024-03-10"},
            {"order_id": 1010, "customer_name": "Helen Park", "customer_email": "helen@email.com", "amount": 89.99, "status": "Cancelled", "order_date": "2024-03-15"},
            {"order_id": 1011, "customer_name": "Ivan Petrov", "customer_email": "unknown@example.com", "amount": 450.00, "status": "Delivered", "order_date": "2024-03-20"},
            {"order_id": 1012, "customer_name": "Julia Adams", "customer_email": "julia@email.com", "amount": 60.00, "status": "Pending", "order_date": "2024-03-25"},
            {"order_id": 1013, "customer_name": "Kevin O'Brien", "customer_email": "kevin@email.com", "amount": 175.00, "status": "Shipped", "order_date": "2024-04-01"},
        ]
        score = _grade_full_pipeline(clean)
        assert score == 1.0, f"Perfect clean data should score 1.0, got {score}"

    def test_string_order_ids_fail(self):
        """order_id must be int."""
        clean = [
            {"order_id": "1001", "customer_name": "John Doe", "customer_email": "john@email.com", "amount": 150.50, "status": "Shipped", "order_date": "2024-01-10"},
            {"order_id": "1002", "customer_name": "Jane Smith", "customer_email": "jane@email.com", "amount": 200.00, "status": "Pending", "order_date": "2024-01-15"},
            {"order_id": "1003", "customer_name": "Bob Wilson", "customer_email": "unknown@example.com", "amount": 50.0, "status": "Delivered", "order_date": "2024-01-20"},
            {"order_id": "1004", "customer_name": "Alice Brown", "customer_email": "alice@email.com", "amount": 0.0, "status": "Shipped", "order_date": "2024-02-01"},
            {"order_id": "1005", "customer_name": "Charlie Davis", "customer_email": "charlie@email.com", "amount": 75.25, "status": "Cancelled", "order_date": "2024-02-10"},
            {"order_id": "1007", "customer_name": "Edward Kim", "customer_email": "ed@email.com", "amount": 300.00, "status": "Delivered", "order_date": "2024-03-01"},
            {"order_id": "1008", "customer_name": "Fiona Chen", "customer_email": "fiona@email.com", "amount": 125.75, "status": "Pending", "order_date": "2024-03-05"},
            {"order_id": "1009", "customer_name": "George Martinez", "customer_email": "george@email.com", "amount": 0.0, "status": "Shipped", "order_date": "2024-03-10"},
            {"order_id": "1010", "customer_name": "Helen Park", "customer_email": "helen@email.com", "amount": 89.99, "status": "Cancelled", "order_date": "2024-03-15"},
            {"order_id": "1011", "customer_name": "Ivan Petrov", "customer_email": "unknown@example.com", "amount": 450.00, "status": "Delivered", "order_date": "2024-03-20"},
            {"order_id": "1012", "customer_name": "Julia Adams", "customer_email": "julia@email.com", "amount": 60.00, "status": "Pending", "order_date": "2024-03-25"},
            {"order_id": "1013", "customer_name": "Kevin O'Brien", "customer_email": "kevin@email.com", "amount": 175.00, "status": "Shipped", "order_date": "2024-04-01"},
        ]
        score = _grade_full_pipeline(clean)
        assert score < 1.0, "String order_ids should score < 1.0"

    def test_uppercase_email_fails(self):
        """customer_email must be lowercase."""
        clean = [
            {"order_id": 1001, "customer_name": "John Doe", "customer_email": "JOHN@EMAIL.COM", "amount": 150.50, "status": "Shipped", "order_date": "2024-01-10"},
            {"order_id": 1002, "customer_name": "Jane Smith", "customer_email": "jane@email.com", "amount": 200.00, "status": "Pending", "order_date": "2024-01-15"},
            {"order_id": 1003, "customer_name": "Bob Wilson", "customer_email": "unknown@example.com", "amount": 50.0, "status": "Delivered", "order_date": "2024-01-20"},
            {"order_id": 1004, "customer_name": "Alice Brown", "customer_email": "alice@email.com", "amount": 0.0, "status": "Shipped", "order_date": "2024-02-01"},
            {"order_id": 1005, "customer_name": "Charlie Davis", "customer_email": "charlie@email.com", "amount": 75.25, "status": "Cancelled", "order_date": "2024-02-10"},
            {"order_id": 1007, "customer_name": "Edward Kim", "customer_email": "ed@email.com", "amount": 300.00, "status": "Delivered", "order_date": "2024-03-01"},
            {"order_id": 1008, "customer_name": "Fiona Chen", "customer_email": "fiona@email.com", "amount": 125.75, "status": "Pending", "order_date": "2024-03-05"},
            {"order_id": 1009, "customer_name": "George Martinez", "customer_email": "george@email.com", "amount": 0.0, "status": "Shipped", "order_date": "2024-03-10"},
            {"order_id": 1010, "customer_name": "Helen Park", "customer_email": "helen@email.com", "amount": 89.99, "status": "Cancelled", "order_date": "2024-03-15"},
            {"order_id": 1011, "customer_name": "Ivan Petrov", "customer_email": "unknown@example.com", "amount": 450.00, "status": "Delivered", "order_date": "2024-03-20"},
            {"order_id": 1012, "customer_name": "Julia Adams", "customer_email": "julia@email.com", "amount": 60.00, "status": "Pending", "order_date": "2024-03-25"},
            {"order_id": 1013, "customer_name": "Kevin O'Brien", "customer_email": "kevin@email.com", "amount": 175.00, "status": "Shipped", "order_date": "2024-04-01"},
        ]
        score = _grade_full_pipeline(clean)
        assert score < 1.0, "Uppercase email should score < 1.0"

    def test_negative_amount_fails(self):
        """Negative amounts must be removed."""
        data = [
            {"order_id": 1001, "customer_name": "John Doe", "customer_email": "john@email.com", "amount": 150.50, "status": "Shipped", "order_date": "2024-01-10"},
            {"order_id": 1002, "customer_name": "Jane Smith", "customer_email": "jane@email.com", "amount": -25.00, "status": "Pending", "order_date": "2024-01-15"},
            {"order_id": 1003, "customer_name": "Bob Wilson", "customer_email": "unknown@example.com", "amount": 50.0, "status": "Delivered", "order_date": "2024-01-20"},
            {"order_id": 1004, "customer_name": "Alice Brown", "customer_email": "alice@email.com", "amount": 0.0, "status": "Shipped", "order_date": "2024-02-01"},
            {"order_id": 1005, "customer_name": "Charlie Davis", "customer_email": "charlie@email.com", "amount": 75.25, "status": "Cancelled", "order_date": "2024-02-10"},
            {"order_id": 1007, "customer_name": "Edward Kim", "customer_email": "ed@email.com", "amount": 300.00, "status": "Delivered", "order_date": "2024-03-01"},
            {"order_id": 1008, "customer_name": "Fiona Chen", "customer_email": "fiona@email.com", "amount": 125.75, "status": "Pending", "order_date": "2024-03-05"},
            {"order_id": 1009, "customer_name": "George Martinez", "customer_email": "george@email.com", "amount": 0.0, "status": "Shipped", "order_date": "2024-03-10"},
            {"order_id": 1010, "customer_name": "Helen Park", "customer_email": "helen@email.com", "amount": 89.99, "status": "Cancelled", "order_date": "2024-03-15"},
            {"order_id": 1011, "customer_name": "Ivan Petrov", "customer_email": "unknown@example.com", "amount": 450.00, "status": "Delivered", "order_date": "2024-03-20"},
            {"order_id": 1012, "customer_name": "Julia Adams", "customer_email": "julia@email.com", "amount": 60.00, "status": "Pending", "order_date": "2024-03-25"},
            {"order_id": 1013, "customer_name": "Kevin O'Brien", "customer_email": "kevin@email.com", "amount": 175.00, "status": "Shipped", "order_date": "2024-04-01"},
        ]
        score = _grade_full_pipeline(data)
        assert score < 1.0, "Negative amount should score < 1.0"

    def test_wrong_row_count_fails(self):
        """Row count must be exactly 12."""
        # 11 rows — missing one
        data = [
            {"order_id": 1001, "customer_name": "John Doe", "customer_email": "john@email.com", "amount": 150.50, "status": "Shipped", "order_date": "2024-01-10"},
            {"order_id": 1002, "customer_name": "Jane Smith", "customer_email": "jane@email.com", "amount": 200.00, "status": "Pending", "order_date": "2024-01-15"},
            {"order_id": 1003, "customer_name": "Bob Wilson", "customer_email": "unknown@example.com", "amount": 50.0, "status": "Delivered", "order_date": "2024-01-20"},
            {"order_id": 1004, "customer_name": "Alice Brown", "customer_email": "alice@email.com", "amount": 0.0, "status": "Shipped", "order_date": "2024-02-01"},
            {"order_id": 1005, "customer_name": "Charlie Davis", "customer_email": "charlie@email.com", "amount": 75.25, "status": "Cancelled", "order_date": "2024-02-10"},
            {"order_id": 1007, "customer_name": "Edward Kim", "customer_email": "ed@email.com", "amount": 300.00, "status": "Delivered", "order_date": "2024-03-01"},
            {"order_id": 1008, "customer_name": "Fiona Chen", "customer_email": "fiona@email.com", "amount": 125.75, "status": "Pending", "order_date": "2024-03-05"},
            {"order_id": 1009, "customer_name": "George Martinez", "customer_email": "george@email.com", "amount": 0.0, "status": "Shipped", "order_date": "2024-03-10"},
            {"order_id": 1010, "customer_name": "Helen Park", "customer_email": "helen@email.com", "amount": 89.99, "status": "Cancelled", "order_date": "2024-03-15"},
            {"order_id": 1011, "customer_name": "Ivan Petrov", "customer_email": "unknown@example.com", "amount": 450.00, "status": "Delivered", "order_date": "2024-03-20"},
            {"order_id": 1012, "customer_name": "Julia Adams", "customer_email": "julia@email.com", "amount": 60.00, "status": "Pending", "order_date": "2024-03-25"},
        ]
        score = _grade_full_pipeline(data)
        assert score < 1.0, "Wrong row count (11 instead of 12) should score < 1.0"


class TestOutlierCleanupGrader:
    """Specific tests for outlier_cleanup grader."""

    def test_dirty_data_initial_score(self):
        score = _grade_outlier_cleanup(copy.deepcopy(TASK_OUTLIER_DATA))
        assert 0.0 <= score < 1.0

    def test_perfect_clean_data(self):
        # 9 rows: 10 original - 1 negative price (txn_id 9 dropped)
        # Monitor price fixed to 500.00, Cable price fixed to 12.99
        # Negative quantity (txn_id 3) fixed to 0, extreme quantity (txn_id 10) fixed to 100
        # All products trimmed + title case, currency uppercase, region title case
        clean = [
            {"txn_id": 1, "product": "Laptop", "price": 999.99, "quantity": 1, "currency": "USD", "region": "North America"},
            {"txn_id": 2, "product": "Mouse", "price": 25.00, "quantity": 3, "currency": "USD", "region": "North America"},
            {"txn_id": 3, "product": "Keyboard", "price": 75.50, "quantity": 0, "currency": "USD", "region": "Europe"},
            {"txn_id": 4, "product": "Monitor", "price": 500.00, "quantity": 1, "currency": "EUR", "region": "Europe"},
            {"txn_id": 5, "product": "Headset", "price": 150.00, "quantity": 10, "currency": "USD", "region": "Asia"},
            {"txn_id": 6, "product": "Webcam", "price": 89.99, "quantity": 0, "currency": "USD", "region": "North America"},
            {"txn_id": 7, "product": "Cable", "price": 12.99, "quantity": 5, "currency": "EUR", "region": "Europe"},
            {"txn_id": 8, "product": "Laptop", "price": 1050.00, "quantity": 1, "currency": "USD", "region": "North America"},
            {"txn_id": 10, "product": "Ssd", "price": 120.00, "quantity": 100, "currency": "EUR", "region": "Europe"},
        ]
        score = _grade_outlier_cleanup(clean)
        assert score == 1.0, f"Perfect clean data should score 1.0, got {score}"

    def test_untrimmed_product_fails(self):
        """Products with leading/trailing whitespace should fail."""
        data = [
            {"txn_id": 1, "product": "  Laptop  ", "price": 999.99, "quantity": 1, "currency": "USD", "region": "North America"},
            {"txn_id": 2, "product": "Mouse", "price": 25.00, "quantity": 3, "currency": "USD", "region": "North America"},
            {"txn_id": 3, "product": "Keyboard", "price": 75.50, "quantity": 0, "currency": "USD", "region": "Europe"},
            {"txn_id": 4, "product": "Monitor", "price": 500.00, "quantity": 1, "currency": "EUR", "region": "Europe"},
            {"txn_id": 5, "product": "Headset", "price": 150.00, "quantity": 10, "currency": "USD", "region": "Asia"},
            {"txn_id": 6, "product": "Webcam", "price": 89.99, "quantity": 0, "currency": "USD", "region": "North America"},
            {"txn_id": 7, "product": "Cable", "price": 12.99, "quantity": 5, "currency": "EUR", "region": "Europe"},
            {"txn_id": 8, "product": "Laptop", "price": 1050.00, "quantity": 1, "currency": "USD", "region": "North America"},
            {"txn_id": 10, "product": "Ssd", "price": 120.00, "quantity": 100, "currency": "EUR", "region": "Europe"},
        ]
        score = _grade_outlier_cleanup(data)
        assert score < 1.0, "Untrimmed product name should score < 1.0"

    def test_monitor_price_outlier_fails(self):
        """Monitor price 50000 instead of 500 should fail."""
        data = [
            {"txn_id": 1, "product": "Laptop", "price": 999.99, "quantity": 1, "currency": "USD", "region": "North America"},
            {"txn_id": 2, "product": "Mouse", "price": 25.00, "quantity": 3, "currency": "USD", "region": "North America"},
            {"txn_id": 3, "product": "Keyboard", "price": 75.50, "quantity": 0, "currency": "USD", "region": "Europe"},
            {"txn_id": 4, "product": "Monitor", "price": 50000.00, "quantity": 1, "currency": "EUR", "region": "Europe"},
            {"txn_id": 5, "product": "Headset", "price": 150.00, "quantity": 10, "currency": "USD", "region": "Asia"},
            {"txn_id": 6, "product": "Webcam", "price": 89.99, "quantity": 0, "currency": "USD", "region": "North America"},
            {"txn_id": 7, "product": "Cable", "price": 12.99, "quantity": 5, "currency": "EUR", "region": "Europe"},
            {"txn_id": 8, "product": "Laptop", "price": 1050.00, "quantity": 1, "currency": "USD", "region": "North America"},
            {"txn_id": 10, "product": "Ssd", "price": 120.00, "quantity": 100, "currency": "EUR", "region": "Europe"},
        ]
        score = _grade_outlier_cleanup(data)
        assert score < 1.0, "Monitor outlier price should score < 1.0"

    def test_row_count_must_be_nine(self):
        """Must have exactly 9 rows (negative price row removed)."""
        # 10 rows (txn_id 9 with negative price still present)
        data = [
            {"txn_id": 1, "product": "Laptop", "price": 999.99, "quantity": 1, "currency": "USD", "region": "North America"},
            {"txn_id": 2, "product": "Mouse", "price": 25.00, "quantity": 3, "currency": "USD", "region": "North America"},
            {"txn_id": 3, "product": "Keyboard", "price": 75.50, "quantity": 0, "currency": "USD", "region": "Europe"},
            {"txn_id": 4, "product": "Monitor", "price": 500.00, "quantity": 1, "currency": "EUR", "region": "Europe"},
            {"txn_id": 5, "product": "Headset", "price": 150.00, "quantity": 10, "currency": "USD", "region": "Asia"},
            {"txn_id": 6, "product": "Webcam", "price": 89.99, "quantity": 0, "currency": "USD", "region": "North America"},
            {"txn_id": 7, "product": "Cable", "price": 12.99, "quantity": 5, "currency": "EUR", "region": "Europe"},
            {"txn_id": 8, "product": "Laptop", "price": 1050.00, "quantity": 1, "currency": "USD", "region": "North America"},
            {"txn_id": 9, "product": "Dock", "price": 199.99, "quantity": 2, "currency": "USD", "region": "Asia"},
            {"txn_id": 10, "product": "Ssd", "price": 120.00, "quantity": 100, "currency": "EUR", "region": "Europe"},
        ]
        score = _grade_outlier_cleanup(data)
        assert score < 1.0, "10 rows instead of 9 should score < 1.0"

    def test_cable_price_zero_fails(self):
        """Cable price 0.00 instead of 12.99 should fail."""
        data = [
            {"txn_id": 1, "product": "Laptop", "price": 999.99, "quantity": 1, "currency": "USD", "region": "North America"},
            {"txn_id": 2, "product": "Mouse", "price": 25.00, "quantity": 3, "currency": "USD", "region": "North America"},
            {"txn_id": 3, "product": "Keyboard", "price": 75.50, "quantity": 0, "currency": "USD", "region": "Europe"},
            {"txn_id": 4, "product": "Monitor", "price": 500.00, "quantity": 1, "currency": "EUR", "region": "Europe"},
            {"txn_id": 5, "product": "Headset", "price": 150.00, "quantity": 10, "currency": "USD", "region": "Asia"},
            {"txn_id": 6, "product": "Webcam", "price": 89.99, "quantity": 0, "currency": "USD", "region": "North America"},
            {"txn_id": 7, "product": "Cable", "price": 0.00, "quantity": 5, "currency": "EUR", "region": "Europe"},
            {"txn_id": 8, "product": "Laptop", "price": 1050.00, "quantity": 1, "currency": "USD", "region": "North America"},
            {"txn_id": 10, "product": "Ssd", "price": 120.00, "quantity": 100, "currency": "EUR", "region": "Europe"},
        ]
        score = _grade_outlier_cleanup(data)
        assert score < 1.0, "Cable price 0.00 should score < 1.0"
