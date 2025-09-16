/**
 * Service Worker for Revolutionary Event Management System PWA
 * 
 * Features:
 * - Offline functionality with caching strategies
 * - Background synchronization
 * - Push notifications
 * - App updates
 * - Performance optimization
 */

const CACHE_NAME = 'EventSync-v1.0.0';
const OFFLINE_URL = '/offline';

// Resources to cache on install
const STATIC_CACHE_URLS = [
  '/',
  '/offline',
  '/static/css/styles.css',
  '/static/css/modern-ui.css',
  '/static/css/security-dashboard.css',
  '/static/js/main.js',
  '/static/js/modern-ui.js',
  '/static/js/security-dashboard.js',
  '/static/js/events.js',
  '/static/js/dashboard.js',
  '/static/manifest.json',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css'
];

// API endpoints to cache with network-first strategy
const API_CACHE_PATTERNS = [
  /^\/api\/events/,
  /^\/api\/users/,
  /^\/api\/analytics/,
  /^\/api\/security/
];

// Dynamic content patterns
const DYNAMIC_CACHE_PATTERNS = [
  /^\/events/,
  /^\/event\/\d+/,
  /^\/admin/,
  /^\/organizer/,
  /^\/attendee/
];

// Install event - cache static resources
self.addEventListener('install', event => {
  console.log('[SW] Installing Service Worker');
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('[SW] Caching static resources');
        return cache.addAll(STATIC_CACHE_URLS);
      })
      .then(() => self.skipWaiting())
      .catch(error => {
        console.error('[SW] Failed to cache static resources:', error);
      })
  );
});

// Activate event - cleanup old caches
self.addEventListener('activate', event => {
  console.log('[SW] Activating Service Worker');
  
  event.waitUntil(
    Promise.all([
      // Clean up old caches
      caches.keys().then(cacheNames => {
        return Promise.all(
          cacheNames.map(cacheName => {
            if (cacheName !== CACHE_NAME) {
              console.log('[SW] Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      }),
      // Claim all clients
      self.clients.claim()
    ])
  );
});

// Fetch event - handle requests with caching strategies
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests and chrome-extension requests
  if (request.method !== 'GET' || url.protocol === 'chrome-extension:') {
    return;
  }

  // Handle different request types with appropriate strategies
  if (isStaticResource(url.pathname)) {
    // Cache-first for static resources
    event.respondWith(cacheFirstStrategy(request));
  } else if (isAPIRequest(url.pathname)) {
    // Network-first for API requests
    event.respondWith(networkFirstStrategy(request));
  } else if (isDynamicContent(url.pathname)) {
    // Stale-while-revalidate for dynamic content
    event.respondWith(staleWhileRevalidateStrategy(request));
  } else {
    // Default: network-first with offline fallback
    event.respondWith(networkWithOfflineFallback(request));
  }
});

// Background Sync for offline actions
self.addEventListener('sync', event => {
  console.log('[SW] Background sync triggered:', event.tag);
  
  switch (event.tag) {
    case 'event-registration':
      event.waitUntil(syncEventRegistrations());
      break;
    case 'event-creation':
      event.waitUntil(syncEventCreations());
      break;
    case 'user-data':
      event.waitUntil(syncUserData());
      break;
    default:
      console.log('[SW] Unknown sync tag:', event.tag);
  }
});

// Push notification event
self.addEventListener('push', event => {
  console.log('[SW] Push notification received');
  
  let notificationData = {
    title: 'EventSync',
    body: 'You have a new notification',
    icon: '/static/icons/icon-192x192.png',
    badge: '/static/icons/icon-72x72.png',
    tag: 'event-notification',
    requireInteraction: false
  };

  if (event.data) {
    try {
      const data = event.data.json();
      notificationData = { ...notificationData, ...data };
    } catch (error) {
      notificationData.body = event.data.text();
    }
  }

  event.waitUntil(
    self.registration.showNotification(notificationData.title, {
      body: notificationData.body,
      icon: notificationData.icon,
      badge: notificationData.badge,
      tag: notificationData.tag,
      requireInteraction: notificationData.requireInteraction,
      actions: [
        {
          action: 'view',
          title: 'View',
          icon: '/static/icons/action-view.png'
        },
        {
          action: 'dismiss',
          title: 'Dismiss',
          icon: '/static/icons/action-dismiss.png'
        }
      ],
      data: notificationData.data || {}
    })
  );
});

// Notification click event
self.addEventListener('notificationclick', event => {
  console.log('[SW] Notification clicked:', event.action);
  
  event.notification.close();
  
  if (event.action === 'dismiss') {
    return;
  }
  
  const urlToOpen = event.notification.data?.url || '/';
  
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then(clientList => {
        // Try to focus existing window
        for (const client of clientList) {
          if (client.url === urlToOpen && 'focus' in client) {
            return client.focus();
          }
        }
        
        // Open new window
        if (clients.openWindow) {
          return clients.openWindow(urlToOpen);
        }
      })
  );
});

// Message event for client communication
self.addEventListener('message', event => {
  console.log('[SW] Message received:', event.data);
  
  switch (event.data.type) {
    case 'SKIP_WAITING':
      self.skipWaiting();
      break;
    case 'GET_VERSION':
      event.ports[0].postMessage({ version: CACHE_NAME });
      break;
    case 'CACHE_URLS':
      event.waitUntil(
        caches.open(CACHE_NAME)
          .then(cache => cache.addAll(event.data.urls))
      );
      break;
    default:
      console.log('[SW] Unknown message type:', event.data.type);
  }
});

// Caching Strategies

function cacheFirstStrategy(request) {
  return caches.match(request)
    .then(response => {
      if (response) {
        return response;
      }
      
      return fetch(request)
        .then(response => {
          if (response.status === 200) {
            const responseClone = response.clone();
            caches.open(CACHE_NAME)
              .then(cache => cache.put(request, responseClone));
          }
          return response;
        });
    })
    .catch(() => {
      // Return offline fallback for navigation requests
      if (request.mode === 'navigate') {
        return caches.match(OFFLINE_URL);
      }
    });
}

function networkFirstStrategy(request) {
  return fetch(request)
    .then(response => {
      if (response.status === 200) {
        const responseClone = response.clone();
        caches.open(CACHE_NAME)
          .then(cache => cache.put(request, responseClone));
      }
      return response;
    })
    .catch(() => {
      return caches.match(request);
    });
}

function staleWhileRevalidateStrategy(request) {
  const fetchPromise = fetch(request)
    .then(response => {
      if (response.status === 200) {
        const responseClone = response.clone();
        caches.open(CACHE_NAME)
          .then(cache => cache.put(request, responseClone));
      }
      return response;
    });

  return caches.match(request)
    .then(response => {
      return response || fetchPromise;
    })
    .catch(() => fetchPromise);
}

function networkWithOfflineFallback(request) {
  return fetch(request)
    .catch(() => {
      if (request.mode === 'navigate') {
        return caches.match(OFFLINE_URL);
      }
      return caches.match(request);
    });
}

// Helper Functions

function isStaticResource(pathname) {
  return pathname.startsWith('/static/') ||
         pathname.endsWith('.css') ||
         pathname.endsWith('.js') ||
         pathname.endsWith('.png') ||
         pathname.endsWith('.jpg') ||
         pathname.endsWith('.svg') ||
         pathname.endsWith('.ico');
}

function isAPIRequest(pathname) {
  return API_CACHE_PATTERNS.some(pattern => pattern.test(pathname));
}

function isDynamicContent(pathname) {
  return DYNAMIC_CACHE_PATTERNS.some(pattern => pattern.test(pathname));
}

// Background Sync Functions

async function syncEventRegistrations() {
  try {
    console.log('[SW] Syncing event registrations');
    
    const registrations = await getStoredData('pending-registrations');
    
    for (const registration of registrations) {
      try {
        const response = await fetch('/api/events/register', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(registration)
        });
        
        if (response.ok) {
          await removeStoredData('pending-registrations', registration.id);
          await showNotification({
            title: 'Registration Successful',
            body: `Successfully registered for ${registration.eventTitle}`,
            tag: 'sync-success'
          });
        }
      } catch (error) {
        console.error('[SW] Failed to sync registration:', error);
      }
    }
  } catch (error) {
    console.error('[SW] Background sync failed:', error);
  }
}

async function syncEventCreations() {
  try {
    console.log('[SW] Syncing event creations');
    
    const events = await getStoredData('pending-events');
    
    for (const event of events) {
      try {
        const response = await fetch('/api/events', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(event)
        });
        
        if (response.ok) {
          await removeStoredData('pending-events', event.id);
          await showNotification({
            title: 'Event Created',
            body: `Successfully created "${event.title}"`,
            tag: 'sync-success'
          });
        }
      } catch (error) {
        console.error('[SW] Failed to sync event:', error);
      }
    }
  } catch (error) {
    console.error('[SW] Event sync failed:', error);
  }
}

async function syncUserData() {
  try {
    console.log('[SW] Syncing user data');
    
    const userData = await getStoredData('pending-user-updates');
    
    for (const update of userData) {
      try {
        const response = await fetch('/api/users/profile', {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(update)
        });
        
        if (response.ok) {
          await removeStoredData('pending-user-updates', update.id);
        }
      } catch (error) {
        console.error('[SW] Failed to sync user data:', error);
      }
    }
  } catch (error) {
    console.error('[SW] User data sync failed:', error);
  }
}

// IndexedDB helpers for offline storage
async function getStoredData(storeName) {
  return new Promise((resolve, reject) => {
const request = indexedDB.open('EVENTSYNCOffline', 1);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => {
      const db = request.result;
      const transaction = db.transaction([storeName], 'readonly');
      const store = transaction.objectStore(storeName);
      const getRequest = store.getAll();
      
      getRequest.onsuccess = () => resolve(getRequest.result || []);
      getRequest.onerror = () => reject(getRequest.error);
    };
    
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(storeName)) {
        db.createObjectStore(storeName, { keyPath: 'id' });
      }
    };
  });
}

async function removeStoredData(storeName, id) {
  return new Promise((resolve, reject) => {
const request = indexedDB.open('EVENTSYNCOffline', 1);
    
    request.onsuccess = () => {
      const db = request.result;
      const transaction = db.transaction([storeName], 'readwrite');
      const store = transaction.objectStore(storeName);
      const deleteRequest = store.delete(id);
      
      deleteRequest.onsuccess = () => resolve();
      deleteRequest.onerror = () => reject(deleteRequest.error);
    };
  });
}

async function showNotification(options) {
  if ('serviceWorker' in navigator && 'Notification' in window) {
    return self.registration.showNotification(options.title, {
      body: options.body,
      icon: '/static/icons/icon-192x192.png',
      tag: options.tag || 'general',
      requireInteraction: false
    });
  }
}

console.log('[SW] Service Worker loaded successfully');
