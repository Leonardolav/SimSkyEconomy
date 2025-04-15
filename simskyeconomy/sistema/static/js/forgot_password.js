document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('forgotPasswordForm');
    const emailVerificationModal = new bootstrap.Modal(document.getElementById('emailVerificationModal'));
    const modalBody = document.getElementById('email-verification-modal-body');
    const modalTitle = document.getElementById('emailVerificationModalLabel');
    const resetSuccessModal = new bootstrap.Modal(document.getElementById('resetSuccessModal'));
    const forgotPasswordModal = new bootstrap.Modal(document.getElementById('forgotPasswordModal'));

    if (form) {
        form.addEventListener('submit', (event) => {
            event.preventDefault();

            fetch(form.action, {
                method: 'POST',
                body: new FormData(form),
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.account_locked) {
                    // Close the forgotPasswordModal before opening the emailVerificationModal
                    const forgotPasswordModalInstance = bootstrap.Modal.getInstance(document.getElementById('forgotPasswordModal'));
                    forgotPasswordModalInstance.hide();

                    // Display the account locked message in the emailVerificationModal
                    modalTitle.textContent = 'Account Locked';
                    modalBody.innerHTML = data.message; // Message: "Your account is locked due to multiple failed login attempts..."

                    // Add event listener to reopen forgotPasswordModal when emailVerificationModal is closed
                    const modalElement = document.getElementById('emailVerificationModal');
                    const okButton = modalElement.querySelector('.btn-primary[data-bs-dismiss="modal"]');
                    const closeButton = modalElement.querySelector('.btn-close');

                    // Remove any existing listeners to avoid duplicates
                    const newOkButton = okButton.cloneNode(true);
                    okButton.parentNode.replaceChild(newOkButton, okButton);
                    const newCloseButton = closeButton.cloneNode(true);
                    closeButton.parentNode.replaceChild(newCloseButton, closeButton);

                    // Add listeners for OK button and X button
                    newOkButton.addEventListener('click', () => {
                        emailVerificationModal.hide();
                        forgotPasswordModal.show();
                    });

                    newCloseButton.addEventListener('click', () => {
                        emailVerificationModal.hide();
                        forgotPasswordModal.show();
                    });

                    emailVerificationModal.show();
                } else if (data.success) {
                    // Close the forgotPasswordModal and show the resetSuccessModal
                    const forgotPasswordModalInstance = bootstrap.Modal.getInstance(document.getElementById('forgotPasswordModal'));
                    forgotPasswordModalInstance.hide();
                    resetSuccessModal.show();
                } else {
                    // Display error message in the forgotPasswordModal
                    const errorDiv = document.createElement('div');
                    errorDiv.className = 'alert alert-danger';
                    errorDiv.textContent = data.error || 'An error occurred. Please try again.';
                    form.prepend(errorDiv);
                }
            })
            .catch(error => {
                console.error('Error during password reset:', error);
                const errorDiv = document.createElement('div');
                errorDiv.className = 'alert alert-danger';
                errorDiv.textContent = 'An error occurred during password reset. Please try again.';
                form.prepend(errorDiv);
            });
        });
    }
});