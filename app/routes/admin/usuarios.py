from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required
from flask import jsonify
from app.db.connection import executar_transacao
from app.utils.decorators import perfil_required, modulo_required
from app.services.usuario_service import listar_usuarios, criar_usuario
from app.services.usuario_service import listar_perfis


from app.services.usuario_service import (
    listar_usuarios,
    criar_usuario,
    listar_perfis,
    listar_modulos
)

admin_usuarios_bp = Blueprint(
    "admin_usuarios_bp",
    __name__,
    url_prefix="/admin/usuarios"
)


# ======================================================
# ✅ LISTAR USUÁRIOS
# ======================================================
@admin_usuarios_bp.route("/", methods=["GET"])
@login_required
@perfil_required("ADMIN")
@modulo_required("ADMIN")
def listar():

    filtro = request.args.get("q", "").strip().lower()

    usuarios = listar_usuarios()
    perfis = listar_perfis()
    modulos = listar_modulos()

    # ✅ FILTRO
    if filtro:
        usuarios = [
            u for u in usuarios
            if filtro in (u.get("nome") or "").lower()
            or filtro in (u.get("login") or "").lower()
        ]

    return render_template(
        "admin/usuarios/list.html",
        usuarios=usuarios,
        perfis=perfis,
        modulos=modulos
    )


# ======================================================
# ✅ NOVO USUÁRIO
# ======================================================
@admin_usuarios_bp.route("/novo", methods=["GET", "POST"])
@login_required
@perfil_required("ADMIN")
@modulo_required("ADMIN")
def novo():

    perfis = listar_perfis()
    modulos = listar_modulos()

    if request.method == "POST":

        try:
            dados = {
                "login": request.form.get("login", "").strip().upper(),
                "nome": request.form.get("nome", "").strip(),
                "ativo": request.form.get("ativo", "S"),
                "perfis": request.form.getlist("perfis"),
                "modulos": request.form.getlist("modulos")  # ✅ novo
            }

            # ✅ validações
            if not dados["login"] or not dados["nome"]:
                raise Exception("Preencha login e nome")

            if not dados["perfis"]:
                raise Exception("Selecione pelo menos um perfil")

            criar_usuario(dados)

            flash("✅ Usuário criado com sucesso!", "success")
            return redirect(url_for("admin_usuarios_bp.listar"))

        except Exception as e:

            flash(f"❌ {str(e)}", "error")

            return render_template(
                "admin/usuarios/form.html",
                perfis=perfis,
                modulos=modulos
            )

    # ✅ GET
    return render_template(
        "admin/usuarios/form.html",
        perfis=perfis,
        modulos=modulos
    )


# ======================================================
# ✅ EDITAR USUÁRIO (AJAX)
# ======================================================
@admin_usuarios_bp.route("/editar-ajax", methods=["POST"])
@login_required
@perfil_required("ADMIN")
@modulo_required("ADMIN")
def editar_ajax():

    try:

        data = request.get_json()

        def _update(cursor):

            # 🔥 CONVERSÃO DE STATUS (RESOLVE O ERRO)
            status = data.get("status")
            status_db = 'S' if status == 'A' else 'N'

            # ✅ atualizar dados básicos
            cursor.execute("""
                UPDATE GVDW_OWNER.USUARIO_APP
                SET DS_LOGIN = :login,
                    NM_USUARIO = :nome,
                    FL_ATIVO = :status
                WHERE ID_USUARIO = :id
            """, {
                "id": data.get("id"),
                "login": data.get("login"),
                "nome": data.get("nome"),
                "status": status_db  # 🔥 corrigido aqui
            })

            # ✅ atualizar perfis
            if data.get("perfis") is not None:

                cursor.execute("""
                    DELETE FROM GVDW_OWNER.USUARIO_PERFIL
                    WHERE ID_USUARIO = :id
                """, {"id": data.get("id")})

                for p in data.get("perfis"):
                    cursor.execute("""
                        INSERT INTO GVDW_OWNER.USUARIO_PERFIL
                        (ID_USUARIO, ID_PERFIL)
                        VALUES (:id_usuario, :id_perfil)
                    """, {
                        "id_usuario": data.get("id"),
                        "id_perfil": p
                    })

            # ✅ atualizar módulos
            if data.get("modulos") is not None:

                cursor.execute("""
                    DELETE FROM GVDW_OWNER.USUARIO_MODULO
                    WHERE ID_USUARIO = :id
                """, {"id": data.get("id")})

                for m in data.get("modulos"):
                    cursor.execute("""
                        INSERT INTO GVDW_OWNER.USUARIO_MODULO
                        (ID_USUARIO, ID_MODULO, FL_EXECUCAO, FL_VISUALIZACAO)
                        VALUES (:id_usuario, :id_modulo, 'S', 'S')
                    """, {
                        "id_usuario": data.get("id"),
                        "id_modulo": m
                    })

        executar_transacao(_update)

        return {"sucesso": True}

    except Exception as e:
        print("ERRO EDITAR USUARIO:", e)
        return {"sucesso": False, "erro": str(e)}


