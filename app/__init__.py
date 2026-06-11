from flask import Flask
from flask_login import LoginManager

login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.secret_key = "datapulse-secret-dev"

    login_manager.init_app(app)

    # ✅ IMPORTS DO USER LOADER
    from app.services.usuario_service import buscar_usuario_por_id
    from app.models.usuario_login import UsuarioLogin

    # ✅ USER LOADER (OBRIGATÓRIO)
    @login_manager.user_loader
    def load_user(user_id):
        usuario = buscar_usuario_por_id(int(user_id))

        if not usuario:
            return None

        return UsuarioLogin(
            usuario["id_usuario"],
            usuario["login"]
        )

    # IMPORTS
    from app.routes.auth import auth_bp
    from app.routes.home import home_bp
    from app.routes.rv import rv_bp

    from app.routes.admin import admin_bp
    from app.routes.admin.usuarios import admin_usuarios_bp
    from app.routes.admin.admin_modulo_routes import admin_modulo_bp
    from app.routes.admin.perfis import admin_perfis_bp 
    from app.routes.admin.segmento import admin_segmentos_bp
    from app.routes.admin.estrutura import admin_estruturas_bp
    from app.routes.etl import etl_bp

    # REGISTRO
    app.register_blueprint(auth_bp, url_prefix="/")
    app.register_blueprint(home_bp)
    app.register_blueprint(admin_segmentos_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(admin_usuarios_bp)
    app.register_blueprint(admin_modulo_bp)
    app.register_blueprint(rv_bp)
    app.register_blueprint(admin_perfis_bp)
    app.register_blueprint(admin_estruturas_bp)
    app.register_blueprint(etl_bp)

    return app
