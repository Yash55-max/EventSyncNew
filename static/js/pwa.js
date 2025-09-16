/**
 * PWA Client-side JavaScript
 * Handles Progressive Web App functionality including:
 * - Service Worker registration
 * - Push notifications
 * - Offline detection
 * - App installation
 * - Background sync
 */

class PWAManager {
    constructor() {
        this.swRegistration = null;
        this.isOnline = navigator.onLine;
        this.deferredPrompt = null;
        this.installButton = null;
        this.notificationPermission = 'default';
        
        this.init();
    }

    async init() {
        console.log('🔄 Initializing PWA Manager');
        
        // Check PWA support
        if (!this.isPWASupported()) {
            console.warn('PWA features not fully supported');
            return;
        }

        // Initialize core features
        await this.registerServiceWorker();
        this.setupOnlineOfflineHandlers();
        this.setupInstallHandlers();
        this.setupPushNotifications();
        this.setupBackgroundSync();
        this.createOfflineIndicator();
        this.checkForUpdates();
        
        console.log('✅ PWA Manager initialized successfully');
    }

    isPWASupported() {
        return 'serviceWorker' in navigator && 
               'PushManager' in window && 
               'Notification' in window;
    }

    async registerServiceWorker() {
        try {
            console.log('🔄 Registering Service Worker...');
            
            this.swRegistration = await navigator.serviceWorker.register('/static/sw.js', {
                scope: '/'
            });

            console.log('✅ Service Worker registered:', this.swRegistration.scope);

            // Handle updates
            this.swRegistration.addEventListener('updatefound', () => {
                const newWorker = this.swRegistration.installing;
                newWorker.addEventListener('statechange', () => {
                    if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                        this.showUpdateNotification();
                    }
                });
            });

            // Handle messages from service worker
            navigator.serviceWorker.addEventListener('message', event => {
                this.handleServiceWorkerMessage(event.data);
            });

        } catch (error) {
            console.error('❌ Service Worker registration failed:', error);
        }
    }

    setupOnlineOfflineHandlers() {
        window.addEventListener('online', () => {
            console.log('🌐 Back online');
            this.isOnline = true;
            this.updateOnlineStatus();
            this.syncPendingData();
        });

        window.addEventListener('offline', () => {
            console.log('📱 Gone offline');
            this.isOnline = false;
            this.updateOnlineStatus();
        });

        this.updateOnlineStatus();
    }

    updateOnlineStatus() {
        const indicator = document.getElementById('offline-indicator');
        if (indicator) {
            indicator.style.display = this.isOnline ? 'none' : 'flex';
        }

        // Update UI elements
        document.querySelectorAll('[data-online-only]').forEach(element => {
            element.style.display = this.isOnline ? '' : 'none';
        });

        document.querySelectorAll('[data-offline-only]').forEach(element => {
            element.style.display = this.isOnline ? 'none' : '';
        });

        // Dispatch custom event
        window.dispatchEvent(new CustomEvent('connectivity-change', {
            detail: { isOnline: this.isOnline }
        }));
    }

    setupInstallHandlers() {
        // Listen for app install prompt
        window.addEventListener('beforeinstallprompt', (e) => {
            console.log('📱 App install prompt available');
            e.preventDefault();
            this.deferredPrompt = e;
            this.showInstallPrompt();
        });

        // Listen for app install
        window.addEventListener('appinstalled', () => {
            console.log('✅ App installed successfully');
            this.hideInstallPrompt();
            this.showNotification({
                title: 'App Installed!',
                body: 'EVENTSYNC is now installed on your device',
                tag: 'app-installed'
            });
        });
    }

    showInstallPrompt() {
        // Create install button if it doesn't exist
        if (!this.installButton) {
            this.installButton = document.createElement('button');
            this.installButton.id = 'pwa-install-btn';
            this.installButton.className = 'pwa-install-btn';
            this.installButton.innerHTML = `
                <i class="fas fa-download"></i>
                <span>Install App</span>
            `;
            
            this.installButton.addEventListener('click', () => {
                this.promptInstall();
            });

            // Add to header or navigation
            const header = document.querySelector('header') || document.querySelector('nav') || document.body;
            header.appendChild(this.installButton);
        }

        this.installButton.style.display = 'flex';
    }

    hideInstallPrompt() {
        if (this.installButton) {
            this.installButton.style.display = 'none';
        }
    }

    async promptInstall() {
        if (!this.deferredPrompt) {
            console.log('No install prompt available');
            return;
        }

        try {
            this.deferredPrompt.prompt();
            const result = await this.deferredPrompt.userChoice;
            
            console.log('Install prompt result:', result.outcome);
            
            this.deferredPrompt = null;
            this.hideInstallPrompt();
            
        } catch (error) {
            console.error('Install prompt error:', error);
        }
    }

    async setupPushNotifications() {
        if (!('PushManager' in window) || !('Notification' in window)) {
            console.warn('Push notifications not supported');
            return;
        }

        // Check notification permission
        this.notificationPermission = Notification.permission;
        
        // Create notification controls
        this.createNotificationControls();
    }

    createNotificationControls() {
        const controls = document.createElement('div');
        controls.id = 'notification-controls';
        controls.className = 'notification-controls';
        
        if (this.notificationPermission === 'default') {
            controls.innerHTML = `
                <button id="enable-notifications" class="btn btn-primary">
                    <i class="fas fa-bell"></i>
                    Enable Notifications
                </button>
            `;
            
            controls.querySelector('#enable-notifications').addEventListener('click', () => {
                this.requestNotificationPermission();
            });
        }

        // Add to settings or user menu
        const settingsArea = document.querySelector('.user-settings') || 
                           document.querySelector('.header-actions') || 
                           document.body;
        settingsArea.appendChild(controls);
    }

    async requestNotificationPermission() {
        try {
            const permission = await Notification.requestPermission();
            this.notificationPermission = permission;
            
            if (permission === 'granted') {
                console.log('✅ Notification permission granted');
                await this.subscribeToPushNotifications();
                this.showNotification({
                    title: 'Notifications Enabled!',
                    body: 'You\'ll now receive important updates about your events',
                    tag: 'notifications-enabled'
                });
            } else {
                console.log('❌ Notification permission denied');
            }
            
            this.updateNotificationControls();
            
        } catch (error) {
            console.error('Notification permission error:', error);
        }
    }

    async subscribeToPushNotifications() {
        if (!this.swRegistration) {
            console.error('Service Worker not registered');
            return;
        }

        try {
            const subscription = await this.swRegistration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: this.urlB64ToUint8Array(this.getVAPIDPublicKey())
            });

            console.log('✅ Push notification subscription:', subscription);

            // Send subscription to server
            await this.sendSubscriptionToServer(subscription);
            
        } catch (error) {
            console.error('Push subscription error:', error);
        }
    }

    async sendSubscriptionToServer(subscription) {
        try {
            const response = await fetch('/api/push-subscription', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(subscription)
            });

            if (!response.ok) {
                throw new Error('Failed to send subscription to server');
            }

            console.log('✅ Subscription sent to server');
            
        } catch (error) {
            console.error('Failed to send subscription:', error);
        }
    }

    getVAPIDPublicKey() {
        // In production, this should come from your server
        return 'BMwYlhyeKnVx9Lh-EYE7_E8XcEaXHfwTSe7JZ8_7EV3EHVHVDRrO4YtCZLEz8vH6O7w8yOUmhiKZP9yXcUqW5wA';
    }

    urlB64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding).replace(/\-/g, '+').replace(/_/g, '/');
        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);
        
        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray;
    }

    updateNotificationControls() {
        const controls = document.getElementById('notification-controls');
        if (!controls) return;

        if (this.notificationPermission === 'granted') {
            controls.innerHTML = `
                <div class="notification-status">
                    <i class="fas fa-bell text-success"></i>
                    Notifications Enabled
                </div>
            `;
        } else if (this.notificationPermission === 'denied') {
            controls.innerHTML = `
                <div class="notification-status">
                    <i class="fas fa-bell-slash text-danger"></i>
                    Notifications Blocked
                </div>
            `;
        }
    }

    setupBackgroundSync() {
        if (!('serviceWorker' in navigator) || !('sync' in window.ServiceWorkerRegistration.prototype)) {
            console.warn('Background sync not supported');
            return;
        }

        // Intercept form submissions for offline handling
        this.interceptFormSubmissions();
        
        // Listen for connectivity changes to sync pending data
        window.addEventListener('online', () => {
            this.syncPendingData();
        });
    }

    interceptFormSubmissions() {
        document.addEventListener('submit', async (event) => {
            if (!this.isOnline && event.target.dataset.offlineSync) {
                event.preventDefault();
                await this.handleOfflineSubmission(event.target);
            }
        });
    }

    async handleOfflineSubmission(form) {
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        data.id = Date.now().toString();
        data.timestamp = new Date().toISOString();
        
        // Store in IndexedDB
        await this.storeOfflineData(form.dataset.offlineSync, data);
        
        // Register for background sync
        if (this.swRegistration && this.swRegistration.sync) {
            await this.swRegistration.sync.register(form.dataset.offlineSync);
        }
        
        this.showNotification({
            title: 'Saved Offline',
            body: 'Your data will be synced when you\'re back online',
            tag: 'offline-save'
        });
    }

    async storeOfflineData(type, data) {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open('EventMgmtOffline', 1);
            
            request.onerror = () => reject(request.error);
            request.onsuccess = () => {
                const db = request.result;
                const transaction = db.transaction([type], 'readwrite');
                const store = transaction.objectStore(type);
                const addRequest = store.add(data);
                
                addRequest.onsuccess = () => resolve();
                addRequest.onerror = () => reject(addRequest.error);
            };
            
            request.onupgradeneeded = () => {
                const db = request.result;
                if (!db.objectStoreNames.contains(type)) {
                    db.createObjectStore(type, { keyPath: 'id' });
                }
            };
        });
    }

    async syncPendingData() {
        if (!this.swRegistration || !this.swRegistration.sync) {
            return;
        }

        try {
            // Trigger sync for different data types
            const syncTags = ['event-registration', 'event-creation', 'user-data'];
            
            for (const tag of syncTags) {
                await this.swRegistration.sync.register(tag);
            }
            
        } catch (error) {
            console.error('Background sync error:', error);
        }
    }

    createOfflineIndicator() {
        const indicator = document.createElement('div');
        indicator.id = 'offline-indicator';
        indicator.className = 'offline-indicator';
        indicator.innerHTML = `
            <div class="offline-content">
                <i class="fas fa-wifi-slash"></i>
                <span>You're offline</span>
                <small>Some features may be limited</small>
            </div>
        `;
        
        document.body.appendChild(indicator);
    }

    async checkForUpdates() {
        if (!this.swRegistration) return;

        // Check for updates every 60 seconds
        setInterval(async () => {
            try {
                await this.swRegistration.update();
            } catch (error) {
                console.error('Update check failed:', error);
            }
        }, 60000);
    }

    showUpdateNotification() {
        const notification = document.createElement('div');
        notification.className = 'update-notification';
        notification.innerHTML = `
            <div class="update-content">
                <i class="fas fa-download"></i>
                <div>
                    <strong>Update Available</strong>
                    <p>A new version of the app is ready</p>
                </div>
                <button id="apply-update" class="btn btn-primary">Update</button>
                <button id="dismiss-update" class="btn btn-secondary">Later</button>
            </div>
        `;

        document.body.appendChild(notification);

        // Handle update actions
        notification.querySelector('#apply-update').addEventListener('click', () => {
            this.applyUpdate();
            notification.remove();
        });

        notification.querySelector('#dismiss-update').addEventListener('click', () => {
            notification.remove();
        });

        // Auto-dismiss after 10 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 10000);
    }

    applyUpdate() {
        if (this.swRegistration && this.swRegistration.waiting) {
            this.swRegistration.waiting.postMessage({ type: 'SKIP_WAITING' });
            window.location.reload();
        }
    }

    handleServiceWorkerMessage(data) {
        switch (data.type) {
            case 'CACHE_UPDATED':
                console.log('Cache updated with new content');
                break;
            case 'SYNC_COMPLETE':
                this.showNotification({
                    title: 'Sync Complete',
                    body: 'Your offline data has been synchronized',
                    tag: 'sync-complete'
                });
                break;
            default:
                console.log('Unknown service worker message:', data);
        }
    }

    async showNotification(options) {
        if (this.notificationPermission !== 'granted') {
            console.log('Notifications not permitted');
            return;
        }

        try {
            if (this.swRegistration) {
                await this.swRegistration.showNotification(options.title, {
                    body: options.body,
                    icon: '/static/icons/icon-192x192.png',
                    badge: '/static/icons/icon-72x72.png',
                    tag: options.tag || 'default',
                    requireInteraction: false,
                    data: options.data || {}
                });
            } else {
                new Notification(options.title, {
                    body: options.body,
                    icon: '/static/icons/icon-192x192.png',
                    tag: options.tag || 'default'
                });
            }
        } catch (error) {
            console.error('Notification error:', error);
        }
    }

    // Utility methods for offline functionality
    async getCachedData(url) {
        try {
            const cache = await caches.open('eventmgmt-v1.0.0');
            const response = await cache.match(url);
            return response ? await response.json() : null;
        } catch (error) {
            console.error('Cache read error:', error);
            return null;
        }
    }

    async cacheData(url, data) {
        try {
            const cache = await caches.open('eventmgmt-v1.0.0');
            const response = new Response(JSON.stringify(data), {
                headers: { 'Content-Type': 'application/json' }
            });
            await cache.put(url, response);
        } catch (error) {
            console.error('Cache write error:', error);
        }
    }

    // Share API integration
    async shareContent(data) {
        if (navigator.share) {
            try {
                await navigator.share(data);
                console.log('Content shared successfully');
            } catch (error) {
                console.log('Share cancelled or failed:', error);
            }
        } else {
            // Fallback: copy to clipboard or show share options
            this.fallbackShare(data);
        }
    }

    fallbackShare(data) {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(data.url || data.text);
            this.showNotification({
                title: 'Link Copied',
                body: 'Link copied to clipboard',
                tag: 'share-fallback'
            });
        }
    }

    // Performance monitoring
    measurePerformance() {
        if ('PerformanceObserver' in window) {
            const observer = new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    console.log(`${entry.name}: ${entry.duration}ms`);
                }
            });
            observer.observe({ entryTypes: ['measure', 'navigation'] });
        }
    }
}

// Initialize PWA Manager when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.pwaManager = new PWAManager();
    });
} else {
    window.pwaManager = new PWAManager();
}

// Export for modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PWAManager;
}
