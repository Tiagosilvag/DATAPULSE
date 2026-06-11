from flask import Blueprint, request, jsonify, render_template
from app.db.connection import executar_transacao

from app.services.usuario_service import (
    criar_modulo,
    listar_modulos
)

admin_modulo_bp = Blueprint(
    "admin_modulo_bp",
    __name__,
    url_prefix="/admin/modulos"
)

# =========================================
# API - LISTAR MÓDULOS
# =========================================
@admin_modulo_bp.route("/", methods=["GET"])
def listar():

    modulos = listar_modulos()

    return jsonify({
        "sucesso": True,
        "dados": modulos
    })


# =========================================
# API - CRIAR MÓDULO
# =========================================
@admin_modulo_bp.route("/novo-ajax", methods=["POST"])
def novo_ajax():

    try:
        data = request.get_json()

        print("DADOS RECEBIDOS:", data)

        criar_modulo(data)

        return jsonify({
            "sucesso": True,
            "mensagem": "Módulo criado com sucesso"
        })

    except ValueError as e:
        return jsonify({
            "sucesso": False,
            "erro": str(e)
        }), 400

    except Exception as e:
        print("ERRO DETALHADO:", e)

        return jsonify({
            "sucesso": False,
            "erro": str(e)
        }), 500


# =========================================
# TELA - LISTAGEM DE MÓDULOS
# =========================================
@admin_modulo_bp.route("/listar")
def listar_tela():

    modulos = listar_modulos()

    return render_template(
        "admin/modulos/list.html",
        modulos=modulos
    )

@admin_modulo_bp.route("/editar-ajax", methods=["POST"])
def editar_ajax():

    data = request.get_json()

    def _update(cursor):
        cursor.execute("""
            UPDATE GVDW_OWNER.MODULO_APP
            SET DS_CODIGO_MODULO = :codigo,
                DS_DESCRICAO = :descricao
            WHERE ID_MODULO = :id
        """, {
            "id": data.get("id"),
            "codigo": data.get("codigo"),
            "descricao": data.get("descricao")
        })

    executar_transacao(_update)

    return jsonify({"sucesso": True})

@admin_modulo_bp.route("/excluir-ajax", methods=["POST"])
def excluir_ajax():

    data = request.get_json()

    def _update(cursor):
        cursor.execute("""
            UPDATE GVDW_OWNER.MODULO_APP
            SET FL_ATIVO = 'N'
            WHERE ID_MODULO = :id
        """, {
            "id": data.get("id")
        })

    executar_transacao(_update)

    return jsonify({"sucesso": True})