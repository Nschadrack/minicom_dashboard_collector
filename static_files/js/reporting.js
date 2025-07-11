document.addEventListener('DOMContentLoaded', function() {
    const periodFilter = document.getElementById('period-filter');
    const statusFilter = document.getElementById('status-filter');
    const loader = document.getElementById('loader');
    const contentArea = document.getElementById('report-content');
    const placeholder = `<div class="placeholder">Please select a reporting period to view data.</div>`;

    function buildPagination(data, type) {
        if (data.num_pages <= 1) return '';

        let html = '<div class="pagination">';
        if (data.has_previous) {
            html += `<a href="#" data-page="${data.previous_page_number}" data-type="${type}">&laquo; Prev</a>`;
        } else {
            html += `<span class="disabled">&laquo; Prev</span>`;
        }

        html += `<span class="current">Page ${data.number} of ${data.num_pages}</span>`;

        if (data.has_next) {
            html += `<a href="#" data-page="${data.next_page_number}" data-type="${type}">Next &raquo;</a>`;
        } else {
            html += `<span class="disabled">Next &raquo;</span>`;
        }
        html += '</div>';
        return html;
    }

    function renderNotReported(data, periodId) {
        let html = `
            <div class="stats-grid">
                <div class="stat-card"><h3>Total Industries To Report</h3><p>${data.stats.total}</p></div>
                <div class="stat-card"><h3>Pending Industries On Production Report</h3><p>${data.stats.pending_production}</p></div>
                <div class="stat-card"><h3>Pending Industries On Employment Report</h3><p>${data.stats.pending_employment}</p></div>
                <div class="stat-card"><h3>Fully Reported</h3><p>${data.stats.fully_compliant}</p></div>
            </div>
            <div class="hub-grid">
                <div class="report-section">
                    <h3>List of Industries To Report On Product Production</h3>
                    <div class="table-wrapper" id="production-list"></div>
                    <div id="production-pagination"></div>
                </div>
                <div class="report-section">
                    <h3>List of Industries To Report On Employment</h3>
                    <div class="table-wrapper" id="employment-list"></div>
                    <div id="employment-pagination"></div>
                </div>
            </div>`;
        contentArea.innerHTML = html;

        const prodList = document.getElementById('production-list');
        const prodPagination = document.getElementById('production-pagination');
        if (data.non_compliant_production.items.length > 0) {
            let tableHtml = `<table class="compliance-table">
                <thead><tr><th>#</th><th>TIN</th><th>Industry Name</th><th></th></tr></thead><tbody>`;
            data.non_compliant_production.items.forEach((company, index) => {
                tableHtml += `<tr>
                    <td>${index + 1}</td>
                    <td>${company.company__tin_number}</td>
                    <td>${company.company__name}</td>
                    <td><a href="/reporting/admin/industry/${company.id}/${periodId}/" class="action-link">View Details</a></td>
                </tr>`;
            });
            tableHtml += `</tbody></table>`;
            prodList.innerHTML = tableHtml;
            prodPagination.innerHTML = buildPagination(data.non_compliant_production, 'prod');
        } else {
            prodList.innerHTML = `<div class="placeholder">All industries have reported on production.</div>`;
        }

        const empList = document.getElementById('employment-list');
        const empPagination = document.getElementById('employment-pagination');
        if (data.non_compliant_employment.items.length > 0) {
            let tableHtml = `<table class="compliance-table">
                <thead><tr><th>#</th><th></th><th>TIN</th><th>Industry Name</th></tr></thead><tbody>`;
            data.non_compliant_employment.items.forEach((company, index) => {
                tableHtml += `<tr>
                    <td>${index + 1}</td>
                    <td><a href="/industry/industries/${company.id}" class="action-link">View industry</a></td>
                    <td>${company.company__tin_number}</td>
                    <td>${company.company__name}</td>
                </tr>`;
            });
            tableHtml += `</tbody></table>`;
            empList.innerHTML = tableHtml;
            empPagination.innerHTML = buildPagination(data.non_compliant_employment, 'emp');
        } else {
            empList.innerHTML = `<div class="placeholder">All industries have reported on employment.</div>`;
        }
    }

    function renderReported(data) {
        let html = `
            <div class="report-section">
                <h3>Fully Reported Industries</h3>
                <div class="table-wrapper" id="compliant-list"></div>
            </div>`;
        contentArea.innerHTML = html;

        const compliantList = document.getElementById('compliant-list');
        if (data.compliant_companies.length > 0) {
            let tableHtml = `<table class="compliance-table">
                <thead><tr><th>Industry Name</th><th>TIN</th></tr></thead><tbody>`;
            data.compliant_companies.forEach(company => {
                tableHtml += `<tr>
                    <td>${company.company__name}</td>
                    <td>${company.company__tin_number}</td>
                </tr>`;
            });
            tableHtml += `</tbody></table>`;
            compliantList.innerHTML = tableHtml;
        } else {
            compliantList.innerHTML = `<div class="placeholder">No industries are fully reported for this period.</div>`;
        }
    }

    function fetchData(prodPage = 1, empPage = 1) {
        const periodId = periodFilter.value;
        const status = statusFilter.value;

        if (!periodId) {
            contentArea.innerHTML = placeholder;
            return;
        }

        loader.style.display = 'flex';
        contentArea.innerHTML = '';

        const url = `/reporting/admin/?period_id=${periodId}&status=${status}&prod_page=${prodPage}&emp_page=${empPage}`;

        fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
            .then(response => response.json())
            .then(data => {
                if (data.error) throw new Error(data.error);
                
                if (status === 'not_reported') {
                    renderNotReported(data, periodId);
                } else {
                    renderReported(data);
                }
            })
            .catch(error => {
                console.error("Fetch Error:", error);
                contentArea.innerHTML = `<div class="placeholder" style="color: red;">Error loading data.</div>`;
            })
            .finally(() => {
                loader.style.display = 'none';
            });
    }

    periodFilter.addEventListener('change', () => fetchData());
    statusFilter.addEventListener('change', () => fetchData());

    contentArea.addEventListener('click', function(e) {
        if (e.target.tagName === 'A' && e.target.parentElement.classList.contains('pagination')) {
            e.preventDefault();
            const page = e.target.dataset.page;
            const type = e.target.dataset.type;
            
            const currentProdPage = document.querySelector('.pagination a[data-type="prod"]')?.dataset.page || 1;
            const currentEmpPage = document.querySelector('.pagination a[data-type="emp"]')?.dataset.page || 1;

            if (type === 'prod') {
                fetchData(page, currentEmpPage);
            } else if (type === 'emp') {
                fetchData(currentProdPage, page);
            }
        }
    });
});
