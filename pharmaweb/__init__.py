from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

# Initialisation des extensions
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()

def create_app(config_class='config.Config'):
    """Factory d'application compatible WSGI"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Configuration des extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Veuillez vous connecter'

    # Import tardif des blueprints
    from .auth import auth_bp
    from .views import views_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(views_bp)

    # Initialisation DB
    with app.app_context():
        db.create_all()
        from .models import ParametrePharmacie, Utilisateur
        if not ParametrePharmacie.query.first():
            db.session.add(ParametrePharmacie())
        
        if not Utilisateur.query.filter_by(role='admin').first():
            admin = Utilisateur(
                nom="Admin", 
                login="admin",
                password='admin123',  # Le modèle doit hasher ce mot de passe
                role='admin'
            )
            db.session.add(admin)
        
        db.session.commit()

    return app