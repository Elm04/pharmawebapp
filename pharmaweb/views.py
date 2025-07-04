from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from pharmaweb import db
from pharmaweb.models import (Utilisateur, Medicament, Patient, Fournisseur, 
                            ParametrePharmacie, Vente, LigneVente)
from pharmaweb.forms import (UtilisateurForm, MedicamentForm, PatientForm, 
                            ParametresPharmacieForm, VenteForm, LigneVenteForm)
from pharmaweb.decorators import admin_required, caissier_required
# from pharmaweb.utils.helpers import save_image
from datetime import datetime

views = Blueprint('views', __name__)

# ---------------------------
# Routes communes
# ---------------------------

@views.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('main.admin_dashboard'))
        elif current_user.role in ['caissier', 'pharmacien']:
            return redirect(url_for('main.ventes_dashboard'))
    return render_template('index.html')

@views.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

# ---------------------------
# Section Admin
# ---------------------------

@views.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    stats = {
        'users': Utilisateur.query.count(),
        'medicaments': Medicament.query.count(),
        'patients': Patient.query.count()
    }
    return render_template('admin/dashboard.html', stats=stats)

@views.route('/admin/utilisateurs')
@login_required
@admin_required
def gestion_utilisateurs():
    users = Utilisateur.query.all()
    return render_template('admin/utilisateurs/liste.html', users=users)

@views.route('/admin/utilisateur/ajouter', methods=['GET', 'POST'])
@login_required
@admin_required
def ajouter_utilisateur():
    form = UtilisateurForm()
    if form.validate_on_submit():
        # Logique d'ajout d'utilisateur
        pass
    return render_template('admin/utilisateurs/ajouter.html', form=form)

# Ajouter d'autres routes admin ici...

# ---------------------------
# Section Ventes
# ---------------------------

@views.route('/ventes/dashboard')
@login_required
@caissier_required
def ventes_dashboard():
    return render_template('ventes/dashboard.html')

@views.route('/ventes/nouvelle-vente', methods=['GET', 'POST'])
@login_required
@caissier_required
def nouvelle_vente():
    form = VenteForm()
    form.patient_id.choices = [(p.id, f"{p.nom} {p.prenom}") for p in Patient.query.all()]
    
    if form.validate_on_submit():
        # Logique de création de vente
        pass
    
    return render_template('ventes/nouvelle_vente.html', form=form)

@views.route('/api/medicaments')
@login_required
def api_medicaments():
    search = request.args.get('q', '')
    medicaments = Medicament.query.filter(
        (Medicament.nom_commercial.ilike(f'%{search}%')) | 
        (Medicament.code_cip.ilike(f'%{search}%'))
    ).limit(10).all()
    
    results = [{
        'id': m.id,
        'text': f"{m.nom_commercial} - {m.code_cip} - Stock: {m.stock_actuel}",
        'prix': float(m.prix_vente),
        'stock': m.stock_actuel
    } for m in medicaments]
    
    return jsonify({'results': results})

# Ajouter d'autres routes ventes ici...