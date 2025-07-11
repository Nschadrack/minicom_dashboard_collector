document.addEventListener('DOMContentLoaded', function () {
    const professionalColors = ['rgb(58, 148, 218)', 'rgba(9, 117, 175, 0.622)', '#07a8d4', '#f59e0b', '#97c1ff', '#0ea5e9', '#64748b', '#be185d'];
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
    
    const formatCurrency = (num, unit = 'M', divisor = 1e6) => {
        // Calculate the value after division.
        const value = num / divisor;

        // Use Intl.NumberFormat to format the number with commas and 2 decimal places.
        // 'en-US' locale is used here to ensure commas are used as thousand separators.
        const formattedValue = new Intl.NumberFormat('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        }).format(value);

        return `$${formattedValue}${unit}`;
    };

    const formatRwfCurrency = (num, unit = 'M', divisor = 1e6) => {
        // Calculate the value after division.
        const value = num / divisor;

        // Use Intl.NumberFormat to format the number with commas and 2 decimal places.
        const formattedValue = new Intl.NumberFormat('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        }).format(value);

        return `${formattedValue}${unit} Rwf`;
    };

    const roundValue = (num, figure=1e6, places=1e2) => {
        return Math.round((num / figure) * places) / places
    };

    function cleanFormalProduct(product) {
        // Trim whitespace from the beginning and end of the line.
        let cleanedLine = product.trim();

        // Rule 1: Use a regular expression to remove any leading commas,
        // hyphens, or whitespace characters.
        // ^      - matches the beginning of the string
        // [,\s-] - matches any character in the set: comma, whitespace, or hyphen
        // +      - matches one or more of the preceding characters
        cleanedLine = cleanedLine.replace(/^[,\s-]+/, '');

        // Rule 2: Split the line on '(' and take the first part.
        // This effectively removes the parenthesis and anything after it.
        cleanedLine = cleanedLine.split('(')[0];
        return cleanedLine;
    };


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
        document.getElementById('total-companies').textContent = formatNumber(data.industry.total_industries);
        document.getElementById('total-companies-locations').textContent = formatNumber(data.industry.total_industries_locations);
        document.getElementById('total-investment').textContent = formatCurrency(data.industry.total_investment);
        document.getElementById('avg-investment').textContent = formatCurrency(data.industry.avg_investment, 'K', 1e3);

        createOrUpdateChart('company-by-sector-chart', 'bar', { labels: Object.keys(data.industry.company_by_sector), 
                                                                datasets: [{ label: 'Industries', data: Object.values(data.industry.company_by_sector), 
                                                                backgroundColor: Object.values(data.industry.company_by_sector).map((v, index) => professionalColors[index])}]}, 
                                                                { responsive: true, maintainAspectRatio: false, plugins: { title: { display: true, text: 'Industries by Economic Sector' } } });
        
        createOrUpdateChart('company-by-size-chart', 'bar', { labels: Object.keys(data.industry.industry_size), 
                                                                datasets: [{ label: 'Industries', data: Object.values(data.industry.industry_size), 
                                                                backgroundColor: Object.values(data.industry.industry_size).map((v, index) => professionalColors[index])}]}, 
                                                                { responsive: true, maintainAspectRatio: false, plugins: { title: { display: true, text: 'Industries by Size' } } });

        createOrUpdateChart('operational-status-chart', 'pie', { labels: Object.keys(data.industry.operational_status), 
                                                                datasets: [{ data: Object.values(data.industry.operational_status), 
                                                                backgroundColor: Object.values(data.industry.operational_status).map((v, index) => professionalColors[index + 2])}]}, 
                                                                { responsive: true, maintainAspectRatio: false, plugins: { title: { display: true, text: 'Industries By Operational Status' } } });
        createOrUpdateChart('electricity-tarrif-chart', 'doughnut', { labels: Object.keys(data.industry.electricity_tariff).map(v => v == "true"? "YES": "NO"), 
                                                                datasets: [{ data: Object.values(data.industry.electricity_tariff), 
                                                                backgroundColor: Object.values(data.industry.operational_status).map((v, index) => professionalColors[index + 2])}]}, 
                                                                { responsive: true, maintainAspectRatio: false, plugins: { title: { display: true, text: 'Industries Benefited Electricity Tariff' } } });                                                        

        createOrUpdateChart('location-industry-chart', 'doughnut', { labels: Object.keys(data.industry.location).map(v => v == "true"? "In The Park": "Not In The Park"), 
                                                                    datasets: [{ data: Object.values(data.industry.location), 
                                                                        backgroundColor: [professionalColors[2], professionalColors[3]] }] }, 
                                                                        { responsive: true, maintainAspectRatio: false, plugins: { title: { display: true, text: 'Industries By Location' } } });

        // Parks
        document.getElementById('total-parks').textContent = formatNumber(data.parks.total_parks);
        document.getElementById('total-parks-land').textContent = formatNumber(data.parks.total_parks_land);
        document.getElementById('total-leasable-land').textContent = formatNumber(data.parks.total_parks_leasable_land);
        document.getElementById('total-unleasable-land').textContent = formatNumber(data.parks.total_parks_unleasable_land);
        document.getElementById('total-leased-land').textContent = formatNumber(data.parks.total_leased_land);
        document.getElementById('total-allocated-plots').textContent = formatNumber(data.parks.total_allocated_plots);
        document.getElementById('total-available-plots').textContent = formatNumber(data.parks.total_available_plots);

        createOrUpdateChart('industries-by-park-chart', 'bar', { labels: Object.keys(data.parks.industries_by_park), 
                                                                datasets: [{ label: 'Industries', data: Object.values(data.parks.industries_by_park), 
                                                                backgroundColor: professionalColors[1] }] }, 
                                                                { responsive: true, maintainAspectRatio: false, plugins: { title: { display: true, text: 'Industries per Park' } } });
        
        // 2. Define the data for the pie chart.
        const unavailableParkOccupancy = data.parks.total_leased_land;
        const availableParkOccupancy = data.parks.total_unleased_land;
        let pieChartData = {
            labels: ['Used', 'Unused'],
            datasets: [{
                label: 'Occupancy Rate (%)', // This label appears in tooltips
                data: [
                    roundValue(unavailableParkOccupancy),
                    roundValue(availableParkOccupancy)
                ],
                backgroundColor: [
                    professionalColors[3],
                    professionalColors[0]
                ],
                borderColor: '#ffffff', // Add a border to slices for better separation
                borderWidth: 1
            }]
        };

        // 3. Define the options for the pie chart, including the plugin to show percentages.
        let pieChartOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Industrial Parks Occupancy Rate (%)', // New title
                    font: {
                        size: 12
                    }
                },
                tooltip: {
                    // Customize tooltips to show the value and percentage
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed;
                            const sum = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = roundValue((value * 100 / sum), 1e0) + '%';
                            return `${percentage})`;
                        }
                    }
                },
                datalabels: {
                    // This plugin configuration displays the percentage on each slice
                    formatter: (value, ctx) => {
                        const sum = ctx.chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
                        const percentage = roundValue((value * 100 / sum), 1e0) + '%';
                        // Only show the label if the percentage is significant
                        return (value / sum) > 0.05 ? percentage : '';
                    },
                    color: '#fff',
                    font: {
                        weight: 'bold',
                        size: 12
                    }
                }
            }
        };

        createOrUpdateChart('park-occupancy-chart', 'doughnut', pieChartData, pieChartOptions);

        createOrUpdateChart('plot-status-by-park-chart', 'bar', { labels: Object.keys(data.parks.plot_status), 
                                                                datasets: [{ label: 'Allocated', data: Object.values(data.parks.plot_status).map(d => d.allocated), 
                                                                backgroundColor: professionalColors[5] }, { label: 'Available', data: Object.values(data.parks.plot_status).map(d => d.available), backgroundColor: professionalColors[6] }] }, 
                                                                { responsive: true, maintainAspectRatio: false, scales: { x: { stacked: true }, y: { stacked: true } }, plugins: { title: { display: true, text: 'Plot Status in Parks' } } });

        pieChartData = {
            labels: Object.keys(data.parks.construction_status),
            datasets: [{
                label: 'Construction status rate (%)', // This label appears in tooltips
                data: Object.values(data.parks.construction_status),
                backgroundColor: Object.values(data.parks.construction_status).map((v, index) => professionalColors[index + 1]),
                borderColor: '#ffffff', // Add a border to slices for better separation
                borderWidth: 1
            }]
        };

        // 3. Define the options for the pie chart, including the plugin to show percentages.
        pieChartOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Allocated Plots Construction status rate (%)', // New title
                    font: {
                        size: 12
                    }
                },
                tooltip: {
                    // Customize tooltips to show the value and percentage
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed;
                            const sum = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = roundValue((value * 100 / sum), 1e0) + '%';
                            return `${percentage})`;
                        }
                    }
                },
                datalabels: {
                    // This plugin configuration displays the percentage on each slice
                    formatter: (value, ctx) => {
                        const sum = ctx.chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
                        const percentage = roundValue((value * 100 / sum), 1e0) + '%';
                        // Only show the label if the percentage is significant
                        return (value / sum) > 0.05 ? percentage : '';
                    },
                    color: '#fff',
                    font: {
                        weight: 'bold',
                        size: 12
                    }
                }
            }
        };
                                                       
        createOrUpdateChart('construction-status-park-chart', 'doughnut', pieChartData, pieChartOptions);

        createOrUpdateChart('industry-economic-sector-park-chart', 'bar', { labels: Object.keys(data.parks.industry_economic_sector), 
                                                                datasets: [{ label: 'Industries', data: Object.values(data.parks.industry_economic_sector), 
                                                                backgroundColor: Object.values(data.parks.industry_economic_sector).map((v, index) => professionalColors[index]) }]}, 
                                                                { responsive: true, maintainAspectRatio: false, plugins: { title: { display: true, text: 'Industries by Economic Sector' } } });
        
        createOrUpdateChart('industry-size-by-park-chart', 'bar', { labels: Object.keys(data.parks.industry_size), 
                                                                datasets: [{ label: 'Industries', data: Object.values(data.parks.industry_size), 
                                                                backgroundColor: Object.values(data.parks.industry_size).map((v, index) => professionalColors[index]) }]}, 
                                                                { responsive: true, maintainAspectRatio: false, plugins: { title: { display: true, text: 'Industries by Size' } } });

        //Trade
        document.getElementById('formal-export-trade-value').textContent = formatCurrency(data.trade.formal_exports_val);
        document.getElementById('formal-export-trade-value-rw').textContent = formatRwfCurrency(data.trade.formal_exports_val_rw, 'B', 1e9);
        document.getElementById('formal-re-export-trade-value').textContent = formatCurrency(data.trade.formal_re_exports_val);
        document.getElementById('formal-re-export-trade-value-rw').textContent = formatRwfCurrency(data.trade.formal_re_exports_val_rw, 'B', 1e9);
        document.getElementById('formal-import-trade-value').textContent = formatCurrency(data.trade.formal_imports_val);
        document.getElementById('formal-import-trade-value-rw').textContent = formatRwfCurrency(data.trade.formal_imports_val_rw, 'B', 1e9);
        
        document.getElementById('informal-export-trade-value').textContent = formatCurrency(data.trade.icbt_exports_val);
        document.getElementById('informal-export-trade-value-rw').textContent = formatRwfCurrency(data.trade.icbt_exports_val_rw, 'B', 1e9);
        document.getElementById('informal-import-trade-value').textContent = formatCurrency(data.trade.icbt_imports_val);
        document.getElementById('informal-import-trade-value-rw').textContent = formatRwfCurrency(data.trade.icbt_imports_val_rw, 'B', 1e9);

        document.getElementById('formal-trade-balance').textContent = formatCurrency(data.trade.formal_trade_balance);
        document.getElementById('formal-trade-balance-rw').textContent = formatRwfCurrency(data.trade.formal_trade_balance_rw, 'B', 1e9);
        document.getElementById('icbt-trade-balance').textContent = formatCurrency(data.trade.icbt_balance);
        document.getElementById('icbt-trade-balance-rw').textContent = formatRwfCurrency(data.trade.icbt_balance_rw, 'B', 1e9);

        if(data.trade.formal_trade_balance < 0){
            document.getElementById('formal-trade-balance').style.color = "red";
            document.getElementById('formal-trade-balance-rw').style.color = "red";
        }
        
        // Formal Trade Pie Chart

        // 2. Define the data for the pie chart.
        let importValue = data.trade.formal_imports_val;
        let exportValue = data.trade.formal_exports_val;
        pieChartData = {
            labels: ['ICBT Import', 'ICBT Export'],
            datasets: [{
                label: 'Trade Value', // This label appears in tooltips
                data: [
                    roundValue(importValue),
                    roundValue(exportValue)
                ],
                backgroundColor: [
                    professionalColors[0], // Color for Imports
                    professionalColors[3]  // Color for Exports
                ],
                borderColor: '#ffffff', // Add a border to slices for better separation
                borderWidth: 1
            }]
        };

        // 3. Define the options for the pie chart, including the plugin to show percentages.
        pieChartOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Formal Trade (Import vs. Export)', // New title
                    font: {
                        size: 12
                    }
                },
                tooltip: {
                    // Customize tooltips to show the value and percentage
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed;
                            const sum = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = roundValue((value * 100 / sum), 1e0) + '%';
                            return `$${value}M (${percentage})`;
                        }
                    }
                },
                datalabels: {
                    // This plugin configuration displays the percentage on each slice
                    formatter: (value, ctx) => {
                        const sum = ctx.chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
                        const percentage = roundValue((value * 100 / sum), 1e0) + '%';
                        // Only show the label if the percentage is significant
                        return (value / sum) > 0.05 ? percentage : '';
                    },
                    color: '#fff',
                    font: {
                        weight: 'bold',
                        size: 12
                    }
                }
            }
        };

        createOrUpdateChart('formal-trade-comparison-pie-chart', 'doughnut', pieChartData, pieChartOptions); 
        
        importValue = data.trade.icbt_imports_val;
        exportValue = data.trade.icbt_exports_val;

        // 2. Define the data for the pie chart.
        pieChartData = {
            labels: ['ICBT Import', 'ICBT Export'],
            datasets: [{
                label: 'Trade Value', // This label appears in tooltips
                data: [
                    roundValue(importValue),
                    roundValue(exportValue)
                ],
                backgroundColor: [
                    professionalColors[0], // Color for Imports
                    professionalColors[3]  // Color for Exports
                ],
                borderColor: '#ffffff', // Add a border to slices for better separation
                borderWidth: 1
            }]
        };

        // 3. Define the options for the pie chart, including the plugin to show percentages.
        pieChartOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'ICBT (Import vs. Export)', // New title
                    font: {
                        size: 12
                    }
                },
                tooltip: {
                    // Customize tooltips to show the value and percentage
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed;
                            const sum = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = roundValue((value * 100 / sum), 1e0) + '%';
                            return `$${value}M (${percentage})`;
                        }
                    }
                },
                datalabels: {
                    // This plugin configuration displays the percentage on each slice
                    formatter: (value, ctx) => {
                        const sum = ctx.chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
                        const percentage = roundValue((value * 100 / sum), 1e0) + '%';
                        // Only show the label if the percentage is significant
                        return (value / sum) > 0.05 ? percentage : '';
                    },
                    color: '#fff',
                    font: {
                        weight: 'bold',
                        size: 12
                    }
                }
            }
        };

        createOrUpdateChart('icbt-comparison-pie-chart', 'doughnut', pieChartData, pieChartOptions); 

        createOrUpdateChart('formal-trade-flow-chart', 'line', { labels: data.trade.trade_flow.labels, 
                                                        datasets: [{ label: 'Imports (USD M)', data: data.trade.trade_flow.imports.map(v => roundValue(v)), borderColor: professionalColors[0], fill: false }, 
                                                                    { label: 'Exports (USD M)', data: data.trade.trade_flow.exports.map(v => roundValue(v)), borderColor: professionalColors[3], fill: false },
                                                                    { label: 'Re-Exports (USD M)', data: data.trade.trade_flow.re_exports.map(v => roundValue(v)), borderColor: professionalColors[7], fill: false }]}, 
                                                                    { responsive: true, maintainAspectRatio: false, plugins: { title: { display: true, text: 'Monthly Formal Trade Trends' } } });

        createOrUpdateChart('icbt-flow-chart', 'line', { labels: data.trade.icbt_flow.labels, 
                                                        datasets: [{ label: 'Imports (USD M)', data: data.trade.icbt_flow.imports.map(v => roundValue(v)), borderColor: professionalColors[0], fill: false }, 
                                                                    { label: 'Exports (USD M)', data: data.trade.icbt_flow.exports.map(v => roundValue(v)), borderColor: professionalColors[3], fill: false }]},
                                                                    { responsive: true, maintainAspectRatio: false, plugins: { title: { display: true, text: 'Monthly ICBT Trends' } } });
        
        // Top Partners
        createOrUpdateChart('top-import-formal-partners-chart', 'bar', { labels: Object.keys(data.trade.formal_top_imports), 
                                                                        datasets: [{ label: 'Import Value (USD M)', data: Object.values(data.trade.formal_top_imports).map(v => roundValue(v)), 
                                                                        backgroundColor: professionalColors[0] }] }, { responsive: true, maintainAspectRatio: false, indexAxis: 'y', plugins: { title: { display: true, text: 'Top Partners - Formal Trade Imports' } } });

        createOrUpdateChart('top-export-formal-partners-chart', 'bar', { labels: Object.keys(data.trade.formal_top_exports), 
                                                                        datasets: [{ label: 'Export Value (USD M)', data: Object.values(data.trade.formal_top_exports).map(v => roundValue(v)), 
                                                                        backgroundColor: professionalColors[3] }] }, { responsive: true, maintainAspectRatio: false, indexAxis: 'y', plugins: { title: { display: true, text: 'Top Partners - Formal Trade Exports' } } });  
        
        createOrUpdateChart('top-re-export-formal-partners-chart', 'bar', { labels: Object.keys(data.trade.formal_top_re_exports), 
                                                                        datasets: [{ label: 'Re-Export Value (USD M)', data: Object.values(data.trade.formal_top_re_exports).map(v => roundValue(v)), 
                                                                        backgroundColor: professionalColors[2] }] }, { responsive: true, maintainAspectRatio: false, indexAxis: 'y', plugins: { title: { display: true, text: 'Top Partners - Formal Trade Re-Exports' } } });      

        
        // Top Products
        createOrUpdateChart('top-import-formal-products-chart', 'bar', { labels: Object.keys(data.trade.formal_top_product_imports).map(p => cleanFormalProduct(p)), 
                                                                        datasets: [{ label: 'Import Value (USD M)', data: Object.values(data.trade.formal_top_product_imports).map(v => roundValue(v)), 
                                                                        backgroundColor: professionalColors[0] }] }, { responsive: true, maintainAspectRatio: false, indexAxis: 'y', plugins: { title: { display: true, text: 'Top Products - Formal Trade Imports' } } });

        createOrUpdateChart('top-export-formal-products-chart', 'bar', { labels: Object.keys(data.trade.formal_top_product_exports).map(p => cleanFormalProduct(p)), 
                                                                        datasets: [{ label: 'Export Value (USD M)', data: Object.values(data.trade.formal_top_product_exports).map(v => roundValue(v)), 
                                                                        backgroundColor: professionalColors[3] }] }, { responsive: true, maintainAspectRatio: false, indexAxis: 'y', plugins: { title: { display: true, text: 'Top Products - Formal Trade Exports' } } });  
        
        createOrUpdateChart('top-re-export-formal-products-chart', 'bar', { labels: Object.keys(data.trade.formal_top_re_product_exports).map(p => cleanFormalProduct(p)), 
                                                                        datasets: [{ label: 'Re-Export Value (USD M)', data: Object.values(data.trade.formal_top_re_product_exports).map(v => roundValue(v)), 
                                                                        backgroundColor: professionalColors[2] }] }, { responsive: true, maintainAspectRatio: false, indexAxis: 'y', plugins: { title: { display: true, text: 'Top Products - Formal Trade Re-Exports' } } });  
                                                                        
        createOrUpdateChart('top-export-icbt-products-chart', 'bar', { labels: Object.keys(data.trade.icbt_top_product_imports), 
                                                                        datasets: [{ label:  'Import Value (USD M)', data: Object.values(data.trade.icbt_top_product_imports).map(v => roundValue(v)), 
                                                                        backgroundColor: professionalColors[0] }] }, { responsive: true, maintainAspectRatio: false, indexAxis: 'y', plugins: { title: { display: true, text: 'Top Products - ICBT Imports' } } });  
                                                                        
        createOrUpdateChart('top-import-icbt-products-chart', 'bar', { labels: Object.keys(data.trade.icbt_top_product_exports), 
                                                                        datasets: [{ label:  'Export Value (USD M)', data: Object.values(data.trade.icbt_top_product_exports).map(v => roundValue(v)), 
                                                                        backgroundColor: professionalColors[3] }] }, { responsive: true, maintainAspectRatio: false, indexAxis: 'y', plugins: { title: { display: true, text: 'Top Products - ICBT Exports' } } });                                                                  

        // ICBT
        const allPartners = [...new Set([
            ...Object.keys(data.trade.icbt_top_imports), 
            ...Object.keys(data.trade.icbt_top_exports)
        ])]; 
        
        // Create data arrays for imports and exports that match the order of `allPartners`.
        // If a country doesn't have an import/export value, use 0.
        const importData = allPartners.map(country => roundValue(data.trade.icbt_top_imports[country] || 0));
        const exportData = allPartners.map(country => roundValue(data.trade.icbt_top_exports[country] || 0));

        // Define the new combined chart configuration.
        const combinedChartData = {
            labels: allPartners,
            datasets: [
                {
                    label: 'Import Value (USD M)',
                    data: importData,
                    backgroundColor: professionalColors[0] // Original import color
                },
                {
                    label: 'Export Value (USD M)',
                    data: exportData,
                    backgroundColor: professionalColors[3] // Original export color
                }
            ]
        };

        const combinedChartOptions = {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'x', // Keep it as a horizontal bar chart
            scales: {
                x: {
                    stacked: false, // Ensure bars are side-by-side (grouped), not stacked
                    title: {
                        display: true,
                        text: 'Value (USD M)'
                    }
                },
                y: {
                    stacked: false
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'ICBT Imports vs. Exports by Partner Country' // New, combined title
                }
            }
        };
        createOrUpdateChart('icbt-trade-comparison-chart', 'bar', combinedChartData, combinedChartOptions);
       

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