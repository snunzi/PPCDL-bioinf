import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
import os
from flask import Flask, request, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_session import Session
from config import Config
from flask_bootstrap import Bootstrap
import flask_excel as excel
from flask_debugtoolbar import DebugToolbarExtension
#from redis import Redis
#import rq
#from flask_wtf.csrf import CSRFProtect, generate_csrf, validate_csrf

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.login'
login.login_message = ('Please log in to access this page.')
bootstrap = Bootstrap()
sess = Session()
toolbar = DebugToolbarExtension()
#csrf = CSRFProtect()

def create_app(config_class=Config):
    app = Flask(__name__)
    #csrf.init_app(app)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    bootstrap.init_app(app)
    excel.init_excel(app)
    sess.init_app(app)
    toolbar.init_app(app)

    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.static import bp as static_bp
    app.register_blueprint(static_bp)

    return app

from app import models
