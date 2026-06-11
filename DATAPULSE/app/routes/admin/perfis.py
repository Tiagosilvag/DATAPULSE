from flask import Blueprint, render_template, request, jsonify
from app.services.perfil_service import listar_perfis_app
from app.db.connection import executar_transacao

admin_perfis_bp = Blueprint(
    "admin_perfis_bp",
    __name__,
    url_prefix="/admin/perfis"
)

# LISTAGEM
@admin_perfis_bp.route("/listar")
def listar():

    filtro = request.args.get("q", "").strip().lower()

    perfis = listar_perfis_app()

    if filtro:
            perfis = [
                p for p in perfis
                if filtro in (p.get("ds_perfil") or "").lower()
                or filtro in (p.get("sg_perfil") or "").lower()
            ]

    return render_template(
        "admin/perfis/list.html",
        perfis=perfis
    )


# NOVO PERFIL
@admin_perfis_bp.route("/novo-ajax", methods=["POST"])
def novo_perfil():

    data = request.get_json()

    def _insert(cursor):
        cursor.execute("""
            INSERT INTO GVDW_OWNER.PERFIL_APP (DS_PERFIL, DS_DESCRICAO)
            VALUES (:codigo, :descricao)
        """, {
            "codigo": data.get("codigo"),
            "descricao": data.get("descricao")
        })

    executar_transacao(_insert)

    return jsonify({"sucesso": True})


# EDITAR PERFIL
@admin_perfis_bp.route("/editar-ajax", methods=["POST"])
def editar_perfil():

    data = request.get_json()

    def _update(cursor):
        cursor.execute("""
            UPDATE GVDW_OWNER.PERFIL_APP
            SET DS_PERFIL = :codigo,
                DS_DESCRICAO = :descricao
            WHERE ID_PERFIL = :id
        """, {
            "id": data.get("id"),
            "codigo": data.get("codigo"),
            "descricao": data.get("descricao")
        })

    executar_transacao(_update)

    return jsonify({"sucesso": True})