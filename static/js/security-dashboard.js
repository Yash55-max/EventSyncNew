/**
 * Security Dashboard JavaScript
 * Provides interactive functionality for the comprehensive security management system
 */

class SecurityDashboard {
    constructor() {
        this.currentTab = 'overview';
        this.auditLogs = [];
        this.currentUser = null;
        this.twoFactorSetup = {
            secret: null,
            qrCode: null,
            backupCodes: []
        };
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadInitialData();
        this.setupWebSocket();
        this.initializePermissionMatrix();
    }

    setupEventListeners() {
        // Tab navigation
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });

        // 2FA Setup
        const setup2FABtn = document.getElementById('setup-2fa');
        if (setup2FABtn) {
            setup2FABtn.addEventListener('click', () => this.initiate2FASetup());
        }

        const verify2FABtn = document.getElementById('verify-2fa');
        if (verify2FABtn) {
            verify2FABtn.addEventListener('click', () => this.verify2FASetup());
        }

        // GDPR Actions
        document.getElementById('export-user-data')?.addEventListener('click', () => this.exportUserData());
        document.getElementById('anonymize-data')?.addEventListener('click', () => this.anonymizeData());
        document.getElementById('delete-expired')?.addEventListener('click', () => this.deleteExpiredData());

        // Audit Log Controls
        document.getElementById('export-logs')?.addEventListener('click', () => this.exportAuditLogs());
        document.getElementById('date-range')?.addEventListener('change', () => this.filterAuditLogs());
        document.getElementById('event-type')?.addEventListener('change', () => this.filterAuditLogs());
        document.getElementById('success-filter')?.addEventListener('change', () => this.filterAuditLogs());

        // Settings
        document.getElementById('save-settings')?.addEventListener('click', () => this.saveSettings());
        document.getElementById('reset-settings')?.addEventListener('click', () => this.resetSettings());

        // Modal controls
        document.querySelectorAll('.modal-close').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.closeModal(e.target.closest('.modal').id);
            });
        });

        // Real-time security monitoring
        this.startSecurityMonitoring();
    }

    switchTab(tabName) {
        // Update active tab
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // Update tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(tabName).classList.add('active');

        this.currentTab = tabName;
        this.loadTabData(tabName);
    }

    async loadTabData(tabName) {
        switch (tabName) {
            case 'overview':
                await this.loadOverviewData();
                break;
            case 'rbac':
                await this.loadRBACData();
                break;
            case 'audit':
                await this.loadAuditLogs();
                break;
            case 'privacy':
                await this.loadPrivacyData();
                break;
            case 'settings':
                await this.loadSecuritySettings();
                break;
        }
    }

    async loadInitialData() {
        try {
            const response = await fetch('/api/security/dashboard-data');
            const data = await response.json();
            
            if (data.success) {
                this.updateOverviewMetrics(data.dashboard_data);
                this.updateSecurityScore(data.security_score);
            }
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
            this.showNotification('Failed to load dashboard data', 'error');
        }
    }

    async loadOverviewData() {
        try {
            const response = await fetch('/api/security/overview');
            const data = await response.json();
            
            if (data.success) {
                this.updateOverviewMetrics(data.metrics);
                this.updateSecurityEvents(data.recent_events);
            }
        } catch (error) {
            console.error('Failed to load overview data:', error);
        }
    }

    updateOverviewMetrics(metrics) {
        // Update metric cards with real data
        document.querySelector('.metric-card:nth-child(1) h3').textContent = metrics.total_events_24h || '0';
        document.querySelector('.metric-card:nth-child(2) h3').textContent = metrics.failed_attempts_24h || '0';
        document.querySelector('.metric-card:nth-child(3) h3').textContent = metrics.blocked_ips || '0';
        document.querySelector('.metric-card:nth-child(4) h3').textContent = metrics.active_data_processing_records || '0';
    }

    updateSecurityScore(score) {
        const scoreElement = document.querySelector('.status-indicator .score');
        const indicatorElement = document.querySelector('.status-indicator');
        
        if (scoreElement) {
            scoreElement.textContent = `${score}%`;
            
            // Update indicator class based on score
            indicatorElement.className = 'status-indicator';
            if (score > 80) {
                indicatorElement.classList.add('secure');
            } else if (score > 60) {
                indicatorElement.classList.add('warning');
            } else {
                indicatorElement.classList.add('danger');
            }
        }
    }

    updateSecurityEvents(events) {
        const eventsList = document.querySelector('.events-list');
        if (!eventsList || !events) return;

        eventsList.innerHTML = events.map(event => `
            <div class="event-item ${event.success ? 'success' : 'failed'}">
                <div class="event-icon">
                    <i class="fas fa-${event.success ? 'check-circle' : 'times-circle'}"></i>
                </div>
                <div class="event-details">
                    <div class="event-title">${event.action}</div>
                    <div class="event-meta">
                        <span class="timestamp">${new Date(event.timestamp).toLocaleString()}</span>
                        <span class="ip">IP: ${event.ip_address}</span>
                    </div>
                </div>
            </div>
        `).join('');
    }

    async loadRBACData() {
        try {
            const response = await fetch('/api/security/rbac');
            const data = await response.json();
            
            if (data.success) {
                this.updatePermissionMatrix(data.permissions);
                this.updateRoleCards(data.roles);
            }
        } catch (error) {
            console.error('Failed to load RBAC data:', error);
        }
    }

    initializePermissionMatrix() {
        const permissions = [
            'read_events', 'create_events', 'edit_events', 'delete_events',
            'manage_users', 'view_analytics', 'manage_payments', 'system_admin',
            'moderate_content', 'export_data', 'manage_integrations'
        ];

        const roles = ['guest', 'attendee', 'organizer', 'moderator', 'admin', 'super_admin'];
        
        const matrixBody = document.getElementById('permission-matrix-body');
        if (!matrixBody) return;

        matrixBody.innerHTML = permissions.map(permission => {
            const formattedPermission = permission.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
            
            return `
                <tr>
                    <td>${formattedPermission}</td>
                    ${roles.map(role => `
                        <td>
                            <i class="fas fa-${this.hasPermission(role, permission) ? 'check text-success' : 'times text-danger'}"></i>
                        </td>
                    `).join('')}
                </tr>
            `;
        }).join('');
    }

    hasPermission(role, permission) {
        const rolePermissions = {
            guest: [],
            attendee: ['read_events'],
            organizer: ['read_events', 'create_events', 'edit_events', 'view_analytics'],
            moderator: ['read_events', 'create_events', 'edit_events', 'moderate_content', 'view_analytics'],
            admin: ['read_events', 'create_events', 'edit_events', 'delete_events', 'manage_users', 'view_analytics', 'manage_payments', 'moderate_content', 'export_data', 'manage_integrations'],
            super_admin: ['read_events', 'create_events', 'edit_events', 'delete_events', 'manage_users', 'view_analytics', 'manage_payments', 'system_admin', 'moderate_content', 'export_data', 'manage_integrations']
        };

        return rolePermissions[role]?.includes(permission) || false;
    }

    async loadAuditLogs() {
        try {
            const params = new URLSearchParams({
                date_range: document.getElementById('date-range')?.value || '24h',
                event_type: document.getElementById('event-type')?.value || 'all',
                success_filter: document.getElementById('success-filter')?.value || 'all'
            });

            const response = await fetch(`/api/security/audit-logs?${params}`);
            const data = await response.json();
            
            if (data.success) {
                this.auditLogs = data.logs;
                this.updateAuditLogsTable(data.logs);
            }
        } catch (error) {
            console.error('Failed to load audit logs:', error);
        }
    }

    updateAuditLogsTable(logs) {
        const tableBody = document.getElementById('audit-logs-body');
        if (!tableBody) return;

        tableBody.innerHTML = logs.map(log => `
            <tr>
                <td>${new Date(log.timestamp).toLocaleString()}</td>
                <td>${log.user_id ? `User ${log.user_id}` : 'System'}</td>
                <td>${log.action}</td>
                <td>${log.resource}</td>
                <td>${log.ip_address}</td>
                <td>
                    <span class="badge ${log.success ? 'badge-success' : 'badge-danger'}">
                        ${log.success ? 'Success' : 'Failed'}
                    </span>
                </td>
                <td>
                    <button class="btn btn-sm" onclick="securityDashboard.showLogDetails(${JSON.stringify(log).replace(/"/g, '&quot;')})">
                        <i class="fas fa-info-circle"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }

    showLogDetails(log) {
        const details = JSON.stringify(log.details, null, 2);
        alert(`Log Details:\n\n${details}`);
    }

    filterAuditLogs() {
        this.loadAuditLogs();
    }

    async exportAuditLogs() {
        try {
            const params = new URLSearchParams({
                date_range: document.getElementById('date-range')?.value || '24h',
                event_type: document.getElementById('event-type')?.value || 'all',
                success_filter: document.getElementById('success-filter')?.value || 'all'
            });

            const response = await fetch(`/api/security/export-audit-logs?${params}`);
            const blob = await response.blob();
            
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `security-audit-logs-${new Date().toISOString().split('T')[0]}.csv`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            this.showNotification('Audit logs exported successfully', 'success');
        } catch (error) {
            console.error('Failed to export audit logs:', error);
            this.showNotification('Failed to export audit logs', 'error');
        }
    }

    async loadPrivacyData() {
        try {
            const response = await fetch('/api/security/privacy-data');
            const data = await response.json();
            
            if (data.success) {
                this.updatePrivacyStats(data.stats);
            }
        } catch (error) {
            console.error('Failed to load privacy data:', error);
        }
    }

    updatePrivacyStats(stats) {
        document.querySelector('.stat-item:nth-child(1) .stat-number').textContent = stats.total_records || '0';
        document.querySelector('.stat-item:nth-child(2) .stat-number').textContent = stats.expiring_soon || '0';
        document.querySelector('.stat-item:nth-child(3) .stat-number').textContent = stats.anonymized || '0';
    }

    async exportUserData() {
        const userId = prompt('Enter User ID to export data for:');
        if (!userId) return;

        try {
            const response = await fetch(`/api/security/export-user-data/${userId}`, {
                method: 'POST'
            });
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `user-data-${userId}-${new Date().toISOString().split('T')[0]}.json`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                this.showNotification('User data exported successfully', 'success');
            } else {
                throw new Error('Export failed');
            }
        } catch (error) {
            console.error('Failed to export user data:', error);
            this.showNotification('Failed to export user data', 'error');
        }
    }

    async anonymizeData() {
        const userId = prompt('Enter User ID to anonymize data for:');
        if (!userId) return;

        if (!confirm('This action cannot be undone. Are you sure you want to anonymize this user\'s data?')) {
            return;
        }

        try {
            const response = await fetch(`/api/security/anonymize-user-data/${userId}`, {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('User data anonymized successfully', 'success');
                this.loadPrivacyData(); // Refresh stats
            } else {
                throw new Error(data.message || 'Anonymization failed');
            }
        } catch (error) {
            console.error('Failed to anonymize user data:', error);
            this.showNotification('Failed to anonymize user data', 'error');
        }
    }

    async deleteExpiredData() {
        if (!confirm('This action will permanently delete all expired data. Are you sure?')) {
            return;
        }

        try {
            const response = await fetch('/api/security/delete-expired-data', {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification(`Deleted ${data.deleted_count} expired records`, 'success');
                this.loadPrivacyData(); // Refresh stats
            } else {
                throw new Error(data.message || 'Deletion failed');
            }
        } catch (error) {
            console.error('Failed to delete expired data:', error);
            this.showNotification('Failed to delete expired data', 'error');
        }
    }

    async initiate2FASetup() {
        try {
            const response = await fetch('/api/security/setup-2fa', {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.twoFactorSetup.secret = data.secret;
                this.twoFactorSetup.qrCode = data.qr_code;
                this.twoFactorSetup.backupCodes = data.backup_codes;
                
                document.getElementById('qr-code').src = data.qr_code;
                document.getElementById('manual-code').textContent = data.secret;
                
                // Display backup codes
                const backupCodesList = document.getElementById('backup-codes-list');
                backupCodesList.innerHTML = data.backup_codes.map(code => 
                    `<div class="backup-code">${code}</div>`
                ).join('');
                
                this.showModal('twofa-modal');
            } else {
                throw new Error(data.message || '2FA setup failed');
            }
        } catch (error) {
            console.error('Failed to setup 2FA:', error);
            this.showNotification('Failed to setup 2FA', 'error');
        }
    }

    async verify2FASetup() {
        const verificationCode = document.getElementById('verification-code').value;
        
        if (!verificationCode || verificationCode.length !== 6) {
            this.showNotification('Please enter a valid 6-digit code', 'error');
            return;
        }

        try {
            const response = await fetch('/api/security/verify-2fa', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    secret: this.twoFactorSetup.secret,
                    token: verificationCode
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('2FA enabled successfully!', 'success');
                this.closeModal('twofa-modal');
                
                // Update UI to show 2FA is enabled
                document.getElementById('enforce-2fa').checked = true;
            } else {
                throw new Error(data.message || 'Verification failed');
            }
        } catch (error) {
            console.error('Failed to verify 2FA:', error);
            this.showNotification('Invalid verification code', 'error');
        }
    }

    async loadSecuritySettings() {
        try {
            const response = await fetch('/api/security/settings');
            const data = await response.json();
            
            if (data.success) {
                this.populateSettings(data.settings);
            }
        } catch (error) {
            console.error('Failed to load security settings:', error);
        }
    }

    populateSettings(settings) {
        // Populate form fields with current settings
        document.getElementById('enforce-2fa').checked = settings.enforce_2fa || false;
        document.getElementById('session-timeout').value = settings.session_timeout || 30;
        document.getElementById('strict-ip').checked = settings.strict_ip || false;
        document.getElementById('login-attempts').value = settings.login_attempts || 5;
        document.getElementById('api-calls').value = settings.api_calls || 100;
        document.getElementById('password-resets').value = settings.password_resets || 3;
        document.getElementById('min-length').value = settings.password_min_length || 8;
    }

    async saveSettings() {
        const settings = {
            enforce_2fa: document.getElementById('enforce-2fa').checked,
            session_timeout: parseInt(document.getElementById('session-timeout').value),
            strict_ip: document.getElementById('strict-ip').checked,
            login_attempts: parseInt(document.getElementById('login-attempts').value),
            api_calls: parseInt(document.getElementById('api-calls').value),
            password_resets: parseInt(document.getElementById('password-resets').value),
            password_min_length: parseInt(document.getElementById('min-length').value),
            password_require_uppercase: document.querySelector('input[type="checkbox"]:nth-of-type(3)').checked,
            password_require_lowercase: document.querySelector('input[type="checkbox"]:nth-of-type(4)').checked,
            password_require_numbers: document.querySelector('input[type="checkbox"]:nth-of-type(5)').checked,
            password_require_special: document.querySelector('input[type="checkbox"]:nth-of-type(6)').checked
        };

        try {
            const response = await fetch('/api/security/settings', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(settings)
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Security settings saved successfully', 'success');
            } else {
                throw new Error(data.message || 'Save failed');
            }
        } catch (error) {
            console.error('Failed to save settings:', error);
            this.showNotification('Failed to save settings', 'error');
        }
    }

    resetSettings() {
        if (!confirm('Reset all security settings to defaults?')) {
            return;
        }

        // Reset to default values
        document.getElementById('enforce-2fa').checked = true;
        document.getElementById('session-timeout').value = 30;
        document.getElementById('strict-ip').checked = false;
        document.getElementById('login-attempts').value = 5;
        document.getElementById('api-calls').value = 100;
        document.getElementById('password-resets').value = 3;
        document.getElementById('min-length').value = 8;
        
        // Reset password policy checkboxes
        document.querySelectorAll('.policy-checkboxes input[type="checkbox"]').forEach(cb => {
            cb.checked = true;
        });

        this.showNotification('Settings reset to defaults', 'info');
    }

    setupWebSocket() {
        if (typeof io !== 'undefined') {
            this.socket = io('/security');
            
            this.socket.on('security_alert', (data) => {
                this.handleSecurityAlert(data);
            });
            
            this.socket.on('audit_log_update', (data) => {
                this.handleAuditLogUpdate(data);
            });
        }
    }

    handleSecurityAlert(alert) {
        this.showNotification(alert.message, alert.severity);
        
        // Update relevant dashboard sections
        if (alert.type === 'failed_login') {
            this.loadOverviewData();
        }
    }

    handleAuditLogUpdate(logEntry) {
        if (this.currentTab === 'audit') {
            this.loadAuditLogs();
        }
        
        // Update overview metrics
        this.loadOverviewData();
    }

    startSecurityMonitoring() {
        // Update dashboard every 30 seconds
        setInterval(() => {
            if (this.currentTab === 'overview') {
                this.loadOverviewData();
            }
        }, 30000);
    }

    showModal(modalId) {
        document.getElementById(modalId).style.display = 'block';
    }

    closeModal(modalId) {
        document.getElementById(modalId).style.display = 'none';
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-${this.getNotificationIcon(type)}"></i>
                <span>${message}</span>
                <button class="notification-close">&times;</button>
            </div>
        `;

        // Add to page
        document.body.appendChild(notification);

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);

        // Add close button functionality
        notification.querySelector('.notification-close').addEventListener('click', () => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        });
    }

    getNotificationIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'times-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    }
}

// Global functions for inline event handlers
window.closeModal = function(modalId) {
    document.getElementById(modalId).style.display = 'none';
};

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.securityDashboard = new SecurityDashboard();
});

// Add notification styles dynamically
const notificationStyles = `
.notification {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 10000;
    max-width: 400px;
    background: white;
    border-radius: 8px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
    animation: slideInRight 0.3s ease;
}

.notification-success {
    border-left: 4px solid #27ae60;
}

.notification-error {
    border-left: 4px solid #e74c3c;
}

.notification-warning {
    border-left: 4px solid #f39c12;
}

.notification-info {
    border-left: 4px solid #3498db;
}

.notification-content {
    padding: 15px 20px;
    display: flex;
    align-items: center;
    gap: 10px;
}

.notification-close {
    background: none;
    border: none;
    font-size: 1.2rem;
    color: #95a5a6;
    cursor: pointer;
    margin-left: auto;
}

@keyframes slideInRight {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

.badge {
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.8rem;
    font-weight: 600;
}

.badge-success {
    background: #d4edda;
    color: #155724;
}

.badge-danger {
    background: #f8d7da;
    color: #721c24;
}

.text-success {
    color: #27ae60 !important;
}

.text-danger {
    color: #e74c3c !important;
}
`;

// Inject styles
const styleSheet = document.createElement('style');
styleSheet.textContent = notificationStyles;
document.head.appendChild(styleSheet);