#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Routes RH - CRM Elite Globibat
Toutes les endpoints pour les fonctionnalités RH
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_, or_
import json
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

# Créer le blueprint RH
rh_bp = Blueprint('rh', __name__, url_prefix='/rh')

# Import des modèles (à adapter selon votre structure)
from models_rh import *
from app import db, Employe

# ===== DASHBOARD RH =====

@rh_bp.route('/dashboard')
@login_required
def dashboard_rh():
    """Tableau de bord RH avec KPIs"""
    # Statistiques employés
    stats = {
        'effectif_total': Employe.query.filter_by(actif=True).count(),
        'nouveaux_ce_mois': Employe.query.filter(
            Employe.date_embauche >= datetime.now().replace(day=1)
        ).count(),
        'contrats_cdi': Contrat.query.filter_by(type_contrat='CDI', actif=True).count(),
        'contrats_cdd': Contrat.query.filter_by(type_contrat='CDD', actif=True).count(),
    }
    
    # Congés en cours
    conges_en_cours = DemandeConge.query.filter(
        and_(
            DemandeConge.statut == 'approuve',
            DemandeConge.date_debut <= date.today(),
            DemandeConge.date_fin >= date.today()
        )
    ).count()
    
    # Formations ce mois
    formations_mois = SessionFormation.query.filter(
        func.extract('month', SessionFormation.date_debut) == datetime.now().month
    ).count()
    
    # Absences du jour
    absences_jour = Absence.query.filter(
        and_(
            Absence.date_debut <= date.today(),
            Absence.date_fin >= date.today()
        )
    ).count()
    
    # Alertes RH
    alertes = []
    
    # Contrats qui se terminent bientôt
    contrats_fin = Contrat.query.filter(
        and_(
            Contrat.date_fin != None,
            Contrat.date_fin <= date.today() + timedelta(days=30),
            Contrat.actif == True
        )
    ).all()
    for c in contrats_fin:
        alertes.append(f"Contrat de {c.employe.prenom} {c.employe.nom} se termine le {c.date_fin}")
    
    # Visites médicales à prévoir
    visites = VisiteMedicale.query.filter(
        VisiteMedicale.prochaine_visite <= date.today() + timedelta(days=30)
    ).all()
    for v in visites:
        alertes.append(f"Visite médicale à prévoir pour {v.employe.prenom} {v.employe.nom}")
    
    return render_template('rh/dashboard.html',
                         stats=stats,
                         conges_en_cours=conges_en_cours,
                         formations_mois=formations_mois,
                         absences_jour=absences_jour,
                         alertes=alertes)

# ===== GESTION DES CONGÉS =====

@rh_bp.route('/conges')
@login_required
def liste_conges():
    """Liste des demandes de congés"""
    demandes = DemandeConge.query.order_by(DemandeConge.date_demande.desc()).all()
    types_conges = TypeConge.query.filter_by(actif=True).all()
    return render_template('rh/conges.html', demandes=demandes, types_conges=types_conges)

@rh_bp.route('/conges/demande', methods=['GET', 'POST'])
@login_required
def nouvelle_demande_conge():
    """Créer une nouvelle demande de congé"""
    if request.method == 'POST':
        data = request.form
        
        # Calculer le nombre de jours
        date_debut = datetime.strptime(data['date_debut'], '%Y-%m-%d').date()
        date_fin = datetime.strptime(data['date_fin'], '%Y-%m-%d').date()
        nombre_jours = (date_fin - date_debut).days + 1
        
        # Ajuster pour les demi-journées
        if data.get('demi_journee_debut'):
            nombre_jours -= 0.5
        if data.get('demi_journee_fin'):
            nombre_jours -= 0.5
        
        # Vérifier le solde de congés
        solde = SoldeConge.query.filter_by(
            employe_id=data['employe_id'],
            type_conge_id=data['type_conge_id'],
            annee=datetime.now().year
        ).first()
        
        if solde and solde.solde_restant < nombre_jours:
            flash('Solde de congés insuffisant', 'error')
            return redirect(url_for('rh.nouvelle_demande_conge'))
        
        demande = DemandeConge(
            employe_id=data['employe_id'],
            type_conge_id=data['type_conge_id'],
            date_debut=date_debut,
            date_fin=date_fin,
            demi_journee_debut=bool(data.get('demi_journee_debut')),
            demi_journee_fin=bool(data.get('demi_journee_fin')),
            nombre_jours=nombre_jours,
            motif=data.get('motif'),
            remplacant_id=data.get('remplacant_id')
        )
        
        db.session.add(demande)
        db.session.commit()
        
        flash('Demande de congé créée avec succès', 'success')
        return redirect(url_for('rh.liste_conges'))
    
    employes = Employe.query.filter_by(actif=True).all()
    types_conges = TypeConge.query.filter_by(actif=True).all()
    return render_template('rh/demande_conge.html', employes=employes, types_conges=types_conges)

@rh_bp.route('/conges/<int:id>/valider', methods=['POST'])
@login_required
def valider_conge(id):
    """Valider ou refuser une demande de congé"""
    demande = DemandeConge.query.get_or_404(id)
    action = request.form.get('action')
    
    if action == 'approuver':
        demande.statut = 'approuve'
        demande.validateur_id = current_user.id
        demande.date_validation = datetime.now()
        
        # Mettre à jour le solde de congés
        solde = SoldeConge.query.filter_by(
            employe_id=demande.employe_id,
            type_conge_id=demande.type_conge_id,
            annee=datetime.now().year
        ).first()
        
        if solde:
            solde.solde_pris += demande.nombre_jours
            solde.solde_restant -= demande.nombre_jours
            solde.date_maj = datetime.now()
        
        flash('Demande de congé approuvée', 'success')
    
    elif action == 'refuser':
        demande.statut = 'refuse'
        demande.validateur_id = current_user.id
        demande.date_validation = datetime.now()
        demande.commentaire_validation = request.form.get('commentaire')
        flash('Demande de congé refusée', 'info')
    
    db.session.commit()
    return redirect(url_for('rh.liste_conges'))

@rh_bp.route('/conges/soldes')
@login_required
def soldes_conges():
    """Afficher les soldes de congés"""
    soldes = db.session.query(
        SoldeConge, Employe, TypeConge
    ).join(
        Employe, SoldeConge.employe_id == Employe.id
    ).join(
        TypeConge, SoldeConge.type_conge_id == TypeConge.id
    ).filter(
        SoldeConge.annee == datetime.now().year
    ).all()
    
    return render_template('rh/soldes_conges.html', soldes=soldes)

# ===== GESTION DE LA PAIE =====

@rh_bp.route('/paie')
@login_required
def liste_fiches_paie():
    """Liste des fiches de paie"""
    fiches = FichePaie.query.order_by(
        FichePaie.annee.desc(),
        FichePaie.mois.desc()
    ).all()
    return render_template('rh/paie.html', fiches=fiches)

@rh_bp.route('/paie/generer', methods=['GET', 'POST'])
@login_required
def generer_fiche_paie():
    """Générer les fiches de paie du mois"""
    if request.method == 'POST':
        mois = int(request.form['mois'])
        annee = int(request.form['annee'])
        
        # Récupérer tous les employés actifs avec contrat
        contrats = Contrat.query.filter_by(actif=True).all()
        
        for contrat in contrats:
            employe = Employe.query.get(contrat.employe_id)
            
            # Calculer les heures travaillées
            pointages = Pointage.query.filter(
                and_(
                    Pointage.employe_id == employe.id,
                    func.extract('month', Pointage.date_pointage) == mois,
                    func.extract('year', Pointage.date_pointage) == annee
                )
            ).all()
            
            heures_travaillees = sum(p.heures_travaillees for p in pointages)
            heures_supp = sum(p.heures_supplementaires for p in pointages)
            
            # Calculer le salaire
            salaire_base = contrat.salaire_base
            
            # Calcul des heures supplémentaires
            montant_hs_25 = min(heures_supp, 8) * (salaire_base / 151.67) * 1.25
            montant_hs_50 = max(0, heures_supp - 8) * (salaire_base / 151.67) * 1.50
            
            brut = salaire_base + montant_hs_25 + montant_hs_50
            
            # Cotisations (simplifiées pour la démo)
            cotisations_salariales = brut * 0.23  # ~23% de cotisations salariales
            cotisations_patronales = brut * 0.42  # ~42% de cotisations patronales
            
            net_imposable = brut - cotisations_salariales
            prelevement_source = net_imposable * 0.10  # Taux par défaut 10%
            net_paye = net_imposable - prelevement_source
            
            # Créer la fiche de paie
            fiche = FichePaie(
                employe_id=employe.id,
                mois=mois,
                annee=annee,
                salaire_base=salaire_base,
                heures_travaillees=heures_travaillees,
                heures_supplementaires=heures_supp,
                heures_supplementaires_25=min(heures_supp, 8),
                heures_supplementaires_50=max(0, heures_supp - 8),
                brut=brut,
                net_imposable=net_imposable,
                net_paye=net_paye,
                prelevement_source=prelevement_source,
                statut='validee'
            )
            
            db.session.add(fiche)
        
        db.session.commit()
        flash(f'Fiches de paie générées pour {mois}/{annee}', 'success')
        return redirect(url_for('rh.liste_fiches_paie'))
    
    return render_template('rh/generer_paie.html')

@rh_bp.route('/paie/<int:id>/pdf')
@login_required
def telecharger_fiche_paie(id):
    """Générer et télécharger le PDF d'une fiche de paie"""
    fiche = FichePaie.query.get_or_404(id)
    employe = Employe.query.get(fiche.employe_id)
    
    # Créer le PDF
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # En-tête
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50*mm, height - 30*mm, "BULLETIN DE PAIE")
    
    p.setFont("Helvetica", 10)
    p.drawString(50*mm, height - 40*mm, f"Période: {fiche.mois:02d}/{fiche.annee}")
    
    # Informations employé
    p.drawString(20*mm, height - 60*mm, f"Employé: {employe.prenom} {employe.nom}")
    p.drawString(20*mm, height - 65*mm, f"Matricule: {employe.matricule}")
    p.drawString(20*mm, height - 70*mm, f"Poste: {employe.position or 'N/A'}")
    
    # Détails de paie
    y = height - 90*mm
    
    # Salaire de base
    p.drawString(20*mm, y, "SALAIRE DE BASE")
    p.drawRightString(180*mm, y, f"{fiche.salaire_base:.2f} €")
    y -= 5*mm
    
    # Heures supplémentaires
    if fiche.heures_supplementaires_25 > 0:
        p.drawString(20*mm, y, f"Heures supp. 25% ({fiche.heures_supplementaires_25:.1f}h)")
        montant = fiche.heures_supplementaires_25 * (fiche.salaire_base / 151.67) * 0.25
        p.drawRightString(180*mm, y, f"{montant:.2f} €")
        y -= 5*mm
    
    if fiche.heures_supplementaires_50 > 0:
        p.drawString(20*mm, y, f"Heures supp. 50% ({fiche.heures_supplementaires_50:.1f}h)")
        montant = fiche.heures_supplementaires_50 * (fiche.salaire_base / 151.67) * 0.50
        p.drawRightString(180*mm, y, f"{montant:.2f} €")
        y -= 5*mm
    
    # Brut
    y -= 5*mm
    p.setFont("Helvetica-Bold", 10)
    p.drawString(20*mm, y, "SALAIRE BRUT")
    p.drawRightString(180*mm, y, f"{fiche.brut:.2f} €")
    
    # Cotisations
    y -= 10*mm
    p.setFont("Helvetica", 10)
    p.drawString(20*mm, y, "Cotisations salariales")
    p.drawRightString(180*mm, y, f"-{fiche.brut * 0.23:.2f} €")
    
    # Net imposable
    y -= 10*mm
    p.setFont("Helvetica-Bold", 10)
    p.drawString(20*mm, y, "NET IMPOSABLE")
    p.drawRightString(180*mm, y, f"{fiche.net_imposable:.2f} €")
    
    # Prélèvement à la source
    y -= 5*mm
    p.setFont("Helvetica", 10)
    p.drawString(20*mm, y, "Prélèvement à la source")
    p.drawRightString(180*mm, y, f"-{fiche.prelevement_source:.2f} €")
    
    # Net à payer
    y -= 10*mm
    p.setFont("Helvetica-Bold", 12)
    p.drawString(20*mm, y, "NET À PAYER")
    p.drawRightString(180*mm, y, f"{fiche.net_paye:.2f} €")
    
    # Footer
    p.setFont("Helvetica", 8)
    p.drawString(20*mm, 20*mm, f"Document généré le {datetime.now().strftime('%d/%m/%Y')}")
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'fiche_paie_{employe.matricule}_{fiche.mois:02d}_{fiche.annee}.pdf'
    )

# ===== FORMATIONS =====

@rh_bp.route('/formations')
@login_required
def liste_formations():
    """Liste des formations disponibles"""
    formations = Formation.query.all()
    sessions = SessionFormation.query.filter(
        SessionFormation.date_debut >= datetime.now()
    ).all()
    return render_template('rh/formations.html', formations=formations, sessions=sessions)

@rh_bp.route('/formations/inscription/<int:session_id>', methods=['POST'])
@login_required
def inscription_formation(session_id):
    """Inscrire un employé à une formation"""
    session = SessionFormation.query.get_or_404(session_id)
    employe_id = request.form.get('employe_id')
    
    # Vérifier si déjà inscrit
    inscription_existante = InscriptionFormation.query.filter_by(
        session_id=session_id,
        employe_id=employe_id
    ).first()
    
    if inscription_existante:
        flash('Employé déjà inscrit à cette session', 'warning')
    else:
        inscription = InscriptionFormation(
            session_id=session_id,
            employe_id=employe_id
        )
        db.session.add(inscription)
        db.session.commit()
        flash('Inscription enregistrée avec succès', 'success')
    
    return redirect(url_for('rh.liste_formations'))

# ===== ÉVALUATIONS =====

@rh_bp.route('/evaluations')
@login_required
def liste_evaluations():
    """Liste des campagnes d'évaluation"""
    campagnes = CampagneEvaluation.query.order_by(CampagneEvaluation.annee.desc()).all()
    evaluations = Evaluation.query.filter_by(evaluateur_id=current_user.id).all()
    return render_template('rh/evaluations.html', campagnes=campagnes, evaluations=evaluations)

@rh_bp.route('/evaluations/nouvelle/<int:employe_id>', methods=['GET', 'POST'])
@login_required
def nouvelle_evaluation(employe_id):
    """Créer une nouvelle évaluation"""
    employe = Employe.query.get_or_404(employe_id)
    
    if request.method == 'POST':
        data = request.form
        
        evaluation = Evaluation(
            employe_id=employe_id,
            evaluateur_id=current_user.id,
            campagne_id=data.get('campagne_id'),
            note_globale=float(data.get('note_globale', 0)),
            points_forts=data.get('points_forts'),
            points_amelioration=data.get('points_amelioration'),
            plan_action=data.get('plan_action'),
            commentaire_manager=data.get('commentaire_manager')
        )
        
        # Enregistrer les objectifs
        objectifs = []
        for i in range(1, 6):  # Max 5 objectifs
            if f'objectif_{i}' in data:
                objectifs.append({
                    'titre': data[f'objectif_{i}'],
                    'resultat': data.get(f'resultat_{i}', ''),
                    'note': data.get(f'note_{i}', 0)
                })
        
        evaluation.objectifs = json.dumps(objectifs)
        
        db.session.add(evaluation)
        db.session.commit()
        
        flash('Évaluation créée avec succès', 'success')
        return redirect(url_for('rh.liste_evaluations'))
    
    campagnes = CampagneEvaluation.query.filter_by(statut='en_cours').all()
    return render_template('rh/nouvelle_evaluation.html', employe=employe, campagnes=campagnes)

# ===== CONTRATS =====

@rh_bp.route('/contrats')
@login_required
def liste_contrats():
    """Liste des contrats de travail"""
    contrats = Contrat.query.order_by(Contrat.date_debut.desc()).all()
    return render_template('rh/contrats.html', contrats=contrats)

@rh_bp.route('/contrats/nouveau/<int:employe_id>', methods=['GET', 'POST'])
@login_required
def nouveau_contrat(employe_id):
    """Créer un nouveau contrat"""
    employe = Employe.query.get_or_404(employe_id)
    
    if request.method == 'POST':
        data = request.form
        
        contrat = Contrat(
            employe_id=employe_id,
            type_contrat=data['type_contrat'],
            date_debut=datetime.strptime(data['date_debut'], '%Y-%m-%d').date(),
            date_fin=datetime.strptime(data['date_fin'], '%Y-%m-%d').date() if data.get('date_fin') else None,
            salaire_base=float(data['salaire_base']),
            heures_hebdo=float(data.get('heures_hebdo', 35)),
            coefficient=data.get('coefficient'),
            convention=data.get('convention'),
            niveau=data.get('niveau'),
            echelon=data.get('echelon'),
            periode_essai_jours=int(data.get('periode_essai_jours', 0)) if data.get('periode_essai_jours') else None,
            clause_non_concurrence=bool(data.get('clause_non_concurrence')),
            clause_mobilite=bool(data.get('clause_mobilite'))
        )
        
        # Calculer la fin de période d'essai
        if contrat.periode_essai_jours:
            contrat.fin_periode_essai = contrat.date_debut + timedelta(days=contrat.periode_essai_jours)
        
        db.session.add(contrat)
        db.session.commit()
        
        flash('Contrat créé avec succès', 'success')
        return redirect(url_for('rh.liste_contrats'))
    
    return render_template('rh/nouveau_contrat.html', employe=employe)

# ===== NOTES DE FRAIS =====

@rh_bp.route('/frais')
@login_required
def liste_notes_frais():
    """Liste des notes de frais"""
    notes = NoteFrais.query.order_by(
        NoteFrais.annee.desc(),
        NoteFrais.mois.desc()
    ).all()
    return render_template('rh/notes_frais.html', notes=notes)

@rh_bp.route('/frais/nouvelle', methods=['GET', 'POST'])
@login_required
def nouvelle_note_frais():
    """Créer une nouvelle note de frais"""
    if request.method == 'POST':
        data = request.form
        
        note = NoteFrais(
            employe_id=data['employe_id'],
            mois=int(data['mois']),
            annee=int(data['annee']),
            statut='brouillon'
        )
        
        db.session.add(note)
        db.session.flush()  # Pour obtenir l'ID
        
        # Ajouter les lignes de frais
        montant_total = 0
        for i in range(1, 11):  # Max 10 lignes
            if f'date_{i}' in data and data[f'date_{i}']:
                ligne = LigneFrais(
                    note_frais_id=note.id,
                    date=datetime.strptime(data[f'date_{i}'], '%Y-%m-%d').date(),
                    categorie=data[f'categorie_{i}'],
                    description=data[f'description_{i}'],
                    montant_ttc=float(data[f'montant_{i}']),
                    chantier_id=data.get(f'chantier_{i}') if data.get(f'chantier_{i}') else None
                )
                db.session.add(ligne)
                montant_total += ligne.montant_ttc
        
        note.montant_total = montant_total
        db.session.commit()
        
        flash('Note de frais créée avec succès', 'success')
        return redirect(url_for('rh.liste_notes_frais'))
    
    employes = Employe.query.filter_by(actif=True).all()
    chantiers = Chantier.query.filter_by(statut='en_cours').all()
    return render_template('rh/nouvelle_note_frais.html', employes=employes, chantiers=chantiers)

# ===== SANTÉ & SÉCURITÉ =====

@rh_bp.route('/securite/accidents')
@login_required
def liste_accidents():
    """Liste des accidents du travail"""
    accidents = AccidentTravail.query.order_by(AccidentTravail.date_accident.desc()).all()
    return render_template('rh/accidents.html', accidents=accidents)

@rh_bp.route('/securite/visites-medicales')
@login_required
def liste_visites_medicales():
    """Liste des visites médicales"""
    visites = VisiteMedicale.query.order_by(VisiteMedicale.date_visite.desc()).all()
    
    # Alertes pour les prochaines visites
    alertes = VisiteMedicale.query.filter(
        VisiteMedicale.prochaine_visite <= date.today() + timedelta(days=60)
    ).all()
    
    return render_template('rh/visites_medicales.html', visites=visites, alertes=alertes)

# ===== ORGANIGRAMME =====

@rh_bp.route('/organigramme')
@login_required
def organigramme():
    """Afficher l'organigramme de l'entreprise"""
    postes = PosteOrganigramme.query.filter_by(actif=True).order_by(
        PosteOrganigramme.niveau_hierarchique,
        PosteOrganigramme.ordre_affichage
    ).all()
    
    # Construire l'arbre hiérarchique
    arbre = {}
    for poste in postes:
        if poste.poste_parent_id is None:
            arbre[poste.id] = {'poste': poste, 'enfants': []}
    
    for poste in postes:
        if poste.poste_parent_id and poste.poste_parent_id in arbre:
            arbre[poste.poste_parent_id]['enfants'].append(poste)
    
    return render_template('rh/organigramme.html', arbre=arbre)

# ===== API ENDPOINTS =====

@rh_bp.route('/api/stats')
@login_required
def api_stats_rh():
    """API pour les statistiques RH"""
    stats = {
        'effectif': {
            'total': Employe.query.filter_by(actif=True).count(),
            'cdi': Contrat.query.filter_by(type_contrat='CDI', actif=True).count(),
            'cdd': Contrat.query.filter_by(type_contrat='CDD', actif=True).count(),
        },
        'conges': {
            'en_cours': DemandeConge.query.filter(
                and_(
                    DemandeConge.statut == 'approuve',
                    DemandeConge.date_debut <= date.today(),
                    DemandeConge.date_fin >= date.today()
                )
            ).count(),
            'demandes_attente': DemandeConge.query.filter_by(statut='en_attente').count(),
        },
        'formations': {
            'sessions_mois': SessionFormation.query.filter(
                func.extract('month', SessionFormation.date_debut) == datetime.now().month
            ).count(),
            'inscriptions': InscriptionFormation.query.filter_by(statut='inscrit').count(),
        },
        'paie': {
            'masse_salariale_mois': db.session.query(func.sum(FichePaie.net_paye)).filter(
                and_(
                    FichePaie.mois == datetime.now().month,
                    FichePaie.annee == datetime.now().year
                )
            ).scalar() or 0,
        }
    }
    
    return jsonify(stats)

@rh_bp.route('/api/planning/<int:employe_id>')
@login_required
def api_planning_employe(employe_id):
    """API pour le planning d'un employé"""
    debut = request.args.get('debut', date.today().isoformat())
    fin = request.args.get('fin', (date.today() + timedelta(days=30)).isoformat())
    
    planning = PlanningEmploye.query.filter(
        and_(
            PlanningEmploye.employe_id == employe_id,
            PlanningEmploye.date >= debut,
            PlanningEmploye.date <= fin
        )
    ).all()
    
    events = []
    for p in planning:
        events.append({
            'id': p.id,
            'title': p.tache or 'Travail',
            'start': f"{p.date}T{p.heure_debut}" if p.heure_debut else p.date,
            'end': f"{p.date}T{p.heure_fin}" if p.heure_fin else p.date,
            'color': '#28a745' if p.statut == 'confirme' else '#ffc107'
        })
    
    return jsonify(events)

@rh_bp.route('/api/competences/<int:employe_id>')
@login_required
def api_competences_employe(employe_id):
    """API pour les compétences d'un employé"""
    competences = db.session.query(
        CompetenceEmploye, Competence
    ).join(
        Competence, CompetenceEmploye.competence_id == Competence.id
    ).filter(
        CompetenceEmploye.employe_id == employe_id
    ).all()
    
    data = []
    for ce, c in competences:
        data.append({
            'nom': c.nom,
            'categorie': c.categorie,
            'niveau': ce.niveau,
            'niveau_max': c.niveau_max,
            'certifie': ce.certifie,
            'date_expiration': ce.date_expiration.isoformat() if ce.date_expiration else None
        })
    
    return jsonify(data)