document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById('settings-form');
    const usernameInput = document.getElementById('username');
    const usernameError = document.getElementById('username-error');
    const usernameSuccess = document.getElementById('username-success');
    const currentPasswordInput = document.getElementById('current_password');
    const currentPasswordError = document.getElementById('current-password-error');
    const newPasswordInput = document.getElementById('new_password');
    const confirmPasswordInput = document.getElementById('confirm_password');
    const confirmPasswordError = document.getElementById('confirm-password-error');
    const passwordRequirements = document.getElementById('password-requirements');
    const saveButton = document.getElementById('save-changes-btn');
    const userId = usernameInput.dataset.userId;
    let debounceTimeout;
    let isCurrentPasswordValid = false;
    let isUsernameValid = true;
    let isNewPasswordValid = true;
    const passwordRequirementsList = {
        uppercase: /[A-Z]/,
        minLength: /.{10,}/,
        specialChar: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/,
        number: /[0-9]/,
    };
    function updateSaveButton() {
        saveButton.disabled = !(isCurrentPasswordValid && isUsernameValid && isNewPasswordValid);
    }
    function checkUsername() {
        const username = usernameInput.value.trim();
        if (!username) {
            usernameError.style.display = "none";
            usernameSuccess.style.display = "none";
            isUsernameValid = false;
            updateSaveButton();
            return;
        }
        const formData = new FormData();
        formData.append("username", username);
        formData.append("check_username", "true");
        fetch(`/settings/${userId}/`, {
            method: "POST",
            body: formData,
            headers: {
                "X-Requested-With": "XMLHttpRequest",
            },
        })
            .then((response) => response.json())
            .then((data) => {
                isUsernameValid = data.available;
                usernameError.style.display = data.available ? "none" : "block";
                usernameSuccess.style.display = data.available ? "block" : "none";
                updateSaveButton();
            })
            .catch((error) => {
                console.error("Error checking username:", error);
                isUsernameValid = false;
                updateSaveButton();
            });
    }
    function checkCurrentPassword() {
        const password = currentPasswordInput.value.trim();
        if (!password) {
            currentPasswordError.style.display = "none";
            isCurrentPasswordValid = false;
            updateSaveButton();
            return;
        }
        const formData = new FormData();
        formData.append("current_password", password);
        formData.append("check_password", "true");
        fetch(`/settings/${userId}/`, {
            method: "POST",
            body: formData,
            headers: {
                "X-Requested-With": "XMLHttpRequest",
            },
        })
            .then((response) => response.json())
            .then((data) => {
                isCurrentPasswordValid = data.valid;
                currentPasswordError.style.display = data.valid ? "none" : "block";
                updateSaveButton();
            })
            .catch((error) => {
                console.error("Error checking password:", error);
                isCurrentPasswordValid = false;
                updateSaveButton();
            });
    }
    function checkNewPassword() {
        const newPassword = newPasswordInput.value.trim();
        const confirmPassword = confirmPasswordInput.value.trim();
        const username = usernameInput.value.trim();
        if (!newPassword && !confirmPassword) {
            passwordRequirements.style.display = "none";
            confirmPasswordError.style.display = "none";
            isNewPasswordValid = true;
            updateSaveButton();
            return;
        }
        let errors = [];
        if (!passwordRequirementsList.uppercase.test(newPassword))
            errors.push("Must contain at least one uppercase letter");
        if (!passwordRequirementsList.minLength.test(newPassword))
            errors.push("Must be at least 10 characters long");
        if (!passwordRequirementsList.specialChar.test(newPassword))
            errors.push("Must contain at least one special character");
        if (!passwordRequirementsList.number.test(newPassword))
            errors.push("Must contain at least one number");
        if (newPassword === username)
            errors.push("Must not be similar to username");
        if (newPassword && confirmPassword && newPassword !== confirmPassword) {
            confirmPasswordError.style.display = "block";
        } else {
            confirmPasswordError.style.display = "none";
        }
        if (errors.length > 0) {
            passwordRequirements.innerHTML = errors.join("<br>");
            passwordRequirements.style.display = "block";
            isNewPasswordValid = false;
        } else {
            passwordRequirements.style.display = "none";
            isNewPasswordValid = newPassword === confirmPassword;
        }
        updateSaveButton();
    }
    usernameInput.addEventListener("input", function () {
        clearTimeout(debounceTimeout);
        debounceTimeout = setTimeout(checkUsername, 500);
    });
    currentPasswordInput.addEventListener("input", function () {
        clearTimeout(debounceTimeout);
        debounceTimeout = setTimeout(checkCurrentPassword, 500);
    });
    newPasswordInput.addEventListener("input", function () {
        clearTimeout(debounceTimeout);
        debounceTimeout = setTimeout(checkNewPassword, 500);
    });
    confirmPasswordInput.addEventListener("input", function () {
        clearTimeout(debounceTimeout);
        debounceTimeout = setTimeout(checkNewPassword, 500);
    });
    updateSaveButton();
});