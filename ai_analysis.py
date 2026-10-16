from datetime import datetime


def safe_number(value, default=0):
    try:
        if value is None:
            return default
        return float(value)
    except:
        return default


def percentage(part, total):
    if total == 0:
        return 0
    return round((part / total) * 100, 2)


def clamp(value, minimum=0, maximum=100):
    return max(minimum, min(maximum, round(value)))


def score_from_ratio(ratio):
    return clamp(ratio * 100)


def build_admin_analysis(data):
    """
    Creates a detailed business analysis for ADMIN.
    """

    orders = safe_number(data.get("orders"))
    sales = safe_number(data.get("sales"))
    average_order = safe_number(data.get("average_order"))
    highest_order = safe_number(data.get("highest_order"))

    customers = safe_number(data.get("customers"))
    products = safe_number(data.get("products"))
    inventory = safe_number(data.get("inventory"))
    employees = safe_number(data.get("employees"))
    invoices = safe_number(data.get("invoices"))
    projects = safe_number(data.get("projects"))

    completed = safe_number(data.get("completed_orders"))
    pending = safe_number(data.get("pending_orders"))
    cancelled = safe_number(data.get("cancelled_orders"))

    low_stock = safe_number(data.get("low_stock"))
    out_of_stock = safe_number(data.get("out_of_stock"))

    paid_invoices = safe_number(data.get("paid_invoices"))
    pending_invoices = safe_number(data.get("pending_invoices"))

    active_projects = safe_number(data.get("active_projects"))
    completed_projects = safe_number(data.get("completed_projects"))

    # -------------------------
    # SALES SCORE
    # -------------------------

    if sales <= 0:
        sales_score = 25
    elif sales >= 100000:
        sales_score = 100
    elif sales >= 50000:
        sales_score = 90
    elif sales >= 25000:
        sales_score = 80
    elif sales >= 10000:
        sales_score = 70
    else:
        sales_score = 55

    sales_score = clamp(sales_score)

    # -------------------------
    # ORDER SCORE
    # -------------------------

    total_status_orders = completed + pending + cancelled

    if total_status_orders > 0:
        completion_rate = percentage(completed, total_status_orders)
        cancellation_rate = percentage(cancelled, total_status_orders)

        order_score = (
            completion_rate
            - (cancellation_rate * 0.7)
            + 30
        )
    else:
        completion_rate = 0
        cancellation_rate = 0
        order_score = 50

    order_score = clamp(order_score)

    # -------------------------
    # CUSTOMER SCORE
    # -------------------------

    if customers == 0:
        customer_score = 25
    elif orders == 0:
        customer_score = 50
    else:
        orders_per_customer = orders / customers

        if orders_per_customer >= 5:
            customer_score = 95
        elif orders_per_customer >= 3:
            customer_score = 85
        elif orders_per_customer >= 2:
            customer_score = 75
        elif orders_per_customer >= 1:
            customer_score = 65
        else:
            customer_score = 50

    customer_score = clamp(customer_score)

    # -------------------------
    # PRODUCT SCORE
    # -------------------------

    if products == 0:
        product_score = 30
    elif orders >= products * 3:
        product_score = 95
    elif orders >= products * 2:
        product_score = 85
    elif orders >= products:
        product_score = 75
    else:
        product_score = 60

    product_score = clamp(product_score)

    # -------------------------
    # INVENTORY SCORE
    # -------------------------

    if inventory == 0:
        inventory_score = 45
    else:
        inventory_problem_rate = percentage(
            low_stock + out_of_stock,
            inventory
        )

        inventory_score = 100 - inventory_problem_rate

        if out_of_stock > 0:
            inventory_score -= 10

    inventory_score = clamp(inventory_score)

    # -------------------------
    # INVOICE SCORE
    # -------------------------

    if invoices == 0:
        invoice_score = 50
    else:
        payment_rate = percentage(paid_invoices, invoices)
        invoice_score = payment_rate

        if pending_invoices > invoices * 0.5:
            invoice_score -= 15

    invoice_score = clamp(invoice_score)

    # -------------------------
    # EMPLOYEE SCORE
    # -------------------------

    if employees == 0:
        employee_score = 40
    elif orders == 0:
        employee_score = 60
    else:
        orders_per_employee = orders / employees

        if orders_per_employee >= 10:
            employee_score = 95
        elif orders_per_employee >= 5:
            employee_score = 85
        elif orders_per_employee >= 2:
            employee_score = 75
        else:
            employee_score = 65

    employee_score = clamp(employee_score)

    # -------------------------
    # PROJECT SCORE
    # -------------------------

    if projects == 0:
        project_score = 50
    else:
        project_completion_rate = percentage(
            completed_projects,
            projects
        )

        project_score = 50 + (project_completion_rate * 0.5)

        if active_projects > 0:
            project_score += 10

    project_score = clamp(project_score)

    # -------------------------
    # OVERALL SCORE
    # -------------------------

    overall_score = round(
        (
            sales_score +
            order_score +
            customer_score +
            product_score +
            inventory_score +
            invoice_score +
            employee_score +
            project_score
        ) / 8
    )

    # -------------------------
    # BUSINESS LEVEL
    # -------------------------

    if overall_score >= 90:
        business_level = "Excellent"
    elif overall_score >= 80:
        business_level = "Very Strong"
    elif overall_score >= 70:
        business_level = "Healthy"
    elif overall_score >= 60:
        business_level = "Moderate"
    elif overall_score >= 45:
        business_level = "Needs Attention"
    else:
        business_level = "Critical"

    # -------------------------
    # EXPLANATIONS
    # -------------------------

    sales_explanation = (
        f"The business generated total sales of ₹{sales:,.2f}. "
        f"The average order value is ₹{average_order:,.2f}, "
        f"while the highest recorded order is ₹{highest_order:,.2f}. "
        f"The sales performance score is {sales_score}/100."
    )

    order_explanation = (
        f"There are {int(orders)} orders in the system. "
        f"{int(completed)} are completed, "
        f"{int(pending)} are pending and "
        f"{int(cancelled)} are cancelled. "
        f"The completion rate is {completion_rate}% "
        f"and the cancellation rate is {cancellation_rate}%. "
        f"The order management score is {order_score}/100."
    )

    customer_explanation = (
        f"The system contains {int(customers)} customers. "
        f"There are approximately {round(orders / customers, 2) if customers else 0} "
        f"orders per customer. "
        f"The customer engagement score is {customer_score}/100."
    )

    product_explanation = (
        f"The business currently manages {int(products)} products. "
        f"The relationship between product count and order activity "
        f"produces a product performance score of {product_score}/100."
    )

    inventory_explanation = (
        f"There are {int(inventory)} inventory records. "
        f"{int(low_stock)} records are classified as low stock and "
        f"{int(out_of_stock)} are out of stock. "
        f"The inventory health score is {inventory_score}/100."
    )

    invoice_explanation = (
        f"There are {int(invoices)} invoices. "
        f"{int(paid_invoices)} are paid and "
        f"{int(pending_invoices)} are pending. "
        f"The invoice/payment score is {invoice_score}/100."
    )

    employee_explanation = (
        f"The organization contains {int(employees)} employees. "
        f"Based on order activity relative to employee count, "
        f"the workforce efficiency score is {employee_score}/100."
    )

    project_explanation = (
        f"The system contains {int(projects)} projects. "
        f"{int(active_projects)} are active and "
        f"{int(completed_projects)} are completed. "
        f"The project performance score is {project_score}/100."
    )

    # -------------------------
    # RECOMMENDATIONS
    # -------------------------

    recommendations = []

    if cancellation_rate > 15:
        recommendations.append(
            "High cancellation rate detected. Investigate cancelled orders and customer issues."
        )

    if pending > completed:
        recommendations.append(
            "Pending orders are higher than completed orders. Improve order processing speed."
        )

    if low_stock > 0:
        recommendations.append(
            f"{int(low_stock)} low-stock inventory records detected. Consider reordering important products."
        )

    if out_of_stock > 0:
        recommendations.append(
            f"{int(out_of_stock)} products appear to be out of stock. Immediate inventory attention is recommended."
        )

    if pending_invoices > invoices * 0.3 if invoices else False:
        recommendations.append(
            "A significant number of invoices are pending. Follow up with customers for payment."
        )

    if project_score < 65:
        recommendations.append(
            "Project completion performance is relatively low. Review delayed projects."
        )

    if customer_score < 65:
        recommendations.append(
            "Customer engagement is moderate. Consider loyalty programs and follow-up campaigns."
        )

    if sales_score < 65:
        recommendations.append(
            "Sales performance is below the desired level. Focus on high-value products and customer retention."
        )

    if not recommendations:
        recommendations.append(
            "Business indicators are healthy. Continue monitoring sales, customers, inventory and invoices."
        )

    return {
        "overall_score": overall_score,
        "business_level": business_level,

        "scores": {
            "sales": sales_score,
            "orders": order_score,
            "customers": customer_score,
            "products": product_score,
            "inventory": inventory_score,
            "invoices": invoice_score,
            "employees": employee_score,
            "projects": project_score
        },

        "explanations": {
            "sales": sales_explanation,
            "orders": order_explanation,
            "customers": customer_explanation,
            "products": product_explanation,
            "inventory": inventory_explanation,
            "invoices": invoice_explanation,
            "employees": employee_explanation,
            "projects": project_explanation
        },

        "recommendations": recommendations,

        "summary": (
            f"The AI analysis rates the overall business at "
            f"{overall_score}/100 ({business_level}). "
            f"The analysis considers sales performance, order completion, "
            f"customer activity, product performance, inventory health, "
            f"invoice collection, employee efficiency and project progress."
        )
    }


def build_user_analysis(data):

    orders = safe_number(data.get("orders"))
    sales = safe_number(data.get("sales"))
    customers = safe_number(data.get("customers"))
    products = safe_number(data.get("products"))
    projects = safe_number(data.get("projects"))

    completed = safe_number(data.get("completed_orders"))
    pending = safe_number(data.get("pending_orders"))
    cancelled = safe_number(data.get("cancelled_orders"))

    total = completed + pending + cancelled

    if total:
        completion_rate = percentage(completed, total)
        cancellation_rate = percentage(cancelled, total)
    else:
        completion_rate = 0
        cancellation_rate = 0

    sales_score = 80 if sales > 0 else 40

    if completion_rate >= 80:
        order_score = 95
    elif completion_rate >= 60:
        order_score = 80
    elif completion_rate >= 40:
        order_score = 65
    else:
        order_score = 50

    customer_score = 80 if customers > 0 else 40
    product_score = 80 if products > 0 else 45
    project_score = 80 if projects > 0 else 50

    overall_score = round(
        (
            sales_score +
            order_score +
            customer_score +
            product_score +
            project_score
        ) / 5
    )

    if overall_score >= 85:
        level = "Excellent"
    elif overall_score >= 70:
        level = "Healthy"
    elif overall_score >= 55:
        level = "Moderate"
    else:
        level = "Needs Attention"

    recommendations = []

    if cancellation_rate > 15:
        recommendations.append(
            "Order cancellation rate is high. Review cancelled orders."
        )

    if pending > completed:
        recommendations.append(
            "Pending orders exceed completed orders. Improve order processing."
        )

    if customers < 5:
        recommendations.append(
            "Customer base is currently small. Focus on customer acquisition."
        )

    if sales <= 0:
        recommendations.append(
            "No sales value was detected. Verify order amount data."
        )

    if not recommendations:
        recommendations.append(
            "The available business indicators look healthy. Continue monitoring performance."
        )

    return {
        "overall_score": overall_score,
        "business_level": level,

        "scores": {
            "sales": sales_score,
            "orders": order_score,
            "customers": customer_score,
            "products": product_score,
            "projects": project_score
        },

        "explanations": {
            "sales": (
                f"Total sales are ₹{sales:,.2f}. "
                f"The sales performance score is {sales_score}/100."
            ),

            "orders": (
                f"There are {int(orders)} orders. "
                f"{int(completed)} are completed, "
                f"{int(pending)} are pending and "
                f"{int(cancelled)} are cancelled. "
                f"Completion rate is {completion_rate}%."
            ),

            "customers": (
                f"The system contains {int(customers)} customers. "
                f"The customer availability score is {customer_score}/100."
            ),

            "products": (
                f"The system contains {int(products)} products. "
                f"The product availability score is {product_score}/100."
            ),

            "projects": (
                f"The system contains {int(projects)} projects. "
                f"The project availability score is {project_score}/100."
            )
        },

        "recommendations": recommendations,

        "summary": (
            f"The user-level AI analysis gives the business a score of "
            f"{overall_score}/100 ({level}). "
            f"This score is based only on the customer, order, product "
            f"and project information available to the user."
        )
    }