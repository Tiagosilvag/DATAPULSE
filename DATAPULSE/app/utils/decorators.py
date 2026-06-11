from functools import wraps
from flask import redirect, url_for, session
from flask_login import current_user

from app.services.usuario_service import buscar_modulos_usuario


# ======================================================
# ✅ PERFIL REQUIRED
# ======================================================
def perfil_required(*perfis_permitidos):

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):

            print("PERFIL NA SESSÃO:", session.get("perfil"))
            print("PERFIS PERMITIDOS:", perfis_permitidos)

            if not current_user.is_authenticated:
                return redirect(url_for("auth_bp.login"))

            perfil_usuario = session.get("perfil")

            if perfil_usuario not in perfis_permitidos:
                return redirect(url_for("home_bp.dashboard"))

            return func(*args, **kwargs)

        return wrapper
    return decorator


# ======================================================
# ✅ MODULO REQUIRED (CORRIGIDO)
# ======================================================
def modulo_required(*modulos_permitidos):

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):

            if not current_user.is_authenticated:
                return redirect(url_for("auth_bp.login"))

            # 🔥 busca direto do banco
            modulos_usuario = buscar_modulos_usuario(current_user.id)

            # 🔥 normaliza os códigos
            codigos = [m["codigo"].strip().upper() for m in modulos_usuario]

            print("🔥 MODULOS USER:", codigos)
            print("🔥 PERMITIDOS:", modulos_permitidos)

            # 🔥 validação correta
            if not any(m.upper() in codigos for m in modulos_permitidos):
                print("❌ BLOQUEADO")
                return redirect(url_for("home_bp.dashboard"))

            print("✅ LIBERADO")
            return func(*args, **kwargs)

        return wrapper
    return decorator