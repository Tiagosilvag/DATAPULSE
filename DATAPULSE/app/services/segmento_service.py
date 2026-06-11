
from app.db.connection import get_connection
def listar_segmentos():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT 
        ID_SEGMENTO,
        SG_SEGMENTO,
        NM_SEGMENTO
    FROM GVDW_OWNER.SEGMENTO_APP
    ORDER BY NM_SEGMENTO
    """)

    colunas = [col[0].lower() for col in cursor.description]

    resultados = [
        dict(zip(colunas, row))
        for row in cursor.fetchall()
    ]

    cursor.close()
    conn.close()

    return resultados
