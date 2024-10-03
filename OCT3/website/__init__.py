from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
from flask_socketio import SocketIO  # Import SocketIO

db = SQLAlchemy()
DB_NAME = "database.db"
socketio = SocketIO()  # Initialize SocketIO without app


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'I am a hacker!'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)
    socketio.init_app(app)  # Initialize SocketIO with app

    from .views import views
    from .views_creator import views_creator
    from .views_client import views_client
    from .views_attendee import views_attendee
    from .views_supplier import views_supplier
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(views_creator, url_prefix='/')
    app.register_blueprint(views_client, url_prefix='/')
    app.register_blueprint(views_attendee, url_prefix='/')
    app.register_blueprint(views_supplier, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    from .models import Users6, Note
    
    with app.app_context():
        db.create_all()

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return Users6.query.get(int(id))

    return app


def create_database(app):
    if not path.exists('website/' + DB_NAME):
        db.create_all(app=app)
        print('Created Database!')
