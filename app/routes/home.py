from flask import Blueprint, render_template
from flask_login import login_required, current_user

from app.services.usuario_service import buscar_modulos_usuario

home_bp = Blueprint("home_bp", __name__)


@home_bp.route("/dashboard")
@login_required
def dashboard():

    modulos = buscar_modulos_usuario(current_user.id)

    return render_template(
        "dashboard.html",
        usuario=current_user.login,
        modulos=modulos
    )
