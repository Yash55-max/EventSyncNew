// Main JavaScript for the Event Management System

document.addEventListener('DOMContentLoaded', function() {
  // Initialize tooltips
  const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  if (tooltips.length > 0) {
    tooltips.forEach(tooltip => {
      new bootstrap.Tooltip(tooltip);
    });
  }
  
  // Initialize popovers
  const popovers = document.querySelectorAll('[data-bs-toggle="popover"]');
  if (popovers.length > 0) {
    popovers.forEach(popover => {
      new bootstrap.Popover(popover);
    });
  }

  // Add animation classes to elements when they come into view
  const animatedElements = document.querySelectorAll('.animate-on-scroll');
  if (animatedElements.length > 0) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('animate-fade-in');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1 });

    animatedElements.forEach(element => {
      observer.observe(element);
    });
  }

  // Flash messages auto-close
  const flashMessages = document.querySelectorAll('.alert-dismissible');
  if (flashMessages.length > 0) {
    flashMessages.forEach(message => {
      setTimeout(() => {
        const closeButton = message.querySelector('.btn-close');
        if (closeButton) {
          closeButton.click();
        }
      }, 5000);
    });
  }

  // Toggle password visibility
  const passwordToggles = document.querySelectorAll('.toggle-password');
  if (passwordToggles.length > 0) {
    passwordToggles.forEach(toggle => {
      toggle.addEventListener('click', function() {
        const targetId = this.getAttribute('data-target');
        const target = document.getElementById(targetId);
        
        if (target.type === 'password') {
          target.type = 'text';
          this.innerHTML = '<i class="fas fa-eye-slash"></i>';
        } else {
          target.type = 'password';
          this.innerHTML = '<i class="fas fa-eye"></i>';
        }
      });
    });
  }

  // Navbar scroll behavior
  const navbar = document.querySelector('.navbar');
  if (navbar) {
    window.addEventListener('scroll', function() {
      if (window.scrollY > 50) {
        navbar.classList.add('navbar-scrolled', 'shadow-md');
      } else {
        navbar.classList.remove('navbar-scrolled', 'shadow-md');
      }
    });
  }

  // Format date inputs to show date and time correctly
  const dateInputs = document.querySelectorAll('input[type="datetime-local"]');
  if (dateInputs.length > 0) {
    dateInputs.forEach(input => {
      if (!input.value && input.getAttribute('placeholder') === 'Now') {
        const now = new Date();
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        
        input.value = `${year}-${month}-${day}T${hours}:${minutes}`;
      }
    });
  }

  // Handle modal confirm actions
  const confirmModals = document.querySelectorAll('.confirm-modal');
  if (confirmModals.length > 0) {
    confirmModals.forEach(modal => {
      const confirmBtn = modal.querySelector('.btn-confirm');
      if (confirmBtn) {
        confirmBtn.addEventListener('click', function() {
          const targetForm = document.getElementById(this.getAttribute('data-target-form'));
          if (targetForm) {
            targetForm.submit();
          }
        });
      }
    });
  }

  // Handle category filter changes
  const categoryFilter = document.getElementById('category');
  if (categoryFilter) {
    categoryFilter.addEventListener('change', function() {
      const form = this.closest('form');
      if (form) {
        form.submit();
      }
    });
  }

  // Search form handling
  const searchForm = document.querySelector('.search-form');
  if (searchForm) {
    const searchInput = searchForm.querySelector('input[name="query"]');
    const clearSearch = searchForm.querySelector('.clear-search');
    
    if (searchInput && clearSearch) {
      // Show clear button if search input has value
      searchInput.addEventListener('input', function() {
        if (this.value.length > 0) {
          clearSearch.style.display = 'block';
        } else {
          clearSearch.style.display = 'none';
        }
      });
      
      // Trigger display on page load
      if (searchInput.value.length > 0) {
        clearSearch.style.display = 'block';
      }
      
      // Clear search input and submit form
      clearSearch.addEventListener('click', function() {
        searchInput.value = '';
        clearSearch.style.display = 'none';
        searchForm.submit();
      });
    }
  }

  // Image preview for event creation/editing
  const imageUrlInput = document.getElementById('image_url');
  const imagePreview = document.getElementById('image-preview');
  
  if (imageUrlInput && imagePreview) {
    imageUrlInput.addEventListener('input', function() {
      const imageUrl = this.value.trim();
      if (imageUrl) {
        imagePreview.innerHTML = `<img src="${imageUrl}" alt="Event image preview" class="img-fluid rounded">`;
        imagePreview.style.display = 'block';
      } else {
        imagePreview.innerHTML = '';
        imagePreview.style.display = 'none';
      }
    });
    
    // Trigger on page load
    if (imageUrlInput.value.trim()) {
      imagePreview.innerHTML = `<img src="${imageUrlInput.value.trim()}" alt="Event image preview" class="img-fluid rounded">`;
      imagePreview.style.display = 'block';
    }
  }

  // Countdown timer for upcoming events
  const countdownElements = document.querySelectorAll('.event-countdown');
  if (countdownElements.length > 0) {
    countdownElements.forEach(element => {
      const eventDate = new Date(element.getAttribute('data-date')).getTime();
      
      const updateCountdown = () => {
        const now = new Date().getTime();
        const distance = eventDate - now;
        
        if (distance < 0) {
          element.innerHTML = 'Event has started!';
          return;
        }
        
        const days = Math.floor(distance / (1000 * 60 * 60 * 24));
        const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((distance % (1000 * 60)) / 1000);
        
        let countdownText = '';
        
        if (days > 0) {
          countdownText += `${days}d `;
        }
        
        countdownText += `${hours}h ${minutes}m ${seconds}s`;
        element.innerHTML = countdownText;
      };
      
      updateCountdown();
      setInterval(updateCountdown, 1000);
    });
  }
});
