SCHEMA = "GVDW_B2B"


# =====================================
# BASE CONFIG
# =====================================
def get_base_config(cur, id_base):
    cur.execute(f"""
        SELECT 
            UPPER(NM_BASE_RH),
            UPPER(NM_TABELA_BKP)
        FROM {SCHEMA}.TB_ETL_BASES
        WHERE ID_BASE_MIS = :id
          AND SN_ATIVO = 'S'
    """, {"id": id_base})

    return cur.fetchone()


# =====================================
# SNAPSHOT
# =====================================
def limpar_backup(cur, tabela_bkp):
    cur.execute(f"DELETE FROM {SCHEMA}.{tabela_bkp}")


def copiar_para_backup(cur, nm_base, nm_bkp):
    origem = f"{SCHEMA}.{nm_base}"
    destino = f"{SCHEMA}.{nm_bkp}"

    cur.execute(f"""
        INSERT INTO {destino}
        SELECT * FROM {origem}
    """)


def contar_registros(cur, tabela):
    cur.execute(f"SELECT COUNT(*) FROM {SCHEMA}.{tabela}")
    return int(cur.fetchone()[0])


# =====================================
# EXECUÇÃO
# =====================================
def gerar_id_execucao(cur):
    cur.execute(f"""
        SELECT {SCHEMA}.SEQ_CONTROLE_ETL_BASES.NEXTVAL
        FROM DUAL
    """)
    return int(cur.fetchone()[0])


def inserir_execucao(cur, id_execucao, id_base, anomes, usuario):
    """
    ⚠️ IMPORTANTE:
    - NÃO inclui BASE_ORIGEM (mantém padrão legado)
    - triggers cuidam de DT_INSERT e LOGIN se necessário
    """

    cur.execute(f"""
        INSERT INTO {SCHEMA}.CONTROLE_ETL_BASES
        (
            ID_EXECUCAO,
            ID_BASE_MIS,
            ANO_MES,
            STATUS_EXECUCAO,
            DT_SOLICITACAO,
            DS_LOGIN_INSERT,
            DT_INSERT
        )
        VALUES
        (
            :id_execucao,
            :id_base,
            :anomes,
            'PENDENTE',
            SYSDATE,
            :usuario,
            SYSDATE
        )
    """, {
        "id_execucao": id_execucao,
        "id_base": id_base,
        "anomes": anomes,
        "usuario": usuario
    })


# =====================================
# LOG
# =====================================
def inserir_log(cur, id_execucao, ordem_etapa, nivel, mensagem):
    cur.execute(f"""
        INSERT INTO {SCHEMA}.ETL_EXEC_LOGS (
            ID_EXECUCAO,
            ORDEM_ETAPA,
            DT_LOG,
            NIVEL,
            MENSAGEM
        )
        VALUES (
            :id_execucao,
            :ordem,
            SYSDATE,
            :nivel,
            :msg
        )
    """, {
        "id_execucao": id_execucao,
        "ordem": ordem_etapa,
        "nivel": nivel,
        "msg": mensagem
    })


# =====================================
# CONSULTAS
# =====================================
def listar_execucoes(cur):
    cur.execute(f"""
        SELECT 
            c.ID_EXECUCAO,
            b.NM_BASE_RH,
            c.ANO_MES,
            c.STATUS_EXECUCAO,
            c.DT_EXECUCAO,
            c.QTD_REGISTROS
        FROM {SCHEMA}.CONTROLE_ETL_BASES c
        JOIN {SCHEMA}.TB_ETL_BASES b 
            ON b.ID_BASE_MIS = c.ID_BASE_MIS
        ORDER BY c.ID_EXECUCAO DESC
    """)
    return cur.fetchall()


def listar_bases(cur):
    cur.execute(f"""
        SELECT ID_BASE_MIS, NM_BASE_RH
        FROM {SCHEMA}.TB_ETL_BASES
        WHERE SN_ATIVO = 'S'
        ORDER BY NM_BASE_RH
    """)
    return cur.fetchall()