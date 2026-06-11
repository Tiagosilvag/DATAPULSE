from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required
from app.db.connection import get_connection
from app.services import etl_service

etl_bp = Blueprint("etl_bp", __name__, url_prefix="/etl")


# ==========================================
# TELA DISPARO
# ==========================================
@etl_bp.route("/disparo")
@login_required
def tela_disparo():

    conn = get_connection()

    try:
        bases = etl_service.obter_bases(conn)
        return render_template("etl/disparo.html", bases=bases)
    finally:
        conn.close()


# ==========================================
# DISPARAR EXECUÇÃO
# ==========================================
@etl_bp.route("/disparar", methods=["POST"])
@login_required
def disparar():

    conn = get_connection()

    try:
        data = request.get_json()

        bases = data.get("bases", [])
        anomes = data.get("anomes")
        usuario = "web"

        resultado = etl_service.disparar_multiplas_execucoes(
            conn,
            bases,
            anomes,
            usuario
        )

        return jsonify(resultado)

    except Exception as e:
        return jsonify({
            "status": "erro",
            "msg": str(e)
        }), 500

    finally:
        conn.close()


# ==========================================
# FILA
# ==========================================
@etl_bp.route("/fila")
@login_required
def fila():

    conn = get_connection()

    try:
        page = int(request.args.get("page", 1))
        return jsonify(etl_service.obter_fila(conn, page=page))

    except Exception as e:
        print("ERRO FILA:", e)
        return jsonify({
            "dados": [],
            "page": 1,
            "total_paginas": 1
        })

    finally:
        conn.close()


# ==========================================
# MONITOR (VIEW)
# ==========================================
@etl_bp.route("/monitor")
@login_required
def monitor():

    conn = get_connection()

    try:
        fila = etl_service.obter_fila(conn)
        bases = etl_service.obter_bases(conn)

        dados = fila.get("dados", [])

        def norm(s):
            return (s or "").lower()

        return render_template(
            "etl/monitor.html",
            fila=fila,
            bases=bases,
            total=len(dados),
            concluidas=len([f for f in dados if norm(f.get("status")) == "concluido"]),
            executando=len([f for f in dados if norm(f.get("status")) == "executando"]),
            pendentes=len([f for f in dados if norm(f.get("status")) == "pendente"]),
            falhas=len([f for f in dados if norm(f.get("status")) == "falha"])
        )

    finally:
        conn.close()


# ==========================================
# ✅ MONITOR DATA (RESTAURADO COMPLETO)
# ==========================================
@etl_bp.route("/monitor/data")
@login_required
def monitor_data():

    conn = get_connection()

    try:
        base = request.args.get("base")
        ano_mes = request.args.get("ano_mes")

        if not ano_mes or ano_mes == "null":
            ano_mes = None

        fila = etl_service.obter_fila(conn).get("dados", [])

        def norm(s):
            return (s or "").lower()

        metrics = {
            "total": len(fila),
            "concluidas": len([f for f in fila if norm(f.get("status")) == "concluido"]),
            "executando": len([f for f in fila if norm(f.get("status")) == "executando"]),
            "pendentes": len([f for f in fila if norm(f.get("status")) == "pendente"]),
            "falhas": len([f for f in fila if norm(f.get("status")) == "falha"])
        }

        pipeline = etl_service.gerar_pipeline_base(base) if base else []

        detalhe, validacao = etl_service.obter_execucao_base(
            conn,
            base,
            ano_mes
        ) if base else (None, None)

        volumetria = {
            "labels": [],
            "atual": []
        }

        if base:
            volumetria = etl_service.obter_volumetria(conn, base, ano_mes)

        return jsonify({
            "metrics": metrics,
            "fila": fila,
            "pipeline": pipeline,
            "detalhe": detalhe,
            "validacao": validacao,
            "volumetria": volumetria
        })

    except Exception as e:
        print("ERRO MONITOR DATA:", e)
        return jsonify({}), 500

    finally:
        conn.close()


# ==========================================
# ✅ ACOMPANHAMENTO (MANTIDO)
# ==========================================
@etl_bp.route("/acompanhamento")
@login_required
def acompanhamento():
    return render_template("etl/acompanhamento.html")