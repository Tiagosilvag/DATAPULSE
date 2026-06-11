from flask import Blueprint, render_template
from app.db.connection import get_connection

admin_estruturas_bp = Blueprint(
    "admin_estruturas_bp",
    __name__,
    url_prefix="/admin/estruturas"
)

@admin_estruturas_bp.route("/listar")
def listar():

    estruturas = listar_estruturas()

    return render_template(
        "admin/estrutura/list.html",
        estruturas=estruturas
    )


def listar_estruturas():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT ID_ESTRUTURA, NM_ESTRUTURA
        FROM GVDW_OWNER.ESTRUTURA_APP
        ORDER BY NM_ESTRUTURA
    """)

    colunas = [col[0].lower() for col in cursor.description]

    dados = [
        dict(zip(colunas, row))
        for row in cursor.fetchall()
    ]

    cursor.close()
    conn.close()

    return dados