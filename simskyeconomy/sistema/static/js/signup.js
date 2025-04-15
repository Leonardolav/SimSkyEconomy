
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
        const hasUpperCase = /[A-Z]/.test(password); // Check for uppercase letters
        const hasMinLength = password.length >= 10; // Check for minimum length of 10 characters
        const hasSpecial = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password); // Check for special characters
        const hasNumber = /\d/.test(password); // Check for numbers
        const notSimilarToUsername = password.toLowerCase() !== username.toLowerCase() &&
                                   !password.toLowerCase().includes(username.toLowerCase());

        document.getElementById('uppercase').className = hasUpperCase ? 'valid' : 'invalid';
        document.getElementById('minlength').className = hasMinLength ? 'valid' : 'invalid';
        document.getElementById('special').className = hasSpecial ? 'valid' : 'invalid';
        document.getElementById('number').className = hasNumber ? 'valid' : 'invalid';
        document.getElementById('notusername').className = notSimilarToUsername ? 'valid' : 'invalid'; // Check if the password is not similar to the username

        return hasUpperCase && hasMinLength && hasSpecial && hasNumber && notSimilarToUsername;
    }// Returns true if the password meets all the requirements

    function validateEmailFormat(email) {
        // Check if email contains a "+" sign
        return !email.includes('+');
    }

    function checkFormValidity() {
        const allFieldsFilled = Array.from(inputs).every(input => input.value.trim() !== '');
        const passwordValid = validatePassword(passwordInput.value, usernameInput.value); // Validate the password based on the defined requirements
        const passwordsMatch = passwordInput.value === confirmPasswordInput.value; // Check if the password and confirm password fields match
        const usernameFeedbackContent = usernameFeedback.textContent.replace(/['"]+/g, '').trim(); // Get feedback text for username
        const emailFeedbackContent = emailFeedback.textContent.replace(/['"]+/g, '').trim(); // Get feedback text for email
        const usernameTaken = usernameFeedbackContent === 'Username already in use'; // Check if the username is already in use
        const emailTaken = emailFeedbackContent === 'Email already in use'; // Check if the email is already in use
        const emailFormatValid = validateEmailFormat(emailInput.value); // Validate the email format
        const emailInvalidFormat = !emailFormatValid; // Check if the email format is valid

        // Show/hide "Please fill in all required fields" message
        if (!allFieldsFilled) {
            requiredMessage.style.display = 'block';
        } else {
            requiredMessage.style.display = 'none';
        }

        // Show/hide email feedback
        if (emailFeedbackContent && emailFeedbackContent !== '') {
            emailFeedback.style.display = 'block';
        } else {
            emailFeedback.textContent = '';
            emailFeedback.style.display = 'none';
        }
        // Show/hide username feedback
        if (usernameFeedbackContent && usernameFeedbackContent !== '') {
            usernameFeedback.style.display = 'block';
        } else {
            usernameFeedback.style.display = 'none';
        }
        // Show/hide password mismatch feedback
        if (allFieldsFilled && !passwordsMatch) {
            passwordMismatch.style.display = 'block';
        } else {
            passwordMismatch.style.display = 'none';
        }

        // Enable/disable the Sign Up button
        submitBtn.disabled = !(allFieldsFilled && passwordValid && passwordsMatch && !usernameTaken && !emailTaken && emailFormatValid);
    }// Enables or disables the form submission button based on field validity

    function showModal(title, body, redirectUrl) {
        modalTitle.textContent = title;
        modalBody.textContent = body;
        modal.show();
        modalOkBtn.onclick = () => { // Set the action to be performed when the OK button in the modal is clicked
            if (redirectUrl) {
                window.location.href = redirectUrl;
            }
        }; // When the modal is closed, check if a redirect URL is available and redirect if it is
    }// Shows a modal with a given title, body, and optional redirect URL

    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
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
            .then(response => response.json()) // Parse the JSON response
        .then(data => {
            if (data.success) { // If the operation was successful
                showModal('Great! Welcome to SimSky Economy', 'Your account was successfully created.', '/login/');
            } else {
                showModal('Sorry, we couldn’t create your account', `Please try again later\nError: ${data.error}`, '/signup/'); // Show error in modal
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
        } else {// Check if the email format is valid. If it is, proceed with HTMX to check if the email is already in use
            emailFeedback.textContent = ''; // Clear previous error messages
            emailFeedback.style.display = 'none';
            emailInput.dispatchEvent(new Event('change'));
        }
        checkFormValidity();
    });

    const debouncedCheckUsername = debounce(() => {
        usernameInput.dispatchEvent(new Event('change'));
    }, 500);

    inputs.forEach(input => {
        if (input !== emailInput) { // Add listener to each input except the email, avoiding duplicate listeners
            input.addEventListener('input', checkFormValidity);
        } else {
            input.addEventListener('input', checkFormValidity);
        }
        if (input === usernameInput) {
            input.addEventListener('input', debouncedCheckUsername)
        }
    }); //Add an event listener to each input for immediate validation

    document.addEventListener('htmx:afterSwap', (event) => {
        const target = event.target; // Get the target of the HTMX swap event
        if (target.id === 'username-feedback') {// Check if the target is the username feedback element
            try {
                const data = JSON.parse(target.textContent); // Try parsing the content to get the data
                usernameFeedback.textContent = data.username_error || ''; // Update feedback with errors or clear if there are none
            } catch (e) {
                console.error('Error parsing username feedback JSON:', e);
            }
        } else if (target.id === 'email-feedback') { // Check if the target is the email feedback element
            try {
                const data = JSON.parse(target.textContent);// Try parsing the content to get the data
                // Only update email feedback with backend message if the format is valid
                if (!validateEmailFormat(emailInput.value) && emailInput.value.trim() !== '') {// Validate if the email format is valid and if the input is empty
                    emailFeedback.textContent = 'Invalid email format';// Show the error message for an invalid format
                    emailFeedback.style.display = 'block';
                } else {
                    emailFeedback.textContent = data.email_error || '';// Updates feedback with the error message received from the backend or clears it if no error is found
                    emailFeedback.style.display = data.email_error ? 'block' : 'none';// Show or hide the message based on the error
                }
            } catch (e) {
                console.error('Error parsing email feedback JSON:', e);
            }
        }
        checkFormValidity();// After each swap, check the overall validity of the form
    });// HTMX event listener to handle responses from username and email availability checks

    checkFormValidity();// Initial form check
});// Waits for the DOM to load