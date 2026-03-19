document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    if (!loginForm) return;

    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault(); // Остановка системного перехода на JSON-страницу

        const formData = new FormData(loginForm);

        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                // ПРИСВАИВАЕМ ТОКЕН В ПАМЯТЬ БРАУЗЕРА
                localStorage.setItem('token', data.access_token);
                console.log("Вход успешен, токен присвоен");
                window.location.href = '/feed';
            } else {
                // Вывод ошибки (например, "Неверный ИНН или пароль")
                alert(data.detail || "Ошибка входа");
            }
        } catch (error) {
            console.error("Ошибка сети:", error);
            alert("Не удалось связаться с сервером");
        }
    });
});


document.getElementById('inn').addEventListener('input', (e) => {
    e.target.value = e.target.value.replace(/\D/g, '');
});
