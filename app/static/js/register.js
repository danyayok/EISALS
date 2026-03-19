document.addEventListener('DOMContentLoaded', () => {
    const regForm = document.getElementById('reg-form');
    if (!regForm) return;

    regForm.addEventListener('submit', async (e) => {
        e.preventDefault(); // КРИТИЧЕСКИ ВАЖНО: останавливаем системный переход

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
                window.location.href = '/feed';
            } else {
                alert(data.detail || "Ошибка при регистрации");
            }
        } catch (error) {
            console.error("Ошибка сети:", error);
            alert("Не удалось связаться с сервером");
        }
    });
});

const inputAva = document.getElementById("avatarka"), imgAva = document.getElementById("ava-log");
inputAva.addEventListener("change", () => {
    const file = inputAva.files[0];
    if (file) { const reader = new FileReader(); reader.onload = e => imgAva.src = e.target.result; reader.readAsDataURL(file); }
});

const phoneInput = document.getElementById('phone');
phoneInput.addEventListener('input', e => {
    let x = e.target.value.replace(/\D/g, '').match(/(\d{0,1})(\d{0,3})(\d{0,3})(\d{0,2})(\d{0,2})/);
    e.target.value = !x[2] ? x[1] === '7' ? '+7 ' : x[1] : '+7 (' + x[2] + (x[3] ? ') ' + x[3] : '') + (x[4] ? '-' + x[4] : '') + (x[5] ? '-' + x[5] : '');
});

const innInput = document.getElementById('inn');
innInput.addEventListener('input', e => {
    e.target.value = e.target.value.replace(/\D/g, '');
    e.target.style.borderColor = (e.target.value.length === 10 || e.target.value.length === 12) ? "#4ade80" : "white";
});

const pass = document.getElementById('password'), confirmPass = document.getElementById('confirm_password'), strengthBar = document.getElementById('strength-bar'), strengthText = document.getElementById('strength-text'), strengthPercent = document.getElementById('strength-percent'), strengthWrapper = document.getElementById('strength-wrapper'), matchMsg = document.getElementById('match-message'), submitBtn = document.getElementById('submit-btn');

function validate() {
    const val = pass.value, confVal = confirmPass.value;
    let score = 0;
    strengthWrapper.style.opacity = val.length > 0 ? "1" : "0";
    if (val.length >= 8) score += 25;
    if (/[a-z]/.test(val) && /[A-Z]/.test(val)) score += 25;
    if (/\d/.test(val)) score += 25;
    if (/[^A-Za-z0-9]/.test(val)) score += 25;
    strengthBar.style.width = score + "%";
    strengthPercent.innerText = score + "%";
    if (score <= 25) { strengthBar.className = "h-full bg-red-500 transition-all"; strengthText.innerText = "Слабый"; strengthText.style.color = "#ef4444"; }
    else if (score <= 50) { strengthBar.className = "h-full bg-yellow-500 transition-all"; strengthText.innerText = "Средний"; strengthText.style.color = "#eab308"; }
    else if (score <= 75) { strengthBar.className = "h-full bg-blue-400 transition-all"; strengthText.innerText = "Надежный"; strengthText.style.color = "#60a5fa"; }
    else { strengthBar.className = "h-full bg-green-400 transition-all shadow-[0_0_10px_#4ade80]"; strengthText.innerText = "Идеальный"; strengthText.style.color = "#4ade80"; }

    if (confVal.length > 0) {
        matchMsg.style.opacity = "1";
        const isMatch = val === confVal && val !== "";
        confirmPass.style.borderColor = isMatch ? "#4ade80" : "#ef4444";
        matchMsg.innerText = isMatch ? "Пароли совпадают" : "Пароли не совпадают";
        matchMsg.style.color = isMatch ? "#4ade80" : "#ef4444";
        submitBtn.disabled = !isMatch;
    } else { matchMsg.style.opacity = "0"; confirmPass.style.borderColor = "white"; submitBtn.disabled = true; }
}
pass.addEventListener('input', validate); confirmPass.addEventListener('input', validate);
