from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify
)

from functools import wraps
from decimal import Decimal
from datetime import date, datetime
import json

from database import get_connection, test_connection
from ai_analysis import build_admin_analysis, build_user_analysis


app = Flask(__name__)

app.secret_key = "AI_BUSINESS_MANAGEMENT_SECRET_2026"


# ============================================================
# USERS
# ============================================================

USERS = {
    "admin": {
        "password": "Admin@123",
        "role": "admin"
    },

    "user": {
        "password": "User@123",
        "role": "user"
    }
}


# ============================================================
# TABLE PERMISSIONS
# ============================================================

ALL_TABLES = {
    "customer",
    "orders",
    "product",
    "inventory",
    "employee",
    "project",
    "invoice"
}

USER_ALLOWED_TABLES = {
    "customer",
    "orders",
    "product",
    "project"
}

ADMIN_ALLOWED_TABLES = {
    "customer",
    "orders",
    "product",
    "inventory",
    "employee",
    "project",
    "invoice"
}

# CUSTOMER CAN NOT BE EDITED
ADMIN_EDIT_BLOCKED_TABLES = {
    "customer"
}


TABLE_DISPLAY_NAMES = {
    "customer": "Customers",
    "orders": "Orders",
    "product": "Products",
    "inventory": "Inventory",
    "employee": "Employees",
    "project": "Projects",
    "invoice": "Invoices"
}


# ============================================================
# BASIC HELPERS
# ============================================================

def serialize_value(value):
    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    return value


def serialize_row(row):
    return {
        key: serialize_value(value)
        for key, value in row.items()
    }


def get_role():
    return session.get("role")


def is_logged_in():
    return "username" in session and "role" in session


def user_can_access_table(table_name):
    role = get_role()

    if role == "admin":
        return table_name in ADMIN_ALLOWED_TABLES

    if role == "user":
        return table_name in USER_ALLOWED_TABLES

    return False


def admin_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):

        if not is_logged_in():
            return jsonify({
                "success": False,
                "error": "Login required"
            }), 401

        if get_role() != "admin":
            return jsonify({
                "success": False,
                "error": "Admin access required"
            }), 403

        return function(*args, **kwargs)

    return wrapper


def login_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):

        if not is_logged_in():
            return jsonify({
                "success": False,
                "error": "Login required"
            }), 401

        return function(*args, **kwargs)

    return wrapper


def valid_table(table_name):
    return table_name in ALL_TABLES


# ============================================================
# DATABASE SCHEMA HELPERS
# ============================================================

def get_table_columns(connection, table_name):

    if not valid_table(table_name):
        return []

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(f"SHOW COLUMNS FROM `{table_name}`")
        rows = cursor.fetchall()

        return rows

    except Exception as e:
        print("Column error:", e)
        return []

    finally:
        cursor.close()


def get_column_names(connection, table_name):

    columns = get_table_columns(connection, table_name)

    return [
        column["Field"]
        for column in columns
    ]


def get_primary_key(connection, table_name):

    columns = get_table_columns(connection, table_name)

    for column in columns:
        if column.get("Key") == "PRI":
            return column["Field"]

    # fallback
    names = [
        column["Field"]
        for column in columns
    ]

    for candidate in [
        "id",
        f"{table_name}_id",
        "customer_id",
        "product_id",
        "order_id",
        "employee_id",
        "project_id",
        "invoice_id"
    ]:
        if candidate in names:
            return candidate

    return names[0] if names else None


def find_column(connection, table_name, candidates):

    columns = get_column_names(connection, table_name)

    lower_map = {
        column.lower(): column
        for column in columns
    }

    for candidate in candidates:

        if candidate.lower() in lower_map:
            return lower_map[candidate.lower()]

    return None


# ============================================================
# LOGIN
# ============================================================

@app.route("/")
def home():

    if not is_logged_in():
        return redirect(url_for("login"))

    if get_role() == "admin":
        return redirect(url_for("admin_dashboard"))

    return redirect(url_for("user_dashboard"))


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        account = USERS.get(username)

        if account and account["password"] == password:

            session["username"] = username
            session["role"] = account["role"]

            if account["role"] == "admin":
                return redirect(url_for("admin_dashboard"))

            return redirect(url_for("user_dashboard"))

        return render_template(
            "login.html",
            error="Invalid username or password"
        )

    return render_template("login.html")


@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# ============================================================
# PAGES
# ============================================================

@app.route("/admin")
def admin_dashboard():

    if not is_logged_in():
        return redirect(url_for("login"))

    if get_role() != "admin":
        return redirect(url_for("user_dashboard"))

    return render_template(
        "admin.html",
        username=session.get("username")
    )


@app.route("/user")
def user_dashboard():

    if not is_logged_in():
        return redirect(url_for("login"))

    if get_role() != "user":
        return redirect(url_for("admin_dashboard"))

    return render_template(
        "user.html",
        username=session.get("username")
    )


# ============================================================
# TABLE LIST
# ============================================================

@app.route("/api/tables")
@login_required
def api_tables():

    if get_role() == "admin":
        tables = sorted(ADMIN_ALLOWED_TABLES)
    else:
        tables = sorted(USER_ALLOWED_TABLES)

    return jsonify({
        "success": True,
        "tables": [
            {
                "name": table,
                "display_name": TABLE_DISPLAY_NAMES.get(
                    table,
                    table.title()
                )
            }
            for table in tables
        ]
    })


# ============================================================
# TABLE COLUMNS
# ============================================================

@app.route("/api/table/<table_name>/columns")
@login_required
def table_columns(table_name):

    if not valid_table(table_name):
        return jsonify({
            "success": False,
            "error": "Invalid table"
        }), 400

    if not user_can_access_table(table_name):
        return jsonify({
            "success": False,
            "error": "Access denied"
        }), 403

    connection = get_connection()

    if not connection:
        return jsonify({
            "success": False,
            "error": "Database connection failed"
        }), 500

    try:

        columns = get_table_columns(
            connection,
            table_name
        )

        return jsonify({
            "success": True,
            "table": table_name,
            "primary_key": get_primary_key(
                connection,
                table_name
            ),
            "columns": columns
        })

    finally:
        connection.close()


# ============================================================
# GET TABLE DATA
# ============================================================

@app.route("/api/table/<table_name>")
@login_required
def get_table_data(table_name):

    if not valid_table(table_name):
        return jsonify({
            "success": False,
            "error": "Invalid table"
        }), 400

    if not user_can_access_table(table_name):
        return jsonify({
            "success": False,
            "error": "Access denied"
        }), 403

    connection = get_connection()

    if not connection:
        return jsonify({
            "success": False,
            "error": "Database connection failed"
        }), 500

    try:

        columns = get_column_names(
            connection,
            table_name
        )

        primary_key = get_primary_key(
            connection,
            table_name
        )

        search = request.args.get(
            "search",
            ""
        ).strip()

        limit = min(
            int(request.args.get("limit", 100)),
            500
        )

        offset = max(
            int(request.args.get("offset", 0)),
            0
        )

        cursor = connection.cursor(
            dictionary=True
        )

        if search and columns:

            conditions = []

            for column in columns:
                conditions.append(
                    f"CAST(`{column}` AS CHAR) LIKE %s"
                )

            query = f"""
                SELECT *
                FROM `{table_name}`
                WHERE {" OR ".join(conditions)}
                LIMIT %s OFFSET %s
            """

            values = [
                f"%{search}%"
                for _ in columns
            ]

            values.extend([
                limit,
                offset
            ])

            cursor.execute(
                query,
                values
            )

        else:

            query = f"""
                SELECT *
                FROM `{table_name}`
                LIMIT %s OFFSET %s
            """

            cursor.execute(
                query,
                (limit, offset)
            )

        rows = cursor.fetchall()

        return jsonify({
            "success": True,
            "table": table_name,
            "columns": columns,
            "primary_key": primary_key,
            "rows": [
                serialize_row(row)
                for row in rows
            ]
        })

    except Exception as e:

        print("GET TABLE ERROR:", e)

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

    finally:
        connection.close()


# ============================================================
# INSERT
# ============================================================

@app.route("/api/table/<table_name>", methods=["POST"])
@admin_required
def insert_row(table_name):

    if table_name not in ADMIN_ALLOWED_TABLES:
        return jsonify({
            "success": False,
            "error": "Access denied"
        }), 403

    data = request.get_json(silent=True) or {}

    if not data:
        return jsonify({
            "success": False,
            "error": "No data supplied"
        }), 400

    connection = get_connection()

    if not connection:
        return jsonify({
            "success": False,
            "error": "Database connection failed"
        }), 500

    try:

        columns = get_column_names(
            connection,
            table_name
        )

        primary_key = get_primary_key(
            connection,
            table_name
        )

        valid_data = {}

        for key, value in data.items():

            if key not in columns:
                continue

            # Don't manually insert auto increment PK
            if key == primary_key:
                continue

            if value == "":
                value = None

            valid_data[key] = value

        if not valid_data:
            return jsonify({
                "success": False,
                "error": "No valid columns supplied"
            }), 400

        column_sql = ", ".join(
            f"`{key}`"
            for key in valid_data
        )

        placeholders = ", ".join(
            ["%s"] * len(valid_data)
        )

        query = f"""
            INSERT INTO `{table_name}`
            ({column_sql})
            VALUES ({placeholders})
        """

        cursor = connection.cursor()

        cursor.execute(
            query,
            list(valid_data.values())
        )

        connection.commit()

        new_id = cursor.lastrowid

        cursor.close()

        return jsonify({
            "success": True,
            "message": "Record added successfully",
            "id": new_id
        })

    except Exception as e:

        connection.rollback()

        print("INSERT ERROR:", e)

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

    finally:
        connection.close()


# ============================================================
# UPDATE
# ============================================================

@app.route(
    "/api/table/<table_name>/<path:primary_value>",
    methods=["PUT"]
)
@admin_required
def update_row(table_name, primary_value):

    if table_name not in ADMIN_ALLOWED_TABLES:
        return jsonify({
            "success": False,
            "error": "Access denied"
        }), 403

    # IMPORTANT:
    # Customer can NOT be edited.
    if table_name in ADMIN_EDIT_BLOCKED_TABLES:
        return jsonify({
            "success": False,
            "error": "Customer records cannot be edited by admin."
        }), 403

    data = request.get_json(silent=True) or {}

    connection = get_connection()

    if not connection:
        return jsonify({
            "success": False,
            "error": "Database connection failed"
        }), 500

    try:

        columns = get_column_names(
            connection,
            table_name
        )

        primary_key = get_primary_key(
            connection,
            table_name
        )

        if not primary_key:
            return jsonify({
                "success": False,
                "error": "Primary key not found"
            }), 400

        update_data = {}

        for key, value in data.items():

            if key not in columns:
                continue

            if key == primary_key:
                continue

            if value == "":
                value = None

            update_data[key] = value

        if not update_data:
            return jsonify({
                "success": False,
                "error": "Nothing to update"
            }), 400

        assignments = ", ".join(
            f"`{key}` = %s"
            for key in update_data
        )

        query = f"""
            UPDATE `{table_name}`
            SET {assignments}
            WHERE `{primary_key}` = %s
        """

        values = list(
            update_data.values()
        )

        values.append(primary_value)

        cursor = connection.cursor()

        cursor.execute(
            query,
            values
        )

        connection.commit()

        affected = cursor.rowcount

        cursor.close()

        return jsonify({
            "success": True,
            "message": "Record updated successfully",
            "affected": affected
        })

    except Exception as e:

        connection.rollback()

        print("UPDATE ERROR:", e)

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

    finally:
        connection.close()


# ============================================================
# DELETE
# ============================================================

@app.route(
    "/api/table/<table_name>/<path:primary_value>",
    methods=["DELETE"]
)
@admin_required
def delete_row(table_name, primary_value):

    if table_name not in ADMIN_ALLOWED_TABLES:
        return jsonify({
            "success": False,
            "error": "Access denied"
        }), 403

    connection = get_connection()

    if not connection:
        return jsonify({
            "success": False,
            "error": "Database connection failed"
        }), 500

    try:

        primary_key = get_primary_key(
            connection,
            table_name
        )

        if not primary_key:
            return jsonify({
                "success": False,
                "error": "Primary key not found"
            }), 400

        query = f"""
            DELETE FROM `{table_name}`
            WHERE `{primary_key}` = %s
        """

        cursor = connection.cursor()

        cursor.execute(
            query,
            (primary_value,)
        )

        connection.commit()

        affected = cursor.rowcount

        cursor.close()

        return jsonify({
            "success": True,
            "message": "Record deleted successfully",
            "affected": affected
        })

    except Exception as e:

        connection.rollback()

        print("DELETE ERROR:", e)

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

    finally:
        connection.close()


# ============================================================
# SAFE COUNT
# ============================================================

def table_count(connection, table_name):

    try:

        cursor = connection.cursor()

        cursor.execute(
            f"SELECT COUNT(*) FROM `{table_name}`"
        )

        result = cursor.fetchone()

        cursor.close()

        return int(result[0]) if result else 0

    except Exception as e:

        print(
            f"Count error for {table_name}:",
            e
        )

        return 0


# ============================================================
# DASHBOARD DATA
# ============================================================

@app.route("/api/dashboard")
@login_required
def dashboard_data():

    connection = get_connection()

    if not connection:
        return jsonify({
            "success": False,
            "error": "Database connection failed"
        }), 500

    role = get_role()

    try:

        result = {
            "role": role,

            "counts": {},

            "statistics": {
                "total_orders": 0,
                "total_sales": 0,
                "average_order": 0,
                "highest_order": 0
            },

            "charts": {},

            "recent_orders": [],

            "ai": {}
        }

        # ----------------------------------------------------
        # COUNTS
        # ----------------------------------------------------

        allowed_tables = (
            ADMIN_ALLOWED_TABLES
            if role == "admin"
            else USER_ALLOWED_TABLES
        )

        for table in allowed_tables:
            result["counts"][table] = table_count(
                connection,
                table
            )

        # ----------------------------------------------------
        # ORDERS
        # ----------------------------------------------------

        if "orders" in allowed_tables:

            cursor = connection.cursor(
                dictionary=True
            )

            amount_column = find_column(
                connection,
                "orders",
                [
                    "total_amount",
                    "amount",
                    "total",
                    "order_amount",
                    "price"
                ]
            )

            status_column = find_column(
                connection,
                "orders",
                [
                    "status",
                    "order_status"
                ]
            )

            order_date_column = find_column(
                connection,
                "orders",
                [
                    "order_date",
                    "date",
                    "created_at",
                    "created_date"
                ]
            )

            if amount_column:

                query = f"""
                    SELECT
                        COALESCE(SUM(`{amount_column}`), 0) AS total_sales,
                        COALESCE(AVG(`{amount_column}`), 0) AS average_order,
                        COALESCE(MAX(`{amount_column}`), 0) AS highest_order
                    FROM `orders`
                """

                cursor.execute(query)

                row = cursor.fetchone()

                result["statistics"][
                    "total_sales"
                ] = serialize_value(
                    row["total_sales"]
                )

                result["statistics"][
                    "average_order"
                ] = serialize_value(
                    row["average_order"]
                )

                result["statistics"][
                    "highest_order"
                ] = serialize_value(
                    row["highest_order"]
                )

            result["statistics"][
                "total_orders"
            ] = table_count(
                connection,
                "orders"
            )

            # -----------------------------------------------
            # ORDER STATUS
            # -----------------------------------------------

            status_chart = []

            completed = 0
            pending = 0
            cancelled = 0

            if status_column:

                cursor.execute(
                    f"""
                    SELECT
                        COALESCE(`{status_column}`, 'Unknown') AS status,
                        COUNT(*) AS total
                    FROM `orders`
                    GROUP BY `{status_column}`
                    ORDER BY total DESC
                    """
                )

                rows = cursor.fetchall()

                for row in rows:

                    status = str(
                        row["status"]
                    )

                    total = int(
                        row["total"]
                    )

                    status_chart.append({
                        "label": status,
                        "value": total
                    })

                    lower = status.lower()

                    if "complete" in lower or "deliver" in lower:
                        completed += total

                    elif "pending" in lower or "process" in lower:
                        pending += total

                    elif "cancel" in lower:
                        cancelled += total

            result["charts"][
                "order_status"
            ] = status_chart

            # -----------------------------------------------
            # MONTHLY SALES
            # -----------------------------------------------

            monthly_sales = []

            if amount_column and order_date_column:

                try:

                    cursor.execute(
                        f"""
                        SELECT
                            DATE_FORMAT(
                                `{order_date_column}`,
                                '%Y-%m'
                            ) AS month,
                            COALESCE(
                                SUM(`{amount_column}`),
                                0
                            ) AS sales
                        FROM `orders`
                        GROUP BY
                            DATE_FORMAT(
                                `{order_date_column}`,
                                '%Y-%m'
                            )
                        ORDER BY month
                        """
                    )

                    rows = cursor.fetchall()

                    for row in rows:
                        monthly_sales.append({
                            "label": row["month"],
                            "value": serialize_value(
                                row["sales"]
                            )
                        })

                except Exception as e:
                    print(
                        "Monthly sales error:",
                        e
                    )

            result["charts"][
                "monthly_sales"
            ] = monthly_sales

            # -----------------------------------------------
            # RECENT ORDERS
            # -----------------------------------------------

            try:

                cursor.execute(
                    """
                    SELECT *
                    FROM `orders`
                    ORDER BY 1 DESC
                    LIMIT 8
                    """
                )

                recent = cursor.fetchall()

                result["recent_orders"] = [
                    serialize_row(row)
                    for row in recent
                ]

            except Exception as e:

                print(
                    "Recent orders error:",
                    e
                )

            cursor.close()

        # ----------------------------------------------------
        # PRODUCT CHART
        # ----------------------------------------------------

        product_chart = []

        if "product" in allowed_tables:

            product_name = find_column(
                connection,
                "product",
                [
                    "product_name",
                    "name",
                    "product",
                    "title"
                ]
            )

            if product_name:

                cursor = connection.cursor(
                    dictionary=True
                )

                try:

                    cursor.execute(
                        f"""
                        SELECT
                            `{product_name}` AS name,
                            COUNT(*) AS total
                        FROM `product`
                        GROUP BY `{product_name}`
                        ORDER BY total DESC
                        LIMIT 10
                        """
                    )

                    rows = cursor.fetchall()

                    product_chart = [
                        {
                            "label": str(row["name"]),
                            "value": int(row["total"])
                        }
                        for row in rows
                    ]

                except Exception as e:

                    print(
                        "Product chart error:",
                        e
                    )

                cursor.close()

        result["charts"][
            "product_performance"
        ] = product_chart

        # ----------------------------------------------------
        # CUSTOMER CHART
        # ----------------------------------------------------

        customer_chart = []

        if "customer" in allowed_tables:

            customer_name = find_column(
                connection,
                "customer",
                [
                    "customer_name",
                    "name",
                    "full_name",
                    "first_name"
                ]
            )

            if customer_name:

                cursor = connection.cursor(
                    dictionary=True
                )

                try:

                    cursor.execute(
                        f"""
                        SELECT
                            `{customer_name}` AS name,
                            COUNT(*) AS total
                        FROM `customer`
                        GROUP BY `{customer_name}`
                        ORDER BY total DESC
                        LIMIT 10
                        """
                    )

                    rows = cursor.fetchall()

                    customer_chart = [
                        {
                            "label": str(row["name"]),
                            "value": int(row["total"])
                        }
                        for row in rows
                    ]

                except Exception as e:

                    print(
                        "Customer chart error:",
                        e
                    )

                cursor.close()

        result["charts"][
            "customer_activity"
        ] = customer_chart

        # ----------------------------------------------------
        # PROJECT STATUS
        # ----------------------------------------------------

        project_chart = []

        if "project" in allowed_tables:

            project_status = find_column(
                connection,
                "project",
                [
                    "status",
                    "project_status"
                ]
            )

            if project_status:

                cursor = connection.cursor(
                    dictionary=True
                )

                try:

                    cursor.execute(
                        f"""
                        SELECT
                            COALESCE(
                                `{project_status}`,
                                'Unknown'
                            ) AS status,
                            COUNT(*) AS total
                        FROM `project`
                        GROUP BY `{project_status}`
                        """
                    )

                    rows = cursor.fetchall()

                    project_chart = [
                        {
                            "label": str(row["status"]),
                            "value": int(row["total"])
                        }
                        for row in rows
                    ]

                except Exception as e:

                    print(
                        "Project chart error:",
                        e
                    )

                cursor.close()

        result["charts"][
            "project_status"
        ] = project_chart

        # ====================================================
        # ADMIN ONLY ANALYTICS
        # ====================================================

        if role == "admin":

            # ------------------------------------------------
            # INVENTORY
            # ------------------------------------------------

            inventory_chart = []

            inventory_count = result[
                "counts"
            ].get(
                "inventory",
                0
            )

            low_stock = 0
            out_of_stock = 0

            if "inventory" in ADMIN_ALLOWED_TABLES:

                category_column = find_column(
                    connection,
                    "inventory",
                    [
                        "category",
                        "type",
                        "inventory_category"
                    ]
                )

                quantity_column = find_column(
                    connection,
                    "inventory",
                    [
                        "quantity",
                        "stock",
                        "stock_quantity"
                    ]
                )

                if category_column:

                    cursor = connection.cursor(
                        dictionary=True
                    )

                    try:

                        cursor.execute(
                            f"""
                            SELECT
                                COALESCE(
                                    `{category_column}`,
                                    'Unknown'
                                ) AS category,
                                COUNT(*) AS total
                            FROM `inventory`
                            GROUP BY `{category_column}`
                            ORDER BY total DESC
                            """
                        )

                        rows = cursor.fetchall()

                        inventory_chart = [
                            {
                                "label": str(
                                    row["category"]
                                ),
                                "value": int(
                                    row["total"]
                                )
                            }
                            for row in rows
                        ]

                    except Exception as e:

                        print(
                            "Inventory chart error:",
                            e
                        )

                    cursor.close()

                if quantity_column:

                    cursor = connection.cursor()

                    try:

                        cursor.execute(
                            f"""
                            SELECT
                                SUM(
                                    CASE
                                    WHEN `{quantity_column}` <= 0
                                    THEN 1
                                    ELSE 0
                                    END
                                ),
                                SUM(
                                    CASE
                                    WHEN `{quantity_column}` > 0
                                    AND `{quantity_column}` <= 5
                                    THEN 1
                                    ELSE 0
                                    END
                                )
                            FROM `inventory`
                            """
                        )

                        row = cursor.fetchone()

                        out_of_stock = int(
                            row[0] or 0
                        )

                        low_stock = int(
                            row[1] or 0
                        )

                    except Exception as e:

                        print(
                            "Inventory quantity error:",
                            e
                        )

                    cursor.close()

            result["charts"][
                "inventory_category"
            ] = inventory_chart

            # ------------------------------------------------
            # INVOICE
            # ------------------------------------------------

            invoice_chart = []

            paid_invoices = 0
            pending_invoices = 0

            invoice_status = find_column(
                connection,
                "invoice",
                [
                    "status",
                    "invoice_status",
                    "payment_status"
                ]
            )

            if invoice_status:

                cursor = connection.cursor(
                    dictionary=True
                )

                try:

                    cursor.execute(
                        f"""
                        SELECT
                            COALESCE(
                                `{invoice_status}`,
                                'Unknown'
                            ) AS status,
                            COUNT(*) AS total
                        FROM `invoice`
                        GROUP BY `{invoice_status}`
                        """
                    )

                    rows = cursor.fetchall()

                    for row in rows:

                        status = str(
                            row["status"]
                        )

                        total = int(
                            row["total"]
                        )

                        invoice_chart.append({
                            "label": status,
                            "value": total
                        })

                        lower = status.lower()

                        if "paid" in lower:
                            paid_invoices += total

                        if (
                            "pending" in lower
                            or "unpaid" in lower
                            or "overdue" in lower
                        ):
                            pending_invoices += total

                except Exception as e:

                    print(
                        "Invoice chart error:",
                        e
                    )

                cursor.close()

            result["charts"][
                "invoice_status"
            ] = invoice_chart

            # ------------------------------------------------
            # EMPLOYEE
            # ------------------------------------------------

            employee_chart = []

            employee_department = find_column(
                connection,
                "employee",
                [
                    "department",
                    "dept",
                    "employee_department"
                ]
            )

            if employee_department:

                cursor = connection.cursor(
                    dictionary=True
                )

                try:

                    cursor.execute(
                        f"""
                        SELECT
                            COALESCE(
                                `{employee_department}`,
                                'Unknown'
                            ) AS department,
                            COUNT(*) AS total
                        FROM `employee`
                        GROUP BY `{employee_department}`
                        ORDER BY total DESC
                        """
                    )

                    rows = cursor.fetchall()

                    employee_chart = [
                        {
                            "label": str(
                                row["department"]
                            ),
                            "value": int(
                                row["total"]
                            )
                        }
                        for row in rows
                    ]

                except Exception as e:

                    print(
                        "Employee chart error:",
                        e
                    )

                cursor.close()

            result["charts"][
                "employee_department"
            ] = employee_chart

            # ------------------------------------------------
            # ADMIN AI
            # ------------------------------------------------

            ai_input = {
                "orders": result[
                    "counts"
                ].get("orders", 0),

                "sales": result[
                    "statistics"
                ].get("total_sales", 0),

                "average_order": result[
                    "statistics"
                ].get("average_order", 0),

                "highest_order": result[
                    "statistics"
                ].get("highest_order", 0),

                "customers": result[
                    "counts"
                ].get("customer", 0),

                "products": result[
                    "counts"
                ].get("product", 0),

                "inventory": inventory_count,

                "employees": result[
                    "counts"
                ].get("employee", 0),

                "invoices": result[
                    "counts"
                ].get("invoice", 0),

                "projects": result[
                    "counts"
                ].get("project", 0),

                "completed_orders": completed,

                "pending_orders": pending,

                "cancelled_orders": cancelled,

                "low_stock": low_stock,

                "out_of_stock": out_of_stock,

                "paid_invoices": paid_invoices,

                "pending_invoices": pending_invoices,

                "active_projects": 0,

                "completed_projects": 0
            }

            # project statistics
            project_status_column = find_column(
                connection,
                "project",
                [
                    "status",
                    "project_status"
                ]
            )

            if project_status_column:

                cursor = connection.cursor()

                try:

                    cursor.execute(
                        f"""
                        SELECT
                            `{project_status_column}`,
                            COUNT(*)
                        FROM `project`
                        GROUP BY `{project_status_column}`
                        """
                    )

                    project_rows = cursor.fetchall()

                    for status, total in project_rows:

                        lower = str(
                            status
                        ).lower()

                        if "complete" in lower:
                            ai_input[
                                "completed_projects"
                            ] += int(total)

                        if "active" in lower or "progress" in lower:
                            ai_input[
                                "active_projects"
                            ] += int(total)

                except Exception as e:

                    print(
                        "Project AI error:",
                        e
                    )

                cursor.close()

            result["ai"] = build_admin_analysis(
                ai_input
            )

        # ====================================================
        # USER AI
        # ====================================================

        else:

            ai_input = {
                "orders": result[
                    "counts"
                ].get("orders", 0),

                "sales": result[
                    "statistics"
                ].get("total_sales", 0),

                "customers": result[
                    "counts"
                ].get("customer", 0),

                "products": result[
                    "counts"
                ].get("product", 0),

                "projects": result[
                    "counts"
                ].get("project", 0),

                "completed_orders": completed,

                "pending_orders": pending,

                "cancelled_orders": cancelled
            }

            result["ai"] = build_user_analysis(
                ai_input
            )

            # IMPORTANT:
            # Remove admin-only charts
            result["charts"].pop(
                "inventory_category",
                None
            )

            result["charts"].pop(
                "invoice_status",
                None
            )

            result["charts"].pop(
                "employee_department",
                None
            )

        return jsonify({
            "success": True,
            "data": result
        })

    except Exception as e:

        print(
            "DASHBOARD ERROR:",
            e
        )

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

    finally:
        connection.close()


# ============================================================
# AI ONLY ENDPOINT
# ============================================================

@app.route("/api/ai-analysis")
@login_required
def ai_analysis():

    response = dashboard_data()

    return response


# ============================================================
# DATABASE TEST
# ============================================================

@app.route("/api/database-test")
@login_required
def database_test():

    if test_connection():

        return jsonify({
            "success": True,
            "message": "MySQL connected successfully"
        })

    return jsonify({
        "success": False,
        "message": "MySQL connection failed"
    }), 500


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def page_not_found(error):

    return jsonify({
        "success": False,
        "error": "Page not found"
    }), 404


@app.errorhandler(500)
def server_error(error):

    return jsonify({
        "success": False,
        "error": "Internal server error"
    }), 500


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    print()
    print("==========================================")
    print(" AI BUSINESS MANAGEMENT SYSTEM")
    print("==========================================")

    test_connection()

    print()
    print("Admin Login:")
    print("Username: admin")
    print("Password: Admin@123")

    print()
    print("User Login:")
    print("Username: user")
    print("Password: User@123")

    print()
    print("Server starting...")
    print("http://127.0.0.1:5000")
    print("==========================================")
    print()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )