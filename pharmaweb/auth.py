from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user
from sqlalchemy import text
from sqlalchemy.exc import OperationalError, DatabaseError
from .models import Utilisateur
from .forms import LoginForm
from . import login_manager, db  # Ajoutez db à l'import

auth = Blueprint('auth', __name__)

@login_manager.user_loader
def load_user(user_id):
    """Charge l'utilisateur à partir de l'ID stocké dans la session"""
    try:
        return Utilisateur.query.get(int(user_id))
    except OperationalError as e:
        flash('Erreur de connexion à la base de données. Veuillez vérifier votre connexion Internet.', 'danger')
        return None
    except Exception as e:
        flash('Erreur technique lors du chargement de l\'utilisateur', 'danger')
        return None

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    
    if form.validate_on_submit():
        try:
            # Test de connexion à la base avant de continuer (version corrigée)
            db.session.execute(text('SELECT 1'))
            
            user = Utilisateur.query.filter_by(login=form.username.data).first()
            
            if not user:
                flash('Identifiant incorrect', 'danger')
                return redirect(url_for('auth.login'))
            
            from werkzeug.security import check_password_hash
            if not check_password_hash(user.password, form.password.data):
                flash('Mot de passe incorrect', 'danger')
                return redirect(url_for('auth.login'))
            
            if not user.actif:
                flash('Compte désactivé', 'warning')
                return redirect(url_for('auth.login'))
            
            login_user(user, remember=form.remember.data)
            flash(f'Connexion réussie! Bienvenue {user.prenom}', 'success')
            
            return redirect(url_for('views.admin_dashboard' if user.role == 'admin' else 'views.ventes_dashboard'))
            
        except OperationalError as e:
            print(f"ERREUR CONNEXION DB: {str(e)}")
            flash('Impossible de se connecter à la base de données. Veuillez vérifier votre connexion Internet.', 'danger')
            return render_template('auth/login.html', form=form)
            
        except DatabaseError as e:
            print(f"ERREUR DB: {str(e)}")
            flash('Erreur technique avec la base de données. Veuillez réessayer plus tard.', 'danger')
            return render_template('auth/login.html', form=form)
            
        except Exception as e:
            print(f"ERREUR INATTENDUE: {str(e)}")
            flash('Erreur technique lors de la connexion', 'danger')
            return render_template('auth/login.html', form=form)
    
    return render_template('auth/login.html', form=form)

@auth.route('/logout')
def logout():
    logout_user()
    flash('Vous avez été déconnecté avec succès.', 'info')
    return redirect(url_for('views.index'))