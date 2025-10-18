from flask import Flask
from flask_jwt_extended import JWTManager
from datetime import timedelta
import uuid

jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = str(uuid.uuid4())
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)

    jwt.init_app(app)

    from .auth import auth_bp
    from .sql import sql_bp
    from .patch import patch_bp
    from .dis import dis_bp
    from .journal import journal_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(sql_bp, url_prefix='/sql')
    app.register_blueprint(patch_bp, url_prefix='/patch')
    app.register_blueprint(dis_bp, url_prefix='/dis')
    app.register_blueprint(journal_bp, url_prefix='/journal')

    return app
