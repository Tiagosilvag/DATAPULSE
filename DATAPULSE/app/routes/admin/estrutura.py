from flask import Blueprint, render_template, request, jsonify
from app.db.connection import executar_transacao
from app.services.estrutura_service import listar_estruturas

admin_estruturas_bp = Blueprint(
    "admin_estruturas_bp",
    __name__,
    url_prefix="/admin/estruturas"
)

@admin_estruturas_bp.route("/listar")
def listar():

    estruturas = listar_estruturas()

    return render_template(
        "admin/estruturas/list.html",
        estruturas=estruturas
    )


@admin_estruturas_bp.route("/novo-ajax", methods=["POST"])
def novo():

    data = request.get_json()

    def _insert(cursor):
        cursor.execute("""
            INSERT INTO GVDW_OWNER.ESTRUTURA_APP (ID_ESTRUTURA, NM_ESTRUTURA)
            VALUES (:codigo, :descricao)
        """, data)

    executar_transacao(_insert)

    return jsonify(sucesso=True)


@admin_estruturas_bp.route("/editar-ajax", methods=["POST"])
def editar():

    data = request.get_json()

    def _update(cursor):
        cursor.execute("""
            UPDATE GVDW_OWNER.ESTRUTURA_APP
            SET ID_ESTRUTURA = :codigo,
                NM_ESTRUTURA = :descricao
            WHERE ID_ESTRUTURA = :id
        """, data)

    executar_transacao(_update)

    return jsonify(sucesso=True)