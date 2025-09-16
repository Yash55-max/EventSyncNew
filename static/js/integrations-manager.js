/**
 * Seamless Integrations Manager for Revolutionary Event Management Platform
 * Manages OAuth flows, payment processing, calendar sync, and third-party connections
 */

class IntegrationsManager {
    constructor() {
        this.integrations = {};
        this.oauthWindows = {};
        this.statusUpdateInterval = null;
        
        this.init();
    }
    
    init() {
        this.loadUserIntegrations();
        this.setupEventListeners();
        
        // Check integration status every 30 seconds
        this.statusUpdateInterval = setInterval(() => {
            this.updateIntegrationStatuses();
        }, 30000);
    }
    
    setupEventListeners() {
        // Integration connection buttons
        document.querySelectorAll('.connect-integration').forEach(button => {
            button.addEventListener('click', (e) => {
                const integrationType = e.target.dataset.integration;
                this.connectIntegration(integrationType);
            });
        });
        
        // Disconnect buttons
        document.querySelectorAll('.disconnect-integration').forEach(button => {
            button.addEventListener('click', (e) => {
                const integrationId = e.target.dataset.integrationId;
                this.disconnectIntegration(integrationId);
            });
        });
        
        // Test integration buttons
        document.querySelectorAll('.test-integration').forEach(button => {
            button.addEventListener('click', (e) => {
                const integrationType = e.target.dataset.integration;
                this.testIntegration(integrationType);
            });
        });
        
        // Payment method selection
        document.querySelectorAll('input[name="payment-method"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.updatePaymentMethodUI(e.target.value);
            });
        });
        
        // OAuth callback handling
        window.addEventListener('message', (event) => {
            this.handleOAuthCallback(event);
        });
    }
    
    async loadUserIntegrations() {
        try {
            const response = await fetch('/api/integrations/user');
            if (!response.ok) {
                throw new Error('Failed to load integrations');
            }
            
            const integrations = await response.json();
            this.integrations = {};
            
            integrations.forEach(integration => {
                this.integrations[integration.type] = integration;
                this.updateIntegrationUI(integration);
            });
            
        } catch (error) {
            console.error('Error loading user integrations:', error);
            this.showNotification('Failed to load integrations', 'error');
        }
    }
    
    async connectIntegration(integrationType) {
        try {
            this.showLoading(true, `Connecting to ${integrationType}...`);
            
            switch (integrationType) {
                case 'google_calendar':
                    await this.connectGoogleCalendar();
                    break;
                case 'outlook_calendar':
                    await this.connectOutlookCalendar();
                    break;
                case 'stripe_payment':
                    await this.connectStripe();
                    break;
                case 'paypal_payment':
                    await this.connectPayPal();
                    break;
                case 'github':
                    await this.connectGitHub();
                    break;
                case 'slack':
                    await this.connectSlack();
                    break;
                case 'webhooks':
                    await this.connectWebhooks();
                    break;
                default:
                    throw new Error(`Unsupported integration type: ${integrationType}`);
            }
            
        } catch (error) {
            console.error(`Error connecting ${integrationType}:`, error);
            this.showNotification(`Failed to connect ${integrationType}`, 'error');
        } finally {
            this.showLoading(false);
        }
    }
    
    // Google Calendar Integration
    async connectGoogleCalendar() {
        const clientId = this.getConfig('GOOGLE_CLIENT_ID');
        if (!clientId) {
            throw new Error('Google Client ID not configured');
        }
        
        const scope = 'https://www.googleapis.com/auth/calendar';
        const redirectUri = `${window.location.origin}/oauth/google/callback`;
        
        const authUrl = `https://accounts.google.com/oauth2/authorize?` +
            `client_id=${encodeURIComponent(clientId)}&` +
            `redirect_uri=${encodeURIComponent(redirectUri)}&` +
            `scope=${encodeURIComponent(scope)}&` +
            `response_type=code&` +
            `access_type=offline&` +
            `prompt=consent`;
        
        return this.openOAuthWindow('google_calendar', authUrl);
    }
    
    // Outlook Calendar Integration
    async connectOutlookCalendar() {
        const clientId = this.getConfig('MICROSOFT_CLIENT_ID');
        if (!clientId) {
            throw new Error('Microsoft Client ID not configured');
        }
        
        const tenantId = this.getConfig('MICROSOFT_TENANT_ID', 'common');
        const scope = 'https://graph.microsoft.com/calendars.readwrite offline_access';
        const redirectUri = `${window.location.origin}/oauth/microsoft/callback`;
        
        const authUrl = `https://login.microsoftonline.com/${tenantId}/oauth2/v2.0/authorize?` +
            `client_id=${encodeURIComponent(clientId)}&` +
            `response_type=code&` +
            `redirect_uri=${encodeURIComponent(redirectUri)}&` +
            `scope=${encodeURIComponent(scope)}&` +
            `response_mode=query`;
        
        return this.openOAuthWindow('outlook_calendar', authUrl);
    }
    
    // Stripe Payment Integration
    async connectStripe() {
        const modal = this.createStripeConnectionModal();
        document.body.appendChild(modal);
        
        return new Promise((resolve, reject) => {
            const form = modal.querySelector('#stripeConnectionForm');
            
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const formData = new FormData(form);
                const credentials = {
                    publishable_key: formData.get('publishable_key'),
                    secret_key: formData.get('secret_key'),
                    webhook_secret: formData.get('webhook_secret')
                };
                
                try {
                    const success = await this.registerIntegration('stripe_payment', credentials, {});
                    document.body.removeChild(modal);
                    
                    if (success) {
                        resolve();
                    } else {
                        reject(new Error('Failed to register Stripe integration'));
                    }
                } catch (error) {
                    reject(error);
                }
            });
            
            modal.querySelector('.close-modal').addEventListener('click', () => {
                document.body.removeChild(modal);
                reject(new Error('User cancelled'));
            });
        });
    }
    
    createStripeConnectionModal() {
        const modal = document.createElement('div');
        modal.className = 'integration-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Connect Stripe</h3>
                    <button class="close-modal">&times;</button>
                </div>
                
                <form id="stripeConnectionForm" class="integration-form">
                    <div class="form-group">
                        <label for="publishable_key">Publishable Key:</label>
                        <input type="text" id="publishable_key" name="publishable_key" 
                               placeholder="pk_test_..." required>
                        <small>Your Stripe publishable key (starts with pk_)</small>
                    </div>
                    
                    <div class="form-group">
                        <label for="secret_key">Secret Key:</label>
                        <input type="password" id="secret_key" name="secret_key" 
                               placeholder="sk_test_..." required>
                        <small>Your Stripe secret key (starts with sk_)</small>
                    </div>
                    
                    <div class="form-group">
                        <label for="webhook_secret">Webhook Secret (Optional):</label>
                        <input type="text" id="webhook_secret" name="webhook_secret" 
                               placeholder="whsec_...">
                        <small>Your Stripe webhook endpoint secret</small>
                    </div>
                    
                    <div class="form-actions">
                        <button type="button" class="btn btn-secondary close-modal">Cancel</button>
                        <button type="submit" class="btn btn-primary">Connect Stripe</button>
                    </div>
                </form>
            </div>
        `;
        
        return modal;
    }
    
    // PayPal Payment Integration
    async connectPayPal() {
        const modal = this.createPayPalConnectionModal();
        document.body.appendChild(modal);
        
        return new Promise((resolve, reject) => {
            const form = modal.querySelector('#paypalConnectionForm');
            
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const formData = new FormData(form);
                const credentials = {
                    client_id: formData.get('client_id'),
                    client_secret: formData.get('client_secret'),
                    sandbox: formData.get('sandbox') === 'on'
                };
                
                try {
                    const success = await this.registerIntegration('paypal_payment', credentials, {});
                    document.body.removeChild(modal);
                    
                    if (success) {
                        resolve();
                    } else {
                        reject(new Error('Failed to register PayPal integration'));
                    }
                } catch (error) {
                    reject(error);
                }
            });
            
            modal.querySelector('.close-modal').addEventListener('click', () => {
                document.body.removeChild(modal);
                reject(new Error('User cancelled'));
            });
        });
    }
    
    createPayPalConnectionModal() {
        const modal = document.createElement('div');
        modal.className = 'integration-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Connect PayPal</h3>
                    <button class="close-modal">&times;</button>
                </div>
                
                <form id="paypalConnectionForm" class="integration-form">
                    <div class="form-group">
                        <label for="client_id">Client ID:</label>
                        <input type="text" id="client_id" name="client_id" required>
                        <small>Your PayPal application client ID</small>
                    </div>
                    
                    <div class="form-group">
                        <label for="client_secret">Client Secret:</label>
                        <input type="password" id="client_secret" name="client_secret" required>
                        <small>Your PayPal application client secret</small>
                    </div>
                    
                    <div class="form-group">
                        <label class="checkbox-label">
                            <input type="checkbox" id="sandbox" name="sandbox" checked>
                            Use Sandbox (for testing)
                        </label>
                    </div>
                    
                    <div class="form-actions">
                        <button type="button" class="btn btn-secondary close-modal">Cancel</button>
                        <button type="submit" class="btn btn-primary">Connect PayPal</button>
                    </div>
                </form>
            </div>
        `;
        
        return modal;
    }
    
    // GitHub Integration
    async connectGitHub() {
        const clientId = this.getConfig('GITHUB_CLIENT_ID');
        if (!clientId) {
            throw new Error('GitHub Client ID not configured');
        }
        
        const scope = 'repo user';
        const redirectUri = `${window.location.origin}/oauth/github/callback`;
        
        const authUrl = `https://github.com/login/oauth/authorize?` +
            `client_id=${encodeURIComponent(clientId)}&` +
            `redirect_uri=${encodeURIComponent(redirectUri)}&` +
            `scope=${encodeURIComponent(scope)}&` +
            `state=${this.generateOAuthState()}`;
        
        return this.openOAuthWindow('github', authUrl);
    }
    
    // Slack Integration
    async connectSlack() {
        const clientId = this.getConfig('SLACK_CLIENT_ID');
        if (!clientId) {
            throw new Error('Slack Client ID not configured');
        }
        
        const scope = 'chat:write channels:manage channels:read';
        const redirectUri = `${window.location.origin}/oauth/slack/callback`;
        
        const authUrl = `https://slack.com/oauth/v2/authorize?` +
            `client_id=${encodeURIComponent(clientId)}&` +
            `scope=${encodeURIComponent(scope)}&` +
            `redirect_uri=${encodeURIComponent(redirectUri)}&` +
            `state=${this.generateOAuthState()}`;
        
        return this.openOAuthWindow('slack', authUrl);
    }
    
    // Webhooks Integration
    async connectWebhooks() {
        const modal = this.createWebhookConnectionModal();
        document.body.appendChild(modal);
        
        return new Promise((resolve, reject) => {
            const form = modal.querySelector('#webhookConnectionForm');
            
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const formData = new FormData(form);
                const webhookUrl = formData.get('webhook_url');
                const events = Array.from(formData.getAll('events'));
                
                try {
                    const response = await fetch('/api/integrations/webhooks/register', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            webhook_url: webhookUrl,
                            events: events
                        })
                    });
                    
                    if (!response.ok) {
                        throw new Error('Failed to register webhook');
                    }
                    
                    document.body.removeChild(modal);
                    await this.loadUserIntegrations(); // Refresh integrations list
                    this.showNotification('Webhook registered successfully!', 'success');
                    resolve();
                    
                } catch (error) {
                    reject(error);
                }
            });
            
            modal.querySelector('.close-modal').addEventListener('click', () => {
                document.body.removeChild(modal);
                reject(new Error('User cancelled'));
            });
        });
    }
    
    createWebhookConnectionModal() {
        const modal = document.createElement('div');
        modal.className = 'integration-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Configure Webhooks</h3>
                    <button class="close-modal">&times;</button>
                </div>
                
                <form id="webhookConnectionForm" class="integration-form">
                    <div class="form-group">
                        <label for="webhook_url">Webhook URL:</label>
                        <input type="url" id="webhook_url" name="webhook_url" 
                               placeholder="https://your-app.com/webhooks/events" required>
                        <small>The URL where webhook notifications will be sent</small>
                    </div>
                    
                    <div class="form-group">
                        <label>Select Events to Subscribe:</label>
                        <div class="checkbox-group">
                            <label class="checkbox-label">
                                <input type="checkbox" name="events" value="event.created" checked>
                                Event Created
                            </label>
                            <label class="checkbox-label">
                                <input type="checkbox" name="events" value="event.updated">
                                Event Updated
                            </label>
                            <label class="checkbox-label">
                                <input type="checkbox" name="events" value="ticket.purchased" checked>
                                Ticket Purchased
                            </label>
                            <label class="checkbox-label">
                                <input type="checkbox" name="events" value="event.cancelled">
                                Event Cancelled
                            </label>
                            <label class="checkbox-label">
                                <input type="checkbox" name="events" value="payment.completed">
                                Payment Completed
                            </label>
                        </div>
                    </div>
                    
                    <div class="form-actions">
                        <button type="button" class="btn btn-secondary close-modal">Cancel</button>
                        <button type="submit" class="btn btn-primary">Register Webhook</button>
                    </div>
                </form>
            </div>
        `;
        
        return modal;
    }
    
    openOAuthWindow(integrationType, authUrl) {
        return new Promise((resolve, reject) => {
            const width = 600;
            const height = 600;
            const left = (screen.width / 2) - (width / 2);
            const top = (screen.height / 2) - (height / 2);
            
            const oauthWindow = window.open(
                authUrl,
                `${integrationType}_oauth`,
                `width=${width},height=${height},left=${left},top=${top},resizable=yes,scrollbars=yes`
            );
            
            this.oauthWindows[integrationType] = {
                window: oauthWindow,
                resolve: resolve,
                reject: reject
            };
            
            // Check if window was closed manually
            const checkClosed = setInterval(() => {
                if (oauthWindow.closed) {
                    clearInterval(checkClosed);
                    delete this.oauthWindows[integrationType];
                    reject(new Error('OAuth window was closed'));
                }
            }, 1000);
        });
    }
    
    handleOAuthCallback(event) {
        // Handle OAuth callback from popup window
        if (event.origin !== window.location.origin) {
            return; // Ignore messages from other origins
        }
        
        const { type, success, data, error } = event.data;
        
        if (type === 'oauth_callback' && this.oauthWindows[data.integration_type]) {
            const oauthData = this.oauthWindows[data.integration_type];
            
            if (success) {
                oauthData.resolve();
                this.loadUserIntegrations(); // Refresh integrations list
                this.showNotification(`${data.integration_type} connected successfully!`, 'success');
            } else {
                oauthData.reject(new Error(error || 'OAuth failed'));
                this.showNotification(`Failed to connect ${data.integration_type}`, 'error');
            }
            
            oauthData.window.close();
            delete this.oauthWindows[data.integration_type];
        }
    }
    
    async registerIntegration(integrationType, credentials, settings) {
        try {
            const response = await fetch('/api/integrations/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    integration_type: integrationType,
                    credentials: credentials,
                    settings: settings
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to register integration');
            }
            
            const result = await response.json();
            
            if (result.success) {
                await this.loadUserIntegrations(); // Refresh integrations list
                this.showNotification(`${integrationType} connected successfully!`, 'success');
                return true;
            } else {
                throw new Error(result.error || 'Registration failed');
            }
            
        } catch (error) {
            console.error('Error registering integration:', error);
            this.showNotification(`Failed to connect ${integrationType}: ${error.message}`, 'error');
            return false;
        }
    }
    
    async disconnectIntegration(integrationId) {
        try {
            const response = await fetch(`/api/integrations/${integrationId}/disconnect`, {
                method: 'POST'
            });
            
            if (!response.ok) {
                throw new Error('Failed to disconnect integration');
            }
            
            await this.loadUserIntegrations(); // Refresh integrations list
            this.showNotification('Integration disconnected successfully!', 'success');
            
        } catch (error) {
            console.error('Error disconnecting integration:', error);
            this.showNotification('Failed to disconnect integration', 'error');
        }
    }
    
    async testIntegration(integrationType) {
        try {
            this.showLoading(true, `Testing ${integrationType}...`);
            
            const response = await fetch(`/api/integrations/test/${integrationType}`, {
                method: 'POST'
            });
            
            if (!response.ok) {
                throw new Error('Integration test failed');
            }
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification(`${integrationType} test successful!`, 'success');
            } else {
                this.showNotification(`${integrationType} test failed: ${result.error}`, 'error');
            }
            
        } catch (error) {
            console.error('Error testing integration:', error);
            this.showNotification(`Failed to test ${integrationType}`, 'error');
        } finally {
            this.showLoading(false);
        }
    }
    
    updateIntegrationUI(integration) {
        const card = document.querySelector(`[data-integration="${integration.type}"]`);
        if (!card) return;
        
        const statusElement = card.querySelector('.integration-status');
        const connectButton = card.querySelector('.connect-integration');
        const disconnectButton = card.querySelector('.disconnect-integration');
        const testButton = card.querySelector('.test-integration');
        
        // Update status
        if (statusElement) {
            statusElement.textContent = integration.status;
            statusElement.className = `integration-status status-${integration.status}`;
        }
        
        // Update buttons
        if (integration.status === 'active') {
            if (connectButton) connectButton.style.display = 'none';
            if (disconnectButton) {
                disconnectButton.style.display = 'inline-block';
                disconnectButton.dataset.integrationId = integration.id;
            }
            if (testButton) testButton.style.display = 'inline-block';
        } else {
            if (connectButton) connectButton.style.display = 'inline-block';
            if (disconnectButton) disconnectButton.style.display = 'none';
            if (testButton) testButton.style.display = 'none';
        }
        
        // Add connection info
        const infoElement = card.querySelector('.integration-info');
        if (infoElement && integration.status === 'active') {
            infoElement.innerHTML = `
                <small>Connected on ${new Date(integration.created_at).toLocaleDateString()}</small>
            `;
        }
    }
    
    async updateIntegrationStatuses() {
        // Update integration statuses in the background
        try {
            const response = await fetch('/api/integrations/status');
            if (!response.ok) return;
            
            const statuses = await response.json();
            
            Object.entries(statuses).forEach(([type, status]) => {
                if (this.integrations[type]) {
                    this.integrations[type].status = status;
                    this.updateIntegrationUI(this.integrations[type]);
                }
            });
            
        } catch (error) {
            console.error('Error updating integration statuses:', error);
        }
    }
    
    updatePaymentMethodUI(selectedMethod) {
        const paymentMethods = ['stripe', 'paypal'];
        
        paymentMethods.forEach(method => {
            const section = document.getElementById(`${method}-payment-section`);
            if (section) {
                section.style.display = method === selectedMethod ? 'block' : 'none';
            }
        });
    }
    
    // Calendar Sync Methods
    async syncEventToCalendars(eventId) {
        try {
            this.showLoading(true, 'Syncing to calendars...');
            
            const response = await fetch(`/api/integrations/calendar/sync/${eventId}`, {
                method: 'POST'
            });
            
            if (!response.ok) {
                throw new Error('Calendar sync failed');
            }
            
            const result = await response.json();
            
            const successCount = Object.values(result).filter(success => success).length;
            const totalCount = Object.keys(result).length;
            
            this.showNotification(
                `Event synced to ${successCount}/${totalCount} calendar services`,
                successCount > 0 ? 'success' : 'warning'
            );
            
            return result;
            
        } catch (error) {
            console.error('Error syncing to calendars:', error);
            this.showNotification('Failed to sync to calendars', 'error');
            return {};
        } finally {
            this.showLoading(false);
        }
    }
    
    // Payment Processing Methods
    async processPayment(eventId, amount, paymentMethod = 'stripe', paymentData = {}) {
        try {
            this.showLoading(true, 'Processing payment...');
            
            const response = await fetch('/api/integrations/payment/process', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    event_id: eventId,
                    amount: amount,
                    payment_method: paymentMethod,
                    ...paymentData
                })
            });
            
            if (!response.ok) {
                throw new Error('Payment processing failed');
            }
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('Payment processed successfully!', 'success');
                return result;
            } else {
                throw new Error(result.error_message || 'Payment failed');
            }
            
        } catch (error) {
            console.error('Error processing payment:', error);
            this.showNotification(`Payment failed: ${error.message}`, 'error');
            throw error;
        } finally {
            this.showLoading(false);
        }
    }
    
    // GitHub Repository Creation
    async createEventRepository(eventId, repoName, description = '', isPrivate = false) {
        try {
            this.showLoading(true, 'Creating GitHub repository...');
            
            const response = await fetch('/api/integrations/github/create-repo', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    event_id: eventId,
                    repo_name: repoName,
                    description: description,
                    private: isPrivate
                })
            });
            
            if (!response.ok) {
                throw new Error('Repository creation failed');
            }
            
            const result = await response.json();
            
            if (result.repository_url) {
                this.showNotification('GitHub repository created successfully!', 'success');
                return result.repository_url;
            } else {
                throw new Error('Repository creation failed');
            }
            
        } catch (error) {
            console.error('Error creating GitHub repository:', error);
            this.showNotification('Failed to create GitHub repository', 'error');
            throw error;
        } finally {
            this.showLoading(false);
        }
    }
    
    // Slack Channel Creation
    async createEventSlackChannel(eventId, channelName, isPrivate = false) {
        try {
            this.showLoading(true, 'Creating Slack channel...');
            
            const response = await fetch('/api/integrations/slack/create-channel', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    event_id: eventId,
                    channel_name: channelName,
                    is_private: isPrivate
                })
            });
            
            if (!response.ok) {
                throw new Error('Slack channel creation failed');
            }
            
            const result = await response.json();
            
            if (result.channel_id) {
                this.showNotification('Slack channel created successfully!', 'success');
                return result.channel_id;
            } else {
                throw new Error('Channel creation failed');
            }
            
        } catch (error) {
            console.error('Error creating Slack channel:', error);
            this.showNotification('Failed to create Slack channel', 'error');
            throw error;
        } finally {
            this.showLoading(false);
        }
    }
    
    // Utility Methods
    generateOAuthState() {
        return Math.random().toString(36).substring(2, 15) + 
               Math.random().toString(36).substring(2, 15);
    }
    
    getConfig(key, defaultValue = null) {
        // Get configuration from meta tags or environment
        const metaTag = document.querySelector(`meta[name="config-${key.toLowerCase()}"]`);
        return metaTag ? metaTag.content : defaultValue;
    }
    
    showLoading(show, message = 'Loading...') {
        let overlay = document.getElementById('integrationsLoadingOverlay');
        
        if (show && !overlay) {
            overlay = document.createElement('div');
            overlay.id = 'integrationsLoadingOverlay';
            overlay.className = 'loading-overlay';
            overlay.innerHTML = `
                <div class="loading-spinner">
                    <div class="spinner"></div>
                    <p>${message}</p>
                </div>
            `;
            document.body.appendChild(overlay);
        } else if (!show && overlay) {
            document.body.removeChild(overlay);
        } else if (show && overlay) {
            overlay.querySelector('p').textContent = message;
        }
    }
    
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-icon">
                    ${type === 'success' ? '✅' : type === 'error' ? '❌' : type === 'warning' ? '⚠️' : 'ℹ️'}
                </span>
                <span class="notification-message">${message}</span>
                <button class="notification-close">&times;</button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.classList.add('fade-out');
                setTimeout(() => {
                    if (notification.parentNode) {
                        document.body.removeChild(notification);
                    }
                }, 300);
            }
        }, 5000);
        
        // Manual close
        notification.querySelector('.notification-close').addEventListener('click', () => {
            if (notification.parentNode) {
                document.body.removeChild(notification);
            }
        });
    }
    
    destroy() {
        if (this.statusUpdateInterval) {
            clearInterval(this.statusUpdateInterval);
        }
        
        // Close any open OAuth windows
        Object.values(this.oauthWindows).forEach(oauthData => {
            if (oauthData.window && !oauthData.window.closed) {
                oauthData.window.close();
            }
        });
    }
}

// Payment Form Handler
class PaymentFormHandler {
    constructor(integrationsManager) {
        this.integrationsManager = integrationsManager;
        this.stripe = null;
        this.elements = null;
        this.cardElement = null;
        
        this.initStripe();
    }
    
    async initStripe() {
        const publishableKey = this.integrationsManager.getConfig('STRIPE_PUBLISHABLE_KEY');
        
        if (publishableKey && typeof Stripe !== 'undefined') {
            this.stripe = Stripe(publishableKey);
            this.elements = this.stripe.elements();
            
            this.setupStripeElements();
        }
    }
    
    setupStripeElements() {
        // Create card element
        this.cardElement = this.elements.create('card', {
            style: {
                base: {
                    fontSize: '16px',
                    color: '#424770',
                    '::placeholder': {
                        color: '#aab7c4',
                    },
                },
                invalid: {
                    color: '#9e2146',
                },
            },
        });
        
        const cardElementMount = document.getElementById('stripe-card-element');
        if (cardElementMount) {
            this.cardElement.mount('#stripe-card-element');
        }
        
        // Handle real-time validation errors from the card Element
        this.cardElement.on('change', ({error}) => {
            const displayError = document.getElementById('stripe-card-errors');
            if (error) {
                displayError.textContent = error.message;
            } else {
                displayError.textContent = '';
            }
        });
    }
    
    async processStripePayment(eventId, amount) {
        if (!this.stripe || !this.cardElement) {
            throw new Error('Stripe not initialized');
        }
        
        try {
            // Create payment method
            const {error, paymentMethod} = await this.stripe.createPaymentMethod({
                type: 'card',
                card: this.cardElement,
            });
            
            if (error) {
                throw new Error(error.message);
            }
            
            // Process payment through integrations manager
            return await this.integrationsManager.processPayment(eventId, amount, 'stripe', {
                payment_method_id: paymentMethod.id
            });
            
        } catch (error) {
            console.error('Stripe payment error:', error);
            throw error;
        }
    }
    
    async processPayPalPayment(eventId, amount) {
        try {
            // Process PayPal payment through integrations manager
            return await this.integrationsManager.processPayment(eventId, amount, 'paypal');
            
        } catch (error) {
            console.error('PayPal payment error:', error);
            throw error;
        }
    }
}

// Initialize integrations manager when DOM is loaded
let integrationsManager;
let paymentFormHandler;

document.addEventListener('DOMContentLoaded', function() {
    integrationsManager = new IntegrationsManager();
    paymentFormHandler = new PaymentFormHandler(integrationsManager);
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (integrationsManager) {
        integrationsManager.destroy();
    }
});

// Export for global access
window.IntegrationsManager = IntegrationsManager;
window.PaymentFormHandler = PaymentFormHandler;
window.integrationsManager = integrationsManager;