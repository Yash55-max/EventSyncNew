// Events.js - JavaScript for event-related functions

document.addEventListener('DOMContentLoaded', function() {
  // Confirmation modal for deleting events
  const deleteEventBtns = document.querySelectorAll('.delete-event-btn');
  if (deleteEventBtns.length > 0) {
    deleteEventBtns.forEach(btn => {
      btn.addEventListener('click', function(e) {
        e.preventDefault();
        
        const eventId = this.getAttribute('data-event-id');
        const eventTitle = this.getAttribute('data-event-title');
        
        // Set modal content
        const modal = document.getElementById('deleteEventModal');
        if (modal) {
          const modalTitle = modal.querySelector('.modal-title');
          const modalBody = modal.querySelector('.modal-body');
          const confirmBtn = modal.querySelector('.btn-danger');
          
          if (modalTitle && modalBody && confirmBtn) {
            modalTitle.textContent = 'Delete Event';
            modalBody.textContent = `Are you sure you want to delete "${eventTitle}"? This action cannot be undone.`;
            confirmBtn.setAttribute('data-event-id', eventId);
            
            // Create and show the modal
            const bootstrapModal = new bootstrap.Modal(modal);
            bootstrapModal.show();
          }
        }
      });
    });
    
    // Handle delete confirmation
    const confirmDeleteBtn = document.querySelector('#deleteEventModal .btn-danger');
    if (confirmDeleteBtn) {
      confirmDeleteBtn.addEventListener('click', function() {
        const eventId = this.getAttribute('data-event-id');
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/organizer/events/${eventId}/delete`;
        document.body.appendChild(form);
        form.submit();
      });
    }
  }

  // Filter events by status (for organizer event management)
  const eventStatusFilters = document.querySelectorAll('.event-status-filter');
  if (eventStatusFilters.length > 0) {
    eventStatusFilters.forEach(filter => {
      filter.addEventListener('click', function(e) {
        e.preventDefault();
        
        // Remove active class from all filters
        eventStatusFilters.forEach(f => f.classList.remove('active'));
        
        // Add active class to clicked filter
        this.classList.add('active');
        
        const status = this.getAttribute('data-status');
        const eventItems = document.querySelectorAll('.event-item');
        
        if (eventItems.length > 0) {
          eventItems.forEach(item => {
            if (status === 'all' || item.getAttribute('data-status') === status) {
              item.style.display = 'flex';
            } else {
              item.style.display = 'none';
            }
          });
        }
      });
    });
  }

  // Search events on the events page
  const eventSearchInput = document.getElementById('eventSearch');
  if (eventSearchInput) {
    eventSearchInput.addEventListener('input', function() {
      const searchValue = this.value.toLowerCase();
      const eventCards = document.querySelectorAll('.event-card');
      
      eventCards.forEach(card => {
        const title = card.querySelector('.event-card-title').textContent.toLowerCase();
        const description = card.querySelector('.event-card-text') ? 
          card.querySelector('.event-card-text').textContent.toLowerCase() : '';
        const category = card.querySelector('.event-card-category') ?
          card.querySelector('.event-card-category').textContent.toLowerCase() : '';
        
        if (title.includes(searchValue) || description.includes(searchValue) || category.includes(searchValue)) {
          card.style.display = 'flex';
        } else {
          card.style.display = 'none';
        }
      });
    });
  }

  // Date range filter for events
  const dateFromInput = document.getElementById('date_from');
  const dateToInput = document.getElementById('date_to');
  
  if (dateFromInput && dateToInput) {
    // Ensure date_to is always after date_from
    dateFromInput.addEventListener('change', function() {
      if (dateToInput.value && new Date(dateToInput.value) < new Date(this.value)) {
        dateToInput.value = this.value;
      }
      dateToInput.min = this.value;
    });
    
    // Initialize min attribute on page load
    if (dateFromInput.value) {
      dateToInput.min = dateFromInput.value;
    }
  }

  // Event capacity progress bars
  const capacityBars = document.querySelectorAll('.capacity-progress-bar');
  if (capacityBars.length > 0) {
    capacityBars.forEach(bar => {
      const percent = parseFloat(bar.getAttribute('data-percent'));
      bar.style.width = `${percent}%`;
      
      // Change color based on capacity
      if (percent >= 90) {
        bar.style.backgroundColor = '#f44336'; // Almost full - red
      } else if (percent >= 70) {
        bar.style.backgroundColor = '#ff9800'; // Getting full - orange
      }
    });
  }

  // Event card hover effect
  const eventCards = document.querySelectorAll('.event-card');
  if (eventCards.length > 0) {
    eventCards.forEach(card => {
      card.addEventListener('mouseenter', function() {
        this.classList.add('shadow-lg');
      });
      
      card.addEventListener('mouseleave', function() {
        this.classList.remove('shadow-lg');
      });
    });
  }

  // Event creation form validation
  const eventForm = document.querySelector('form.event-form');
  if (eventForm) {
    eventForm.addEventListener('submit', function(e) {
      const startDate = new Date(document.getElementById('start_date').value);
      const endDate = new Date(document.getElementById('end_date').value);
      const now = new Date();
      
      // Clear previous errors
      const errorMessages = document.querySelectorAll('.error-message');
      errorMessages.forEach(msg => msg.remove());
      
      let hasErrors = false;
      
      // Validate start date is in the future
      if (startDate < now) {
        e.preventDefault();
        hasErrors = true;
        const startDateInput = document.getElementById('start_date');
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message text-danger mt-1';
        errorDiv.textContent = 'Start date must be in the future';
        
        startDateInput.parentNode.appendChild(errorDiv);
      }
      
      // Validate end date is after start date
      if (endDate <= startDate) {
        e.preventDefault();
        hasErrors = true;
        const endDateInput = document.getElementById('end_date');
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message text-danger mt-1';
        errorDiv.textContent = 'End date must be after start date';
        
        endDateInput.parentNode.appendChild(errorDiv);
      }
      
      if (hasErrors) {
        // Show validation error alert
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger alert-dismissible fade show';
        alertDiv.role = 'alert';
        alertDiv.innerHTML = `
          <strong>Error!</strong> Please fix the form errors before submitting.
          <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        eventForm.prepend(alertDiv);
        
        // Scroll to top of form
        eventForm.scrollIntoView({ behavior: 'smooth' });
      }
    });
  }
});
