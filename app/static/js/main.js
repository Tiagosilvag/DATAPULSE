document.addEventListener("DOMContentLoaded", function () {

    const toggle = document.getElementById("themeToggle");
    const savedTheme = localStorage.getItem("theme") || "dark";

    // 🔥 aplica no BODY (padronizado)
    document.body.setAttribute("data-theme", savedTheme);

    if (toggle) {
        toggle.checked = savedTheme === "light";

        toggle.addEventListener("change", function () {
            const theme = toggle.checked ? "light" : "dark";

            document.body.setAttribute("data-theme", theme);
            localStorage.setItem("theme", theme);
        });
    }

});