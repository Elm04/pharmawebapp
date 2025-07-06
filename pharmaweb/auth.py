from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user
from .models import Utilisateur
from .forms import LoginForm
from . import login_manager  # Importez login_manager depuis votre package

auth = Blueprint('auth', __name__)


# Configuration du user_loader
@login_manager.user_loader
def load_user(user_id):
    """Charge l'utilisateur à partir de l'ID stocké dans la session"""
    return Utilisateur.query.get(int(user_id))

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        try:
            user = Utilisateur.query.filter_by(login=form.username.data).first()
            
            # Debug: Afficher les valeurs comparées
            print(f"Tentative de connexion: {form.username.data}")
            print(f"Utilisateur trouvé: {user}")
            if user:
                print(f"Hash stocké: {user.password}")
                from werkzeug.security import check_password_hash
                print(f"Mot de passe testé: {form.password.data}")
                print(f"Résultat vérification: {check_password_hash(user.password, form.password.data)}")
            
            if not user:
                flash('Identifiant incorrect', 'danger')
                return redirect(url_for('auth.login'))
            
            if not check_password_hash(user.password, form.password.data):
                flash('Mot de passe incorrect', 'danger')
                return redirect(url_for('auth.login'))
            
            if not user.actif:
                flash('Compte désactivé', 'warning')
                return redirect(url_for('auth.login'))
            
            login_user(user, remember=form.remember.data)
            flash(f'Connexion réussie! Bienvenue {user.prenom}', 'success')
            
            return redirect(url_for('views.admin_dashboard' if user.role == 'admin' else 'views.ventes_dashboard'))
            
        except Exception as e:
            print(f"ERREUR CONNEXION: {str(e)}")
            flash('Erreur technique lors de la connexion', 'danger')
    
    return render_template('auth/login.html', form=form)

@auth.route('/logout')
def logout():
    logout_user()
    flash('Vous avez été déconnecté avec succès.', 'info')
    return redirect(url_for('views.index'))