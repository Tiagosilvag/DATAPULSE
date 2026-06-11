// ==========================================
// ✅ SELEÇÃO DE CHECKS
// ==========================================
function marcarTodos() {
    document.querySelectorAll('.check-item')
        .forEach(cb => cb.checked = true);
}

function limparTodos() {
    document.querySelectorAll('.check-item')
        .forEach(cb => cb.checked = false);
}


// ==========================================
// ✅ DETALHAR FINALIDADE
// ==========================================
function toggleDetalhe(id) {

    const el = document.getElementById("detalhe-" + id);
    if (!el) return;

    const isOpen = (el.style.display === "block");

    // fecha todos
    document.querySelectorAll(".finalidade-text").forEach(e => {
        e.style.display = "none";
    });

    // abre só se estava fechado
    if (!isOpen) {
        el.style.display = "block";
    }
}


// ==========================================
// ✅ MODAL (VERSÃO)
// ==========================================
function abrirModalParametro() {
    const modal = document.getElementById("modalParametro");
    if (modal) modal.style.display = "flex";
}

function fecharModal() {
    const modal = document.getElementById("modalParametro");
    if (modal) modal.style.display = "none";
}


// ==========================================
// ✅ EVENTOS PRINCIPAIS
// ==========================================
document.addEventListener("DOMContentLoaded", () => {

    // ✅ garante que começa fechado
    const modal = document.getElementById("modalParametro");
    if (modal) modal.style.display = "none";

    const form = document.getElementById("formParametro");

    // ======================================
    // ✅ SUBMIT DO MODAL
    // ======================================
    if (form) {

        form.addEventListener("submit", async function (e) {

            e.preventDefault();

            const formData = new FormData(this);

            const comboAtual = formData.get("combo_atual");
            const comboAnterior = formData.get("combo_anterior");

            if (!comboAtual) {
                alert("Selecione a versão atual!");
                return;
            }

            const [anomesAtual, versaoAtual] = comboAtual.split("|");

            let versaoAnterior = null;

            if (comboAnterior) {
                const parts = comboAnterior.split("|");
                versaoAnterior = parts[1];
            }

            const payload = new FormData();
            payload.append("segmento", formData.get("segmento"));
            payload.append("anomes", anomesAtual);
            payload.append("versao", versaoAtual);

            if (versaoAnterior) {
                payload.append("versao_anterior", versaoAnterior);
            }

            try {

                const resp = await fetch("/rv/atualizar_parametro", {
                    method: "POST",
                    body: payload
                });

                const data = await resp.json();

                if (data.status === "ok") {
                    location.reload();
                } else {
                    alert("Erro ao salvar: " + data.msg);
                }

            } catch (err) {
                console.error(err);
                alert("Erro ao atualizar parâmetros");
            }

        });

    }

    // ======================================
    // ✅ BLOQUEAR SELEÇÃO DUPLICADA
    // ======================================
    const selectAtual = document.querySelector("[name='combo_atual']");
    const selectAnterior = document.querySelector("[name='combo_anterior']");

    if (selectAtual && selectAnterior) {

        function atualizarBloqueio() {

            const valorAtual = selectAtual.value;

            Array.from(selectAnterior.options).forEach(opt => {
                opt.disabled = (opt.value === valorAtual);
            });

        }

        selectAtual.addEventListener("change", atualizarBloqueio);

        // dispara na carga
        atualizarBloqueio();
    }

});


// ==========================================
// ✅ CONSULTAR (ABRIR DETALHE)
// ==========================================
function consultarCheck(idCheck) {

    window.open(`/rv/consultar/${idCheck}`, "_blank");

}
