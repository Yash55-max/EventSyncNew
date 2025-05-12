// Tickets.js - JavaScript for ticket-related functions

document.addEventListener('DOMContentLoaded', function() {
  // Ticket tabs functionality
  const ticketTabs = document.querySelectorAll('.ticket-tab');
  if (ticketTabs.length > 0) {
    ticketTabs.forEach(tab => {
      tab.addEventListener('click', function() {
        // Remove active class from all tabs
        ticketTabs.forEach(t => t.classList.remove('active'));
        
        // Add active class to clicked tab
        this.classList.add('active');
        
        // Show corresponding ticket section
        const tabType = this.getAttribute('data-tab');
        const ticketSections = document.querySelectorAll('.ticket-section');
        
        ticketSections.forEach(section => {
          if (section.id === `${tabType}-tickets`) {
            section.style.display = 'block';
          } else {
            section.style.display = 'none';
          }
        });
      });
    });
  }

  // Ticket cancellation confirmation
  const cancelTicketBtns = document.querySelectorAll('.cancel-ticket-btn');
  if (cancelTicketBtns.length > 0) {
    cancelTicketBtns.forEach(btn => {
      btn.addEventListener('click', function(e) {
        e.preventDefault();
        
        const ticketId = this.getAttribute('data-ticket-id');
        const eventTitle = this.getAttribute('data-event-title');
        
        // Set modal content
        const modal = document.getElementById('cancelTicketModal');
        if (modal) {
          const modalTitle = modal.querySelector('.modal-title');
          const modalBody = modal.querySelector('.modal-body');
          const confirmBtn = modal.querySelector('.btn-danger');
          
          if (modalTitle && modalBody && confirmBtn) {
            modalTitle.textContent = 'Cancel Ticket';
            modalBody.textContent = `Are you sure you want to cancel your ticket for "${eventTitle}"? This action cannot be undone.`;
            confirmBtn.setAttribute('data-ticket-id', ticketId);
            
            // Create and show the modal
            const bootstrapModal = new bootstrap.Modal(modal);
            bootstrapModal.show();
          }
        }
      });
    });
    
    // Handle cancel confirmation
    const confirmCancelBtn = document.querySelector('#cancelTicketModal .btn-danger');
    if (confirmCancelBtn) {
      confirmCancelBtn.addEventListener('click', function() {
        const ticketId = this.getAttribute('data-ticket-id');
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/tickets/${ticketId}/cancel`;
        document.body.appendChild(form);
        form.submit();
      });
    }
  }

  // Ticket quantity input validation
  const ticketQuantityInput = document.getElementById('quantity');
  if (ticketQuantityInput) {
    ticketQuantityInput.addEventListener('input', function() {
      const maxAttendees = parseInt(this.getAttribute('data-max-attendees'));
      const currentAttendees = parseInt(this.getAttribute('data-current-attendees'));
      const quantity = parseInt(this.value);
      
      if (isNaN(quantity) || quantity < 1) {
        this.value = 1;
      } else if (maxAttendees > 0 && (currentAttendees + quantity) > maxAttendees) {
        // If the current quantity exceeds available tickets
        const availableTickets = maxAttendees - currentAttendees;
        this.value = availableTickets > 0 ? availableTickets : 1;
        
        // Show warning message
        const warningElement = document.getElementById('quantity-warning');
        if (warningElement) {
          warningElement.textContent = `Only ${availableTickets} tickets available for this event.`;
          warningElement.style.display = 'block';
        }
      } else {
        // Hide warning message if input is valid
        const warningElement = document.getElementById('quantity-warning');
        if (warningElement) {
          warningElement.style.display = 'none';
        }
      }
      
      // Update total price if price element exists
      const pricePerTicket = parseFloat(this.getAttribute('data-price'));
      const totalPriceElement = document.getElementById('total-price');
      
      if (!isNaN(pricePerTicket) && totalPriceElement) {
        const totalPrice = (quantity * pricePerTicket).toFixed(2);
        totalPriceElement.textContent = `$${totalPrice}`;
      }
    });
    
    // Trigger input event on page load to set initial values
    ticketQuantityInput.dispatchEvent(new Event('input'));
  }

  // Ticket print functionality
  const printTicketBtns = document.querySelectorAll('.print-ticket-btn');
  if (printTicketBtns.length > 0) {
    printTicketBtns.forEach(btn => {
      btn.addEventListener('click', function() {
        const ticketId = this.getAttribute('data-ticket-id');
        const ticketCard = document.getElementById(`ticket-${ticketId}`);
        
        if (ticketCard) {
          // Create a new window for printing
          const printWindow = window.open('', '_blank');
          
          // Create printable content
          const content = `
            <!DOCTYPE html>
            <html lang="en">
            <head>
              <meta charset="UTF-8">
              <meta name="viewport" content="width=device-width, initial-scale=1.0">
              <title>Event Ticket</title>
              <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css" rel="stylesheet">
              <style>
                body {
                  font-family: Arial, sans-serif;
                  padding: 20px;
                }
                .ticket {
                  border: 2px solid #333;
                  border-radius: 10px;
                  overflow: hidden;
                  max-width: 600px;
                  margin: 0 auto;
                }
                .ticket-header {
                  background-color: #00bcd4;
                  color: white;
                  padding: 15px;
                  text-align: center;
                }
                .ticket-body {
                  padding: 20px;
                }
                .ticket-info {
                  margin-bottom: 15px;
                }
                .ticket-label {
                  font-weight: bold;
                  margin-bottom: 5px;
                }
                .ticket-number {
                  font-family: monospace;
                  font-size: 18px;
                  text-align: center;
                  margin: 20px 0;
                  padding: 10px;
                  background-color: #f5f5f5;
                  border-radius: 5px;
                }
                .ticket-footer {
                  text-align: center;
                  font-size: 12px;
                  padding: 10px;
                  background-color: #f5f5f5;
                }
                @media print {
                  .no-print {
                    display: none;
                  }
                }
              </style>
            </head>
            <body>
              <div class="container">
                <div class="row mb-4">
                  <div class="col">
                    <button class="btn btn-primary no-print" onclick="window.print()">Print Ticket</button>
                    <button class="btn btn-secondary no-print" onclick="window.close()">Close</button>
                  </div>
                </div>
                
                <div class="ticket">
                  <div class="ticket-header">
                    <h2>${ticketCard.getAttribute('data-event-title')}</h2>
                  </div>
                  <div class="ticket-body">
                    <div class="ticket-info">
                      <div class="ticket-label">Date & Time:</div>
                      <div>${ticketCard.getAttribute('data-event-date')}</div>
                    </div>
                    <div class="ticket-info">
                      <div class="ticket-label">Location:</div>
                      <div>${ticketCard.getAttribute('data-event-location')}</div>
                    </div>
                    <div class="ticket-info">
                      <div class="ticket-label">Attendee:</div>
                      <div>${ticketCard.getAttribute('data-attendee-name')}</div>
                    </div>
                    <div class="ticket-number">
                      Ticket #: ${ticketCard.getAttribute('data-ticket-number')}
                    </div>
                  </div>
                  <div class="ticket-footer">
                    <p>This ticket is your proof of purchase. Please present it at the venue.</p>
                  </div>
                </div>
              </div>
            </body>
            </html>
          `;
          
          printWindow.document.open();
          printWindow.document.write(content);
          printWindow.document.close();
        }
      });
    });
  }

  // Check all tickets
  const checkAllTickets = document.getElementById('check-all-tickets');
  if (checkAllTickets) {
    checkAllTickets.addEventListener('change', function() {
      const ticketCheckboxes = document.querySelectorAll('.ticket-checkbox');
      ticketCheckboxes.forEach(checkbox => {
        checkbox.checked = this.checked;
      });
      
      // Enable/disable bulk actions button
      const bulkActionsBtn = document.getElementById('bulk-actions-btn');
      if (bulkActionsBtn) {
        bulkActionsBtn.disabled = !this.checked;
      }
    });
    
    // Check if any individual checkbox is checked
    const ticketCheckboxes = document.querySelectorAll('.ticket-checkbox');
    ticketCheckboxes.forEach(checkbox => {
      checkbox.addEventListener('change', function() {
        const bulkActionsBtn = document.getElementById('bulk-actions-btn');
        if (bulkActionsBtn) {
          const anyChecked = Array.from(ticketCheckboxes).some(cb => cb.checked);
          bulkActionsBtn.disabled = !anyChecked;
        }
      });
    });
  }
});
