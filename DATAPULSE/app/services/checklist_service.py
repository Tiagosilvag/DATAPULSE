from app.db.connection import get_connection


def buscar_checklist():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            ID_CHECK,
            NM_SEGMENTO,
            NM_VIEW,
            CHECK_KIND,
            FINALIDADE,
            MSG_OK,
            MSG_ERRO
        FROM GVDW_B2B.TB_CHECK_LIST
        WHERE ENABLED = 'S'
        ORDER BY NM_SEGMENTO, ORDEM
    """)

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    # 🔥 organiza por segmento
    result = {}

    for r in rows:
        segmento = r[1]

        if segmento not in result:
            result[segmento] = []

        result[segmento].append({
            "id": r[0],
            "view": r[2],
            "tipo": r[3],
            "finalidade": r[4],
            "ok": r[5],
            "erro": r[6]
        })

    return result