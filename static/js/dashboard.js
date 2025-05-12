// Dashboard.js - JavaScript for dashboard functionality

document.addEventListener('DOMContentLoaded', function() {
  // Organizer dashboard charts
  initEventStatsChart();
  initAttendeeGrowthChart();
  initCategoryDistributionChart();
  
  // Initialize counters animation
  animateCounters();
});

// Function to initialize event statistics chart
function initEventStatsChart() {
  const eventStatsCanvas = document.getElementById('eventStatsChart');
  if (!eventStatsCanvas) return;
  
  // Get data from the data attributes
  const totalEvents = parseInt(eventStatsCanvas.getAttribute('data-total') || 0);
  const upcomingEvents = parseInt(eventStatsCanvas.getAttribute('data-upcoming') || 0);
  const ongoingEvents = parseInt(eventStatsCanvas.getAttribute('data-ongoing') || 0);
  const pastEvents = parseInt(eventStatsCanvas.getAttribute('data-past') || 0);
  
  const chart = new Chart(eventStatsCanvas, {
    type: 'bar',
    data: {
      labels: ['Total', 'Upcoming', 'Ongoing', 'Past'],
      datasets: [{
        label: 'Events Count',
        data: [totalEvents, upcomingEvents, ongoingEvents, pastEvents],
        backgroundColor: [
          'rgba(93, 63, 211, 0.7)',  // Primary color (purple)
          'rgba(76, 175, 80, 0.7)',  // Success color (green)
          'rgba(33, 150, 243, 0.7)', // Info color (blue)
          'rgba(158, 158, 158, 0.7)' // Gray for past events
        ],
        borderColor: [
          'rgba(93, 63, 211, 1)',
          'rgba(76, 175, 80, 1)',
          'rgba(33, 150, 243, 1)',
          'rgba(158, 158, 158, 1)'
        ],
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            precision: 0
          }
        }
      },
      plugins: {
        legend: {
          display: false
        },
        title: {
          display: true,
          text: 'Event Statistics',
          font: {
            size: 16,
            weight: 'bold'
          }
        }
      }
    }
  });
}

// Function to initialize attendee growth chart
function initAttendeeGrowthChart() {
  const attendeeGrowthCanvas = document.getElementById('attendeeGrowthChart');
  if (!attendeeGrowthCanvas) return;
  
  // This would typically come from the server with real data
  // For now, we'll simulate data from the data attributes
  
  // Get the total tickets attribute value
  const totalTickets = parseInt(attendeeGrowthCanvas.getAttribute('data-total-tickets') || 0);
  
  // Create simulated monthly data for the last 6 months
  const labels = [];
  const data = [];
  
  const date = new Date();
  
  // If we have no tickets, create a blank chart
  if (totalTickets === 0) {
    for (let i = 5; i >= 0; i--) {
      const month = new Date(date.getFullYear(), date.getMonth() - i, 1);
      labels.push(month.toLocaleDateString('en-US', { month: 'short' }));
      data.push(0);
    }
  } else {
    // Distribute total tickets over the last 6 months with a growth trend
    let remainingTickets = totalTickets;
    
    // Create a growth pattern (lower in earlier months, higher in recent months)
    const growthPattern = [0.05, 0.10, 0.15, 0.20, 0.25, 0.25];
    
    for (let i = 5; i >= 0; i--) {
      const month = new Date(date.getFullYear(), date.getMonth() - i, 1);
      labels.push(month.toLocaleDateString('en-US', { month: 'short' }));
      
      // Calculate tickets for this month
      const monthTickets = Math.round(totalTickets * growthPattern[5-i]);
      data.push(monthTickets);
    }
  }
  
  const chart = new Chart(attendeeGrowthCanvas, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Attendees',
        data: data,
        fill: true,
        backgroundColor: 'rgba(93, 63, 211, 0.2)',
        borderColor: 'rgba(93, 63, 211, 1)',
        tension: 0.3,
        pointBackgroundColor: 'rgba(93, 63, 211, 1)',
        pointBorderColor: '#fff',
        pointRadius: 4
      }]
    },
    options: {
      responsive: true,
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            precision: 0
          }
        }
      },
      plugins: {
        title: {
          display: true,
          text: 'Attendee Growth (Last 6 Months)',
          font: {
            size: 16,
            weight: 'bold'
          }
        }
      }
    }
  });
}

// Function to initialize category distribution chart
function initCategoryDistributionChart() {
  const categoryChartCanvas = document.getElementById('categoryDistributionChart');
  if (!categoryChartCanvas) return;
  
  // Get data from the element's data attributes
  const categories = categoryChartCanvas.getAttribute('data-categories');
  let categoryData = {};
  
  if (categories) {
    try {
      categoryData = JSON.parse(categories);
    } catch (e) {
      console.error('Error parsing category data:', e);
      categoryData = {};
    }
  }
  
  const labels = Object.keys(categoryData);
  const data = Object.values(categoryData);
  
  // If no data, use placeholder data
  if (labels.length === 0) {
    labels.push('No Data');
    data.push(1);
  }
  
  // Generate colors for each category
  const backgroundColors = [
    'rgba(93, 63, 211, 0.7)',   // Primary purple
    'rgba(255, 87, 34, 0.7)',   // Secondary orange
    'rgba(0, 188, 212, 0.7)',   // Cyan
    'rgba(76, 175, 80, 0.7)',   // Green
    'rgba(255, 152, 0, 0.7)',   // Amber
    'rgba(33, 150, 243, 0.7)',  // Blue
    'rgba(156, 39, 176, 0.7)'   // Purple
  ];
  
  // Duplicate colors if there are more categories than colors
  while (backgroundColors.length < labels.length) {
    backgroundColors.push(...backgroundColors);
  }
  
  const chart = new Chart(categoryChartCanvas, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: data,
        backgroundColor: backgroundColors.slice(0, labels.length),
        borderColor: '#ffffff',
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      plugins: {
        title: {
          display: true,
          text: 'Event Categories Distribution',
          font: {
            size: 16,
            weight: 'bold'
          }
        },
        legend: {
          position: 'right'
        }
      }
    }
  });
}

// Animate counters with counting effect
function animateCounters() {
  const counters = document.querySelectorAll('.counter-value');
  
  counters.forEach(counter => {
    const target = parseInt(counter.getAttribute('data-target'));
    const duration = 1500; // Animation duration in milliseconds
    const start = 0;
    const startTime = performance.now();
    
    function updateCounter(currentTime) {
      const elapsedTime = currentTime - startTime;
      const progress = Math.min(elapsedTime / duration, 1);
      
      // Easing function for smoother animation
      const easedProgress = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
      
      const currentValue = Math.floor(start + (target - start) * easedProgress);
      counter.textContent = new Intl.NumberFormat().format(currentValue);
      
      if (progress < 1) {
        requestAnimationFrame(updateCounter);
      }
    }
    
    requestAnimationFrame(updateCounter);
  });
}
