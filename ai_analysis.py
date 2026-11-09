"""
AI Business Management System
Business Intelligence / AI Analysis Module

This module performs intelligent rule-based business analysis
using the data received from the Flask dashboard.

It does not require an external AI API.
"""

from typing import Any, Dict, List


# =========================================================
# BASIC HELPERS
# =========================================================

def safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value, default=0):
    try:
        if value is None:
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def safe_list(value):
    return value if isinstance(value, list) else []


def safe_dict(value):
    return value if isinstance(value, dict) else {}


def text(value, default="Unknown"):
    if value is None:
        return default

    value = str(value).strip()

    return value if value else default


def first_value(row, keys, default=None):
    if not isinstance(row, dict):
        return default

    for key in keys:
        if key in row and row[key] is not None:
            return row[key]

    return default


# =========================================================
# SCORE
# =========================================================

def score_label(score):

    score = safe_float(score)

    if score >= 90:
        return "Excellent"

    if score >= 75:
        return "Very Good"

    if score >= 60:
        return "Good"

    if score >= 45:
        return "Moderate"

    if score >= 30:
        return "Needs Attention"

    return "Critical"


def score_message(score):

    score = safe_float(score)

    if score >= 90:
        return "Business performance is excellent across the available indicators."

    if score >= 75:
        return "Business performance is strong with some areas that can still be improved."

    if score >= 60:
        return "Business performance is generally healthy but should be monitored."

    if score >= 45:
        return "Business activity is moderate and several areas need improvement."

    if score >= 30:
        return "Several important business indicators require attention."

    return "The available data indicates significant areas requiring immediate attention."


# =========================================================
# AMOUNT
# =========================================================

def get_amount(row):

    return safe_float(
        first_value(
            row,
            [
                "total_amount",
                "amount",
                "total",
                "grand_total",
                "order_amount",
                "invoice_amount",
                "price"
            ],
            0
        )
    )


# =========================================================
# MONTHLY SALES
# =========================================================

def analyze_monthly_sales(data):

    result = []

    for row in safe_list(data):

        if not isinstance(row, dict):
            continue

        month = first_value(
            row,
            ["month", "Month"],
            "Unknown"
        )

        sales = safe_float(
            first_value(
                row,
                ["sales", "total_sales", "amount"],
                0
            )
        )

        result.append({
            "month": str(month),
            "sales": round(sales, 2)
        })

    if not result:

        return {
            "data": [],
            "best_month": None,
            "worst_month": None,
            "average_monthly_sales": 0,
            "growth_percent": 0,
            "trend": "No Data"
        }

    best = max(
        result,
        key=lambda x: x["sales"]
    )

    worst = min(
        result,
        key=lambda x: x["sales"]
    )

    average = sum(
        x["sales"] for x in result
    ) / len(result)

    if len(result) >= 2:

        previous = result[-2]["sales"]
        current = result[-1]["sales"]

        if previous == 0:
            growth = 100 if current > 0 else 0
        else:
            growth = (
                (current - previous)
                / previous
            ) * 100

    else:
        growth = 0

    if growth > 5:
        trend = "Growing"
    elif growth < -5:
        trend = "Declining"
    else:
        trend = "Stable"

    return {
        "data": result,

        "best_month": {
            "month": best["month"],
            "sales": best["sales"]
        },

        "worst_month": {
            "month": worst["month"],
            "sales": worst["sales"]
        },

        "average_monthly_sales": round(
            average,
            2
        ),

        "growth_percent": round(
            growth,
            2
        ),

        "trend": trend
    }


# =========================================================
# ORDER ANALYSIS
# =========================================================

def analyze_orders(
    orders,
    kpis,
    status_data
):

    orders = safe_list(orders)
    kpis = safe_dict(kpis)
    status_data = safe_dict(status_data)

    total_orders = safe_int(
        kpis.get(
            "total_orders",
            len(orders)
        )
    )

    total_sales = safe_float(
        kpis.get(
            "total_sales",
            sum(
                get_amount(x)
                for x in orders
            )
        )
    )

    average_order = safe_float(
        kpis.get(
            "average_order",
            total_sales / total_orders
            if total_orders else 0
        )
    )

    highest_order = safe_float(
        kpis.get(
            "highest_order",
            max(
                [
                    get_amount(x)
                    for x in orders
                ],
                default=0
            )
        )
    )

    completed = 0
    pending = 0
    cancelled = 0

    for status, count in status_data.items():

        s = str(status).lower()

        count = safe_int(count)

        if s in [
            "completed",
            "complete",
            "delivered",
            "success",
            "successful"
        ]:
            completed += count

        elif s in [
            "pending",
            "processing",
            "in progress",
            "in_progress"
        ]:
            pending += count

        elif s in [
            "cancelled",
            "canceled",
            "failed",
            "rejected"
        ]:
            cancelled += count

    completion_rate = (
        completed / total_orders * 100
        if total_orders
        else 0
    )

    cancellation_rate = (
        cancelled / total_orders * 100
        if total_orders
        else 0
    )

    if cancellation_rate > 20:
        health = "Critical"

    elif cancellation_rate > 10:
        health = "Needs Attention"

    elif completion_rate >= 70:
        health = "Healthy"

    else:
        health = "Moderate"

    return {
        "total_orders": total_orders,
        "total_sales": round(total_sales, 2),
        "average_order": round(average_order, 2),
        "highest_order": round(highest_order, 2),
        "completed_orders": completed,
        "pending_orders": pending,
        "cancelled_orders": cancelled,
        "completion_rate": round(
            completion_rate,
            2
        ),
        "cancellation_rate": round(
            cancellation_rate,
            2
        ),
        "statuses": status_data,
        "health": health
    }


# =========================================================
# PRODUCT ANALYSIS
# =========================================================

def analyze_products(
    products,
    performance
):

    products = safe_list(products)
    performance = safe_list(performance)

    if not performance:
        performance = products

    result = []

    for row in performance:

        if not isinstance(row, dict):
            continue

        name = first_value(
            row,
            [
                "product_name",
                "name",
                "product",
                "title"
            ],
            "Unknown Product"
        )

        sales = safe_float(
            first_value(
                row,
                [
                    "sales",
                    "total_sales",
                    "revenue",
                    "amount"
                ],
                0
            )
        )

        quantity = safe_float(
            first_value(
                row,
                [
                    "quantity",
                    "units",
                    "count",
                    "orders"
                ],
                0
            )
        )

        result.append({
            "product": str(name),
            "sales": round(sales, 2),
            "quantity": round(quantity, 2)
        })

    result.sort(
        key=lambda x: (
            x["sales"],
            x["quantity"]
        ),
        reverse=True
    )

    return {
        "total_products": len(products),
        "performance": result,
        "best_product": (
            result[0]
            if result
            else None
        ),
        "health": (
            "Strong"
            if result
            else "No Data"
        )
    }


# =========================================================
# PROJECT ANALYSIS
# =========================================================

def analyze_projects(
    projects,
    status_data
):

    projects = safe_list(projects)
    status_data = safe_dict(status_data)

    completed = 0
    active = 0
    pending = 0

    for status, count in status_data.items():

        s = str(status).lower()
        count = safe_int(count)

        if s in [
            "completed",
            "complete",
            "finished",
            "done"
        ]:
            completed += count

        elif s in [
            "active",
            "ongoing",
            "in progress",
            "in_progress"
        ]:
            active += count

        elif s in [
            "pending",
            "planned",
            "not started"
        ]:
            pending += count

    total = len(projects)

    completion_rate = (
        completed / total * 100
        if total
        else 0
    )

    if completion_rate >= 70:
        health = "Strong"

    elif completion_rate >= 40:
        health = "Moderate"

    elif total:
        health = "Needs Attention"

    else:
        health = "No Data"

    return {
        "total_projects": total,
        "completed_projects": completed,
        "active_projects": active,
        "pending_projects": pending,
        "completion_rate": round(
            completion_rate,
            2
        ),
        "statuses": status_data,
        "health": health
    }


# =========================================================
# INVENTORY ANALYSIS
# =========================================================

def analyze_inventory(
    inventory,
    category_data
):

    inventory = safe_list(inventory)

    low_stock = 0
    out_of_stock = 0
    healthy = 0
    total_quantity = 0

    for row in inventory:

        quantity = safe_float(
            first_value(
                row,
                [
                    "quantity",
                    "stock",
                    "stock_quantity",
                    "qty"
                ],
                0
            )
        )

        total_quantity += quantity

        if quantity <= 0:
            out_of_stock += 1

        elif quantity <= 10:
            low_stock += 1

        else:
            healthy += 1

    if out_of_stock:
        health = "Critical"

    elif low_stock:
        health = "Needs Attention"

    elif inventory:
        health = "Healthy"

    else:
        health = "No Data"

    return {
        "total_items": len(inventory),
        "total_quantity": round(
            total_quantity,
            2
        ),
        "low_stock_items": low_stock,
        "out_of_stock_items": out_of_stock,
        "healthy_stock_items": healthy,
        "category_data": safe_dict(
            category_data
        ),
        "health": health
    }


# =========================================================
# INVOICE ANALYSIS
# =========================================================

def analyze_invoices(
    invoices,
    status_data
):

    invoices = safe_list(invoices)
    status_data = safe_dict(status_data)

    paid = 0
    unpaid = 0
    pending = 0
    total_amount = 0

    for row in invoices:
        total_amount += get_amount(row)

    for status, count in status_data.items():

        s = str(status).lower()
        count = safe_int(count)

        if s in [
            "paid",
            "completed",
            "complete",
            "settled"
        ]:
            paid += count

        elif s in [
            "unpaid",
            "overdue",
            "failed"
        ]:
            unpaid += count

        elif s in [
            "pending",
            "processing"
        ]:
            pending += count

    total = len(invoices)

    paid_rate = (
        paid / total * 100
        if total
        else 0
    )

    return {
        "total_invoices": total,
        "total_amount": round(
            total_amount,
            2
        ),
        "paid_invoices": paid,
        "unpaid_invoices": unpaid,
        "pending_invoices": pending,
        "paid_rate": round(
            paid_rate,
            2
        ),
        "statuses": status_data,
        "health": (
            "Needs Attention"
            if unpaid
            else "Healthy"
            if total
            else "No Data"
        )
    }


# =========================================================
# EMPLOYEE ANALYSIS
# =========================================================

def analyze_employees(
    employees,
    department_data
):

    employees = safe_list(employees)

    active = 0
    inactive = 0

    for row in employees:

        status = str(
            first_value(
                row,
                [
                    "status",
                    "employee_status"
                ],
                "active"
            )
        ).lower()

        if status in [
            "inactive",
            "left",
            "terminated",
            "resigned"
        ]:
            inactive += 1
        else:
            active += 1

    total = len(employees)

    active_rate = (
        active / total * 100
        if total
        else 0
    )

    return {
        "total_employees": total,
        "active_employees": active,
        "inactive_employees": inactive,
        "active_rate": round(
            active_rate,
            2
        ),
        "department_data": safe_dict(
            department_data
        ),
        "health": (
            "Healthy"
            if active_rate >= 70
            else "Needs Attention"
        )
    }


# =========================================================
# CUSTOMER ANALYSIS
# =========================================================

def analyze_customers(
    customers,
    activity
):

    customers = safe_list(customers)
    activity = safe_list(activity)

    active = 0

    for row in activity:

        count = safe_int(
            first_value(
                row,
                [
                    "orders",
                    "order_count",
                    "total_orders",
                    "count"
                ],
                0
            )
        )

        if count > 0:
            active += 1

    engagement = (
        active / len(activity) * 100
        if activity
        else 0
    )

    return {
        "total_customers": len(customers),
        "active_customers": active,
        "engagement_rate": round(
            engagement,
            2
        ),
        "activity": activity,
        "health": (
            "Strong"
            if engagement >= 70
            else "Moderate"
            if engagement >= 40
            else "Needs Attention"
            if customers
            else "No Data"
        )
    }


# =========================================================
# BUSINESS SCORE
# =========================================================

def calculate_score(
    orders,
    monthly,
    products,
    projects,
    inventory=None,
    invoices=None,
    employees=None,
    customers=None,
    role="admin"
):

    growth = safe_float(
        monthly.get(
            "growth_percent"
        )
    )

    # SALES
    if orders["total_sales"] > 0:

        sales_score = 70

        if growth > 20:
            sales_score += 30
        elif growth > 10:
            sales_score += 20
        elif growth > 0:
            sales_score += 10
        elif growth < -20:
            sales_score -= 25
        elif growth < -10:
            sales_score -= 15
        elif growth < 0:
            sales_score -= 8

    else:
        sales_score = 0

    # ORDERS
    if orders["total_orders"]:

        order_score = (
            orders["completion_rate"]
            -
            orders["cancellation_rate"]
            * 0.5
        )

        order_score = max(
            0,
            min(100, order_score)
        )

    else:
        order_score = 0

    # PRODUCTS
    if products["total_products"]:

        product_score = 70

        if products["performance"]:
            product_score += 20

        if products["best_product"]:
            product_score += 10

        product_score = min(
            100,
            product_score
        )

    else:
        product_score = 0

    # PROJECTS
    project_score = projects[
        "completion_rate"
    ]

    components = {
        "sales": round(sales_score),
        "orders": round(order_score),
        "products": round(product_score),
        "projects": round(project_score)
    }

    if role == "user":

        weights = {
            "sales": 0.30,
            "orders": 0.35,
            "products": 0.15,
            "projects": 0.20
        }

    else:

        weights = {
            "sales": 0.20,
            "orders": 0.20,
            "products": 0.10,
            "projects": 0.10,
            "inventory": 0.15,
            "invoices": 0.10,
            "employees": 0.075,
            "customers": 0.075
        }

        if inventory is not None:

            total = inventory[
                "total_items"
            ]

            if total:

                inventory_score = 100

                inventory_score -= (
                    inventory[
                        "out_of_stock_items"
                    ]
                    / total
                    * 60
                )

                inventory_score -= (
                    inventory[
                        "low_stock_items"
                    ]
                    / total
                    * 30
                )

                components[
                    "inventory"
                ] = round(
                    max(
                        0,
                        min(
                            100,
                            inventory_score
                        )
                    )
                )

        if invoices is not None:

            components[
                "invoices"
            ] = round(
                invoices["paid_rate"]
            )

        if employees is not None:

            components[
                "employees"
            ] = round(
                employees["active_rate"]
            )

        if customers is not None:

            components[
                "customers"
            ] = round(
                customers["engagement_rate"]
            )

    active_weights = {
        key: value
        for key, value in weights.items()
        if key in components
    }

    weight_sum = sum(
        active_weights.values()
    )

    if weight_sum:

        score = sum(
            components[key]
            *
            (
                active_weights[key]
                / weight_sum
            )
            for key in active_weights
        )

    else:

        score = 0

    return {
        "score": round(
            max(
                0,
                min(100, score)
            )
        ),
        "components": components
    }


# =========================================================
# STRENGTHS
# =========================================================

def generate_strengths(
    orders,
    monthly,
    products,
    projects,
    inventory,
    invoices,
    employees,
    customers,
    role
):

    strengths = []

    if monthly["growth_percent"] > 10:

        strengths.append(
            f"Monthly sales are growing by "
            f"{monthly['growth_percent']:.1f}%."
        )

    if orders["completion_rate"] >= 70:

        strengths.append(
            f"Order completion rate is strong at "
            f"{orders['completion_rate']:.1f}%."
        )

    if products["best_product"]:

        strengths.append(
            f"{products['best_product']['product']} "
            "is the strongest available product."
        )

    if projects["completion_rate"] >= 70:

        strengths.append(
            f"Project completion rate is "
            f"{projects['completion_rate']:.1f}%."
        )

    if role == "admin":

        if inventory and inventory[
            "out_of_stock_items"
        ] == 0:

            strengths.append(
                "No out-of-stock inventory items were detected."
            )

        if invoices and invoices[
            "paid_rate"
        ] >= 70:

            strengths.append(
                f"Invoice payment performance is strong "
                f"at {invoices['paid_rate']:.1f}%."
            )

        if employees and employees[
            "active_rate"
        ] >= 80:

            strengths.append(
                f"Employee activity is healthy at "
                f"{employees['active_rate']:.1f}%."
            )

        if customers and customers[
            "engagement_rate"
        ] >= 70:

            strengths.append(
                f"Customer engagement is strong at "
                f"{customers['engagement_rate']:.1f}%."
            )

    if not strengths:

        strengths.append(
            "Business data is available for continued monitoring."
        )

    return strengths


# =========================================================
# RISKS
# =========================================================

def generate_risks(
    orders,
    monthly,
    products,
    projects,
    inventory,
    invoices,
    employees,
    customers,
    role
):

    risks = []

    if monthly["growth_percent"] < -10:

        risks.append(
            f"Monthly sales have declined by "
            f"{abs(monthly['growth_percent']):.1f}%."
        )

    if orders["cancellation_rate"] > 10:

        risks.append(
            f"Order cancellation rate is "
            f"{orders['cancellation_rate']:.1f}%."
        )

    if (
        orders["total_orders"] > 0
        and
        orders["completion_rate"] < 50
    ):

        risks.append(
            "Order completion rate is below 50%."
        )

    if (
        projects["total_projects"] > 0
        and
        projects["completion_rate"] < 40
    ):

        risks.append(
            "Project completion rate is low."
        )

    if role == "admin":

        if inventory:

            if inventory[
                "out_of_stock_items"
            ] > 0:

                risks.append(
                    f"{inventory['out_of_stock_items']} "
                    "inventory item(s) are out of stock."
                )

            if inventory[
                "low_stock_items"
            ] > 0:

                risks.append(
                    f"{inventory['low_stock_items']} "
                    "inventory item(s) have low stock."
                )

        if invoices and invoices[
            "unpaid_invoices"
        ] > 0:

            risks.append(
                f"{invoices['unpaid_invoices']} "
                "invoice(s) are unpaid or overdue."
            )

        if (
            employees
            and
            employees["active_rate"] < 60
        ):

            risks.append(
                "Employee activity is relatively low."
            )

        if (
            customers
            and
            customers["engagement_rate"] < 40
        ):

            risks.append(
                "Customer engagement appears low."
            )

    if not risks:

        risks.append(
            "No major risk indicators were detected."
        )

    return risks


# =========================================================
# RECOMMENDATIONS
# =========================================================

def generate_recommendations(
    orders,
    monthly,
    products,
    projects,
    inventory,
    invoices,
    employees,
    customers,
    role
):

    recommendations = []

    if monthly["growth_percent"] < 0:

        recommendations.append(
            "Investigate the reason for declining sales "
            "and focus on high-performing products."
        )

    else:

        recommendations.append(
            "Continue monitoring monthly sales and "
            "increase the average order value."
        )

    if orders["cancellation_rate"] > 10:

        recommendations.append(
            "Investigate order cancellation reasons "
            "and improve order processing."
        )

    if orders["completion_rate"] < 60:

        recommendations.append(
            "Improve order fulfillment and reduce pending orders."
        )

    if products["best_product"]:

        recommendations.append(
            f"Focus marketing and inventory planning on "
            f"{products['best_product']['product']}."
        )

    if projects["completion_rate"] < 60:

        recommendations.append(
            "Review project timelines and prioritize delayed projects."
        )

    if role == "admin":

        if inventory and (
            inventory["low_stock_items"] > 0
            or
            inventory["out_of_stock_items"] > 0
        ):

            recommendations.append(
                "Create a reorder plan for low-stock and "
                "out-of-stock inventory."
            )

        if invoices and invoices[
            "unpaid_invoices"
        ] > 0:

            recommendations.append(
                "Follow up on unpaid invoices to improve cash flow."
            )

        if customers and customers[
            "engagement_rate"
        ] < 60:

            recommendations.append(
                "Improve customer engagement through follow-ups "
                "and targeted offers."
            )

        if employees and employees[
            "active_rate"
        ] < 70:

            recommendations.append(
                "Review employee workload and activity."
            )

    return recommendations


# =========================================================
# MAIN FUNCTION
# =========================================================

def generate_ai_analysis(
    dashboard_data=None,
    role="admin"
):

    dashboard_data = safe_dict(
        dashboard_data
    )

    role = str(
        role or "user"
    ).lower()

    kpis = safe_dict(
        dashboard_data.get("kpis")
    )

    monthly = analyze_monthly_sales(
        dashboard_data.get(
            "monthly_sales",
            []
        )
    )

    orders = analyze_orders(
        dashboard_data.get(
            "orders_data",
            []
        ),
        kpis,
        dashboard_data.get(
            "order_status",
            {}
        )
    )

    products = analyze_products(
        dashboard_data.get(
            "products_data",
            []
        ),
        dashboard_data.get(
            "product_performance",
            []
        )
    )

    projects = analyze_projects(
        dashboard_data.get(
            "projects_data",
            []
        ),
        dashboard_data.get(
            "project_status",
            {}
        )
    )

    inventory = None
    invoices = None
    employees = None
    customers = None

    if role == "admin":

        inventory = analyze_inventory(
            dashboard_data.get(
                "inventory_data",
                []
            ),
            dashboard_data.get(
                "inventory_category",
                {}
            )
        )

        invoices = analyze_invoices(
            dashboard_data.get(
                "invoice_data",
                []
            ),
            dashboard_data.get(
                "invoice_status",
                {}
            )
        )

        employees = analyze_employees(
            dashboard_data.get(
                "employee_data",
                []
            ),
            dashboard_data.get(
                "employee_department",
                {}
            )
        )

        customers = analyze_customers(
            dashboard_data.get(
                "customer_data",
                []
            ),
            dashboard_data.get(
                "customer_activity",
                []
            )
        )

    score = calculate_score(
        orders,
        monthly,
        products,
        projects,
        inventory,
        invoices,
        employees,
        customers,
        role
    )

    strengths = generate_strengths(
        orders,
        monthly,
        products,
        projects,
        inventory,
        invoices,
        employees,
        customers,
        role
    )

    risks = generate_risks(
        orders,
        monthly,
        products,
        projects,
        inventory,
        invoices,
        employees,
        customers,
        role
    )

    recommendations = generate_recommendations(
        orders,
        monthly,
        products,
        projects,
        inventory,
        invoices,
        employees,
        customers,
        role
    )

    total_sales = orders["total_sales"]
    total_orders = orders["total_orders"]

    summary = (
        f"The current business health score is "
        f"{score['score']}/100 ({score_label(score['score'])}). "
        f"The system contains {total_orders} order(s) "
        f"with total sales of ₹{total_sales:,.2f}. "
        f"Monthly sales are currently {monthly['trend'].lower()}."
    )

    if role == "admin":

        summary += (
            f" Inventory contains "
            f"{inventory['low_stock_items']} low-stock item(s), "
            f"while invoice analysis identifies "
            f"{invoices['unpaid_invoices']} unpaid invoice(s)."
        )

    return {
        "success": True,

        "role": role,

        "score": score["score"],

        "score_label": score_label(
            score["score"]
        ),

        "score_message": score_message(
            score["score"]
        ),

        "summary": summary,

        "detailed_explanation": summary,

        "components": score["components"],

        "sales_analysis": monthly,

        "order_analysis": orders,

        "product_analysis": products,

        "project_analysis": projects,

        "strengths": strengths,

        "risks": risks,

        "recommendations": recommendations,

        "admin_analysis": (
            {
                "inventory": inventory,
                "invoices": invoices,
                "employees": employees,
                "customers": customers
            }
            if role == "admin"
            else {}
        ),

        "charts": {
            "ai_score": {
                "labels": list(
                    score["components"].keys()
                ),
                "values": list(
                    score["components"].values()
                )
            }
        }
    }


def build_ai_analysis(
    dashboard_data=None,
    role="admin"
):

    return generate_ai_analysis(
        dashboard_data,
        role
    )


def analyze_business(
    dashboard_data=None,
    role="admin"
):

    return generate_ai_analysis(
        dashboard_data,
        role
    )