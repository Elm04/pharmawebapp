from flask import Flask
from config import Config
from .extensions import db, login_manager, migrate, csrf
from werkzeug.security import generate_password_hash
from .models import Utilisateur, ParametrePharmacie
from .filters import format_currency
from datetime import datetime

def mainapp(config_class='config.Config'):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialisation EXTENSIONS
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Configuration LoginManager
    login_manager.login_view = 'auth.login'

    # Import TARDIF des Blueprints
    from .auth import auth
    from .views import views
    app.register_blueprint(auth)
    app.register_blueprint(views)

    # Import TARDIF des modèles
    with app.app_context():
        from . import models
        db.create_all()
        initialize_default_data()

    return app

def initialize_default_data():
    from .models import ParametrePharmacie, Utilisateur

def initialize_extensions(app):
    """Initialise les extensions Flask"""
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    
    # Configuration LoginManager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
    login_manager.login_message_category = 'warning'

def configure_template_filters(app):
    """Configure les filtres de template"""
    app.jinja_env.filters['format_currency'] = format_currency
    
    @app.template_filter('format_datetime')
    def format_datetime_filter(value, format="%d/%m/%Y %H:%M"):
        if value is None:
            return ""
        if isinstance(value, str):
            value = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        return value.strftime(format)
    
    @app.context_processor
    def inject_parametres():
        parametres = ParametrePharmacie.query.first()
        return dict(parametres_pharmacie=parametres if parametres else None)

def register_blueprints(app):
    """Enregistre les blueprints"""
    from .auth import auth
    from .views import views
    
    app.register_blueprint(auth)
    app.register_blueprint(views)

def initialize_database(app):
    """Initialise la base de données"""
    db.create_all()
    
    if not ParametrePharmacie.query.first():
        default_params = ParametrePharmacie()
        db.session.add(default_params)
    
    create_default_users()
    db.session.commit()

def create_default_users():
    """Crée les utilisateurs par défaut"""
    if not Utilisateur.query.filter_by(role='admin').first():
        admin = Utilisateur(
            nom="Admin",
            prenom="System",
            email="admin@pharmagest.com",
            telephone="+1234567890",
            role="admin",
            login="admin",
            actif=True
        )
        admin.set_password("admin123")
        db.session.add(admin)

    if not Utilisateur.query.filter_by(role='caissier').first():
        caissier = Utilisateur(
            nom="Dupont",
            prenom="Jean",
            email="caissier@pharmagest.com",
            telephone="+0987654321",
            role="caissier",
            login="caissier",
            actif=True
        )
        caissier.set_password("caissier123")
        db.session.add(caissier)