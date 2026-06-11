document.addEventListener("DOMContentLoaded", function () {

    // =========================
    // ELEMENTOS DO DOM
    // =========================
    const modal = document.getElementById("modalPerfil");
    const tituloModal = document.getElementById("tituloModal");

    const idPerfil = document.getElementById("id_perfil");
    const dsPerfil = document.getElementById("ds_perfil");
    const dsDescricao = document.getElementById("ds_descricao");

    const btnNovoPerfil = document.getElementById("btnNovoPerfil");
    const btnCancelarPerfil = document.getElementById("btnCancelarPerfil");

    // =========================
    // VALIDAÇÃO BÁSICA
    // =========================
    if (!modal) {
        console.error("Modal de perfil não encontrado (#modalPerfil)");
        return;
    }

    // =========================
    // NOVO PERFIL
    // =========================
    if (btnNovoPerfil) {
        btnNovoPerfil.addEventListener("click", function () {
            abrirModalNovoPerfil();
        });
    }

    // =========================
    // CANCELAR
    // =========================
    if (btnCancelarPerfil) {
        btnCancelarPerfil.addEventListener("click", function () {
            fecharModal();
        });
    }

    // =========================
    // EDITAR PERFIL
    // =========================
    document.querySelectorAll(".btnEditarPerfil").forEach(function (btn) {
        btn.addEventListener("click", function () {
            abrirModalEditarPerfil(
                btn.dataset.id,
                btn.dataset.codigo,
                btn.dataset.descricao
            );
        });
    });

    // =========================
    // FUNÇÕES
    // =========================
    function abrirModalNovoPerfil() {
        tituloModal.innerText = "Novo Perfil";
        idPerfil.value = "";
        dsPerfil.value = "";
        dsDescricao.value = "";
        dsPerfil.disabled = false;
        modal.style.display = "flex";
    }

    function abrirModalEditarPerfil(id, codigo, descricao) {
        tituloModal.innerText = "Editar Perfil";
        idPerfil.value = id;
        dsPerfil.value = codigo;
        dsDescricao.value = descricao;
        dsPerfil.disabled = true; // código não deve ser alterado
        modal.style.display = "flex";
    }

    function fecharModal() {
        modal.style.display = "none";
    }

});