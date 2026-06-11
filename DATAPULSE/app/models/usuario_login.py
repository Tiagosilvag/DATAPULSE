from flask_login import UserMixin


class UsuarioLogin(UserMixin):

    def __init__(self, id_usuario, login):
        self.id = str(id_usuario)
        self.login = login

    def get_id(self):
        return self.id