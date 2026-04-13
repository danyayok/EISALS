document.addEventListener('DOMContentLoaded', () => {
    const regForm = document.getElementById('reg-form');
    if (!regForm) return;

    // --- ОБРАБОТКА ФОРМЫ ---
    regForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirm_password').value;

        if (password !== confirmPassword) {
            alert("Пароли не совпадают!");
            return;
        }

        const formData = new FormData(regForm);
        try {
            const response = await fetch('/api/register', {
                method: 'POST',
                body: formData,
                credentials: 'same-origin'
            });
            const data = await response.json();
            if (response.ok) {
                showToast('Регистрация успешна!', 'success');
                setTimeout(() => window.location.href = '/feed', 1500);
            } else {
                showToast(data.detail || 'Ошибка регистрации', 'warning');
            }
        } catch (error) {
            alert("Не удалось связаться с сервером");
        }
    });

    // --- АВАТАР ---
    const inputAva = document.getElementById("avatarka"), imgAva = document.getElementById("ava-log");
    inputAva.addEventListener("change", () => {
        const file = inputAva.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = e => imgAva.src = e.target.result;
            reader.readAsDataURL(file);
        }
    });

    const phoneInput = document.getElementById('phone');
    phoneInput.addEventListener('input', e => {
        let x = e.target.value.replace(/\D/g, '').match(/(\d{0,1})(\d{0,3})(\d{0,3})(\d{0,2})(\d{0,2})/);
        if (!x) return;
        e.target.value = !x[2] ? (x[1] ? '+7 (' : '') : '+7 (' + x[2] + (x[3] ? ') ' + x[3] : '') + (x[4] ? '-' + x[4] : '') + (x[5] ? '-' + x[5] : '');
    });

    const innInput = document.getElementById('inn');
    const kppInput = document.getElementById('kpp');
    const kppStar = document.getElementById('kpp-star');
    const kppStatus = document.getElementById('kpp-status');
    const kppBlock = document.getElementById('kpp-block');

    innInput.addEventListener('input', e => {
        e.target.value = e.target.value.replace(/\D/g, '');
        const val = e.target.value;

        // Подсветка рамки ИНН (зеленый если ок, синий если в процессе, белый если пусто)
        if (val.length === 10 || val.length === 12) {
            e.target.style.borderColor = "#4ade80"; // Зеленый
        } else if (val.length > 0) {
            e.target.style.borderColor = "#60a5fa"; // Синий (в процессе)
        } else {
            e.target.style.borderColor = "white";
        }

        if (val.length === 12) {
            // Логика для ИП
            kppStar?.classList.add('hidden');
            if (kppStatus) {
                kppStatus.innerText = 'Не требуется для ИП';
                kppStatus.style.color = 'rgba(255,255,255,0.2)';
            }
            kppInput.required = false;
            kppInput.disabled = true;
            kppInput.value = '';
            kppBlock.style.opacity = "0.4";
            kppInput.style.borderColor = "white";
        } else if (val.length === 10) {
            // Логика для ЮЛ
            kppStar?.classList.remove('hidden');
            if (kppStatus) {
                kppStatus.innerText = 'Обязательно для ЮЛ';
                kppStatus.style.color = '#60a5fa';
            }
            kppInput.required = true;
            kppInput.disabled = false;
            kppBlock.style.opacity = "1";
        } else {
            // Нейтральное состояние (пока ИНН не допит)
            kppStar?.classList.add('hidden');
            if (kppStatus) kppStatus.innerText = 'Введите ИНН';
            kppInput.disabled = true; // Блокируем, пока не поймем кто это (ИП или ЮЛ)
            kppBlock.style.opacity = "0.6";
        }
    });


    const pass = document.getElementById('password'),
          confirmPass = document.getElementById('confirm_password'),
          strengthBar = document.getElementById('strength-bar'),
          strengthText = document.getElementById('strength-text'),
          strengthPercent = document.getElementById('strength-percent'),
          strengthWrapper = document.getElementById('strength-wrapper'),
          matchMsg = document.getElementById('match-message'),
          submitBtn = document.getElementById('submit-btn');

function validate() {
    const val = pass.value, confVal = confirmPass.value;
    let score = 0;

    if (!strengthWrapper) return;
    strengthWrapper.style.opacity = val.length > 0 ? "1" : "0";

    // Логика подсчета баллов
    if (val.length >= 8) score += 25;
    if (/[a-z]/.test(val) && /[A-Z]/.test(val)) score += 25;
    if (/\d/.test(val)) score += 25;
    if (/[^A-Za-z0-9]/.test(val)) score += 25;

    // Применяем ширину
    strengthBar.style.width = score + "%";
    strengthPercent.innerText = score + "%";

    // Убираем все фоновые классы Tailwind, чтобы они не мешали цветам из JS
    strengthBar.className = "h-full transition-all duration-500";

    if (score <= 25) {
        strengthBar.style.backgroundColor = "#ef4444"; // Red 500
        strengthBar.style.boxShadow = "none";
        strengthText.innerText = "Слабый";
        strengthText.style.color = "#ef4444";
    } else if (score <= 50) {
        strengthBar.style.backgroundColor = "#eab308"; // Yellow 500
        strengthBar.style.boxShadow = "none";
        strengthText.innerText = "Средний";
        strengthText.style.color = "#eab308";
    } else if (score <= 75) {
        strengthBar.style.backgroundColor = "#60a5fa"; // Blue 400
        strengthBar.style.boxShadow = "none";
        strengthText.innerText = "Надежный";
        strengthText.style.color = "#60a5fa";
    } else {
        strengthBar.style.backgroundColor = "#4ade80"; // Green 400
        strengthBar.style.boxShadow = "0 0 10px #4ade80";
        strengthText.innerText = "Идеальный";
        strengthText.style.color = "#4ade80";
    }


        if (confVal.length > 0) {
            matchMsg.style.opacity = "1";
            const isMatch = val === confVal && val !== "";
            confirmPass.style.borderColor = isMatch ? "#4ade80" : "#ef4444";
            matchMsg.innerText = isMatch ? "Пароли совпадают" : "Пароли не совпадают";
            matchMsg.style.color = isMatch ? "#4ade80" : "#ef4444";
            submitBtn.disabled = !isMatch;
        } else {
            matchMsg.style.opacity = "0";
            confirmPass.style.borderColor = "white";
            submitBtn.disabled = true;
        }
    }

    pass.addEventListener('input', validate);
    confirmPass.addEventListener('input', validate);
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
