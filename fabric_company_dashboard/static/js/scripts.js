// Currently, most modal logic and search is inline in the HTML for simplicity.
// For larger projects, you would centralize more JS here.

// Example of a reusable function to toggle modal visibility
function toggleModal(modalId, show) {
    const modal = document.getElementById(modalId);
    if (show) {
        modal.classList.remove('hidden');
    } else {
        modal.classList.add('hidden');
    }
}

// You could refactor the open/close modal functions to use this:
// function openAddClientModal() { toggleModal('addClientModal', true); }
// function closeAddClientModal() { toggleModal('addClientModal', false); }

// The current setup directly manipulates classes which is fine for this scale.

// Function to format dates
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return new Date(dateString).toLocaleDateString(undefined, options);
}

// Function to format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-PK', { style: 'currency', currency: 'PKR' }).format(amount);
}

// Initialize any tooltips
document.addEventListener('DOMContentLoaded', function() {
    // Initialize any tooltips if needed
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});