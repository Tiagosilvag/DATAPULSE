from app.db.connection import get_connection
from app.utils.monitor import monitor
from werkzeug.security import generate_password_hash


# =====================================================
# 🔹 QUERY UTIL
# =====================================================
def _exec_query(query, params=None, fetchone=False, fetchall=False):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(query, params or {})

    if fetchone:
        result = cursor.fetchone()
    elif fetchall:
        result = cursor.fetchall()
    else:
        result = cursor.fetchall()

    cursor.close()
    conn.close()

    return result


# =====================================================
# 🔹 USUÁRIO
# =====================================================
@monitor
def buscar_usuario_por_login(login):

    row = _exec_query("""
        SELECT ID_USUARIO,
               DS_LOGIN,
               NM_USUARIO,
               DS_PASSWORD_HASH,
               FL_ATIVO
        FROM GVDW_OWNER.USUARIO_APP
        WHERE UPPER(DS_LOGIN) = :login
    """, {"login": login}, fetchone=True)

    if not row:
        return None

    return {
        "id_usuario": row[0],
        "login": row[1],
        "nome": row[2],
        "password_hash": row[3],
        "ativo": row[4]
    }


def buscar_usuario_por_id(id_usuario):

    row = _exec_query("""
        SELECT ID_USUARIO,
               DS_LOGIN,
               NM_USUARIO,
               FL_ATIVO,
               FL_TROCAR_SENHA
        FROM GVDW_OWNER.USUARIO_APP
        WHERE ID_USUARIO = :id
    """, {"id": id_usuario}, fetchone=True)

    if not row:
        return None

    return {
        "id_usuario": row[0],
        "login": row[1],
        "nome": row[2],
        "ativo": row[3],
        "fl_trocar_senha": row[4]
    }


# =====================================================
# 🔹 LISTAGEM USUÁRIOS
# =====================================================
def listar_usuarios():

    rows = _exec_query("""
        SELECT U.ID_USUARIO,
               U.NM_USUARIO,
               U.DS_LOGIN,
               LISTAGG(PP.DS_PERFIL, ', ')
                   WITHIN GROUP (ORDER BY PP.DS_PERFIL) AS PERFIS,
               U.FL_ATIVO,
               U.DT_INSERT
        FROM GVDW_OWNER.USUARIO_APP U
        LEFT JOIN GVDW_OWNER.USUARIO_PERFIL UP
            ON UP.ID_USUARIO = U.ID_USUARIO
        LEFT JOIN GVDW_OWNER.PERFIL_APP PP
            ON PP.ID_PERFIL = UP.ID_PERFIL
        GROUP BY U.ID_USUARIO, U.NM_USUARIO, U.DS_LOGIN, U.FL_ATIVO, U.DT_INSERT
        ORDER BY U.NM_USUARIO
    """, fetchall=True)

    usuarios = []

    for r in rows:

        id_usuario = r[0]

        modulos = buscar_modulos_usuario(id_usuario)

        usuarios.append({
            "id_usuario": id_usuario,
            "nome": r[1],
            "login": r[2],
            "perfis": r[3].split(", ") if r[3] else [],
            "modulos": [m["codigo"] for m in modulos],  # ✅ módulos
            "ativo": r[4],
            "data_cadastro": r[5]
        })

    return usuarios


# =====================================================
# 🔹 PERFIS
# =====================================================
def buscar_perfis_usuario(id_usuario):

    rows = _exec_query("""
        SELECT P.DS_PERFIL
        FROM GVDW_OWNER.USUARIO_PERFIL UP
        JOIN GVDW_OWNER.PERFIL_APP P
            ON P.ID_PERFIL = UP.ID_PERFIL
        WHERE UP.ID_USUARIO = :id
    """, {"id": id_usuario}, fetchall=True)

    return [r[0] for r in rows]


def inserir_perfis_usuario(cursor, id_usuario, perfis):

    for id_perfil in perfis:
        cursor.execute("""
            INSERT INTO GVDW_OWNER.USUARIO_PERFIL (
                ID_USUARIO,
                ID_PERFIL
            )
            VALUES (:id_usuario, :id_perfil)
        """, {
            "id_usuario": id_usuario,
            "id_perfil": id_perfil
        })


def listar_perfis():

    rows = _exec_query("""
        SELECT ID_PERFIL,
               DS_PERFIL,
               DS_DESCRICAO
        FROM GVDW_OWNER.PERFIL_APP
        ORDER BY DS_PERFIL
    """, fetchall=True)

    return [
        {
            "id_perfil": r[0],
            "ds_perfil": r[1],
            "ds_descricao": r[2] or ""
        }
        for r in rows
    ]


# =====================================================
# 🔹 MÓDULOS
# =====================================================
def criar_modulo(dados):

    codigo = dados.get("codigo")
    descricao = dados.get("descricao")

    if not codigo:
        raise ValueError("Código obrigatório")

    if not descricao:
        raise ValueError("Descrição obrigatória")

    def _insert(cursor):

        cursor.execute("""
            INSERT INTO GVDW_OWNER.MODULO_APP (
                ID_MODULO,
                DS_CODIGO_MODULO,
                DS_DESCRICAO,
                FL_ATIVO
            ) VALUES (
                GVDW_OWNER.SEQ_MODULO_APP.NEXTVAL,
                :codigo,
                :descricao,
                'S'
            )
        """, {
            "codigo": codigo.upper(),
            "descricao": descricao
        })

    executar_transacao(_insert)

    return True



def buscar_modulos_usuario(id_usuario):

    rows = _exec_query("""
        SELECT M.ID_MODULO,
               M.DS_CODIGO_MODULO
        FROM GVDW_OWNER.USUARIO_MODULO UM
        JOIN GVDW_OWNER.MODULO_APP M
            ON M.ID_MODULO = UM.ID_MODULO
        WHERE UM.ID_USUARIO = :id
          AND UM.FL_VISUALIZACAO = 'S'
          AND M.FL_ATIVO = 'S'
    """, {"id": id_usuario}, fetchall=True)

    return [
        {
            "id_modulo": r[0],
            "codigo": r[1]
        }
        for r in rows
    ]


def inserir_modulos_usuario(cursor, id_usuario, modulos):

    for id_modulo in modulos:
        cursor.execute("""
            INSERT INTO GVDW_OWNER.USUARIO_MODULO (
                ID_USUARIO,
                ID_MODULO,
                FL_EXECUCAO,
                FL_VISUALIZACAO
            )
            VALUES (:id_usuario, :id_modulo, 'S', 'S')
        """, {
            "id_usuario": id_usuario,
            "id_modulo": id_modulo
        })


def atualizar_modulos_usuario(cursor, id_usuario, modulos):

    cursor.execute("""
        DELETE FROM GVDW_OWNER.USUARIO_MODULO
        WHERE ID_USUARIO = :id
    """, {"id": id_usuario})

    inserir_modulos_usuario(cursor, id_usuario, modulos)


def listar_modulos():

    rows = _exec_query("""
        SELECT ID_MODULO,
               DS_CODIGO_MODULO,
               DS_DESCRICAO,
               NVL(FL_ATIVO, 'S')
        FROM GVDW_OWNER.MODULO_APP
        ORDER BY DS_CODIGO_MODULO
    """, fetchall=True)

    return [
        {
            "id_modulo": r[0],
            "ds_codigo_modulo": r[1],
            "ds_descricao": r[2],
            "fl_ativo": r[3]
        }
        for r in rows
    ]


# =====================================================
# 🔹 CRIAR USUÁRIO
# =====================================================
def existe_login(login):

    row = _exec_query("""
        SELECT 1
        FROM GVDW_OWNER.USUARIO_APP
        WHERE DS_LOGIN = :login
    """, {"login": login}, fetchone=True)

    return row is not None


def criar_usuario(dados):

    def _insert(cursor):

        if existe_login(dados["login"]):
            raise Exception("Login já existe")

        senha_hash = generate_password_hash("12345678")

        cursor.execute("""
            INSERT INTO GVDW_OWNER.USUARIO_APP (
                DS_LOGIN,
                NM_USUARIO,
                DS_PASSWORD_HASH,
                FL_ATIVO,
                FL_TROCAR_SENHA
            )
            VALUES (
                :login,
                :nome,
                :senha,
                :ativo,
                'S'
            )
        """, {
            "login": dados["login"],
            "nome": dados["nome"],
            "senha": senha_hash,
            "ativo": dados.get("ativo", "S")
        })

        # 🔥 pega ID
        cursor.execute("""
            SELECT ID_USUARIO
            FROM GVDW_OWNER.USUARIO_APP
            WHERE DS_LOGIN = :login
        """, {"login": dados["login"]})

        id_usuario = cursor.fetchone()[0]

        # ✅ perfis
        if dados.get("perfis"):
            inserir_perfis_usuario(cursor, id_usuario, dados["perfis"])

        # ✅ módulos 🔥
        if dados.get("modulos"):
            inserir_modulos_usuario(cursor, id_usuario, dados["modulos"])

    executar_transacao(_insert)


# =====================================================
# 🔹 TRANSACTION
# =====================================================
def executar_transacao(func):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        result = func(cursor)
        conn.commit()
        return result

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()
