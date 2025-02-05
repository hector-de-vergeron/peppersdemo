# app.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import calendar
from payroll import *

def create_calendar_input(timesheet_name, year, month):
    """Crée un calendrier interactif pour saisir les heures"""
    global absence_motifs
    # Calcul de la date de début du mois
    first_date = datetime(year, month, 1)
    # On recule jusqu'au lundi de la semaine contenant le premier jour du mois
    start_date = first_date - timedelta(days=first_date.weekday())
    
    # Calcul du dernier jour du mois
    last_day = calendar.monthrange(year, month)[1]
    last_date = datetime(year, month, last_day)
    # On avance jusqu'au dimanche de la semaine contenant le dernier jour du mois
    end_date = last_date + timedelta(days=(6 - last_date.weekday()))
    
    st.write(f"*{timesheet_name}*")
    
    # Affichage des en-têtes des jours
    jours = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
    cols = st.columns(7)
    for col, jour in zip(cols, jours):
        col.markdown(f"<div style='text-align: center'><b>{jour}</b></div>", unsafe_allow_html=True)
    
    # Initialiser les valeurs dans session_state si nécessaire
    if f'timesheet_{timesheet_name}' not in st.session_state:
        st.session_state[f'timesheet_{timesheet_name}'] = {}
    
    # Création des semaines
    current_date = start_date
    while current_date <= end_date:
        week_cols = st.columns(7)
        for col in week_cols:
            date_str = current_date.strftime('%Y-%m-%d')
            if current_date.month == month:
                with col:
                    # Définir la valeur par défaut selon le type d'heures
                    if timesheet_name in ["contractuelles", "reelles"]:
                        # Si c'est un jour de semaine, afficher 7, sinon 0
                        default_value = 7.0 if current_date.weekday() < 5 else 0.0
                    else:
                        # Pour les autres types d'heures, valeur par défaut = 0
                        default_value = 0.0

                    value = st.number_input(
                        f"{date_str}",
                        min_value=0.0,
                        max_value=24.0,
                        value=float(st.session_state[f'timesheet_{timesheet_name}'].get(date_str, default_value)),
                        step=0.5 if timesheet_name in ['rtt', 'cp', 'jf', 'maladie'] else 1.0,
                        key=f"{timesheet_name}_{date_str}_{year}_{month}",
                        label_visibility="collapsed"
                    )
                    st.session_state[f'timesheet_{timesheet_name}'][date_str] = value
            else:
                col.write("")
            current_date += timedelta(days=1)
    
    # Si c'est l'onglet "maladie", ajouter la gestion des périodes d'absence
    if timesheet_name == "maladie":
        # Initialiser le dictionnaire des absences dans session_state s'il n'existe pas déjà
        if 'absence_motifs' not in st.session_state:
            st.session_state.absence_motifs = {}
        
        st.markdown("### Ajouter une période d'absence")
        with st.form(key=f"absence_form_{year}_{month}"):
            col1, col2, col3 = st.columns(3)
            start_absence = col1.date_input("Date de début", date.today(), key=f"start_absence_{year}_{month}")
            end_absence = col2.date_input("Date de fin", date.today(), key=f"end_absence_{year}_{month}")
            motif_absence = col3.selectbox(
                "Motif d'absence", 
                ["maladie", "accident travail", "maternité"], 
                key=f"motif_absence_{year}_{month}"
            )
            submitted = st.form_submit_button("Ajouter cette période")
            if submitted:
                current = start_absence
                # Pour chaque jour entre la date de début et de fin
                while current <= end_absence:
                    date_str = current.strftime("%Y-%m-%d")
                    # On vérifie que le jour appartient bien au mois affiché
                    if current.month == month:
                        # On suppose qu'une absence correspond à une journée complète (7h d'absence)
                        st.session_state[f"timesheet_{timesheet_name}"][date_str] = 7.0
                        st.session_state.absence_motifs[date_str] = motif_absence
                    current += timedelta(days=1)
                st.success("Période d'absence ajoutée avec succès.")
        
        st.markdown("**Absences enregistrées :**")
        for date_str, motif in st.session_state.absence_motifs.items():
            st.write(f"{date_str} : {motif}")



dec_24_contrat = [[None, None, None, None, None, None, {'2024-12-01': 0}], [{'2024-12-02': 7}, {'2024-12-03': 7}, {'2024-12-04': 7}, {'2024-12-05': 7}, {'2024-12-06': 7}, {'2024-12-07': 0}, {'2024-12-08': 0}], [{'2024-12-09': 7}, {'2024-12-10': 7}, {'2024-12-11': 7}, {'2024-12-12': 7}, {'2024-12-13': 7}, {'2024-12-14': 0}, {'2024-12-15': 0}], [{'2024-12-16': 7}, {'2024-12-17': 7}, {'2024-12-18': 7}, {'2024-12-19': 7}, {'2024-12-20': 7}, {'2024-12-21': 0}, {'2024-12-22': 0}], [{'2024-12-23': 7}, {'2024-12-24': 7}, {'2024-12-25': 7}, {'2024-12-26': 7}, {'2024-12-27': 7}, {'2024-12-28': 0}, {'2024-12-29': 0}], [{'2024-12-30': 7}, {'2024-12-31': 7}, None, None, None, None, None]]
dec_24_reel = [[None, None, None, None, None, None, {'2024-12-01': 0}], [{'2024-12-02': 7}, {'2024-12-03': 8}, {'2024-12-04': 8}, {'2024-12-05': 7}, {'2024-12-06': 7}, {'2024-12-07': 0}, {'2024-12-08': 0}], [{'2024-12-09': 4}, {'2024-12-10': 8}, {'2024-12-11': 8}, {'2024-12-12': 10}, {'2024-12-13': 4}, {'2024-12-14': 0}, {'2024-12-15': 0}], [{'2024-12-16': 7}, {'2024-12-17': 7}, {'2024-12-18': 7}, {'2024-12-19': 6}, {'2024-12-20': 8}, {'2024-12-21': 0}, {'2024-12-22': 0}], [{'2024-12-23': 7}, {'2024-12-24': 8}, {'2024-12-25': 8}, {'2024-12-26': 7}, {'2024-12-27': 7}, {'2024-12-28': 0}, {'2024-12-29': 0}], [{'2024-12-30': 12}, {'2024-12-31': 12}, None, None, None, None, None]]
dec_24_nuit = [[None, None, None, None, None, None, {'2024-12-01': 0}], [{'2024-12-02': 0}, {'2024-12-03': 0}, {'2024-12-04': 0}, {'2024-12-05': 0}, {'2024-12-06': 0}, {'2024-12-07': 0}, {'2024-12-08': 0}], [{'2024-12-09': 0}, {'2024-12-10': 0}, {'2024-12-11': 0}, {'2024-12-12': 0}, {'2024-12-13': 0}, {'2024-12-14': 0}, {'2024-12-15': 0}], [{'2024-12-16': 0}, {'2024-12-17': 0}, {'2024-12-18': 0}, {'2024-12-19': 0}, {'2024-12-20': 0}, {'2024-12-21': 0}, {'2024-12-22': 0}], [{'2024-12-23': 0}, {'2024-12-24': 0}, {'2024-12-25': 0}, {'2024-12-26': 0}, {'2024-12-27': 0}, {'2024-12-28': 0}, {'2024-12-29': 0}], [{'2024-12-30': 0}, {'2024-12-31': 0}, None, None, None, None, None]]
dec_24_dimanche = [[None, None, None, None, None, None, {'2024-12-01': 0}], [{'2024-12-02': 0}, {'2024-12-03': 0}, {'2024-12-04': 0}, {'2024-12-05': 0}, {'2024-12-06': 0}, {'2024-12-07': 0}, {'2024-12-08': 0}], [{'2024-12-09': 0}, {'2024-12-10': 0}, {'2024-12-11': 0}, {'2024-12-12': 0}, {'2024-12-13': 0}, {'2024-12-14': 0}, {'2024-12-15': 0}], [{'2024-12-16': 0}, {'2024-12-17': 0}, {'2024-12-18': 0}, {'2024-12-19': 0}, {'2024-12-20': 0}, {'2024-12-21': 0}, {'2024-12-22': 0}], [{'2024-12-23': 0}, {'2024-12-24': 0}, {'2024-12-25': 0}, {'2024-12-26': 0}, {'2024-12-27': 0}, {'2024-12-28': 0}, {'2024-12-29': 0}], [{'2024-12-30': 0}, {'2024-12-31': 0}, None, None, None, None, None]]
dec_24_rtt = [[None, None, None, None, None, None, {'2024-12-01': 0}], [{'2024-12-02': 0}, {'2024-12-03': 0}, {'2024-12-04': 0}, {'2024-12-05': 0}, {'2024-12-06': 0}, {'2024-12-07': 0}, {'2024-12-08': 0}], [{'2024-12-09': 0}, {'2024-12-10': 0}, {'2024-12-11': 0}, {'2024-12-12': 0}, {'2024-12-13': 0}, {'2024-12-14': 0}, {'2024-12-15': 0}], [{'2024-12-16': 0}, {'2024-12-17': 0}, {'2024-12-18': 0}, {'2024-12-19': 0}, {'2024-12-20': 0}, {'2024-12-21': 0}, {'2024-12-22': 0}], [{'2024-12-23': 0}, {'2024-12-24': 0}, {'2024-12-25': 0}, {'2024-12-26': 0}, {'2024-12-27': 0}, {'2024-12-28': 0}, {'2024-12-29': 0}], [{'2024-12-30': 0}, {'2024-12-31': 0}, None, None, None, None, None]]
dec_24_cp = [[None, None, None, None, None, None, {'2024-12-01': 0}], [{'2024-12-02': 0}, {'2024-12-03': 0}, {'2024-12-04': 0}, {'2024-12-05': 0}, {'2024-12-06': 0}, {'2024-12-07': 0}, {'2024-12-08': 0}], [{'2024-12-09': 0}, {'2024-12-10': 0}, {'2024-12-11': 0}, {'2024-12-12': 0}, {'2024-12-13': 0}, {'2024-12-14': 0}, {'2024-12-15': 0}], [{'2024-12-16': 0}, {'2024-12-17': 0}, {'2024-12-18': 0}, {'2024-12-19': 0}, {'2024-12-20': 0}, {'2024-12-21': 0}, {'2024-12-22': 0}], [{'2024-12-23': 0}, {'2024-12-24': 0}, {'2024-12-25': 0}, {'2024-12-26': 0}, {'2024-12-27': 0}, {'2024-12-28': 0}, {'2024-12-29': 0}], [{'2024-12-30': 0}, {'2024-12-31': 0}, None, None, None, None, None]]
dec_24_jfr = [[None, None, None, None, None, None, {'2024-12-01': 0}], [{'2024-12-02': 0}, {'2024-12-03': 0}, {'2024-12-04': 0}, {'2024-12-05': 0}, {'2024-12-06': 0}, {'2024-12-07': 0}, {'2024-12-08': 0}], [{'2024-12-09': 0}, {'2024-12-10': 0}, {'2024-12-11': 0}, {'2024-12-12': 0}, {'2024-12-13': 0}, {'2024-12-14': 0}, {'2024-12-15': 0}], [{'2024-12-16': 0}, {'2024-12-17': 0}, {'2024-12-18': 0}, {'2024-12-19': 0}, {'2024-12-20': 0}, {'2024-12-21': 0}, {'2024-12-22': 0}], [{'2024-12-23': 0}, {'2024-12-24': 0}, {'2024-12-25': 0}, {'2024-12-26': 0}, {'2024-12-27': 0}, {'2024-12-28': 0}, {'2024-12-29': 0}], [{'2024-12-30': 0}, {'2024-12-31': 0}, None, None, None, None, None]]
dec_24_jfnr = [[None, None, None, None, None, None, {'2024-12-01': 0}], [{'2024-12-02': 0}, {'2024-12-03': 0}, {'2024-12-04': 0}, {'2024-12-05': 0}, {'2024-12-06': 0}, {'2024-12-07': 0}, {'2024-12-08': 0}], [{'2024-12-09': 0}, {'2024-12-10': 0}, {'2024-12-11': 0}, {'2024-12-12': 0}, {'2024-12-13': 0}, {'2024-12-14': 0}, {'2024-12-15': 0}], [{'2024-12-16': 0}, {'2024-12-17': 0}, {'2024-12-18': 0}, {'2024-12-19': 0}, {'2024-12-20': 0}, {'2024-12-21': 0}, {'2024-12-22': 0}], [{'2024-12-23': 0}, {'2024-12-24': 0}, {'2024-12-25': 0}, {'2024-12-26': 0}, {'2024-12-27': 0}, {'2024-12-28': 0}, {'2024-12-29': 0}], [{'2024-12-30': 0}, {'2024-12-31': 0}, None, None, None, None, None]]
dec_24_abs_inj = [[None, None, None, None, None, None, {'2024-12-01': 0}], [{'2024-12-02': 0}, {'2024-12-03': 0}, {'2024-12-04': 0}, {'2024-12-05': 0}, {'2024-12-06': 0}, {'2024-12-07': 0}, {'2024-12-08': 0}], [{'2024-12-09': 0}, {'2024-12-10': 0}, {'2024-12-11': 0}, {'2024-12-12': 0}, {'2024-12-13': 0}, {'2024-12-14': 0}, {'2024-12-15': 0}], [{'2024-12-16': 0}, {'2024-12-17': 0}, {'2024-12-18': 0}, {'2024-12-19': 0}, {'2024-12-20': 0}, {'2024-12-21': 0}, {'2024-12-22': 0}], [{'2024-12-23': 0}, {'2024-12-24': 0}, {'2024-12-25': 0}, {'2024-12-26': 0}, {'2024-12-27': 0}, {'2024-12-28': 0}, {'2024-12-29': 0}], [{'2024-12-30': 0}, {'2024-12-31': 0}, None, None, None, None, None]]
dec_24_abs_mal = [[None, None, None, None, None, None, {'2024-12-01': 0}], [{'2024-12-02': 0}, {'2024-12-03': 0}, {'2024-12-04': 0}, {'2024-12-05': 0}, {'2024-12-06': 0}, {'2024-12-07': 0}, {'2024-12-08': 0}], [{'2024-12-09': 1}, {'2024-12-10': 0}, {'2024-12-11': 0}, {'2024-12-12': 0}, {'2024-12-13': 0}, {'2024-12-14': 0}, {'2024-12-15': 0}], [{'2024-12-16': 0}, {'2024-12-17': 0}, {'2024-12-18': 0}, {'2024-12-19': 0}, {'2024-12-20': 0}, {'2024-12-21': 0}, {'2024-12-22': 0}], [{'2024-12-23': 0}, {'2024-12-24': 0}, {'2024-12-25': 0}, {'2024-12-26': 0}, {'2024-12-27': 0}, {'2024-12-28': 0}, {'2024-12-29': 0}], [{'2024-12-30': 0}, {'2024-12-31': 0}, None, None, None, None, None]]
dec_24 = combine_timesheets(dec_24_contrat, dec_24_reel, dec_24_nuit, dec_24_dimanche, dec_24_rtt, dec_24_cp, dec_24_jfr, dec_24_jfnr, dec_24_abs_inj, dec_24_abs_mal)

jan_25_contrat = [[None, None, {'2025-01-01': 7}, {'2025-01-02': 7}, {'2025-01-03': 7}, {'2025-01-04': 0}, {'2025-01-05': 0}], [{'2025-01-06': 7}, {'2025-01-07': 7}, {'2025-01-08': 7}, {'2025-01-09': 7}, {'2025-01-10': 7}, {'2025-01-11': 0}, {'2025-01-12': 0}], [{'2025-01-13': 7}, {'2025-01-14': 7}, {'2025-01-15': 7}, {'2025-01-16': 7}, {'2025-01-17': 7}, {'2025-01-18': 0}, {'2025-01-19': 0}], [{'2025-01-20': 7}, {'2025-01-21': 7}, {'2025-01-22': 7}, {'2025-01-23': 7}, {'2025-01-24': 7}, {'2025-01-25': 0}, {'2025-01-26': 0}], [{'2025-01-27': 7}, {'2025-01-28': 7}, {'2025-01-29': 7}, {'2025-01-30': 7}, {'2025-01-31': 7}, None, None]]
jan_25_reel = [[None, None, {'2025-01-01': 7}, {'2025-01-02': 7}, {'2025-01-03': 7}, {'2025-01-04': 0}, {'2025-01-05': 0}], [{'2025-01-06': 7}, {'2025-01-07': 7}, {'2025-01-08': 7}, {'2025-01-09': 7}, {'2025-01-10': 7}, {'2025-01-11': 0}, {'2025-01-12': 0}], [{'2025-01-13': 7}, {'2025-01-14': 7}, {'2025-01-15': 7}, {'2025-01-16': 7}, {'2025-01-17': 7}, {'2025-01-18': 0}, {'2025-01-19': 0}], [{'2025-01-20': 7}, {'2025-01-21': 7}, {'2025-01-22': 7}, {'2025-01-23': 7}, {'2025-01-24': 7}, {'2025-01-25': 0}, {'2025-01-26': 0}], [{'2025-01-27': 7}, {'2025-01-28': 7}, {'2025-01-29': 7}, {'2025-01-30': 7}, {'2025-01-31': 7}, None, None]]
jan_25_nuit = generate_timesheet(2025, 1)
jan_25_dimanche = generate_timesheet(2025, 1)
jan_25_rtt = generate_timesheet(2025, 1)
jan_25_cp = generate_timesheet(2025, 1)
jan_25_jfr = generate_timesheet(2025, 1)
jan_25_jfnr = generate_timesheet(2025, 1)
jan_25_abs_inj = generate_timesheet(2025, 1)
jan_25_abs_mal = generate_timesheet(2025, 1)
jan_25 = combine_timesheets(jan_25_contrat, jan_25_reel, jan_25_nuit, jan_25_dimanche, jan_25_rtt, jan_25_cp, jan_25_jfr, jan_25_jfnr, jan_25_abs_inj, jan_25_abs_mal)

def afficher_evolution_conges_payes(salarie, timesheet):
    # Initialiser une liste pour stocker les soldes mensuels
    soldes_mensuels = []
    
    # Obtenir la plage de dates pour les mois à afficher
    dates = pd.date_range(start=timesheet.index.min(), end=timesheet.index.max(), freq='M')
    
    for date in dates:
        # Filtrer le timesheet pour le mois courant
        timesheet_mois = timesheet[timesheet.index.to_period('M') == date.to_period('M')]
        
        # Appeler la fonction evolution_cp pour obtenir les soldes
        solde_debut, gain_cp, utilisation, solde_fin = evolution_cp(salarie, timesheet_mois)
        
        # Ajouter les résultats à la liste
        soldes_mensuels.append({
            'Mois': date.month,
            'Solde Début': solde_debut,
            'Gain CP': gain_cp,
            'Utilisation': utilisation,
            'Solde Fin': solde_fin
        })
    
    # Créer un DataFrame à partir des soldes mensuels
    df_soldes = pd.DataFrame(soldes_mensuels).tail(1)
    
    # Afficher le tableau
    st.dataframe(df_soldes)

def main():
    # Configuration de la page
    st.set_page_config(
        page_title="Peppers",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Créer deux colonnes pour le logo et le titre
    col1, col2 = st.columns([1, 4])

    with col1:
        # Ajouter le logo
        st.image("logo_peppers_black.png", width=200)  # Ajustez le chemin et la taille selon votre logo

    with col2:
        # Ajouter le titre
        st.title("Peppers: Générateur de Fiche de Paie")
        st.write("Renseignez vos variables de rémunération et générez votre bulletin de paie au format CSV.")

    # Create three columns with the middle one empty for spacing
    col1, col_space, col2 = st.columns([4, 1, 4])

    # --- Entreprise Inputs (Left Column) ---
    with col1:
        st.markdown("---")
        st.header("Entreprise")
        st.markdown("<br>", unsafe_allow_html=True)
        
        entreprise_nom = st.text_input("Nom de l'Entreprise", "Pennylane")
        st.markdown("<br>", unsafe_allow_html=True)
        
        entreprise_adresse = st.text_input("Adresse", "4 rue Jules Lefebvre, 75009 Paris")
        st.markdown("<br>", unsafe_allow_html=True)
        
        entreprise_siret = st.text_input("SIRET", "1209384736")
        st.markdown("<br>", unsafe_allow_html=True)
        
        entreprise_effectif = st.number_input("Effectif", min_value=1, value=12)
        st.markdown("<br>", unsafe_allow_html=True)
        
        entreprise_taux_AT = st.number_input("Taux AT", value=0.00212, format="%.5f")
        st.markdown("<br>", unsafe_allow_html=True)

        entreprise = Entreprise(
            nom=entreprise_nom,
            adresse=entreprise_adresse,
            siret=entreprise_siret,
            effectif=entreprise_effectif,
            taux_AT=entreprise_taux_AT
        )
        st.markdown("---")



    # --- Salarie Inputs (Right Column) ---
    with col2:
        st.markdown("---")
        st.header("Salarie")
        st.markdown("<br>", unsafe_allow_html=True)
        
        salarie_nom = st.text_input("Nom", "Dupont")
        st.markdown("<br>", unsafe_allow_html=True)
        
        salarie_prenom = st.text_input("Prénom", "Eric")
        st.markdown("<br>", unsafe_allow_html=True)
        
        salarie_numero_ss = st.text_input("Numéro de Sécurité Sociale", "120000")
        st.markdown("<br>", unsafe_allow_html=True)
        
        salarie_date_naissance = st.date_input("Date de Naissance", date(1973, 2, 28))
        st.markdown("<br>", unsafe_allow_html=True)
        
        salarie_date_entree = st.date_input("Date d'entrée", date(2016, 9, 17))
        st.markdown("<br>", unsafe_allow_html=True)
        
        salarie_contrat = st.selectbox("Contrat", ["CDI", "CDD"], index=0)
        st.markdown("<br>", unsafe_allow_html=True)
        
        salarie_statut = st.selectbox("Statut", ["salarié", "cadre"], index=0)
        st.markdown("<br>", unsafe_allow_html=True)
        
        salarie_salaire_de_base = st.number_input("Salaire de Base", value=1801.80)
        st.markdown("<br>", unsafe_allow_html=True)

        salarie = Salarie(
            nom=salarie_nom,
            prenom=salarie_prenom,
            numero_ss=salarie_numero_ss,
            date_naissance=salarie_date_naissance.strftime("%Y-%m-%d"),
            date_entree=salarie_date_entree.strftime("%Y-%m-%d"),
            contrat=salarie_contrat,
            statut=salarie_statut,
            horaires_par_defaut={"lundi": 7},
            salaire_de_base=salarie_salaire_de_base,
            entreprise=entreprise,
            douze_derniers_salaires=[salarie_salaire_de_base] * 12
        )
        st.markdown("---")

    # --- Timesheet Section ---
    st.header("Timesheet Janvier 2025")
    
    # Tabs pour différents types d'heures
    tabs = st.tabs([
        "Heures contractuelles",
        "Heures réelles",
        "Heures de nuit",
        "Heures dimanche",
        "RTT",
        "Congés payés",
        "Jours fériés",
        "Absences maladie"
    ])
    
    with tabs[0]:
        create_calendar_input("contractuelles", 2025, 1)
    
    with tabs[1]:
        create_calendar_input("reelles", 2025, 1)
    
    with tabs[2]:
        create_calendar_input("nuit", 2025, 1)
    
    with tabs[3]:
        create_calendar_input("dimanche", 2025, 1)
    
    with tabs[4]:
        create_calendar_input("rtt", 2025, 1)
    
    with tabs[5]:
        create_calendar_input("cp", 2025, 1)
    
    with tabs[6]:
        create_calendar_input("jf", 2025, 1)
    
    with tabs[7]:
        create_calendar_input("maladie", 2025, 1)

    # --- Avantages Section ---
    st.header("Avantages")
    
    # Create expandable sections for each type of advantage
    with st.expander("Nourriture"):
        nourriture_enabled = st.checkbox("Activer l'avantage nourriture")
        if nourriture_enabled:
            nourriture_type = st.selectbox("Type de nourriture", ["restaurant", "cantine"])
        else:
            nourriture_type = None

    with st.expander("Logement"):
        logement_enabled = st.checkbox("Activer l'avantage logement")
        if logement_enabled:
            logement_mode = st.selectbox("Mode", ["forfaitaire", "réel"])
            pieces_principales = st.number_input("Nombre de pièces principales", min_value=1, value=3)
        else:
            logement_mode = None
            pieces_principales = None

    with st.expander("Voiture"):
        voiture_enabled = st.checkbox("Activer l'avantage voiture")
        if voiture_enabled:
            voiture_mode = st.selectbox("Mode voiture", ["forfaitaire", "réel"])
        else:
            voiture_mode = None

    # Build avantages dictionary based on user inputs
    avantages = {}
    if nourriture_enabled:
        avantages["nourriture"] = {"type": "nourriture"}
        if nourriture_type:
            avantages["nourriture"]["mode"] = nourriture_type

    if logement_enabled:
        avantages["logement"] = {
            "type": "logement",
            "mode": logement_mode,
            "params": {"pieces principales": pieces_principales} if logement_mode == "forfaitaire" else {}
        }

    if voiture_enabled:
        avantages["voiture"] = {
            "type": "voiture",
            "mode": voiture_mode
        }


 # --- Primes Section ---
    st.header("Primes")

    # Créer des sections extensibles pour chaque type de prime
    with st.expander("13ème mois"):
        prime_13_mois_enabled = st.checkbox("Activer la prime 13ème mois")
        if prime_13_mois_enabled:
            prime_13_mois_mensualise = st.checkbox("Mensualiser la prime 13ème mois", value=False)

    with st.expander("Ancienneté"):
        prime_anciennete_enabled = st.checkbox("Activer la prime d'ancienneté")

    with st.expander("Exceptionnelle"):
        prime_exceptionnelle_enabled = st.checkbox("Activer la prime exceptionnelle")
        if prime_exceptionnelle_enabled:
            prime_exceptionnelle_valeur = st.number_input("Valeur de la prime exceptionnelle", value=0.0)

    # Construire le dictionnaire des primes basé sur les entrées de l'utilisateur
    primes = {}
    if prime_13_mois_enabled:
        primes["13ème mois"] = {
            "type": "13ème mois",
            "mode": prime_13_mois_mensualise,
        }
    if prime_anciennete_enabled:
        # Correction : utiliser "ancienneté" avec accent pour être cohérent avec le back
        primes["ancienneté"] = {"type": "ancienneté"}
    if prime_exceptionnelle_enabled:
        primes["exceptionnelle"] = {"type": "exceptionnelle", "valeur": prime_exceptionnelle_valeur}
    

    # --- Compute Payroll ---
    if st.button("Génération Fiche de Paie"):
        # Show the current avantages configuration
        #st.subheader("Avantages configurés")
        #st.json(avantages)

        # Calculer les cotisations
        cotisations = calcul_cotisations(salarie)

        # Convertir les données du formulaire en timesheet
        ts_contract = convert_to_timesheet(st.session_state['timesheet_contractuelles'], 2025, 1)
        ts_reelles = convert_to_timesheet(st.session_state['timesheet_reelles'], 2025, 1)
        ts_nuit = convert_to_timesheet(st.session_state['timesheet_nuit'], 2025, 1)
        ts_dimanche = convert_to_timesheet(st.session_state['timesheet_dimanche'], 2025, 1)
        ts_rtt = convert_to_timesheet(st.session_state['timesheet_rtt'], 2025, 1)
        ts_cp = convert_to_timesheet(st.session_state['timesheet_cp'], 2025, 1)
        ts_jf = convert_to_timesheet(st.session_state['timesheet_jf'], 2025, 1)
        ts_maladie = convert_to_timesheet(st.session_state['timesheet_maladie'], 2025, 1)

        # Combiner les timesheets
        jan_25 = combine_timesheets(
            ts_contract,
            ts_reelles,
            ts_nuit,
            ts_dimanche,
            ts_rtt,
            ts_cp,
            ts_jf,
            generate_timesheet(2025, 1),  # jf non rémunérés vides
            generate_timesheet(2025, 1),  # absences injustifiées vides
            ts_maladie
        )

        

        # Calculer la fiche de paie avec les absences
        df_pay = fiche_de_paie(
            salarie=salarie,
            avantages=avantages,
            primes=primes,
            timesheet=jan_25,
            timesheet_prec=dec_24,
            absence_motifs=st.session_state.absence_motifs
        )


        cotis=calcul_cotisations(salarie=salarie)
        df_cotisations = df_cotis(salarie=salarie,cotisations=cotis,df_salaire=df_pay)
 
          # Ajouter les réductions
        df_reduc = df_reductions(salarie, df_cotisations, jan_25, avantages)
    
         # Ajouter les sous-totaux
        df_final = ajouter_sous_totaux(df_reduc, salarie, jan_25)
    
        

         # Convertir les colonnes en numérique
        df_final['Total (€)'] = pd.to_numeric(df_final['Total (€)'], errors='coerce')
        df_final['Part_Employeur'] = pd.to_numeric(df_final['Part_Employeur'], errors='coerce')
        
        # # Filtrer les lignes
        df_filtered = df_final[
             ~((df_final['Total (€)'].fillna(0) == 0) & 
               (df_final['Part_Employeur'].fillna(0) == 0)) |
             (df_final['Catégorie'].str.contains('Sous-total|Total|Net|Salaire', na=False))]
        
        df_filtered = df_filtered.fillna("")


        # Afficher le DataFrame filtré
        st.subheader("Fiche de paie")
        st.dataframe(
            df_filtered,
            hide_index=True,
            use_container_width=True,
            height=800
        )

        # Option pour télécharger la fiche de paie
        csv = df_filtered.to_csv(index=True)
        st.download_button(
            label="Télécharger la fiche de paie (CSV)",
            data=csv,
            file_name=f'fiche_de_paie_{salarie.nom}_{datetime.now().strftime("%Y-%m")}.csv',
            mime='text/csv'
        )


        st.subheader("Solde Congés Payés")
        # Affichage de l'évolution des congés payés
        afficher_evolution_conges_payes(salarie, jan_25)



def convert_to_timesheet(data_dict, year, month):
    """Convert flat dictionary to timesheet format"""
    timesheet = generate_timesheet(year, month)
    for week in timesheet:
        for day in week:
            if day is not None:
                date_str = list(day.keys())[0]
                day[date_str] = data_dict.get(date_str, 0)
    return timesheet

if __name__ == "__main__":
    main()
