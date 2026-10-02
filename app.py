from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify
)

from database import get_connection
from ai_analysis import analyze_sales


app = Flask(__name__)

app.secret_key = "ai_business_management_secret_key"


# =========================================================
# USERS
# =========================================================

USERS = {

    "admin": {
        "password": "admin123",
        "role": "admin"
    },

    "user": {
        "password": "user123",
        "role": "user"
    }

}


# =========================================================
# TABLE PERMISSIONS
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
# HELPER
# =========================================================

def allowed_table(table):

    return table in ALL_TABLES


def get_primary_key(cursor, table):

    cursor.execute(
        f"SHOW KEYS FROM `{table}` "
        f"WHERE Key_name = 'PRIMARY'"
    )

    result = cursor.fetchone()

    if result:

        return result["Column_name"]

    return None


def get_columns(cursor, table):

    cursor.execute(
        f"SHOW COLUMNS FROM `{table}`"
    )

    return cursor.fetchall()


def get_table_data(
    cursor,
    table,
    search=""
):

    columns = get_columns(
        cursor,
        table
    )

    column_names = [
        column["Field"]
        for column in columns
    ]


    query = (
        f"SELECT * FROM `{table}`"
    )

    params = []


    if search:

        conditions = []

        for column in column_names:

            conditions.append(
                f"CAST(`{column}` AS CHAR) LIKE %s"
            )

            params.append(
                f"%{search}%"
            )


        query += (
            " WHERE "
            +
            " OR ".join(
                conditions
            )
        )


    primary_key = get_primary_key(
        cursor,
        table
    )


    if primary_key:

        query += (
            f" ORDER BY `{primary_key}`"
        )


    cursor.execute(
        query,
        params
    )

    rows = cursor.fetchall()


    return {

        "columns":
            column_names,

        "rows":
            rows,

        "primary_key":
            primary_key

    }


# =========================================================
# LOGIN REQUIRED
# =========================================================

def login_required(function):

    def wrapper(*args, **kwargs):

        if "username" not in session:

            return redirect(
                url_for("login")
            )

        return function(
            *args,
            **kwargs
        )

    wrapper.__name__ = function.__name__

    return wrapper


# =========================================================
# ADMIN REQUIRED
# =========================================================

def admin_required(function):

    def wrapper(*args, **kwargs):

        if "username" not in session:

            return redirect(
                url_for("login")
            )

        if session.get("role") != "admin":

            return "Access denied", 403

        return function(
            *args,
            **kwargs
        )

    wrapper.__name__ = function.__name__

    return wrapper


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    if "username" not in session:

        return redirect(
            url_for("login")
        )


    if session.get("role") == "admin":

        return redirect(
            url_for("admin_dashboard")
        )


    return redirect(
        url_for("user_dashboard")
    )


# =========================================================
# LOGIN PAGE
# =========================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    error = None


    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )


        if (
            username in USERS
            and
            USERS[username]["password"]
            == password
        ):

            session["username"] = username

            session["role"] = (
                USERS[username]["role"]
            )


            if session["role"] == "admin":

                return redirect(
                    url_for(
                        "admin_dashboard"
                    )
                )


            return redirect(
                url_for(
                    "user_dashboard"
                )
            )


        error = (
            "Invalid username or password."
        )


    return render_template(
        "login.html",
        error=error
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route("/admin")
@admin_required
def admin_dashboard():

    return render_template(

        "admin.html",

        username=session.get(
            "username"
        ),

        tables=ALL_TABLES

    )


# =========================================================
# USER DASHBOARD
# =========================================================

@app.route("/user")
@login_required
def user_dashboard():

    if session.get("role") != "user":

        return "Access denied", 403


    return render_template(

        "user.html",

        username=session.get(
            "username"
        ),

        tables=USER_VIEW_TABLES

    )


# =========================================================
# GET TABLE DATA
# =========================================================

@app.route(
    "/api/table/<table>",
    methods=["GET"]
)
@login_required
def api_get_table(table):

    if not allowed_table(table):

        return jsonify({
            "error": "Invalid table."
        }), 404


    # User permissions
    if (
        session.get("role") == "user"
        and
        table not in USER_VIEW_TABLES
    ):

        return jsonify({
            "error": "You do not have permission to access this table."
        }), 403


    search = request.args.get(
        "search",
        ""
    ).strip()


    connection = None
    cursor = None


    try:

        connection = get_connection()

        cursor = connection.cursor(
            dictionary=True
        )


        data = get_table_data(
            cursor,
            table,
            search
        )


        return jsonify(data)


    except Exception as error:

        return jsonify({
            "error": str(error)
        }), 400


    finally:

        if cursor:

            cursor.close()


        if connection:

            connection.close()


# =========================================================
# GET TABLE COLUMNS
# =========================================================

@app.route(
    "/api/table/<table>/columns",
    methods=["GET"]
)
@login_required
def api_columns(table):

    if not allowed_table(table):

        return jsonify({
            "error": "Invalid table."
        }), 404


    if (
        session.get("role") == "user"
        and
        table not in USER_VIEW_TABLES
    ):

        return jsonify({
            "error": "Access denied."
        }), 403


    connection = None
    cursor = None


    try:

        connection = get_connection()

        cursor = connection.cursor(
            dictionary=True
        )


        columns = get_columns(
            cursor,
            table
        )


        return jsonify({

            "columns":
                columns,

            "primary_key":
                get_primary_key(
                    cursor,
                    table
                )

        })


    except Exception as error:

        return jsonify({
            "error": str(error)
        }), 400


    finally:

        if cursor:

            cursor.close()


        if connection:

            connection.close()


# =========================================================
# INSERT
# =========================================================

@app.route(
    "/api/table/<table>",
    methods=["POST"]
)
@admin_required
def api_insert(table):

    if not allowed_table(table):

        return jsonify({
            "error": "Invalid table."
        }), 404


    data = request.get_json(
        silent=True
    ) or {}


    if not data:

        return jsonify({
            "error": "No data received."
        }), 400


    connection = None
    cursor = None


    try:

        connection = get_connection()

        cursor = connection.cursor()


        columns = get_columns(
            cursor,
            table
        )


        allowed_columns = {
            column["Field"]
            for column in columns
        }


        clean_data = {

            key: value

            for key, value in data.items()

            if key in allowed_columns
            and value != ""

        }


        if not clean_data:

            return jsonify({
                "error": "No valid fields received."
            }), 400


        names = list(
            clean_data.keys()
        )


        placeholders = ", ".join(
            ["%s"] * len(names)
        )


        query = (

            f"INSERT INTO `{table}` "
            f"(`"
            + "`, `".join(names)
            + "`) VALUES ("
            + placeholders
            + ")"

        )


        values = [
            clean_data[name]
            for name in names
        ]


        cursor.execute(
            query,
            values
        )


        connection.commit()


        return jsonify({

            "success": True,

            "message":
                "Record inserted successfully."

        })


    except Exception as error:

        if connection:

            connection.rollback()


        return jsonify({
            "error": str(error)
        }), 400


    finally:

        if cursor:

            cursor.close()


        if connection:

            connection.close()


# =========================================================
# UPDATE
# =========================================================

@app.route(
    "/api/table/<table>/<path:primary_value>",
    methods=["PUT"]
)
@admin_required
def api_update(
    table,
    primary_value
):

    if not allowed_table(table):

        return jsonify({
            "error": "Invalid table."
        }), 404


    data = request.get_json(
        silent=True
    ) or {}


    connection = None
    cursor = None


    try:

        connection = get_connection()

        cursor = connection.cursor(
            dictionary=True
        )


        primary_key = get_primary_key(
            cursor,
            table
        )


        if not primary_key:

            return jsonify({
                "error":
                    "No primary key found."
            }), 400


        columns = get_columns(
            cursor,
            table
        )


        allowed_columns = {
            column["Field"]
            for column in columns
        }


        clean_data = {

            key: value

            for key, value in data.items()

            if key in allowed_columns
            and key != primary_key

        }


        if not clean_data:

            return jsonify({
                "error":
                    "No fields to update."
            }), 400


        set_parts = []

        values = []


        for column, value in clean_data.items():

            set_parts.append(
                f"`{column}` = %s"
            )

            values.append(value)


        values.append(
            primary_value
        )


        query = (

            f"UPDATE `{table}` "
            f"SET "
            +
            ", ".join(set_parts)
            +
            f" WHERE `{primary_key}` = %s"

        )


        cursor.execute(
            query,
            values
        )


        connection.commit()


        return jsonify({

            "success": True,

            "message":
                "Record updated successfully."

        })


    except Exception as error:

        if connection:

            connection.rollback()


        return jsonify({
            "error": str(error)
        }), 400


    finally:

        if cursor:

            cursor.close()


        if connection:

            connection.close()


# =========================================================
# DELETE
# =========================================================

@app.route(
    "/api/table/<table>/<path:primary_value>",
    methods=["DELETE"]
)
@admin_required
def api_delete(
    table,
    primary_value
):

    if not allowed_table(table):

        return jsonify({
            "error": "Invalid table."
        }), 404


    connection = None
    cursor = None


    try:

        connection = get_connection()

        cursor = connection.cursor(
            dictionary=True
        )


        primary_key = get_primary_key(
            cursor,
            table
        )


        if not primary_key:

            return jsonify({
                "error":
                    "No primary key found."
            }), 400


        query = (

            f"DELETE FROM `{table}` "
            f"WHERE `{primary_key}` = %s"

        )


        cursor.execute(
            query,
            [primary_value]
        )


        connection.commit()


        return jsonify({

            "success": True,

            "message":
                "Record deleted successfully."

        })


    except Exception as error:

        if connection:

            connection.rollback()


        return jsonify({
            "error": str(error)
        }), 400


    finally:

        if cursor:

            cursor.close()


        if connection:

            connection.close()


# =========================================================
# DASHBOARD / AI
# =========================================================

@app.route("/api/dashboard")
@login_required
def dashboard_data():

    connection = None
    cursor = None


    try:

        connection = get_connection()

        cursor = connection.cursor(
            dictionary=True
        )


        # =================================================
        # ORDER STATUS
        # =================================================

        cursor.execute("""

            SELECT

                status,

                COUNT(*) AS count

            FROM orders

            GROUP BY status

            ORDER BY count DESC

        """)


        order_status = (
            cursor.fetchall()
        )


        # =================================================
        # INVENTORY CATEGORY
        # =================================================

        cursor.execute("""

            SELECT

                category,

                SUM(quantity) AS quantity

            FROM inventory

            GROUP BY category

            ORDER BY quantity DESC

        """)


        inventory_category = (
            cursor.fetchall()
        )


        # Convert inventory numbers

        for row in inventory_category:

            row["quantity"] = int(
                row["quantity"] or 0
            )


        # =================================================
        # SALES TREND
        # =================================================

        cursor.execute("""

            SELECT

                DATE(order_date) AS order_date,

                SUM(total_amount) AS sales,

                COUNT(*) AS orders

            FROM orders

            GROUP BY DATE(order_date)

            ORDER BY DATE(order_date)

        """)


        sales_trend = (
            cursor.fetchall()
        )


        for row in sales_trend:

            if row["order_date"]:

                row["order_date"] = str(
                    row["order_date"]
                )


            row["sales"] = float(
                row["sales"] or 0
            )


            row["orders"] = int(
                row["orders"] or 0
            )


        # =================================================
        # SALES BY STATUS
        # =================================================

        cursor.execute("""

            SELECT

                status,

                COUNT(*) AS order_count,

                SUM(total_amount) AS sales

            FROM orders

            GROUP BY status

            ORDER BY sales DESC

        """)


        sales_by_status = (
            cursor.fetchall()
        )


        for row in sales_by_status:

            row["order_count"] = int(
                row["order_count"] or 0
            )


            row["sales"] = float(
                row["sales"] or 0
            )


        # =================================================
        # SUMMARY
        # =================================================

        cursor.execute("""

            SELECT

                COUNT(*) AS total_orders,

                COALESCE(
                    SUM(total_amount),
                    0
                ) AS total_sales,

                COALESCE(
                    AVG(total_amount),
                    0
                ) AS average_order,

                COALESCE(
                    MAX(total_amount),
                    0
                ) AS highest_order,

                COALESCE(
                    MIN(total_amount),
                    0
                ) AS lowest_order

            FROM orders

        """)


        summary = cursor.fetchone()


        summary["total_orders"] = int(
            summary["total_orders"] or 0
        )


        summary["total_sales"] = float(
            summary["total_sales"] or 0
        )


        summary["average_order"] = float(
            summary["average_order"] or 0
        )


        summary["highest_order"] = float(
            summary["highest_order"] or 0
        )


        summary["lowest_order"] = float(
            summary["lowest_order"] or 0
        )


        # =================================================
        # ORDERS FOR AI
        # =================================================

        cursor.execute("""

            SELECT

                order_id,

                order_date,

                total_amount,

                status

            FROM orders

            ORDER BY order_id

        """)


        orders = cursor.fetchall()


        # =================================================
        # AI
        # =================================================

        ai_result = analyze_sales(
            orders
        )


        # =================================================
        # RETURN
        # =================================================

        return jsonify({

            "order_status":
                order_status,

            "inventory_category":
                inventory_category,

            "sales_trend":
                sales_trend,

            "sales_by_status":
                sales_by_status,

            "summary":
                summary,

            "ai":
                ai_result

        })


    except Exception as error:

        return jsonify({

            "error":
                str(error)

        }), 400


    finally:

        if cursor:

            cursor.close()


        if connection:

            connection.close()


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )
