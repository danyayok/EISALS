document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    const innInput = document.getElementById('inn');

    if (innInput) {
        innInput.addEventListener('input', (e) => {
            e.target.value = e.target.value.replace(/\D/g, '');
        });
    }

    if (!loginForm) return;

    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = new FormData(loginForm);

        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                body: formData,
                credentials: 'same-origin'
            });

            const data = await response.json();

            if (response.ok) {
                window.location.href = '/feed';
            } else {
                alert(data.detail || 'Ошибка входа');
            }
        } catch (error) {
            console.error('Ошибка сети:', error);
            alert('Не удалось связаться с сервером');
        }
    });
});
