// Profile.js - JavaScript for profile functionality

document.addEventListener('DOMContentLoaded', function() {
  // Profile image preview
  const profileImageInput = document.getElementById('profile_image');
  const profileImagePreview = document.getElementById('profile-image-preview');
  
  if (profileImageInput && profileImagePreview) {
    profileImageInput.addEventListener('input', function() {
      const imageUrl = this.value.trim();
      if (imageUrl) {
        profileImagePreview.src = imageUrl;
        profileImagePreview.style.display = 'block';
      } else {
        profileImagePreview.src = '';
        profileImagePreview.style.display = 'none';
      }
    });
  }

  // Password visibility toggle
  const togglePasswordButtons = document.querySelectorAll('.toggle-password');
  if (togglePasswordButtons.length > 0) {
    togglePasswordButtons.forEach(button => {
      button.addEventListener('click', function() {
        const targetId = this.getAttribute('data-target');
        const passwordField = document.getElementById(targetId);
        
        if (passwordField.type === 'password') {
          passwordField.type = 'text';
          this.innerHTML = '<i class="fas fa-eye-slash"></i>';
        } else {
          passwordField.type = 'password';
          this.innerHTML = '<i class="fas fa-eye"></i>';
        }
      });
    });
  }

  // Password strength meter
  const newPasswordInput = document.getElementById('new_password');
  const passwordStrengthMeter = document.getElementById('password-strength-meter');
  const passwordStrengthText = document.getElementById('password-strength-text');
  
  if (newPasswordInput && passwordStrengthMeter && passwordStrengthText) {
    newPasswordInput.addEventListener('input', function() {
      const password = this.value;
      let strength = 0;
      let message = '';
      
      if (password.length === 0) {
        strength = 0;
        message = '';
      } else if (password.length < 6) {
        strength = 1;
        message = 'Weak';
      } else if (password.length < 10) {
        strength = 2;
        message = 'Medium';
      } else {
        strength = 3;
        
        // Check for complexity
        const hasUppercase = /[A-Z]/.test(password);
        const hasLowercase = /[a-z]/.test(password);
        const hasNumbers = /\d/.test(password);
        const hasSpecialChars = /[!@#$%^&*(),.?":{}|<>]/.test(password);
        
        const complexity = [hasUppercase, hasLowercase, hasNumbers, hasSpecialChars].filter(Boolean).length;
        
        if (complexity >= 3) {
          strength = 4;
          message = 'Strong';
        } else {
          message = 'Good';
        }
      }
      
      // Update strength indicator
      passwordStrengthMeter.value = strength;
      passwordStrengthText.textContent = message;
      
      // Set color based on strength
      let color = '';
      switch (strength) {
        case 1:
          color = '#ff4d4d'; // Red
          break;
        case 2:
          color = '#ffa64d'; // Orange
          break;
        case 3:
          color = '#4da6ff'; // Blue
          break;
        case 4:
          color = '#4dff4d'; // Green
          break;
        default:
          color = '#e6e6e6'; // Gray
      }
      
      passwordStrengthMeter.style.setProperty('--strength-color', color);
    });
  }

  // Profile statistics charts
  if (document.getElementById('eventCategoriesChart')) {
    initProfileCharts();
  }
});

// Function to initialize profile statistics charts
function initProfileCharts() {
  // Only initialize for attendee profile with chart
  const eventCategoriesChartCanvas = document.getElementById('eventCategoriesChart');
  if (!eventCategoriesChartCanvas) return;
  
  // Get category data from data attribute
  const categoriesAttr = eventCategoriesChartCanvas.getAttribute('data-categories');
  let categories = {};
  
  try {
    categories = JSON.parse(categoriesAttr || '{}');
  } catch (e) {
    console.error('Error parsing categories data:', e);
  }
  
  const labels = Object.keys(categories);
  const data = Object.values(categories);
  
  // Use placeholder if no data
  if (labels.length === 0) {
    labels.push('No events yet');
    data.push(1);
  }
  
  // Generate colors for each category
  const backgroundColors = [
    'rgba(0, 188, 212, 0.7)',   // Cyan (primary for attendees)
    'rgba(255, 87, 34, 0.7)',   // Orange (secondary)
    'rgba(76, 175, 80, 0.7)',   // Green
    'rgba(255, 152, 0, 0.7)',   // Amber
    'rgba(33, 150, 243, 0.7)',   // Blue
    'rgba(156, 39, 176, 0.7)',   // Purple
    'rgba(233, 30, 99, 0.7)'     // Pink
  ];
  
  const chart = new Chart(eventCategoriesChartCanvas, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: data,
        backgroundColor: backgroundColors.slice(0, labels.length),
        borderColor: 'white',
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          position: 'right'
        },
        title: {
          display: true,
          text: 'Event Categories',
          font: {
            size: 16,
            weight: 'bold'
          }
        }
      }
    }
  });
  
  // Upcoming vs Past Events chart (if present)
  const eventsDistributionCanvas = document.getElementById('eventsDistributionChart');
  if (eventsDistributionCanvas) {
    const upcomingTickets = parseInt(eventsDistributionCanvas.getAttribute('data-upcoming') || 0);
    const pastTickets = parseInt(eventsDistributionCanvas.getAttribute('data-past') || 0);
    
    const chart = new Chart(eventsDistributionCanvas, {
      type: 'pie',
      data: {
        labels: ['Upcoming Events', 'Past Events'],
        datasets: [{
          data: [upcomingTickets, pastTickets],
          backgroundColor: [
            'rgba(76, 175, 80, 0.7)', // Green for upcoming
            'rgba(158, 158, 158, 0.7)' // Gray for past
          ],
          borderColor: 'white',
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: {
            position: 'bottom'
          },
          title: {
            display: true,
            text: 'Upcoming vs Past Events',
            font: {
              size: 16,
              weight: 'bold'
            }
          }
        }
      }
    });
  }
}
