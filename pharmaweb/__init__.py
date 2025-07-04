from flask import Flask
from config import Config
from .extensions import db, login_manager, migrate  # Import depuis extensions.py

def mainapp(config_class=Config):
    """Factory d'application Flask"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialisation des extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    
    # Configuration LoginManager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
    login_manager.login_message_category = 'warning'
    
    # Importation retardée des blueprints
    from pharmaweb.auth import auth
    from pharmaweb.views import views
    
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