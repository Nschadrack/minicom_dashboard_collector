// Initialize all charts when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Color palette for charts
    const colors = {
        blue: ['#3498db', '#2980b9', '#1f6aa5'],
        green: ['#2ecc71', '#27ae60', '#219653'],
        orange: ['#f39c12', '#e67e22', '#d35400'],
        red: ['#e74c3c', '#c0392b', '#a23526'],
        purple: ['#9b59b6', '#8e44ad', '#7d3c98']
    };

    // Exports by Product Category (Pie Chart)
    const exportsCtx = document.getElementById('exportsChart').getContext('2d');
    new Chart(exportsCtx, {
        type: 'pie',
        data: {
            labels: ['Electronics', 'Textiles', 'Chemicals', 'Machinery', 'Agriculture'],
            datasets: [{
                data: [35, 25, 15, 18, 7],
                backgroundColor: [
                    colors.blue[0],
                    colors.green[0],
                    colors.orange[0],
                    colors.purple[0],
                    colors.red[0]
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });

    // Imports vs Exports (Bar Chart)
    const tradeComparisonCtx = document.getElementById('tradeComparisonChart').getContext('2d');
    new Chart(tradeComparisonCtx, {
        type: 'bar',
        data: {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            datasets: [
                {
                    label: 'Imports',
                    data: [65, 59, 80, 81, 76, 75],
                    backgroundColor: colors.blue[0],
                    borderColor: colors.blue[1],
                    borderWidth: 1
                },
                {
                    label: 'Exports',
                    data: [55, 49, 70, 91, 66, 85],
                    backgroundColor: colors.green[0],
                    borderColor: colors.green[1],
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });

    // Re-Export Distribution (Doughnut Chart)
    const reExportCtx = document.getElementById('reExportChart').getContext('2d');
    new Chart(reExportCtx, {
        type: 'doughnut',
        data: {
            labels: ['Regional', 'Continental', 'Intercontinental'],
            datasets: [{
                data: [55, 30, 15],
                backgroundColor: [
                    colors.purple[0],
                    colors.orange[0],
                    colors.blue[0]
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });

    // Trade Value by Border Point (Bar Chart)
    const borderTradeCtx = document.getElementById('borderTradeChart').getContext('2d');
    new Chart(borderTradeCtx, {
        type: 'bar',
        data: {
            labels: ['Point A', 'Point B', 'Point C', 'Point D', 'Point E'],
            datasets: [{
                label: 'Trade Value (Million USD)',
                data: [12.5, 19.3, 15.2, 8.7, 10.4],
                backgroundColor: colors.orange[0],
                borderColor: colors.orange[1],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });

    // Monthly Trade Volume (Line Chart)
    const tradeVolumeCtx = document.getElementById('tradeVolumeChart').getContext('2d');
    new Chart(tradeVolumeCtx, {
        type: 'line',
        data: {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul'],
            datasets: [{
                label: 'Monthly Volume',
                data: [65, 59, 80, 81, 76, 75, 85],
                fill: false,
                backgroundColor: colors.red[0],
                borderColor: colors.red[1],
                tension: 0.1,
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: false
                }
            }
        }
    });

    // Commodity Distribution (Pie Chart)
    const commodityCtx = document.getElementById('commodityChart').getContext('2d');
    new Chart(commodityCtx, {
        type: 'pie',
        data: {
            labels: ['Consumer Goods', 'Raw Materials', 'Electronics', 'Food', 'Other'],
            datasets: [{
                data: [40, 25, 15, 12, 8],
                backgroundColor: [
                    colors.green[0],
                    colors.blue[0],
                    colors.orange[0],
                    colors.purple[0],
                    colors.red[0]
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });

    // Zone Occupancy Rate (Bar Chart)
    const occupancyCtx = document.getElementById('occupancyChart').getContext('2d');
    new Chart(occupancyCtx, {
        type: 'bar',
        data: {
            labels: ['Zone 1', 'Zone 2', 'Zone 3', 'Zone 4', 'Zone 5'],
            datasets: [{
                label: 'Occupancy Rate (%)',
                data: [85, 92, 78, 65, 88],
                backgroundColor: colors.blue[0],
                borderColor: colors.blue[1],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });

    // Investment by Sector (Doughnut Chart)
    const investmentCtx = document.getElementById('investmentChart').getContext('2d');
    new Chart(investmentCtx, {
        type: 'doughnut',
        data: {
            labels: ['Manufacturing', 'Logistics', 'Tech', 'Energy', 'Services'],
            datasets: [{
                data: [45, 20, 15, 12, 8],
                backgroundColor: [
                    colors.purple[0],
                    colors.blue[0],
                    colors.green[0],
                    colors.orange[0],
                    colors.red[0]
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });

    // Employment Distribution (Pie Chart)
    const employmentCtx = document.getElementById('employmentChart').getContext('2d');
    new Chart(employmentCtx, {
        type: 'pie',
        data: {
            labels: ['Full-time', 'Part-time', 'Contract', 'Temporary', 'Interns'],
            datasets: [{
                data: [65, 15, 10, 7, 3],
                backgroundColor: [
                    colors.green[0],
                    colors.blue[0],
                    colors.orange[0],
                    colors.purple[0],
                    colors.red[0]
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
});