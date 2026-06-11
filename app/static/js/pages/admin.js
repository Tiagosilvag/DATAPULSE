document.addEventListener("DOMContentLoaded", () => {

    console.log("✅ admin.js carregado");

    const toggle = document.getElementById("themeToggle");
    if (!toggle) return;

    function aplicarTema(theme) {

        // 🔥 padrão novo (admin)
        if (theme === "light") {
            document.body.setAttribute("data-theme", "light");
        } else {
            document.body.removeAttribute("data-theme");
        }

        // 🔥 mantém compatibilidade ETL
        document.body.classList.remove("light", "dark");
        document.body.classList.add(theme);

        toggle.checked = theme === "light";
    }

    const savedTheme = localStorage.getItem("theme") || "dark";
    aplicarTema(savedTheme);

    toggle.addEventListener("change", () => {

        const theme = toggle.checked ? "light" : "dark";
        localStorage.setItem("theme", theme);

        aplicarTema(theme);

    });

});