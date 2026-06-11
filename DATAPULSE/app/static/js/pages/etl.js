document.addEventListener("DOMContentLoaded", () => {

    const form = document.getElementById("formDisparo");

    if (!form) return;

    form.addEventListener("submit", async function (e) {

        e.preventDefault();

        const formData = new FormData(this);

        try {

            const resp = await fetch("/etl/disparar", {
                method: "POST",
                body: formData
            });

            const data = await resp.json();

            if (data.status === "ok") {
                alert("✅ Execução enviada para fila!");
                location.reload();
            } else {
                alert("Erro: " + data.msg);
            }

        } catch (err) {
            console.error(err);
            alert("Erro ao disparar execução");
        }

    });

});