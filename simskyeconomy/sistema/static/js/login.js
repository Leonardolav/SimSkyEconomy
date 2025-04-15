document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('login-form');
    const emailVerificationModal = new bootstrap.Modal(document.getElementById('emailVerificationModal'));
    const modalBody = document.getElementById('email-verification-modal-body');
    const modalTitle = document.getElementById('emailVerificationModalLabel');
    const errorContainer = document.createElement('div'); // Container for error messages
    const usernameField = document.getElementById('username');

    // Insert the error container above the Username/Email field
    errorContainer.id = 'login-error';
    errorContainer.className = 'alert alert-danger d-none mb-2'; // Add bottom margin to avoid overlap
    usernameField.parentElement.parentElement.insertBefore(errorContainer, usernameField.parentElement);

    if (typeof htmx === 'undefined') {
        console.error('HTMX not loaded correctly.');
        return;
    } else {
        console.log('HTMX loaded successfully.');
    }

    form.addEventListener('submit', (event) => {
        event.preventDefault();

        // Clear previous error messages
        errorContainer.classList.add('d-none');
        errorContainer.textContent = '';

        fetch(form.action, {
            method: 'POST',
            body: new FormData(form),
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (response.redirected) {
                window.location.href = response.url;
            } else if (response.ok) {
                return response.json();
            } else {
                throw new Error('Unexpected error: ' + response.status);
            }
        })
        .then(data => {
            if (data) {
                if (data.account_locked) {
                    // Display the account locked message in the modal
                    modalTitle.textContent = 'Account Locked';
                    modalBody.innerHTML = data.message; // Message: "Your account is locked due to multiple failed login attempts..."
                    emailVerificationModal.show();
                } else if (data.email_not_verified) {
                    modalTitle.textContent = 'Email Not Verified';
                    modalBody.innerHTML = data.message;
                    htmx.process(modalBody);
                    emailVerificationModal.show();
                } else if (!data.success) {
                    // Display error message above the Username/Email field
                    errorContainer.textContent = 'Invalid username, email, or password.'; // Already in English
                    errorContainer.classList.remove('d-none');
                }
            }
        })
        .catch(error => {
            console.error('Error during login:', error);
            errorContainer.textContent = 'An error occurred during login. Please try again.';
            errorContainer.classList.remove('d-none');
        });
    });

    document.body.addEventListener('htmx:beforeRequest', (event) => {
        console.log('HTMX before request:', event.detail);
    });

    document.body.addEventListener('htmx:afterSwap', (event) => {
        if (event.target.id === 'email-verification-modal-body') {
            console.log('HTMX after swap:', event.detail.xhr.responseText);
            emailVerificationModal.show();
        }
    });
});