from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash
from app.services.usuario_service import buscar_perfis_usuario

from app.models.usuario_login import UsuarioLogin
from app.services.usuario_service import buscar_usuario_por_login

auth_bp = Blueprint("auth_bp", __name__)


# ======================================================
# ✅ LOGIN
# ======================================================
@auth_bp.route("/", methods=["GET", "POST"])
def login():

    # 🔹 GET → mostra tela
    if request.method == "GET":
        return render_template("login.html")

    # 🔹 POST (tentativa de login)
    login = request.form.get("login", "").strip().upper()
    senha = request.form.get("senha", "")

    usuario = buscar_usuario_por_login(login)

    # ✅ usuário não existe
    if not usuario:
        flash("Usuário não encontrado", "error")
        return redirect(url_for("auth_bp.login"))

    # ✅ usuário inativo
    if usuario.get("ativo") != "S":
        flash("Usuário inativo", "error")
        return redirect(url_for("auth_bp.login"))

    # ✅ senha incorreta
    if not check_password_hash(usuario.get("password_hash"), senha):
        flash("Senha inválida", "error")
        return redirect(url_for("auth_bp.login"))

    # ✅ limpa sessão
    session.clear()

    # ✅ cria usuário Flask-Login
    user = UsuarioLogin(
        usuario["id_usuario"],
        usuario["login"]
    )

    login_user(user)

    # ✅ salva contexto básico
    session["login"] = usuario["login"]

    # ✅ 🔥 PERFIL (CORREÇÃO IMPORTANTE)
    perfis = buscar_perfis_usuario(usuario["id_usuario"])
    session["perfil"] = perfis[0] if perfis else None

    # 🔍 debug
    print("PERFIS DO USUÁRIO:", perfis)
    print("PERFIL NA SESSÃO:", session["perfil"])

    # ✅ REDIRECT PRINCIPAL
    return redirect(url_for("home_bp.dashboard"))

    # ✅ fallback (segurança contra erro de retorno)
    # nunca deve chegar aqui, mas evita erro 500
    return redirect(url_for("auth_bp.login"))


# ======================================================
# ✅ LOGOUT
# ======================================================
@auth_bp.route("/logout")
@login_required
def logout():

    logout_user()
    session.clear()

    flash("Logout realizado com sucesso", "info")

    return redirect(url_for("auth_bp.login"))