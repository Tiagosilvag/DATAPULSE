   
from flask import Blueprint, render_template, request, jsonify
from app.services.segmento_service import listar_segmentos
from app.db.connection import executar_transacao

admin_segmentos_bp = Blueprint(
    "admin_segmentos_bp",
    __name__,
    url_prefix="/admin/segmentos"
)


@admin_segmentos_bp.route("/listar")
def listar():

    filtro = request.args.get("q", "").strip().lower()

    segmentos = listar_segmentos()


    if filtro:
            segmentos = [
                s for s in segmentos
                if filtro in (s.get("nm_segmento") or "").lower()
                or filtro in (s.get("sg_segmento") or "").lower()
            ]


    return render_template(
        "admin/segmento/list.html",
        segmentos=segmentos
    )
