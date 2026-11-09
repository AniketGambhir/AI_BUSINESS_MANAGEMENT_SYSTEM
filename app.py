from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import mysql.connector
from mysql.connector import Error
from functools import wraps
from datetime import date, datetime
import json
import math

app = Flask(__name__)
app.secret_key = "ai-business-management-system-secret-key"


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Aniket$2007",
    "database": "ai_business_management_system"
}


# ============================================================
# TABLE PERMISSIONS
# ============================================================

ADMIN_ALLOWED_TABLES = {
    "customer",
    "employee",
    "product",
    "inventory",
    "orders",
    "project",
    "invoice"
}

# Customer cannot be edited/updated
ADMIN_EDIT_BLOCKED_TABLES = {
    "customer"
}

USER_ALLOWED_TABLES = {
    "orders",
    "product",
    "project"
}


# ============================================================
# COLUMN CANDIDATES
# ============================================================

ORDER_DATE_COLUMNS = [
    "order_date",
    "date",
    "created_at",
    "created_date",
    "orderDate"
]

ORDER_AMOUNT_COLUMNS = [
    "total_amount",
    "amount",
    "total",
    "grand_total",
    "price",
    "order_amount"
]

ORDER_STATUS_COLUMNS = [
    "status",
    "order_status"
]

ORDER_PRODUCT_COLUMNS = [
    "product_id",
    "product",
    "productid"
]

PRODUCT_NAME_COLUMNS = [
    "product_name",
    "name",
    "product",
    "title"
]

PRODUCT_PRICE_COLUMNS = [
    "price",
    "unit_price",
    "selling_price",
    "sale_price"
]

INVENTORY_CATEGORY_COLUMNS = [
    "category",
    "type",
    "product_category"
]

INVENTORY_QUANTITY_COLUMNS = [
    "quantity",
    "stock",
    "stock_quantity",
    "qty"
]

INVENTORY_NAME_COLUMNS = [
    "product_name",
    "name",
    "item_name"
]

EMPLOYEE_DEPARTMENT_COLUMNS = [
    "department",
    "dept"
]

EMPLOYEE_STATUS_COLUMNS = [
    "status",
    "employee_status"
]

INVOICE_STATUS_COLUMNS = [
    "status",
    "invoice_status",
    "payment_status"
]

INVOICE_AMOUNT_COLUMNS = [
    "amount",
    "total_amount",
    "invoice_amount",
    "grand_total"
]

PROJECT_STATUS_COLUMNS = [
    "status",
    "project_status"
]

CUSTOMER_NAME_COLUMNS = [
    "customer_name",
    "name",
    "full_name"
]

CUSTOMER_EMAIL_COLUMNS = [
    "email",
    "email_address"
]


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)

        if connection.is_connected():
            return connection

    except Error as error:
        print("DATABASE CONNECTION ERROR:", error)

    return None


# ============================================================
# CLOSE CONNECTION
# ============================================================

def close_connection(connection, cursor=None):
    try:
        if cursor:
            cursor.close()
    except Exception:
        pass

    try:
        if connection and connection.is_connected():
            connection.close()
    except Exception:
        pass


# ============================================================
# JSON SAFE VALUE
# ============================================================

def clean_value(value):
    if value is None:
        return None

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, bytes):
        return value.decode("utf-8", errors="ignore")

    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return 0

    return value


def clean_row(row):
    return {
        key: clean_value(value)
        for key, value in row.items()
    }


# ============================================================
# SQL IDENTIFIER
# ============================================================

def quote_identifier(identifier):
    identifier = str(identifier)

    if not identifier.replace("_", "").isalnum():
        raise ValueError("Invalid SQL identifier")

    return f"`{identifier}`"


# ============================================================
# SESSION / ROLE HELPERS
# ============================================================

def current_role():
    return session.get("role")


def allowed_tables_for_role():
    if current_role() == "admin":
        return ADMIN_ALLOWED_TABLES

    if current_role() == "user":
        return USER_ALLOWED_TABLES

    return set()


def table_is_allowed(table_name):
    return table_name in allowed_tables_for_role()


def table_edit_allowed(table_name):
    if current_role() != "admin":
        return False

    if table_name not in ADMIN_ALLOWED_TABLES:
        return False

    if table_name in ADMIN_EDIT_BLOCKED_TABLES:
        return False

    return True


# ============================================================
# LOGIN DECORATORS
# ============================================================

def login_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):

        if "username" not in session:
            return redirect(url_for("login"))

        return function(*args, **kwargs)

    return wrapper


def admin_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):

        if "username" not in session:
            return redirect(url_for("login"))

        if session.get("role") != "admin":
            return redirect(url_for("user"))

        return function(*args, **kwargs)

    return wrapper


# ============================================================
# GET TABLE COLUMNS
# ============================================================

def get_table_columns(table_name):

    if table_name not in ADMIN_ALLOWED_TABLES:
        return []

    connection = get_db_connection()

    if not connection:
        return []

    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = %s
            AND TABLE_NAME = %s
            ORDER BY ORDINAL_POSITION
            """,
            (
                DB_CONFIG["database"],
                table_name
            )
        )

        rows = cursor.fetchall()

        return [
            row["COLUMN_NAME"]
            for row in rows
        ]

    except Error as error:
        print("COLUMN ERROR:", error)
        return []

    finally:
        close_connection(
            connection,
            cursor
        )


# ============================================================
# PRIMARY KEY
# ============================================================

def get_primary_key(table_name):

    connection = get_db_connection()

    if not connection:
        return None

    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = %s
            AND TABLE_NAME = %s
            AND CONSTRAINT_NAME = 'PRIMARY'
            ORDER BY ORDINAL_POSITION
            LIMIT 1
            """,
            (
                DB_CONFIG["database"],
                table_name
            )
        )

        row = cursor.fetchone()

        if row:
            return row["COLUMN_NAME"]

        return None

    except Error as error:
        print("PRIMARY KEY ERROR:", error)
        return None

    finally:
        close_connection(
            connection,
            cursor
        )


# ============================================================
# FIND COLUMN
# ============================================================

def find_column(columns, candidates):

    lower_map = {
        str(column).lower(): column
        for column in columns
    }

    for candidate in candidates:

        if candidate.lower() in lower_map:
            return lower_map[candidate.lower()]

    return None


# ============================================================
# GET TABLE DATA
# ============================================================

def get_table_data(table_name, limit=100):

    if not table_is_allowed(table_name):
        return []

    columns = get_table_columns(table_name)

    if not columns:
        return []

    connection = get_db_connection()

    if not connection:
        return []

    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)

        query = f"""
            SELECT *
            FROM {quote_identifier(table_name)}
            LIMIT %s
        """

        cursor.execute(
            query,
            (int(limit),)
        )

        rows = cursor.fetchall()

        return [
            clean_row(row)
            for row in rows
        ]

    except Error as error:
        print(
            f"GET {table_name} ERROR:",
            error
        )

        return []

    finally:
        close_connection(
            connection,
            cursor
        )


# ============================================================
# GET TABLE COUNT
# ============================================================

def get_table_count(table_name):

    if not table_is_allowed(table_name):
        return 0

    connection = get_db_connection()

    if not connection:
        return 0

    cursor = None

    try:
        cursor = connection.cursor()

        query = f"""
            SELECT COUNT(*)
            FROM {quote_identifier(table_name)}
        """

        cursor.execute(query)

        result = cursor.fetchone()

        return int(result[0]) if result else 0

    except Error as error:
        print(
            f"COUNT {table_name} ERROR:",
            error
        )

        return 0

    finally:
        close_connection(
            connection,
            cursor
        )


# ============================================================
# ORDER METRICS
# ============================================================

def get_order_metrics():

    result = {
        "total_orders": 0,
        "total_sales": 0,
        "average_order": 0,
        "highest_order": 0,
        "lowest_order": 0
    }

    if "orders" not in allowed_tables_for_role():
        return result

    columns = get_table_columns("orders")

    amount_column = find_column(
        columns,
        ORDER_AMOUNT_COLUMNS
    )

    if not amount_column:
        result["total_orders"] = get_table_count("orders")
        return result

    connection = get_db_connection()

    if not connection:
        return result

    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)

        query = f"""
            SELECT
                COUNT(*) AS total_orders,
                COALESCE(SUM({quote_identifier(amount_column)}), 0) AS total_sales,
                COALESCE(AVG({quote_identifier(amount_column)}), 0) AS average_order,
                COALESCE(MAX({quote_identifier(amount_column)}), 0) AS highest_order,
                COALESCE(MIN({quote_identifier(amount_column)}), 0) AS lowest_order
            FROM orders
        """

        cursor.execute(query)

        row = cursor.fetchone()

        if row:
            result = clean_row(row)

        return result

    except Error as error:
        print("ORDER METRICS ERROR:", error)
        return result

    finally:
        close_connection(
            connection,
            cursor
        )


# ============================================================
# MONTHLY SALES
# ============================================================

def get_monthly_sales():

    if "orders" not in allowed_tables_for_role():
        return []

    columns = get_table_columns("orders")

    date_column = find_column(
        columns,
        ORDER_DATE_COLUMNS
    )

    amount_column = find_column(
        columns,
        ORDER_AMOUNT_COLUMNS
    )

    if not date_column or not amount_column:
        return []

    connection = get_db_connection()

    if not connection:
        return []

    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)

        query = f"""
            SELECT
                DATE_FORMAT(
                    {quote_identifier(date_column)},
                    '%Y-%m'
                ) AS month,
                COALESCE(
                    SUM({quote_identifier(amount_column)}),
                    0
                ) AS sales
            FROM orders
            GROUP BY DATE_FORMAT(
                {quote_identifier(date_column)},
                '%Y-%m'
            )
            ORDER BY month
        """

        cursor.execute(query)

        rows = cursor.fetchall()

        return [
            clean_row(row)
            for row in rows
        ]

    except Error as error:
        print(
            "MONTHLY SALES ERROR:",
            error
        )

        return []

    finally:
        close_connection(
            connection,
            cursor
        )


# ============================================================
# ORDER STATUS
# ============================================================

def get_order_status():

    if "orders" not in allowed_tables_for_role():
        return []

    columns = get_table_columns("orders")

    status_column = find_column(
        columns,
        ORDER_STATUS_COLUMNS
    )

    if not status_column:
        return []

    connection = get_db_connection()

    if not connection:
        return []

    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)

        query = f"""
            SELECT
                COALESCE(
                    {quote_identifier(status_column)},
                    'Unknown'
                ) AS status,
                COUNT(*) AS count
            FROM orders
            GROUP BY {quote_identifier(status_column)}
            ORDER BY count DESC
        """

        cursor.execute(query)

        return [
            clean_row(row)
            for row in cursor.fetchall()
        ]

    except Error as error:
        print(
            "ORDER STATUS ERROR:",
            error
        )

        return []

    finally:
        close_connection(
            connection,
            cursor
        )


# ============================================================
# PRODUCT PERFORMANCE
# ============================================================

def get_product_performance():

    if "orders" not in allowed_tables_for_role():
        return []

    order_columns = get_table_columns("orders")
    product_columns = get_table_columns("product")

    order_product_column = find_column(
        order_columns,
        ORDER_PRODUCT_COLUMNS
    )

    product_id_column = find_column(
        product_columns,
        [
            "product_id",
            "id",
            "productid"
        ]
    )

    product_name_column = find_column(
        product_columns,
        PRODUCT_NAME_COLUMNS
    )

    if not order_product_column:
        return []

    connection = get_db_connection()

    if not connection:
        return []

    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)

        if (
            product_id_column
            and product_name_column
        ):

            query = f"""
                SELECT
                    COALESCE(
                        p.{quote_identifier(product_name_column)},
                        'Unknown'
                    ) AS product,
                    COUNT(o.{quote_identifier(order_product_column)})
                    AS count
                FROM orders o
                LEFT JOIN product p
                    ON o.{quote_identifier(order_product_column)}
                    =
                    p.{quote_identifier(product_id_column)}
                GROUP BY
                    p.{quote_identifier(product_name_column)}
                ORDER BY count DESC
                LIMIT 15
            """

        else:

            query = f"""
                SELECT
                    CAST(
                        {quote_identifier(order_product_column)}
                        AS CHAR
                    ) AS product,
                    COUNT(*) AS count
                FROM orders
                GROUP BY
                    {quote_identifier(order_product_column)}
                ORDER BY count DESC
                LIMIT 15
            """

        cursor.execute(query)

        return [
            clean_row(row)
            for row in cursor.fetchall()
        ]

    except Error as error:
        print(
            "PRODUCT PERFORMANCE ERROR:",
            error
        )

        return []

    finally:
        close_connection(
            connection,
            cursor
        )


# ============================================================
# PROJECT STATUS
# ============================================================

def get_project_status():

    if "project" not in allowed_tables_for_role():
        return []

    columns = get_table_columns("project")

    status_column = find_column(
        columns,
        PROJECT_STATUS_COLUMNS
    )

    if not status_column:
        return []

    connection = get_db_connection()

    if not connection:
        return []

    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)

        query = f"""
            SELECT
                COALESCE(
                    {quote_identifier(status_column)},
                    'Unknown'
                ) AS status,
                COUNT(*) AS count
            FROM project
            GROUP BY
                {quote_identifier(status_column)}
            ORDER BY count DESC
        """

        cursor.execute(query)

        return [
            clean_row(row)
            for row in cursor.fetchall()
        ]

    except Error as error:
        print(
            "PROJECT STATUS ERROR:",
            error
        )

        return []

    finally:
        close_connection(
            connection,
            cursor
        )


# ============================================================
# INVENTORY CATEGORY
# ============================================================

def get_inventory_category():

    if (
        current_role() != "admin"
        or "inventory" not in ADMIN_ALLOWED_TABLES
    ):
        return []

    columns = get_table_columns("inventory")

    category_column = find_column(
        columns,
        INVENTORY_CATEGORY_COLUMNS
    )

    quantity_column = find_column(
        columns,
        INVENTORY_QUANTITY_COLUMNS
    )

    if not category_column:
        return []

    connection = get_db_connection()

    if not connection:
        return []

    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)

        if quantity_column:

            query = f"""
                SELECT
                    COALESCE(
                        {quote_identifier(category_column)},
                        'Unknown'
                    ) AS category,
                    COALESCE(
                        SUM(
                            {quote_identifier(quantity_column)}
                        ),
                        0
                    ) AS quantity
                FROM inventory
                GROUP BY
                    {quote_identifier(category_column)}
                ORDER BY quantity DESC
            """

        else:

            query = f"""
                SELECT
                    COALESCE(
                        {quote_identifier(category_column)},
                        'Unknown'
                    ) AS category,
                    COUNT(*) AS quantity
                FROM inventory
                GROUP BY
                    {quote_identifier(category_column)}
                ORDER BY quantity DESC
            """

        cursor.execute(query)

        return [
            clean_row(row)
            for row in cursor.fetchall()
        ]

    except Error as error:
        print(
            "INVENTORY CATEGORY ERROR:",
            error
        )

        return []

    finally:
        close_connection(
            connection,
            cursor
        )


# ============================================================
# INVOICE STATUS
# ============================================================

def get_invoice_status():

    if current_role() != "admin":
        return []

    columns = get_table_columns("invoice")

    status_column = find_column(
        columns,
        INVOICE_STATUS_COLUMNS
    )

    if not status_column:
        return []

    connection = get_db_connection()

    if not connection:
        return []

    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)

        query = f"""
            SELECT
                COALESCE(
                    {quote_identifier(status_column)},
                    'Unknown'
                ) AS status,
                COUNT(*) AS count
            FROM invoice
            GROUP BY
                {quote_identifier(status_column)}
            ORDER BY count DESC
        """

        cursor.execute(query)

        return [
            clean_row(row)
            for row in cursor.fetchall()
        ]

    except Error as error:
        print(
            "INVOICE STATUS ERROR:",
            error
        )

        return []

    finally:
        close_connection(
            connection,
            cursor
        )


# ============================================================
# EMPLOYEE DEPARTMENT
# ============================================================

def get_employee_department():

    if current_role() != "admin":
        return []

    columns = get_table_columns("employee")

    department_column = find_column(
        columns,
        EMPLOYEE_DEPARTMENT_COLUMNS
    )

    if not department_column:
        return []

    connection = get_db_connection()

    if not connection:
        return []

    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)

        query = f"""
            SELECT
                COALESCE(
                    {quote_identifier(department_column)},
                    'Unknown'
                ) AS department,
                COUNT(*) AS count
            FROM employee
            GROUP BY
                {quote_identifier(department_column)}
            ORDER BY count DESC
        """

        cursor.execute(query)

        return [
            clean_row(row)
            for row in cursor.fetchall()
        ]

    except Error as error:
        print(
            "EMPLOYEE DEPARTMENT ERROR:",
            error
        )

        return []

    finally:
        close_connection(
            connection,
            cursor
        )


# ============================================================
# RECENT ORDERS
# ============================================================

def get_recent_orders(limit=10):

    if "orders" not in allowed_tables_for_role():
        return []

    columns = get_table_columns("orders")

    date_column = find_column(
        columns,
        ORDER_DATE_COLUMNS
    )

    connection = get_db_connection()

    if not connection:
        return []

    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)

        if date_column:

            query = f"""
                SELECT *
                FROM orders
                ORDER BY
                    {quote_identifier(date_column)}
                    DESC
                LIMIT %s
            """

        else:

            query = """
                SELECT *
                FROM orders
                LIMIT %s
            """

        cursor.execute(
            query,
            (limit,)
        )

        return [
            clean_row(row)
            for row in cursor.fetchall()
        ]

    except Error as error:
        print(
            "RECENT ORDERS ERROR:",
            error
        )

        return []

    finally:
        close_connection(
            connection,
            cursor
        )


# ============================================================
# AI ANALYSIS
# ============================================================

def generate_ai_analysis():

    metrics = get_order_metrics()

    total_orders = float(
        metrics.get("total_orders", 0)
        or 0
    )

    total_sales = float(
        metrics.get("total_sales", 0)
        or 0
    )

    average_order = float(
        metrics.get("average_order", 0)
        or 0
    )

    highest_order = float(
        metrics.get("highest_order", 0)
        or 0
    )

    score = 50

    if total_orders > 0:
        score += 10

    if total_sales > 0:
        score += 10

    if average_order > 0:
        score += 10

    order_status = get_order_status()

    if order_status:
        score += 5

    product_performance = (
        get_product_performance()
    )

    if product_performance:
        score += 5

    project_status = get_project_status()

    if project_status:
        score += 5

    if current_role() == "admin":

        inventory_data = (
            get_inventory_category()
        )

        invoice_data = (
            get_invoice_status()
        )

        employee_data = (
            get_employee_department()
        )

        if inventory_data:
            score += 2

        if invoice_data:
            score += 2

        if employee_data:
            score += 1

    score = max(
        0,
        min(100, score)
    )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    if score >= 85:
        health_text = "Excellent"

    elif score >= 70:
        health_text = "Good"

    elif score >= 50:
        health_text = "Moderate"

    else:
        health_text = "Needs Attention"

    summary = (
        f"The current business health is {health_text} "
        f"with a score of {score}/100. "
        f"The system recorded {int(total_orders)} orders "
        f"with total sales of ₹{total_sales:,.2f}. "
        f"The average order value is "
        f"₹{average_order:,.2f} and the highest "
        f"recorded order is ₹{highest_order:,.2f}."
    )

    strengths = []

    if total_orders > 0:
        strengths.append(
            f"The business has recorded {int(total_orders)} orders."
        )

    if total_sales > 0:
        strengths.append(
            f"Total recorded sales are ₹{total_sales:,.2f}."
        )

    if product_performance:
        best_product = (
            product_performance[0]
        )

        strengths.append(
            "Product/order activity is available "
            "for performance analysis."
        )

    if project_status:
        strengths.append(
            "Project information is available "
            "for operational monitoring."
        )

    if not strengths:
        strengths.append(
            "The system is ready for business data analysis."
        )

    risks = []

    if total_orders == 0:
        risks.append(
            "No orders are currently available."
        )

    if total_sales == 0:
        risks.append(
            "No sales amount is currently available."
        )

    if not order_status:
        risks.append(
            "Order status information is unavailable."
        )

    if current_role() == "admin":

        inventory_data = (
            get_inventory_category()
        )

        if not inventory_data:
            risks.append(
                "Inventory category data is unavailable."
            )

    if not risks:
        risks.append(
            "No major data-quality risks were detected "
            "from the available dashboard data."
        )

    recommendations = [
        "Monitor monthly sales trends regularly.",
        "Identify high-performing products and focus on them.",
        "Track order statuses to reduce pending or cancelled orders.",
        "Keep inventory quantities updated.",
        "Review invoice and payment status regularly."
    ]

    if total_orders == 0:
        recommendations.insert(
            0,
            "Add order records so the system can calculate meaningful business trends."
        )

    return {
        "score": score,
        "health_score": score,
        "summary": summary,

        "metrics": {
            "Total Orders": int(total_orders),
            "Total Sales": f"₹{total_sales:,.2f}",
            "Average Order": f"₹{average_order:,.2f}",
            "Highest Order": f"₹{highest_order:,.2f}"
        },

        "strengths": strengths,
        "risks": risks,
        "recommendations": recommendations,

        "order_status": order_status,
        "product_performance": product_performance,
        "project_status": project_status
    }


# ============================================================
# LOGIN PAGE
# ============================================================

@app.route("/")
def home():

    if "username" in session:

        if session.get("role") == "admin":
            return redirect(url_for("admin"))

        return redirect(url_for("user"))

    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():

    error = None

    if request.method == "POST":

        username = (
            request.form.get("username", "")
            .strip()
        )

        password = (
            request.form.get("password", "")
            .strip()
        )

        if (
            username == "admin"
            and password == "Admin@123"
        ):

            session["username"] = "admin"
            session["role"] = "admin"

            return redirect(
                url_for("admin")
            )

        if (
            username == "user"
            and password == "User@123"
        ):

            session["username"] = "user"
            session["role"] = "user"

            return redirect(
                url_for("user")
            )

        error = "Invalid username or password."

    return render_template(
        "login.html",
        error=error
    )


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# ============================================================
# ADMIN PAGE
# ============================================================

@app.route("/admin")
@admin_required
def admin():

    return render_template(
        "admin.html",
        username=session.get("username"),
        role=session.get("role")
    )


# ============================================================
# USER PAGE
# ============================================================

@app.route("/user")
@login_required
def user():

    if session.get("role") != "user":
        return redirect(
            url_for("admin")
        )

    return render_template(
        "user.html",
        username=session.get("username"),
        role=session.get("role")
    )


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/dashboard")
@login_required
def dashboard():

    if session.get("role") == "admin":
        return redirect(
            url_for("admin")
        )

    return redirect(
        url_for("user")
    )


# ============================================================
# DATABASE TEST API
# ============================================================

@app.route("/api/database-test")
@login_required
def database_test():

    connection = get_db_connection()

    if not connection:
        return jsonify({
            "success": False,
            "message": "Database connection failed."
        }), 500

    close_connection(connection)

    return jsonify({
        "success": True,
        "message": "Database connection successful.",
        "database": DB_CONFIG["database"]
    })


# ============================================================
# TABLE LIST API
# ============================================================

@app.route("/api/tables")
@login_required
def api_tables():

    return jsonify({
        "success": True,
        "tables": sorted(
            list(
                allowed_tables_for_role()
            )
        )
    })


# ============================================================
# DASHBOARD API
# ============================================================

@app.route("/api/dashboard")
@login_required
def api_dashboard():

    metrics = get_order_metrics()

    counts = {}

    for table in allowed_tables_for_role():

        counts[
            f"{table}_count"
        ] = get_table_count(table)

    result = {
        "success": True,

        "role": current_role(),

        "metrics": metrics,

        "counts": counts,

        "total_orders":
            metrics.get(
                "total_orders",
                0
            ),

        "total_sales":
            metrics.get(
                "total_sales",
                0
            ),

        "average_order":
            metrics.get(
                "average_order",
                0
            ),

        "highest_order":
            metrics.get(
                "highest_order",
                0
            ),

        "monthly_sales":
            get_monthly_sales(),

        "order_status":
            get_order_status(),

        "product_performance":
            get_product_performance(),

        "project_status":
            get_project_status(),

        "recent_orders":
            get_recent_orders(),

        "records": {}
    }

    # --------------------------------------------------------
    # ADMIN DATA
    # --------------------------------------------------------

    if current_role() == "admin":

        result["inventory_category"] = (
            get_inventory_category()
        )

        result["invoice_status"] = (
            get_invoice_status()
        )

        result["employee_department"] = (
            get_employee_department()
        )

        for table in ADMIN_ALLOWED_TABLES:

            result["records"][table] = (
                get_table_data(
                    table,
                    5
                )
            )

    # --------------------------------------------------------
    # USER DATA
    # --------------------------------------------------------

    else:

        for table in USER_ALLOWED_TABLES:

            result["records"][table] = (
                get_table_data(
                    table,
                    5
                )
            )

    return jsonify(result)


# ============================================================
# AI ANALYSIS API
# ============================================================

@app.route("/api/ai-analysis")
@login_required
def api_ai_analysis():

    try:

        analysis = (
            generate_ai_analysis()
        )

        return jsonify({
            "success": True,
            **analysis
        })

    except Exception as error:

        print(
            "AI ANALYSIS ERROR:",
            error
        )

        return jsonify({
            "success": False,
            "score": 0,
            "summary": "Unable to generate AI analysis.",
            "strengths": [],
            "risks": [
                str(error)
            ],
            "recommendations": []
        }), 500


# ============================================================
# GET TABLE DATA API
# ============================================================

@app.route(
    "/api/table/<table_name>",
    methods=["GET"]
)
@login_required
def api_get_table(table_name):

    if not table_is_allowed(table_name):

        return jsonify({
            "success": False,
            "error": "You are not allowed to access this table."
        }), 403

    rows = get_table_data(
        table_name,
        1000
    )

    columns = get_table_columns(
        table_name
    )

    return jsonify({
        "success": True,
        "table": table_name,
        "columns": columns,
        "rows": rows,
        "count": len(rows)
    })


# ============================================================
# GET TABLE COLUMNS API
# ============================================================

@app.route(
    "/api/table/<table_name>/columns",
    methods=["GET"]
)
@login_required
def api_table_columns(table_name):

    if not table_is_allowed(table_name):

        return jsonify({
            "success": False,
            "error": "You are not allowed to access this table."
        }), 403

    columns = get_table_columns(
        table_name
    )

    return jsonify({
        "success": True,
        "columns": columns
    })


# ============================================================
# ADD RECORD
# ============================================================

@app.route(
    "/api/table/<table_name>",
    methods=["POST"]
)
@login_required
def api_add_record(table_name):

    if current_role() != "admin":

        return jsonify({
            "success": False,
            "error": "Admin access required."
        }), 403

    if table_name not in ADMIN_ALLOWED_TABLES:

        return jsonify({
            "success": False,
            "error": "Invalid table."
        }), 403

    data = request.get_json(
        silent=True
    )

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "error": "Invalid JSON data."
        }), 400

    columns = get_table_columns(
        table_name
    )

    valid_data = {}

    for key, value in data.items():

        if key not in columns:
            continue

        # Skip blank values
        if value == "":
            continue

        valid_data[key] = value

    if not valid_data:

        return jsonify({
            "success": False,
            "error": "No valid fields supplied."
        }), 400

    connection = get_db_connection()

    if not connection:

        return jsonify({
            "success": False,
            "error": "Database connection failed."
        }), 500

    cursor = None

    try:

        cursor = connection.cursor()

        column_names = list(
            valid_data.keys()
        )

        placeholders = ", ".join(
            ["%s"] *
            len(column_names)
        )

        quoted_columns = ", ".join(
            quote_identifier(column)
            for column in column_names
        )

        query = f"""
            INSERT INTO {quote_identifier(table_name)}
            ({quoted_columns})
            VALUES ({placeholders})
        """

        cursor.execute(
            query,
            [
                valid_data[column]
                for column in column_names
            ]
        )

        connection.commit()

        return jsonify({
            "success": True,
            "message": "Record added successfully.",
            "id": cursor.lastrowid
        })

    except Error as error:

        connection.rollback()

        print(
            "INSERT ERROR:",
            error
        )

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500

    finally:

        close_connection(
            connection,
            cursor
        )


# ============================================================
# UPDATE RECORD
# ============================================================

@app.route(
    "/api/table/<table_name>",
    methods=["PUT"]
)
@login_required
def api_update_record(table_name):

    if not table_edit_allowed(
        table_name
    ):

        return jsonify({
            "success": False,
            "error": (
                "This table cannot be edited."
            )
        }), 403

    data = request.get_json(
        silent=True
    )

    if not isinstance(data, dict):

        return jsonify({
            "success": False,
            "error": "Invalid JSON data."
        }), 400

    primary_key = get_primary_key(
        table_name
    )

    if not primary_key:

        return jsonify({
            "success": False,
            "error": "Primary key not found."
        }), 400

    if primary_key not in data:

        return jsonify({
            "success": False,
            "error": (
                f"Primary key '{primary_key}' is required."
            )
        }), 400

    primary_value = data[
        primary_key
    ]

    columns = get_table_columns(
        table_name
    )

    update_fields = []

    update_values = []

    for key, value in data.items():

        if key == primary_key:
            continue

        if key not in columns:
            continue

        update_fields.append(
            f"{quote_identifier(key)} = %s"
        )

        update_values.append(value)

    if not update_fields:

        return jsonify({
            "success": False,
            "error": "No fields to update."
        }), 400

    update_values.append(
        primary_value
    )

    query = f"""
        UPDATE {quote_identifier(table_name)}
        SET {", ".join(update_fields)}
        WHERE {quote_identifier(primary_key)} = %s
    """

    connection = get_db_connection()

    if not connection:

        return jsonify({
            "success": False,
            "error": "Database connection failed."
        }), 500

    cursor = None

    try:

        cursor = connection.cursor()

        cursor.execute(
            query,
            update_values
        )

        connection.commit()

        return jsonify({
            "success": True,
            "message": "Record updated successfully.",
            "affected_rows": cursor.rowcount
        })

    except Error as error:

        connection.rollback()

        print(
            "UPDATE ERROR:",
            error
        )

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500

    finally:

        close_connection(
            connection,
            cursor
        )


# ============================================================
# DELETE RECORD
# ============================================================

@app.route(
    "/api/table/<table_name>/<primary_value>",
    methods=["DELETE"]
)
@login_required
def api_delete_record(
    table_name,
    primary_value
):

    if current_role() != "admin":

        return jsonify({
            "success": False,
            "error": "Admin access required."
        }), 403

    if table_name not in ADMIN_ALLOWED_TABLES:

        return jsonify({
            "success": False,
            "error": "Invalid table."
        }), 403

    primary_key = get_primary_key(
        table_name
    )

    if not primary_key:

        return jsonify({
            "success": False,
            "error": "Primary key not found."
        }), 400

    connection = get_db_connection()

    if not connection:

        return jsonify({
            "success": False,
            "error": "Database connection failed."
        }), 500

    cursor = None

    try:

        cursor = connection.cursor()

        query = f"""
            DELETE FROM {quote_identifier(table_name)}
            WHERE {quote_identifier(primary_key)} = %s
        """

        cursor.execute(
            query,
            (primary_value,)
        )

        connection.commit()

        return jsonify({
            "success": True,
            "message": "Record deleted successfully.",
            "affected_rows": cursor.rowcount
        })

    except Error as error:

        connection.rollback()

        print(
            "DELETE ERROR:",
            error
        )

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500

    finally:

        close_connection(
            connection,
            cursor
        )


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def page_not_found(error):

    return jsonify({
        "success": False,
        "error": "Page or API endpoint not found."
    }), 404


@app.errorhandler(500)
def internal_server_error(error):

    return jsonify({
        "success": False,
        "error": "Internal server error."
    }), 500


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("AI BUSINESS MANAGEMENT SYSTEM")
    print("=" * 60)
    print("Database:", DB_CONFIG["database"])
    print("Admin: admin / Admin@123")
    print("User : user / User@123")
    print("URL  : http://127.0.0.1:5000")
    print("=" * 60)

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )