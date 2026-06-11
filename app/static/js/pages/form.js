// =======================================
// INIT GLOBAL
// =======================================
document.addEventListener("DOMContentLoaded", () => {

    console.log("✅ form.js carregado");

    // fecha modal clicando fora
    document.querySelectorAll(".modal-overlay").forEach(modal => {
        modal.addEventListener("click", (e) => {
            if (e.target === modal) fecharModal();
        });
    });

    iniciarFormUsuario(); // ✅ GARANTE EXECUÇÃO

});


// =======================================
// TOAST
// =======================================
function showToast(msg, tipo = "success") {

    const container = document.getElementById("toastContainer");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast ${tipo}`;
    toast.innerText = msg;

    container.appendChild(toast);

    setTimeout(() => toast.remove(), 3000);
}


// =======================================
// MODAL
// =======================================
function abrirModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.style.display = "flex";
}

function fecharModal() {
    document.querySelectorAll(".modal-overlay")
        .forEach(m => m.style.display = "none");
}


// =======================================
// FORM NOVO USUÁRIO ✅ CORRIGIDO
// =======================================
function iniciarFormUsuario() {

    const form = document.getElementById("formUsuario");

    if (!form) {
        console.log("⚠️ formUsuario não encontrado nesta tela");
        return;
    }

    console.log("✅ formUsuario encontrado");

    const erroLogin = document.getElementById("erro-login");
    const erroNome = document.getElementById("erro-nome");
    const erroPerfis = document.getElementById("erro-perfis");

    form.addEventListener("submit", function (e) {

        console.log("🔥 SUBMIT DISPAROU");

        e.preventDefault();

        // limpa erros
        if (erroLogin) erroLogin.style.display = "none";
        if (erroNome) erroNome.style.display = "none";
        if (erroPerfis) erroPerfis.style.display = "none";

        const dados = new FormData(form);

        const login = (dados.get("login") || "").trim();
        const nome = (dados.get("nome") || "").trim();
        const perfis = dados.getAll("perfis");

        let erro = false;

        if (!login) {
            if (erroLogin) erroLogin.style.display = "block";
            erro = true;
        }

        if (!nome) {
            if (erroNome) erroNome.style.display = "block";
            erro = true;
        }

        if (perfis.length === 0) {
            if (erroPerfis) erroPerfis.style.display = "block";
            erro = true;
        }

        if (erro) {
            showToast("Preencha os campos obrigatórios", "error");
            return;
        }

        // ✅ SUCESSO (mock - depois integra backend)
        showToast("Usuário válido ✅", "success");

        console.log({
            login,
            nome,
            perfis
        });

    });
}


// =======================================
// USUÁRIO EDITAR
// =======================================
window.usuarioEditando = null;

function editarUsuarioBtn(btn) {

    const id = parseInt(btn.dataset.id);
    const login = btn.dataset.login;
    const nome = btn.dataset.nome;
    const status = btn.dataset.status;

    const perfis = JSON.parse(btn.dataset.perfis || "[]");
    const modulos = JSON.parse(btn.dataset.modulos || "[]");

    abrirModal("modalUsuario");

    document.getElementById("usuarioLogin").value = login;
    document.getElementById("usuarioNome").value = nome;
    document.getElementById("usuarioStatus").value = status;

    window.usuarioEditando = id;

    document.querySelectorAll("#usuarioPerfis input").forEach(cb => {
        cb.checked = perfis.includes(parseInt(cb.value));
    });

    document.querySelectorAll("#usuarioModulos input").forEach(cb => {
        cb.checked = modulos.includes(parseInt(cb.value));
    });
}


// =======================================
// SALVAR USUÁRIO (EDIÇÃO)
// =======================================
async function salvarUsuario() {

    const login = document.getElementById("usuarioLogin").value.trim();
    const nome = document.getElementById("usuarioNome").value.trim();
    const status = document.getElementById("usuarioStatus").value;

    if (!login || !nome) {
        showToast("Preencha os campos!", "error");
        return;
    }

    const perfis = Array.from(
        document.querySelectorAll("#usuarioPerfis input:checked")
    ).map(cb => parseInt(cb.value));

    const modulos = Array.from(
        document.querySelectorAll("#usuarioModulos input:checked")
    ).map(cb => parseInt(cb.value));

    try {

        const resp = await fetch("/admin/usuarios/editar-ajax", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                id: window.usuarioEditando,
                login,
                nome,
                status,
                perfis,
                modulos
            })
        });

        const data = await resp.json();

        if (data.sucesso) {
            showToast("Usuário atualizado!", "success");
            fecharModal();
            setTimeout(() => location.reload(), 800);
        } else {
            showToast(data.erro || "Erro ao salvar", "error");
        }

    } catch (e) {
        console.error(e);
        showToast("Erro ao salvar usuário", "error");
    }
}