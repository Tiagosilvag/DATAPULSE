from app.db.connection import get_connection


def buscar_amostragem_provisao(ano_mes, page=1, page_size=50):
    """
    Retorna uma página completa da provisão RV
    com valores idênticos ao SQL do banco.
    """

    offset = (page - 1) * page_size

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM (
            SELECT
                ANO_MES AS ANOMES_PRODUCAO,
                G.NM_SEGMENTO AS DS_CANAL,
                G.MATRICULA_UNIFICADA AS MATRICULA,
                G.NM_COLABORADOR AS NOME_COLABORADOR,
                G.NM_CARGO AS CARGO,

                ROUND(SUM(NVL(G.FATOR_FOLHA_PRORATA, 0)), 2) AS SOMA_FATOR,
                ROUND(SUM(NVL(U.SALARIO, 0) * NVL(G.FATOR_FOLHA_PRORATA, 0)), 2) AS VALOR_RV,

                ROUND(
                    (SUM(NVL(U.SALARIO, 0) * NVL(G.FATOR_FOLHA_PRORATA, 0))
                     / NVL(D.DIAS_UTEIS, 1)) * NVL(D.DIAS_NAO_UTEIS, 0),
                2) AS DSR,

                ROUND(
                    SUM(NVL(U.SALARIO, 0) * NVL(G.FATOR_FOLHA_PRORATA, 0)) +
                    ((SUM(NVL(U.SALARIO, 0) * NVL(G.FATOR_FOLHA_PRORATA, 0))
                      / NVL(D.DIAS_UTEIS, 1)) * NVL(D.DIAS_NAO_UTEIS, 0)),
                2) AS TOTAL_RV,

                ROUND(
                    (SUM(NVL(U.SALARIO, 0) * NVL(G.FATOR_FOLHA_PRORATA, 0)) +
                     ((SUM(NVL(U.SALARIO, 0) * NVL(G.FATOR_FOLHA_PRORATA, 0))
                      / NVL(D.DIAS_UTEIS, 1)) * NVL(D.DIAS_NAO_UTEIS, 0))) * 0.08,
                2) AS INSS,

                ROUND(
                    (SUM(NVL(U.SALARIO, 0) * NVL(G.FATOR_FOLHA_PRORATA, 0)) +
                     ((SUM(NVL(U.SALARIO, 0) * NVL(G.FATOR_FOLHA_PRORATA, 0))
                      / NVL(D.DIAS_UTEIS, 1)) * NVL(D.DIAS_NAO_UTEIS, 0))) * 0.28,
                2) AS FGTS
            FROM (
                SELECT
                    G.*,
                    NVL(GVDW_B2B.FN_DE_PARA_TCLOUD_RE(G.RE), G.RE) AS MATRICULA_UNIFICADA
                FROM GVDW_B2B.TB_RESULTADO_CONSOLIDADO G
            ) G

            LEFT JOIN (
                SELECT
                    H.NMBR_MATRICULA,
                    GVDW_OWNER.CRYPTIT.DECRYPT(H.DS_SALARIO) AS SALARIO
                FROM GVDW_OWNER.RV_B2CF_HEADCOUNT H
                INNER JOIN (
                    SELECT NMBR_MATRICULA, MAX(NMBR_ANOMES) AS ULTIMO
                    FROM GVDW_OWNER.RV_B2CF_HEADCOUNT
                    GROUP BY NMBR_MATRICULA
                ) X
                    ON H.NMBR_MATRICULA = X.NMBR_MATRICULA
                   AND H.NMBR_ANOMES = X.ULTIMO

                UNION ALL

                SELECT
                    T.MATRICULA,
                    TO_CHAR(NVL(T.SALARIO, 0))
                FROM GVDW_B2B.BASE_HC_TTECH T
            ) U
                ON U.NMBR_MATRICULA = G.MATRICULA_UNIFICADA

            LEFT JOIN (
                SELECT NM_SEGMENTO, MAX(ID_VERSAO) AS ID_VERSAO_SEGMENTO
                FROM GVDW_B2B.TB_RESULTADO_CONSOLIDADO
                WHERE CALCULO = 'PRE FECHAMENTO'
                GROUP BY NM_SEGMENTO
            ) V
                ON V.NM_SEGMENTO = G.NM_SEGMENTO

            LEFT JOIN GVDW_B2B.BASE_DSR D
                ON D.NMBR_ANOMES_PROVISAO =
                   TO_CHAR(ADD_MONTHS(TO_DATE(G.ANO_MES, 'YYYYMM'), 1), 'YYYYMM')

            WHERE
                G.CALCULO = 'PRE FECHAMENTO'
                AND G.ANO_MES = :ano_mes
                AND G.NM_SEGMENTO <> 'ADVERTISING'

            GROUP BY
                G.ANO_MES,
                G.NM_SEGMENTO,
                G.RE,
                G.NM_COLABORADOR,
                G.NM_CARGO,
                D.DIAS_UTEIS,
                D.DIAS_NAO_UTEIS,
                V.ID_VERSAO_SEGMENTO,
                G.MATRICULA_UNIFICADA

            ORDER BY
                G.NM_SEGMENTO,
                G.NM_COLABORADOR
        )
        OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
    """, {
        "ano_mes": int(ano_mes),
        "offset": offset,
        "limit": page_size
    })

    columns = [c[0].lower() for c in cursor.description]
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return [dict(zip(columns, row)) for row in rows]



# ==========================================================
# EXPORTAÇÃO (EXCEL) — COMPLETA
# ==========================================================
def buscar_provisao_completa(ano_mes):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            ANO_MES AS ANOMES_PRODUCAO,
            G.NM_SEGMENTO AS DS_CANAL,
            G.MATRICULA_UNIFICADA AS MATRICULA,
            G.NM_COLABORADOR AS NOME_COLABORADOR,
            G.NM_CARGO AS CARGO,

            ROUND(SUM(NVL(G.FATOR_FOLHA_PRORATA, 0)), 2) AS SOMA_FATOR,
            ROUND(SUM(NVL(U.SALARIO, 0) * NVL(G.FATOR_FOLHA_PRORATA, 0)), 2) AS VALOR_RV,

            ROUND(
                (SUM(NVL(U.SALARIO, 0) * NVL(G.FATOR_FOLHA_PRORATA, 0))
                 / NVL(D.DIAS_UTEIS, 1)) * NVL(D.DIAS_NAO_UTEIS, 0),
            2) AS DSR,

            ROUND(
                SUM(NVL(U.SALARIO, 0) * NVL(G.FATOR_FOLHA_PRORATA, 0)) +
                ((SUM(NVL(U.SALARIO, 0) * NVL(G.FATOR_FOLHA_PRORATA, 0))
                  / NVL(D.DIAS_UTEIS, 1)) * NVL(D.DIAS_NAO_UTEIS, 0)),
            2) AS TOTAL_RV,

            ROUND(
                (SUM(NVL(U.SALARIO, 0) * NVL(G.FATOR_FOLHA_PRORATA, 0)) +
                 ((SUM(NVL(U.SALARIO, 0) * NVL(G.FATOR_FOLHA_PRORATA, 0))
                  / NVL(D.DIAS_UTEIS, 1)) * NVL(D.DIAS_NAO_UTEIS, 0))) * 0.08,
            2) AS INSS,

            ROUND(
                (SUM(NVL(U.SALARIO, 0) * NVL(G.FATOR_FOLHA_PRORATA, 0)) +
                 ((SUM(NVL(U.SALARIO, 0) * NVL(G.FATOR_FOLHA_PRORATA, 0))
                  / NVL(D.DIAS_UTEIS, 1)) * NVL(D.DIAS_NAO_UTEIS, 0))) * 0.28,
            2) AS FGTS

        FROM (
            SELECT
                G.*,
                NVL(GVDW_B2B.FN_DE_PARA_TCLOUD_RE(G.RE), G.RE) AS MATRICULA_UNIFICADA
            FROM GVDW_B2B.TB_RESULTADO_CONSOLIDADO G
            WHERE G.CALCULO = 'PRE FECHAMENTO'
              AND G.ANO_MES = :ano_mes
              AND G.NM_SEGMENTO <> 'ADVERTISING'
        ) G

        LEFT JOIN (
            SELECT
                H.NMBR_MATRICULA,
                GVDW_OWNER.CRYPTIT.DECRYPT(H.DS_SALARIO) AS SALARIO
            FROM GVDW_OWNER.RV_B2CF_HEADCOUNT H
            UNION ALL
            SELECT
                T.MATRICULA,
                TO_CHAR(NVL(T.SALARIO, 0))
            FROM GVDW_B2B.BASE_HC_TTECH T
        ) U
            ON U.NMBR_MATRICULA = G.MATRICULA_UNIFICADA

        LEFT JOIN GVDW_B2B.BASE_DSR D
            ON D.NMBR_ANOMES_PROVISAO =
               TO_CHAR(ADD_MONTHS(TO_DATE(G.ANO_MES, 'YYYYMM'), 1), 'YYYYMM')

        GROUP BY
            G.ANO_MES,
            G.NM_SEGMENTO,
            G.RE,
            G.NM_COLABORADOR,
            G.NM_CARGO,
            D.DIAS_UTEIS,
            D.DIAS_NAO_UTEIS,
            G.MATRICULA_UNIFICADA

        ORDER BY
            G.NM_SEGMENTO,
            G.NM_COLABORADOR
    """, {"ano_mes": int(ano_mes)})

    columns = [c[0].lower() for c in cursor.description]
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return [dict(zip(columns, row)) for row in rows]


def calcular_dashboard_provisao(dados):
    if not dados:
        return {}

    resumo = {
        "total_rv": 0,
        "total_dsr": 0,
        "total_inss": 0,
        "total_fgts": 0,
        "total_provisao": 0,
        "qtd_colaboradores": 0,
        "por_segmento": {}
    }

    matriculas = set()

    for r in dados:
        rv = r["valor_rv"]
        dsr = r["dsr"]
        inss = r["inss"]
        fgts = r["fgts"]
        total = r["total_rv"] + inss + fgts

        resumo["total_rv"] += rv
        resumo["total_dsr"] += dsr
        resumo["total_inss"] += inss
        resumo["total_fgts"] += fgts
        resumo["total_provisao"] += total

        matriculas.add(r["matricula"])

        seg = r["ds_canal"]
        if seg not in resumo["por_segmento"]:
            resumo["por_segmento"][seg] = {
                "rv": 0,
                "dsr": 0,
                "total": 0
            }

        resumo["por_segmento"][seg]["rv"] += rv
        resumo["por_segmento"][seg]["dsr"] += dsr
        resumo["por_segmento"][seg]["total"] += total

    resumo["qtd_colaboradores"] = len(matriculas)

    return resumo

def buscar_dados_dashboard_provisao(ano_mes):
    """
    Retorna TODOS os registros necessários para o dashboard
    (sem paginação), usando a mesma regra da amostragem.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            ANO_MES AS ANOMES_PRODUCAO,
            G.NM_SEGMENTO AS DS_CANAL,
            G.MATRICULA_UNIFICADA AS MATRICULA,
            G.NM_COLABORADOR AS NOME_COLABORADOR,
            G.NM_CARGO AS CARGO,

            ROUND(SUM(NVL(G.FATOR_FOLHA_PRORATA, 0)), 2) AS SOMA_FATOR,
            ROUND(SUM(NVL(U.SALARIO, 0) * NVL(G.FATOR_FOLHA_PRORATA, 0)), 2) AS VALOR_RV,

            ROUND(
                (SUM(NVL(U.SALARIO, 0) * NVL(G.FATOR_FOLHA_PRORATA, 0))
                 / NVL(D.DIAS_UTEIS, 1)) * NVL(D.DIAS_NAO_UTEIS, 0),
            2) AS DSR,

            ROUND(
                SUM(NVL(U.SALARIO, 0) * NVL(G.FATOR_FOLHA_PRORATA, 0)) +
                ((SUM(NVL(U.SALARIO, 0) * NVL(G.FATOR_FOLHA_PRORATA, 0))
                  / NVL(D.DIAS_UTEIS, 1)) * NVL(D.DIAS_NAO_UTEIS, 0)),
            2) AS TOTAL_RV,

            ROUND(
                (SUM(NVL(U.SALARIO, 0) * NVL(G.FATOR_FOLHA_PRORATA, 0)) +
                 ((SUM(NVL(U.SALARIO, 0) * NVL(G.FATOR_FOLHA_PRORATA, 0))
                  / NVL(D.DIAS_UTEIS, 1)) * NVL(D.DIAS_NAO_UTEIS, 0))) * 0.08,
            2) AS INSS,

            ROUND(
                (SUM(NVL(U.SALARIO, 0) * NVL(G.FATOR_FOLHA_PRORATA, 0)) +
                 ((SUM(NVL(U.SALARIO, 0) * NVL(G.FATOR_FOLHA_PRORATA, 0))
                  / NVL(D.DIAS_UTEIS, 1)) * NVL(D.DIAS_NAO_UTEIS, 0))) * 0.28,
            2) AS FGTS

        FROM (
            SELECT
                G.*,
                NVL(GVDW_B2B.FN_DE_PARA_TCLOUD_RE(G.RE), G.RE) AS MATRICULA_UNIFICADA
            FROM GVDW_B2B.TB_RESULTADO_CONSOLIDADO G
            WHERE G.CALCULO = 'PRE FECHAMENTO'
              AND G.ANO_MES = :ano_mes
              AND G.NM_SEGMENTO <> 'ADVERTISING'
        ) G

        LEFT JOIN (
            SELECT
                H.NMBR_MATRICULA,
                GVDW_OWNER.CRYPTIT.DECRYPT(H.DS_SALARIO) AS SALARIO
            FROM GVDW_OWNER.RV_B2CF_HEADCOUNT H
            UNION ALL
            SELECT
                T.MATRICULA,
                TO_CHAR(NVL(T.SALARIO, 0))
            FROM GVDW_B2B.BASE_HC_TTECH T
        ) U
            ON U.NMBR_MATRICULA = G.MATRICULA_UNIFICADA

        LEFT JOIN GVDW_B2B.BASE_DSR D
            ON D.NMBR_ANOMES_PROVISAO =
               TO_CHAR(ADD_MONTHS(TO_DATE(G.ANO_MES, 'YYYYMM'), 1), 'YYYYMM')

        GROUP BY
            G.ANO_MES,
            G.NM_SEGMENTO,
            G.RE,
            G.NM_COLABORADOR,
            G.NM_CARGO,
            D.DIAS_UTEIS,
            D.DIAS_NAO_UTEIS,
            G.MATRICULA_UNIFICADA
    """, {"ano_mes": int(ano_mes)})

    columns = [c[0].lower() for c in cursor.description]
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return [dict(zip(columns, row)) for row in rows]

def buscar_dashboard_provisao(ano_mes):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            DS_CANAL AS SEGMENTO,
            SUM(NMBR_VALOR_RV_CAMP) AS RV,
            SUM(NMBR_DSR) AS DSR,
            SUM(NMBR_VALOR_RV_CAMP) + SUM(NMBR_DSR) AS TOTAL_RV
        FROM (
            SELECT
                G.NM_SEGMENTO AS DS_CANAL,

                ROUND(
                    SUM(NVL(U.SALARIO, 0) * NVL(G.FATOR_FOLHA_PRORATA, 0)),
                2) AS NMBR_VALOR_RV_CAMP,

                ROUND(
                    (SUM(NVL(U.SALARIO, 0) * NVL(G.FATOR_FOLHA_PRORATA, 0))
                     / NVL(D.DIAS_UTEIS, 1)) * NVL(D.DIAS_NAO_UTEIS, 0),
                2) AS NMBR_DSR

            FROM (
                SELECT
                    G.*,
                    NVL(GVDW_B2B.FN_DE_PARA_TCLOUD_RE(G.RE), G.RE) AS MATRICULA_UNIFICADA
                FROM GVDW_B2B.TB_RESULTADO_CONSOLIDADO G
                WHERE G.CALCULO = 'PRE FECHAMENTO'
                  AND G.ANO_MES = :ano_mes
                  AND G.NM_SEGMENTO <> 'ADVERTISING'
            ) G

            LEFT JOIN (
                SELECT
                    H.NMBR_MATRICULA,
                    GVDW_OWNER.CRYPTIT.DECRYPT(H.DS_SALARIO) AS SALARIO
                FROM GVDW_OWNER.RV_B2CF_HEADCOUNT H
                INNER JOIN (
                    SELECT
                        NMBR_MATRICULA,
                        MAX(NMBR_ANOMES) AS ULTIMO
                    FROM GVDW_OWNER.RV_B2CF_HEADCOUNT
                    GROUP BY NMBR_MATRICULA
                ) X
                    ON H.NMBR_MATRICULA = X.NMBR_MATRICULA
                   AND H.NMBR_ANOMES = X.ULTIMO

                UNION ALL

                SELECT
                    T.MATRICULA,
                    TO_CHAR(NVL(T.SALARIO, 0))
                FROM GVDW_B2B.BASE_HC_TTECH T
                INNER JOIN (
                    SELECT
                        MATRICULA,
                        MAX(ANO_MES) AS ULTIMO
                    FROM GVDW_B2B.BASE_HC_TTECH
                    GROUP BY MATRICULA
                ) TX
                    ON T.MATRICULA = TX.MATRICULA
                   AND T.ANO_MES = TX.ULTIMO
            ) U
                ON U.NMBR_MATRICULA = G.MATRICULA_UNIFICADA

            LEFT JOIN (
                SELECT
                    NM_SEGMENTO,
                    MAX(ID_VERSAO) AS ID_VERSAO_SEGMENTO
                FROM GVDW_B2B.TB_RESULTADO_CONSOLIDADO
                WHERE CALCULO = 'PRE FECHAMENTO'
                GROUP BY NM_SEGMENTO
            ) V
                ON V.NM_SEGMENTO = G.NM_SEGMENTO

            LEFT JOIN GVDW_B2B.BASE_DSR D
                ON D.NMBR_ANOMES_PROVISAO =
                   TO_CHAR(
                       ADD_MONTHS(TO_DATE(G.ANO_MES,'YYYYMM'),1),
                       'YYYYMM'
                   )

            GROUP BY
                G.NM_SEGMENTO,
                D.DIAS_UTEIS,
                D.DIAS_NAO_UTEIS,
                V.ID_VERSAO_SEGMENTO
        )
        GROUP BY DS_CANAL
        ORDER BY DS_CANAL
    """, {"ano_mes": int(ano_mes)})

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    resumo = {
        "total_rv": 0,
        "total_dsr": 0,
        "total_provisao": 0,
        "por_segmento": {}
    }

    for seg, rv, dsr, total in rows:
        resumo["por_segmento"][seg] = {
            "rv": float(rv),
            "dsr": float(dsr),
            "total": float(total)
        }
        resumo["total_rv"] += float(rv)
        resumo["total_dsr"] += float(dsr)
        resumo["total_provisao"] += float(total)

    return resumo

def resumo_validacao(id_run):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT RESULT_STATUS, COUNT(*)
        FROM TB_CHECK_RUN_ITEM
        WHERE ID_RUN = :id_run
        GROUP BY RESULT_STATUS
    """, {"id_run": id_run})

    resumo = {"OK": 0, "ALERTA": 0, "ERRO": 0}

    for status, qtd in cur.fetchall():
        resumo[status] = qtd

    cur.close()
    conn.close()

    return resumo