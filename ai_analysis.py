import numpy as np
from sklearn.linear_model import LinearRegression


def analyze_sales(rows):

    # =====================================================
    # NO DATA
    # =====================================================

    if not rows:

        return {

            "success": False,

            "orders_analyzed": 0,

            "total_sales": 0,

            "average_order": 0,

            "highest_order": 0,

            "lowest_order": 0,

            "predicted_next_order": 0,

            "sales_summary":
                "No order records are currently available. "
                "The AI analysis will become available after "
                "orders are added to the business database.",

            "sales_performance":
                "There is not enough sales data to analyse business performance.",

            "order_pattern":
                "There are no orders available to identify an order pattern.",

            "trend_analysis":
                "A sales trend cannot be calculated without order records.",

            "prediction_analysis":
                "A prediction cannot be generated until sufficient order data is available.",

            "business_recommendation":
                "Add order data and continue monitoring the business dashboard."

        }


    # =====================================================
    # EXTRACT ORDER AMOUNTS
    # =====================================================

    amounts = []

    for row in rows:

        try:

            amount = float(
                row.get("total_amount", 0) or 0
            )

            if amount >= 0:

                amounts.append(amount)

        except (ValueError, TypeError):

            continue


    # =====================================================
    # INVALID DATA
    # =====================================================

    if not amounts:

        return {

            "success": False,

            "orders_analyzed": 0,

            "total_sales": 0,

            "average_order": 0,

            "highest_order": 0,

            "lowest_order": 0,

            "predicted_next_order": 0,

            "sales_summary":
                "Valid sales amounts were not found in the orders table.",

            "sales_performance":
                "The available sales values could not be analysed.",

            "order_pattern":
                "Order pattern analysis is unavailable.",

            "trend_analysis":
                "Sales trend analysis is unavailable.",

            "prediction_analysis":
                "AI prediction is unavailable.",

            "business_recommendation":
                "Check the total_amount column in the orders table."

        }


    # =====================================================
    # BASIC CALCULATIONS
    # =====================================================

    total_sales = sum(amounts)

    order_count = len(amounts)

    average_order = (
        total_sales / order_count
    )

    highest_order = max(amounts)

    lowest_order = min(amounts)


    # =====================================================
    # TREND
    # =====================================================

    if len(amounts) >= 2:

        first_value = amounts[0]

        last_value = amounts[-1]

        difference = (
            last_value - first_value
        )

        if difference > 0:

            trend = "increasing"

        elif difference < 0:

            trend = "decreasing"

        else:

            trend = "stable"

    else:

        trend = "not enough data"


    # =====================================================
    # PERCENTAGE CHANGE
    # =====================================================

    if (
        len(amounts) >= 2
        and amounts[0] != 0
    ):

        percentage_change = (

            (
                amounts[-1]
                - amounts[0]
            )
            /
            abs(amounts[0])
        ) * 100

    else:

        percentage_change = 0


    # =====================================================
    # MACHINE LEARNING PREDICTION
    # =====================================================

    predicted_next_order = average_order


    if len(amounts) >= 2:

        try:

            x = np.arange(
                1,
                len(amounts) + 1
            ).reshape(-1, 1)

            y = np.array(amounts)

            model = LinearRegression()

            model.fit(
                x,
                y
            )

            next_x = np.array(
                [[len(amounts) + 1]]
            )

            predicted_next_order = float(
                model.predict(next_x)[0]
            )

            predicted_next_order = max(
                0,
                predicted_next_order
            )

        except Exception:

            predicted_next_order = average_order


    # =====================================================
    # SALES SUMMARY
    # =====================================================

    sales_summary = (

        f"The AI system analysed {order_count} "
        f"business orders. The total recorded sales "
        f"are ₹{total_sales:,.2f}. The average order "
        f"value is ₹{average_order:,.2f}. The highest "
        f"order is ₹{highest_order:,.2f}, while the "
        f"lowest order is ₹{lowest_order:,.2f}."

    )


    # =====================================================
    # SALES PERFORMANCE
    # =====================================================

    sales_performance = (

        f"The business has generated total sales of "
        f"₹{total_sales:,.2f} across {order_count} "
        f"analysed orders. The average order value is "
        f"₹{average_order:,.2f}. These values provide "
        f"a summary of the sales activity currently "
        f"stored in the business database."

    )


    # =====================================================
    # ORDER PATTERN
    # =====================================================

    order_range = (
        highest_order
        - lowest_order
    )


    if order_range > average_order:

        order_pattern = (

            f"The order values show noticeable variation. "
            f"The difference between the highest and lowest "
            f"order is ₹{order_range:,.2f}. This means that "
            f"the business has orders with significantly "
            f"different values."

        )

    else:

        order_pattern = (

            "The order values are relatively close to "
            "each other compared with the average order "
            "value."

        )


    # =====================================================
    # TREND ANALYSIS
    # =====================================================

    if trend == "increasing":

        trend_analysis = (

            f"The latest order value is higher than "
            f"the first analysed order. The observed "
            f"change is approximately "
            f"{abs(percentage_change):.2f}%. "
            f"The available records therefore show "
            f"an increasing order-value pattern."

        )

    elif trend == "decreasing":

        trend_analysis = (

            f"The latest order value is lower than "
            f"the first analysed order. The observed "
            f"change is approximately "
            f"{abs(percentage_change):.2f}%. "
            f"The available records therefore show "
            f"a decreasing order-value pattern."

        )

    elif trend == "stable":

        trend_analysis = (

            "The first and latest order values are "
            "similar. The available records therefore "
            "show a relatively stable order-value pattern."

        )

    else:

        trend_analysis = (

            "More order records are required to "
            "identify a meaningful trend."

        )


    # =====================================================
    # PREDICTION DESCRIPTION
    # =====================================================

    prediction_difference = (

        predicted_next_order
        - average_order

    )


    if prediction_difference > 0:

        prediction_analysis = (

            f"The simple machine-learning model "
            f"estimates the next order value at "
            f"approximately ₹{predicted_next_order:,.2f}. "
            f"This estimate is above the historical "
            f"average order value of "
            f"₹{average_order:,.2f}."

        )

    elif prediction_difference < 0:

        prediction_analysis = (

            f"The simple machine-learning model "
            f"estimates the next order value at "
            f"approximately ₹{predicted_next_order:,.2f}. "
            f"This estimate is below the historical "
            f"average order value of "
            f"₹{average_order:,.2f}."

        )

    else:

        prediction_analysis = (

            f"The simple machine-learning model "
            f"estimates the next order value at "
            f"approximately ₹{predicted_next_order:,.2f}, "
            f"which is close to the historical average."

        )


    # =====================================================
    # BUSINESS RECOMMENDATION
    # =====================================================

    if trend == "increasing":

        business_recommendation = (

            "The available order records show an "
            "increasing order-value pattern. Continue "
            "monitoring products, customers and order "
            "categories associated with recent activity. "
            "Inventory levels should also be monitored "
            "so that commonly ordered products remain "
            "available."

        )

    elif trend == "decreasing":

        business_recommendation = (

            "The available order records show a "
            "decreasing order-value pattern. Review "
            "recent customer activity, product demand "
            "and order records to understand changes "
            "in business activity."

        )

    else:

        business_recommendation = (

            "Continue monitoring orders, sales values "
            "and inventory activity. The dashboard "
            "provides a central view of business data "
            "and can help identify changes as more "
            "records are collected."

        )


    # =====================================================
    # RETURN
    # =====================================================

    return {

        "success": True,

        "orders_analyzed":
            order_count,

        "total_sales":
            round(
                total_sales,
                2
            ),

        "average_order":
            round(
                average_order,
                2
            ),

        "highest_order":
            round(
                highest_order,
                2
            ),

        "lowest_order":
            round(
                lowest_order,
                2
            ),

        "predicted_next_order":
            round(
                predicted_next_order,
                2
            ),

        "sales_summary":
            sales_summary,

        "sales_performance":
            sales_performance,

        "order_pattern":
            order_pattern,

        "trend_analysis":
            trend_analysis,

        "prediction_analysis":
            prediction_analysis,

        "business_recommendation":
            business_recommendation

    }