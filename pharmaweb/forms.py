from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, DateField, DecimalField, IntegerField, TextAreaField, BooleanField, SubmitField,FileField,validators
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError,DataRequired, Optional,NumberRange
from .models import Utilisateur, Medicament, Patient
from flask import request



ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

CATEGORIES_MEDICAMENTS = [
    # Antibiotiques
    ('ANTIBIOTIQUES_PENICILLINES', 'Antibiotiques - Pénicillines'),
    ('ANTIBIOTIQUES_CEPHALOSPORINES', 'Antibiotiques - Céphalosporines'),
    ('ANTIBIOTIQUES_MACROLIDES', 'Antibiotiques - Macrolides'),
    
    # Antalgiques
    ('ANALGESIQUES_OPIOIDES', 'Antalgiques - Opioïdes'),
    ('ANALGESIQUES_NSAID', 'Antalgiques - Anti-inflammatoires'),
    
    # Cardiovasculaire
    ('CARDIO_ANTIHYPERTENSEURS', 'Cardio - Antihypertenseurs'),
    ('CARDIO_DIURETIQUES', 'Cardio - Diurétiques'),
    
    # Autres
    ('DERMATO_CORTICOIDES', 'Dermatologie - Corticoides'),
    ('DIABETE_INSULINES', 'Diabète - Insulines'),
    ('GASTRO_ANTIACIDES', 'Gastro - Antiacides'),
    ('PSY_ANTIDEPRESSEURS', 'Psychiatrie - Antidépresseurs'),
    ('NEURO_ANTIEPILEPTIQUES', 'Neurologie - Antiépileptiques'),
    ('ONCO_CHIMIOTHERAPIE', 'Oncologie - Chimiothérapie'),
    ('OTC_DOULEUR', 'Automédication - Douleur'),
    ('OTC_GRIPPE', 'Automédication - Grippe'),
    ('PEDIATRIE_VACCINS', 'Pédiatrie - Vaccins'),
    ('GYNECO_CONTRACEPTION', 'Gynécologie - Contraception')
]

class LoginForm(FlaskForm):
    username = StringField('Login', validators=[DataRequired()])  # Changé de 'login' à 'username' pour correspondre au template
    password = PasswordField('Mot de passe', validators=[DataRequired()])
    remember = BooleanField('Se souvenir de moi')  # Ajout du champ remember
    submit = SubmitField('Se connecter')

class UtilisateurForm(FlaskForm):
    nom = StringField('Nom', validators=[DataRequired()])
    prenom = StringField('Prénom', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    telephone = StringField('Téléphone')
    role = SelectField('Rôle', choices=[
        ('admin', 'Administrateur'),
        ('pharmacien', 'Pharmacien'),
        ('caissier', 'Caissier'),
        ('preparateur', 'Préparateur')
    ], validators=[DataRequired()])
    login = StringField('Login', validators=[DataRequired(), Length(min=4)])
    password = PasswordField('Mot de passe', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmer le mot de passe', 
                                   validators=[DataRequired(), EqualTo('password')])
    actif = BooleanField('Actif', default=True)
    submit = SubmitField('Enregistrer')

    def validate_login(self, login):
        user = Utilisateur.query.filter_by(login=login.data).first()
        if user:
            raise ValidationError('Ce login est déjà utilisé. Veuillez en choisir un autre.')

    def validate_email(self, email):
        user = Utilisateur.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Cet email est déjà utilisé.')

class PatientForm(FlaskForm):
    code_patient = StringField('Code Patient', validators=[DataRequired()])
    nom = StringField('Nom', validators=[DataRequired()])
    prenom = StringField('Prénom', validators=[DataRequired()])
    date_naissance = DateField('Date de naissance', format='%Y-%m-%d')
    sexe = SelectField('Sexe', choices=[
        ('M', 'Masculin'),
        ('F', 'Féminin'),
        ('Autre', 'Autre')
    ])
    groupe_sanguin = StringField('Groupe sanguin')
    adresse = TextAreaField('Adresse')
    telephone = StringField('Téléphone')
    email = StringField('Email', validators=[Email()])
    assurance = StringField('Assurance')
    numero_assurance = StringField('Numéro d\'assurance')
    allergies = TextAreaField('Allergies')
    antecedents = TextAreaField('Antécédents')
    submit = SubmitField('Enregistrer')

    def validate_code_patient(self, code_patient):
        patient = Patient.query.filter_by(code_patient=code_patient.data).first()
        if patient:
            raise ValidationError('Ce code patient est déjà utilisé.')

class MedicamentForm(FlaskForm):
    # Champ catégorie dynamique (à remplir dans la vue)
    categorie = SelectField(
        'Catégorie',
        choices=[('', '-- Sélectionnez une catégorie --')] + CATEGORIES_MEDICAMENTS,
        validators=[DataRequired(message="La catégorie est obligatoire")]
    )
    
    code_cip = StringField('Code CIP', validators=[DataRequired()])
    
    nom_commercial = StringField(
        'Nom commercial', 
        validators=[DataRequired(message="Le nom commercial est obligatoire")]
    )
    
    dci = StringField(
        'DCI', 
        validators=[DataRequired(message="La DCI est obligatoire")]
    )
    
    forme_galenique = StringField('Forme galénique')
    dosage = StringField('Dosage')
    
    stock_actuel = IntegerField(
        'Stock actuel', 
        validators=[DataRequired(message="Le stock actuel est obligatoire")]
    )
    
    stock_minimum = IntegerField(
        'Stock minimum', 
        validators=[DataRequired(message="Le stock minimum est obligatoire")]
    )
    
    prix_achat = DecimalField(
        'Prix d\'achat', 
        places=2, 
        validators=[Optional()]
    )
    
    prix_vente = DecimalField(
        'Prix de vente', 
        places=2, 
        validators=[Optional()]
    )
    
    tva = DecimalField(
        'TVA (%)', 
        places=2, 
        validators=[Optional()]
    )
    
    remboursable = BooleanField('Remboursable', default=False)
    conditionnement = StringField('Conditionnement')
    
    date_peremption = DateField(
        'Date de péremption', 
        format='%Y-%m-%d', 
        validators=[Optional()]
    )
    
    
    
    
    fournisseur_id = SelectField(
        'Fournisseur',
        coerce=lambda x: int(x) if x and x != 'None' else None,
        validators=[Optional()],
        choices=[]
    )
    
    submit = SubmitField('Enregistrer')

    def validate_code_cip(self, field):
        """Validation conditionnelle du code CIP"""
        # Si c'est une modification (ID dans l'URL), on skip la validation si le CIP n'a pas changé
        if 'id' in request.view_args:
            medicament = Medicament.query.get(request.view_args['id'])
            if medicament and medicament.code_cip == field.data:
                return
        
        # Sinon, on vérifie l'unicité (pour les nouveaux médicaments)
        if Medicament.query.filter_by(code_cip=field.data).first():
            raise ValidationError('Ce code CIP existe déjà')

class OrdonnanceForm(FlaskForm):
    numero_ordonnance = StringField('Numéro d\'ordonnance', validators=[DataRequired()])
    medecin = StringField('Médecin prescripteur')
    date_prescription = DateField('Date de prescription', format='%Y-%m-%d')
    notes = TextAreaField('Notes')
    submit = SubmitField('Enregistrer')

class LigneOrdonnanceForm(FlaskForm):
    medicament_id = SelectField('Médicament', coerce=int, validators=[DataRequired()])
    quantite = IntegerField('Quantité', validators=[DataRequired()])
    posologie = TextAreaField('Posologie')
    duree_traitement = StringField('Durée du traitement')
    substitutable = BooleanField('Substitutable', default=True)
    submit = SubmitField('Ajouter')

class VenteForm(FlaskForm):
    patient_id = SelectField('Patient', coerce=int)
    mode_paiement = SelectField('Mode de paiement', choices=[
        ('especes', 'Espèces'),
        ('carte', 'Carte bancaire'),
        ('cheque', 'Chèque'),
        ('virement', 'Virement'),
        ('tiers_payant', 'Tiers payant')
    ], validators=[DataRequired()])
    informations_paiement = TextAreaField('Informations de paiement')
    montant_regle = DecimalField('Montant réglé', 
                                places=2,
                                validators=[
                                    DataRequired(),
                                    NumberRange(min=0)
                                ])
    submit = SubmitField('Enregistrer la vente')

class LigneVenteForm(FlaskForm):
    medicament_id = SelectField('Médicament', coerce=int, validators=[DataRequired()])
    quantite = IntegerField('Quantité', validators=[DataRequired()])
    remise = DecimalField('Remise (%)', places=2, default=0)
    submit = SubmitField('Ajouter au panier')

class CommandeForm(FlaskForm):
    fournisseur_id = SelectField('Fournisseur', coerce=int, validators=[DataRequired()])
    date_reception = DateField('Date de réception prévue', format='%Y-%m-%d')
    statut = SelectField('Statut', choices=[
        ('en_attente', 'En attente'),
        ('confirmee', 'Confirmée'),
        ('livree', 'Livrée'),
        ('annulee', 'Annulée')
    ], validators=[DataRequired()])
    notes = TextAreaField('Notes')
    submit = SubmitField('Enregistrer')

class ParametresPharmacieForm(FlaskForm):
    nom_pharmacie = StringField('Nom de la pharmacie', validators=[DataRequired()])
    adresse_rue = StringField('Adresse (rue)', validators=[DataRequired()])
    adresse_ville = StringField('Ville', validators=[DataRequired()])
    adresse_code_postal = StringField('Code postal', validators=[DataRequired()])
    adresse_pays = StringField('Pays', validators=[DataRequired()])
    telephone_principal = StringField('Téléphone principal', validators=[DataRequired()])
    telephone_secondaire = StringField('Téléphone secondaire')
    email = StringField('Email', validators=[Email()])
    site_web = StringField('Site web')
    rccm = StringField('RCCM')
    numero_tva = StringField('Numéro de TVA')
    numero_ordre_pharmaciens = StringField('Numéro d\'ordre des pharmaciens')
    responsable_legal = StringField('Responsable légal')
    message_accueil_recu = TextAreaField('Message d\'accueil')
    inclure_logo = BooleanField('Inclure le logo')
    submit = SubmitField('Mettre à jour')
    
class ProformaForm(FlaskForm):
    reference = StringField('Référence', validators=[DataRequired()])
    client = StringField('Client', validators=[DataRequired()])
    date_validite = DateField('Date validité', format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField('Enregistrer')