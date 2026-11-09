/* =========================================================
   AI BUSINESS MANAGEMENT SYSTEM
   Main Dashboard JavaScript
   ========================================================= */

"use strict";

/* =========================================================
   GLOBAL VARIABLES
   ========================================================= */

let dashboardData = {};
let aiData = {};
let currentTable = "";
let currentRows = [];
let currentColumns = [];
let currentPage = 1;
let rowsPerPage = 10;

const charts = {};


/* =========================================================
   DOM HELPERS
   ========================================================= */

function $(id) {
    return document.getElementById(id);
}

function exists(id) {
    return $(id) !== null;
}

function safeArray(value) {
    return Array.isArray(value) ? value : [];
}

function safeObject(value) {
    return value && typeof value === "object" ? value : {};
}

function escapeHTML(value) {
    if (value === null || value === undefined) {
        return "";
    }

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function formatNumber(value) {
    const number = Number(value);

    if (!Number.isFinite(number)) {
        return "0";
    }

    return number.toLocaleString("en-IN");
}

function formatCurrency(value) {
    const number = Number(value);

    if (!Number.isFinite(number)) {
        return "₹0";
    }

    return "₹" + number.toLocaleString("en-IN", {
        maximumFractionDigits: 2
    });
}

function formatDate(value) {
    if (!value) {
        return "-";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return String(value);
    }

    return date.toLocaleDateString("en-IN");
}

function capitalize(value) {
    if (!value) {
        return "";
    }

    return String(value)
        .charAt(0)
        .toUpperCase() + String(value).slice(1);
}


/* =========================================================
   API HELPER
   ========================================================= */

async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                "Content-Type": "application/json",
                ...(options.headers || {})
            },
            ...options
        });

        let data;

        try {
            data = await response.json();
        } catch (error) {
            data = {};
        }

        if (!response.ok) {
            throw new Error(
                data.error ||
                data.message ||
                `Request failed with status ${response.status}`
            );
        }

        return data;

    } catch (error) {
        console.error("API ERROR:", url, error);
        throw error;
    }
}


/* =========================================================
   LOADING / EMPTY / ERROR
   ========================================================= */

function showLoading(elementId, message = "Loading...") {
    const element = $(elementId);

    if (!element) {
        return;
    }

    element.innerHTML = `
        <div class="loading-state">
            <div class="loading-spinner"></div>
            <p>${escapeHTML(message)}</p>
        </div>
    `;
}

function showEmpty(elementId, message = "No data available") {
    const element = $(elementId);

    if (!element) {
        return;
    }

    element.innerHTML = `
        <div class="empty-state">
            <div class="empty-icon">◌</div>
            <p>${escapeHTML(message)}</p>
        </div>
    `;
}

function showError(elementId, message = "Something went wrong") {
    const element = $(elementId);

    if (!element) {
        return;
    }

    element.innerHTML = `
        <div class="error-state">
            <p>${escapeHTML(message)}</p>
        </div>
    `;
}


/* =========================================================
   DASHBOARD LOADING
   ========================================================= */

async function loadDashboard() {
    try {
        const data = await apiRequest("/api/dashboard");

        dashboardData = safeObject(data);

        console.log("Dashboard data:", dashboardData);

        updateKPIs(dashboardData);
        updateCounts(dashboardData);

        renderMonthlySales(
            getDataset(
                dashboardData,
                [
                    "monthly_sales",
                    "monthlySales",
                    "sales_by_month"
                ]
            )
        );

        renderOrderStatus(
            getDataset(
                dashboardData,
                [
                    "order_status",
                    "orderStatus",
                    "orders_by_status"
                ]
            )
        );

        renderProductPerformance(
            getDataset(
                dashboardData,
                [
                    "product_performance",
                    "productPerformance",
                    "products"
                ]
            )
        );

        renderProjectStatus(
            getDataset(
                dashboardData,
                [
                    "project_status",
                    "projectStatus",
                    "projects_by_status"
                ]
            )
        );

        renderInventoryCategory(
            getDataset(
                dashboardData,
                [
                    "inventory_category",
                    "inventoryCategory",
                    "inventory_by_category"
                ]
            )
        );

        renderInvoiceStatus(
            getDataset(
                dashboardData,
                [
                    "invoice_status",
                    "invoiceStatus",
                    "invoices_by_status"
                ]
            )
        );

        renderEmployeeDepartment(
            getDataset(
                dashboardData,
                [
                    "employee_department",
                    "employeeDepartment",
                    "employees_by_department"
                ]
            )
        );

        renderRecentOrders(
            getDataset(
                dashboardData,
                [
                    "recent_orders",
                    "recentOrders",
                    "orders"
                ]
            )
        );

        renderDashboardRecords(dashboardData);

    } catch (error) {
        console.error("Dashboard loading failed:", error);

        showDashboardError(
            "Unable to load dashboard data. Check Flask and MySQL."
        );
    }
}


/* =========================================================
   DATASET FINDER
   ========================================================= */

function getDataset(data, names) {
    for (const name of names) {
        if (Array.isArray(data[name])) {
            return data[name];
        }
    }

    if (data.data && typeof data.data === "object") {
        for (const name of names) {
            if (Array.isArray(data.data[name])) {
                return data.data[name];
            }
        }
    }

    return [];
}


/* =========================================================
   KPI CARDS
   ========================================================= */

function updateKPIs(data) {
    const metrics =
        safeObject(data.metrics);

    const kpis =
        safeObject(data.kpis);

    const source = {
        ...data,
        ...metrics,
        ...kpis
    };

    const totalOrders =
        firstNumber(source, [
            "total_orders",
            "totalOrders",
            "orders_count",
            "order_count"
        ]);

    const totalSales =
        firstNumber(source, [
            "total_sales",
            "totalSales",
            "sales",
            "total_revenue",
            "revenue"
        ]);

    const averageOrder =
        firstNumber(source, [
            "average_order",
            "averageOrder",
            "avg_order",
            "avgOrder",
            "average_order_value"
        ]);

    const highestOrder =
        firstNumber(source, [
            "highest_order",
            "highestOrder",
            "max_order",
            "maximum_order"
        ]);

    setText("totalOrders", formatNumber(totalOrders));
    setText("totalSales", formatCurrency(totalSales));
    setText("averageOrder", formatCurrency(averageOrder));
    setText("highestOrder", formatCurrency(highestOrder));
}

function firstNumber(object, keys) {
    for (const key of keys) {
        if (
            object[key] !== undefined &&
            object[key] !== null &&
            object[key] !== ""
        ) {
            const number = Number(object[key]);

            if (Number.isFinite(number)) {
                return number;
            }
        }
    }

    return 0;
}

function setText(id, value) {
    const element = $(id);

    if (element) {
        element.textContent = value;
    }
}


/* =========================================================
   DATABASE COUNTS
   ========================================================= */

function updateCounts(data) {
    const counts =
        safeObject(data.counts);

    const source = {
        ...data,
        ...counts
    };

    setText(
        "customerCount",
        formatNumber(
            firstNumber(source, [
                "customer_count",
                "customers",
                "customerCount"
            ])
        )
    );

    setText(
        "employeeCount",
        formatNumber(
            firstNumber(source, [
                "employee_count",
                "employees",
                "employeeCount"
            ])
        )
    );

    setText(
        "productCount",
        formatNumber(
            firstNumber(source, [
                "product_count",
                "products",
                "productCount"
            ])
        )
    );

    setText(
        "inventoryCount",
        formatNumber(
            firstNumber(source, [
                "inventory_count",
                "inventory",
                "inventoryCount"
            ])
        )
    );

    setText(
        "projectCount",
        formatNumber(
            firstNumber(source, [
                "project_count",
                "projects",
                "projectCount"
            ])
        )
    );

    setText(
        "invoiceCount",
        formatNumber(
            firstNumber(source, [
                "invoice_count",
                "invoices",
                "invoiceCount"
            ])
        )
    );

    setText(
        "orderCount",
        formatNumber(
            firstNumber(source, [
                "order_count",
                "orders",
                "orderCount",
                "total_orders"
            ])
        )
    );
}


/* =========================================================
   CHART HELPERS
   ========================================================= */

function chartAvailable() {
    return typeof Chart !== "undefined";
}

function destroyChart(name) {
    if (charts[name]) {
        charts[name].destroy();
        charts[name] = null;
    }
}

function normalizeChartData(data) {
    if (!Array.isArray(data)) {
        return {
            labels: [],
            values: []
        };
    }

    const labels = [];
    const values = [];

    data.forEach(item => {
        if (item === null || item === undefined) {
            return;
        }

        if (typeof item !== "object") {
            labels.push(String(item));
            values.push(1);
            return;
        }

        const label =
            item.label ??
            item.name ??
            item.month ??
            item.status ??
            item.category ??
            item.product ??
            item.product_name ??
            item.project ??
            item.department ??
            "Unknown";

        const value =
            item.value ??
            item.total ??
            item.amount ??
            item.sales ??
            item.count ??
            item.quantity ??
            0;

        labels.push(String(label));
        values.push(Number(value) || 0);
    });

    return {
        labels,
        values
    };
}

function createChart(
    canvasId,
    chartName,
    type,
    data,
    options = {}
) {
    const canvas = $(canvasId);

    if (!canvas) {
        return;
    }

    destroyChart(chartName);

    if (!chartAvailable()) {
        showChartMessage(
            canvasId,
            "Chart.js is not loaded."
        );
        return;
    }

    const normalized =
        normalizeChartData(data);

    if (!normalized.labels.length) {
        showChartMessage(
            canvasId,
            "No data available"
        );
        return;
    }

    charts[chartName] = new Chart(
        canvas.getContext("2d"),
        {
            type: type,

            data: {
                labels: normalized.labels,

                datasets: [
                    {
                        label:
                            options.label || "Value",

                        data: normalized.values,

                        borderWidth: 2,

                        tension: 0.35,

                        fill:
                            type === "line",

                        backgroundColor:
                            [
                                "rgba(124, 92, 255, 0.75)",
                                "rgba(0, 212, 255, 0.75)",
                                "rgba(0, 255, 170, 0.75)",
                                "rgba(255, 170, 0, 0.75)",
                                "rgba(255, 80, 120, 0.75)",
                                "rgba(180, 80, 255, 0.75)"
                            ],

                        borderColor:
                            "rgba(124, 92, 255, 1)"
                    }
                ]
            },

            options: {
                responsive: true,

                maintainAspectRatio: false,

                plugins: {
                    legend: {
                        display:
                            options.legend !== false,

                        labels: {
                            color: "#ffffff"
                        }
                    }
                },

                scales:
                    type === "doughnut" ||
                    type === "pie"
                        ? {}
                        : {
                            x: {
                                ticks: {
                                    color: "#aeb6d1"
                                },

                                grid: {
                                    color:
                                        "rgba(255,255,255,0.05)"
                                }
                            },

                            y: {
                                beginAtZero: true,

                                ticks: {
                                    color: "#aeb6d1"
                                },

                                grid: {
                                    color:
                                        "rgba(255,255,255,0.05)"
                                }
                            }
                        }
            }
        }
    );
}

function showChartMessage(canvasId, message) {
    const canvas = $(canvasId);

    if (!canvas) {
        return;
    }

    const parent =
        canvas.parentElement;

    if (!parent) {
        return;
    }

    parent.innerHTML = `
        <div class="empty-state chart-empty">
            <p>${escapeHTML(message)}</p>
        </div>
    `;
}


/* =========================================================
   MONTHLY SALES
   ========================================================= */

function renderMonthlySales(data) {
    createChart(
        "monthlySalesChart",
        "monthlySales",
        "line",
        data,
        {
            label: "Monthly Sales"
        }
    );
}


/* =========================================================
   ORDER STATUS
   ========================================================= */

function renderOrderStatus(data) {
    createChart(
        "orderStatusChart",
        "orderStatus",
        "doughnut",
        data,
        {
            label: "Orders",
            legend: true
        }
    );
}


/* =========================================================
   PRODUCT PERFORMANCE
   ========================================================= */

function renderProductPerformance(data) {
    createChart(
        "productPerformanceChart",
        "productPerformance",
        "bar",
        data,
        {
            label: "Product Performance"
        }
    );
}


/* =========================================================
   PROJECT STATUS
   ========================================================= */

function renderProjectStatus(data) {
    createChart(
        "projectStatusChart",
        "projectStatus",
        "doughnut",
        data,
        {
            label: "Projects"
        }
    );
}


/* =========================================================
   INVENTORY CATEGORY
   ========================================================= */

function renderInventoryCategory(data) {
    createChart(
        "inventoryCategoryChart",
        "inventoryCategory",
        "bar",
        data,
        {
            label: "Inventory"
        }
    );
}


/* =========================================================
   INVOICE STATUS
   ========================================================= */

function renderInvoiceStatus(data) {
    createChart(
        "invoiceStatusChart",
        "invoiceStatus",
        "doughnut",
        data,
        {
            label: "Invoices"
        }
    );
}


/* =========================================================
   EMPLOYEE DEPARTMENT
   ========================================================= */

function renderEmployeeDepartment(data) {
    createChart(
        "employeeDepartmentChart",
        "employeeDepartment",
        "bar",
        data,
        {
            label: "Employees"
        }
    );
}


/* =========================================================
   RECENT ORDERS
   ========================================================= */

function renderRecentOrders(rows) {
    const body =
        $("recentOrdersBody");

    if (!body) {
        return;
    }

    rows = safeArray(rows);

    if (!rows.length) {
        body.innerHTML = `
            <tr>
                <td colspan="10">
                    <div class="empty-state">
                        No recent orders found.
                    </div>
                </td>
            </tr>
        `;

        return;
    }

    body.innerHTML =
        rows.slice(0, 10)
            .map(row => {

                const data =
                    safeObject(row);

                const id =
                    data.order_id ??
                    data.id ??
                    "-";

                const customer =
                    data.customer_name ??
                    data.customer ??
                    data.customer_id ??
                    "-";

                const product =
                    data.product_name ??
                    data.product ??
                    data.product_id ??
                    "-";

                const amount =
                    data.total_amount ??
                    data.amount ??
                    data.total ??
                    0;

                const status =
                    data.status ??
                    data.order_status ??
                    "Unknown";

                const date =
                    data.order_date ??
                    data.date ??
                    data.created_at ??
                    "-";

                return `
                    <tr>
                        <td>${escapeHTML(id)}</td>

                        <td>
                            ${escapeHTML(customer)}
                        </td>

                        <td>
                            ${escapeHTML(product)}
                        </td>

                        <td>
                            ${formatCurrency(amount)}
                        </td>

                        <td>
                            <span class="status-badge status-info">
                                ${escapeHTML(capitalize(status))}
                            </span>
                        </td>

                        <td>
                            ${escapeHTML(formatDate(date))}
                        </td>
                    </tr>
                `;
            })
            .join("");
}


/* =========================================================
   DASHBOARD RECORDS
   ========================================================= */

function renderDashboardRecords(data) {
    const container =
        $("dashboardTables");

    if (!container) {
        return;
    }

    const records =
        data.records ||
        data.tables ||
        data.database_records;

    if (!records) {
        showEmpty(
            "dashboardTables",
            "Database records will appear here."
        );

        return;
    }

    let html = "";

    if (Array.isArray(records)) {
        html = `
            <div class="table-wrapper">
                ${createGenericTable(records)}
            </div>
        `;
    } else if (
        typeof records === "object"
    ) {
        Object.entries(records)
            .forEach(([table, rows]) => {

                if (!Array.isArray(rows)) {
                    return;
                }

                html += `
                    <div class="table-section">

                        <div class="section-header">
                            <div>
                                <h3 class="section-title">
                                    ${escapeHTML(
                                        capitalize(table)
                                    )}
                                </h3>

                                <p class="section-subtitle">
                                    ${rows.length} record(s)
                                </p>
                            </div>

                            <button
                                class="btn btn-secondary"
                                onclick="openTable('${escapeHTML(table)}')"
                            >
                                View All
                            </button>
                        </div>

                        <div class="table-wrapper">
                            ${createGenericTable(
                                rows.slice(0, 5)
                            )}
                        </div>

                    </div>
                `;
            });
    }

    if (!html) {
        showEmpty(
            "dashboardTables",
            "No database records available."
        );

        return;
    }

    container.innerHTML = html;
}


/* =========================================================
   GENERIC TABLE
   ========================================================= */

function createGenericTable(rows) {
    rows = safeArray(rows);

    if (!rows.length) {
        return `
            <div class="empty-state">
                No records found.
            </div>
        `;
    }

    const columns =
        Object.keys(rows[0]);

    return `
        <table class="data-table">

            <thead>
                <tr>
                    ${columns
                        .map(column => `
                            <th>
                                ${escapeHTML(
                                    column
                                )}
                            </th>
                        `)
                        .join("")}
                </tr>
            </thead>

            <tbody>
                ${rows
                    .map(row => `
                        <tr>
                            ${columns
                                .map(column => `
                                    <td>
                                        ${escapeHTML(
                                            formatCell(
                                                row[column]
                                            )
                                        )}
                                    </td>
                                `)
                                .join("")}
                        </tr>
                    `)
                    .join("")}
            </tbody>

        </table>
    `;
}

function formatCell(value) {
    if (
        value === null ||
        value === undefined
    ) {
        return "-";
    }

    if (
        typeof value === "object"
    ) {
        return JSON.stringify(value);
    }

    return String(value);
}


/* =========================================================
   DATABASE TABLE OPEN
   ========================================================= */

async function openTable(tableName) {
    if (!tableName) {
        return;
    }

    currentTable = tableName;
    currentPage = 1;

    try {
        const result =
            await apiRequest(
                `/api/table/${encodeURIComponent(tableName)}`
            );

        currentRows =
            safeArray(
                result.rows ||
                result.data ||
                result.records
            );

        currentColumns =
            safeArray(result.columns);

        if (!currentColumns.length &&
            currentRows.length) {

            currentColumns =
                Object.keys(
                    currentRows[0]
                );
        }

        renderTableModal(
            tableName,
            currentRows,
            currentColumns
        );

    } catch (error) {
        console.error(
            "Unable to open table:",
            error
        );

        alert(
            "Unable to load table data: " +
            error.message
        );
    }
}


/* =========================================================
   TABLE MODAL
   ========================================================= */

function renderTableModal(
    tableName,
    rows,
    columns
) {
    const modal =
        $("tableModal");

    if (!modal) {
        return;
    }

    const title =
        modal.querySelector(
            ".modal-title"
        );

    if (title) {
        title.textContent =
            capitalize(tableName);
    }

    const body =
        modal.querySelector(
            ".modal-body"
        );

    if (!body) {
        return;
    }

    body.innerHTML = `
        <div class="table-toolbar">

            <div class="search-box">
                <input
                    type="text"
                    id="tableSearch"
                    class="table-search"
                    placeholder="Search records..."
                    oninput="searchCurrentTable(this.value)"
                >
            </div>

            <div class="table-controls">

                <span>
                    ${rows.length} record(s)
                </span>

                ${isAdmin() && tableName !== "customer"
                    ? `
                        <button
                            class="btn btn-primary btn-add"
                            onclick="showAddForm('${escapeHTML(tableName)}')"
                        >
                            + Add Record
                        </button>
                    `
                    : ""
                }

                ${isAdmin() && tableName === "customer"
                    ? `
                        <button
                            class="btn btn-primary btn-add"
                            onclick="showAddForm('${escapeHTML(tableName)}')"
                        >
                            + Add Customer
                        </button>
                    `
                    : ""
                }

            </div>

        </div>

        <div
            id="tableModalContent"
            class="table-wrapper"
        >
            ${buildModalTable(
                rows,
                columns
            )}
        </div>
    `;

    modal.classList.add("active");
    modal.style.display = "flex";
}


/* =========================================================
   BUILD MODAL TABLE
   ========================================================= */

function buildModalTable(
    rows,
    columns
) {
    if (!rows.length) {
        return `
            <div class="empty-state">
                <p>No records found.</p>
            </div>
        `;
    }

    const start =
        (currentPage - 1) *
        rowsPerPage;

    const end =
        start + rowsPerPage;

    const pageRows =
        rows.slice(start, end);

    let html = `
        <table class="data-table">

            <thead>
                <tr>
    `;

    columns.forEach(column => {
        html += `
            <th>
                ${escapeHTML(column)}
            </th>
        `;
    });

    if (isAdmin()) {
        html += `
            <th>Actions</th>
        `;
    }

    html += `
                </tr>
            </thead>

            <tbody>
    `;

    pageRows.forEach(row => {

        html += `
            <tr>
        `;

        columns.forEach(column => {

            html += `
                <td>
                    ${escapeHTML(
                        formatCell(
                            row[column]
                        )
                    )}
                </td>
            `;
        });

        if (isAdmin()) {

            const primaryKey =
                getPrimaryKeyValue(row);

            if (
                currentTable === "customer"
            ) {

                html += `
                    <td>
                        <button
                            class="action-btn action-delete"
                            onclick="deleteRecord(
                                '${escapeHTML(currentTable)}',
                                '${escapeHTML(primaryKey)}'
                            )"
                        >
                            Delete
                        </button>
                    </td>
                `;

            } else {

                html += `
                    <td>

                        <button
                            class="action-btn action-edit"
                            onclick='editRecord(
                                ${JSON.stringify(row)}
                            )'
                        >
                            Edit
                        </button>

                        <button
                            class="action-btn action-delete"
                            onclick="deleteRecord(
                                '${escapeHTML(currentTable)}',
                                '${escapeHTML(primaryKey)}'
                            )"
                        >
                            Delete
                        </button>

                    </td>
                `;
            }
        }

        html += `
            </tr>
        `;
    });

    html += `
            </tbody>

        </table>
    `;

    html += buildPagination(
        rows.length
    );

    return html;
}


/* =========================================================
   PRIMARY KEY
   ========================================================= */

function getPrimaryKeyValue(row) {
    const possibleKeys = [
        "id",
        "customer_id",
        "employee_id",
        "product_id",
        "inventory_id",
        "order_id",
        "project_id",
        "invoice_id"
    ];

    for (const key of possibleKeys) {
        if (
            row[key] !== undefined &&
            row[key] !== null
        ) {
            return row[key];
        }
    }

    const keys =
        Object.keys(row);

    return keys.length
        ? row[keys[0]]
        : "";
}


/* =========================================================
   PAGINATION
   ========================================================= */

function buildPagination(totalRows) {
    const totalPages =
        Math.ceil(
            totalRows / rowsPerPage
        );

    if (totalPages <= 1) {
        return "";
    }

    return `
        <div class="pagination">

            <button
                class="btn btn-secondary"
                onclick="changeTablePage(-1)"
                ${currentPage <= 1
                    ? "disabled"
                    : ""}
            >
                Previous
            </button>

            <span>
                Page ${currentPage}
                of ${totalPages}
            </span>

            <button
                class="btn btn-secondary"
                onclick="changeTablePage(1)"
                ${currentPage >= totalPages
                    ? "disabled"
                    : ""}
            >
                Next
            </button>

        </div>
    `;
}

function changeTablePage(direction) {
    const totalPages =
        Math.ceil(
            currentRows.length /
            rowsPerPage
        );

    currentPage += direction;

    if (currentPage < 1) {
        currentPage = 1;
    }

    if (currentPage > totalPages) {
        currentPage = totalPages;
    }

    const content =
        $("tableModalContent");

    if (content) {
        content.innerHTML =
            buildModalTable(
                currentRows,
                currentColumns
            );
    }
}


/* =========================================================
   SEARCH TABLE
   ========================================================= */

function searchCurrentTable(searchText) {
    const text =
        String(searchText || "")
            .toLowerCase()
            .trim();

    if (!text) {
        currentRows =
            window.originalTableRows ||
            currentRows;

        currentPage = 1;

        refreshModalTable();

        return;
    }

    if (!window.originalTableRows) {
        window.originalTableRows =
            [...currentRows];
    }

    currentRows =
        window.originalTableRows.filter(
            row => {

                return Object.values(row)
                    .some(value =>
                        String(value)
                            .toLowerCase()
                            .includes(text)
                    );
            }
        );

    currentPage = 1;

    refreshModalTable();
}

function refreshModalTable() {
    const content =
        $("tableModalContent");

    if (!content) {
        return;
    }

    content.innerHTML =
        buildModalTable(
            currentRows,
            currentColumns
        );
}


/* =========================================================
   CLOSE TABLE MODAL
   ========================================================= */

function closeTableModal() {
    const modal =
        $("tableModal");

    if (!modal) {
        return;
    }

    modal.classList.remove("active");
    modal.style.display = "none";

    window.originalTableRows = null;
}


/* =========================================================
   ADD RECORD
   ========================================================= */

async function showAddForm(tableName) {
    if (!isAdmin()) {
        alert("Admin access required.");
        return;
    }

    try {
        const result =
            await apiRequest(
                `/api/table/${encodeURIComponent(tableName)}/columns`
            );

        const columns =
            safeArray(
                result.columns ||
                result
            );

        openEditModal(
            tableName,
            {},
            columns,
            true
        );

    } catch (error) {
        console.error(error);

        alert(
            "Unable to get table columns: " +
            error.message
        );
    }
}


/* =========================================================
   EDIT RECORD
   ========================================================= */

function editRecord(row) {
    if (!isAdmin()) {
        alert("Admin access required.");
        return;
    }

    if (
        currentTable === "customer"
    ) {
        alert(
            "Customer records cannot be edited."
        );

        return;
    }

    const columns =
        Object.keys(row);

    openEditModal(
        currentTable,
        row,
        columns,
        false
    );
}


/* =========================================================
   EDIT MODAL
   ========================================================= */

function openEditModal(
    tableName,
    row,
    columns,
    isNew
) {
    const modal =
        $("editModal");

    if (!modal) {
        alert(
            "Edit modal is missing from HTML."
        );

        return;
    }

    const title =
        modal.querySelector(
            ".modal-title"
        );

    if (title) {
        title.textContent =
            isNew
                ? `Add ${capitalize(tableName)}`
                : `Edit ${capitalize(tableName)}`;
    }

    const body =
        modal.querySelector(
            ".modal-body"
        );

    if (!body) {
        return;
    }

    let html = `
        <form
            id="recordForm"
            onsubmit="saveRecord(event, '${escapeHTML(tableName)}', ${isNew})"
        >

            <div class="form-grid">
    `;

    columns.forEach(column => {

        const isPrimary =
            [
                "id",
                "customer_id",
                "employee_id",
                "product_id",
                "inventory_id",
                "order_id",
                "project_id",
                "invoice_id"
            ].includes(column);

        const value =
            row[column] ??
            "";

        html += `
            <div class="form-group">

                <label class="form-label">
                    ${escapeHTML(column)}
                </label>

                <input
                    class="form-input"
                    type="text"
                    name="${escapeHTML(column)}"
                    value="${escapeHTML(value)}"
                    ${!isNew && isPrimary
                        ? "readonly"
                        : ""}
                >

            </div>
        `;
    });

    html += `
            </div>

            <div class="form-actions">

                <button
                    type="button"
                    class="btn btn-secondary"
                    onclick="closeEditModal()"
                >
                    Cancel
                </button>

                <button
                    type="submit"
                    class="btn btn-primary"
                >
                    ${isNew
                        ? "Add Record"
                        : "Save Changes"}
                </button>

            </div>

        </form>
    `;

    body.innerHTML = html;

    modal.classList.add("active");
    modal.style.display = "flex";
}


/* =========================================================
   SAVE RECORD
   ========================================================= */

async function saveRecord(
    event,
    tableName,
    isNew
) {
    event.preventDefault();

    const form =
        $("recordForm");

    if (!form) {
        return;
    }

    const formData =
        new FormData(form);

    const data = {};

    formData.forEach(
        (value, key) => {
            data[key] =
                value === ""
                    ? null
                    : value;
        }
    );

    try {

        const url =
            `/api/table/${encodeURIComponent(tableName)}`;

        const result =
            await apiRequest(
                url,
                {
                    method:
                        isNew
                            ? "POST"
                            : "PUT",

                    body:
                        JSON.stringify(data)
                }
            );

        console.log(
            "Save result:",
            result
        );

        alert(
            isNew
                ? "Record added successfully."
                : "Record updated successfully."
        );

        closeEditModal();

        window.originalTableRows = null;

        await openTable(tableName);

        await loadDashboard();

    } catch (error) {

        console.error(
            "Save failed:",
            error
        );

        alert(
            "Unable to save record: " +
            error.message
        );
    }
}


/* =========================================================
   DELETE RECORD
   ========================================================= */

async function deleteRecord(
    tableName,
    primaryKey
) {
    if (!isAdmin()) {
        alert(
            "Admin access required."
        );

        return;
    }

    if (!confirm(
        "Are you sure you want to delete this record?"
    )) {
        return;
    }

    try {

        await apiRequest(
            `/api/table/${encodeURIComponent(tableName)}/${encodeURIComponent(primaryKey)}`,
            {
                method: "DELETE"
            }
        );

        alert(
            "Record deleted successfully."
        );

        window.originalTableRows = null;

        await openTable(tableName);

        await loadDashboard();

    } catch (error) {

        console.error(
            "Delete failed:",
            error
        );

        alert(
            "Unable to delete record: " +
            error.message
        );
    }
}


/* =========================================================
   CLOSE EDIT MODAL
   ========================================================= */

function closeEditModal() {
    const modal =
        $("editModal");

    if (!modal) {
        return;
    }

    modal.classList.remove("active");
    modal.style.display = "none";
}


/* =========================================================
   ROLE CHECK
   ========================================================= */

function getCurrentRole() {
    const body =
        document.body;

    if (
        body &&
        body.dataset &&
        body.dataset.role
    ) {
        return body.dataset.role
            .toLowerCase();
    }

    const roleElement =
        document.querySelector(
            ".role-badge"
        );

    if (roleElement) {
        return roleElement.textContent
            .trim()
            .toLowerCase();
    }

    const path =
        window.location.pathname
            .toLowerCase();

    if (path.includes("admin")) {
        return "admin";
    }

    return "user";
}

function isAdmin() {
    return getCurrentRole() === "admin";
}


/* =========================================================
   AI ANALYSIS
   ========================================================= */

async function loadAIAnalysis() {
    const container =
        $("aiAnalysisContent");

    if (!container) {
        return;
    }

    try {

        showLoading(
            "aiAnalysisContent",
            "Generating AI Business Analysis..."
        );

        const result =
            await apiRequest(
                "/api/ai-analysis"
            );

        aiData =
            safeObject(result);

        console.log(
            "AI analysis:",
            aiData
        );

        renderAIAnalysis(aiData);

    } catch (error) {

        console.error(
            "AI analysis error:",
            error
        );

        showError(
            "aiAnalysisContent",
            "AI analysis could not be loaded."
        );
    }
}


/* =========================================================
   AI ANALYSIS RENDER
   ========================================================= */

function renderAIAnalysis(data) {
    const container =
        $("aiAnalysisContent");

    if (!container) {
        return;
    }

    const score =
        firstNumber(
            data,
            [
                "score",
                "health_score",
                "business_health_score",
                "healthScore"
            ]
        );

    const summary =
        data.summary ||
        data.explanation ||
        data.overall_analysis ||
        "Business analysis is available below.";

    const strengths =
        safeArray(
            data.strengths
        );

    const risks =
        safeArray(
            data.risks
        );

    const recommendations =
        safeArray(
            data.recommendations
        );

    const metrics =
        safeObject(
            data.metrics
        );

    let html = `

        <div class="ai-analysis-view">

            <div class="health-card">

                <div>
                    <div class="ai-heading">
                        Business Health Score
                    </div>

                    <div class="health-score">
                        ${Math.round(score)}
                        <span>/100</span>
                    </div>
                </div>

                <div class="ai-score-ring">
                    ${Math.round(score)}%
                </div>

            </div>

            <div class="ai-panel">

                <h3 class="ai-title">
                    AI Business Summary
                </h3>

                <p class="ai-text">
                    ${escapeHTML(summary)}
                </p>

            </div>

    `;

    if (Object.keys(metrics).length) {

        html += `
            <div class="ai-metrics-grid">
        `;

        Object.entries(metrics)
            .slice(0, 8)
            .forEach(([key, value]) => {

                html += `
                    <div class="ai-card">

                        <div class="ai-title">
                            ${escapeHTML(
                                formatMetricName(key)
                            )}
                        </div>

                        <div class="ai-text">
                            ${escapeHTML(
                                formatCell(value)
                            )}
                        </div>

                    </div>
                `;
            });

        html += `
            </div>
        `;
    }

    html += `
        <div class="ai-panels">
    `;

    if (strengths.length) {

        html += `
            <div class="ai-panel">

                <h3 class="ai-title">
                    Strengths
                </h3>

                ${createAIList(
                    strengths,
                    "recommendation"
                )}

            </div>
        `;
    }

    if (risks.length) {

        html += `
            <div class="ai-panel">

                <h3 class="ai-title">
                    Risks / Issues
                </h3>

                ${createAIList(
                    risks,
                    "recommendation"
                )}

            </div>
        `;
    }

    html += `
        </div>
    `;

    if (recommendations.length) {

        html += `
            <div class="recommendation-panel">

                <h3 class="ai-title">
                    AI Recommendations
                </h3>

                ${createAIList(
                    recommendations,
                    "recommendation"
                )}

            </div>
        `;
    }

    html += `
        </div>
    `;

    container.innerHTML = html;

    renderAIScoreChart(score);
}

function formatMetricName(value) {
    return String(value)
        .replace(/_/g, " ")
        .replace(/([a-z])([A-Z])/g, "$1 $2")
        .replace(/\b\w/g, char =>
            char.toUpperCase()
        );
}

function createAIList(
    items,
    className
) {
    return items
        .map(item => {

            const text =
                typeof item === "object"
                    ? (
                        item.text ||
                        item.message ||
                        item.description ||
                        JSON.stringify(item)
                    )
                    : item;

            return `
                <div class="${className}">
                    ${escapeHTML(text)}
                </div>
            `;
        })
        .join("");
}


/* =========================================================
   AI SCORE CHART
   ========================================================= */

function renderAIScoreChart(score) {
    if (!exists("aiScoreChart")) {
        return;
    }

    destroyChart("aiScore");

    const canvas =
        $("aiScoreChart");

    if (!chartAvailable()) {
        return;
    }

    charts.aiScore =
        new Chart(
            canvas.getContext("2d"),
            {
                type: "doughnut",

                data: {
                    labels: [
                        "Health",
                        "Remaining"
                    ],

                    datasets: [
                        {
                            data: [
                                score,
                                Math.max(
                                    0,
                                    100 - score
                                )
                            ],

                            borderWidth: 0,

                            backgroundColor: [
                                "rgba(124, 92, 255, 0.85)",
                                "rgba(255,255,255,0.08)"
                            ]
                        }
                    ]
                },

                options: {
                    responsive: true,

                    maintainAspectRatio: false,

                    cutout: "72%",

                    plugins: {
                        legend: {
                            display: false
                        }
                    }
                }
            }
        );
}


/* =========================================================
   DASHBOARD ERROR
   ========================================================= */

function showDashboardError(message) {
    console.error(message);

    const possibleContainers = [
        "dashboardTables",
        "recentOrdersBody"
    ];

    possibleContainers.forEach(id => {

        const element = $(id);

        if (!element) {
            return;
        }

        if (id === "recentOrdersBody") {

            element.innerHTML = `
                <tr>
                    <td colspan="10">
                        <div class="error-state">
                            ${escapeHTML(message)}
                        </div>
                    </td>
                </tr>
            `;

        } else {

            element.innerHTML = `
                <div class="error-state">
                    <p>${escapeHTML(message)}</p>
                </div>
            `;
        }
    });
}


/* =========================================================
   DATABASE TEST
   ========================================================= */

async function testDatabase() {
    try {

        const result =
            await apiRequest(
                "/api/database-test"
            );

        console.log(
            "Database test:",
            result
        );

        return result;

    } catch (error) {

        console.error(
            "Database test failed:",
            error
        );

        return null;
    }
}


/* =========================================================
   LOAD TABLE LIST
   ========================================================= */

async function loadTables() {
    try {

        const result =
            await apiRequest(
                "/api/tables"
            );

        console.log(
            "Available tables:",
            result
        );

        return result;

    } catch (error) {

        console.error(
            "Could not load tables:",
            error
        );

        return null;
    }
}


/* =========================================================
   CURSOR GLOW EFFECT
   ========================================================= */

function initCursorGlow() {
    const glow =
        document.querySelector(
            ".cursor-glow"
        );

    if (!glow) {
        return;
    }

    document.addEventListener(
        "mousemove",
        event => {

            glow.style.left =
                event.clientX + "px";

            glow.style.top =
                event.clientY + "px";
        }
    );
}


/* =========================================================
   SCROLL REVEAL
   ========================================================= */

function initScrollReveal() {
    const elements =
        document.querySelectorAll(
            ".stat-card, .chart-card, .count-card, .recent-card, .ai-card, .ai-panel"
        );

    if (!elements.length) {
        return;
    }

    if (
        typeof IntersectionObserver ===
        "undefined"
    ) {
        elements.forEach(
            element =>
                element.classList.add(
                    "visible"
                )
        );

        return;
    }

    const observer =
        new IntersectionObserver(
            entries => {

                entries.forEach(entry => {

                    if (
                        entry.isIntersecting
                    ) {

                        entry.target.classList.add(
                            "visible"
                        );

                        observer.unobserve(
                            entry.target
                        );
                    }
                });
            },
            {
                threshold: 0.1
            }
        );

    elements.forEach(
        element =>
            observer.observe(element)
    );
}


/* =========================================================
   MOBILE SIDEBAR
   ========================================================= */

function initMobileMenu() {
    const button =
        document.querySelector(
            ".mobile-menu-btn"
        );

    const sidebar =
        document.querySelector(
            ".sidebar"
        );

    if (!button || !sidebar) {
        return;
    }

    button.addEventListener(
        "click",
        () => {
            sidebar.classList.toggle(
                "open"
            );
        }
    );
}


/* =========================================================
   MODAL CLICK OUTSIDE
   ========================================================= */

function initModalHandlers() {
    document.addEventListener(
        "click",
        event => {

            const tableModal =
                $("tableModal");

            const editModal =
                $("editModal");

            if (
                tableModal &&
                event.target === tableModal
            ) {
                closeTableModal();
            }

            if (
                editModal &&
                event.target === editModal
            ) {
                closeEditModal();
            }
        }
    );
}


/* =========================================================
   ESC KEY
   ========================================================= */

function initEscapeKey() {
    document.addEventListener(
        "keydown",
        event => {

            if (
                event.key !== "Escape"
            ) {
                return;
            }

            closeTableModal();
            closeEditModal();
        }
    );
}


/* =========================================================
   DATE CHIP
   ========================================================= */

function updateDateChip() {
    const element =
        document.querySelector(
            ".date-chip"
        );

    if (!element) {
        return;
    }

    const now =
        new Date();

    element.textContent =
        now.toLocaleDateString(
            "en-IN",
            {
                weekday: "short",
                day: "numeric",
                month: "short",
                year: "numeric"
            }
        );
}


/* =========================================================
   LOGOUT HANDLER
   ========================================================= */

function initLogout() {
    const logoutLinks =
        document.querySelectorAll(
            'a[href="/logout"], [data-logout]'
        );

    logoutLinks.forEach(link => {

        link.addEventListener(
            "click",
            () => {
                console.log(
                    "Logging out..."
                );
            }
        );
    });
}


/* =========================================================
   INITIALIZATION
   ========================================================= */

async function initializeDashboard() {

    console.log(
        "AI Business Management System starting..."
    );

    updateDateChip();

    initCursorGlow();

    initScrollReveal();

    initMobileMenu();

    initModalHandlers();

    initEscapeKey();

    initLogout();

    await loadDashboard();

    await loadAIAnalysis();

    console.log(
        "Dashboard initialization complete."
    );
}


/* =========================================================
   PAGE LOAD
   ========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        initializeDashboard()
            .catch(error => {

                console.error(
                    "Initialization error:",
                    error
                );
            });
    }
);


/* =========================================================
   GLOBAL FUNCTIONS
   ========================================================= */

window.loadDashboard =
    loadDashboard;

window.loadAIAnalysis =
    loadAIAnalysis;

window.openTable =
    openTable;

window.closeTableModal =
    closeTableModal;

window.showAddForm =
    showAddForm;

window.editRecord =
    editRecord;

window.saveRecord =
    saveRecord;

window.deleteRecord =
    deleteRecord;

window.closeEditModal =
    closeEditModal;

window.searchCurrentTable =
    searchCurrentTable;

window.changeTablePage =
    changeTablePage;

window.testDatabase =
    testDatabase;

window.loadTables =
    loadTables;