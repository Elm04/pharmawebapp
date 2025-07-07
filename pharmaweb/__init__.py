from flask import Flask
from config import Config
from .extensions import db, login_manager, migrate
from werkzeug.security import generate_password_hash
from .models import Utilisateur, ParametrePharmacie
from pharmaweb.filters import format_currency
from datetime import datetime
from flask_wtf.csrf import CSRFProtect

def mainapp(config_class=Config):
    """Factory d'application Flask"""
    app = Flask(__name__)
    
    # Configuration de l'application
    app.config.from_object(config_class)
    
     # Debug: Affiche la configuration
    print("DB URL:", app.config['SQLALCHEMY_DATABASE_URI'])
    print("Engine Options:", app.config['SQLALCHEMY_ENGINE_OPTIONS'])
    
    # Initialisation des extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf = CSRFProtect(app)
    
    # Configuration du LoginManager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
    login_manager.login_message_category = 'warning'
    
    # Filtres Jinja2
    app.jinja_env.filters['format_currency'] = format_currency
    
    @app.template_filter('format_datetime')
    def format_datetime_filter(value, format="%d/%m/%Y %H:%M"):
        if value is None:
            return ""
        if isinstance(value, str):
            value = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        return value.strftime(format)
    
    # Configuration spéciale pour SQLite
    if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite'):
        from sqlalchemy import event
        from sqlalchemy.engine import Engine
        
        @event.listens_for(Engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
    
    # Importation des blueprints
    from .auth import auth
    from .views import views
    
    # Enregistrement des blueprints
    app.register_blueprint(auth)
    app.register_blueprint(views)
    
    # Context processor
    @app.context_processor
    def inject_parametres():
        parametres = ParametrePharmacie.query.first()
        return dict(parametres_pharmacie=parametres if parametres else None)
    
    # Initialisation de la base de données
    with app.app_context():
        initialize_database()
    
    return app

def initialize_database():
    """Initialise la base de données avec des valeurs par défaut"""
    from .models import ParametrePharmacie, Utilisateur
    
    db.create_all()
    
    if not ParametrePharmacie.query.first():
        db.session.add(ParametrePharmacie())
    
    if not Utilisateur.query.filter_by(role='admin').first():
        admin = Utilisateur(
            nom="Admin",
            prenom="System",
            email="admin@pharmagest.com",
            telephone="+1234567890",
            role="admin",
            login="admin",
            password=generate_password_hash("admin123"),
            actif=True
        )
        db.session.add(admin)
    
    if not Utilisateur.query.filter_by(role='caissier').first():
        caissier = Utilisateur(
            nom="Dupont",
            prenom="Jean",
            email="caissier@pharmagest.com",
            telephone="+0987654321",
            role="caissier",
            login="caissier",
            password=generate_password_hash("caissier123"),
            actif=True
        )
        db.session.add(caissier)
    
    db.session.commit()