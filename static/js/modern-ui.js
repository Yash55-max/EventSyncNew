/**
 * Revolutionary Event Management Platform - Modern UI JavaScript
 * Enhanced with drag-and-drop, AI suggestions, and advanced interactions
 */

class ModernUI {
    constructor() {
        this.init();
        this.eventBuilder = new EventBuilder();
        this.notifications = new NotificationSystem();
        this.aiSuggestions = new AISuggestionEngine();
        this.teamFormation = new TeamFormationUI();
    }

    init() {
        this.setupThemeToggle();
        this.setupModernTabs();
        this.setupModernInputs();
        this.setupProgressBars();
        this.setupInfiniteScroll();
        this.setupKeyboardShortcuts();
    }

    setupThemeToggle() {
        const themeToggle = document.querySelector('#theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('change', (e) => {
                const theme = e.target.checked ? 'dark' : 'light';
                document.documentElement.setAttribute('data-theme', theme);
                localStorage.setItem('theme', theme);
                this.notifications.show('Theme updated!', 'success');
            });

            // Load saved theme
            const savedTheme = localStorage.getItem('theme') || 'light';
            document.documentElement.setAttribute('data-theme', savedTheme);
            themeToggle.checked = savedTheme === 'dark';
        }
    }

    setupModernTabs() {
        document.querySelectorAll('.modern-tab-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const targetId = link.getAttribute('href').substring(1);
                this.switchTab(targetId, link);
            });
        });
    }

    switchTab(targetId, activeLink) {
        // Hide all tab contents
        document.querySelectorAll('.modern-tab-content').forEach(content => {
            content.classList.remove('active');
        });

        // Remove active class from all links
        document.querySelectorAll('.modern-tab-link').forEach(link => {
            link.classList.remove('active');
        });

        // Show target tab content
        const targetContent = document.getElementById(targetId);
        if (targetContent) {
            targetContent.classList.add('active');
        }

        // Add active class to clicked link
        activeLink.classList.add('active');
    }

    setupModernInputs() {
        // Enhanced input validation and animations
        document.querySelectorAll('.modern-input').forEach(input => {
            input.addEventListener('focus', () => {
                input.parentElement.classList.add('focused');
            });

            input.addEventListener('blur', () => {
                input.parentElement.classList.remove('focused');
                this.validateInput(input);
            });

            input.addEventListener('input', () => {
                this.clearValidationError(input);
            });
        });
    }

    validateInput(input) {
        const value = input.value.trim();
        const type = input.type;
        const required = input.hasAttribute('required');

        if (required && !value) {
            this.showValidationError(input, 'This field is required');
            return false;
        }

        if (type === 'email' && value && !this.isValidEmail(value)) {
            this.showValidationError(input, 'Please enter a valid email address');
            return false;
        }

        if (type === 'url' && value && !this.isValidUrl(value)) {
            this.showValidationError(input, 'Please enter a valid URL');
            return false;
        }

        return true;
    }

    showValidationError(input, message) {
        this.clearValidationError(input);
        
        const errorElement = document.createElement('div');
        errorElement.className = 'validation-error';
        errorElement.textContent = message;
        errorElement.style.cssText = `
            color: var(--danger-color);
            font-size: 0.875rem;
            margin-top: 0.25rem;
            animation: fadeIn 0.3s ease;
        `;

        input.parentElement.appendChild(errorElement);
        input.style.borderColor = 'var(--danger-color)';
    }

    clearValidationError(input) {
        const errorElement = input.parentElement.querySelector('.validation-error');
        if (errorElement) {
            errorElement.remove();
        }
        input.style.borderColor = '';
    }

    isValidEmail(email) {
        const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return regex.test(email);
    }

    isValidUrl(url) {
        try {
            new URL(url);
            return true;
        } catch {
            return false;
        }
    }

    setupProgressBars() {
        document.querySelectorAll('.modern-progress-bar').forEach(bar => {
            const percentage = bar.dataset.percentage || 0;
            setTimeout(() => {
                bar.style.width = `${percentage}%`;
            }, 100);
        });
    }

    setupInfiniteScroll() {
        const infiniteScrollElements = document.querySelectorAll('[data-infinite-scroll]');
        
        infiniteScrollElements.forEach(element => {
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        this.loadMoreContent(element);
                    }
                });
            }, { threshold: 0.1 });

            observer.observe(element);
        });
    }

    async loadMoreContent(element) {
        const url = element.dataset.loadUrl;
        const page = parseInt(element.dataset.page) || 1;
        
        if (url && !element.classList.contains('loading')) {
            element.classList.add('loading');
            
            try {
                const response = await fetch(`${url}?page=${page + 1}`);
                const data = await response.json();
                
                if (data.content) {
                    const container = document.querySelector(element.dataset.container);
                    container.insertAdjacentHTML('beforeend', data.content);
                    element.dataset.page = page + 1;
                }
                
                if (!data.hasMore) {
                    element.style.display = 'none';
                }
            } catch (error) {
                console.error('Error loading more content:', error);
                this.notifications.show('Error loading content', 'error');
            } finally {
                element.classList.remove('loading');
            }
        }
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + K for search
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                const searchInput = document.querySelector('#global-search');
                if (searchInput) {
                    searchInput.focus();
                }
            }

            // Escape to close modals
            if (e.key === 'Escape') {
                this.closeModals();
            }
        });
    }

    closeModals() {
        document.querySelectorAll('.modal.show').forEach(modal => {
            const modalInstance = bootstrap.Modal.getInstance(modal);
            if (modalInstance) {
                modalInstance.hide();
            }
        });
    }
}

class EventBuilder {
    constructor() {
        this.components = [];
        this.currentLayout = 'default';
        this.init();
    }

    init() {
        this.setupDragAndDrop();
        this.setupComponentPalette();
        this.setupLayoutSwitcher();
    }

    setupDragAndDrop() {
        const canvas = document.querySelector('.event-builder-canvas');
        if (!canvas) return;

        canvas.addEventListener('dragover', (e) => {
            e.preventDefault();
            canvas.classList.add('drag-over');
        });

        canvas.addEventListener('dragleave', (e) => {
            e.preventDefault();
            canvas.classList.remove('drag-over');
        });

        canvas.addEventListener('drop', (e) => {
            e.preventDefault();
            canvas.classList.remove('drag-over');
            
            const componentType = e.dataTransfer.getData('text/plain');
            const rect = canvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            this.addComponent(componentType, x, y);
        });
    }

    setupComponentPalette() {
        document.querySelectorAll('.draggable-component').forEach(component => {
            component.setAttribute('draggable', 'true');
            
            component.addEventListener('dragstart', (e) => {
                const componentType = component.dataset.type;
                e.dataTransfer.setData('text/plain', componentType);
                component.classList.add('being-dragged');
            });

            component.addEventListener('dragend', () => {
                component.classList.remove('being-dragged');
            });

            // Double click to add to center
            component.addEventListener('dblclick', () => {
                const componentType = component.dataset.type;
                this.addComponent(componentType, 'center');
            });
        });
    }

    addComponent(type, x = 'center', y = 'center') {
        const component = this.createComponent(type, x, y);
        const canvas = document.querySelector('.event-builder-canvas');
        
        if (canvas && component) {
            canvas.appendChild(component);
            this.components.push({
                id: component.id,
                type: type,
                x: x,
                y: y,
                data: this.getDefaultComponentData(type)
            });
            
            this.animateComponentAddition(component);
            window.modernUI.notifications.show(`${type} component added!`, 'success');
        }
    }

    createComponent(type, x, y) {
        const component = document.createElement('div');
        component.className = 'event-component';
        component.id = `component-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        
        if (x !== 'center' && y !== 'center') {
            component.style.position = 'absolute';
            component.style.left = `${x}px`;
            component.style.top = `${y}px`;
        }

        const content = this.getComponentContent(type);
        const controls = this.createComponentControls();
        
        component.innerHTML = content + controls;
        
        this.setupComponentInteractions(component);
        return component;
    }

    getComponentContent(type) {
        const templates = {
            'title-section': `
                <h3>Event Title</h3>
                <p>Click to edit this title section</p>
            `,
            'description': `
                <div class="description-component">
                    <h4>Description</h4>
                    <p>Add your event description here...</p>
                </div>
            `,
            'date-time': `
                <div class="datetime-component">
                    <h4>📅 Date & Time</h4>
                    <p>Select event date and time</p>
                </div>
            `,
            'location': `
                <div class="location-component">
                    <h4>📍 Location</h4>
                    <p>Add venue or virtual link</p>
                </div>
            `,
            'registration': `
                <div class="registration-component">
                    <h4>🎫 Registration</h4>
                    <p>Configure registration settings</p>
                </div>
            `,
            'speakers': `
                <div class="speakers-component">
                    <h4>🎤 Speakers</h4>
                    <p>Add speaker information</p>
                </div>
            `,
            'agenda': `
                <div class="agenda-component">
                    <h4>📋 Agenda</h4>
                    <p>Create event schedule</p>
                </div>
            `,
            'sponsors': `
                <div class="sponsors-component">
                    <h4>🤝 Sponsors</h4>
                    <p>Add sponsor logos and links</p>
                </div>
            `
        };

        return templates[type] || '<p>Unknown component</p>';
    }

    createComponentControls() {
        return `
            <div class="component-controls">
                <button class="component-control edit" title="Edit">✏️</button>
                <button class="component-control delete" title="Delete">🗑️</button>
            </div>
        `;
    }

    setupComponentInteractions(component) {
        const editBtn = component.querySelector('.component-control.edit');
        const deleteBtn = component.querySelector('.component-control.delete');

        if (editBtn) {
            editBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.editComponent(component);
            });
        }

        if (deleteBtn) {
            deleteBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.deleteComponent(component);
            });
        }

        // Make component draggable within canvas
        this.makeDraggable(component);
    }

    makeDraggable(element) {
        let isDragging = false;
        let currentX, currentY, initialX, initialY;
        let xOffset = 0, yOffset = 0;

        element.addEventListener('mousedown', dragStart);

        function dragStart(e) {
            if (e.target.classList.contains('component-control')) return;
            
            initialX = e.clientX - xOffset;
            initialY = e.clientY - yOffset;

            if (e.target === element) {
                isDragging = true;
                element.style.cursor = 'grabbing';
            }
        }

        document.addEventListener('mousemove', drag);
        document.addEventListener('mouseup', dragEnd);

        function drag(e) {
            if (isDragging) {
                e.preventDefault();
                currentX = e.clientX - initialX;
                currentY = e.clientY - initialY;

                xOffset = currentX;
                yOffset = currentY;

                element.style.transform = `translate(${currentX}px, ${currentY}px)`;
            }
        }

        function dragEnd(e) {
            initialX = currentX;
            initialY = currentY;

            isDragging = false;
            element.style.cursor = 'move';
        }
    }

    editComponent(component) {
        const componentType = this.getComponentType(component);
        const modal = this.createEditModal(component, componentType);
        document.body.appendChild(modal);
        
        const bootstrapModal = new bootstrap.Modal(modal);
        bootstrapModal.show();
        
        modal.addEventListener('hidden.bs.modal', () => {
            modal.remove();
        });
    }

    deleteComponent(component) {
        if (confirm('Are you sure you want to delete this component?')) {
            component.style.animation = 'fadeOut 0.3s ease';
            setTimeout(() => {
                component.remove();
                this.components = this.components.filter(c => c.id !== component.id);
                window.modernUI.notifications.show('Component deleted', 'warning');
            }, 300);
        }
    }

    animateComponentAddition(component) {
        component.style.opacity = '0';
        component.style.transform = 'scale(0.8)';
        
        setTimeout(() => {
            component.style.transition = 'all 0.3s ease';
            component.style.opacity = '1';
            component.style.transform = 'scale(1)';
        }, 50);
    }

    getComponentType(component) {
        const classList = Array.from(component.classList);
        return classList.find(cls => cls.includes('-component'))?.replace('-component', '') || 'unknown';
    }

    createEditModal(component, type) {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Edit ${type} Component</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        ${this.getEditForm(type)}
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary" id="save-component">Save Changes</button>
                    </div>
                </div>
            </div>
        `;

        const saveBtn = modal.querySelector('#save-component');
        saveBtn.addEventListener('click', () => {
            this.saveComponentChanges(component, modal);
        });

        return modal;
    }

    getEditForm(type) {
        const forms = {
            'title': `
                <div class="modern-input-group">
                    <input type="text" class="modern-input" id="component-title" placeholder=" ">
                    <label class="modern-label">Title</label>
                </div>
                <div class="modern-input-group">
                    <textarea class="modern-input" id="component-subtitle" placeholder=" " rows="3"></textarea>
                    <label class="modern-label">Subtitle</label>
                </div>
            `,
            'description': `
                <div class="modern-input-group">
                    <textarea class="modern-input" id="component-description" placeholder=" " rows="5"></textarea>
                    <label class="modern-label">Description</label>
                </div>
            `,
            // Add more forms for other component types...
        };

        return forms[type] || '<p>No edit form available for this component type.</p>';
    }

    saveComponentChanges(component, modal) {
        // Save logic here
        const modalInstance = bootstrap.Modal.getInstance(modal);
        modalInstance.hide();
        window.modernUI.notifications.show('Component updated!', 'success');
    }

    setupLayoutSwitcher() {
        document.querySelectorAll('[data-layout]').forEach(btn => {
            btn.addEventListener('click', () => {
                const layout = btn.dataset.layout;
                this.switchLayout(layout);
            });
        });
    }

    switchLayout(layout) {
        const canvas = document.querySelector('.event-builder-canvas');
        if (canvas) {
            canvas.className = `event-builder-canvas layout-${layout}`;
            this.currentLayout = layout;
            window.modernUI.notifications.show(`Layout changed to ${layout}`, 'info');
        }
    }

    getDefaultComponentData(type) {
        const defaults = {
            'title-section': { title: 'Event Title', subtitle: '' },
            'description': { content: '' },
            'date-time': { startDate: '', endDate: '', timezone: 'UTC' },
            'location': { venue: '', address: '', virtualLink: '' },
            'registration': { maxAttendees: 0, price: 0, currency: 'USD' },
            'speakers': { speakers: [] },
            'agenda': { items: [] },
            'sponsors': { sponsors: [] }
        };

        return defaults[type] || {};
    }
}

class NotificationSystem {
    constructor() {
        this.container = this.createContainer();
        this.queue = [];
    }

    createContainer() {
        let container = document.querySelector('.notification-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'notification-container';
            document.body.appendChild(container);
        }
        return container;
    }

    show(message, type = 'info', duration = 5000) {
        const notification = this.createNotification(message, type);
        this.container.appendChild(notification);

        // Auto remove after duration
        setTimeout(() => {
            this.remove(notification);
        }, duration);

        // Allow manual close
        const closeBtn = notification.querySelector('.notification-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                this.remove(notification);
            });
        }
    }

    createNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        
        const icon = this.getIcon(type);
        notification.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px;">
                <span>${icon}</span>
                <span style="flex: 1;">${message}</span>
                <button class="notification-close" style="background: none; border: none; font-size: 18px; cursor: pointer; opacity: 0.7;">&times;</button>
            </div>
        `;

        return notification;
    }

    getIcon(type) {
        const icons = {
            'success': '✅',
            'error': '❌',
            'warning': '⚠️',
            'info': 'ℹ️'
        };
        return icons[type] || icons['info'];
    }

    remove(notification) {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }
}

class AISuggestionEngine {
    constructor() {
        this.setupAISuggestions();
    }

    setupAISuggestions() {
        const aiPanel = document.querySelector('.ai-suggestions');
        if (aiPanel) {
            this.loadSuggestions();
        }
    }

    async loadSuggestions() {
        // Simulate AI suggestions loading
        const suggestions = await this.generateSuggestions();
        this.renderSuggestions(suggestions);
    }

    async generateSuggestions() {
        // Simulate API call to AI service
        return new Promise(resolve => {
            setTimeout(() => {
                resolve([
                    {
                        type: 'layout',
                        title: 'Modern Layout Suggestion',
                        description: 'Based on your event type, consider using a hero section with registration CTA',
                        confidence: 0.85
                    },
                    {
                        type: 'content',
                        title: 'Content Enhancement',
                        description: 'Add speaker bios and testimonials to increase engagement',
                        confidence: 0.72
                    },
                    {
                        type: 'timing',
                        title: 'Optimal Timing',
                        description: 'Tuesday 2PM shows highest attendance for this event category',
                        confidence: 0.91
                    }
                ]);
            }, 1000);
        });
    }

    renderSuggestions(suggestions) {
        const container = document.querySelector('.ai-suggestions');
        if (!container) return;

        const suggestionsHTML = suggestions.map(suggestion => `
            <div class="ai-suggestion-item" data-suggestion-type="${suggestion.type}">
                <h6>${suggestion.title}</h6>
                <p>${suggestion.description}</p>
                <small>Confidence: ${Math.round(suggestion.confidence * 100)}%</small>
            </div>
        `).join('');

        container.innerHTML = `
            <h5>🤖 AI Suggestions</h5>
            ${suggestionsHTML}
        `;

        // Add click handlers
        container.querySelectorAll('.ai-suggestion-item').forEach(item => {
            item.addEventListener('click', () => {
                this.applySuggestion(item.dataset.suggestionType);
            });
        });
    }

    applySuggestion(type) {
        // Apply AI suggestion based on type
        window.modernUI.notifications.show(`Applied ${type} suggestion!`, 'success');
    }
}

class TeamFormationUI {
    constructor() {
        this.participants = [];
        this.teams = [];
        this.init();
    }

    init() {
        this.setupTeamFormation();
        this.loadParticipants();
    }

    setupTeamFormation() {
        const formationArea = document.querySelector('.team-formation-area');
        if (!formationArea) return;

        this.setupDragAndDropForTeams();
        this.setupTeamCreation();
    }

    setupDragAndDropForTeams() {
        // Setup drag and drop for participant cards
        document.querySelectorAll('.participant-card').forEach(card => {
            card.addEventListener('dragstart', (e) => {
                e.dataTransfer.setData('text/plain', card.dataset.userId);
            });
        });

        // Setup drop zones for teams
        document.querySelectorAll('.team-container').forEach(container => {
            container.addEventListener('dragover', (e) => {
                e.preventDefault();
                container.classList.add('drag-over');
            });

            container.addEventListener('dragleave', () => {
                container.classList.remove('drag-over');
            });

            container.addEventListener('drop', (e) => {
                e.preventDefault();
                const userId = e.dataTransfer.getData('text/plain');
                const teamId = container.dataset.teamId;
                
                this.addUserToTeam(userId, teamId);
                container.classList.remove('drag-over');
            });
        });
    }

    setupTeamCreation() {
        const createTeamBtn = document.querySelector('#create-team-btn');
        if (createTeamBtn) {
            createTeamBtn.addEventListener('click', () => {
                this.createNewTeam();
            });
        }

        const autoFormTeamsBtn = document.querySelector('#auto-form-teams');
        if (autoFormTeamsBtn) {
            autoFormTeamsBtn.addEventListener('click', () => {
                this.autoFormTeams();
            });
        }
    }

    addUserToTeam(userId, teamId) {
        // Add user to team logic
        const participantCard = document.querySelector(`[data-user-id="${userId}"]`);
        const teamContainer = document.querySelector(`[data-team-id="${teamId}"]`);
        
        if (participantCard && teamContainer) {
            const clone = participantCard.cloneNode(true);
            clone.style.transform = 'scale(0.9)';
            teamContainer.appendChild(clone);
            
            teamContainer.classList.add('filled');
            participantCard.style.opacity = '0.5';
            
            window.modernUI.notifications.show('User added to team!', 'success');
        }
    }

    createNewTeam() {
        const teamId = `team-${Date.now()}`;
        const teamsContainer = document.querySelector('.teams-container');
        
        if (teamsContainer) {
            const teamElement = document.createElement('div');
            teamElement.className = 'team-container';
            teamElement.dataset.teamId = teamId;
            teamElement.innerHTML = `
                <h6>Team ${this.teams.length + 1}</h6>
                <p>Drag participants here</p>
            `;
            
            teamsContainer.appendChild(teamElement);
            this.setupDragAndDropForTeams();
            
            window.modernUI.notifications.show('New team created!', 'success');
        }
    }

    async autoFormTeams() {
        try {
            const response = await fetch('/api/auto-form-teams', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    eventId: this.getEventId(),
                    maxTeamSize: this.getMaxTeamSize()
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.renderAutoFormedTeams(data.teams);
                window.modernUI.notifications.show('Teams formed automatically!', 'success');
            } else {
                window.modernUI.notifications.show('Error forming teams', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            window.modernUI.notifications.show('Error forming teams', 'error');
        }
    }

    renderAutoFormedTeams(teams) {
        const teamsContainer = document.querySelector('.teams-container');
        if (!teamsContainer) return;

        // Clear existing teams
        teamsContainer.innerHTML = '';

        teams.forEach((team, index) => {
            const teamElement = document.createElement('div');
            teamElement.className = 'team-container filled';
            teamElement.dataset.teamId = `auto-team-${index}`;
            
            const membersHTML = team.members.map(member => `
                <div class="participant-card">
                    <div class="participant-avatar">${member.name.charAt(0)}</div>
                    <div>
                        <strong>${member.name}</strong>
                        <small>${member.skills.join(', ')}</small>
                    </div>
                </div>
            `).join('');

            teamElement.innerHTML = `
                <h6>Team ${index + 1} (Score: ${Math.round(team.compatibility * 100)}%)</h6>
                ${membersHTML}
            `;

            teamsContainer.appendChild(teamElement);
        });
    }

    getEventId() {
        return document.querySelector('[data-event-id]')?.dataset.eventId || null;
    }

    getMaxTeamSize() {
        return parseInt(document.querySelector('#max-team-size')?.value) || 5;
    }

    async loadParticipants() {
        // Load participants for team formation
        try {
            const eventId = this.getEventId();
            if (!eventId) return;

            const response = await fetch(`/api/events/${eventId}/participants`);
            const data = await response.json();
            
            this.participants = data.participants;
            this.renderParticipants();
        } catch (error) {
            console.error('Error loading participants:', error);
        }
    }

    renderParticipants() {
        const container = document.querySelector('.participants-pool');
        if (!container) return;

        const participantsHTML = this.participants.map(participant => `
            <div class="participant-card" data-user-id="${participant.id}" draggable="true">
                <div class="participant-avatar">${participant.name.charAt(0)}</div>
                <div>
                    <strong>${participant.name}</strong>
                    <small>${participant.skills?.join(', ') || 'No skills listed'}</small>
                </div>
            </div>
        `).join('');

        container.innerHTML = participantsHTML;
        this.setupDragAndDropForTeams();
    }
}

// Global search functionality
class GlobalSearch {
    constructor() {
        this.setupSearch();
    }

    setupSearch() {
        const searchInput = document.querySelector('#global-search');
        if (!searchInput) return;

        let debounceTimer;
        
        searchInput.addEventListener('input', (e) => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                this.performSearch(e.target.value);
            }, 300);
        });

        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeSearchResults();
            }
        });
    }

    async performSearch(query) {
        if (query.length < 2) {
            this.closeSearchResults();
            return;
        }

        try {
            const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
            const results = await response.json();
            this.displaySearchResults(results);
        } catch (error) {
            console.error('Search error:', error);
        }
    }

    displaySearchResults(results) {
        let resultsContainer = document.querySelector('.search-results');
        
        if (!resultsContainer) {
            resultsContainer = document.createElement('div');
            resultsContainer.className = 'search-results';
            resultsContainer.style.cssText = `
                position: absolute;
                top: 100%;
                left: 0;
                right: 0;
                background: var(--bg-card);
                border: 1px solid var(--border-color);
                border-radius: var(--border-radius-md);
                box-shadow: var(--shadow-lg);
                max-height: 300px;
                overflow-y: auto;
                z-index: 1000;
            `;
            
            const searchInput = document.querySelector('#global-search');
            searchInput.parentElement.style.position = 'relative';
            searchInput.parentElement.appendChild(resultsContainer);
        }

        if (results.length === 0) {
            resultsContainer.innerHTML = '<div class="p-3">No results found</div>';
        } else {
            const resultsHTML = results.map(result => `
                <div class="search-result-item p-3 border-bottom" data-url="${result.url}">
                    <strong>${result.title}</strong>
                    <p class="mb-0 small text-muted">${result.description}</p>
                </div>
            `).join('');
            
            resultsContainer.innerHTML = resultsHTML;
            
            // Add click handlers
            resultsContainer.querySelectorAll('.search-result-item').forEach(item => {
                item.addEventListener('click', () => {
                    window.location.href = item.dataset.url;
                });
            });
        }

        resultsContainer.style.display = 'block';
    }

    closeSearchResults() {
        const resultsContainer = document.querySelector('.search-results');
        if (resultsContainer) {
            resultsContainer.style.display = 'none';
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.modernUI = new ModernUI();
    window.globalSearch = new GlobalSearch();
    
    // Add some global CSS animations
    const style = document.createElement('style');
    style.textContent = `
        @keyframes fadeOut {
            from { opacity: 1; transform: scale(1); }
            to { opacity: 0; transform: scale(0.8); }
        }
        
        @keyframes slideOut {
            from { transform: translateX(0); opacity: 1; }
            to { transform: translateX(100%); opacity: 0; }
        }
        
        .search-result-item {
            cursor: pointer;
            transition: background-color 0.2s;
        }
        
        .search-result-item:hover {
            background-color: var(--bg-light);
        }
    `;
    
    document.head.appendChild(style);
});

// Export classes for use in other modules
window.ModernUI = ModernUI;
window.EventBuilder = EventBuilder;
window.NotificationSystem = NotificationSystem;
window.AISuggestionEngine = AISuggestionEngine;
window.TeamFormationUI = TeamFormationUI;