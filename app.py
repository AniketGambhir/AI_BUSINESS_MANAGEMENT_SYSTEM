import os
from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    redirect,
    url_for,
    session
)

from database import get_connection
from ai_analysis import analyze_sales


app = Flask(__name__)

# Secret key comes from the environment (set SECRET_KEY on Render)
app.secret_key = os.environ.get("SECRET_KEY", "change-me-locally")


# =========================================================
# LOGIN USERS (passwords come from environment variables)
# =========================================================

USERS = {
    "admin": {
        "password": os.environ.get("ADMIN_PASSWORD", "admin123"),
        "role": "admin"
    },
    "user": {
        "password": os.environ.get("USER_PASSWORD", "user123"),
        "role": "user"
    }
}


# =========================================================
# TABLES
# =========================================================

ALL_TABLES = [
    "customer",
    "employee",
    "product",
    "inventory",
    "orders",
    "invoice",
    "project"
]

USER_VIEW_TABLES = [
    "customer",
    "product",
    "orders",
    "project"
]


# =========================================================
# DECORATORS
# =========================================================

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
            return jsonify({"error": "Admin access required."}), 403

        return function(*args, **kwargs)

    return wrapper


# =========================================================
# HELPERS
# =========================================================

def get_table_columns(table):

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(f"SHOW COLUMNS FROM `{table}`")
        return [row[0] for row in cursor.fetchall()]

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def get_primary_key(table):

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            f"SHOW KEYS FROM `{table}` WHERE Key_name = 'PRIMARY'"
        )
        row = cursor.fetchone()
        return row["Column_name"] if row else None

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# =========================================================
# PAGES
# =========================================================

@app.route("/")
def home():

    if "username" not in session:
        return redirect(url_for("login"))

    if session.get("role") == "admin":
        return redirect(url_for("admin_page"))

    return redirect(url_for("user_page"))


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = USERS.get(username)

        if user and user["password"] == password:

            session["username"] = username
            session["role"] = user["role"]

            if user["role"] == "admin":
                return redirect(url_for("admin_page"))

            return redirect(url_for("user_page"))

        return render_template(
            "login.html",
            error="Invalid username or password."
        )

    return render_template("login.html")


@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


@app.route("/admin")
@admin_required
def admin_page():

    return render_template(
        "admin.html",
        username=session.get("username"),
        tables=ALL_TABLES
    )


@app.route("/user")
@login_required
def user_page():

    if session.get("role") != "user":
        return redirect(url_for("admin_page"))

    return render_template(
        "user.html",
        username=session.get("username"),
        tables=USER_VIEW_TABLES
    )


# =========================================================
# GET TABLE DATA
# =========================================================

@app.route("/api/table/<table_name>", methods=["GET"])
@login_required
def get_table_data(table_name):

    if table_name not in ALL_TABLES:
        return jsonify({"error": "Invalid table."}), 404

    if (
        session.get("role") == "user"
        and table_name not in USER_VIEW_TABLES
    ):
        return jsonify({
            "error": "You do not have permission to view this table."
        }), 403

    search = request.args.get("search", "").strip()

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        columns = get_table_columns(table_name)

        query = f"SELECT * FROM `{table_name}`"
        values = []

        if search:

            conditions = []

            for column in columns:
                conditions.append(f"CAST(`{column}` AS CHAR) LIKE %s")
                values.append(f"%{search}%")

            query += " WHERE " + " OR ".join(conditions)

        query += " LIMIT 500"

        cursor.execute(query, values)
        rows = cursor.fetchall()

        return jsonify({
            "table": table_name,
            "columns": columns,
            "rows": rows
        })

    except Exception as error:
        return jsonify({"error": str(error)}), 400

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# =========================================================
# TABLE COLUMNS (ADMIN)
# =========================================================

@app.route("/api/table/<table_name>/columns", methods=["GET"])
@admin_required
def table_columns(table_name):

    if table_name not in ALL_TABLES:
        return jsonify({"error": "Invalid table."}), 404

    try:
        return jsonify({
            "columns": get_table_columns(table_name),
            "primary_key": get_primary_key(table_name)
        })

    except Exception as error:
        return jsonify({"error": str(error)}), 400


# =========================================================
# INSERT
# =========================================================

@app.route("/api/table/<table_name>", methods=["POST"])
@admin_required
def insert_record(table_name):

    if table_name not in ALL_TABLES:
        return jsonify({"error": "Invalid table."}), 404

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON data."}), 400

    connection = None
    cursor = None

    try:
        columns = get_table_columns(table_name)
        primary_key = get_primary_key(table_name)

        filtered = {}

        for column in columns:

            if column not in data:
                continue

            value = data[column]

            if value == "":
                value = None

            filtered[column] = value

        # Do not manually insert an empty auto-increment ID
        if primary_key in filtered and filtered[primary_key] in (None, ""):
            del filtered[primary_key]

        if not filtered:
            return jsonify({"error": "No data provided."}), 400

        column_names = list(filtered.keys())
        placeholders = ", ".join(["%s"] * len(column_names))
        sql_columns = ", ".join(f"`{c}`" for c in column_names)

        query = (
            f"INSERT INTO `{table_name}` ({sql_columns}) "
            f"VALUES ({placeholders})"
        )

        values = [filtered[c] for c in column_names]

        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(query, values)
        connection.commit()

        return jsonify({
            "success": True,
            "message": "Record inserted successfully.",
            "id": cursor.lastrowid
        })

    except Exception as error:

        if connection:
            connection.rollback()

        return jsonify({"error": str(error)}), 400

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# =========================================================
# UPDATE
# =========================================================

@app.route("/api/table/<table_name>/<record_id>", methods=["PUT"])
@admin_required
def update_record(table_name, record_id):

    if table_name not in ALL_TABLES:
        return jsonify({"error": "Invalid table."}), 404

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON data."}), 400

    connection = None
    cursor = None

    try:
        columns = get_table_columns(table_name)
        primary_key = get_primary_key(table_name)

        if not primary_key:
            return jsonify({"error": "Primary key not found."}), 400

        updates = {}

        for column in columns:

            if column == primary_key or column not in data:
                continue

            value = data[column]

            if value == "":
                value = None

            updates[column] = value

        if not updates:
            return jsonify({"error": "No fields to update."}), 400

        set_clause = ", ".join(f"`{c}` = %s" for c in updates)

        query = (
            f"UPDATE `{table_name}` SET {set_clause} "
            f"WHERE `{primary_key}` = %s"
        )

        values = [updates[c] for c in updates]
        values.append(record_id)

        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(query, values)
        connection.commit()

        return jsonify({
            "success": True,
            "message": "Record updated successfully."
        })

    except Exception as error:

        if connection:
            connection.rollback()

        return jsonify({"error": str(error)}), 400

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# =========================================================
# DELETE
# =========================================================

@app.route("/api/table/<table_name>/<record_id>", methods=["DELETE"])
@admin_required
def delete_record(table_name, record_id):

    if table_name not in ALL_TABLES:
        return jsonify({"error": "Invalid table."}), 404

    connection = None
    cursor = None

    try:
        primary_key = get_primary_key(table_name)

        if not primary_key:
            return jsonify({"error": "Primary key not found."}), 400

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            f"DELETE FROM `{table_name}` WHERE `{primary_key}` = %s",
            (record_id,)
        )

        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Record not found."}), 404

        return jsonify({
            "success": True,
            "message": "Record deleted successfully."
        })

    except Exception as error:

        if connection:
            connection.rollback()

        return jsonify({"error": str(error)}), 400

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# =========================================================
# DASHBOARD + AI DATA
# =========================================================

@app.route("/api/dashboard")
@login_required
def dashboard_data():

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT status, COUNT(*) AS count
            FROM orders
            GROUP BY status
            ORDER BY count DESC
        """)
        order_status = cursor.fetchall()

        cursor.execute("""
            SELECT category, SUM(quantity) AS quantity
            FROM inventory
            GROUP BY category
            ORDER BY quantity DESC
        """)
        inventory_category = cursor.fetchall()

        cursor.execute("""
            SELECT
                COUNT(*) AS total_orders,
                COALESCE(SUM(total_amount), 0) AS total_sales,
                COALESCE(AVG(total_amount), 0) AS average_order,
                COALESCE(MAX(total_amount), 0) AS highest_order,
                COALESCE(MIN(total_amount), 0) AS lowest_order
            FROM orders
        """)
        summary = cursor.fetchone()

        cursor.execute("""
            SELECT order_id, order_date, total_amount, status
            FROM orders
            ORDER BY order_id
        """)
        orders = cursor.fetchall()

        ai_result = analyze_sales(orders)

        return jsonify({
            "order_status": order_status,
            "inventory_category": inventory_category,
            "summary": summary,
            "ai": ai_result
        })

    except Exception as error:
        return jsonify({"error": str(error)}), 400

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# =========================================================
# RUN (local only; Render uses gunicorn app:app)
# =========================================================

if __name__ == "__main__":
    app.run()
