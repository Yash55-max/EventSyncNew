/**
 * Interactive Analytics Dashboard for Revolutionary Event Management Platform
 * Advanced data visualization, real-time updates, and AI-powered insights
 */

class AnalyticsDashboard {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.charts = {};
        this.currentData = null;
        this.filters = {
            timeRange: 'last_30d',
            categories: [],
            eventIds: []
        };
        this.updateInterval = null;
        
        this.init();
    }
    
    init() {
        this.createLayout();
        this.setupEventListeners();
        this.loadAnalyticsData();
        
        // Auto-refresh every 5 minutes
        this.updateInterval = setInterval(() => {
            this.refreshData();
        }, 300000);
    }
    
    createLayout() {
        const layout = `
            <div class="analytics-dashboard">
                <!-- Dashboard Header -->
                <div class="dashboard-header">
                    <h1>📊 Analytics Dashboard</h1>
                    <div class="dashboard-controls">
                        <select id="timeRangeFilter" class="filter-select">
                            <option value="last_24h">Last 24 Hours</option>
                            <option value="last_7d">Last 7 Days</option>
                            <option value="last_30d" selected>Last 30 Days</option>
                            <option value="last_90d">Last 90 Days</option>
                            <option value="last_year">Last Year</option>
                            <option value="all_time">All Time</option>
                        </select>
                        
                        <button id="refreshBtn" class="btn btn-refresh">
                            <i class="fas fa-sync-alt"></i> Refresh
                        </button>
                        
                        <button id="exportBtn" class="btn btn-export">
                            <i class="fas fa-download"></i> Export
                        </button>
                    </div>
                </div>
                
                <!-- Metrics Overview -->
                <div class="metrics-overview">
                    <div class="metric-card" id="attendanceCard">
                        <div class="metric-icon">📈</div>
                        <div class="metric-content">
                            <h3>Total Attendance</h3>
                            <div class="metric-value">-</div>
                            <div class="metric-trend">-</div>
                        </div>
                    </div>
                    
                    <div class="metric-card" id="engagementCard">
                        <div class="metric-icon">💡</div>
                        <div class="metric-content">
                            <h3>Engagement Score</h3>
                            <div class="metric-value">-</div>
                            <div class="metric-trend">-</div>
                        </div>
                    </div>
                    
                    <div class="metric-card" id="revenueCard">
                        <div class="metric-icon">💰</div>
                        <div class="metric-content">
                            <h3>Total Revenue</h3>
                            <div class="metric-value">-</div>
                            <div class="metric-trend">-</div>
                        </div>
                    </div>
                    
                    <div class="metric-card" id="satisfactionCard">
                        <div class="metric-icon">😊</div>
                        <div class="metric-content">
                            <h3>Satisfaction</h3>
                            <div class="metric-value">-</div>
                            <div class="metric-trend">-</div>
                        </div>
                    </div>
                    
                    <div class="metric-card" id="socialCard">
                        <div class="metric-icon">🤝</div>
                        <div class="metric-content">
                            <h3>Social Score</h3>
                            <div class="metric-value">-</div>
                            <div class="metric-trend">-</div>
                        </div>
                    </div>
                    
                    <div class="metric-card" id="performanceCard">
                        <div class="metric-icon">⭐</div>
                        <div class="metric-content">
                            <h3>Performance</h3>
                            <div class="metric-value">-</div>
                            <div class="metric-trend">-</div>
                        </div>
                    </div>
                </div>
                
                <!-- Charts Section -->
                <div class="charts-section">
                    <div class="chart-container">
                        <canvas id="attendanceChart"></canvas>
                    </div>
                    
                    <div class="chart-container">
                        <canvas id="revenueChart"></canvas>
                    </div>
                    
                    <div class="chart-container">
                        <canvas id="satisfactionChart"></canvas>
                    </div>
                    
                    <div class="chart-container">
                        <canvas id="performanceChart"></canvas>
                    </div>
                    
                    <div class="chart-container">
                        <canvas id="sustainabilityChart"></canvas>
                    </div>
                    
                    <div class="chart-container">
                        <canvas id="engagementTrendsChart"></canvas>
                    </div>
                </div>
                
                <!-- Insights and Recommendations -->
                <div class="insights-section">
                    <div class="insights-panel">
                        <h3>🔍 AI-Powered Insights</h3>
                        <div id="insightsList" class="insights-list">
                            <!-- Insights will be populated here -->
                        </div>
                    </div>
                    
                    <div class="recommendations-panel">
                        <h3>💡 Recommendations</h3>
                        <div id="recommendationsList" class="recommendations-list">
                            <!-- Recommendations will be populated here -->
                        </div>
                    </div>
                </div>
                
                <!-- Predictive Analytics -->
                <div class="predictive-section">
                    <div class="section-header">
                        <h3>🔮 Predictive Analytics</h3>
                        <button id="generatePredictionsBtn" class="btn btn-primary">
                            Generate Predictions
                        </button>
                    </div>
                    
                    <div class="predictions-content">
                        <div class="prediction-cards">
                            <div class="prediction-card">
                                <h4>📊 Attendance Forecast</h4>
                                <div id="attendanceForecast" class="forecast-content">
                                    <!-- Forecast data -->
                                </div>
                            </div>
                            
                            <div class="prediction-card">
                                <h4>💰 Revenue Forecast</h4>
                                <div id="revenueForecast" class="forecast-content">
                                    <!-- Forecast data -->
                                </div>
                            </div>
                            
                            <div class="prediction-card">
                                <h4>😊 Satisfaction Forecast</h4>
                                <div id="satisfactionForecast" class="forecast-content">
                                    <!-- Forecast data -->
                                </div>
                            </div>
                        </div>
                        
                        <div class="predictions-chart">
                            <canvas id="predictionsChart"></canvas>
                        </div>
                    </div>
                </div>
                
                <!-- Loading Overlay -->
                <div id="loadingOverlay" class="loading-overlay" style="display: none;">
                    <div class="loading-spinner">
                        <div class="spinner"></div>
                        <p>Loading analytics data...</p>
                    </div>
                </div>
            </div>
        `;
        
        this.container.innerHTML = layout;
        
        // Initialize Chart.js charts
        this.initCharts();
    }
    
    initCharts() {
        // Attendance Chart
        const attendanceCtx = document.getElementById('attendanceChart').getContext('2d');
        this.charts.attendance = new Chart(attendanceCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: []
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Attendance Trends'
                    },
                    legend: {
                        display: true,
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                },
                animation: {
                    duration: 1000
                }
            }
        });
        
        // Revenue Chart
        const revenueCtx = document.getElementById('revenueChart').getContext('2d');
        this.charts.revenue = new Chart(revenueCtx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: []
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Revenue by Category'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
        
        // Satisfaction Chart
        const satisfactionCtx = document.getElementById('satisfactionChart').getContext('2d');
        this.charts.satisfaction = new Chart(satisfactionCtx, {
            type: 'doughnut',
            data: {
                labels: [],
                datasets: []
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Satisfaction Rating Distribution'
                    },
                    legend: {
                        position: 'right'
                    }
                }
            }
        });
        
        // Performance Chart
        const performanceCtx = document.getElementById('performanceChart').getContext('2d');
        this.charts.performance = new Chart(performanceCtx, {
            type: 'radar',
            data: {
                labels: [],
                datasets: []
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Performance by Category'
                    }
                },
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
        
        // Sustainability Chart
        const sustainabilityCtx = document.getElementById('sustainabilityChart').getContext('2d');
        this.charts.sustainability = new Chart(sustainabilityCtx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: []
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Sustainability Score by Event Type'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
        
        // Engagement Trends Chart
        const engagementCtx = document.getElementById('engagementTrendsChart').getContext('2d');
        this.charts.engagement = new Chart(engagementCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: []
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Engagement Trends Over Time'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
        
        // Predictions Chart
        const predictionsCtx = document.getElementById('predictionsChart').getContext('2d');
        this.charts.predictions = new Chart(predictionsCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: []
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Future Event Predictions'
                    },
                    legend: {
                        display: true
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    setupEventListeners() {
        // Time range filter
        document.getElementById('timeRangeFilter').addEventListener('change', (e) => {
            this.filters.timeRange = e.target.value;
            this.loadAnalyticsData();
        });
        
        // Refresh button
        document.getElementById('refreshBtn').addEventListener('click', () => {
            this.refreshData();
        });
        
        // Export button
        document.getElementById('exportBtn').addEventListener('click', () => {
            this.exportData();
        });
        
        // Generate predictions button
        document.getElementById('generatePredictionsBtn').addEventListener('click', () => {
            this.generatePredictions();
        });
    }
    
    async loadAnalyticsData() {
        this.showLoading(true);
        
        try {
            const response = await fetch('/api/analytics/dashboard', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    time_range: this.filters.timeRange,
                    categories: this.filters.categories,
                    event_ids: this.filters.eventIds
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to load analytics data');
            }
            
            const data = await response.json();
            this.currentData = data;
            
            this.updateMetricsCards(data.metrics);
            this.updateCharts(data.charts);
            this.updateInsights(data.insights);
            this.updateRecommendations(data.recommendations);
            
        } catch (error) {
            console.error('Error loading analytics data:', error);
            this.showError('Failed to load analytics data. Please try again.');
        } finally {
            this.showLoading(false);
        }
    }
    
    updateMetricsCards(metrics) {
        const metricTypes = {
            'attendance': 'attendanceCard',
            'engagement': 'engagementCard',
            'revenue': 'revenueCard',
            'satisfaction': 'satisfactionCard',
            'social': 'socialCard',
            'performance': 'performanceCard'
        };
        
        metrics.forEach(metric => {
            const cardId = metricTypes[metric.metric_type];
            if (!cardId) return;
            
            const card = document.getElementById(cardId);
            if (!card) return;
            
            const valueEl = card.querySelector('.metric-value');
            const trendEl = card.querySelector('.metric-trend');
            
            // Format value based on metric type
            let formattedValue = this.formatMetricValue(metric.metric_type, metric.value);
            valueEl.textContent = formattedValue;
            
            // Update trend
            if (metric.change_percentage !== null) {
                const trendIcon = metric.trend === 'up' ? '📈' : 
                               metric.trend === 'down' ? '📉' : '➡️';
                const trendClass = metric.trend === 'up' ? 'trend-up' : 
                                 metric.trend === 'down' ? 'trend-down' : 'trend-stable';
                
                trendEl.innerHTML = `${trendIcon} ${Math.abs(metric.change_percentage).toFixed(1)}%`;
                trendEl.className = `metric-trend ${trendClass}`;
            } else {
                trendEl.textContent = 'No comparison data';
                trendEl.className = 'metric-trend trend-neutral';
            }
            
            // Add hover effect for additional metadata
            if (metric.metadata) {
                card.title = this.createMetadataTooltip(metric.metadata);
            }
        });
    }
    
    formatMetricValue(metricType, value) {
        switch (metricType) {
            case 'revenue':
                return '$' + value.toLocaleString();
            case 'attendance':
                return value.toLocaleString();
            case 'engagement':
            case 'satisfaction':
            case 'social':
            case 'performance':
            case 'sustainability':
                return value.toFixed(1) + '%';
            default:
                return value.toString();
        }
    }
    
    createMetadataTooltip(metadata) {
        return Object.entries(metadata)
            .map(([key, value]) => `${key}: ${value}`)
            .join('\\n');
    }
    
    updateCharts(chartConfigs) {
        chartConfigs.forEach(config => {
            const chartType = this.getChartTypeFromTitle(config.title);
            const chart = this.charts[chartType];
            
            if (chart) {
                chart.data = config.data;
                chart.update('active');
                
                // Add animations
                this.animateChart(chart);
            }
        });
    }
    
    getChartTypeFromTitle(title) {
        if (title.includes('Attendance')) return 'attendance';
        if (title.includes('Revenue')) return 'revenue';
        if (title.includes('Satisfaction')) return 'satisfaction';
        if (title.includes('Performance')) return 'performance';
        if (title.includes('Sustainability')) return 'sustainability';
        if (title.includes('Engagement')) return 'engagement';
        return 'attendance'; // default
    }
    
    animateChart(chart) {
        // Add custom animation effects
        chart.options.animation = {
            duration: 1500,
            easing: 'easeInOutQuart'
        };
        
        // Trigger animation
        chart.update('active');
    }
    
    updateInsights(insights) {
        const insightsList = document.getElementById('insightsList');
        
        if (insights.length === 0) {
            insightsList.innerHTML = '<p class="no-data">No insights available</p>';
            return;
        }
        
        const insightsHTML = insights.map(insight => `
            <div class="insight-item">
                <div class="insight-content">${insight}</div>
            </div>
        `).join('');
        
        insightsList.innerHTML = insightsHTML;
        
        // Add animations
        this.animateList(insightsList);
    }
    
    updateRecommendations(recommendations) {
        const recommendationsList = document.getElementById('recommendationsList');
        
        if (recommendations.length === 0) {
            recommendationsList.innerHTML = '<p class="no-data">No recommendations available</p>';
            return;
        }
        
        const recommendationsHTML = recommendations.map((recommendation, index) => `
            <div class="recommendation-item" data-priority="${index < 3 ? 'high' : 'medium'}">
                <div class="recommendation-content">${recommendation}</div>
                <div class="recommendation-actions">
                    <button class="btn btn-sm btn-primary" onclick="dashboard.implementRecommendation(${index})">
                        Implement
                    </button>
                    <button class="btn btn-sm btn-secondary" onclick="dashboard.dismissRecommendation(${index})">
                        Dismiss
                    </button>
                </div>
            </div>
        `).join('');
        
        recommendationsList.innerHTML = recommendationsHTML;
        
        // Add animations
        this.animateList(recommendationsList);
    }
    
    animateList(listElement) {
        const items = listElement.querySelectorAll('.insight-item, .recommendation-item');
        items.forEach((item, index) => {
            item.style.opacity = '0';
            item.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                item.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                item.style.opacity = '1';
                item.style.transform = 'translateY(0)';
            }, index * 100);
        });
    }
    
    async generatePredictions() {
        this.showLoading(true, 'Generating predictions...');
        
        try {
            const response = await fetch('/api/analytics/predictions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    time_horizon_days: 30
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to generate predictions');
            }
            
            const data = await response.json();
            this.updatePredictions(data);
            
        } catch (error) {
            console.error('Error generating predictions:', error);
            this.showError('Failed to generate predictions. Please try again.');
        } finally {
            this.showLoading(false);
        }
    }
    
    updatePredictions(predictionsData) {
        const { predictions, insights } = predictionsData;
        
        // Update forecast cards
        if (predictions.total_predicted_attendance) {
            document.getElementById('attendanceForecast').innerHTML = `
                <div class="forecast-value">${predictions.total_predicted_attendance.toLocaleString()}</div>
                <div class="forecast-label">Expected Attendees</div>
            `;
        }
        
        if (predictions.total_predicted_revenue) {
            document.getElementById('revenueForecast').innerHTML = `
                <div class="forecast-value">$${predictions.total_predicted_revenue.toLocaleString()}</div>
                <div class="forecast-label">Expected Revenue</div>
            `;
        }
        
        if (predictions.avg_predicted_satisfaction) {
            document.getElementById('satisfactionForecast').innerHTML = `
                <div class="forecast-value">${predictions.avg_predicted_satisfaction.toFixed(1)}/5</div>
                <div class="forecast-label">Expected Satisfaction</div>
            `;
        }
        
        // Update predictions chart
        if (predictions.attendance_forecast) {
            const forecastData = predictions.attendance_forecast;
            const labels = forecastData.map(f => f.event_title);
            const attendanceData = forecastData.map(f => f.predicted_attendance);
            const revenueData = forecastData.map(f => f.predicted_revenue);
            
            this.charts.predictions.data = {
                labels: labels,
                datasets: [
                    {
                        label: 'Predicted Attendance',
                        data: attendanceData,
                        borderColor: '#3498db',
                        backgroundColor: 'rgba(52, 152, 219, 0.1)',
                        yAxisID: 'y'
                    },
                    {
                        label: 'Predicted Revenue',
                        data: revenueData,
                        borderColor: '#e74c3c',
                        backgroundColor: 'rgba(231, 76, 60, 0.1)',
                        yAxisID: 'y1'
                    }
                ]
            };
            
            this.charts.predictions.options.scales = {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Attendance'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Revenue ($)'
                    },
                    grid: {
                        drawOnChartArea: false,
                    },
                }
            };
            
            this.charts.predictions.update();
        }
        
        // Show additional insights
        if (insights && insights.length > 0) {
            const insightsList = document.getElementById('insightsList');
            const currentInsights = insightsList.innerHTML;
            const newInsights = insights.map(insight => `
                <div class="insight-item predictive">
                    <div class="insight-content">${insight}</div>
                </div>
            `).join('');
            
            insightsList.innerHTML = currentInsights + newInsights;
        }
    }
    
    async refreshData() {
        await this.loadAnalyticsData();
        this.showNotification('Data refreshed successfully!', 'success');
    }
    
    exportData() {
        if (!this.currentData) {
            this.showError('No data to export');
            return;
        }
        
        // Create CSV data
        const csvData = this.convertToCSV(this.currentData);
        
        // Download CSV file
        const blob = new Blob([csvData], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `analytics-report-${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
        window.URL.revokeObjectURL(url);
        
        this.showNotification('Report exported successfully!', 'success');
    }
    
    convertToCSV(data) {
        const headers = ['Metric Type', 'Value', 'Change %', 'Trend'];
        const rows = data.metrics.map(metric => [
            metric.metric_type,
            metric.value,
            metric.change_percentage || 'N/A',
            metric.trend || 'N/A'
        ]);
        
        const csvContent = [headers, ...rows]
            .map(row => row.map(cell => `"${cell}"`).join(','))
            .join('\\n');
        
        return csvContent;
    }
    
    implementRecommendation(index) {
        // Placeholder for recommendation implementation
        this.showNotification('Recommendation implementation feature coming soon!', 'info');
    }
    
    dismissRecommendation(index) {
        const recommendationItems = document.querySelectorAll('.recommendation-item');
        if (recommendationItems[index]) {
            recommendationItems[index].style.opacity = '0.5';
            recommendationItems[index].style.textDecoration = 'line-through';
        }
    }
    
    showLoading(show, message = 'Loading analytics data...') {
        const overlay = document.getElementById('loadingOverlay');
        const messageEl = overlay.querySelector('p');
        
        if (show) {
            messageEl.textContent = message;
            overlay.style.display = 'flex';
        } else {
            overlay.style.display = 'none';
        }
    }
    
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
    }
    
    showError(message) {
        this.showNotification(message, 'error');
    }
    
    destroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
        
        // Destroy charts
        Object.values(this.charts).forEach(chart => {
            if (chart) {
                chart.destroy();
            }
        });
        
        this.charts = {};
        this.currentData = null;
    }
}

// Real-time Analytics Updates
class RealTimeAnalytics {
    constructor(dashboard) {
        this.dashboard = dashboard;
        this.socket = null;
        this.isConnected = false;
        
        this.init();
    }
    
    init() {
        if (typeof io !== 'undefined') {
            this.socket = io('/analytics');
            this.setupSocketListeners();
        }
    }
    
    setupSocketListeners() {
        this.socket.on('connect', () => {
            this.isConnected = true;
            console.log('Connected to real-time analytics');
        });
        
        this.socket.on('disconnect', () => {
            this.isConnected = false;
            console.log('Disconnected from real-time analytics');
        });
        
        this.socket.on('metric_update', (data) => {
            this.handleMetricUpdate(data);
        });
        
        this.socket.on('new_event_data', (data) => {
            this.handleNewEventData(data);
        });
        
        this.socket.on('insight_alert', (data) => {
            this.handleInsightAlert(data);
        });
    }
    
    handleMetricUpdate(data) {
        // Update specific metric in real-time
        const { metricType, value, trend } = data;
        
        // Find and update the metric card
        const metricCards = {
            'attendance': 'attendanceCard',
            'engagement': 'engagementCard',
            'revenue': 'revenueCard',
            'satisfaction': 'satisfactionCard',
            'social': 'socialCard',
            'performance': 'performanceCard'
        };
        
        const cardId = metricCards[metricType];
        if (cardId) {
            const card = document.getElementById(cardId);
            if (card) {
                const valueEl = card.querySelector('.metric-value');
                const trendEl = card.querySelector('.metric-trend');
                
                // Animate the value change
                this.animateValueChange(valueEl, value, metricType);
                
                if (trend) {
                    const trendIcon = trend === 'up' ? '📈' : trend === 'down' ? '📉' : '➡️';
                    trendEl.innerHTML = `${trendIcon} Live`;
                    trendEl.className = `metric-trend trend-${trend} live-update`;
                }
            }
        }
    }
    
    animateValueChange(element, newValue, metricType) {
        const currentValue = element.textContent;
        const formattedValue = this.dashboard.formatMetricValue(metricType, newValue);
        
        // Add pulse animation
        element.classList.add('value-updating');
        
        setTimeout(() => {
            element.textContent = formattedValue;
            element.classList.remove('value-updating');
            element.classList.add('value-updated');
            
            setTimeout(() => {
                element.classList.remove('value-updated');
            }, 1000);
        }, 200);
    }
    
    handleNewEventData(data) {
        // Refresh dashboard when new event data is available
        this.dashboard.showNotification('New event data available - refreshing...', 'info');
        setTimeout(() => {
            this.dashboard.refreshData();
        }, 1000);
    }
    
    handleInsightAlert(data) {
        const { insight, priority } = data;
        
        // Show high-priority insights as notifications
        if (priority === 'high') {
            this.dashboard.showNotification(`🚨 ${insight}`, 'warning');
        }
        
        // Add to insights list
        const insightsList = document.getElementById('insightsList');
        const newInsight = document.createElement('div');
        newInsight.className = `insight-item alert-insight priority-${priority}`;
        newInsight.innerHTML = `<div class="insight-content">${insight}</div>`;
        
        insightsList.insertBefore(newInsight, insightsList.firstChild);
        
        // Highlight new insight
        newInsight.style.backgroundColor = '#fff3cd';
        setTimeout(() => {
            newInsight.style.backgroundColor = '';
        }, 3000);
    }
    
    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
        }
    }
}

// Initialize dashboard when DOM is loaded
let dashboard;
let realTimeAnalytics;

document.addEventListener('DOMContentLoaded', function() {
    dashboard = new AnalyticsDashboard('dashboardContainer');
    realTimeAnalytics = new RealTimeAnalytics(dashboard);
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (dashboard) {
        dashboard.destroy();
    }
    if (realTimeAnalytics) {
        realTimeAnalytics.disconnect();
    }
});

// Export for global access
window.AnalyticsDashboard = AnalyticsDashboard;
window.dashboard = dashboard;