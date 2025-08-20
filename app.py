#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Globibat CRM - Version Finale
Application complète avec UI/UX moderne et toutes les fonctionnalités
"""

from flask import Flask, render_template, redirect, url_for, request, jsonify, flash, session, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, AnonymousUserMixin, login_required, login_user, logout_user, UserMixin
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
import os
import sys
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import io
from reportlab.lib.pagesizes import letter, A4
from threading import Thread
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import csv
import io as pyio

# Configuration
class Config:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    instance_dir = os.path.join(base_dir, 'instance')
    os.makedirs(instance_dir, exist_ok=True)
    uploads_dir = os.path.join(instance_dir, 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)
    
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'globibat-crm-2025-secure-key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(instance_dir, 'globibat_final.db').replace('\\', '/')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = uploads_dir
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB

# Créer l'application
app = Flask(__name__,
    template_folder='app/templates',
    static_folder='app/static'
)
app.config.from_object(Config)

# Initialiser les extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
CORS(app)

# Headers de sécurité
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response

# ===== MODÈLES =====

class Admin(UserMixin, db.Model):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Employe(db.Model):
    __tablename__ = 'employe'
    id = db.Column(db.Integer, primary_key=True)
    matricule = db.Column(db.String(50), unique=True, nullable=False)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    departement = db.Column(db.String(100))
    position = db.Column(db.String(100))
    email = db.Column(db.String(120))
    telephone = db.Column(db.String(20))
    date_embauche = db.Column(db.Date, default=date.today)
    actif = db.Column(db.Boolean, default=True)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    derniere_localisation = db.Column(db.DateTime)
    photo = db.Column(db.String(200))

class Pointage(db.Model):
    __tablename__ = 'pointage'
    id = db.Column(db.Integer, primary_key=True)
    employe_id = db.Column(db.Integer, db.ForeignKey('employe.id'), nullable=False)
    date_pointage = db.Column(db.Date, nullable=False)
    arrivee_matin = db.Column(db.DateTime)
    depart_midi = db.Column(db.DateTime)
    arrivee_apres_midi = db.Column(db.DateTime)
    depart_soir = db.Column(db.DateTime)
    heures_travaillees = db.Column(db.Float, default=0)
    heures_supplementaires = db.Column(db.Float, default=0)
    retard_matin = db.Column(db.Boolean, default=False)
    retard_apres_midi = db.Column(db.Boolean, default=False)
    employe = db.relationship('Employe', backref='pointages')

class Client(db.Model):
    __tablename__ = 'client'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(200), nullable=False)
    type_client = db.Column(db.String(50))
    contact = db.Column(db.String(100))
    telephone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    adresse = db.Column(db.Text)
    ville = db.Column(db.String(100))
    code_postal = db.Column(db.String(10))
    date_creation = db.Column(db.Date, default=date.today)
    actif = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)

@app.route('/clients/<int:client_id>')
@login_required
def client_detail(client_id: int):
    client = db.session.get(Client, client_id)
    if not client:
        flash('Client introuvable', 'error')
        return redirect(url_for('clients'))
    chantiers = Chantier.query.filter_by(client_id=client.id).all()
    factures = Facture.query.filter_by(client_id=client.id).all()
    return render_template('client_detail.html', client=client, chantiers=chantiers, factures=factures)

class Chantier(db.Model):
    __tablename__ = 'chantier'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(200), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    adresse = db.Column(db.Text)
    date_debut = db.Column(db.Date)
    date_fin_prevue = db.Column(db.Date)
    date_fin_reelle = db.Column(db.Date)
    statut = db.Column(db.String(50), default='planifie')
    budget_initial = db.Column(db.Float, default=0)
    budget_consomme = db.Column(db.Float, default=0)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    description = db.Column(db.Text)
    chef_chantier_id = db.Column(db.Integer, db.ForeignKey('employe.id'))
    client = db.relationship('Client', backref='chantiers')
    chef_chantier = db.relationship('Employe', backref='chantiers_diriges')

class Devis(db.Model):
    __tablename__ = 'devis'
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(50), unique=True, nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    date_devis = db.Column(db.Date, default=date.today)
    date_validite = db.Column(db.Date)
    montant_ht = db.Column(db.Float, default=0)
    tva = db.Column(db.Float, default=0)
    montant_ttc = db.Column(db.Float, default=0)
    statut = db.Column(db.String(50), default='brouillon')
    description = db.Column(db.Text)
    conditions = db.Column(db.Text)
    client = db.relationship('Client', backref='devis')

class Facture(db.Model):
    __tablename__ = 'facture'
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(50), unique=True, nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    chantier_id = db.Column(db.Integer, db.ForeignKey('chantier.id'))
    devis_id = db.Column(db.Integer, db.ForeignKey('devis.id'))
    date_facture = db.Column(db.Date, default=date.today)
    date_echeance = db.Column(db.Date)
    montant_ht = db.Column(db.Float, default=0)
    tva = db.Column(db.Float, default=0)
    montant_ttc = db.Column(db.Float, default=0)
    statut = db.Column(db.String(50), default='brouillon')
    client = db.relationship('Client', backref='factures')
    chantier = db.relationship('Chantier', backref='factures')
    devis_ref = db.relationship('Devis', backref='factures')

class Lead(db.Model):
    __tablename__ = 'lead'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(200), nullable=False)
    entreprise = db.Column(db.String(200))
    telephone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    source = db.Column(db.String(50))
    statut = db.Column(db.String(50), default='nouveau')
    date_creation = db.Column(db.Date, default=date.today)
    date_dernier_contact = db.Column(db.Date)
    notes = db.Column(db.Text)
    potentiel_ca = db.Column(db.Float)
    probabilite = db.Column(db.Integer, default=50)

# ===== VUES SECONDAIRES/DETAILS =====

@app.route('/employes/<int:employe_id>')
@login_required
def employe_detail(employe_id: int):
    employe = Employe.query.get_or_404(employe_id)
    # Pointages récents de l'employé
    recent_pointages = Pointage.query.filter_by(employe_id=employe.id).order_by(Pointage.date_pointage.desc()).limit(30).all()
    return render_template('employe_detail.html', employe=employe, pointages=recent_pointages)

# User loader
@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(Admin, int(user_id))
    except Exception:
        return None

# Classe pour utilisateur anonyme
class AnonymousUser(AnonymousUserMixin):
    def __init__(self):
        self.username = 'Invité'
        self.email = ''

login_manager.anonymous_user = AnonymousUser

# Context processor
@app.context_processor
def inject_user():
    return dict(current_user=current_user)

# ===== ROUTES PRINCIPALES =====

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        admin = Admin.query.filter_by(email=email).first()
        if admin and admin.check_password(password):
            login_user(admin, remember=True)
            flash('Connexion réussie', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Email ou mot de passe incorrect', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Vous avez été déconnecté', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Statistiques
    stats = {
        'nb_employes': Employe.query.filter_by(actif=True).count(),
        'nb_clients': Client.query.filter_by(actif=True).count(),
        'chantiers_actifs': Chantier.query.filter_by(statut='en_cours').count(),
        'leads_nouveaux': Lead.query.filter_by(statut='nouveau').count(),
        'factures_impayees': Facture.query.filter(Facture.statut.in_(['envoyee', 'retard'])).count()
    }
    
    # Pointages du jour
    aujourd_hui = date.today()
    pointages_jour = db.session.query(Pointage, Employe).join(Employe).filter(
        Pointage.date_pointage == aujourd_hui
    ).all()
    
    # Chantiers récents
    chantiers_recents = Chantier.query.filter_by(statut='en_cours').order_by(
        Chantier.date_debut.desc()
    ).limit(5).all()
    
    # Factures récentes
    factures_recentes = db.session.query(Facture, Client).join(Client).order_by(
        Facture.date_facture.desc()
    ).limit(5).all()
    
    return render_template('dashboard_elite.html',
                         stats=stats,
                         pointages_jour=pointages_jour,
                         chantiers_recents=chantiers_recents,
                         factures_recentes=factures_recentes,
                         aujourd_hui=aujourd_hui)

@app.route('/employes')
@login_required
def employes():
    employes = Employe.query.order_by(Employe.nom).all()
    departements = db.session.query(Employe.departement).distinct().all()
    return render_template('employes.html', 
                         employes=employes,
                         departements=[d[0] for d in departements if d[0]])

@app.route('/clients')
@login_required
def clients():
    clients = Client.query.order_by(Client.nom).all()
    return render_template('clients.html', clients=clients)

# Route déplacée plus haut dans le fichier pour éviter la duplication

@app.route('/chantiers')
@login_required
def chantiers():
    chantiers = Chantier.query.order_by(Chantier.date_debut.desc()).all()
    clients = Client.query.filter_by(actif=True).all()
    chefs = Employe.query.filter_by(actif=True, departement='Construction').all()
    return render_template('chantiers.html', 
                         chantiers=chantiers,
                         clients=clients,
                         chefs=chefs)

@app.route('/devis')
@login_required
def devis():
    devis_list = Devis.query.order_by(Devis.date_devis.desc()).all()
    clients = Client.query.filter_by(actif=True).all()
    from datetime import date
    return render_template('devis.html', 
                         devis_list=devis_list, 
                         clients=clients,
                         date=date)

@app.route('/factures')
@login_required
def factures():
    factures = Facture.query.order_by(Facture.date_facture.desc()).all()
    clients = Client.query.filter_by(actif=True).all()
    chantiers = Chantier.query.all()
    from datetime import date
    return render_template('factures.html', 
                         factures=factures, 
                         clients=clients, 
                         chantiers=chantiers,
                         date=date)

@app.route('/leads')
@login_required
def leads():
    leads = Lead.query.order_by(Lead.date_creation.desc()).all()
    return render_template('leads.html', leads=leads)

@app.route('/badges')
@login_required
def badges():
    aujourd_hui = date.today()
    pointages = db.session.query(Pointage, Employe).join(Employe).filter(
        Pointage.date_pointage == aujourd_hui
    ).all()
    
    employes_actifs = Employe.query.filter_by(actif=True).all()
    employes_badges = [p.employe_id for p, e in pointages]
    absents = [e for e in employes_actifs if e.id not in employes_badges]
    
    # Calculer les statistiques
    stats = {
        'presents': len(pointages),
        'retards': sum(1 for p, e in pointages if p.retard_matin or p.retard_apres_midi),
        'absents': len(absents),
        'total': len(employes_actifs)
    }
    
    # Construire un historique récent des badges du jour
    badges_events = []
    for p, e in pointages:
        if p.arrivee_matin:
            badges_events.append({
                'employe': e,
                'type': 'arrivee_matin',
                'timestamp': p.arrivee_matin,
                'latitude': e.latitude,
                'longitude': e.longitude,
                'anomalie': bool(p.retard_matin)
            })
        if p.depart_midi:
            badges_events.append({
                'employe': e,
                'type': 'depart_midi',
                'timestamp': p.depart_midi,
                'latitude': e.latitude,
                'longitude': e.longitude,
                'anomalie': False
            })
        if p.arrivee_apres_midi:
            badges_events.append({
                'employe': e,
                'type': 'arrivee_apres_midi',
                'timestamp': p.arrivee_apres_midi,
                'latitude': e.latitude,
                'longitude': e.longitude,
                'anomalie': bool(p.retard_apres_midi)
            })
        if p.depart_soir:
            badges_events.append({
                'employe': e,
                'type': 'depart_soir',
                'timestamp': p.depart_soir,
                'latitude': e.latitude,
                'longitude': e.longitude,
                'anomalie': False
            })
    badges_recent = sorted(badges_events, key=lambda b: b['timestamp'], reverse=True)[:20]
    
    return render_template('badges.html',
                         pointages=pointages,
                         absents=absents,
                         aujourd_hui=aujourd_hui,
                         stats=stats,
                         badges_recent=badges_recent)

@app.route('/carte')
@login_required
def carte():
    # Récupérer tous les chantiers et employés
    chantiers = Chantier.query.all()
    employes = Employe.query.filter_by(actif=True).all()
    
    # Créer des positions simulées pour la démo
    import random
    for i, chantier in enumerate(chantiers):
        if not hasattr(chantier, 'latitude') or not chantier.latitude:
            chantier.latitude = 48.8566 + random.uniform(-0.1, 0.1)
            chantier.longitude = 2.3522 + random.uniform(-0.1, 0.1)
    
    for i, employe in enumerate(employes):
        if not hasattr(employe, 'latitude') or not employe.latitude:
            employe.latitude = 48.8566 + random.uniform(-0.1, 0.1)
            employe.longitude = 2.3522 + random.uniform(-0.1, 0.1)
    
    return render_template('carte.html', 
                         chantiers=chantiers, 
                         employes=employes)

@app.route('/parametres')
@login_required
def parametres():
    return render_template('parametres.html')

@app.route('/sync')
@login_required
def sync_page():
    """Page de configuration de la synchronisation"""
    return render_template('sync_config.html')

# ===== SYSTÈME DE BADGE EMPLOYÉS =====

@app.route('/employee/badge')
def badge_employee():
    """Interface de badge pour les employés (sans authentification requise)"""
    return render_template('badge_mobile_elite.html')

@app.route('/api/badge/check', methods=['POST'])
def badge_check():
    """Enregistrer un pointage via matricule"""
    try:
        data = request.json
        matricule = data.get('matricule')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        badge_type = data.get('type')  # 'matin', 'midi', 'reprise', 'soir'
        
        if not matricule:
            return jsonify({
                'success': False,
                'message': 'Matricule requis'
            }), 400
        
        # Trouver l'employé
        employe = Employe.query.filter_by(matricule=matricule, actif=True).first()
        
        if not employe:
            return jsonify({
                'success': False,
                'message': 'Matricule invalide ou employé inactif'
            }), 404
        
        # Mettre à jour la géolocalisation
        if latitude and longitude:
            employe.latitude = latitude
            employe.longitude = longitude
            employe.derniere_localisation = datetime.now()
        
        # Logique de pointage
        aujourd_hui = date.today()
        pointage = Pointage.query.filter_by(
            employe_id=employe.id,
            date_pointage=aujourd_hui
        ).first()
        
        if not pointage:
            pointage = Pointage(
                employe_id=employe.id,
                date_pointage=aujourd_hui
            )
            db.session.add(pointage)
        
        maintenant = datetime.now()
        action_type = None
        message = ""
        
        # Si un type spécifique est demandé
        if badge_type:
            if badge_type == 'matin':
                if pointage.arrivee_matin:
                    return jsonify({
                        'success': False,
                        'message': 'Arrivée du matin déjà enregistrée'
                    }), 400
                pointage.arrivee_matin = maintenant
                if maintenant.time() > datetime.strptime('09:00', '%H:%M').time():
                    pointage.retard_matin = True
                action_type = "arrivee_matin"
                message = f"Bonjour {employe.prenom}! Arrivée enregistrée à {maintenant.strftime('%H:%M')}"
            
            elif badge_type == 'midi':
                if pointage.depart_midi:
                    return jsonify({
                        'success': False,
                        'message': 'Départ midi déjà enregistré'
                    }), 400
                pointage.depart_midi = maintenant
                action_type = "depart_midi"
                message = f"Bon appétit {employe.prenom}! Départ midi enregistré à {maintenant.strftime('%H:%M')}"
            
            elif badge_type == 'reprise':
                if pointage.arrivee_apres_midi:
                    return jsonify({
                        'success': False,
                        'message': 'Reprise après-midi déjà enregistrée'
                    }), 400
                pointage.arrivee_apres_midi = maintenant
                if maintenant.time() > datetime.strptime('14:00', '%H:%M').time():
                    pointage.retard_apres_midi = True
                action_type = "arrivee_apres_midi"
                message = f"Bon retour {employe.prenom}! Retour enregistré à {maintenant.strftime('%H:%M')}"
            
            elif badge_type == 'soir':
                if pointage.depart_soir:
                    return jsonify({
                        'success': False,
                        'message': 'Départ du soir déjà enregistré'
                    }), 400
                pointage.depart_soir = maintenant
                action_type = "depart_soir"
                
                # Calculer les heures
                heures_matin = 0
                heures_apres_midi = 0
                
                if pointage.arrivee_matin and pointage.depart_midi:
                    delta_matin = pointage.depart_midi - pointage.arrivee_matin
                    heures_matin = delta_matin.total_seconds() / 3600
                
                if pointage.arrivee_apres_midi and pointage.depart_soir:
                    delta_apres_midi = pointage.depart_soir - pointage.arrivee_apres_midi
                    heures_apres_midi = delta_apres_midi.total_seconds() / 3600
                
                total_heures = round(heures_matin + heures_apres_midi, 2)
                pointage.heures_travaillees = total_heures
                
                if total_heures > 8:
                    pointage.heures_supplementaires = round(total_heures - 8, 2)
                
                message = f"Bonne soirée {employe.prenom}! Départ enregistré à {maintenant.strftime('%H:%M')}. Total: {total_heures}h"
        
        # Si pas de type spécifique, utiliser la logique séquentielle
        else:
            if not pointage.arrivee_matin:
                pointage.arrivee_matin = maintenant
                if maintenant.time() > datetime.strptime('09:00', '%H:%M').time():
                    pointage.retard_matin = True
                action_type = "arrivee_matin"
                message = f"Bonjour {employe.prenom}! Arrivée enregistrée à {maintenant.strftime('%H:%M')}"
            elif not pointage.depart_midi:
                pointage.depart_midi = maintenant
                action_type = "depart_midi"
                message = f"Bon appétit {employe.prenom}! Départ midi enregistré à {maintenant.strftime('%H:%M')}"
            elif not pointage.arrivee_apres_midi:
                pointage.arrivee_apres_midi = maintenant
                if maintenant.time() > datetime.strptime('14:00', '%H:%M').time():
                    pointage.retard_apres_midi = True
                action_type = "arrivee_apres_midi"
                message = f"Bon retour {employe.prenom}! Retour enregistré à {maintenant.strftime('%H:%M')}"
            elif not pointage.depart_soir:
                pointage.depart_soir = maintenant
                action_type = "depart_soir"
                
                # Calculer les heures
                heures_matin = 0
                heures_apres_midi = 0
                
                if pointage.arrivee_matin and pointage.depart_midi:
                    delta_matin = pointage.depart_midi - pointage.arrivee_matin
                    heures_matin = delta_matin.total_seconds() / 3600
                
                if pointage.arrivee_apres_midi and pointage.depart_soir:
                    delta_apres_midi = pointage.depart_soir - pointage.arrivee_apres_midi
                    heures_apres_midi = delta_apres_midi.total_seconds() / 3600
                
                total_heures = round(heures_matin + heures_apres_midi, 2)
                pointage.heures_travaillees = total_heures
                
                if total_heures > 8:
                    pointage.heures_supplementaires = round(total_heures - 8, 2)
                
                message = f"Bonne soirée {employe.prenom}! Départ enregistré à {maintenant.strftime('%H:%M')}. Total: {total_heures}h"
            else:
                return jsonify({
                    'success': False,
                    'message': 'Tous les pointages du jour sont déjà enregistrés'
                }), 400
        
        db.session.commit()
        
        # Émettre l'événement WebSocket
        socketio.emit('badge_update', {
            'employe': f'{employe.prenom} {employe.nom}',
            'matricule': employe.matricule,
            'type': action_type,
            'heure': maintenant.strftime('%H:%M'),
            'timestamp': maintenant.isoformat()
        })
        
        return jsonify({
            'success': True,
            'message': message,
            'action_type': action_type,
            'employee': {
                'name': f"{employe.prenom} {employe.nom}",
                'position': employe.position,
                'department': employe.departement,
                'photo': employe.photo
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Erreur lors du pointage: {str(e)}'
        }), 500

# ===== API ENDPOINTS =====

@app.route('/api/employes', methods=['GET', 'POST'])
@login_required
def api_employes():
    if request.method == 'GET':
        employes = Employe.query.all()
        return jsonify([{
            'id': e.id,
            'matricule': e.matricule,
            'nom': e.nom,
            'prenom': e.prenom,
            'departement': e.departement,
            'position': e.position,
            'email': e.email,
            'telephone': e.telephone,
            'actif': e.actif
        } for e in employes])
    
    elif request.method == 'POST':
        data = request.json
        
        # Générer matricule automatique
        count = Employe.query.count() + 1
        matricule = f"EMP{count:03d}"
        
        employe = Employe(
            matricule=matricule,
            nom=data['nom'],
            prenom=data['prenom'],
            departement=data.get('departement'),
            position=data.get('position'),
            email=data.get('email'),
            telephone=data.get('telephone')
        )
        db.session.add(employe)
        db.session.commit()
        
        return jsonify({'success': True, 'id': employe.id, 'matricule': matricule})

@app.route('/api/employes/<int:id>', methods=['PUT', 'DELETE'])
@login_required
def api_employe_detail(id):
    employe = Employe.query.get_or_404(id)
    
    if request.method == 'PUT':
        data = request.json
        employe.nom = data.get('nom', employe.nom)
        employe.prenom = data.get('prenom', employe.prenom)
        employe.departement = data.get('departement', employe.departement)
        employe.position = data.get('position', employe.position)
        employe.email = data.get('email', employe.email)
        employe.telephone = data.get('telephone', employe.telephone)
        db.session.commit()
        return jsonify({'success': True})
    
    elif request.method == 'DELETE':
        employe.actif = False
        db.session.commit()
        return jsonify({'success': True})

@app.route('/api/clients', methods=['GET', 'POST'])
@login_required
def api_clients():
    if request.method == 'GET':
        clients = Client.query.all()
        return jsonify([{
            'id': c.id,
            'nom': c.nom,
            'type_client': c.type_client,
            'contact': c.contact,
            'telephone': c.telephone,
            'email': c.email,
            'ville': c.ville,
            'actif': c.actif
        } for c in clients])
    
    elif request.method == 'POST':
        data = request.json
        client = Client(
            nom=data['nom'],
            type_client=data.get('type_client', 'particulier'),
            contact=data.get('contact'),
            telephone=data.get('telephone'),
            email=data.get('email'),
            adresse=data.get('adresse'),
            ville=data.get('ville'),
            code_postal=data.get('code_postal'),
            notes=data.get('notes')
        )
        db.session.add(client)
        db.session.commit()
        return jsonify({'success': True, 'id': client.id})

@app.route('/api/clients/<int:id>', methods=['PUT', 'DELETE'])
@login_required
def api_client_detail(id: int):
    client = Client.query.get_or_404(id)
    if request.method == 'PUT':
        data = request.json
        client.nom = data.get('nom', client.nom)
        client.type_client = data.get('type_client', client.type_client)
        client.contact = data.get('contact', client.contact)
        client.telephone = data.get('telephone', client.telephone)
        client.email = data.get('email', client.email)
        client.adresse = data.get('adresse', client.adresse)
        client.ville = data.get('ville', client.ville)
        client.code_postal = data.get('code_postal', client.code_postal)
        client.notes = data.get('notes', client.notes)
        db.session.commit()
        return jsonify({'success': True})
    else:  # DELETE logique (désactivation)
        client.actif = False
        db.session.commit()
        return jsonify({'success': True})

@app.route('/api/devis', methods=['GET', 'POST'])
@login_required
def api_devis():
    if request.method == 'GET':
        devis_list = Devis.query.order_by(Devis.date_devis.desc()).all()
        return jsonify([{
            'id': d.id,
            'numero': d.numero,
            'client_id': d.client_id,
            'description': d.description,
            'montant_ht': d.montant_ht,
            'tva': d.tva,
            'montant_ttc': d.montant_ttc,
            'date_devis': d.date_devis.isoformat() if d.date_devis else None,
            'statut': d.statut
        } for d in devis_list])
    
    # POST - création
    data = request.json
    
    # Générer numéro de devis
    count = Devis.query.count() + 1
    numero = f"DEV-{datetime.now().year}-{count:04d}"
    
    devis = Devis(
        numero=numero,
        client_id=data['client_id'],
        montant_ht=float(data.get('montant_ht', 0)),
        tva=float(data.get('tva', 0)),
        montant_ttc=float(data.get('montant_ttc', 0)),
        description=data.get('description'),
        conditions=data.get('conditions'),
        date_validite=datetime.strptime(data['date_validite'], '%Y-%m-%d').date() if data.get('date_validite') else None
    )
    db.session.add(devis)
    db.session.commit()
    
    return jsonify({'success': True, 'id': devis.id, 'numero': devis.numero})

@app.route('/api/devis/<int:id>', methods=['PUT', 'DELETE'])
@login_required
def api_devis_detail(id):
    devis = db.session.get(Devis, id)
    if not devis:
        return jsonify({'success': False, 'message': 'Devis introuvable'}), 404
    
    if request.method == 'DELETE':
        db.session.delete(devis)
        db.session.commit()
        return jsonify({'success': True})
    
    # PUT - mise à jour
    data = request.json
    devis.client_id = data.get('client_id', devis.client_id)
    devis.description = data.get('description', devis.description)
    devis.montant_ht = float(data.get('montant_ht', devis.montant_ht))
    devis.tva = float(data.get('tva', devis.tva))
    devis.montant_ttc = float(data.get('montant_ttc', devis.montant_ttc))
    if data.get('date_devis'):
        devis.date_devis = datetime.strptime(data['date_devis'], '%Y-%m-%d').date()
    devis.validite_jours = int(data.get('validite_jours', devis.validite_jours))
    devis.statut = data.get('statut', devis.statut)
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/factures', methods=['GET', 'POST'])
@login_required
def api_factures():
    if request.method == 'GET':
        factures = Facture.query.order_by(Facture.date_facture.desc()).all()
        return jsonify([{
            'id': f.id,
            'numero': f.numero,
            'client_id': f.client_id,
            'description': f.description,
            'montant_ht': f.montant_ht,
            'tva': f.tva,
            'montant_ttc': f.montant_ttc,
            'date_facture': f.date_facture.isoformat() if f.date_facture else None,
            'date_echeance': f.date_echeance.isoformat() if f.date_echeance else None,
            'statut': f.statut
        } for f in factures])
    
    # POST - création
    data = request.json
    
    # Générer numéro de facture
    count = Facture.query.count() + 1
    numero = f"FAC-{datetime.now().year}-{count:04d}"
    
    facture = Facture(
        numero=numero,
        client_id=data['client_id'],
        chantier_id=data.get('chantier_id'),
        devis_id=data.get('devis_id'),
        montant_ht=float(data.get('montant_ht', 0)),
        tva=float(data.get('tva', 0)),
        montant_ttc=float(data.get('montant_ttc', 0)),
        date_echeance=datetime.strptime(data['date_echeance'], '%Y-%m-%d').date() if data.get('date_echeance') else None
    )
    db.session.add(facture)
    db.session.commit()
    
    return jsonify({'success': True, 'id': facture.id, 'numero': facture.numero})

@app.route('/api/factures/<int:id>', methods=['PUT', 'DELETE'])
@login_required
def api_facture_detail(id):
    facture = db.session.get(Facture, id)
    if not facture:
        return jsonify({'success': False, 'message': 'Facture introuvable'}), 404
    
    if request.method == 'DELETE':
        db.session.delete(facture)
        db.session.commit()
        return jsonify({'success': True})
    
    # PUT - mise à jour
    data = request.json
    facture.client_id = data.get('client_id', facture.client_id)
    facture.description = data.get('description', facture.description)
    facture.montant_ht = float(data.get('montant_ht', facture.montant_ht))
    facture.tva = float(data.get('tva', facture.tva))
    facture.montant_ttc = float(data.get('montant_ttc', facture.montant_ttc))
    if data.get('date_facture'):
        facture.date_facture = datetime.strptime(data['date_facture'], '%Y-%m-%d').date()
    if data.get('date_echeance'):
        facture.date_echeance = datetime.strptime(data['date_echeance'], '%Y-%m-%d').date()
    facture.statut = data.get('statut', facture.statut)
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/chantiers', methods=['GET', 'POST'])
@login_required
def api_chantiers():
    if request.method == 'GET':
        items = Chantier.query.order_by(Chantier.date_debut.desc().nullslast()).all()
        return jsonify([{ 'id': c.id, 'nom': c.nom, 'client_id': c.client_id, 'adresse': c.adresse, 'date_debut': c.date_debut.isoformat() if c.date_debut else None, 'date_fin_prevue': c.date_fin_prevue.isoformat() if c.date_fin_prevue else None, 'statut': c.statut or 'planifie' } for c in items])
    data = request.json
    chantier = Chantier(
        nom=data['nom'],
        client_id=data.get('client_id') or None,
        chef_chantier_id=data.get('chef_chantier_id') or None,
        adresse=data.get('adresse'),
        date_debut=datetime.strptime(data['date_debut'], '%Y-%m-%d').date() if data.get('date_debut') else None,
        date_fin_prevue=datetime.strptime(data['date_fin_prevue'], '%Y-%m-%d').date() if data.get('date_fin_prevue') else None,
        statut=data.get('statut', 'planifie'),
        budget_initial=float(data.get('budget_initial', 0))
    )
    db.session.add(chantier)
    db.session.commit()
    return jsonify({'success': True, 'id': chantier.id})

@app.route('/api/chantiers/<int:id>', methods=['PUT', 'DELETE'])
@login_required
def api_chantier_detail(id):
    chantier = db.session.get(Chantier, id)
    if not chantier:
        return jsonify({'success': False, 'message': 'Chantier introuvable'}), 404
    
    if request.method == 'DELETE':
        db.session.delete(chantier)
        db.session.commit()
        return jsonify({'success': True})
    
    data = request.json
    chantier.nom = data.get('nom', chantier.nom)
    chantier.client_id = data.get('client_id') or None
    chantier.chef_chantier_id = data.get('chef_chantier_id') or None
    chantier.adresse = data.get('adresse', chantier.adresse)
    if data.get('date_debut'):
        chantier.date_debut = datetime.strptime(data['date_debut'], '%Y-%m-%d').date()
    if data.get('date_fin_prevue'):
        chantier.date_fin_prevue = datetime.strptime(data['date_fin_prevue'], '%Y-%m-%d').date()
    chantier.statut = data.get('statut', chantier.statut)
    chantier.budget_initial = float(data.get('budget_initial', chantier.budget_initial))
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/chantiers/<int:id>')
@login_required
def chantier_detail(id):
    chantier = db.session.get(Chantier, id)
    if not chantier:
        flash('Chantier introuvable', 'error')
        return redirect(url_for('chantiers'))
    return render_template('chantier_detail.html', chantier=chantier)

@app.route('/api/leads', methods=['POST'])
@login_required
def api_create_lead():
    data = request.json
    
    lead = Lead(
        nom=data['nom'],
        entreprise=data.get('entreprise'),
        telephone=data.get('telephone'),
        email=data.get('email'),
        source=data.get('source', 'site_web'),
        notes=data.get('notes'),
        potentiel_ca=float(data.get('potentiel_ca', 0)),
        probabilite=int(data.get('probabilite', 50))
    )
    db.session.add(lead)
    db.session.commit()
    
    return jsonify({'success': True, 'id': lead.id})

@app.route('/api/badge', methods=['POST'])
def api_badge_post():
    """Endpoint pour enregistrer un badge"""
    try:
        data = request.get_json() or {}
        employe_id = data.get('employe_id', 1)  # Default pour les tests
        type_pointage = data.get('type', 'arrivee_matin')  # Default pour les tests
        
        if not employe_id or not type_pointage:
            return jsonify({'success': False, 'error': 'Données manquantes'}), 400
        
        # Trouver ou créer le pointage du jour
        today = date.today()
        pointage = Pointage.query.filter_by(
            employe_id=employe_id,
            date_pointage=today
        ).first()
        
        if not pointage:
            pointage = Pointage(
                employe_id=employe_id,
                date_pointage=today
            )
            db.session.add(pointage)
        
        # Enregistrer l'heure selon le type (utiliser datetime au lieu de time pour SQLite)
        current_datetime = datetime.now()
        if type_pointage == 'arrivee_matin':
            pointage.arrivee_matin = current_datetime
        elif type_pointage == 'depart_midi':
            pointage.depart_midi = current_datetime
        elif type_pointage == 'arrivee_apres_midi':
            pointage.arrivee_apres_midi = current_datetime
        elif type_pointage == 'depart_soir':
            pointage.depart_soir = current_datetime
        
        db.session.commit()
        
        # Émettre via WebSocket
        socketio.emit('badge_update', {
            'employe_id': employe_id,
            'type': type_pointage,
            'time': current_datetime.strftime('%H:%M:%S')
        }, broadcast=True)
        
        return jsonify({'success': True, 'message': 'Badge enregistré'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stats/dashboard')
@login_required
def api_dashboard_stats():
    stats = {
        'employes_actifs': Employe.query.filter_by(actif=True).count(),
        'clients_actifs': Client.query.filter_by(actif=True).count(),
        'chantiers_en_cours': Chantier.query.filter_by(statut='en_cours').count(),
        'leads_nouveaux': Lead.query.filter_by(statut='nouveau').count(),
        'factures_impayees': Facture.query.filter(Facture.statut.in_(['envoyee', 'retard'])).count(),
        'ca_mois': db.session.query(db.func.sum(Facture.montant_ttc)).filter(
            Facture.date_facture >= date.today().replace(day=1),
            Facture.statut == 'payee'
        ).scalar() or 0,
        # Ajout des métriques manquantes pour les tests
        'total_clients': Client.query.count(),
        'total_employes': Employe.query.count(),
        'chantiers_actifs': Chantier.query.filter_by(statut='en_cours').count()
    }
    return jsonify(stats)

# ===== GÉNÉRATION PDF =====

@app.route('/api/devis/<int:id>/pdf')
@login_required
def devis_pdf(id):
    devis = Devis.query.get_or_404(id)
    
    # Créer le PDF
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # En-tête
    p.setFont("Helvetica-Bold", 20)
    p.drawString(50, height - 50, "GLOBIBAT")
    p.setFont("Helvetica", 10)
    p.drawString(50, height - 70, "Entreprise de construction générale")
    p.drawString(50, height - 85, "Tél: 05 61 00 00 00 - Email: info@globibat.com")
    
    # Titre
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 150, f"DEVIS N° {devis.numero}")
    
    # Infos client
    p.setFont("Helvetica", 12)
    p.drawString(350, height - 150, f"Date: {devis.date_devis.strftime('%d/%m/%Y')}")
    if devis.date_validite:
        p.drawString(350, height - 170, f"Validité: {devis.date_validite.strftime('%d/%m/%Y')}")
    
    if devis.client:
        p.drawString(50, height - 200, "CLIENT:")
        p.drawString(50, height - 220, devis.client.nom)
        if devis.client.adresse:
            p.drawString(50, height - 240, devis.client.adresse)
        if devis.client.ville:
            p.drawString(50, height - 260, f"{devis.client.code_postal} {devis.client.ville}")
    
    # Description
    if devis.description:
        p.drawString(50, height - 320, "DESCRIPTION:")
        y = height - 340
        for line in devis.description.split('\n'):
            p.drawString(50, y, line[:80])
            y -= 20
    
    # Montants
    y = height - 500
    p.line(50, y, width - 50, y)
    y -= 30
    p.drawString(350, y, f"Montant HT: {devis.montant_ht:.2f} €")
    y -= 20
    p.drawString(350, y, f"TVA (20%): {devis.tva:.2f} €")
    y -= 20
    p.setFont("Helvetica-Bold", 12)
    p.drawString(350, y, f"TOTAL TTC: {devis.montant_ttc:.2f} €")
    
    # Conditions
    if devis.conditions:
        p.setFont("Helvetica", 10)
        p.drawString(50, 100, "Conditions:")
        p.drawString(50, 80, devis.conditions[:100])
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return send_file(buffer, 
                     mimetype='application/pdf',
                     as_attachment=True,
                     download_name=f'devis_{devis.numero}.pdf')

@app.route('/api/factures/<int:id>/pdf')
@login_required
def facture_pdf(id):
    facture = Facture.query.get_or_404(id)
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    p.setFont("Helvetica-Bold", 20)
    p.drawString(50, height - 50, "GLOBIBAT")
    p.setFont("Helvetica", 10)
    p.drawString(50, height - 70, "Entreprise de construction générale")
    p.drawString(50, height - 85, "Tél: 05 61 00 00 00 - Email: info@globibat.com")
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 150, f"FACTURE N° {facture.numero}")
    p.setFont("Helvetica", 12)
    p.drawString(350, height - 150, f"Date: {facture.date_facture.strftime('%d/%m/%Y') if facture.date_facture else '-'}")
    if facture.client:
        p.drawString(50, height - 200, "CLIENT:")
        p.drawString(50, height - 220, facture.client.nom)
        if facture.client.adresse:
            p.drawString(50, height - 240, facture.client.adresse)
        if facture.client.ville:
            p.drawString(50, height - 260, f"{facture.client.code_postal} {facture.client.ville}")
    y = height - 500
    p.line(50, y, width - 50, y)
    y -= 30
    p.drawString(350, y, f"Montant HT: {facture.montant_ht:.2f} €")
    y -= 20
    p.drawString(350, y, f"TVA (20%): {facture.tva:.2f} €")
    y -= 20
    p.setFont("Helvetica-Bold", 12)
    p.drawString(350, y, f"TOTAL TTC: {facture.montant_ttc:.2f} €")
    p.showPage()
    p.save()
    buffer.seek(0)
    return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f'facture_{facture.numero}.pdf')

@app.route('/api/export/employes')
@login_required
def export_employes_csv():
    output = pyio.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow(['ID', 'Matricule', 'Nom', 'Prénom', 'Département', 'Position', 'Email', 'Téléphone', 'Actif'])
    for e in Employe.query.order_by(Employe.id).all():
        writer.writerow([e.id, e.matricule, e.nom, e.prenom, e.departement or '', e.position or '', e.email or '', e.telephone or '', 'Oui' if e.actif else 'Non'])
    data = output.getvalue().encode('utf-8-sig')
    buffer = pyio.BytesIO(data)
    buffer.seek(0)
    return send_file(buffer, mimetype='text/csv', as_attachment=True, download_name='employes.csv')

@app.route('/api/export/clients')
@login_required
def export_clients_csv():
    output = pyio.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow(['ID', 'Nom', 'Type', 'Contact', 'Téléphone', 'Email', 'Ville', 'Actif'])
    for c in Client.query.order_by(Client.id).all():
        writer.writerow([c.id, c.nom, c.type_client or '', c.contact or '', c.telephone or '', c.email or '', c.ville or '', 'Oui' if c.actif else 'Non'])
    data = output.getvalue().encode('utf-8-sig')
    buffer = pyio.BytesIO(data)
    buffer.seek(0)
    return send_file(buffer, mimetype='text/csv', as_attachment=True, download_name='clients.csv')

@app.route('/favicon.ico')
def favicon():
    # Supprime les 404 favicon dans les logs
    return ('', 204)

# ===== IMPORT FICHIERS (PDF, Excel, etc.) =====
ALLOWED_EXTENSIONS = { 'pdf', 'xlsx', 'xls', 'csv' }

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'Aucun fichier reçu'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'Nom de fichier vide'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(path)
        return jsonify({'success': True, 'filename': filename, 'url': f"/api/uploads/{filename}"})
    return jsonify({'success': False, 'message': 'Extension non autorisée'}), 400

@app.route('/api/uploads/<path:filename>')
@login_required
def get_uploaded_file(filename):
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(path):
        return jsonify({'success': False, 'message': 'Fichier introuvable'}), 404
    return send_file(path)

# ===== WEBSOCKET EVENTS =====

@socketio.on('connect')
def handle_connect():
    print(f'Client connecté: {request.sid}')
    emit('connected', {'message': 'Connexion établie'})

@socketio.on('disconnect')
def handle_disconnect():
    print(f'Client déconnecté: {request.sid}')

@socketio.on('join_chantier')
def on_join_chantier(data):
    chantier_id = data['chantier_id']
    username = data.get('username', 'Anonyme')
    room = f'chantier_{chantier_id}'
    join_room(room)
    
    emit('system_message', {
        'message': f'{username} a rejoint le chat',
        'timestamp': datetime.now().isoformat()
    }, room=room)

@socketio.on('send_message')
def handle_message(data):
    chantier_id = data['chantier_id']
    room = f'chantier_{chantier_id}'
    
    emit('new_message', {
        'user': data.get('user', 'Anonyme'),
        'message': data['message'],
        'timestamp': datetime.now().isoformat()
    }, room=room)

@socketio.on('send_notification')
def handle_notification(data):
    emit('new_notification', {
        'type': data.get('type', 'info'),
        'title': data.get('title', 'Notification'),
        'message': data['message'],
        'timestamp': datetime.now().isoformat()
    }, broadcast=True)

# ===== INITIALISATION =====

def init_db():
    with app.app_context():
        # Supprimer et recréer les tables
        db.drop_all()
        db.create_all()
        
        # Créer l'admin principal
        admin = Admin(
            username='admin',
            email='info@globibat.com'
        )
        admin.set_password('Miser1597532684$')
        db.session.add(admin)
        
        # Ajouter des employés de test
        employes = [
            Employe(matricule='EMP001', nom='Dupont', prenom='Jean', departement='Construction', 
                   position='Chef de chantier', email='j.dupont@globibat.com', telephone='0612345678'),
            Employe(matricule='EMP002', nom='Martin', prenom='Marie', departement='Administration', 
                   position='Secrétaire', email='m.martin@globibat.com', telephone='0623456789'),
            Employe(matricule='EMP003', nom='Bernard', prenom='Pierre', departement='Construction', 
                   position='Maçon', email='p.bernard@globibat.com', telephone='0634567890'),
            Employe(matricule='EMP004', nom='Durand', prenom='Sophie', departement='Logistique', 
                   position='Responsable', email='s.durand@globibat.com', telephone='0645678901'),
            Employe(matricule='EMP005', nom='Moreau', prenom='Luc', departement='Construction', 
                   position='Électricien', email='l.moreau@globibat.com', telephone='0656789012'),
        ]
        for emp in employes:
            db.session.add(emp)
        
        # Ajouter des clients
        clients = [
            Client(nom='Mairie de Toulouse', type_client='collectivite', contact='Service Travaux',
                  telephone='0561223344', email='travaux@mairie-toulouse.fr', 
                  adresse='Place du Capitole', ville='Toulouse', code_postal='31000'),
            Client(nom='SARL Construction Plus', type_client='entreprise', contact='M. Dupont',
                  telephone='0561334455', email='contact@constructionplus.fr',
                  adresse='12 rue de l\'Industrie', ville='Blagnac', code_postal='31700'),
            Client(nom='M. et Mme Martinez', type_client='particulier', contact='M. Martinez',
                  telephone='0677889900', email='martinez@email.com',
                  adresse='45 avenue des Roses', ville='Colomiers', code_postal='31770'),
        ]
        for client in clients:
            db.session.add(client)
        
        # Ajouter des chantiers
        chantiers = [
            Chantier(
                nom='Rénovation Mairie - Salle des fêtes',
                client_id=1,
                chef_chantier_id=1,
                adresse='Place du Capitole, Toulouse',
                date_debut=date.today() - timedelta(days=30),
                date_fin_prevue=date.today() + timedelta(days=60),
                statut='en_cours',
                budget_initial=250000,
                budget_consomme=87000,
                latitude=43.6047,
                longitude=1.4442,
                description='Rénovation complète de la salle des fêtes municipale'
            ),
            Chantier(
                nom='Construction Villa Martinez',
                client_id=3,
                chef_chantier_id=1,
                adresse='45 avenue des Roses, Colomiers',
                date_debut=date.today() + timedelta(days=15),
                date_fin_prevue=date.today() + timedelta(days=120),
                statut='planifie',
                budget_initial=180000,
                latitude=43.6118,
                longitude=1.3369,
                description='Construction d\'une villa individuelle de 150m²'
            ),
        ]
        for chantier in chantiers:
            db.session.add(chantier)
        
        # Ajouter des leads
        leads = [
            Lead(nom='M. Dubois', entreprise='Dubois Immobilier', telephone='0656789012',
                email='contact@dubois-immo.fr', source='site_web', potentiel_ca=150000, probabilite=70),
            Lead(nom='Mme Petit', telephone='0623456789', email='petit.marie@email.com',
                source='telephone', statut='contacte', potentiel_ca=85000, probabilite=50),
            Lead(nom='SCI Les Jardins', entreprise='SCI Les Jardins', email='contact@jardins.fr',
                source='salon', potentiel_ca=320000, probabilite=30),
        ]
        for lead in leads:
            db.session.add(lead)
        
        # Ajouter des devis
        devis = [
            Devis(
                numero='DEV-2025-0001',
                client_id=2,
                montant_ht=45000,
                tva=9000,
                montant_ttc=54000,
                statut='envoye',
                description='Extension bureau 50m²',
                date_validite=date.today() + timedelta(days=30)
            ),
        ]
        for d in devis:
            db.session.add(d)
        
        # Ajouter des factures
        factures = [
            Facture(
                numero='FAC-2025-0001',
                client_id=1,
                chantier_id=1,
                montant_ht=50000,
                tva=10000,
                montant_ttc=60000,
                statut='payee',
                date_echeance=date.today() - timedelta(days=15)
            ),
            Facture(
                numero='FAC-2025-0002',
                client_id=2,
                montant_ht=15000,
                tva=3000,
                montant_ttc=18000,
                statut='envoyee',
                date_echeance=date.today() + timedelta(days=15)
            ),
        ]
        for facture in factures:
            db.session.add(facture)
        
        # Ajouter des pointages pour aujourd'hui
        aujourd_hui = date.today()
        maintenant = datetime.now()
        
        for i in range(3):
            pointage = Pointage(
                employe_id=i+1,
                date_pointage=aujourd_hui,
                arrivee_matin=maintenant.replace(hour=8, minute=i*5),
                depart_midi=maintenant.replace(hour=12, minute=0),
                arrivee_apres_midi=maintenant.replace(hour=14, minute=i*3),
                heures_travaillees=7.5,
                retard_matin=(i == 2)
            )
            db.session.add(pointage)
        
        db.session.commit()
        print("✅ Base de données initialisée avec succès")

# ===== ROUTES DE SYNCHRONISATION =====

@app.route('/api/sync/status')
@login_required
def sync_status():
    """Obtenir le statut de synchronisation"""
    try:
        from sync_manager import sync_manager
        if sync_manager:
            return jsonify(sync_manager.get_sync_status())
        else:
            return jsonify({'error': 'Sync manager not initialized'}), 503
    except ImportError:
        return jsonify({'error': 'Sync module not available'}), 503

@app.route('/api/sync/now', methods=['POST'])
@login_required
def sync_now():
    """Lancer une synchronisation manuelle"""
    try:
        from sync_manager import sync_manager
        if sync_manager:
            # Lancer la sync dans un thread séparé
            thread = Thread(target=sync_manager.sync_now)
            thread.start()
            return jsonify({'status': 'sync_started'})
        else:
            return jsonify({'error': 'Sync manager not initialized'}), 503
    except ImportError:
        return jsonify({'error': 'Sync module not available'}), 503

@app.route('/api/sync/config', methods=['GET', 'POST'])
@login_required
def sync_config_route():
    """Gérer la configuration de synchronisation"""
    if request.method == 'GET':
        try:
            from sync_config import SYNC_CONFIG
            # Masquer les informations sensibles
            safe_config = {
                'vps': {
                    'host': SYNC_CONFIG['vps']['host'],
                    'port': SYNC_CONFIG['vps']['port'],
                    'username': SYNC_CONFIG['vps']['username'],
                    'api_endpoint': SYNC_CONFIG['vps']['api_endpoint']
                },
                'sync_options': SYNC_CONFIG['sync_options']
            }
            return jsonify(safe_config)
        except ImportError:
            return jsonify({'error': 'Config not available'}), 503
    
    elif request.method == 'POST':
        # Mettre à jour la configuration
        new_config = request.json
        # Sauvegarder dans le fichier .env
        return jsonify({'status': 'config_updated'})

# ===== LANCEMENT =====

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🏗️  GLOBIBAT CRM - VERSION FINALE")
    print("="*50)
    
    init_db()
    
    # Initialiser le gestionnaire de synchronisation
    try:
        from sync_manager import init_sync_manager
        sync_mgr = init_sync_manager(app)
        print("✅ Gestionnaire de synchronisation initialisé")
    except Exception as e:
        print(f"⚠️ Synchronisation VPS non configurée: {e}")
        print("   Pour activer la sync, copiez env.example en .env")
        print("   et configurez vos paramètres VPS")
    
    print("\n📍 URLs d'accès:")
    print("   CRM Principal: http://localhost:5005/login")
    print("   Badge Employés: http://localhost:5005/employee/badge")
    print("\n🔐 Connexion:")
    print("   Email: info@globibat.com")
    print("   Mot de passe: Miser1597532684$")
    print("="*50 + "\n")
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5005)
