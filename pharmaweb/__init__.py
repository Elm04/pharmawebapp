from flask import Flask
from config import Config
from .extensions import db, login_manager, migrate  # Import depuis extensions.py
from werkzeug.security import generate_password_hash
from .models import Utilisateur, ParametrePharmacie
from pharmaweb.filters import format_currency
from datetime import datetime
from flask_wtf.csrf import CSRFProtect

def mainapp(config_class=Config):
    """Factory d'application Flask"""
    app = Flask(__name__)
    
    app.config.from_object(config_class or 'config.Config')
        
    app.jinja_env.filters['format_currency'] = format_currency
    
    # Initialisation des extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    
    # Configuration LoginManager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
    login_manager.login_message_category = 'warning'
    csrf = CSRFProtect(app)
    
    @app.template_filter('format_datetime')
    def format_datetime_filter(value, format="%d/%m/%Y %H:%M"):
        if value is None:
            return ""
        if isinstance(value, str):
            value = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")  # Adaptez au format de votre date si nécessaire
        return value.strftime(format)
    
    # Importation retardée des blueprints
    from pharmaweb.auth import auth
    from pharmaweb.views import views
    
    @app.context_processor
    def inject_parametres():
        parametres = ParametrePharmacie.query.first()
        return dict(parametres_pharmacie=parametres if parametres else None)
    
    # Enregistrement des blueprints
    app.register_blueprint(auth)
    app.register_blueprint(views)
    
    # Initialisation de la DB dans un contexte d'application
    with app.app_context():
        initialize_database()
    
    return app




def initialize_database():
    """Fonction séparée pour l'initialisation de la base de données"""
    from pharmaweb.models import ParametrePharmacie
    
    db.create_all()
    
    if not ParametrePharmacie.query.first():
        default_params = ParametrePharmacie()
        db.session.add(default_params)
        db.session.commit()
    
    # Créer l'admin par défaut s'il n'existe pas
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

    # Créer le caissier par défaut s'il n'existe pas
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