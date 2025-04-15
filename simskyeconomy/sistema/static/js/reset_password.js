document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('reset-password-form');
    const submitBtn = document.getElementById('submit-btn');
    const newPasswordInput = document.getElementById('new_password');
    const confirmPasswordInput = document.getElementById('confirm_password');
    const passwordMismatch = document.getElementById('password-mismatch');
    const requiredMessage = document.getElementById('required-message');
    const inputs = form.querySelectorAll('input[required]');
    const modal = new bootstrap.Modal(document.getElementById('resetPasswordModal'));
    const modalTitle = document.getElementById('resetPasswordModalLabel');
    const modalBody = document.getElementById('resetPasswordModalBody');
    const modalOkBtn = document.getElementById('modalOkBtn');

    function validatePassword(password) {
        const hasUpperCase = /[A-Z]/.test(password);
        const hasMinLength = password.length >= 10;
        const hasSpecial = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password);
        const hasNumber = /\d/.test(password);

        document.getElementById('uppercase').className = hasUpperCase ? 'valid' : 'invalid';
        document.getElementById('minlength').className = hasMinLength ? 'valid' : 'invalid';
        document.getElementById('special').className = hasSpecial ? 'valid' : 'invalid';
        document.getElementById('number').className = hasNumber ? 'valid' : 'invalid';

        return hasUpperCase && hasMinLength && hasSpecial && hasNumber;
    }

    function checkFormValidity() {
        const allFieldsFilled = Array.from(inputs).every(input => input.value.trim() !== '');
        const passwordValid = validatePassword(newPasswordInput.value);
        const passwordsMatch = newPasswordInput.value === confirmPasswordInput.value;

        if (!allFieldsFilled) {
            requiredMessage.style.display = 'block';
        } else {
            requiredMessage.style.display = 'none';
        }

        if (allFieldsFilled && !passwordsMatch) {
            passwordMismatch.style.display = 'block';
        } else {
            passwordMismatch.style.display = 'none';
        }

        submitBtn.disabled = !(allFieldsFilled && passwordValid && passwordsMatch);
    }

    function showModal(title, body, redirectUrl) {
        modalTitle.textContent = title;
        modalBody.textContent = body;
        modal.show();
        modalOkBtn.onclick = () => {
            if (redirectUrl) {
                window.location.href = redirectUrl;
            }
        };
    }

    form.addEventListener('submit', (event) => {
        event.preventDefault();
        const formData = new FormData(form);

        fetch(window.location.pathname, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showModal('Success!', 'Your password has been successfully reset.', '/login/');
            } else {
                showModal('Error', `Unfortunately, we couldn\'t reset your password. Error: ${data.error}`, null);
            }
        })
        .catch(error => {
            showModal('Error', `Unfortunately, we couldn\'t reset your password. Error: ${error}`, null);
        });
    });

    inputs.forEach(input => {
        input.addEventListener('input', checkFormValidity);
    });

    checkFormValidity();
});