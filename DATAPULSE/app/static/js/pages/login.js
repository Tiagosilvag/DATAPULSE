document.addEventListener("DOMContentLoaded", () => {

    const form = document.querySelector("form");
    const btn = document.getElementById("loginBtn");
    const mascot = document.getElementById("loginMascot");
    const card = document.querySelector(".login-card");

    if (!form || !btn) return;

    /* ========================= */
    /* SUBMIT → LOADING */
    /* ========================= */
    form.addEventListener("submit", () => {
        btn.classList.add("loading");

        if (mascot) {
            mascot.classList.remove("error", "success");
            mascot.classList.add("loading");
        }
    });

    /* ========================= */
    /* ERRO (FLASH) */
    /* ========================= */
    const hasError = document.querySelector(".flash.error");

    if (hasError) {
        if (card) card.classList.add("error");

        if (mascot) {
            mascot.classList.remove("loading", "success");
            mascot.classList.add("error");
        }
    }

    /* ========================= */
    /* AUTO-HIDE FLASH */
    /* ========================= */
    const flashes = document.querySelectorAll(".flash");

    flashes.forEach(flash => {
        const isError = flash.classList.contains("error");
        const timeout = isError ? 4000 : 2000;

        setTimeout(() => {
            flash.style.opacity = "0";

            setTimeout(() => {
                flash.remove();
            }, 300);

        }, timeout);
    });

    /* ========================= */
    /* CARREGAR TEMA */
    /* ========================= */
    const saved = localStorage.getItem("theme") || "dark";
    document.body.dataset.theme = saved;

});

/* ========================= */
/* MOSTRAR SENHA */
/* ========================= */
function toggleSenha(){
    const input = document.getElementById("senha");

    if(input.type === "password"){
        input.type = "text";
    } else {
        input.type = "password";
    }
}

/* ========================= */
/* TOGGLE TEMA */
/* ========================= */
function toggleTheme(){
    const body = document.body;
    const btn = document.getElementById("btnTheme");

    if(body.dataset.theme === "light"){
        body.dataset.theme = "dark";
        localStorage.setItem("theme","dark");
        btn.textContent = "☀️";  // 🔥 mostra sol
    } else {
        body.dataset.theme = "light";
        localStorage.setItem("theme","light");
        btn.textContent = "🌙";  // 🔥 mostra lua
    }
}

/* ========================= */
/* CARREGAR TEMA */
/* ========================= */
document.addEventListener("DOMContentLoaded", () => {

    const toggle = document.getElementById("themeToggle");

    /* CARREGA TEMA */
    const saved = localStorage.getItem("theme") || "dark";

    document.body.dataset.theme = saved;

    /* SETA CHECK */
    if(saved === "light"){
        toggle.checked = true;
    }

    /* EVENT CHANGE */
    toggle.addEventListener("change", () => {
        if(toggle.checked){
            document.body.dataset.theme = "light";
            localStorage.setItem("theme","light");
        }else{
            document.body.dataset.theme = "dark";
            localStorage.setItem("theme","dark");
        }
    });

});