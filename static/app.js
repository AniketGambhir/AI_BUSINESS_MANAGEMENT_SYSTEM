// =========================================================
// GLOBAL
// =========================================================

let currentAdminTable = null;
let currentUserTable = null;


// =========================================================
// FORMAT MONEY
// =========================================================

function formatMoney(value) {

    const number =
        Number(value || 0);


    return "₹" +
        number.toLocaleString(
            "en-IN",
            {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }
        );

}


// =========================================================
// ESCAPE HTML
// =========================================================

function escapeHtml(value) {

    if (
        value === null ||
        value === undefined
    ) {

        return "";

    }


    return String(value)

        .replace(
            /&/g,
            "&amp;"
        )

        .replace(
            /</g,
            "&lt;"
        )

        .replace(
            />/g,
            "&gt;"
        )

        .replace(
            /"/g,
            "&quot;"
        )

        .replace(
            /'/g,
            "&#039;"
        );

}


// =========================================================
// ADMIN TABLE
// =========================================================

async function loadAdminTable(table) {

    currentAdminTable =
        table;


    const area =
        document.getElementById(
            "adminTableArea"
        );


    if (!area) {

        return;

    }


    area.innerHTML = `

        <div class="loading">

            Loading ${table}...

        </div>

    `;


    try {

        const response =
            await fetch(
                `/api/table/${table}`
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.error ||
                "Unable to load table."
            );

        }


        renderAdminTable(
            table,
            data
        );

    }
    catch (error) {

        area.innerHTML = `

            <div class="error-message">

                ${escapeHtml(
                    error.message
                )}

            </div>

        `;

    }

}


// =========================================================
// USER TABLE
// =========================================================

async function loadUserTable(table) {

    currentUserTable =
        table;


    const area =
        document.getElementById(
            "userTableArea"
        );


    if (!area) {

        return;

    }


    area.innerHTML = `

        <div class="loading">

            Loading ${table}...

        </div>

    `;


    try {

        const response =
            await fetch(
                `/api/table/${table}`
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.error ||
                "Unable to load table."
            );

        }


        renderUserTable(
            table,
            data
        );

    }
    catch (error) {

        area.innerHTML = `

            <div class="error-message">

                ${escapeHtml(
                    error.message
                )}

            </div>

        `;

    }

}


// =========================================================
// ADMIN TABLE RENDER
// =========================================================

function renderAdminTable(
    table,
    data
) {

    const area =
        document.getElementById(
            "adminTableArea"
        );


    if (!area) {

        return;

    }


    let html = `

        <div class="table-header">

            <div>

                <h3>
                    ${escapeHtml(
                        table.toUpperCase()
                    )}
                </h3>

                <p>
                    ${data.rows.length}
                    record(s)
                </p>

            </div>


            <div class="table-actions">

                <input
                    type="text"
                    id="adminSearch"
                    placeholder="Search ${escapeHtml(table)}..."
                    oninput="searchAdminTable()"
                >

                <button
                    class="neon-button"
                    onclick="showInsertForm('${table}')"
                >
                    + Add
                </button>

            </div>

        </div>


        <div
            id="adminFormArea"
            class="crud-form-area"
        ></div>


        <div class="data-table-wrapper">

            <table class="data-table">

                <thead>

                    <tr>
    `;


    data.columns.forEach(
        function(column) {

            html += `
                <th>
                    ${escapeHtml(column)}
                </th>
            `;

        }
    );


    html += `

                    <th>
                        Actions
                    </th>

                </tr>

                </thead>

                <tbody id="adminTableBody">

    `;


    data.rows.forEach(
        function(row) {

            const primaryKey =
                data.primary_key;


            const primaryValue =
                row[primaryKey];


            html += `<tr>`;


            data.columns.forEach(
                function(column) {

                    html += `

                        <td>

                            ${escapeHtml(
                                row[column]
                            )}

                        </td>

                    `;

                }
            );


            html += `

                <td class="action-cell">

                    <button
                        class="small-button edit-button"
                        onclick='showEditForm(
                            ${JSON.stringify(table)},
                            ${JSON.stringify(row)},
                            ${JSON.stringify(data)}
                        )'
                    >
                        Edit
                    </button>


                    <button
                        class="small-button delete-button"
                        onclick='deleteRecord(
                            ${JSON.stringify(table)},
                            ${JSON.stringify(primaryValue)}
                        )'
                    >
                        Delete
                    </button>

                </td>

            `;


            html += `</tr>`;

        }
    );


    html += `

                </tbody>

            </table>

        </div>

    `;


    area.innerHTML =
        html;

}


// =========================================================
// USER TABLE RENDER
// =========================================================

function renderUserTable(
    table,
    data
) {

    const area =
        document.getElementById(
            "userTableArea"
        );


    if (!area) {

        return;

    }


    let html = `

        <div class="table-header">

            <div>

                <h3>
                    ${escapeHtml(
                        table.toUpperCase()
                    )}
                </h3>

                <p>
                    Read-only data
                </p>

            </div>


            <div class="table-actions">

                <input
                    type="text"
                    id="userSearch"
                    placeholder="Search ${escapeHtml(table)}..."
                    oninput="searchUserTable()"
                >

            </div>

        </div>


        <div class="data-table-wrapper">

            <table class="data-table">

                <thead>

                    <tr>
    `;


    data.columns.forEach(
        function(column) {

            html += `

                <th>
                    ${escapeHtml(column)}
                </th>

            `;

        }
    );


    html += `

                    </tr>

                </thead>

                <tbody>

    `;


    data.rows.forEach(
        function(row) {

            html += `<tr>`;


            data.columns.forEach(
                function(column) {

                    html += `

                        <td>

                            ${escapeHtml(
                                row[column]
                            )}

                        </td>

                    `;

                }
            );


            html += `</tr>`;

        }
    );


    html += `

                </tbody>

            </table>

        </div>

    `;


    area.innerHTML =
        html;

}


// =========================================================
// SEARCH ADMIN
// =========================================================

async function searchAdminTable() {

    if (!currentAdminTable) {

        return;

    }


    const input =
        document.getElementById(
            "adminSearch"
        );


    const search =
        input
            ? input.value
            : "";


    try {

        const response =
            await fetch(

                `/api/table/${currentAdminTable}` +
                `?search=${encodeURIComponent(search)}`

            );


        const data =
            await response.json();


        if (!response.ok) {

            return;

        }


        renderAdminTable(
            currentAdminTable,
            data
        );


        const newInput =
            document.getElementById(
                "adminSearch"
            );


        if (newInput) {

            newInput.focus();

            newInput.value =
                search;

        }

    }
    catch (error) {

        console.error(error);

    }

}


// =========================================================
// SEARCH USER
// =========================================================

async function searchUserTable() {

    if (!currentUserTable) {

        return;

    }


    const input =
        document.getElementById(
            "userSearch"
        );


    const search =
        input
            ? input.value
            : "";


    try {

        const response =
            await fetch(

                `/api/table/${currentUserTable}` +
                `?search=${encodeURIComponent(search)}`

            );


        const data =
            await response.json();


        if (!response.ok) {

            return;

        }


        renderUserTable(
            currentUserTable,
            data
        );


        const newInput =
            document.getElementById(
                "userSearch"
            );


        if (newInput) {

            newInput.focus();

            newInput.value =
                search;

        }

    }
    catch (error) {

        console.error(error);

    }

}


// =========================================================
// INSERT FORM
// =========================================================

async function showInsertForm(table) {

    const formArea =
        document.getElementById(
            "adminFormArea"
        );


    if (!formArea) {

        return;

    }


    try {

        const response =
            await fetch(
                `/api/table/${table}/columns`
            );


        const data =
            await response.json();


        let html = `

            <div class="crud-form">

                <div class="crud-form-title">

                    <h3>
                        Add ${escapeHtml(table)}
                    </h3>

                    <button
                        class="close-button"
                        onclick="closeForm()"
                    >
                        ×
                    </button>

                </div>


                <form
                    onsubmit="insertRecord(event, '${table}')"
                >

                    <div class="form-grid">

        `;


        data.columns.forEach(
            function(column) {

                const isAuto =
                    column.Extra &&
                    column.Extra.includes(
                        "auto_increment"
                    );


                if (isAuto) {

                    return;

                }


                html += `

                    <div class="input-group">

                        <label>
                            ${escapeHtml(
                                column.Field
                            )}
                        </label>

                        <input
                            type="text"
                            name="${escapeHtml(
                                column.Field
                            )}"
                            placeholder="Enter ${escapeHtml(
                                column.Field
                            )}"
                        >

                    </div>

                `;

            }
        );


        html += `

                    </div>


                    <button
                        type="submit"
                        class="neon-button"
                    >
                        Insert Record
                    </button>

                </form>

            </div>

        `;


        formArea.innerHTML =
            html;


    }
    catch (error) {

        formArea.innerHTML = `

            <div class="error-message">

                ${escapeHtml(
                    error.message
                )}

            </div>

        `;

    }

}


// =========================================================
// EDIT FORM
// =========================================================

function showEditForm(
    table,
    row,
    data
) {

    const formArea =
        document.getElementById(
            "adminFormArea"
        );


    if (!formArea) {

        return;

    }


    const primaryKey =
        data.primary_key;


    let html = `

        <div class="crud-form">

            <div class="crud-form-title">

                <h3>
                    Edit ${escapeHtml(table)}
                </h3>

                <button
                    class="close-button"
                    onclick="closeForm()"
                >
                    ×
                </button>

            </div>


            <form
                onsubmit='updateRecord(
                    event,
                    ${JSON.stringify(table)},
                    ${JSON.stringify(row[primaryKey])}
                )'
            >

                <div class="form-grid">

    `;


    data.columns.forEach(
        function(column) {

            const field =
                column;


            const value =
                row[field] ?? "";


            const isPrimary =
                field === primaryKey;


            html += `

                <div class="input-group">

                    <label>
                        ${escapeHtml(field)}
                    </label>

                    <input
                        type="text"
                        name="${escapeHtml(field)}"
                        value="${escapeHtml(value)}"
                        ${isPrimary ? "readonly" : ""}
                    >

                </div>

            `;

        }
    );


    html += `

                </div>


                <button
                    type="submit"
                    class="neon-button"
                >
                    Update Record
                </button>

            </form>

        </div>

    `;


    formArea.innerHTML =
        html;

}


// =========================================================
// CLOSE FORM
// =========================================================

function closeForm() {

    const area =
        document.getElementById(
            "adminFormArea"
        );


    if (area) {

        area.innerHTML =
            "";

    }

}


// =========================================================
// INSERT RECORD
// =========================================================

async function insertRecord(
    event,
    table
) {

    event.preventDefault();


    const form =
        event.target;


    const formData =
        new FormData(form);


    const data = {};


    formData.forEach(
        function(value, key) {

            data[key] =
                value;

        }
    );


    try {

        const response =
            await fetch(
                `/api/table/${table}`,
                {

                    method:
                        "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify(data)

                }
            );


        const result =
            await response.json();


        if (!response.ok) {

            alert(
                result.error ||
                "Insert failed."
            );

            return;

        }


        alert(
            result.message
        );


        closeForm();


        loadAdminTable(
            table
        );


        loadDashboard();

    }
    catch (error) {

        alert(
            error.message
        );

    }

}


// =========================================================
// UPDATE RECORD
// =========================================================

async function updateRecord(
    event,
    table,
    primaryValue
) {

    event.preventDefault();


    const form =
        event.target;


    const formData =
        new FormData(form);


    const data = {};


    formData.forEach(
        function(value, key) {

            data[key] =
                value;

        }
    );


    try {

        const response =
            await fetch(

                `/api/table/${table}/${encodeURIComponent(primaryValue)}`,

                {

                    method:
                        "PUT",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body:
                        JSON.stringify(data)

                }

            );


        const result =
            await response.json();


        if (!response.ok) {

            alert(
                result.error ||
                "Update failed."
            );

            return;

        }


        alert(
            result.message
        );


        closeForm();


        loadAdminTable(
            table
        );


        loadDashboard();

    }
    catch (error) {

        alert(
            error.message
        );

    }

}


// =========================================================
// DELETE RECORD
// =========================================================

async function deleteRecord(
    table,
    primaryValue
) {

    const confirmed =
        confirm(
            "Are you sure you want to delete this record?"
        );


    if (!confirmed) {

        return;

    }


    try {

        const response =
            await fetch(

                `/api/table/${table}/${encodeURIComponent(primaryValue)}`,

                {

                    method:
                        "DELETE"

                }

            );


        const result =
            await response.json();


        if (!response.ok) {

            alert(
                result.error ||
                "Delete failed."
            );

            return;

        }


        alert(
            result.message
        );


        loadAdminTable(
            table
        );


        loadDashboard();

    }
    catch (error) {

        alert(
            error.message
        );

    }

}


// =========================================================
// SUMMARY
// =========================================================

function updateSummary(summary) {

    if (!summary) {

        return;

    }


    const totalOrders =
        document.getElementById(
            "totalOrders"
        );


    const totalSales =
        document.getElementById(
            "totalSales"
        );


    const averageOrder =
        document.getElementById(
            "averageOrder"
        );


    const highestOrder =
        document.getElementById(
            "highestOrder"
        );


    if (totalOrders) {

        totalOrders.textContent =
            Number(
                summary.total_orders || 0
            ).toLocaleString(
                "en-IN"
            );

    }


    if (totalSales) {

        totalSales.textContent =
            formatMoney(
                summary.total_sales
            );

    }


    if (averageOrder) {

        averageOrder.textContent =
            formatMoney(
                summary.average_order
            );

    }


    if (highestOrder) {

        highestOrder.textContent =
            formatMoney(
                summary.highest_order
            );

    }

}


// =========================================================
// AI
// =========================================================

function updateAI(ai) {

    if (!ai) {

        return;

    }


    const aiOrders =
        document.getElementById(
            "aiOrders"
        );


    const aiTotalSales =
        document.getElementById(
            "aiTotalSales"
        );


    const aiAverage =
        document.getElementById(
            "aiAverage"
        );


    const aiHighest =
        document.getElementById(
            "aiHighest"
        );


    const aiLowest =
        document.getElementById(
            "aiLowest"
        );


    const aiPrediction =
        document.getElementById(
            "aiPrediction"
        );


    const aiSalesSummary =
        document.getElementById(
            "aiSalesSummary"
        );


    const aiSalesPerformance =
        document.getElementById(
            "aiSalesPerformance"
        );


    const aiOrderPattern =
        document.getElementById(
            "aiOrderPattern"
        );


    const aiTrendAnalysis =
        document.getElementById(
            "aiTrendAnalysis"
        );


    const aiPredictionAnalysis =
        document.getElementById(
            "aiPredictionAnalysis"
        );


    const aiRecommendation =
        document.getElementById(
            "aiRecommendation"
        );


    if (aiOrders) {

        aiOrders.textContent =
            Number(
                ai.orders_analyzed || 0
            ).toLocaleString(
                "en-IN"
            );

    }


    if (aiTotalSales) {

        aiTotalSales.textContent =
            formatMoney(
                ai.total_sales
            );

    }


    if (aiAverage) {

        aiAverage.textContent =
            formatMoney(
                ai.average_order
            );

    }


    if (aiHighest) {

        aiHighest.textContent =
            formatMoney(
                ai.highest_order
            );

    }


    if (aiLowest) {

        aiLowest.textContent =
            formatMoney(
                ai.lowest_order
            );

    }


    if (aiPrediction) {

        aiPrediction.textContent =
            formatMoney(
                ai.predicted_next_order
            );

    }


    if (aiSalesSummary) {

        aiSalesSummary.textContent =
            ai.sales_summary ||
            "No summary available.";

    }


    if (aiSalesPerformance) {

        aiSalesPerformance.textContent =
            ai.sales_performance ||
            "No sales performance analysis available.";

    }


    if (aiOrderPattern) {

        aiOrderPattern.textContent =
            ai.order_pattern ||
            "No order pattern available.";

    }


    if (aiTrendAnalysis) {

        aiTrendAnalysis.textContent =
            ai.trend_analysis ||
            "No trend analysis available.";

    }


    if (aiPredictionAnalysis) {

        aiPredictionAnalysis.textContent =
            ai.prediction_analysis ||
            "No prediction analysis available.";

    }


    if (aiRecommendation) {

        aiRecommendation.textContent =
            ai.business_recommendation ||
            "No recommendation available.";

    }

}


// =========================================================
// SIMPLE BAR CHART
// =========================================================

function drawBarChart(
    canvas,
    labels,
    values,
    title
) {

    if (!canvas) {

        return;

    }


    const container =
        canvas.parentElement;


    const rect =
        container.getBoundingClientRect();


    const width =
        Math.max(
            rect.width,
            300
        );


    const height =
        Math.max(
            rect.height,
            280
        );


    const ratio =
        window.devicePixelRatio || 1;


    canvas.width =
        width * ratio;


    canvas.height =
        height * ratio;


    canvas.style.width =
        width + "px";


    canvas.style.height =
        height + "px";


    const ctx =
        canvas.getContext(
            "2d"
        );


    ctx.setTransform(
        ratio,
        0,
        0,
        ratio,
        0,
        0
    );


    ctx.clearRect(
        0,
        0,
        width,
        height
    );


    if (!values.length) {

        ctx.fillStyle =
            "#777";

        ctx.font =
            "14px Arial";

        ctx.textAlign =
            "center";

        ctx.fillText(
            "No data available",
            width / 2,
            height / 2
        );

        return;

    }


    const left = 55;

    const right = 25;

    const top = 30;

    const bottom = 55;


    const chartWidth =
        width -
        left -
        right;


    const chartHeight =
        height -
        top -
        bottom;


    const maxValue =
        Math.max(
            ...values,
            1
        );


    // Grid

    ctx.strokeStyle =
        "#1b1b1b";

    ctx.lineWidth = 1;


    for (
        let i = 0;
        i <= 5;
        i++
    ) {

        const y =
            top +
            chartHeight -
            (
                chartHeight *
                i /
                5
            );


        ctx.beginPath();

        ctx.moveTo(
            left,
            y
        );

        ctx.lineTo(
            width - right,
            y
        );

        ctx.stroke();


        ctx.fillStyle =
            "#777";

        ctx.font =
            "11px Arial";

        ctx.textAlign =
            "right";


        ctx.fillText(
            Math.round(
                maxValue * i / 5
            ),
            left - 8,
            y + 4
        );

    }


    const gap = 15;


    const barWidth =
        Math.max(
            20,
            (
                chartWidth -
                gap *
                (values.length - 1)
            )
            /
            values.length
        );


    values.forEach(
        function(value, index) {

            const x =
                left +
                index *
                (
                    barWidth +
                    gap
                );


            const barHeight =
                (
                    value /
                    maxValue
                ) *
                chartHeight;


            const y =
                top +
                chartHeight -
                barHeight;


            // Bar

            ctx.fillStyle =
                "#00bfff";


            ctx.fillRect(
                x,
                y,
                barWidth,
                barHeight
            );


            // Value

            ctx.fillStyle =
                "#ffffff";

            ctx.font =
                "11px Arial";

            ctx.textAlign =
                "center";


            ctx.fillText(
                Number(
                    value
                ).toLocaleString(
                    "en-IN"
                ),
                x +
                barWidth / 2,
                y - 8
            );


            // Label

            ctx.fillStyle =
                "#888";

            ctx.font =
                "10px Arial";


            let label =
                String(
                    labels[index]
                );


            if (
                label.length > 12
            ) {

                label =
                    label.substring(
                        0,
                        12
                    ) +
                    "...";

            }


            ctx.fillText(
                label,
                x +
                barWidth / 2,
                top +
                chartHeight +
                25
            );

        }
    );

}


// =========================================================
// ORDER STATUS CHART
// =========================================================

function drawOrderStatusChart(data) {

    const canvas =
        document.getElementById(
            "orderStatusChart"
        );


    if (!canvas) {

        return;

    }


    const labels = [];

    const values = [];


    (data || []).forEach(
        function(item) {

            labels.push(
                item.status ||
                "Unknown"
            );


            values.push(
                Number(
                    item.count || 0
                )
            );

        }
    );


    drawBarChart(
        canvas,
        labels,
        values,
        "Orders"
    );

}


// =========================================================
// INVENTORY CHART
// =========================================================

function drawInventoryChart(data) {

    const canvas =
        document.getElementById(
            "inventoryChart"
        );


    if (!canvas) {

        return;

    }


    const labels = [];

    const values = [];


    (data || []).forEach(
        function(item) {

            labels.push(
                item.category ||
                "Unknown"
            );


            values.push(
                Number(
                    item.quantity || 0
                )
            );

        }
    );


    drawBarChart(
        canvas,
        labels,
        values,
        "Inventory"
    );

}


// =========================================================
// SALES TREND CHART
// =========================================================

function drawSalesTrendChart(data) {

    const canvas =
        document.getElementById(
            "salesTrendChart"
        );


    if (!canvas) {

        return;

    }


    const labels = [];

    const values = [];


    (data || []).forEach(
        function(item) {

            labels.push(
                item.order_date
            );


            values.push(
                Number(
                    item.sales || 0
                )
            );

        }
    );


    drawLineChart(
        canvas,
        labels,
        values
    );

}


// =========================================================
// SALES STATUS CHART
// =========================================================

function drawSalesStatusChart(data) {

    const canvas =
        document.getElementById(
            "salesStatusChart"
        );


    if (!canvas) {

        return;

    }


    const labels = [];

    const values = [];


    (data || []).forEach(
        function(item) {

            labels.push(
                item.status ||
                "Unknown"
            );


            values.push(
                Number(
                    item.sales || 0
                )
            );

        }
    );


    drawMoneyBarChart(
        canvas,
        labels,
        values
    );

}


// =========================================================
// MONEY BAR CHART
// =========================================================

function drawMoneyBarChart(
    canvas,
    labels,
    values
) {

    if (!canvas) {

        return;

    }


    const container =
        canvas.parentElement;


    const rect =
        container.getBoundingClientRect();


    const width =
        Math.max(
            rect.width,
            300
        );


    const height =
        Math.max(
            rect.height,
            280
        );


    const ratio =
        window.devicePixelRatio || 1;


    canvas.width =
        width * ratio;


    canvas.height =
        height * ratio;


    canvas.style.width =
        width + "px";


    canvas.style.height =
        height + "px";


    const ctx =
        canvas.getContext(
            "2d"
        );


    ctx.setTransform(
        ratio,
        0,
        0,
        ratio,
        0,
        0
    );


    ctx.clearRect(
        0,
        0,
        width,
        height
    );


    if (!values.length) {

        ctx.fillStyle =
            "#777";

        ctx.font =
            "14px Arial";

        ctx.textAlign =
            "center";

        ctx.fillText(
            "No sales data available",
            width / 2,
            height / 2
        );

        return;

    }


    const left = 65;

    const right = 25;

    const top = 30;

    const bottom = 55;


    const chartWidth =
        width -
        left -
        right;


    const chartHeight =
        height -
        top -
        bottom;


    const maxValue =
        Math.max(
            ...values,
            1
        );


    // Grid

    ctx.strokeStyle =
        "#1b1b1b";

    for (
        let i = 0;
        i <= 5;
        i++
    ) {

        const y =
            top +
            chartHeight -
            (
                chartHeight *
                i /
                5
            );


        ctx.beginPath();

        ctx.moveTo(
            left,
            y
        );

        ctx.lineTo(
            width - right,
            y
        );

        ctx.stroke();


        ctx.fillStyle =
            "#777";

        ctx.font =
            "10px Arial";

        ctx.textAlign =
            "right";


        ctx.fillText(
            formatMoney(
                maxValue * i / 5
            ),
            left - 8,
            y + 4
        );

    }


    const gap = 20;


    const barWidth =
        Math.max(
            25,
            (
                chartWidth -
                gap *
                (values.length - 1)
            )
            /
            values.length
        );


    values.forEach(
        function(value, index) {

            const x =
                left +
                index *
                (
                    barWidth +
                    gap
                );


            const barHeight =
                (
                    value /
                    maxValue
                ) *
                chartHeight;


            const y =
                top +
                chartHeight -
                barHeight;


            ctx.fillStyle =
                "#00bfff";


            ctx.fillRect(
                x,
                y,
                barWidth,
                barHeight
            );


            ctx.fillStyle =
                "#ffffff";

            ctx.font =
                "10px Arial";

            ctx.textAlign =
                "center";


            ctx.fillText(
                formatMoney(
                    value
                ),
                x +
                barWidth / 2,
                y - 8
            );


            ctx.fillStyle =
                "#888";

            let label =
                String(
                    labels[index]
                );


            if (
                label.length > 12
            ) {

                label =
                    label.substring(
                        0,
                        12
                    ) +
                    "...";

            }


            ctx.fillText(
                label,
                x +
                barWidth / 2,
                top +
                chartHeight +
                25
            );

        }
    );

}


// =========================================================
// LINE CHART
// =========================================================

function drawLineChart(
    canvas,
    labels,
    values
) {

    if (!canvas) {

        return;

    }


    const container =
        canvas.parentElement;


    const rect =
        container.getBoundingClientRect();


    const width =
        Math.max(
            rect.width,
            300
        );


    const height =
        Math.max(
            rect.height,
            280
        );


    const ratio =
        window.devicePixelRatio || 1;


    canvas.width =
        width * ratio;


    canvas.height =
        height * ratio;


    canvas.style.width =
        width + "px";


    canvas.style.height =
        height + "px";


    const ctx =
        canvas.getContext(
            "2d"
        );


    ctx.setTransform(
        ratio,
        0,
        0,
        ratio,
        0,
        0
    );


    ctx.clearRect(
        0,
        0,
        width,
        height
    );


    if (!values.length) {

        ctx.fillStyle =
            "#777";

        ctx.font =
            "14px Arial";

        ctx.textAlign =
            "center";

        ctx.fillText(
            "No sales data available",
            width / 2,
            height / 2
        );

        return;

    }


    const left = 65;

    const right = 25;

    const top = 30;

    const bottom = 55;


    const chartWidth =
        width -
        left -
        right;


    const chartHeight =
        height -
        top -
        bottom;


    const maxValue =
        Math.max(
            ...values,
            1
        );


    // Grid

    ctx.strokeStyle =
        "#1b1b1b";


    for (
        let i = 0;
        i <= 5;
        i++
    ) {

        const y =
            top +
            chartHeight -
            (
                chartHeight *
                i /
                5
            );


        ctx.beginPath();

        ctx.moveTo(
            left,
            y
        );

        ctx.lineTo(
            width - right,
            y
        );

        ctx.stroke();


        ctx.fillStyle =
            "#777";

        ctx.font =
            "10px Arial";

        ctx.textAlign =
            "right";


        ctx.fillText(
            formatMoney(
                maxValue * i / 5
            ),
            left - 8,
            y + 4
        );

    }


    // Points

    const points = [];


    values.forEach(
        function(value, index) {

            const x =
                left +
                (
                    index /
                    Math.max(
                        values.length - 1,
                        1
                    )
                )
                *
                chartWidth;


            const y =
                top +
                chartHeight -
                (
                    value /
                    maxValue
                )
                *
                chartHeight;


            points.push({

                x: x,

                y: y

            });

        }
    );


    // Line

    ctx.strokeStyle =
        "#00bfff";

    ctx.lineWidth =
        3;


    ctx.beginPath();


    points.forEach(
        function(point, index) {

            if (index === 0) {

                ctx.moveTo(
                    point.x,
                    point.y
                );

            }
            else {

                ctx.lineTo(
                    point.x,
                    point.y
                );

            }

        }
    );


    ctx.stroke();


    // Points

    points.forEach(
        function(point, index) {

            ctx.fillStyle =
                "#00bfff";


            ctx.beginPath();

            ctx.arc(
                point.x,
                point.y,
                5,
                0,
                Math.PI * 2
            );


            ctx.fill();


            ctx.fillStyle =
                "#fff";


            ctx.font =
                "10px Arial";


            ctx.textAlign =
                "center";


            ctx.fillText(
                formatMoney(
                    values[index]
                ),
                point.x,
                point.y - 12
            );

        }
    );


    // Labels

    labels.forEach(
        function(label, index) {

            if (
                labels.length > 8
                &&
                index % 2 !== 0
            ) {

                return;

            }


            const x =
                left +
                (
                    index /
                    Math.max(
                        labels.length - 1,
                        1
                    )
                )
                *
                chartWidth;


            ctx.fillStyle =
                "#888";


            ctx.font =
                "10px Arial";


            ctx.textAlign =
                "center";


            ctx.fillText(
                String(label),
                x,
                top +
                chartHeight +
                25
            );

        }
    );

}


// =========================================================
// LOAD DASHBOARD
// =========================================================

async function loadDashboard() {

    try {

        const response =
            await fetch(
                "/api/dashboard"
            );


        const data =
            await response.json();


        if (!response.ok) {

            console.error(
                data.error
            );

            return;

        }


        updateSummary(
            data.summary
        );


        updateAI(
            data.ai
        );


        drawOrderStatusChart(
            data.order_status
        );


        drawInventoryChart(
            data.inventory_category
        );


        drawSalesTrendChart(
            data.sales_trend
        );


        drawSalesStatusChart(
            data.sales_by_status
        );


        drawAIInventoryChart(
            data.inventory_category
        );

    }
    catch (error) {

        console.error(
            "Dashboard error:",
            error
        );

    }

}


// =========================================================
// AI INVENTORY CHART
// =========================================================

function drawAIInventoryChart(data) {

    const canvas =
        document.getElementById(
            "aiInventoryChart"
        );


    if (!canvas) {

        return;

    }


    const labels = [];

    const values = [];


    (data || []).forEach(
        function(item) {

            labels.push(
                item.category ||
                "Unknown"
            );


            values.push(
                Number(
                    item.quantity || 0
                )
            );

        }
    );


    drawBarChart(
        canvas,
        labels,
        values,
        "Inventory"
    );

}


// =========================================================
// CURSOR GLOW
// =========================================================

document.addEventListener(
    "mousemove",
    function(event) {

        const glow =
            document.querySelector(
                ".cursor-glow"
            );


        if (!glow) {

            return;

        }


        glow.style.left =
            event.clientX + "px";


        glow.style.top =
            event.clientY + "px";

    }
);


// =========================================================
// RESIZE
// =========================================================

window.addEventListener(
    "resize",
    function() {

        const chart =
            document.getElementById(
                "salesTrendChart"
            );


        if (chart) {

            loadDashboard();

        }

    }
);


// =========================================================
// PAGE LOAD
// =========================================================

document.addEventListener(
    "DOMContentLoaded",
    function() {

        if (
            document.getElementById(
                "salesTrendChart"
            )
        ) {

            loadDashboard();

        }

    }
);