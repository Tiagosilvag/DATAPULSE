from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from app.db.connection import get_connection
import re

rv_bp = Blueprint("rv_bp", __name__, url_prefix="/rv")


# ======================================================
# ✅ CHECKLIST
# ======================================================
@rv_bp.route("/checklist", methods=["GET", "POST"])
@login_required
def checklist():

    conn = get_connection()
    cur = conn.cursor()

    segmento = request.args.get("segmento") or request.form.get("segmento")

    segmentos = []
    checks = []
    status_por_check = {}
    parametros = None
    versoes_disponiveis = []

    resumo = {"OK": 0, "ALERTA": 0, "ERRO": 0}
    progresso = "0/0"

    try:

        # ======================================================
        # SEGMENTOS
        # ======================================================
        cur.execute("""
            SELECT DISTINCT NM_SEGMENTO
            FROM GVDW_B2B.VW_RESULTADO_FINAL
            ORDER BY NM_SEGMENTO
        """)
        segmentos = [r[0] for r in cur.fetchall()]

        # ======================================================
        # PARAMETROS
        # ======================================================
        if segmento:
            cur.execute("""
                SELECT ANOMES, ID_VERSAO, ID_VERSAO_ANTERIOR, TRIMESTRE
                FROM GVDW_OWNER.RV_B2B_PARAMETROS_VALIDACAO
                WHERE SEGMENTO = :1
            """, (segmento,))

            row = cur.fetchone()

            if row:
                parametros = {
                    "anomes": row[0],
                    "versao": row[1],
                    "versao_ant": row[2],
                    "trimestre": row[3]
                }

        # ======================================================
        # VERSOES MODAL
        # ======================================================
        if segmento:
            cur.execute("""
                SELECT DISTINCT ANO_MES, ID_VERSAO, TP_CALCULO
                FROM GVDW_B2B.VW_RESULTADO_FINAL
                WHERE NM_SEGMENTO = :1
                ORDER BY ANO_MES DESC, ID_VERSAO DESC
            """, (segmento,))
            versoes_disponiveis = cur.fetchall()

        # ======================================================
        # CHECKS
        # ======================================================
        sql = """
            SELECT
                ID_CHECK,
                NM_VIEW,
                CHECK_KIND,
                EVAL_MODE,
                FINALIDADE,
                EVAL_SQL
            FROM GVDW_B2B.TB_CHECK_LIST
            WHERE ENABLED = 'S'
        """

        params = {}
        if segmento:
            sql += " AND NM_SEGMENTO = :seg"
            params["seg"] = segmento

        cur.execute(sql, params)
        cols = [c[0].lower() for c in cur.description]

        for row in cur.fetchall():
            item = dict(zip(cols, row))

            # LOB safe
            if hasattr(item.get("eval_sql"), "read"):
                item["eval_sql"] = item["eval_sql"].read()

            if hasattr(item.get("finalidade"), "read"):
                item["finalidade"] = item["finalidade"].read()

            checks.append(item)

        # ======================================================
        # EXECUÇÃO (ENGINE CORRETA)
        # ======================================================
        if request.method == "POST" and segmento and parametros:

            selecionados = request.form.getlist("checks")

            if selecionados:

                cur.execute("SELECT NVL(MAX(ID_RUN),0)+1 FROM GVDW_B2B.TB_CHECK_RUN")
                id_run = cur.fetchone()[0]

                cur.execute("""
                    INSERT INTO GVDW_B2B.TB_CHECK_RUN
                    (ID_RUN, DT_INICIO, NM_SEGMENTO, STATUS, USR_EXECUTOU)
                    VALUES (:1, SYSDATE, :2, 'CONCLUIDO', :3)
                """, (id_run, segmento, current_user.login))

                for c in checks:

                    if str(c["id_check"]) not in selecionados:
                        continue

                    status = "ERRO"
                    qtd = 0
                    msg = ""

                    try:
                        sql_check = (c.get("eval_sql") or "").strip()

                        if sql_check:

                            # 🔥 DETECTA SE JA É COUNT
                            if "COUNT(" in sql_check.upper():
                                cur.execute(sql_check)
                                qtd = cur.fetchone()[0] or 0
                            else:
                                cur.execute(f"SELECT COUNT(*) FROM ({sql_check}) TMP")
                                qtd = cur.fetchone()[0] or 0

                        check_kind = (c.get("check_kind") or "").upper()

                        # ✅ STATUS CORRETO
                        if qtd == 0:
                            status = "OK"
                        elif check_kind in ["BLOCK", "ERRO"]:
                            status = "ERRO"
                        else:
                            status = "ALERTA"

                        msg = f"{qtd} inconsistência(s)"

                    except Exception as e:
                        print(f"Erro check {c['id_check']}: {e}")
                        status = "ERRO"
                        msg = str(e)

                    # ======================================================
                    # SNAPSHOT
                    # ======================================================
                    nm_view = c.get("nm_view") or "SEM_NOME"
                    check_kind = c.get("check_kind") or "PADRAO"
                    eval_mode = c.get("eval_mode") or "DEFAULT"

                    cur.execute("""
                        INSERT INTO GVDW_B2B.TB_CHECK_RUN_ITEM (
                            ID_RUN_ITEM,
                            ID_RUN,
                            ID_CHECK,
                            VERSAO_CHECK,
                            NM_VIEW,
                            CHECK_KIND,
                            EVAL_MODE,
                            EVAL_SQL_SNAPSHOT,
                            FINALIDADE_SNAP,
                            RESULT_STATUS,
                            RESULT_QTD,
                            MSG_RESULT,
                            DT_EXECUCAO
                        )
                        VALUES (
                            (SELECT NVL(MAX(ID_RUN_ITEM),0)+1 FROM GVDW_B2B.TB_CHECK_RUN_ITEM),
                            :1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11, SYSDATE
                        )
                    """, (
                        id_run,
                        c["id_check"],
                        parametros["versao"],
                        nm_view,
                        check_kind,
                        eval_mode,
                        sql_check,
                        c.get("finalidade"),
                        status,
                        qtd,
                        msg
                    ))

                conn.commit()

        # ======================================================
        # ÚLTIMO RUN
        # ======================================================
        id_run = None

        if segmento:
            cur.execute("""
                SELECT MAX(ID_RUN)
                FROM GVDW_B2B.TB_CHECK_RUN
                WHERE NM_SEGMENTO = :1
            """, (segmento,))
            id_run = cur.fetchone()[0]

        # ======================================================
        # RESULTADOS
        # ======================================================
        if id_run:
            cur.execute("""
                SELECT ID_CHECK, RESULT_STATUS
                FROM GVDW_B2B.TB_CHECK_RUN_ITEM
                WHERE ID_RUN = :1
            """, (id_run,))

            for id_check, status in cur.fetchall():
                status_por_check[id_check] = status
                if status in resumo:
                    resumo[status] += 1

        total = len(checks)
        executados = len(status_por_check)
        progresso = f"{executados}/{total}" if total else "0/0"

    finally:
        cur.close()
        conn.close()

    return render_template(
        "rv/checklist.html",
        segmentos=segmentos,
        checks=checks,
        status_por_check=status_por_check,
        resumo=resumo,
        progresso=progresso,
        parametros=parametros,
        versoes_disponiveis=versoes_disponiveis,
        segmento=segmento
    )

@rv_bp.route("/consultar/<int:id_check>")
@login_required
def consultar(id_check):

    conn = get_connection()
    cur = conn.cursor()

    try:
        # ======================================================
        # 🔥 PEGAR ÚLTIMO RUN DO CHECK
        # ======================================================
        cur.execute("""
            SELECT
                ID_CHECK,
                NM_VIEW,
                CHECK_KIND,
                EVAL_MODE,
                EVAL_SQL_SNAPSHOT,
                FINALIDADE_SNAP
            FROM GVDW_B2B.TB_CHECK_RUN_ITEM
            WHERE ID_CHECK = :1
            ORDER BY DT_EXECUCAO DESC
        """, (id_check,))

        row = cur.fetchone()

        if not row:
            return {"erro": "Nenhuma execução encontrada"}

        cols = [c[0].lower() for c in cur.description]
        d = dict(zip(cols, row))

        nm_view = d.get("nm_view")
        eval_mode = (d.get("eval_mode") or "").upper()
        eval_sql = d.get("eval_sql_snapshot")

        # tratar LOB
        if hasattr(eval_sql, "read"):
            eval_sql = eval_sql.read()

        eval_sql = (eval_sql or "").strip()

        # ======================================================
        # 🧠 MONTAR SQL DE DETALHE
        # ======================================================
        if eval_mode == "SQL_CUSTOM" and eval_sql:

            # 🔥 caso seja COUNT
            if "COUNT(" in eval_sql.upper():

                # tenta identificar coluna padrão
                sql = f"""
                    SELECT *
                    FROM {nm_view}
                    WHERE NVL(DIFERENCA, 0) <> 0
                """

            else:
                # já retorna linhas
                sql = eval_sql

        else:
            # fallback seguro
            sql = f"SELECT * FROM {nm_view}"

        # ======================================================
        # ▶ EXECUTAR QUERY
        # ======================================================
        cur.execute(sql)

        rows = cur.fetchall()
        colnames = [c[0] for c in cur.description]

        resultado = []

        for r in rows:
            linha = {}

            for i, v in enumerate(r):

                if hasattr(v, "read"):
                    v = v.read()

                linha[colnames[i]] = v

            resultado.append(linha)

        return {
            "qtd": len(resultado),
            "dados": resultado
        }

    except Exception as e:
        return {"erro": str(e)}

    finally:
        cur.close()
        conn.close()
# ======================================================
# ✅ ATUALIZAR PARÂMETRO (VIA MODAL)
# ======================================================
@rv_bp.route("/atualizar_parametro", methods=["POST"])
@login_required
def atualizar_parametro():

    conn = get_connection()
    cur = conn.cursor()

    try:
        # ========================================
        # 📥 RECEBER DADOS DO JS
        # ========================================
        segmento = request.form.get("segmento")
        anomes = request.form.get("anomes")
        versao = request.form.get("versao")
        versao_anterior = request.form.get("versao_anterior")

        # ========================================
        # ✅ VALIDAÇÃO
        # ========================================
        if not segmento or not versao or not anomes:
            return {"status": "erro", "msg": "Versão atual não informada"}

        # ========================================
        # ✅ MERGE (UPSERT)
        # ========================================
        cur.execute("""
                    MERGE INTO GVDW_OWNER.RV_B2B_PARAMETROS_VALIDACAO T
                    USING (SELECT :segmento AS SEGMENTO FROM DUAL) S
                    ON (T.SEGMENTO = S.SEGMENTO)

                    WHEN MATCHED THEN
                        UPDATE SET
                            T.ID_VERSAO = :versao,
                            T.ANOMES = :anomes,
                            T.ID_VERSAO_ANTERIOR = :versao_ant

                    WHEN NOT MATCHED THEN
                        INSERT (SEGMENTO, ID_VERSAO, ANOMES, ID_VERSAO_ANTERIOR)
                        VALUES (:segmento, :versao, :anomes, :versao_ant)

                """, {
                    "segmento": segmento,
                    "versao": versao,
                    "anomes": anomes,
                    "versao_ant": versao_anterior
                })

        conn.commit()

        return {"status": "ok"}

    except Exception as e:
        conn.rollback()
        return {"status": "erro", "msg": str(e)}

    finally:
        cur.close()
        conn.close()



@rv_bp.route("/")
@login_required
def index():
    return redirect(url_for("rv_bp.checklist"))


@rv_bp.route("/detalhe/<int:id_check>")
@login_required
def detalhe(id_check):

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT *
            FROM GVDW_B2B.TB_CHECK_RUN_ITEM
            WHERE ID_CHECK = :1
            ORDER BY DT_EXECUCAO DESC
        """, (id_check,))

        dados = cur.fetchall()

    finally:
        cur.close()
        conn.close()

    return render_template("rv/detalhe.html", dados=dados)
