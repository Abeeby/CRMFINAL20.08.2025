#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Modèles RH Complets - CRM Elite Globibat
Toutes les fonctionnalités RH avancées
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from sqlalchemy import func

db = SQLAlchemy()

# ===== GESTION DES CONGÉS =====

class TypeConge(db.Model):
    """Types de congés disponibles"""
    __tablename__ = 'type_conge'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)  # CP, RTT, Maladie, Maternité, etc.
    code = db.Column(db.String(20), unique=True)
    jours_par_an = db.Column(db.Float, default=0)
    paye = db.Column(db.Boolean, default=True)
    justificatif_requis = db.Column(db.Boolean, default=False)
    delai_demande_jours = db.Column(db.Integer, default=7)  # Délai minimum pour demander
    couleur = db.Column(db.String(7), default='#007bff')  # Pour le calendrier
    actif = db.Column(db.Boolean, default=True)
    
class SoldeConge(db.Model):
    """Solde de congés par employé et par type"""
    __tablename__ = 'solde_conge'
    id = db.Column(db.Integer, primary_key=True)
    employe_id = db.Column(db.Integer, db.ForeignKey('employe.id'), nullable=False)
    type_conge_id = db.Column(db.Integer, db.ForeignKey('type_conge.id'), nullable=False)
    annee = db.Column(db.Integer, nullable=False)
    solde_initial = db.Column(db.Float, default=0)
    solde_acquis = db.Column(db.Float, default=0)
    solde_pris = db.Column(db.Float, default=0)
    solde_restant = db.Column(db.Float, default=0)
    report_annee_precedente = db.Column(db.Float, default=0)
    date_maj = db.Column(db.DateTime, default=datetime.utcnow)
    
class DemandeConge(db.Model):
    """Demandes de congés"""
    __tablename__ = 'demande_conge'
    id = db.Column(db.Integer, primary_key=True)
    employe_id = db.Column(db.Integer, db.ForeignKey('employe.id'), nullable=False)
    type_conge_id = db.Column(db.Integer, db.ForeignKey('type_conge.id'), nullable=False)
    date_debut = db.Column(db.Date, nullable=False)
    date_fin = db.Column(db.Date, nullable=False)
    demi_journee_debut = db.Column(db.Boolean, default=False)  # Matin uniquement
    demi_journee_fin = db.Column(db.Boolean, default=False)  # Après-midi uniquement
    nombre_jours = db.Column(db.Float, nullable=False)
    motif = db.Column(db.Text)
    justificatif = db.Column(db.String(255))  # URL du fichier
    statut = db.Column(db.String(50), default='en_attente')  # en_attente, approuve, refuse, annule
    date_demande = db.Column(db.DateTime, default=datetime.utcnow)
    validateur_id = db.Column(db.Integer, db.ForeignKey('employe.id'))
    date_validation = db.Column(db.DateTime)
    commentaire_validation = db.Column(db.Text)
    remplacant_id = db.Column(db.Integer, db.ForeignKey('employe.id'))  # Qui remplace pendant l'absence
    
# ===== GESTION DE LA PAIE =====

class Contrat(db.Model):
    """Contrats de travail"""
    __tablename__ = 'contrat'
    id = db.Column(db.Integer, primary_key=True)
    employe_id = db.Column(db.Integer, db.ForeignKey('employe.id'), nullable=False)
    type_contrat = db.Column(db.String(50))  # CDI, CDD, Intérim, Alternance, Stage
    date_debut = db.Column(db.Date, nullable=False)
    date_fin = db.Column(db.Date)  # NULL pour CDI
    salaire_base = db.Column(db.Float, nullable=False)
    heures_hebdo = db.Column(db.Float, default=35)
    coefficient = db.Column(db.String(20))
    convention = db.Column(db.String(100))
    niveau = db.Column(db.String(50))
    echelon = db.Column(db.String(50))
    periode_essai_jours = db.Column(db.Integer)
    fin_periode_essai = db.Column(db.Date)
    clause_non_concurrence = db.Column(db.Boolean, default=False)
    clause_mobilite = db.Column(db.Boolean, default=False)
    avantages = db.Column(db.Text)  # JSON des avantages (voiture, tel, etc.)
    document_url = db.Column(db.String(255))
    actif = db.Column(db.Boolean, default=True)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    
class ElementPaie(db.Model):
    """Éléments variables de paie"""
    __tablename__ = 'element_paie'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True)
    type_element = db.Column(db.String(50))  # prime, indemnite, retenue, cotisation
    calcul = db.Column(db.String(50))  # fixe, pourcentage, formule
    valeur_defaut = db.Column(db.Float)
    soumis_cotisations = db.Column(db.Boolean, default=True)
    soumis_impot = db.Column(db.Boolean, default=True)
    actif = db.Column(db.Boolean, default=True)
    
class FichePaie(db.Model):
    """Fiches de paie mensuelles"""
    __tablename__ = 'fiche_paie'
    id = db.Column(db.Integer, primary_key=True)
    employe_id = db.Column(db.Integer, db.ForeignKey('employe.id'), nullable=False)
    mois = db.Column(db.Integer, nullable=False)
    annee = db.Column(db.Integer, nullable=False)
    salaire_base = db.Column(db.Float, nullable=False)
    heures_travaillees = db.Column(db.Float)
    heures_supplementaires = db.Column(db.Float, default=0)
    heures_supplementaires_25 = db.Column(db.Float, default=0)  # HS à 25%
    heures_supplementaires_50 = db.Column(db.Float, default=0)  # HS à 50%
    primes = db.Column(db.Text)  # JSON des primes
    indemnites = db.Column(db.Text)  # JSON des indemnités
    avantages_nature = db.Column(db.Text)  # JSON
    brut = db.Column(db.Float, nullable=False)
    cotisations_salariales = db.Column(db.Text)  # JSON détaillé
    cotisations_patronales = db.Column(db.Text)  # JSON détaillé
    net_imposable = db.Column(db.Float)
    net_paye = db.Column(db.Float, nullable=False)
    prelevement_source = db.Column(db.Float, default=0)
    date_paiement = db.Column(db.Date)
    mode_paiement = db.Column(db.String(50))  # virement, cheque, especes
    statut = db.Column(db.String(50), default='brouillon')  # brouillon, validee, payee
    pdf_url = db.Column(db.String(255))
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    
# ===== ÉVALUATIONS & PERFORMANCE =====

class CampagneEvaluation(db.Model):
    """Campagnes d'évaluation annuelles"""
    __tablename__ = 'campagne_evaluation'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(200), nullable=False)
    annee = db.Column(db.Integer, nullable=False)
    date_debut = db.Column(db.Date, nullable=False)
    date_fin = db.Column(db.Date, nullable=False)
    statut = db.Column(db.String(50), default='planifiee')  # planifiee, en_cours, terminee
    template = db.Column(db.Text)  # JSON du template d'évaluation
    
class Evaluation(db.Model):
    """Évaluations individuelles"""
    __tablename__ = 'evaluation'
    id = db.Column(db.Integer, primary_key=True)
    campagne_id = db.Column(db.Integer, db.ForeignKey('campagne_evaluation.id'))
    employe_id = db.Column(db.Integer, db.ForeignKey('employe.id'), nullable=False)
    evaluateur_id = db.Column(db.Integer, db.ForeignKey('employe.id'), nullable=False)
    date_evaluation = db.Column(db.DateTime, default=datetime.utcnow)
    objectifs = db.Column(db.Text)  # JSON des objectifs et résultats
    competences = db.Column(db.Text)  # JSON des compétences évaluées
    note_globale = db.Column(db.Float)  # Sur 5 ou 10
    points_forts = db.Column(db.Text)
    points_amelioration = db.Column(db.Text)
    plan_action = db.Column(db.Text)
    commentaire_employe = db.Column(db.Text)
    commentaire_manager = db.Column(db.Text)
    statut = db.Column(db.String(50), default='brouillon')
    date_validation_employe = db.Column(db.DateTime)
    date_validation_manager = db.Column(db.DateTime)
    
class Objectif(db.Model):
    """Objectifs individuels ou d'équipe"""
    __tablename__ = 'objectif'
    id = db.Column(db.Integer, primary_key=True)
    employe_id = db.Column(db.Integer, db.ForeignKey('employe.id'))
    equipe_id = db.Column(db.Integer, db.ForeignKey('equipe.id'))
    titre = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    type_objectif = db.Column(db.String(50))  # SMART, KPI, Projet
    date_debut = db.Column(db.Date, nullable=False)
    date_fin = db.Column(db.Date, nullable=False)
    indicateurs = db.Column(db.Text)  # JSON des KPIs
    progression = db.Column(db.Float, default=0)  # 0-100%
    statut = db.Column(db.String(50), default='en_cours')
    priorite = db.Column(db.Integer, default=3)  # 1-5
    
# ===== FORMATION & COMPÉTENCES =====

class Competence(db.Model):
    """Référentiel de compétences"""
    __tablename__ = 'competence'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    categorie = db.Column(db.String(100))  # Technique, Comportementale, Métier
    description = db.Column(db.Text)
    niveau_max = db.Column(db.Integer, default=5)
    obligatoire_poste = db.Column(db.Text)  # JSON des postes où c'est obligatoire
    
class CompetenceEmploye(db.Model):
    """Compétences des employés"""
    __tablename__ = 'competence_employe'
    id = db.Column(db.Integer, primary_key=True)
    employe_id = db.Column(db.Integer, db.ForeignKey('employe.id'), nullable=False)
    competence_id = db.Column(db.Integer, db.ForeignKey('competence.id'), nullable=False)
    niveau = db.Column(db.Integer, nullable=False)  # 1-5
    certifie = db.Column(db.Boolean, default=False)
    date_evaluation = db.Column(db.Date)
    date_expiration = db.Column(db.Date)  # Pour les certifications
    evaluateur_id = db.Column(db.Integer, db.ForeignKey('employe.id'))
    
class Formation(db.Model):
    """Catalogue de formations"""
    __tablename__ = 'formation'
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200), nullable=False)
    type_formation = db.Column(db.String(50))  # Interne, Externe, E-learning, Certification
    organisme = db.Column(db.String(200))
    duree_heures = db.Column(db.Float)
    cout = db.Column(db.Float)
    competences_visees = db.Column(db.Text)  # JSON des compétences
    prerequis = db.Column(db.Text)
    programme = db.Column(db.Text)
    modalites = db.Column(db.String(100))  # Présentiel, Distanciel, Mixte
    certification = db.Column(db.Boolean, default=False)
    obligatoire = db.Column(db.Boolean, default=False)
    
class SessionFormation(db.Model):
    """Sessions de formation planifiées"""
    __tablename__ = 'session_formation'
    id = db.Column(db.Integer, primary_key=True)
    formation_id = db.Column(db.Integer, db.ForeignKey('formation.id'), nullable=False)
    date_debut = db.Column(db.DateTime, nullable=False)
    date_fin = db.Column(db.DateTime, nullable=False)
    lieu = db.Column(db.String(200))
    formateur = db.Column(db.String(200))
    places_disponibles = db.Column(db.Integer)
    statut = db.Column(db.String(50), default='planifiee')
    
class InscriptionFormation(db.Model):
    """Inscriptions aux formations"""
    __tablename__ = 'inscription_formation'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('session_formation.id'), nullable=False)
    employe_id = db.Column(db.Integer, db.ForeignKey('employe.id'), nullable=False)
    date_inscription = db.Column(db.DateTime, default=datetime.utcnow)
    statut = db.Column(db.String(50), default='inscrit')  # inscrit, present, absent, complete
    validation_manager = db.Column(db.Boolean, default=False)
    date_validation = db.Column(db.DateTime)
    presence = db.Column(db.Float, default=0)  # Pourcentage de présence
    note = db.Column(db.Float)  # Note si évaluation
    certificat_obtenu = db.Column(db.Boolean, default=False)
    commentaires = db.Column(db.Text)
    
# ===== GESTION DES ÉQUIPES =====

class Equipe(db.Model):
    """Équipes et départements"""
    __tablename__ = 'equipe'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True)
    type_equipe = db.Column(db.String(50))  # departement, projet, temporaire
    manager_id = db.Column(db.Integer, db.ForeignKey('employe.id'))
    equipe_parent_id = db.Column(db.Integer, db.ForeignKey('equipe.id'))
    description = db.Column(db.Text)
    budget = db.Column(db.Float)
    effectif_cible = db.Column(db.Integer)
    date_creation = db.Column(db.Date, default=date.today)
    active = db.Column(db.Boolean, default=True)
    
class MembreEquipe(db.Model):
    """Membres des équipes"""
    __tablename__ = 'membre_equipe'
    id = db.Column(db.Integer, primary_key=True)
    equipe_id = db.Column(db.Integer, db.ForeignKey('equipe.id'), nullable=False)
    employe_id = db.Column(db.Integer, db.ForeignKey('employe.id'), nullable=False)
    role = db.Column(db.String(100))  # Manager, Membre, Expert, Support
    date_debut = db.Column(db.Date, nullable=False)
    date_fin = db.Column(db.Date)
    pourcentage_affectation = db.Column(db.Float, default=100)  # Pour les affectations partielles
    
# ===== PLANNING & HORAIRES =====

class HoraireType(db.Model):
    """Types d'horaires"""
    __tablename__ = 'horaire_type'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True)
    heure_debut_matin = db.Column(db.Time)
    heure_fin_matin = db.Column(db.Time)
    heure_debut_aprem = db.Column(db.Time)
    heure_fin_aprem = db.Column(db.Time)
    heures_jour = db.Column(db.Float)
    jours_semaine = db.Column(db.String(50))  # JSON des jours travaillés
    pause_dejeuner_min = db.Column(db.Integer, default=30)
    flexible = db.Column(db.Boolean, default=False)
    
class PlanningEmploye(db.Model):
    """Planning individuel"""
    __tablename__ = 'planning_employe'
    id = db.Column(db.Integer, primary_key=True)
    employe_id = db.Column(db.Integer, db.ForeignKey('employe.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    horaire_type_id = db.Column(db.Integer, db.ForeignKey('horaire_type.id'))
    heure_debut = db.Column(db.Time)
    heure_fin = db.Column(db.Time)
    pause_duree = db.Column(db.Integer)  # Minutes
    chantier_id = db.Column(db.Integer, db.ForeignKey('chantier.id'))
    tache = db.Column(db.String(200))
    statut = db.Column(db.String(50), default='prevu')  # prevu, confirme, realise, annule
    commentaire = db.Column(db.Text)
    
# ===== SANTÉ & SÉCURITÉ =====

class VisiteMedicale(db.Model):
    """Visites médicales"""
    __tablename__ = 'visite_medicale'
    id = db.Column(db.Integer, primary_key=True)
    employe_id = db.Column(db.Integer, db.ForeignKey('employe.id'), nullable=False)
    type_visite = db.Column(db.String(50))  # embauche, periodique, reprise, demande
    date_visite = db.Column(db.Date, nullable=False)
    medecin = db.Column(db.String(100))
    aptitude = db.Column(db.String(50))  # apte, inapte_temporaire, inapte_definitif, apte_restriction
    restrictions = db.Column(db.Text)
    prochaine_visite = db.Column(db.Date)
    commentaires = db.Column(db.Text)
    document_url = db.Column(db.String(255))
    
class AccidentTravail(db.Model):
    """Accidents du travail"""
    __tablename__ = 'accident_travail'
    id = db.Column(db.Integer, primary_key=True)
    employe_id = db.Column(db.Integer, db.ForeignKey('employe.id'), nullable=False)
    date_accident = db.Column(db.DateTime, nullable=False)
    lieu = db.Column(db.String(200))
    chantier_id = db.Column(db.Integer, db.ForeignKey('chantier.id'))
    type_accident = db.Column(db.String(100))  # chute, coupure, etc.
    gravite = db.Column(db.String(50))  # benin, grave, mortel
    partie_corps = db.Column(db.String(100))
    description = db.Column(db.Text, nullable=False)
    temoins = db.Column(db.Text)
    arret_travail = db.Column(db.Boolean, default=False)
    duree_arret = db.Column(db.Integer)  # Jours
    date_reprise = db.Column(db.Date)
    declaration_cpam = db.Column(db.Boolean, default=False)
    numero_declaration = db.Column(db.String(50))
    enquete = db.Column(db.Text)
    mesures_preventives = db.Column(db.Text)
    cout_total = db.Column(db.Float)
    
# ===== NOTES DE FRAIS =====

class NoteFrais(db.Model):
    """Notes de frais"""
    __tablename__ = 'note_frais'
    id = db.Column(db.Integer, primary_key=True)
    employe_id = db.Column(db.Integer, db.ForeignKey('employe.id'), nullable=False)
    mois = db.Column(db.Integer, nullable=False)
    annee = db.Column(db.Integer, nullable=False)
    statut = db.Column(db.String(50), default='brouillon')  # brouillon, soumise, validee, rejetee, remboursee
    montant_total = db.Column(db.Float, default=0)
    date_soumission = db.Column(db.DateTime)
    validateur_id = db.Column(db.Integer, db.ForeignKey('employe.id'))
    date_validation = db.Column(db.DateTime)
    date_remboursement = db.Column(db.Date)
    commentaires = db.Column(db.Text)
    
class LigneFrais(db.Model):
    """Lignes de frais détaillées"""
    __tablename__ = 'ligne_frais'
    id = db.Column(db.Integer, primary_key=True)
    note_frais_id = db.Column(db.Integer, db.ForeignKey('note_frais.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    categorie = db.Column(db.String(50))  # transport, repas, hotel, autre
    description = db.Column(db.String(200), nullable=False)
    montant_ht = db.Column(db.Float)
    tva = db.Column(db.Float)
    montant_ttc = db.Column(db.Float, nullable=False)
    justificatif_url = db.Column(db.String(255))
    chantier_id = db.Column(db.Integer, db.ForeignKey('chantier.id'))
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    remboursable = db.Column(db.Boolean, default=True)
    
# ===== DOCUMENTS RH =====

class DocumentRH(db.Model):
    """Documents RH des employés"""
    __tablename__ = 'document_rh'
    id = db.Column(db.Integer, primary_key=True)
    employe_id = db.Column(db.Integer, db.ForeignKey('employe.id'), nullable=False)
    type_document = db.Column(db.String(100), nullable=False)  # CV, diplome, CNI, contrat, etc.
    nom = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    fichier_url = db.Column(db.String(255), nullable=False)
    date_document = db.Column(db.Date)
    date_expiration = db.Column(db.Date)
    confidentiel = db.Column(db.Boolean, default=False)
    date_upload = db.Column(db.DateTime, default=datetime.utcnow)
    upload_par = db.Column(db.Integer, db.ForeignKey('employe.id'))
    
# ===== INDICATEURS RH =====

class IndicateurRH(db.Model):
    """KPIs RH mensuels"""
    __tablename__ = 'indicateur_rh'
    id = db.Column(db.Integer, primary_key=True)
    mois = db.Column(db.Integer, nullable=False)
    annee = db.Column(db.Integer, nullable=False)
    effectif_total = db.Column(db.Integer)
    effectif_cdi = db.Column(db.Integer)
    effectif_cdd = db.Column(db.Integer)
    effectif_interim = db.Column(db.Integer)
    embauches = db.Column(db.Integer)
    departs = db.Column(db.Integer)
    taux_rotation = db.Column(db.Float)  # Turnover
    taux_absenteisme = db.Column(db.Float)
    accidents_travail = db.Column(db.Integer)
    jours_formation = db.Column(db.Float)
    masse_salariale = db.Column(db.Float)
    cout_formation = db.Column(db.Float)
    heures_supplementaires = db.Column(db.Float)
    date_calcul = db.Column(db.DateTime, default=datetime.utcnow)
    
# ===== ORGANIGRAMME =====

class PosteOrganigramme(db.Model):
    """Postes dans l'organigramme"""
    __tablename__ = 'poste_organigramme'
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200), nullable=False)
    code = db.Column(db.String(50), unique=True)
    niveau_hierarchique = db.Column(db.Integer)
    poste_parent_id = db.Column(db.Integer, db.ForeignKey('poste_organigramme.id'))
    employe_titulaire_id = db.Column(db.Integer, db.ForeignKey('employe.id'))
    employe_interim_id = db.Column(db.Integer, db.ForeignKey('employe.id'))
    description = db.Column(db.Text)
    missions = db.Column(db.Text)
    competences_requises = db.Column(db.Text)  # JSON
    delegation_pouvoirs = db.Column(db.Text)
    ordre_affichage = db.Column(db.Integer)
    actif = db.Column(db.Boolean, default=True)
    
# ===== ENTRETIENS RH =====

class EntretienRH(db.Model):
    """Entretiens RH (annuels, professionnels, etc.)"""
    __tablename__ = 'entretien_rh'
    id = db.Column(db.Integer, primary_key=True)
    employe_id = db.Column(db.Integer, db.ForeignKey('employe.id'), nullable=False)
    type_entretien = db.Column(db.String(100))  # annuel, professionnel, disciplinaire, depart
    date_entretien = db.Column(db.DateTime, nullable=False)
    manager_id = db.Column(db.Integer, db.ForeignKey('employe.id'))
    rh_present_id = db.Column(db.Integer, db.ForeignKey('employe.id'))
    ordre_jour = db.Column(db.Text)
    compte_rendu = db.Column(db.Text)
    decisions = db.Column(db.Text)
    plan_action = db.Column(db.Text)
    prochain_entretien = db.Column(db.Date)
    document_signe = db.Column(db.String(255))
    statut = db.Column(db.String(50), default='planifie')