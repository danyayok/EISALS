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
            if (response.ok) { window.location.href = '/feed'; }
            else { alert(data.detail || "Ошибка при регистрации"); }
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
