let dashboardData = null;
let currentTable = null;
let currentColumns = [];
let currentPrimaryKey = null;
let editingId = null;

const charts = {};

const chartColors = [
    "#8b5cf6",
    "#3b82f6",
    "#06b6d4",
    "#ec4899",
    "#22c55e",
    "#f59e0b",
    "#ef4444",
    "#14b8a6",
    "#6366f1",
    "#a855f7"
];


document.addEventListener("DOMContentLoaded", () => {

    setupCursorGlow();
    setupNavigation();
    setupTableControls();

    loadDashboard();

});


/* ============================================================
   CURSOR
============================================================ */

function setupCursorGlow() {

    const glow = document.querySelector(".cursor-glow");

    if (!glow) return;

    document.addEventListener("mousemove", (event) => {

        glow.style.left = `${event.clientX}px`;
        glow.style.top = `${event.clientY}px`;

    });

}


/* ============================================================
   NAVIGATION
============================================================ */

function setupNavigation() {

    document.querySelectorAll(".nav-item").forEach(item => {

        item.addEventListener("click", () => {

            document.querySelectorAll(".nav-item")
                .forEach(nav => nav.classList.remove("active"));

            item.classList.add("active");

            const table = item.dataset.table;

            if (table) {

                openTable(table);

            } else {

                showDashboard();

            }

        });

    });

}


function showDashboard() {

    document
        .getElementById("dashboard-section")
        ?.classList.remove("hidden");

    document
        .getElementById("table-section")
        ?.classList.add("hidden");

    const title = document.getElementById("page-title");

    if (title) {
        title.textContent = "Business Dashboard";
    }

    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
}


/* ============================================================
   DASHBOARD
============================================================ */

async function loadDashboard() {

    try {

        const response = await fetch(
            "/api/dashboard"
        );

        const json = await response.json();

        if (!json.success) {

            showToast(
                json.error || "Dashboard error",
                "error"
            );

            return;
        }

        dashboardData = json.data;

        renderStatistics(
            dashboardData
        );

        renderAI(
            dashboardData.ai
        );

        renderCharts(
            dashboardData.charts
        );

        renderRecentOrders(
            dashboardData.recent_orders
        );

    } catch (error) {

        console.error(error);

        showToast(
            "Unable to load dashboard",
            "error"
        );

    }

}


/* ============================================================
   STATISTICS
============================================================ */

function renderStatistics(data) {

    const stats = data.statistics || {};
    const counts = data.counts || {};

    setText(
        "total-orders",
        formatNumber(
            stats.total_orders || 0
        )
    );

    setText(
        "total-sales",
        formatCurrency(
            stats.total_sales || 0
        )
    );

    setText(
        "average-order",
        formatCurrency(
            stats.average_order || 0
        )
    );

    setText(
        "highest-order",
        formatCurrency(
            stats.highest_order || 0
        )
    );


    Object.keys(counts).forEach(table => {

        setText(
            `count-${table}`,
            formatNumber(
                counts[table]
            )
        );

    });

}


/* ============================================================
   AI
============================================================ */

function renderAI(ai) {

    if (!ai) return;

    const score = Number(
        ai.overall_score || 0
    );

    setText(
        "health-score",
        score
    );

    setText(
        "business-level",
        ai.business_level || "Analysing..."
    );

    setText(
        "ai-summary",
        ai.summary || ""
    );


    const scores = ai.scores || {};

    Object.keys(scores).forEach(key => {

        setText(
            `score-${key}`,
            scores[key]
        );

    });


    const explanations =
        ai.explanations || {};

    Object.keys(explanations).forEach(key => {

        setText(
            `explain-${key}`,
            explanations[key]
        );

    });


    const recommendations =
        ai.recommendations || [];

    const recommendationContainer =
        document.getElementById(
            "recommendations"
        );

    if (recommendationContainer) {

        recommendationContainer.innerHTML = "";

        recommendations.forEach(
            recommendation => {

                const item =
                    document.createElement("div");

                item.className =
                    "recommendation-item";

                item.innerHTML = `
                    <span>✓</span>
                    <p>${escapeHtml(
                        recommendation
                    )}</p>
                `;

                recommendationContainer.appendChild(
                    item
                );

            }
        );

    }

}


/* ============================================================
   CHARTS
============================================================ */

function destroyChart(name) {

    if (charts[name]) {

        charts[name].destroy();

        delete charts[name];

    }

}


function createChart(
    name,
    canvasId,
    type,
    labels,
    values
) {

    const canvas =
        document.getElementById(
            canvasId
        );

    if (!canvas) return;

    destroyChart(name);

    if (
        !labels ||
        !labels.length ||
        !values ||
        !values.length
    ) {

        const parent =
            canvas.parentElement;

        parent.innerHTML = `
            <div class="chart-empty">
                No data available
            </div>
        `;

        return;

    }

    const isLine =
        type === "line";

    charts[name] = new Chart(
        canvas.getContext("2d"),
        {
            type: type,

            data: {
                labels: labels,

                datasets: [
                    {
                        label: "Value",

                        data: values,

                        backgroundColor:
                            isLine
                                ? "rgba(59,130,246,0.12)"
                                : chartColors,

                        borderColor:
                            isLine
                                ? "#3b82f6"
                                : chartColors,

                        borderWidth: 2,

                        borderRadius:
                            type === "bar"
                                ? 8
                                : 0,

                        fill: isLine,

                        tension:
                            isLine
                                ? 0.4
                                : 0
                    }
                ]
            },

            options: {
                responsive: true,

                maintainAspectRatio: false,

                animation: {
                    duration: 1200
                },

                plugins: {
                    legend: {
                        display:
                            type === "doughnut"
                    }
                },

                scales:
                    type === "doughnut"
                        ? {}
                        : {
                            x: {
                                grid: {
                                    color:
                                        "rgba(148,163,184,.08)"
                                },

                                ticks: {
                                    color:
                                        "#94a3b8"
                                }
                            },

                            y: {
                                grid: {
                                    color:
                                        "rgba(148,163,184,.08)"
                                },

                                ticks: {
                                    color:
                                        "#94a3b8"
                                },

                                beginAtZero: true
                            }
                        }
            }
        }
    );

}


function renderCharts(chartsData) {

    chartsData =
        chartsData || {};


    /* Monthly Sales */

    const monthly =
        chartsData.monthly_sales || [];

    createChart(
        "monthlySales",
        "monthlySalesChart",
        "line",

        monthly.map(
            item => item.label
        ),

        monthly.map(
            item => Number(item.value)
        )
    );


    /* Order Status */

    const orderStatus =
        chartsData.order_status || [];

    createChart(
        "orderStatus",
        "orderStatusChart",
        "doughnut",

        orderStatus.map(
            item => item.label
        ),

        orderStatus.map(
            item => Number(item.value)
        )
    );


    /* Product */

    const products =
        chartsData.product_performance || [];

    createChart(
        "products",
        "productChart",
        "bar",

        products.map(
            item => item.label
        ),

        products.map(
            item => Number(item.value)
        )
    );


    /* Customer */

    const customers =
        chartsData.customer_activity || [];

    createChart(
        "customers",
        "customerChart",
        "bar",

        customers.map(
            item => item.label
        ),

        customers.map(
            item => Number(item.value)
        )
    );


    /* Projects */

    const projects =
        chartsData.project_status || [];

    createChart(
        "projects",
        "projectChart",
        "doughnut",

        projects.map(
            item => item.label
        ),

        projects.map(
            item => Number(item.value)
        )
    );


    /* Admin charts */

    if (
        window.APP_ROLE === "admin"
    ) {

        const inventory =
            chartsData.inventory_category || [];

        createChart(
            "inventory",
            "inventoryChart",
            "bar",

            inventory.map(
                item => item.label
            ),

            inventory.map(
                item => Number(item.value)
            )
        );


        const invoices =
            chartsData.invoice_status || [];

        createChart(
            "invoices",
            "invoiceChart",
            "doughnut",

            invoices.map(
                item => item.label
            ),

            invoices.map(
                item => Number(item.value)
            )
        );


        const employees =
            chartsData.employee_department || [];

        createChart(
            "employees",
            "employeeChart",
            "bar",

            employees.map(
                item => item.label
            ),

            employees.map(
                item => Number(item.value)
            )
        );

    }

}


/* ============================================================
   RECENT ORDERS
============================================================ */

function renderRecentOrders(rows) {

    const container =
        document.getElementById(
            "recent-orders"
        );

    if (!container) return;

    if (
        !rows ||
        !rows.length
    ) {

        container.innerHTML = `
            <div class="empty-state">
                No recent orders found.
            </div>
        `;

        return;
    }

    const columns =
        Object.keys(rows[0]);

    let html = `
        <div class="table-scroll">
            <table class="data-table">
                <thead>
                    <tr>
    `;

    columns.slice(0, 6).forEach(
        column => {

            html += `
                <th>
                    ${escapeHtml(
                        column
                    )}
                </th>
            `;

        }
    );

    html += `
                    </tr>
                </thead>
                <tbody>
    `;

    rows.forEach(row => {

        html += "<tr>";

        columns.slice(0, 6).forEach(
            column => {

                html += `
                    <td>
                        ${escapeHtml(
                            row[column]
                        )}
                    </td>
                `;

            }
        );

        html += "</tr>";

    });

    html += `
                </tbody>
            </table>
        </div>
    `;

    container.innerHTML = html;

}


/* ============================================================
   TABLE MANAGEMENT
============================================================ */

function setupTableControls() {

    const search =
        document.getElementById(
            "table-search"
        );

    if (search) {

        let timer;

        search.addEventListener(
            "input",
            () => {

                clearTimeout(timer);

                timer = setTimeout(
                    () => {

                        loadTable(
                            currentTable,
                            search.value
                        );

                    },
                    300
                );

            }
        );

    }


    const refresh =
        document.getElementById(
            "refresh-table"
        );

    if (refresh) {

        refresh.addEventListener(
            "click",
            () => {

                loadTable(
                    currentTable,
                    search?.value || ""
                );

            }
        );

    }


    const add =
        document.getElementById(
            "add-record-button"
        );

    if (add) {

        add.addEventListener(
            "click",
            () => {

                if (
                    window.APP_ROLE === "admin"
                ) {

                    openAddModal();

                }

            }
        );

    }


    const modalClose =
        document.getElementById(
            "modal-close"
        );

    const modalCancel =
        document.getElementById(
            "modal-cancel"
        );

    modalClose?.addEventListener(
        "click",
        closeModal
    );

    modalCancel?.addEventListener(
        "click",
        closeModal
    );


    const form =
        document.getElementById(
            "record-form"
        );

    form?.addEventListener(
        "submit",
        saveRecord
    );

}


async function openTable(table) {

    currentTable = table;

    document
        .getElementById("dashboard-section")
        ?.classList.add("hidden");

    document
        .getElementById("table-section")
        ?.classList.remove("hidden");

    const displayName =
        table.charAt(0).toUpperCase() +
        table.slice(1);

    setText(
        "table-title",
        displayName
    );

    setText(
        "page-title",
        displayName
    );

    setText(
        "table-description",
        window.APP_ROLE === "admin"
            ? "Manage database records"
            : "Read-only database records"
    );


    const addButton =
        document.getElementById(
            "add-record-button"
        );

    if (addButton) {

        if (
            window.APP_ROLE === "admin"
        ) {

            addButton.style.display =
                "block";

        } else {

            addButton.style.display =
                "none";

        }

    }


    await loadColumns(table);

    await loadTable(table);

}


async function loadColumns(table) {

    try {

        const response =
            await fetch(
                `/api/table/${table}/columns`
            );

        const json =
            await response.json();

        if (!json.success) {

            showToast(
                json.error,
                "error"
            );

            return;
        }

        currentColumns =
            json.columns || [];

        currentPrimaryKey =
            json.primary_key;

    } catch (error) {

        console.error(error);

    }

}


async function loadTable(
    table,
    search = ""
) {

    if (!table) return;

    try {

        const url =
            `/api/table/${table}` +
            `?search=${encodeURIComponent(search)}` +
            `&limit=100`;

        const response =
            await fetch(url);

        const json =
            await response.json();

        if (!json.success) {

            showToast(
                json.error,
                "error"
            );

            return;
        }

        renderDataTable(json);

    } catch (error) {

        console.error(error);

        showToast(
            "Unable to load table",
            "error"
        );

    }

}


/* ============================================================
   DATA TABLE
============================================================ */

function renderDataTable(data) {

    const container =
        document.getElementById(
            "data-table-container"
        );

    if (!container) return;

    const columns =
        data.columns || [];

    const rows =
        data.rows || [];

    currentPrimaryKey =
        data.primary_key;


    if (!rows.length) {

        container.innerHTML = `
            <div class="empty-state">
                No records found.
            </div>
        `;

        return;
    }


    let html = `
        <div class="table-scroll">
        <table class="data-table">
            <thead>
                <tr>
    `;

    columns.forEach(column => {

        html += `
            <th>
                ${escapeHtml(column)}
            </th>
        `;

    });


    if (
        window.APP_ROLE === "admin"
    ) {

        html += `
            <th>
                Actions
            </th>
        `;

    }

    html += `
                </tr>
            </thead>
            <tbody>
    `;


    rows.forEach(row => {

        html += "<tr>";

        columns.forEach(column => {

            let value =
                row[column];

            if (
                value === null ||
                value === undefined
            ) {

                value = "-";

            }

            html += `
                <td>
                    ${escapeHtml(value)}
                </td>
            `;

        });


        if (
            window.APP_ROLE === "admin"
        ) {

            const id =
                row[currentPrimaryKey];


            html += `
                <td>
                    <div class="action-buttons">
            `;


            /*
             CUSTOMER:
             View + Delete
             NO EDIT
            */

            if (
                currentTable !== "customer"
            ) {

                html += `
                    <button
                        class="action-button edit"
                        onclick='openEditModal(${JSON.stringify(
                            row
                        )})'
                    >
                        Edit
                    </button>
                `;

            } else {

                html += `
                    <button
                        class="action-button view"
                        onclick='viewRecord(${JSON.stringify(
                            row
                        )})'
                    >
                        View
                    </button>
                `;

            }


            html += `
                    <button
                        class="action-button delete"
                        onclick='deleteRecord(${JSON.stringify(
                            id
                        )})'
                    >
                        Delete
                    </button>

                    </div>
                </td>
            `;

        }


        html += "</tr>";

    });


    html += `
            </tbody>
        </table>
        </div>
    `;

    container.innerHTML = html;

}


/* ============================================================
   ADD
============================================================ */

function openAddModal() {

    if (
        window.APP_ROLE !== "admin"
    ) return;

    editingId = null;

    setText(
        "modal-title",
        `Add ${currentTable}`
    );

    const container =
        document.getElementById(
            "form-fields"
        );

    container.innerHTML = "";


    currentColumns.forEach(column => {

        if (
            column.Field ===
            currentPrimaryKey
        ) {

            return;

        }


        const group =
            document.createElement(
                "div"
            );

        group.className =
            "form-group";


        group.innerHTML = `
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
        `;

        container.appendChild(
            group
        );

    });


    document
        .getElementById("modal")
        .classList.remove("hidden");

}


/* ============================================================
   EDIT
============================================================ */

function openEditModal(row) {

    if (
        window.APP_ROLE !== "admin"
    ) return;

    if (
        currentTable === "customer"
    ) {

        showToast(
            "Customer records cannot be edited.",
            "error"
        );

        return;

    }


    editingId =
        row[currentPrimaryKey];


    setText(
        "modal-title",
        `Edit ${currentTable}`
    );


    const container =
        document.getElementById(
            "form-fields"
        );

    container.innerHTML = "";


    currentColumns.forEach(column => {

        const field =
            column.Field;


        if (
            field ===
            currentPrimaryKey
        ) {

            return;

        }


        const group =
            document.createElement(
                "div"
            );

        group.className =
            "form-group";


        const value =
            row[field] ?? "";


        group.innerHTML = `
            <label>
                ${escapeHtml(field)}
            </label>

            <input
                type="text"
                name="${escapeHtml(field)}"
                value="${escapeAttribute(
                    value
                )}"
            >
        `;


        container.appendChild(
            group
        );

    });


    document
        .getElementById("modal")
        .classList.remove("hidden");

}


/* ============================================================
   VIEW CUSTOMER
============================================================ */

function viewRecord(row) {

    const values =
        Object.entries(row)
            .map(
                ([key, value]) => `
                    <div class="view-row">
                        <strong>
                            ${escapeHtml(key)}
                        </strong>

                        <span>
                            ${escapeHtml(
                                value ?? "-"
                            )}
                        </span>
                    </div>
                `
            )
            .join("");


    const container =
        document.getElementById(
            "form-fields"
        );

    container.innerHTML = values;

    setText(
        "modal-title",
        "Customer Details"
    );


    document
        .getElementById("modal")
        .classList.remove("hidden");


    const form =
        document.getElementById(
            "record-form"
        );

    form.onsubmit = event => {
        event.preventDefault();
    };

}


/* ============================================================
   SAVE
============================================================ */

async function saveRecord(event) {

    event.preventDefault();

    if (
        window.APP_ROLE !== "admin"
    ) return;


    const form =
        event.target;

    const formData =
        new FormData(form);

    const data = {};


    formData.forEach(
        (value, key) => {

            data[key] =
                value;

        }
    );


    try {

        let url =
            `/api/table/${currentTable}`;

        let method = "POST";


        if (editingId !== null) {

            url +=
                `/${encodeURIComponent(
                    editingId
                )}`;

            method = "PUT";

        }


        const response =
            await fetch(
                url,
                {
                    method: method,

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify(
                            data
                        )
                }
            );


        const json =
            await response.json();


        if (!json.success) {

            showToast(
                json.error,
                "error"
            );

            return;
        }


        closeModal();

        showToast(
            json.message ||
            "Saved successfully",
            "success"
        );


        loadTable(
            currentTable,
            document.getElementById(
                "table-search"
            )?.value || ""
        );


        loadDashboard();


    } catch (error) {

        console.error(error);

        showToast(
            "Operation failed",
            "error"
        );

    }

}


/* ============================================================
   DELETE
============================================================ */

async function deleteRecord(id) {

    if (
        window.APP_ROLE !== "admin"
    ) return;


    const confirmed =
        confirm(
            "Are you sure you want to delete this record?"
        );


    if (!confirmed) return;


    try {

        const response =
            await fetch(
                `/api/table/${currentTable}/${encodeURIComponent(
                    id
                )}`,
                {
                    method: "DELETE"
                }
            );


        const json =
            await response.json();


        if (!json.success) {

            showToast(
                json.error,
                "error"
            );

            return;
        }


        showToast(
            "Record deleted successfully",
            "success"
        );


        loadTable(
            currentTable,
            document.getElementById(
                "table-search"
            )?.value || ""
        );


        loadDashboard();


    } catch (error) {

        console.error(error);

        showToast(
            "Delete failed",
            "error"
        );

    }

}


/* ============================================================
   MODAL
============================================================ */

function closeModal() {

    const modal =
        document.getElementById(
            "modal"
        );

    modal?.classList.add(
        "hidden"
    );


    const form =
        document.getElementById(
            "record-form"
        );

    if (form) {

        form.reset();

        form.onsubmit = null;

    }

}


/* ============================================================
   TOAST
============================================================ */

function showToast(
    message,
    type = "success"
) {

    const toast =
        document.getElementById(
            "toast"
        );

    if (!toast) return;


    toast.textContent =
        message;


    toast.className =
        `toast ${type} show`;


    setTimeout(
        () => {

            toast.classList.remove(
                "show"
            );

        },
        3000
    );

}


/* ============================================================
   HELPERS
============================================================ */

function setText(
    id,
    value
) {

    const element =
        document.getElementById(id);

    if (element) {

        element.textContent =
            value;

    }

}


function formatNumber(value) {

    const number =
        Number(value || 0);

    return number.toLocaleString(
        "en-IN"
    );

}


function formatCurrency(value) {

    const number =
        Number(value || 0);

    return "₹" +
        number.toLocaleString(
            "en-IN",
            {
                maximumFractionDigits: 2
            }
        );

}


function escapeHtml(value) {

    if (
        value === null ||
        value === undefined
    ) {

        return "";

    }

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");

}


function escapeAttribute(value) {

    return escapeHtml(value);

}