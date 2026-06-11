from app.db.connection import get_connection


def cadastrar_perfil(cursor, ds_perfil, ds_descricao):
    """
    Cadastra um novo perfil na PERFIL_APP.
    NÃO faz commit (controle transacional externo).
    ID_PERFIL e auditoria são tratados por trigger.
    """
    cursor.execute("""
        INSERT INTO PERFIL_APP (
            DS_PERFIL,
            DS_DESCRICAO
        )
        VALUES (
            :ds_perfil,
            :ds_descricao
        )
    """, {
        "ds_perfil": ds_perfil,
        "ds_descricao": ds_descricao
    })


def listar_perfis_app():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT
                ID_PERFIL,
                DS_PERFIL,
                DS_DESCRICAO,
                DT_INSERT
            FROM PERFIL_APP
            ORDER BY UPPER(DS_PERFIL)
        """)
        columns = [c[0].lower() for c in cur.description]
        rows = cur.fetchall()
        return [dict(zip(columns, row)) for row in rows]
    finally:
        cur.close()
        conn.close()
