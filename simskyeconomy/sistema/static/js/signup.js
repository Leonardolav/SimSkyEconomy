document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('signup-form');
    const submitBtn = document.getElementById('submit-btn');
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirm_password');
    const usernameInput = document.getElementById('username');
    const emailInput = document.getElementById('email');
    const usernameFeedback = document.getElementById('username-feedback');
    const emailFeedback = document.getElementById('email-feedback');
    const requiredMessage = document.getElementById('required-message');
    const passwordMismatch = document.getElementById('password-mismatch');
    const inputs = form.querySelectorAll('input[required]');
    const modal = new bootstrap.Modal(document.getElementById('signupModal'));
    const modalTitle = document.getElementById('signupModalLabel');
    const modalBody = document.getElementById('signupModalBody');
    const modalOkBtn = document.getElementById('modalOkBtn');

    function validatePassword(password, username) {
        const hasUpperCase = /[A-Z]/.test(password);
        const hasMinLength = password.length >= 10;
        const hasSpecial = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password);
        const hasNumber = /\d/.test(password);
        const notSimilarToUsername = password.toLowerCase() !== username.toLowerCase() && 
                                   !password.toLowerCase().includes(username.toLowerCase());

        document.getElementById('uppercase').className = hasUpperCase ? 'valid' : 'invalid';
        document.getElementById('minlength').className = hasMinLength ? 'valid' : 'invalid';
        document.getElementById('special').className = hasSpecial ? 'valid' : 'invalid';
        document.getElementById('number').className = hasNumber ? 'valid' : 'invalid';
        document.getElementById('notusername').className = notSimilarToUsername ? 'valid' : 'invalid';

        return hasUpperCase && hasMinLength && hasSpecial && hasNumber && notSimilarToUsername;
    }

    function validateEmailFormat(email) {
        // Check if email contains a "+" sign
        return !email.includes('+');
    }

    function checkFormValidity() {
        const allFieldsFilled = Array.from(inputs).every(input => input.value.trim() !== '');
        const passwordValid = validatePassword(passwordInput.value, usernameInput.value);
        const passwordsMatch = passwordInput.value === confirmPasswordInput.value;
        const usernameFeedbackContent = usernameFeedback.textContent.replace(/['"]+/g, '').trim();
        const emailFeedbackContent = emailFeedback.textContent.replace(/['"]+/g, '').trim();
        const usernameTaken = usernameFeedbackContent === 'Username already in use';
        const emailTaken = emailFeedbackContent === 'Email already in use';
        const emailFormatValid = validateEmailFormat(emailInput.value);
        const emailInvalidFormat = !emailFormatValid; // True if email contains "+"

        if (!allFieldsFilled) {
            requiredMessage.style.display = 'block';
        } else {
            requiredMessage.style.display = 'none';
        }

        // Display email feedback based on existing content (updated by HTMX or blur event)
        if (emailFeedbackContent && emailFeedbackContent !== '') {
            emailFeedback.style.display = 'block';
        } else {
            emailFeedback.textContent = ''; // Clear the feedback if no error
            emailFeedback.style.display = 'none';
        }

        if (usernameFeedbackContent && usernameFeedbackContent !== '') {
            usernameFeedback.style.display = 'block';
        } else {
            usernameFeedback.style.display = 'none';
        }

        if (allFieldsFilled && !passwordsMatch) {
            passwordMismatch.style.display = 'block';
        } else {
            passwordMismatch.style.display = 'none';
        }

        // Disable the Sign Up button if email format is invalid, username/email is taken, or other conditions are not met
        submitBtn.disabled = !(allFieldsFilled && passwordValid && passwordsMatch && !usernameTaken && !emailTaken && emailFormatValid);
    }

    function showModal(title, body, redirectUrl) {
        modalTitle.textContent = title;
        modalBody.textContent = body;
        modal.show();
        modalOkBtn.onclick = () => {
            window.location.href = redirectUrl;
        };
    }

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
            if (data.success) {
                showModal('Great! Welcome to SimSky Economy', 'Your account was successfully created.', '/login/');
            } else {
                showModal('Sorry, we couldn’t create your account', `Please try again later\nError: ${data.error}`, '/signup/');
            }
        })
        .catch(error => {
            showModal('Sorry, we couldn’t create your account', `Please try again later\nError: ${error}`, '/signup/');
        });
    });

    // Add blur event listener to email to validate format after the user finishes typing
    emailInput.addEventListener('blur', () => {
        if (!validateEmailFormat(emailInput.value) && emailInput.value.trim() !== '') {
            emailFeedback.textContent = 'Invalid email format';
            emailFeedback.style.display = 'block';
        } else {
            // Trigger HTMX to check if email is already in use
            emailInput.dispatchEvent(new Event('change'));
        }
        checkFormValidity();
    });

    inputs.forEach(input => {
        if (input !== emailInput) { // Avoid duplicate listener for email
            input.addEventListener('input', checkFormValidity);
        }
    });

    document.addEventListener('htmx:afterSwap', (event) => {
        const target = event.target;
        if (target.id === 'username-feedback') {
            const data = JSON.parse(target.textContent);
            usernameFeedback.textContent = data.username_error || '';
            checkFormValidity();
        } else if (target.id === 'email-feedback') {
            const data = JSON.parse(target.textContent);
            // Only update email feedback with backend message if the format is valid
            if (!validateEmailFormat(emailInput.value) && emailInput.value.trim() !== '') {
                emailFeedback.textContent = 'Invalid email format';
                emailFeedback.style.display = 'block';
            } else {
                emailFeedback.textContent = data.email_error || '';
                emailFeedback.style.display = data.email_error ? 'block' : 'none';
            }
            checkFormValidity();
        }
    });

    checkFormValidity();
});