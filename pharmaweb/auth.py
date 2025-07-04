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
        user = Utilisateur.query.filter_by(login=form.username.data).first()  # Recherche par le champ login
        
        # Vérification de l'utilisateur et du mot de passe
        if user is None or not user.verify_password(form.password.data):
            flash('Nom d\'utilisateur ou mot de passe invalide', 'danger')
            return redirect(url_for('auth.login'))
        
        # Vérification si le compte est actif
        if not user.actif:
            flash('Ce compte est désactivé', 'warning')
            return redirect(url_for('auth.login'))
        
        # Connexion de l'utilisateur
        login_user(user, remember=form.remember.data)
        
        # Redirection selon le rôle
        next_page = request.args.get('next')
        if not next_page:
            if user.role == 'admin':
                next_page = url_for('admin.dashboard')
            else:
                next_page = url_for('ventes.dashboard')
        
        flash('Connexion réussie!', 'success')
        return redirect(next_page)
    
    return render_template('auth/login.html', form=form)

@auth.route('/logout')
def logout():
    logout_user()
    flash('Vous avez été déconnecté avec succès.', 'info')
    return redirect(url_for('main.index'))