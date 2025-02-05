from dataclasses import dataclass, field
from typing import Dict
from datetime import datetime, timedelta
import calendar
import pandas as pd

@dataclass

class Entreprise:
    nom: str
    adresse: str
    siret: str
    effectif: float
    taux_AT: float
    complementaire_sante: bool = False
    complementaire_invalidité: bool = False
    versement_mobilite: bool = False
    taux_complementaire_sante: float = 0.0
    forfait_complementaire_sante: float = 100.0
    forfait_mutuelle: float = 30.0
    taux_complementaire_invalidité: float = 0.0
    forfait_complementaire_invalidité: float = 0.0
    taux_versement_mobilite: float = 0.0
    taux_transport: float = 0.5
    prix_transport: float = 88.80
    titre_restaurant: float = 12.50
    participation_titre_restaurant: float = 0.6
    titre_transport: float = 0.0
    taux_anciennete: float =0.005
    subrogation: bool = True

@dataclass
class Salarie:
    nom: str
    prenom: str
    numero_ss: str
    date_naissance: str
    date_entree: str
    contrat: str  # e.g., "CDI" ou "CDD"
    statut: str   # e.g., "salarié" ou "cadre"
    horaires_par_defaut: Dict[str, int]
    salaire_de_base: float
    temps_travail: float = 151.67
    solde_cp: float =6.0
    solde_rtt: float =0.0
    mutuelle: bool = False
    douze_derniers_salaires: list = field(default_factory=lambda: [0.0 for _ in range(12)])
    rtt: bool = False
    entreprise: Entreprise = field(default=None)
    salaire_brut: float = 0.0

# =============================================================================
# Functions for Timesheet Generation, Flattening, Combining, and Calculations
# =============================================================================
def generate_timesheet(year, month, manual_data=None):
    """
    Génère une timesheet pour un mois donné.
    Args:
        year: année
        month: mois
        manual_data: dictionnaire optionnel {date_str: heures} pour les valeurs saisies manuellement
    """
    first_day, days_in_month = calendar.monthrange(year, month)
    first_date = datetime(year, month, 1)
    if first_day != 0:  # Si le premier jour n'est pas un lundi
        first_date -= timedelta(days=first_day)
    
    timesheet = []
    current_date = first_date
    
    # Tant que la semaine en cours contient au moins un jour dans le mois
    while current_date.month == month or (current_date + timedelta(days=6)).month == month:
        week = []
        for _ in range(7):
            date_str = current_date.strftime('%Y-%m-%d')
            if current_date.month == month:
                # Utilise la valeur manuelle si disponible, sinon 0
                hours = manual_data.get(date_str, 0) if manual_data else 0
                week.append({date_str: hours})
            else:
                week.append(None)
            current_date += timedelta(days=1)
        timesheet.append(week)
    return timesheet

def flatten_timesheet(timesheet):
    """
    Aplati la timesheet (liste de semaines) en un dictionnaire {date: valeur}.
    On parcourt les semaines et on construit un dictionnaire pour toutes les dates entre
    le lundi de la semaine contenant le premier jour du mois et le dernier jour du mois.
    """
    original_flat = {}
    for week in timesheet:
        for day in week:
            if day is not None:
                for date_str, value in day.items():
                    original_flat[date_str] = value
    if not original_flat:
        return {}
    dates = [datetime.strptime(d, '%Y-%m-%d') for d in original_flat.keys()]
    first_in_month = min(dates)
    start_date = first_in_month - timedelta(days=first_in_month.weekday())
    year = first_in_month.year
    month = first_in_month.month
    last_day = calendar.monthrange(year, month)[1]
    end_date = datetime(year, month, last_day)
    flat = {}
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        flat[date_str] = original_flat.get(date_str, 0)
        current_date += timedelta(days=1)
    return flat

def combine_timesheets(ts_contract, ts_reelles, ts_nuit, ts_dimanche,
                      ts_RTT, ts_CP, ts_jf_r, ts_jf_nonr, ts_injust, ts_maladie,
                      manual_data=None):
    """
    Combine les différentes timesheets en un DataFrame pandas.
    Args:
        ts_*: timesheets au format liste de semaines
        manual_data: dictionnaire optionnel contenant les données manuelles pour chaque type
                    {type: {date: valeur}}
    """
    # Conversion des timesheets en dictionnaires plats
    data_contract = flatten_timesheet(ts_contract)
    data_reelles = flatten_timesheet(ts_reelles)
    data_nuit = flatten_timesheet(ts_nuit)
    data_dimanche = flatten_timesheet(ts_dimanche)
    data_RTT = flatten_timesheet(ts_RTT)
    data_CP = flatten_timesheet(ts_CP)
    data_jf_r = flatten_timesheet(ts_jf_r)
    data_jf_nonr = flatten_timesheet(ts_jf_nonr)
    data_injust = flatten_timesheet(ts_injust)
    data_maladie = flatten_timesheet(ts_maladie)

    # Si des données manuelles sont fournies, les utiliser pour écraser les valeurs
    if manual_data:
        if 'heures_reelles' in manual_data:
            data_reelles.update(manual_data['heures_reelles'])
        if 'heures_nuit' in manual_data:
            data_nuit.update(manual_data['heures_nuit'])
        if 'heures_dimanche' in manual_data:
            data_dimanche.update(manual_data['heures_dimanche'])
        if 'RTT' in manual_data:
            data_RTT.update(manual_data['RTT'])
        if 'conges_payes' in manual_data:
            data_CP.update(manual_data['conges_payes'])
        if 'absences' in manual_data:
            data_maladie.update(manual_data['absences'])

    # Utiliser l'union de toutes les dates comme index
    all_dates = sorted(set().union(
        data_contract.keys(), data_reelles.keys(), data_nuit.keys(),
        data_dimanche.keys(), data_RTT.keys(), data_CP.keys(),
        data_jf_r.keys(), data_jf_nonr.keys(), data_injust.keys(),
        data_maladie.keys()
    ))

    df = pd.DataFrame({
        "heures contractuelles": [data_contract.get(date, 0) for date in all_dates],
        "heures réelles normales": [data_reelles.get(date, 0) for date in all_dates],
        "heures de nuit": [data_nuit.get(date, 0) for date in all_dates],
        "heures de dimanche": [data_dimanche.get(date, 0) for date in all_dates],
        "absence rémunérée RTT": [data_RTT.get(date, 0) for date in all_dates],
        "absence rémunérée congé payé": [data_CP.get(date, 0) for date in all_dates],
        "absence rémunérée jour férié": [data_jf_r.get(date, 0) for date in all_dates],
        "absence non rémunérée jour férié": [data_jf_nonr.get(date, 0) for date in all_dates],
        "absence non rémunérée absence injustifiée": [data_injust.get(date, 0) for date in all_dates],
        "absence maladie": [data_maladie.get(date, 0) for date in all_dates],
    }, index=all_dates)
    
    df.index.name = "date"
    return df

def merge_overlapping_days(df_prev, df_current):
    """
    Fusionne les données de deux DataFrames (mois précédent et mois en cours)
    pour les dates communes en additionnant les valeurs.
    """
    dates_communes = df_prev.index.intersection(df_current.index)
    df_current.loc[dates_communes] = df_current.loc[dates_communes].add(
        df_prev.loc[dates_communes], fill_value=0
    )
    return df_current

def filter_ts(timesheet):
    timesheet.index = pd.to_datetime(timesheet.index)
    first_day_of_month = timesheet.index.max().replace(day=1)
    timesheet_filtered = timesheet[timesheet.index>= first_day_of_month]
    return timesheet_filtered

def get_absence_motifs(timesheet_df):
    absence_dates = timesheet_df[timesheet_df['absence maladie'] > 0].index.strftime('%Y-%m-%d').tolist()
    absence_motifs = {}
    for date in absence_dates:
        motif = input(f"Veuillez entrer le motif de l'absence pour {date} (maladie, accident travail, maternité) : ")
        absence_motifs[date] = motif
    return absence_motifs

def calcul_hs(df):
    """
    Calcule les heures supplémentaires journalières puis agrège par semaine.
    Pour chaque jour :
        heures supplémentaires = (heures réelles normales - heures contractuelles)
                                  + (absences rémunérées * heures contractuelles)
    Puis, pour chaque semaine :
      - Les 8 premières heures supplémentaires (ou moins) sont majorées à 25%.
      - Les heures au-delà de 8 sont majorées à 50%.
      
    Si la dernière date du DataFrame n'est pas un vendredi, samedi ou dimanche,
    la dernière semaine est exclue du calcul.
    """
    # Assurer que l'index est en datetime
    df.index = pd.to_datetime(df.index)
    df["heures supplémentaires"] = (
        df["heures réelles normales"] - df["heures contractuelles"] +
        (df["absence rémunérée RTT"] + df["absence rémunérée congé payé"] + df["absence rémunérée jour férié"]) *
        df["heures contractuelles"]
    )
    weekly_hs = df.resample('W-SUN')["heures supplémentaires"].sum()
    last_date = df.index.max()
    if last_date.weekday() not in [4, 5, 6]:  # 4: vendredi, 5: samedi, 6: dimanche
        weekly_hs = weekly_hs.iloc[:-1]
    total_25 = 0
    total_50 = 0
    for hs_semaine in weekly_hs:
        hs_25 = min(hs_semaine, 8)
        hs_50 = max(hs_semaine - 8, 0)
        total_25 += hs_25
        total_50 += hs_50
    return total_25, total_50


def evolution_cp(salarie, timesheet):
    solde_debut = salarie.solde_cp
    if not isinstance(timesheet.index, pd.DatetimeIndex):
        timesheet.index = pd.to_datetime(timesheet.index)
    
    first_day_of_month = timesheet.index.min().replace(day=1)
    timesheet_filtered = timesheet[timesheet.index>= first_day_of_month]
    
    # Sum the usage of paid leave ("absence rémunérée congé payé").
    utilisation = timesheet_filtered["absence rémunérée congé payé"].sum()
    
    # Define the monthly gain in CP (congé payé).
    gain_cp = 2.08
    
    # Calculate the ending balance.
    solde_fin = solde_debut + gain_cp - utilisation
    
    return [solde_debut, gain_cp, utilisation, solde_fin]



def prime_de_treizieme_mois(salarie,mois,is_mensualise=False):
    if is_mensualise==True:
        prime = salarie.salaire_de_base /12 
    elif mois == 12 and is_mensualise==False:
        prime = salarie.salaire_de_base
    else: 
        prime = 0
    return prime

def prime_anciennete(salarie):    
    date_entree = datetime.strptime(salarie.date_entree, "%Y-%m-%d")
    anciennete = int((datetime.now() - date_entree).days // 365)
    taux_anciennete_reel=(salarie.entreprise.taux_anciennete)*(anciennete) 
    prime = taux_anciennete_reel * salarie.salaire_de_base
    return float(prime)

def prime_exceptionnelle (salarie,valeur=0.0):
    if valeur !=0:
        prime = float(valeur)
    else:
        prime= 0
    return prime

def calcul_primes(salarie: Salarie, primes: Dict[str, dict], timesheet) -> dict:
    primes_totales = {}
    total_primes = 0
    # Récupérer le mois en se basant sur la date minimale du timesheet
    first_day_of_month = timesheet.index.min().replace(day=1)
    mois = first_day_of_month.month
    
    for prime, details in primes.items():
        type_prime = details["type"]
        
        if type_prime == "13ème mois":
            # On récupère le mode de calcul : True si mensualisé, False sinon
            mode_calcul = details.get("mode", False)
            valeur_13 = prime_de_treizieme_mois(salarie, mois, is_mensualise=mode_calcul)
            primes_totales[prime] = valeur_13
            total_primes += valeur_13

        elif type_prime == "ancienneté":
            valeur_anc = prime_anciennete(salarie)
            primes_totales[prime] = valeur_anc
            total_primes += valeur_anc

        elif type_prime == "exceptionnelle":
            valeur_ex = prime_exceptionnelle(salarie, details['valeur'])
            primes_totales[prime] = valeur_ex
            total_primes += valeur_ex


    result = {
        "Détail des primes": {k: round(v, 2) for k, v in primes_totales.items()},
        "Total des primes": round(total_primes, 2)
    }
    return result



def calcul_avantages_en_nature(salarie: Salarie, avantages: Dict[str, dict], timesheet) -> dict:
    """
    Calcule les avantages en nature à intégrer au salaire brut et au bulletin de paie.

    :param salarie: Objet Salarie contenant les informations du salarié
    :param avantages: Dictionnaire décrivant les avantages en nature (type, mode de calcul, paramètres)
    :param timesheet: DataFrame contenant les heures travaillées
    :return: Dictionnaire avec les valeurs des avantages et les impacts sur le salaire
    """

    avantages_totaux = {}
    total_avantages = 0
    first_day_of_month = timesheet.index.min().replace(day=1)
    timesheet_filtered = timesheet[timesheet.index >= first_day_of_month]
    jours_travailles = (timesheet_filtered["heures réelles normales"] != 0).sum()

    for avantage, details in avantages.items():
        type_avantage = details["type"]
        mode_calcul = details.get("mode", "forfaitaire")  # Par défaut, mode forfaitaire
        params = details.get("params", {})

        if type_avantage == "nourriture":
            valeur_nourriture = 0
            repas_par_jour = params.get("repas_par_jour", 1)
            forfait_par_repas = salarie.entreprise.titre_restaurant * (1-salarie.entreprise.participation_titre_restaurant)
            valeur_nourriture = repas_par_jour * forfait_par_repas * jours_travailles
            avantages_totaux[avantage] = valeur_nourriture
            # Ne rentre pas dans le total des avantages / sert uniquement pour déduire la part salariale à la fin du bulletin
        
        elif type_avantage == "logement":
            valeur_logement = 0
            salaire_ref = salarie.salaire_de_base
            pieces = params.get("pieces principales", 1)

            if mode_calcul == "forfaitaire":
                if salaire_ref < 1932:
                    valeur_logement = 77.30 if pieces == 1 else 41.40 * pieces
                elif 1932 <= salaire_ref < 2318.39:
                    valeur_logement = 90.20 if pieces == 1 else 57.90 * pieces
                elif 2318.40 <= salaire_ref < 2704.79:
                    valeur_logement = 102.90 if pieces == 1 else 77.90 * pieces
                elif 2704.80 <= salaire_ref < 3477.59:
                    valeur_logement = 115.80 if pieces == 1 else 96.50 * pieces
                elif 3477.60 <= salaire_ref < 4250.39:
                    valeur_logement = 141.90 if pieces == 1 else 122.30 * pieces
                elif 4250.40 <= salaire_ref < 5023.19:
                    valeur_logement = 167.40 if pieces == 1 else 147.70 * pieces
                elif 5023.20 <= salaire_ref < 5795.99:
                    valeur_logement = 193.30 if pieces == 1 else 178.10 * pieces
                elif salaire_ref >= 5796:
                    valeur_logement = 218.80 if pieces == 1 else 205.90 * pieces
            elif mode_calcul == "reelle":
                valeur_logement = params.get("valeur_reelle", 1000)

            avantages_totaux[avantage] = valeur_logement
            total_avantages += valeur_logement

        elif type_avantage == "voiture":
            valeur_voiture = 0
            mode_calcul = params.get("mode", "forfaitaire")
            type_vehicule = params.get("type_vehicule", "thermique")
            carburant_inclus = params.get("carburant_inclus", False)
            carburant_professionnel_et_personnel = params.get("carburant_professionnel_et_personnel", False)
            achat_ou_location = params.get("achat_ou_location", "achat")

            if mode_calcul == "forfaitaire":
                if achat_ou_location == "achat":
                    prix_achat_ttc = params.get("prix_achat_ttc", 25000)
                    anciennete = params.get("anciennete", "moins_5_ans")

                    if anciennete == "moins_5_ans":
                        taux_base = 0.09 if not carburant_inclus else 0.12
                    else:
                        taux_base = 0.06 if not carburant_inclus else 0.09

                    valeur_voiture = prix_achat_ttc * taux_base

                elif achat_ou_location == "location":
                    cout_annuel_ttc = params.get("cout_annuel_ttc", 5000)
                    if not carburant_inclus:
                        valeur_voiture = 0.30 * cout_annuel_ttc
                    else:
                        if not carburant_professionnel_et_personnel:
                            frais_reels_carburant = params.get("frais_reels_carburant", 2000)
                            valeur_voiture = 0.30 * cout_annuel_ttc + frais_reels_carburant
                        else:
                            valeur_voiture = 0.40 * cout_annuel_ttc

            elif mode_calcul == "reelle":
                amortissement = params.get("amortissement", 5000)
                assurance = params.get("assurance", 1000)
                entretien = params.get("entretien", 1000)
                frais_reels_carburant = params.get("frais_reels_carburant", 2000)
                valeur_voiture = amortissement + assurance + entretien + frais_reels_carburant

            if type_vehicule == "electrique":
                abattement = 0.50 * valeur_voiture
                valeur_voiture -= abattement
                valeur_voiture = max(0, valeur_voiture)
                valeur_voiture = min(valeur_voiture, 1800)
            
            valeur_voiture = valeur_voiture/12
            avantages_totaux[avantage] = valeur_voiture
            total_avantages += valeur_voiture

        elif type_avantage == "autres":
            valeur_autre = params.get("valeur_reelle", 0) * 0.1
            avantages_totaux[avantage] = valeur_autre
            total_avantages += valeur_autre

    # Résumé des avantages
    result = {
        "Détail des avantages": {k: round(v, 2) for k, v in avantages_totaux.items()},
        "Total des avantages": round(total_avantages, 2),
    }

    return result



def calcul_ijss(histo_salaire_annuel, absences, subrogation=True):
    """
    Calcule les IJSS brutes et nettes et simule la présentation sur un bulletin de paie
    en prenant en compte les absences et les délais de carence.
    """
    from datetime import datetime
    
    # Délais de carence selon le motif de l'absence
    delais_carence = {
        "maladie": 3,
        "accident travail": 0,
        "maternité": 0
    }
    
    # Calcul du salaire journalier de base
    salaire_brut_total = sum([histo_salaire_annuel[-3],histo_salaire_annuel[-2],histo_salaire_annuel[-1]])
    salaire_journalier_base = salaire_brut_total / 91.25  # 3 mois = 91.25 jours en moyenne
    
    # Calcul des jours d'absence et jours indemnisés
    jours_absences = {motif: 0 for motif in delais_carence}
    for date, motif in absences.items():
        if motif in jours_absences:
            jours_absences[motif] += 1
    
    ijss_total_brutes = 0
    ijss_total_nettes = 0
    ijss_maladie_brutes = 0
    ijss_maladie_nettes = 0
    ijss_maternite_brutes = 0
    ijss_maternite_nettes = 0
    ijss_accident_brutes = 0
    ijss_accident_nettes = 0
    
    for  motif,jours in jours_absences.items():
        if motif== "maladie":
            jours_indemnises = max(0, jours - delais_carence.get(motif, 0))
            ijss_mal_brutes = jours_indemnises * min(salaire_journalier_base * 0.5, 53.31)
            ijss_mal_nettes = ijss_mal_brutes * (1 - 6.7 / 100)
            ijss_maladie_brutes += ijss_mal_brutes
            ijss_maladie_nettes += ijss_mal_nettes
            
            ijss_total_brutes += ijss_mal_brutes
            ijss_total_nettes += ijss_mal_nettes
        
        if motif== "maternité":
            jours_indemnises = max(0, jours - delais_carence.get(motif, 0))
            ijss_mat_brutes = jours_indemnises * min(salaire_journalier_base, 100.36)
            ijss_mat_nettes = ijss_mat_brutes * (1 - 6.7 / 100)
            ijss_maternite_brutes += ijss_mat_brutes
            ijss_maternite_nettes += ijss_mat_nettes
            
            ijss_total_brutes += ijss_mat_brutes
            ijss_total_nettes += ijss_mat_nettes

        if motif== "accident travail":
            jours_indemnises = max(0, jours - delais_carence.get(motif, 0))
            ijss_acc_brutes = jours_indemnises * min(salaire_journalier_base*0.6, 232.03)
            ijss_acc_nettes = ijss_acc_brutes * (1 - 6.7 / 100)
            ijss_accident_brutes += ijss_acc_brutes
            ijss_accident_nettes += ijss_acc_nettes
            
            ijss_total_brutes += ijss_acc_brutes
            ijss_total_nettes += ijss_acc_nettes
    return ijss_total_brutes, ijss_total_nettes

def regrouper_absences(absences): #Plugger absences_motifs dedans
    if len(absences) == 0:  # Vérifie si le dictionnaire est vide
        return []
    sorted_dates = sorted(absences.keys(), key=lambda x: datetime.strptime(x, "%Y-%m-%d"))
    result = []
    
    debut = sorted_dates[0]
    motif = absences[debut]
    fin = debut

    for i in range(1, len(sorted_dates)):
        date = sorted_dates[i]
        if absences[date] == motif and (datetime.strptime(date, "%Y-%m-%d") - datetime.strptime(fin, "%Y-%m-%d")).days == 1:
            fin = date
        else:
            result.append([motif, debut, fin])
            debut = date
            motif = absences[date]
            fin = date
    
    result.append([motif, debut, fin])  # Ajouter le dernier bloc d'absence
    return result

def reconstruire_dictionnaire(une_liste_absence):
    label, start_date, end_date = une_liste_absence[0], une_liste_absence[1], une_liste_absence[2]
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")
    
    date_dict = {}
    current_date = start_date
    while current_date <= end_date:
        date_dict[current_date.strftime("%Y-%m-%d")] = label
        current_date += timedelta(days=1)
    
    return date_dict

def salaire_de_base(salarie: Salarie):
    base = salarie.temps_travail
    taux = salarie.salaire_de_base/salarie.temps_travail
    total = base*taux
    return base, taux, total

def absence_rtt(salarie: Salarie, timesheet):
    timesheet_filtered = filter_ts(timesheet)
    nb_jours_abs_rtt = timesheet_filtered["absence rémunérée RTT"].sum()
    base = nb_jours_abs_rtt * 7
    taux = salarie.salaire_de_base/salarie.temps_travail
    total = base*taux
    return base, taux, total

def absence_cp(salarie: Salarie, timesheet):
    timesheet_filtered = filter_ts(timesheet)
    nb_jours_abs_cp = timesheet_filtered["absence rémunérée congé payé"].sum()
    base = nb_jours_abs_cp * 7
    taux = salarie.salaire_de_base/salarie.temps_travail
    total = base*taux
    return base, taux, total

def absence_jfr(salarie: Salarie, timesheet):
    timesheet_filtered = filter_ts(timesheet)
    nb_jours_abs_jfr = timesheet_filtered["absence rémunérée jour férié"].sum()
    base = nb_jours_abs_jfr * 7
    taux = salarie.salaire_de_base/salarie.temps_travail
    total = base*taux
    return base, taux, total

def absence_jfnr(salarie: Salarie, timesheet):
    timesheet_filtered = filter_ts(timesheet)
    nb_jours_abs_jfnr = timesheet_filtered["absence non rémunérée jour férié"].sum()
    base = nb_jours_abs_jfnr * 7
    taux = salarie.salaire_de_base/salarie.temps_travail
    total = base*taux
    return base, taux, total

def absence_maladie(salarie: Salarie, timesheet):
    timesheet_filtered = filter_ts(timesheet)
    nb_jours_abs_jfnr = timesheet_filtered["absence maladie"].sum()
    base = nb_jours_abs_jfnr * 7
    taux = salarie.salaire_de_base/salarie.temps_travail
    total = base*taux
    return base, taux, total
    
    


SMIC=1801.80
PMSS = 3925.00  # PMSS (Plafond Mensuel de la Sécurité Sociale)
SMIC = 1801.80
PLAFOND_SEUIL_MALADIE = 2.5*SMIC
PMSS_COMPLET = 3925.00
PLAFOND_FAMILLE = 3.5*SMIC
PLAFOND_CHOMAGE =4*PMSS
PLAFOND_APEC =4*PMSS



def calcul_cotisations(salarie):
    """
    Calcule les cotisations sociales en tenant compte de :
    - Cotisations salariales (retenues sur le salaire)
    - Cotisations patronales (charges de l'employeur)
    - Effectif de l'entreprise (impact sur FNAL, Versement Mobilités, etc.)
    """


    salaire_brut = salarie.salaire_brut
    salaire_plafonne = min(salaire_brut, PMSS)
    salaire_plafonne_T2 = min(salaire_brut,8*PMSS_COMPLET)
    effectif = salarie.entreprise.effectif
    taux_AT = salarie.entreprise.taux_AT
    salaire_plafonne_famille= min(salaire_brut, 3.5*SMIC)
    salaire_plafonne_chomage = min(salaire_brut, 4*PMSS)
    salaire_plafonne_apec = min(salaire_brut, 4*PMSS)
    taux_versement_mobilite= salarie.entreprise.taux_versement_mobilite
    part_patronale_prevoyance = salarie.entreprise. forfait_complementaire_sante
    part_patronale_mutuelle = salarie.entreprise.forfait_mutuelle
    assiette_csg= (salaire_brut + part_patronale_prevoyance + part_patronale_mutuelle)*0.9825

    cotisations = {
        "Salarial": {},
        "Patronal": {}
    }


    # ✅ Sécurité Sociale
    if salaire_brut<PLAFOND_SEUIL_MALADIE:
        cotisations["Patronal"]["Maladie-Maternité"] = salaire_brut * 0.07  # 7% 
    else:
        cotisations["Patronal"]["Maladie-Maternité"] = salaire_brut * 0.07
        cotisations["Patronal"]["Maladie-Maternité Complément"] = salaire_brut * 0.06  # 6%

    cotisations["Salarial"]["Vieillesse Déplafonnée"] = salaire_brut * 0.004  # 0.4%
    cotisations["Patronal"]["Vieillesse Déplafonnée"] = salaire_brut * 0.0202  # 2%

    cotisations["Salarial"]["Vieillesse Plafonnée"] = salaire_plafonne * 0.069  # 6.9%
    cotisations["Patronal"]["Vieillesse Plafonnée"] = salaire_plafonne * 0.0855  # 8.55%

    # ✅ Accident du travail
    cotisations["Patronal"]["Accident du travail"] = salaire_brut * taux_AT  

    # ✅ Retraite complémentaire Agirc-Arrco (Tranche 1& 2)
    cotisations["Salarial"]["Retraite Complémentaire (Tr1)"] = salaire_plafonne * 0.0315  # 3.15%
    cotisations["Patronal"]["Retraite Complémentaire (Tr1)"] = salaire_plafonne * 0.0472  # 4.72%
    
    if PMSS< salaire_brut:
        cotisations["Salarial"]["Retraite Complémentaire (Tr2)"] =(salaire_plafonne_T2-PMSS) * 0.0864
        cotisations["Patronal"]["Retraite Complémentaire (Tr2)"] =(salaire_plafonne_T2-PMSS) * 0.1295

    # ✅ CET
    if PMSS< salaire_brut:
        cotisations["Salarial"]["CET"] = salaire_plafonne_T2*0.0014
        cotisations["Patronal"]["CET"] = salaire_plafonne_T2*0.0021

    
    # ✅ CEG(TU1)
    
    cotisations["Salarial"]["CEG_T1"] = salaire_plafonne *0.0086
    cotisations["Patronal"]["CEG_T1"] = salaire_plafonne* 0.0129
    
    # ✅ CEG(TU2)
    if PMSS< salaire_brut:
        cotisations["Salarial"]["CEG_T2"] = (salaire_plafonne_T2-PMSS) *0.0108
        cotisations["Patronal"]["CEG_T2"] = (salaire_plafonne_T2-PMSS)*0.0162
    

    # ✅ Famille(TU2)
    if salaire_brut<PLAFOND_FAMILLE:
        cotisations["Patronal"]["FAMILLE"] = salaire_plafonne_famille*0.0345
    else:
        cotisations["Patronal"]["FAMILLE"] = salaire_plafonne_famille*0.525


    # ✅ Assurance chômage (hors fonction publique)
    cotisations["Patronal"]["Assurance Chômage"] = salaire_plafonne_chomage * 0.0405 # 4,05%
    cotisations["Patronal"]["AGS"] = salaire_plafonne_chomage * 0.0025 # 0.25%


    # ✅ APEC (Cadres uniquement)
    if salarie.statut.lower() == "cadre":
        cotisations["Salarial"]["APEC"] = salaire_plafonne_apec * 0.0024  # 0.24%
        cotisations["Patronal"]["APEC"] = salaire_plafonne_apec * 0.0036  # 0.36%
        cotisations["Patronal"]["Prévoyance"] = salaire_plafonne * 0.015  # 1.5%


    # ✅ FNAL (varie selon effectif)
    if effectif < 50:
        cotisations["Patronal"]["FNAL"] = salaire_plafonne * 0.001  # 0.1% (<50 salariés)
    else:
        cotisations["Patronal"]["FNAL"] = salaire_plafonne  * 0.005  # 0.5% (≥50 salariés)

    # ✅ Versement Mobilités (varie selon effectif)
    if effectif >= 11:
        cotisations["Patronal"]["Versement Transport"] = salaire_brut * taux_versement_mobilite 

    # ✅ Cotisations solidarité autonomie
    cotisations["Patronal"]["Solidarité autonomie"] = salaire_brut * 0.003
    

    # ✅ Financement Dialogue social
    cotisations["Patronal"]["Dialogue social"] = salaire_brut *0.00016 

    # ✅ Contribution à la formation professionnelle (varie selon effectif)
    if effectif >= 11:
        cotisations["Patronal"]["Formation professionnelle"] = salaire_brut * 0.01  
    else:
        cotisations["Patronal"]["Formation professionnelle"] = salaire_brut*0.0055 
    
    # ✅ Taxe d'apprentissage 
        cotisations["Patronal"]["Taxe d'Apprentissage"] = salaire_brut*0.0059
        cotisations["Patronal"]["Taxe d'Apprentissage libératoire"] = salaire_brut*0.0009

    # ✅ Participation à l'effort construction (entreprises ≥50 salariés)
    if effectif >= 50:
        cotisations["Patronal"]["Effort Construction"] = salaire_brut * 0.0045  # 0.45%
    

    # ✅ CSG
    cotisations["Salarial"]["CSG Deductible"] = assiette_csg * (0.068)
    cotisations["Salarial"]["CSG non Deductible"] = assiette_csg * 0.029
    cotisations["Salarial"]["CRDS"] = assiette_csg * 0.005

    #✅ forfait social 
    if effectif >=11:
        cotisations["Patronal"]["Forfait social 8%"] = (part_patronale_mutuelle+part_patronale_prevoyance) * 0.08


    return cotisations



smics = [1766.92,1766.92,1766.92,1766.92,1766.92,1766.92,1766.92,1766.92,1766.92,1801.80,1801.80,1801.80]



def calculer_reduction_fillon(salarie, douze_derniers_smics):
    # Calcul de T
    if salarie.entreprise.effectif < 50:
        T = 0.3194 - 0.0046
    else:
        T = 0.3234 - 0.0046
    
    T += min(salarie.entreprise.taux_AT, 0.0046)
    
    # Calcul de C
    C = (1.6 * sum(douze_derniers_smics) / sum(salarie.douze_derniers_salaires) - 1) * (T / 0.6)
    
    # Calcul de la réduction Fillon
    if salarie.salaire_brut> 1.6*SMIC:
        return 0,0
    
    else:
        reduction = C * salarie.salaire_brut
        
        # Répartition de la réduction Fillon
        taux_retraite = 0.0601
        taux_urssaf = T - taux_retraite
        
        reduction_urssaf = reduction * (taux_urssaf / T)
        reduction_retraite = reduction * (taux_retraite / T)
        
        return reduction_urssaf, reduction_retraite



def reduction_tepa(timesheet,salarie):
    hs_25, hs_50 = calcul_hs(timesheet)
    hs=hs_25+hs_50
    effectif=salarie.entreprise.effectif
    if effectif < 20:
        reduction_tepa =  hs* 1.50  # 1,50€ par heure
    elif effectif < 250:
        reduction_tepa = hs * 0.50  # 0,50€ par heure
    else:
        reduction_tepa = 0.0  # Pas de réduction si +250 salariés
    return reduction_tepa




def exoneration_hs(timesheet, salarie):
    hs_25, hs_50 = calcul_hs(timesheet)
    hs=hs_25+hs_50
    rem_hs = (salarie.salaire_de_base/salarie.temps_travail)*(1.25*hs_25+1.5*hs_50)
    exoneration = rem_hs*0.1131
    return exoneration


def retirer_tickets_resto(salarie, avantages, timesheet):
    dic_avantages = calcul_avantages_en_nature(salarie, avantages, timesheet)
    if not dic_avantages or 'Détail des avantages' not in dic_avantages:
        return 0
        
    avantages_detail = dic_avantages['Détail des avantages']
    if 'nourriture' not in avantages_detail:
        return 0
    montant_a_deduire_tickets_resto = dic_avantages['Détail des avantages']['nourriture']
    return montant_a_deduire_tickets_resto

def navigo(salarie):
    navigo= salarie.entreprise.taux_transport*salarie.entreprise.prix_transport
    return navigo



def calcul_taxe_progressive(revenu: float) -> float:
    """
    Calcule le montant total des taxes en appliquant le barème progressif.

    :param revenu: Le revenu brut soumis à taxation.
    :return: Montant total de la taxe due.
    """

    tranches = [
        (1591, 0.0),
        (1653, 0.5),
        (1759, 1.3),
        (1877, 2.1),
        (2006, 2.9),
        (2113, 3.5),
        (2253, 4.1),
        (2666, 5.3),
        (3052, 7.5),
        (3476, 9.9),
        (3913, 11.9),
        (4566, 13.8),
        (5475, 15.8),
        (6851, 17.9),
        (8557, 20.0),
        (11877, 24.0),
        (16086, 28.0),
        (25251, 33.0),
        (54088, 38.0),
        (float('inf'), 43.0),
    ]

    taxe_totale = 0.0

    for seuil, taux in tranches:
        if revenu <= seuil:
            taxe_totale = revenu * (taux / 100)
            return round(taxe_totale, 2)

    return round(taxe_totale, 2)


def net_imposable(salarie):
    salaire_brut = salarie.salaire_brut
    cotisations = calcul_cotisations(salarie)
    somme_cotis = sum(cotisations['Salarial'].values())
    a_reintegrer = cotisations['Salarial'].get('CSG non Deductible',0) + cotisations["Patronal"].get("Prévoyance",0) + cotisations["Salarial"].get("CRDS", 0)
    net_imposable = salaire_brut - somme_cotis + a_reintegrer
    return net_imposable



def montant_net_social(salarie, cotisations,timesheet,absences={}):
    s= salarie.salaire_brut - sum(cotisations['Salarial'].values()) - calcul_ijss(salarie.douze_derniers_salaires,absences)[1] + exoneration_hs(timesheet,salarie)
    return s

def net_a_payer(salarie):
    base= net_imposable(salarie)
    pas= calcul_taxe_progressive(base)
    return base-pas



def cout_entreprise(salarie, cotisations, timesheet):
    s= salarie.salaire_brut + sum(cotisations['Salarial'].values()) + navigo(salarie) + salarie.entreprise.titre_restaurant
    return s
    



import pandas as pd

def fiche_de_paie(salarie, avantages, primes,timesheet, timesheet_prec, absence_motifs=None):
    # Initialisation sécurisée
    if absence_motifs is None:
        absence_motifs = {}
    
    
    timesheet_filtered = filter_ts(timesheet)
    salaire_mensuel_3_mois = [salarie.douze_derniers_salaires[-3], salarie.douze_derniers_salaires[-2], salarie.douze_derniers_salaires[-1]]

    base_sdb,taux_sdb, total_sdb = salaire_de_base(salarie)
    base_rtt,taux_rtt, total_rtt =    absence_rtt(salarie,timesheet)
    base_cp,taux_cp, total_cp = absence_cp(salarie,timesheet)
    base_jfr,taux_jfr, total_jfr = absence_jfr(salarie,timesheet)
    base_jfnr,taux_jfnr, total_jfnr = absence_jfnr(salarie,timesheet)

    data = {"Catégorie": ["Salaire de base", "absence RTT", "indemnisation absence RTT", "absence congés payés", "indemnisation absence congés payés", "absence jour ferié", "indemnisation absence jour férié", "absence jour ferié non rémunéré"],
        "Base": [ base_sdb, -base_rtt, base_rtt, -base_cp, base_cp, -base_jfr, base_jfr, -base_jfnr],
        "Taux (%)": [taux_sdb, taux_rtt, taux_rtt, taux_cp, taux_cp, taux_jfr, taux_jfr, taux_jfnr],
        "Total (€)": [total_sdb, -total_rtt, total_rtt, -total_cp,total_cp,  -total_jfr, total_jfr, -total_jfnr],}
    
    df= pd.DataFrame(data)


    absences_rangees = regrouper_absences(absence_motifs)
    

    if salarie.entreprise.subrogation:
        for absence in absences_rangees: # Cas avec subrogation
            duree = (datetime.strptime(absence[2], "%Y-%m-%d") - datetime.strptime(absence[1], "%Y-%m-%d")).days + 1
            total_absence = duree*total_sdb/30.42
            df = df.reset_index(drop=True)
            new_row=pd.DataFrame({"Catégorie": f"Abs. {absence[0]} {duree} jours", "Base": duree*7, "Taux (%)": taux_sdb, "Total (€)": -total_absence},index=[0])
            df = pd.concat([df, new_row], ignore_index=True)

            ijss_brutes, ijss_nettes = calcul_ijss(salaire_mensuel_3_mois, reconstruire_dictionnaire(absence), salarie.entreprise.subrogation)
            if duree > 7: # Il y a donc maintien
                maintien = total_absence*0.9
                df = df.reset_index(drop=True)
                new_row=pd.DataFrame({"Catégorie": "Subrogation - maintien de salaire à 90%", "Base": maintien, "Taux (%)": 1, "Total (€)": maintien},index=[0])
                df = pd.concat([df, new_row], ignore_index=True)
                df = df.reset_index(drop=True)
                new_row=pd.DataFrame({"Catégorie": "IJSS brutes", "Base": ijss_brutes, "Taux (%)": 1, "Total (€)": ijss_brutes},index=[0])
                df = pd.concat([df, new_row], ignore_index=True)
    
            else:
                maintien = ijss_brutes
                df = df.reset_index(drop=True)
                new_row=pd.DataFrame({"Catégorie": "Subrogation - maintien de salaire à 90%", "Base": maintien, "Taux (%)": 1, "Total (€)": maintien},index=[0])
                df = pd.concat([df, new_row], ignore_index=True)
                df = df.reset_index(drop=True)
                new_row=pd.DataFrame({"Catégorie": "IJSS brutes", "Base": ijss_brutes, "Taux (%)": 1, "Total (€)": ijss_brutes},index=[0])
                df = pd.concat([df, new_row], ignore_index=True)
            

    else:
        for absence in absences_rangees: # Cas sans subrogation
            duree = (datetime.strptime(absence[2], "%Y-%m-%d") - datetime.strptime(absence[1], "%Y-%m-%d")).days + 1
            total_absence = duree*total_sdb/30.42
            df = df.reset_index(drop=True)
            new_row=pd.DataFrame({"Catégorie": f"Absence {absence[0]} - {duree} jours", "Base": duree*7, "Taux (%)": taux_sdb, "Total (€)": -total_absence},index=[0])
            df = pd.concat([df, new_row], ignore_index=True)
            
            if duree > 7: # Il y a donc maintien
                ijss_brutes, ijss_nettes = calcul_ijss(salaire_mensuel_3_mois, reconstruire_dictionnaire(absence), salarie.entreprise.subrogation)
                maintien = total_absence*0.9-ijss_brutes
                df = df.reset_index(drop=True)
                new_row=pd.DataFrame({"Catégorie": "Maintien de salaire à 90%", "Base": maintien, "Taux (%)": 1, "Total (€)": maintien},index=[0])
                df = pd.concat([df, new_row], ignore_index=True)
    

    toutes_primes = calcul_primes(salarie,primes,timesheet)
    for prime, valeur in toutes_primes["Détail des primes"].items():
        new_row = pd.DataFrame({
            "Catégorie": [f"{prime}"],
            "Base": [valeur],
            "Taux (%)": [1],
            "Total (€)": [valeur]
        })
        df = pd.concat([df, new_row], ignore_index=True)

    avantage_nature = calcul_avantages_en_nature(salarie,avantages,timesheet)
    for avantage, valeur in avantage_nature["Détail des avantages"].items():
        if avantage != "nourriture":
            new_row = pd.DataFrame({
                "Catégorie": [f"Avantage {avantage}"],
                "Base": [valeur],
                "Taux (%)": [1],
                "Total (€)": [valeur]
            })
            df = pd.concat([df, new_row], ignore_index=True)
    
    merged_ts = merge_overlapping_days(timesheet_prec, timesheet)
    hs25, hs50 = calcul_hs(merged_ts)
    if hs25 > 0:
        taux_hs25 = taux_sdb*1.25
        montant_hs25 = hs25*taux_hs25
        new_row=pd.DataFrame({"Catégorie": "Heures supplémentaires maj. 25%", "Base": hs25, "Taux (%)": taux_hs25, "Total (€)": montant_hs25},index=[0])
        df = pd.concat([df, new_row], ignore_index=True)

    if hs50 > 0:
        taux_hs50 = taux_sdb*1.50
        montant_hs50 = hs50*taux_hs50
        new_row=pd.DataFrame({"Catégorie": "Heures supplémentaires maj. 50%", "Base": hs50, "Taux (%)": taux_hs50, "Total (€)": montant_hs50},index=[0])
        df = pd.concat([df, new_row], ignore_index=True)
    
    new_row = pd.DataFrame({
        "Catégorie": "Salaire Brut",
        "Base": "" ,
        "Taux (%)":"" ,
        "Total (€)": df["Total (€)"].sum()
    },index=[0])
    
    df = pd.concat([df, pd.DataFrame(new_row)], ignore_index=True)
    salaire_brut_index = df[df["Catégorie"] == "Salaire Brut"].index[0]
    df_brut = df.iloc[:salaire_brut_index].copy()
    salarie.salaire_brut = df_brut["Total (€)"].sum()


    return df



def df_cotis(salarie,cotisations,df_salaire):
    df= df_salaire

    PMSS = 3925.00  # PMSS (Plafond Mensuel de la Sécurité Sociale)
    SMIC = 1801.80
    PLAFOND_SEUIL_MALADIE = 2.5*SMIC
    PMSS_COMPLET = 3925.00
    PLAFOND_FAMILLE = 3.5*SMIC
    PLAFOND_CHOMAGE =4*PMSS
    PLAFOND_APEC =4*PMSS
    
    salaire_brut = float(df_salaire.loc[df_salaire["Catégorie"] == "Salaire Brut", "Total (€)"].values[0])
    salaire_plafonne = min(salaire_brut, PMSS)
    salaire_plafonne_T2 = min(salaire_brut,8*PMSS_COMPLET)
    effectif = salarie.entreprise.effectif
    taux_AT = salarie.entreprise.taux_AT
    salaire_plafonne_famille= min(salaire_brut, 3.5*SMIC)
    salaire_plafonne_chomage = min(salaire_brut, 4*PMSS)
    salaire_plafonne_apec = min(salaire_brut, 4*PMSS)
    taux_versement_mobilite= salarie.entreprise.taux_versement_mobilite
    part_patronale_prevoyance = salarie.entreprise. forfait_complementaire_sante
    part_patronale_mutuelle = salarie.entreprise.forfait_mutuelle
    assiette_csg= (salaire_brut + part_patronale_prevoyance + part_patronale_mutuelle)*0.9825

    if salaire_brut< PLAFOND_SEUIL_MALADIE:
        new_row= {"Catégorie": "Maladie Maternité", "Base": "", "Taux (%)": "", "Total (€)": "","Part_Employeur":-salaire_brut*0.07}
        df = pd.concat([df, pd.DataFrame(new_row, index=[0])], ignore_index=True)
    else: 
        new_row= {"Catégorie": "Maladie Maternité", "Base": "", "Taux (%)": "", "Total (€)": "","Part_Employeur":-salaire_brut*0.07}
        df =  pd.concat([df, pd.DataFrame(new_row, index=[0])], ignore_index=True)
        new_row= {"Catégorie": "Maladie Maternité Complément", "Base": "", "Taux (%)": "", "Total (€)": "","Part_Employeur":-salaire_brut*0.06}
        df = pd.concat([df, pd.DataFrame(new_row, index=[0])], ignore_index=True)
    
    new_row= {"Catégorie": "Vieillesse Déplafonnée", "Base": salaire_brut, "Taux (%)": 0.4, "Total (€)": -salaire_brut*0.004,"Part_Employeur":-salaire_brut*0.0202}
    df = pd.concat([df, pd.DataFrame(new_row, index=[0])], ignore_index=True)
    new_row= {"Catégorie": "Vieillesse Plafonée", "Base": salaire_plafonne, "Taux (%)": 6.9, "Total (€)": -salaire_plafonne*0.069,"Part_Employeur":-salaire_brut*0.0855}
    df = pd.concat([df, pd.DataFrame(new_row, index=[0])], ignore_index=True)

    new_row= {"Catégorie": "Accident du travail", "Base": "", "Taux (%)": "", "Total (€)": "","Part_Employeur":-salaire_brut*taux_AT}
    df = pd.concat([df, pd.DataFrame(new_row, index=[0])], ignore_index=True)
    
    new_row= {"Catégorie": "Retraite Complémentaire", "Base": salaire_plafonne, "Taux (%)": 3.15, "Total (€)": -salaire_plafonne*0.0315,"Part_Employeur":-salaire_plafonne*0.0472}
    df = pd.concat([df, pd.DataFrame(new_row, index=[0])], ignore_index=True)

    if PMSS <salaire_brut:
        new_row= {"Catégorie": "Retraite Complémentaire T2", "Base": (salaire_plafonne_T2 - PMSS), "Taux (%)": 8.64, "Total (€)": -(salaire_plafonne_T2 - PMSS)*0.0864,"Part_Employeur":-(salaire_plafonne_T2 - PMSS)*0.1285}
        df = pd.concat([df, pd.DataFrame(new_row, index=[0])], ignore_index=True)
        new_row= {"Catégorie": "CET", "Base": salaire_plafonne_T2, "Taux (%)": 0.14, "Total (€)": -salaire_plafonne_T2*0.0014,"Part_Employeur":-salaire_plafonne_T2*0.0021}
        df = pd.concat([df, pd.DataFrame(new_row, index=[0])], ignore_index=True)

    
    new_row = {"Catégorie": "CEG T1", "Base": salaire_plafonne, "Taux (%)": 0.86, "Total (€)": -salaire_plafonne*0.0086,"Part_Employeur":-salaire_plafonne*0.0129}
    df = pd.concat([df, pd.DataFrame(new_row, index=[0])], ignore_index=True)

    if PMSS<salaire_brut:
        new_row = {"Catégorie": "CEG T2", "Base": (salaire_plafonne_T2 -PMSS), "Taux (%)": 1.08, "Total (€)": -(salaire_plafonne_T2 -PMSS)*0.0108,"Part_Employeur":-(salaire_plafonne_T2 -PMSS)*0.0162}
        df = pd.concat([df, pd.DataFrame(new_row, index=[0])], ignore_index=True)
    
    if salaire_brut<PLAFOND_FAMILLE:
        new_row= {"Catégorie": "Famille", "Base": "", "Taux (%)": "", "Total (€)": "","Part_Employeur":-salaire_plafonne_famille*0.0345}
        df = pd.concat([df, pd.DataFrame(new_row, index=[0])], ignore_index=True)
    else: 
        new_row= {"Catégorie": "Famille", "Base": "", "Taux (%)": "", "Total (€)": "","Part_Employeur":-salaire_plafonne_famille*0.0525}
        df = pd.concat([df, pd.DataFrame(new_row, index=[0])], ignore_index=True)
    
    new_row= {"Catégorie": "Chomage", "Base": "", "Taux (%)": "", "Total (€)": "","Part_Employeur":-salaire_plafonne_chomage*0.0405}
    df = pd.concat([df, pd.DataFrame(new_row, index=[0])], ignore_index=True)
    
    new_row= {"Catégorie": "AGS", "Base": "", "Taux (%)":"", "Total (€)":"","Part_Employeur":-salaire_plafonne_chomage*0.0025}
    df = pd.concat([df, pd.DataFrame(new_row, index=[0])], ignore_index=True)

    if salarie.statut.lower() == "cadre":
        new_row= {"Catégorie": "APEC", "Base": salaire_plafonne_apec, "Taux (%)":0.24, "Total (€)":-salaire_plafonne_apec*0.0024,"Part_Employeur":-salaire_plafonne_apec*0.0036}
        df = pd.concat([df, pd.DataFrame(new_row, index=[0])], ignore_index=True)
        new_row= {"Catégorie": "Prévoyance", "Base": "", "Taux (%)":"", "Total (€)":"","Part_Employeur":-salaire_plafonne*0.015}
        df = pd.concat([df, pd.DataFrame(new_row, index=[0])], ignore_index=True)

    if salarie.entreprise.effectif < 50:
        new_row= {"Catégorie": "FNAL", "Base": "", "Taux (%)":"", "Total (€)":"","Part_Employeur":-salaire_plafonne*0.001}
        df = pd.concat([df, pd.DataFrame(new_row, index=[0])], ignore_index=True)
    else:
        new_row= {"Catégorie": "FNAL", "Base": "", "Taux (%)":"", "Total (€)":"","Part_Employeur":-salaire_plafonne*0.005}
        df = pd.concat([df, pd.DataFrame(new_row, index=[0])], ignore_index=True)
    
    if salarie.entreprise.effectif >= 11:
        new_row= {"Catégorie": "Versement transport", "Base": "", "Taux (%)":"", "Total (€)":"","Part_Employeur":-salaire_brut*taux_versement_mobilite}
        df = pd.concat([df, pd.DataFrame(new_row, index=[0])], ignore_index=True)
    
    new_row= {"Catégorie": "Solidarité autonomie", "Base": "", "Taux (%)":"", "Total (€)":"","Part_Employeur":-salaire_brut*0.03}
    df = pd.concat([df, pd.DataFrame(new_row, index=[0])], ignore_index=True)

    new_row= {"Catégorie": "Dialogue social", "Base": "", "Taux (%)":"", "Total (€)":"","Part_Employeur":-salaire_brut*0.00016}
    df = pd.concat([df, pd.DataFrame(new_row, index=[0])], ignore_index=True)

    if salarie.entreprise.effectif >= 11:
        new_row= {"Catégorie": "Formation professionnelle", "Base": "", "Taux (%)":"", "Total (€)":"","Part_Employeur":-salaire_brut*0.01}
        df = pd.concat([df, pd.DataFrame(new_row, index=[0])], ignore_index=True)
    else:
        new_row= {"Catégorie": "Formation professionnelle", "Base": "", "Taux (%)":"", "Total (€)":"","Part_Employeur":-salaire_brut*0.0055}
        df = pd.concat([df, pd.DataFrame(new_row, index=[0])], ignore_index=True)

    new_row= {"Catégorie": "Taxe d'apprentissage", "Base": "", "Taux (%)":"", "Total (€)":"","Part_Employeur":-salaire_brut*0.0059}
    df = pd.concat([df, pd.DataFrame(new_row, index=[0])], ignore_index=True)

    new_row= {"Catégorie": "Taxe d'apprentissage libératoire", "Base": "", "Taux (%)":"", "Total (€)":"","Part_Employeur":-salaire_brut*0.0009}
    df = pd.concat([df, pd.DataFrame(new_row, index=[0])], ignore_index=True)

    if salarie.entreprise.effectif >= 11:
        new_row= {"Catégorie": "Effort construction", "Base": "", "Taux (%)":"", "Total (€)":"","Part_Employeur":-salaire_brut*0.0045}
        df = pd.concat([df, pd.DataFrame(new_row, index=[0])], ignore_index=True)
    else:
        new_row= {"Catégorie": "Effort construction", "Base": "", "Taux (%)":"", "Total (€)":"","Part_Employeur":-salaire_brut*0.0055}
        df = pd.concat([df, pd.DataFrame(new_row, index=[0])], ignore_index=True)
    
    new_row = {"Catégorie": "CSG déductible", "Base": assiette_csg, "Taux (%)": 6.8, "Total (€)": -assiette_csg*0.068,"Part_Employeur":""}
    df = pd.concat([df, pd.DataFrame(new_row, index=[0])], ignore_index=True)

    new_row = {"Catégorie": "CSG non déductible", "Base": assiette_csg, "Taux (%)": 2.9, "Total (€)": -assiette_csg*0.029,"Part_Employeur":""}
    df = pd.concat([df, pd.DataFrame(new_row, index=[0])], ignore_index=True)

    new_row = {"Catégorie": "CRDS", "Base": assiette_csg, "Taux (%)": 0.5, "Total (€)": -assiette_csg*0.005,"Part_Employeur":""}
    df = pd.concat([df, pd.DataFrame(new_row, index=[0])], ignore_index=True)

    if salarie.entreprise.effectif >= 11:
        new_row= {"Catégorie": "Forfait social 8%", "Base": "", "Taux (%)":"", "Total (€)":"","Part_Employeur":-(part_patronale_mutuelle+part_patronale_prevoyance)*0.08}
        df = pd.concat([df, pd.DataFrame(new_row, index=[0])], ignore_index=True)

    
    return df




def df_reductions(salarie, df_cotisations,timesheet,avantages,douze_derniers_smics=[1766.92,1766.92,1766.92,1766.92,1766.92,1766.92,1766.92,1766.92,1766.92,1801.80,1801.80,1801.80]):
    df = df_cotisations
    fillon_urssaf, fillon_retraite = calculer_reduction_fillon(salarie, douze_derniers_smics)
    new_row = {"Catégorie": "Réduction Fillon - URSSAF", "Base":"", "Taux (%)":"", "Total (€)":"","Part_Employeur":fillon_urssaf}
    df = pd.concat([df, pd.DataFrame(new_row, index=[0])], ignore_index=True)
    new_row = {"Catégorie": "Réduction Fillon - Retraite", "Base":"", "Taux (%)":"", "Total (€)":"","Part_Employeur":fillon_retraite}
    df = pd.concat([df, pd.DataFrame(new_row, index=[0])], ignore_index=True)

    tepa = reduction_tepa(timesheet, salarie)
    new_row = {"Catégorie": "Réduction TEPA", "Base":"", "Taux (%)":"", "Total (€)":"","Part_Employeur":tepa}
    df = pd.concat([df, pd.DataFrame(new_row, index=[0])], ignore_index=True)

    exo_hs = exoneration_hs(timesheet, salarie)
    new_row = {"Catégorie": "Exonération Heures supplémentaires", "Base":"", "Taux (%)":"", "Total (€)":"","Part_Employeur":exo_hs}
    df = pd.concat([df, pd.DataFrame(new_row, index=[0])], ignore_index=True)

# Sélectionner les lignes après "Salaire Brut"
    salaire_brut_index = df[df["Catégorie"] == "Salaire Brut"].index[0]
    df_de_passage = df.iloc[salaire_brut_index:].copy()

    # Convertir en numérique pour éviter les erreurs
    df_de_passage["Total (€)"] = pd.to_numeric(df_de_passage["Total (€)"], errors='coerce')

    # Calculer la somme de "Total (€)"
    somme_total = df_de_passage["Total (€)"].sum(skipna=True)

    # Ajouter la ligne "Salaire Net"
    new_row = pd.DataFrame({
        "Catégorie": ["Salaire Net Avant Impôts"],
        "Base": [""],
        "Taux (%)": [""],
        "Total (€)": [somme_total],
        "Part_Employeur": [""]
    })

    # Ajouter la ligne au DataFrame
    df = pd.concat([df, new_row], ignore_index=True)

    new_row = {"Catégorie": " Navigo", "Base":88.80, "Taux (%)": 50, "Total (€)": -44.40,"Part_Employeur":-44.40}
    df = pd.concat([df, pd.DataFrame(new_row, index=[0])], ignore_index=True)

    resto = retirer_tickets_resto(salarie, avantages, timesheet)
    new_row = {"Catégorie": " Participation tickets restaurant", "Base":"", "Taux (%)": "", "Total (€)": -resto,"Part_Employeur":-resto*salarie.entreprise.participation_titre_restaurant/(1-salarie.entreprise.participation_titre_restaurant)}
    df = pd.concat([df, pd.DataFrame(new_row, index=[0])], ignore_index=True)

    return df


def ajouter_sous_totaux(df_reduc, salarie, timesheet):
    df= df_reduc

    cotisations = calcul_cotisations(salarie)
    mns = montant_net_social(salarie, cotisations, timesheet)
    new_row = {"Catégorie": "Montant net social", "Base":"", "Taux (%)":"", "Total (€)":mns,"Part_Employeur":""}
    df = pd.concat([df, pd.DataFrame(new_row, index=[0])], ignore_index=True)

    net_impos = net_imposable(salarie)
    new_row = {"Catégorie": "Net imposable", "Base":"", "Taux (%)":"", "Total (€)":net_impos,"Part_Employeur":""}
    df = pd.concat([df, pd.DataFrame(new_row, index=[0])], ignore_index=True)


    pas = calcul_taxe_progressive(net_impos)
    new_row = {"Catégorie": "Prelevement à la source", "Base":"", "Taux (%)":"", "Total (€)":-pas,"Part_Employeur":""}
    df = pd.concat([df, pd.DataFrame(new_row, index=[0])], ignore_index=True)

    net_paye = net_a_payer(salarie)
    new_row = {"Catégorie": "Net à payer", "Base":"", "Taux (%)":"", "Total (€)":net_paye,"Part_Employeur":""}
    df = pd.concat([df, pd.DataFrame(new_row, index=[0])], ignore_index=True)

    new_row = {"Catégorie": "Sous-total Cotisations Patronales", "Base":"", "Taux (%)":"", "Total (€)":"","Part_Employeur":-pd.to_numeric(df['Part_Employeur'], errors='coerce').sum()}
    df = pd.concat([df, pd.DataFrame(new_row, index=[0])], ignore_index=True)


    df_formatted =df
    df_formatted["Base"] = pd.to_numeric(df_formatted["Base"], errors='coerce')
    df_formatted["Taux (%)"] = pd.to_numeric(df_formatted["Taux (%)"], errors='coerce')
    df_formatted["Total (€)"] = pd.to_numeric(df_formatted["Total (€)"], errors='coerce')
    df_formatted["Part_Employeur"] = pd.to_numeric(df_formatted["Part_Employeur"], errors='coerce')

    # Formatting to two decimal places and handling missing values
    df_formatted["Base"] = df_formatted["Base"].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "")
    df_formatted["Taux (%)"] = df_formatted["Taux (%)"].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "")
    df_formatted["Total (€)"] = df_formatted["Total (€)"].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "")
    df_formatted["Part_Employeur"] = df_formatted["Part_Employeur"].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "")


    return df_formatted




