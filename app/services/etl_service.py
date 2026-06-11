from app.repositories import etl_repository
from datetime import datetime

# ==========================================
# CONFIG
# ==========================================
SCHEMA = "GVDW_B2B"


def get_tabela(nome):
    """Monta tabela com schema + valida"""
    if not nome:
        raise Exception("Nome de tabela inválido")
    return f"{SCHEMA}.{nome}"


def tratar_anomes(valor):
    """Corrige problema de ano_mes=null"""
    if not valor or valor == "null":
        return None
    return valor


# ==========================================
# DISPARO
# ==========================================
def disparar_execucao(conn, nm_base, anomes):

    cur = conn.cursor()

    try:
        # =====================================
        # NORMALIZA PARAMETRO
        # =====================================
        anomes = tratar_anomes(anomes)
        usuario = "web"  # ou session no route

        if not nm_base or not anomes:
            return {
                "status": "erro",
                "msg": "Base e ANOMES são obrigatórios",
                "base": nm_base
            }

        # =====================================
        # BUSCA CONFIG BASE (REPOSITORY)
        # =====================================
        base_cfg = etl_repository.get_base_config(cur, None)  # vamos ajustar abaixo

        # 🔴 buscar corretamente pelo nome
        cur.execute(f"""
            SELECT ID_BASE_MIS, NM_BASE_RH, NM_TABELA_BKP
            FROM {SCHEMA}.TB_ETL_BASES
            WHERE NM_BASE_RH = :base
              AND SN_ATIVO = 'S'
        """, {"base": nm_base})

        row = cur.fetchone()

        if not row:
            return {
                "status": "erro",
                "msg": "Base não encontrada",
                "base": nm_base
            }

        id_base, nm_base_rh, nm_bkp = row

        if not nm_bkp:
            return {
                "status": "erro",
                "msg": "Base sem BKP configurado",
                "base": nm_base
            }

        # =====================================
        # LOCK EVITA DUPLICIDADE
        # =====================================
        cur.execute(f"""
            SELECT 1
            FROM {SCHEMA}.CONTROLE_ETL_BASES
            WHERE ID_BASE_MIS = :id_base
              AND ANO_MES = :anomes
              AND STATUS_EXECUCAO IN ('PENDENTE', 'EM_EXECUCAO')
        """, {
            "id_base": id_base,
            "anomes": anomes
        })

        if cur.fetchone():
            return {
                "status": "ignorado",
                "msg": "Execução já em andamento",
                "base": nm_base
            }

        # =====================================
        # ✅ SNAPSHOT REAL (CRÍTICO)
        # =====================================
        etl_repository.limpar_backup(cur, nm_bkp)
        etl_repository.copiar_para_backup(cur, nm_base_rh, nm_bkp)

        qtd_bkp = etl_repository.contar_registros(cur, nm_bkp)

        if qtd_bkp == 0:
            raise Exception("Snapshot falhou (backup vazio)")

        # =====================================
        # ✅ GERAR ID + INSERT
        # =====================================
        id_execucao = etl_repository.gerar_id_execucao(cur)

        etl_repository.inserir_execucao(
            cur,
            id_execucao,
            id_base,
            anomes,
            usuario
        )

        # =====================================
        # ✅ PIPELINE (ETAPAS)
        # =====================================
        criar_etapas_execucao(cur, id_execucao)

        # =====================================
        # ✅ COMMIT FINAL (ÚNICO)
        # =====================================
        conn.commit()

        return {
            "status": "ok",
            "base": nm_base,
            "id_execucao": id_execucao,
            "snapshot": qtd_bkp
        }

    except Exception as e:
        conn.rollback()

        return {
            "status": "erro",
            "msg": str(e),
            "base": nm_base
        }

    finally:
        cur.close()

def disparar_multiplas_execucoes(conn, bases, anomes, usuario):

    resultados = []

    for base in bases:

        res = disparar_execucao(
            conn,
            base,
            anomes
        )

        resultados.append(res)

    return {
        "status": "ok",
        "resultado": resultados
    }

def criar_etapas_execucao(cur, id_execucao):

    etapas = [
        ("Validação de Permissões", 1),
        ("Verificação de Dependências", 2),
        ("Preparação do Ambiente", 3),
        ("Extração de Dados", 4),
        ("Transformação de Dados", 5),
        ("Carga no Data Warehouse", 6),
        ("Validação de Volumetria", 7),
        ("Finalização", 8),
    ]

    try:
        # =====================================
        # REMOVE ETAPAS EXISTENTES (SEGURANÇA)
        # =====================================
        cur.execute("""
            DELETE FROM GVDW_B2B.ETL_EXEC_ETAPAS
            WHERE ID_EXECUCAO = :id_execucao
        """, {"id_execucao": id_execucao})

        # =====================================
        # INSERE ETAPAS
        # =====================================
        for nome, ordem in etapas:
            cur.execute("""
                INSERT INTO GVDW_B2B.ETL_EXEC_ETAPAS
                (ID_EXECUCAO, ETAPA, ORDEM, STATUS, DT_INICIO, DT_FIM)
                VALUES (:id, :etapa, :ordem, 'PENDENTE', NULL, NULL)
            """, {
                "id": id_execucao,
                "etapa": nome,
                "ordem": ordem
            })

    except Exception as e:
        raise Exception(f"Erro ao criar etapas: {str(e)}")

# ==========================================
# FILA
# ==========================================
def obter_fila(conn, page=1, page_size=10):

    cur = conn.cursor()

    try:
        offset = (page - 1) * page_size

        cur.execute(f"""
            SELECT COUNT(*)
            FROM {SCHEMA}.CONTROLE_ETL_BASES
        """)
        total_registros = cur.fetchone()[0]

        cur.execute(f"""
            SELECT * FROM (
                SELECT 
                    c.ID_EXECUCAO,
                    b.NM_BASE_RH,
                    c.STATUS_EXECUCAO,
                    c.DT_SOLICITACAO,
                    c.DT_EXECUCAO,
                    c.QTD_REGISTROS,
                    ROW_NUMBER() OVER (ORDER BY c.ID_EXECUCAO DESC) as rn
                FROM {SCHEMA}.CONTROLE_ETL_BASES c
                JOIN {SCHEMA}.TB_ETL_BASES b
                    ON b.ID_BASE_MIS = c.ID_BASE_MIS
            )
            WHERE rn BETWEEN :inicio AND :fim
        """, {
            "inicio": offset + 1,
            "fim": offset + page_size
        })

        rows = cur.fetchall()

        result = []

        for idx, r in enumerate(rows):

            inicio = r[3]
            fim = r[4]

            def fmt(dt):
                return dt.strftime("%d/%m/%Y %H:%M:%S") if dt else "-"

            def fmt_h(dt):
                return dt.strftime("%H:%M:%S") if dt else "-"

            def dur(inicio, fim):
                if not inicio:
                    return "-"
                fim_calc = fim or datetime.now()
                delta = fim_calc - inicio
                total = int(delta.total_seconds())
                h = total // 3600
                m = (total % 3600) // 60
                s = total % 60
                return f"{h:02d}:{m:02d}:{s:02d}"

            def status(s):
                s = (s or "").lower()
                if s in ["finalizado", "concluido"]:
                    return "concluido"
                if s == "executando":
                    return "executando"
                if s in ["erro", "falha"]:
                    return "falha"
                return "pendente"

            item = {
                "ordem": offset + idx + 1,
                "base": r[1],
                "status": status(r[2]),
                "data_execucao": fmt(inicio),
                "dt_inicio": fmt_h(inicio),
                "dt_fim": fmt_h(fim),
                "duracao": dur(inicio, fim),
                "qtd": f"{int(r[5]):,}".replace(",", ".") if r[5] else "0",
            }

            result.append(item)

        return {
            "dados": result,
            "total": total_registros,
            "page": page,
            "page_size": page_size,
            "total_paginas": (total_registros + page_size - 1) // page_size
        }

    finally:
        cur.close()


# ==========================================
# VALIDAÇÃO (CORRIGIDA)
# ==========================================
def validar_volumetria(conn, base, ano_mes):

    cur = conn.cursor()

    try:
        ano_mes = tratar_anomes(ano_mes)

        if not ano_mes:
            return {"status": "sem_dados"}

        cur.execute(f"""
            SELECT NM_TABELA_BKP
            FROM {SCHEMA}.TB_ETL_BASES
            WHERE NM_BASE_RH = :base
        """, {"base": base})

        row = cur.fetchone()

        if not row or not row[0]:
            return {"status": "sem_backup"}

        tabela_backup = get_tabela(row[0])
        tabela_atual = get_tabela(base)

        try:
            cur.execute(f"""
                SELECT COUNT(*) FROM {tabela_backup}
                WHERE ANO_MES = :ano_mes
            """, {"ano_mes": ano_mes})
            qtd_backup = cur.fetchone()[0]

            cur.execute(f"""
                SELECT COUNT(*) FROM {tabela_atual}
                WHERE ANO_MES = :ano_mes
            """, {"ano_mes": ano_mes})
            qtd_atual = cur.fetchone()[0]

        except Exception:
            return {"status": "erro_tabela"}

        diferenca = qtd_atual - qtd_backup

        variacao = 0
        if qtd_backup > 0:
            variacao = (diferenca / qtd_backup) * 100

        status = "ok"
        if qtd_atual < qtd_backup:
            status = "divergente"

        return {
            "status": status,
            "qtd_backup": qtd_backup,
            "qtd_atual": qtd_atual,
            "diferenca": diferenca,
            "variacao": round(variacao, 2)
        }

    finally:
        cur.close()

# ==========================================
# BASES (RESTAURADO)
# ==========================================
def obter_bases(conn):

    cur = conn.cursor()

    try:
        cur.execute(f"""
            SELECT ID_BASE_MIS, NM_BASE_RH
            FROM {SCHEMA}.TB_ETL_BASES
            ORDER BY NM_BASE_RH
        """)

        rows = cur.fetchall()

        return [
            {"id": r[0], "nome": r[1]}
            for r in rows
        ]

    except Exception as e:
        return []

    finally:
        cur.close()        

# ==========================================
# PIPELINE PADRÃO
# ==========================================
PIPELINE_PADRAO = [
    {"ordem": 1, "nome": "Validação de Permissões"},
    {"ordem": 2, "nome": "Verificação de Dependências"},
    {"ordem": 3, "nome": "Preparação do Ambiente"},
    {"ordem": 4, "nome": "Extração de Dados"},
    {"ordem": 5, "nome": "Transformação de Dados"},
    {"ordem": 6, "nome": "Carga no Data Warehouse"},
    {"ordem": 7, "nome": "Validação de Volumetria"},
    {"ordem": 8, "nome": "Finalização"}
]


# ==========================================
# GERAR PIPELINE (RESTAURADO)
# ==========================================
def gerar_pipeline_base(base=None, status_execucao=None):

    if not base:
        return []

    pipeline = []

    for etapa in PIPELINE_PADRAO:

        ordem = etapa["ordem"]

        if status_execucao == "concluido":
            status = "concluido"

        elif status_execucao == "executando":
            if ordem < 5:
                status = "concluido"
            elif ordem == 5:
                status = "executando"
            else:
                status = "pendente"

        elif status_execucao == "falha":
            if ordem < 4:
                status = "concluido"
            elif ordem == 4:
                status = "falha"
            else:
                status = "pendente"

        else:
            status = "pendente"

        pipeline.append({
            "ordem": ordem,
            "nome": etapa["nome"],
            "status": status
        })

    return pipeline

def obter_execucao_base(conn, base, ano_mes=None):  # ✅ DEFAULT

    cur = conn.cursor()

    try:
        query = f"""
   SELECT
    c.STATUS_EXECUCAO,
    c.DT_SOLICITACAO,
    c.DT_EXECUCAO,
    c.ANO_MES,
    c.QTD_REGISTROS
FROM {SCHEMA}.CONTROLE_ETL_BASES c
JOIN {SCHEMA}.TB_ETL_BASES b
    ON b.ID_BASE_MIS = c.ID_BASE_MIS
WHERE b.NM_BASE_RH = :base
  AND (:ano_mes IS NULL OR c.ANO_MES = :ano_mes)
ORDER BY c.DT_EXECUCAO DESC NULLS LAST
FETCH FIRST 2 ROWS ONLY
"""

        cur.execute(query, {
            "base": base,
            "ano_mes": ano_mes
        })

        rows = cur.fetchall()

        if not rows:
            return None, None

        atual = rows[0]
        anterior = rows[1] if len(rows) > 1 else None

        # =========================
        # TEMPO
        # =========================
        def formatar_tempo(inicio, fim):
            if not inicio:
                return "-"

            fim_calc = fim or datetime.now()
            delta = fim_calc - inicio
            total = int(delta.total_seconds())

            h = total // 3600
            m = (total % 3600) // 60
            s = total % 60

            return f"{h:02d}:{m:02d}:{s:02d}"

        status = (atual[0] or "").lower()
        inicio = atual[1]
        fim = atual[2]

        detalhe = {
            "status": status,
            "base": base,
            "inicio": inicio.strftime("%H:%M:%S") if inicio else "-",
            "tempo": formatar_tempo(inicio, fim),
            "previsao": "-" if status != "executando" else "estimando...",
            "etapa": "Processamento" if status == "executando" else "-"
        }

        # =========================
        # VALIDAÇÃO (REGRA CORRETA)
        # =========================
        qtd_atual = atual[4] or 0
        qtd_backup = obter_qtd_backup(conn, base, ano_mes)

        diferenca = None
        variacao = None
        status_validacao = "ok"

        if qtd_backup is not None and qtd_backup > 0:

            diferenca = qtd_atual - qtd_backup
            variacao = round((diferenca / qtd_backup) * 100, 2)

            # 🔴 REGRA PRINCIPAL (NEGÓCIO)
            if qtd_atual < qtd_backup:
                status_validacao = "critico"


        validacao = {
            "qtd_backup": qtd_backup,
            "qtd_atual": qtd_atual,
            "diferenca": diferenca,
            "variacao": variacao,
            "status": status_validacao
        }

        return detalhe, validacao

    except Exception as e:
        print("Erro obter_execucao_base:", e)
        return None, None

    finally:
        cur.close()

def obter_pipeline_real(conn, base):

    cur = conn.cursor()

    try:
        query = f"""
            SELECT 
                e.ORDEM,
                e.ETAPA,
                e.STATUS
            FROM {SCHEMA}.ETL_EXEC_ETAPAS e
            JOIN {SCHEMA}.CONTROLE_ETL_BASES c
                ON c.ID_EXECUCAO = e.ID_EXECUCAO
            JOIN {SCHEMA}.TB_ETL_BASES b
                ON b.ID_BASE_MIS = c.ID_BASE_MIS
            WHERE b.NM_BASE_RH = :base
            ORDER BY e.ORDEM
        """

        cur.execute(query, {"base": base})

        rows = cur.fetchall()

        return [
            {
                "ordem": r[0],
                "nome": r[1],
                "status": (r[2] or "pendente").lower()
            }
            for r in rows
        ]

    except:
        return []

    finally:
        cur.close()


def obter_logs_execucao(conn, base):

    cur = conn.cursor()

    try:
        query = f"""
            SELECT 
                l.DT_LOG,
                l.NIVEL,
                l.MENSAGEM
            FROM GVDW_B2B.ETL_EXEC_LOGS l
            JOIN GVDW_B2B.CONTROLE_ETL_BASES c
                ON c.ID_EXECUCAO = l.ID_EXECUCAO
            JOIN GVDW_B2B.TB_ETL_BASES b
                ON b.ID_BASE_MIS = c.ID_BASE_MIS
            WHERE b.NM_BASE_RH = :base
            ORDER BY l.DT_LOG DESC
            FETCH FIRST 50 ROWS ONLY
        """

        cur.execute(query, {"base": base})

        rows = cur.fetchall()

        return [
            {
                "hora": r[0].strftime("%H:%M:%S"),
                "nivel": r[1],
                "mensagem": r[2]
            }
            for r in rows
        ]

    finally:
        cur.close()

def obter_qtd_backup(conn, base, ano_mes):

    cur = conn.cursor()

    try:
        if not ano_mes:
            return None

        cur.execute(f"""
            SELECT NM_TABELA_BKP
            FROM {SCHEMA}.TB_ETL_BASES
            WHERE NM_BASE_RH = :base
        """, {"base": base})

        row = cur.fetchone()

        if not row or not row[0]:
            return None

        tabela_backup = get_tabela(row[0])

        cur.execute(f"""
            SELECT COUNT(*)
            FROM {tabela_backup}
            WHERE ANO_MES = :ano_mes
        """, {"ano_mes": ano_mes})

        return cur.fetchone()[0]

    except Exception as e:
        print("Erro obter_qtd_backup:", e)
        return None

    finally:
        cur.close()

