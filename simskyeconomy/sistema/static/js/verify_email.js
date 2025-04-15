document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('verify-email-form');
    const modal = new bootstrap.Modal(document.getElementById('verifyModal'));
    const modalTitle = document.getElementById('verifyModalLabel');
    const modalBody = document.getElementById('verifyModalBody');
    const modalOkBtn = document.getElementById('modalOkBtn');

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
                if (data.success) {
                    showModal('Success!', 'Your email has been verified. You can now log in.', '/login/');
                } else {
                    showModal('Error', `Verification failed: ${data.error}`, '/signup/');
                }
            })
            .catch(error => {
                showModal('Error', `Verification failed: ${error}`, '/signup/');
            });
        });
    }

    function showModal(title, body, redirectUrl) {
        modalTitle.textContent = title;
        modalBody.textContent = body;
        modal.show();
        modalOkBtn.onclick = () => {
            window.location.href = redirectUrl;
        };
    }
});