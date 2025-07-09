document.addEventListener('DOMContentLoaded', function () {
    const professionalColors = ['#1d4ed8', '#7c3aed', '#db2777', '#f59e0b', '#16a34a', '#0ea5e9', '#64748b', '#be185d'];
    let charts = {};

    // --- Tab Handling ---
    const tabs = document.querySelectorAll('[role="tab"]');
    tabs.forEach(tab => {
        tab.addEventListener('click', (e) => {
            document.querySelectorAll('[role="tabpanel"]').forEach(p => p.classList.add('hidden'));
            document.getElementById(e.target.getAttribute('aria-controls')).classList.remove('hidden');
            tabs.forEach(t => t.setAttribute('aria-selected', 'false'));
            e.target.setAttribute('aria-selected', 'true');
        });
    });
    document.getElementById('industry-tab').click();

    // --- Charting & Formatting Utilities ---
    const createOrUpdateChart = (id, type, data, options) => {
        const ctx = document.getElementById(id)?.getContext('2d');
        if (!ctx) return;
        if (charts[id]) charts[id].destroy();
        charts[id] = new Chart(ctx, { type, data, options });
    };
    const formatNumber = (num) => new Intl.NumberFormat('en-US').format(Math.round(num));
    const formatCurrency = (num, unit = 'M', divisor = 1e6) => `$${(num / divisor).toFixed(2)}${unit}`;

    // --- Data Fetching & Rendering ---
    const fetchData = async (url) => {
        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (error) { console.error("Could not fetch data:", error); return null; }
    };

    const populateFilters = (data) => {
        const populate = (elId, opts) => {
            const select = document.getElementById(elId);
            if(select && opts) opts.forEach(opt => select.innerHTML += `<option value="${opt}">${opt}</option>`);
        };
        populate('industry-sector-filter', data.filters.sectors);
        populate('industry-size-filter', data.filters.company_sizes);
        populate('park-filter', data.filters.parks);
        populate('trade-country-filter', data.filters.countries);
        populate('payment-company-filter', data.filters.companies);
        const currentYear = new Date().getFullYear();
        for (let i = 0; i < 10; i++) {
            const year = currentYear - i;
            ['industry-year-filter', 'trade-year-filter', 'payment-year-filter'].forEach(id => document.getElementById(id).innerHTML += `<option value="${year}">${year}</option>`);
        }
    };

    const renderDashboard = (data) => {
        // Industry
        document.getElementById('total-companies').textContent = formatNumber(data.industry.total_companies);
        document.getElementById('total-investment').textContent = formatCurrency(data.industry.total_investment);
        document.getElementById('avg-investment').textContent = formatCurrency(data.industry.avg_investment, 'K', 1e3);
        document.getElementById('total-employees').textContent = formatNumber(data.industry.total_employees);
        document.getElementById('companies-under-construction').textContent = formatNumber(data.industry.companies_under_construction);
        createOrUpdateChart('company-by-sector-chart', 'bar', { labels: Object.keys(data.industry.company_by_sector), datasets: [{ label: 'Companies', data: Object.values(data.industry.company_by_sector), backgroundColor: professionalColors[0] }] }, { responsive: true, maintainAspectRatio: false, plugins: { title: { display: true, text: 'Companies by Economic Sector' } } });
        createOrUpdateChart('operational-status-chart', 'pie', { labels: Object.keys(data.industry.operational_status), datasets: [{ data: Object.values(data.industry.operational_status), backgroundColor: professionalColors }] }, { responsive: true, maintainAspectRatio: false, plugins: { title: { display: true, text: 'Company Operational Status' } } });
        createOrUpdateChart('production-by-product-chart', 'doughnut', { labels: Object.keys(data.industry.production_by_product), datasets: [{ data: Object.values(data.industry.production_by_product), backgroundColor: professionalColors }] }, { responsive: true, maintainAspectRatio: false, plugins: { title: { display: true, text: 'Production Volume by Top 5 Products' } } });
        createOrUpdateChart('employment-by-gender-chart', 'bar', { labels: ['Male', 'Female'], datasets: [{ label: 'Employees', data: [data.industry.employment_by_gender.male, data.industry.employment_by_gender.female], backgroundColor: [professionalColors[0], professionalColors[2]] }] }, { responsive: true, maintainAspectRatio: false, indexAxis: 'y', plugins: { title: { display: true, text: 'Employment by Gender' } } });

        // Parks
        document.getElementById('total-parks').textContent = formatNumber(data.parks.total_parks);
        document.getElementById('total-land').textContent = formatNumber(data.parks.total_land);
        document.getElementById('total-allocated-plots').textContent = formatNumber(data.parks.total_allocated_plots);
        document.getElementById('total-available-plots').textContent = formatNumber(data.parks.total_available_plots);
        createOrUpdateChart('industries-by-park-chart', 'bar', { labels: Object.keys(data.parks.industries_by_park), datasets: [{ label: 'Industries', data: Object.values(data.parks.industries_by_park), backgroundColor: professionalColors[1] }] }, { responsive: true, maintainAspectRatio: false, plugins: { title: { display: true, text: 'Industries per Park' } } });
        createOrUpdateChart('park-occupancy-chart', 'bar', { labels: Object.keys(data.parks.park_occupancy), datasets: [{ label: 'Occupancy Rate (%)', data: Object.values(data.parks.park_occupancy), backgroundColor: professionalColors[4] }] }, { responsive: true, maintainAspectRatio: false, plugins: { title: { display: true, text: 'Park Land Occupancy Rate' } } });
        createOrUpdateChart('plot-status-by-park-chart', 'bar', { labels: Object.keys(data.parks.plot_status), datasets: [{ label: 'Allocated', data: Object.values(data.parks.plot_status).map(d => d.allocated), backgroundColor: professionalColors[5] }, { label: 'Available', data: Object.values(data.parks.plot_status).map(d => d.available), backgroundColor: professionalColors[6] }] }, { responsive: true, maintainAspectRatio: false, scales: { x: { stacked: true }, y: { stacked: true } }, plugins: { title: { display: true, text: 'Plot Status in Parks' } } });
        createOrUpdateChart('investment-by-park-chart', 'doughnut', { labels: Object.keys(data.parks.investment_by_park), datasets: [{ label: 'Investment (USD)', data: Object.values(data.parks.investment_by_park), backgroundColor: professionalColors }] }, { responsive: true, maintainAspectRatio: false, plugins: { title: { display: true, text: 'Investment Distribution by Park' } } });

        // Trade
        document.getElementById('formal-trade-value').textContent = formatCurrency(data.trade.formal_total);
        document.getElementById('informal-trade-value').textContent = formatCurrency(data.trade.informal_total);
        document.getElementById('trade-balance').textContent = formatCurrency(data.trade.trade_balance);
        document.getElementById('top-partner').textContent = data.trade.top_partner;
        createOrUpdateChart('trade-comparison-chart', 'bar', { labels: ['Formal Trade', 'Informal Trade'], datasets: [{ label: 'Trade Value (USD M)', data: [data.trade.formal_total / 1e6, data.trade.informal_total / 1e6], backgroundColor: [professionalColors[3], professionalColors[7]] }] }, { responsive: true, maintainAspectRatio: false, plugins: { title: { display: true, text: 'Formal vs Informal Trade' } } });
        createOrUpdateChart('trade-flow-chart', 'line', { labels: data.trade.trade_flow.labels, datasets: [{ label: 'Imports (USD M)', data: data.trade.trade_flow.imports.map(v => v / 1e6), borderColor: professionalColors[3], fill: false }, { label: 'Exports (USD M)', data: data.trade.trade_flow.exports.map(v => v / 1e6), borderColor: professionalColors[4], fill: false }] }, { responsive: true, maintainAspectRatio: false, plugins: { title: { display: true, text: 'Monthly Trade Flow' } } });
        
        // FIX: Changed 'horizontalBar' to 'bar' and added indexAxis: 'y'
        createOrUpdateChart('top-import-products-chart', 'bar', { labels: Object.keys(data.trade.top_imports), datasets: [{ label: 'Import Value (USD)', data: Object.values(data.trade.top_imports), backgroundColor: professionalColors[5] }] }, { responsive: true, maintainAspectRatio: false, indexAxis: 'y', plugins: { title: { display: true, text: 'Top 5 Imported Products' } } });
        createOrUpdateChart('top-export-products-chart', 'bar', { labels: Object.keys(data.trade.top_exports), datasets: [{ label: 'Export Value (USD)', data: Object.values(data.trade.top_exports), backgroundColor: professionalColors[6] }] }, { responsive: true, maintainAspectRatio: false, indexAxis: 'y', plugins: { title: { display: true, text: 'Top 5 Exported Products' } } });

        // Payments
        document.getElementById('total-paid').textContent = formatCurrency(data.payments.total_paid);
        document.getElementById('total-unpaid').textContent = formatCurrency(data.payments.total_unpaid);
        document.getElementById('total-overdue').textContent = formatCurrency(data.payments.total_overdue);
        document.getElementById('contracts-in-arrears').textContent = formatNumber(data.payments.contracts_in_arrears);
        createOrUpdateChart('payment-status-chart', 'pie', { labels: Object.keys(data.payments.payment_status_summary), datasets: [{ data: Object.values(data.payments.payment_status_summary), backgroundColor: professionalColors }] }, { responsive: true, maintainAspectRatio: false, plugins: { title: { display: true, text: 'Contract Payment Status' } } });
        createOrUpdateChart('payment-trends-chart', 'line', { labels: data.payments.payment_trends.labels, datasets: [{ label: 'Amount Paid (USD)', data: data.payments.payment_trends.data, borderColor: professionalColors[1], fill: false, tension: 0.1 }] }, { responsive: true, maintainAspectRatio: false, scales: { x: { type: 'time', time: { unit: 'month' } } }, plugins: { title: { display: true, text: 'Payment Trends Over Time' } } });
        
        // FIX: Changed 'horizontalBar' to 'bar' and added indexAxis: 'y'
        createOrUpdateChart('top-unpaid-companies-chart', 'bar', { labels: Object.keys(data.payments.top_unpaid_companies), datasets: [{ label: 'Unpaid Amount (USD)', data: Object.values(data.payments.top_unpaid_companies), backgroundColor: professionalColors[7] }] }, { responsive: true, maintainAspectRatio: false, indexAxis: 'y', plugins: { title: { display: true, text: 'Top 5 Companies by Unpaid Amount' } } });
        createOrUpdateChart('payment-modality-chart', 'doughnut', { labels: Object.keys(data.payments.payment_modality), datasets: [{ data: Object.values(data.payments.payment_modality), backgroundColor: professionalColors }] }, { responsive: true, maintainAspectRatio: false, plugins: { title: { display: true, text: 'Payment Modality Distribution' } } });

        // Reporting
        document.getElementById('reporting-total-industries').textContent = formatNumber(data.reporting.total_industries);
        document.getElementById('reporting-reported').textContent = formatNumber(data.reporting.reported_count);
        document.getElementById('reporting-not-reported').textContent = formatNumber(data.reporting.not_reported_count);
        document.getElementById('reporting-compliance-rate').textContent = `${data.reporting.compliance_rate.toFixed(1)}%`;
        createOrUpdateChart('reporting-compliance-chart', 'doughnut', { labels: ['Reported', 'Not Reported'], datasets: [{ data: [data.reporting.reported_count, data.reporting.not_reported_count], backgroundColor: [professionalColors[4], professionalColors[6]] }] }, { responsive: true, maintainAspectRatio: false, plugins: { title: { display: true, text: 'Reporting Compliance' } } });
        createOrUpdateChart('reported-production-by-sector-chart', 'bar', { labels: Object.keys(data.reporting.production_by_sector), datasets: [{ label: 'Production Volume', data: Object.values(data.reporting.production_by_sector), backgroundColor: professionalColors[5] }] }, { responsive: true, maintainAspectRatio: false, plugins: { title: { display: true, text: 'Reported Production by Sector' } } });

        // Admin
        document.getElementById('admin-total-users').textContent = formatNumber(data.admin.total_users);
        document.getElementById('admin-staff-users').textContent = formatNumber(data.admin.users_by_category['MINICOM STAFF'] || 0);
        document.getElementById('admin-company-users').textContent = formatNumber(data.admin.users_by_category['COMPANY'] || 0);
        document.getElementById('admin-active-roles').textContent = formatNumber(data.admin.total_roles);
        createOrUpdateChart('admin-users-by-category-chart', 'pie', { labels: Object.keys(data.admin.users_by_category), datasets: [{ data: Object.values(data.admin.users_by_category), backgroundColor: professionalColors }] }, { responsive: true, maintainAspectRatio: false, plugins: { title: { display: true, text: 'Users by Category' } } });
        createOrUpdateChart('admin-user-roles-chart', 'bar', { labels: Object.keys(data.admin.users_by_role), datasets: [{ label: 'User Count', data: Object.values(data.admin.users_by_role), backgroundColor: professionalColors[0] }] }, { responsive: true, maintainAspectRatio: false, plugins: { title: { display: true, text: 'User Distribution by Role' } } });
    };

    const loadDashboardData = async () => {
        const filters = {
            industry_year: document.getElementById('industry-year-filter').value,
            industry_sector: document.getElementById('industry-sector-filter').value,
            industry_size: document.getElementById('industry-size-filter').value,
            park: document.getElementById('park-filter').value,
            trade_year: document.getElementById('trade-year-filter').value,
            trade_country: document.getElementById('trade-country-filter').value,
            payment_year: document.getElementById('payment-year-filter').value,
            payment_company: document.getElementById('payment-company-filter').value,
            reporting_period: document.getElementById('reporting-period-filter').value,
        };
        const params = new URLSearchParams(filters).toString();
        const data = await fetchData(`/dashboard/api/dashboard-data/?${params}`);
        if (data) renderDashboard(data);
    };

    const initialLoad = async () => {
        const data = await fetchData('/dashboard/api/dashboard-data/');
        if (data) {
            populateFilters(data);
            renderDashboard(data);
        }
        document.querySelectorAll('.filter-select').forEach(el => el.addEventListener('change', loadDashboardData));
    };
    initialLoad();
});