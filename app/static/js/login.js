document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    const innInput = document.getElementById('inn');
    const kppInput = document.getElementById('kpp');
    const kppBlock = document.getElementById('kpp-block');

    const toggleKpp = () => {
        if (!innInput || !kppInput || !kppBlock) return;

        const val = innInput.value.replace(/\D/g, '');
        innInput.value = val;

        // 1. Подсветка рамки ИНН (как в регистрации)
        if (val.length === 10 || val.length === 12) {
            innInput.style.borderColor = "#4ade80"; // Зеленый
        } else if (val.length > 0) {
            innInput.style.borderColor = "#60a5fa"; // Синий
        } else {
            innInput.style.borderColor = "white";
        }

        // 2. Логика для КПП
        if (val.length === 12) {
            kppInput.value = '';
            kppInput.disabled = true;
            kppInput.required = false;
            kppBlock.style.opacity = "0.4";
            kppInput.style.borderColor = "white";
        } else if (val.length === 10) {
            kppInput.disabled = false;
            kppInput.required = true;
            kppBlock.style.opacity = "1";
        } else {
            kppInput.disabled = true;
            kppBlock.style.opacity = "0.6";
            kppInput.style.borderColor = "white";
        }
    };

    if (innInput) {
        // Слушаем и ввод, и изменение (для автозаполнения)
        innInput.addEventListener('input', toggleKpp);
        innInput.addEventListener('change', toggleKpp);

        // Запуск при загрузке
        toggleKpp();
        // Дополнительный микро-таймаут для браузерных менеджеров паролей
        setTimeout(toggleKpp, 200);
    }

    // Обработка отправки формы
    if (loginForm) {
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
                    showToast(data.detail || 'Неправильный ИНН/КПП или пароль', 'error');
                }
            } catch (error) {
                console.error('Ошибка сети:', error);
                showToast('Ошибка подключения к серверу', 'error');
            }
        });
    }
});

function showToast(message, type = 'error', duration = 4000) {
    const config = {
        error: { icon: '✕', color: '#ef4444' },
        success: { icon: '✓', color: '#3b82f6' },
        warning: { icon: '!', color: '#facc15' }
    };

    const style = config[type] || config.error;

    // контейнер (создаётся один раз)
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        Object.assign(container.style, {
            position: 'fixed',
            bottom: '30px',
            right: '30px',
            display: 'flex',
            flexDirection: 'column',
            gap: '12px',
            zIndex: 99999
        });
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');

    Object.assign(toast.style, {
        width: '360px',
        background: '#070F2B',
        border: '1px solid rgba(255,255,255,0.08)',
        borderRadius: '18px',
        boxShadow: `0 20px 60px ${style.color}33`,
        overflow: 'hidden',
        cursor: 'pointer',
        transform: 'translateX(120%)',
        opacity: '0',
        transition: 'all 0.35s cubic-bezier(0.22,1,0.36,1)'
    });

    toast.innerHTML = `
        <div style="display:flex; gap:12px; align-items:center; padding:14px 16px;">
            <div style="
                width:42px;height:42px;
                display:flex;align-items:center;justify-content:center;
                border-radius:12px;
                background:rgba(255,255,255,0.03);
                border:1px solid rgba(255,255,255,0.06);
                flex-shrink:0;
            ">
                <span style="color:${style.color}; font-size:18px; font-weight:900;">
                    ${style.icon}
                </span>
            </div>

            <div style="flex:1; min-width:0;">
                <div style="
                    font-size:11px;
                    letter-spacing:0.25em;
                    opacity:0.4;
                    text-transform:uppercase;
                    font-family:monospace;
                    margin-bottom:4px;
                ">System</div>

                <div style="
                    font-size:15px;
                    font-weight:600;
                    color:white;
                    line-height:1.2;
                ">${message}</div>
            </div>
        </div>

        <div style="height:3px; width:100%; background:rgba(255,255,255,0.06);">
            <div style="
                height:100%;
                width:100%;
                background:${style.color};
                transition: width ${duration}ms linear;
            "></div>
        </div>
    `;

    const progress = toast.querySelector('div div div');

    container.appendChild(toast);

    requestAnimationFrame(() => {
        toast.style.transform = 'translateX(0)';
        toast.style.opacity = '1';
        if (progress) progress.style.width = '0%';
    });

    const remove = () => {
        toast.style.transform = 'translateX(120%)';
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 350);
    };

    const timer = setTimeout(remove, duration);

    toast.onclick = () => {
        clearTimeout(timer);
        remove();
    };
}