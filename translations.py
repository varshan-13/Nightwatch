# Every piece of UI text, in English and French.
# Templates read these through the variable `t`, e.g. {{ t.tab_watch }}.

import re

T = {
    "en": {
        # Header
        "tab_watch": "Watch",
        "tab_alerts": "Alerts",
        "tab_validation": "Validation",
        "tab_method": "Method",
        "nav_label": "Main",
        "lang_label": "Language",
        "ops": "Coast guard ops",
        "prototype": "Prototype",

        # Footer
        "footer_credit": "Nightwatch · Tech Wave AI Hackathon · Data: Global Fishing Watch",
        "footer_notice": "Prototype, not an official enforcement tool.",
        "footer_ethics": "Ethics",
        "ethics_anchor": "ethics",

        # Page titles (browser tab) and headlines
        "title_landing": "Nightwatch landing page",
        "title_watch": "Nightwatch dashboard",
        "title_alert": "Nightwatch alert detail",
        "title_validation": "Nightwatch validation",
        "h1_watch": "Morning watch",
        "h1_validation": "Does it work?",

        # Landing page
        "how_anchor": "how",
        "l_nav_map": "Live map",
        "l_nav_how": "How it decides",
        "l_nav_works": "Does it work",
        "l_nav_limits": "Limits",
        "l_eyebrow": "Mauritius Exclusive Economic Zone · 2.3M km²",
        "l_h1": "See the ships that go dark.",
        "l_lead": "Nightwatch combines satellite radar with ship tracking signals, ranks the vessels that look suspicious, and says why, in plain words, so patrols go where they matter.",
        "l_search_label": "Search a vessel, MMSI or area",
        "l_search_placeholder": "Search a vessel name, MMSI or area...",
        "l_scan": "Scan →",
        "l_sample_link": "Open a sample alert →",
        "l_person_decides": "A person always decides.",
        "l_radar_label": "Radar scope centred on Mauritius, with vessel contacts and one flagged contact",
        "l_radar_tag": "NO AIS · 87",
        "l_point_1": "Radar and AIS, side by side",
        "l_point_2": "Every alert explains itself",
        "l_point_3": "Officers confirm or dismiss",

        "l_ex_tag": "[ 01 / Example alert ]",
        "l_ex_h2": "A risk score is useless without the reason.",
        "l_ex_lead": "Each alert lists the three behaviours that pushed its score up, and what to do next.",
        "l_sample_data": "Sample data",
        "l_ex_vessel": "Vessel 014",
        "l_ex_meta": "Longliner · last seen 6 h ago",
        "l_ex_id": "Alert #0014",
        "l_ex_r1_label": "Went dark near the border",
        "l_ex_r1_text": "AIS switched off for 31 hours, 12 km inside the EEZ edge.",
        "l_ex_r2_label": "Met a carrier at sea",
        "l_ex_r2_text": "Ran alongside a refrigerated cargo ship for 3 hours after reappearing.",
        "l_ex_r3_label": "Long time away from port",
        "l_ex_r3_text": "No port visit in 40 days, longer than most longliners in this area.",
        "l_ex_risk": "Risk 82 / 100",
        "l_ex_action": "Send a patrol",
        "l_ex_open": "Open alert →",

        "l_how_tag": "[ 02 / How it decides ]",
        "l_how_h2a": "The model ranks the ocean.",
        "l_how_h2b": "An officer makes the call.",
        "l_step_1_title": "Detect",
        "l_step_1_text": "Satellite radar spots every hull. Radar dots with no matching AIS signal become dark-vessel contacts.",
        "l_step_2_title": "Profile",
        "l_step_2_text": "Tracking gaps, meetings with carriers, loitering and port visits are added up into one profile per vessel.",
        "l_step_3_title": "Score",
        "l_step_3_text": "An anomaly model learns what normal looks like here and scores each vessel 0 to 100, with its top three reasons.",
        "l_step_4_title": "Decide",
        "l_step_4_text": "Officers confirm or dismiss each alert. Their feedback is logged and used to check the model.",

        "l_works_tag": "[ 03 / Does it work ]",
        "l_works_h2": "How we’ll check the ranking",
        "l_works_lead": "We plan to compare the highest-ranked vessels with the Indian Ocean Tuna Commission’s illegal fishing list and officer feedback. This version uses sample data; real-data validation has not run yet.",
        "l_works_cta": "See the validation",
        "l_stat_1_value": "Not measured yet",
        "l_stat_1_text": "Planned check: IOTC list matches among the top 20 alerts",
        "l_stat_2_value": "Not measured yet",
        "l_stat_2_text": "Planned measure: share of reviewed alerts dismissed as false alarms",

        "l_limits_tag": "[ 04 / Limits we take seriously ]",
        "l_limits_h2": "A flag is a clue, not a verdict.",
        "l_limit_1_title": "Innocent gaps",
        "l_limit_1_text": "Ships switch off AIS to avoid pirates, and signals drop out far from land. A gap alone never makes a high score.",
        "l_limit_2_title": "No flag profiling",
        "l_limit_2_text": "A vessel's flag country is never used to raise its score. Behaviour is.",
        "l_limit_3_title": "Prototype",
        "l_limit_3_text": "Built for the Tech Wave AI Hackathon. Not an official enforcement tool. Vessel data from Global Fishing Watch.",

        "l_cta_h2": "Two million km². A handful of patrols.",
        "l_cta_lead": "Send them where the evidence points.",
        "l_cta_how": "How it works",
        # Watch page
        "w_tag": "[ Last 72 hours · Sample data ]",
        "w_search_short": "Vessel, MMSI or area...",
        "w_scan": "Scan",
        "c_alerts": "Alerts",
        "c_high": "High risk",
        "c_dark": "Dark vessels",
        "c_awaiting": "Awaiting review",
        "w_map_tag": "[ Mauritius EEZ ]",
        "w_map_label": "Map of the Mauritius EEZ with one dot per alert shown in the table",
        "w_map_credit": "Vessel data: Global Fishing Watch.",
        "no_ais": "No AIS",
        "f_tag": "[ Filters ]",
        "f_min_risk": "Minimum risk",
        "f_dark_only": "Dark vessels only",
        "f_apply": "Apply",
        "f_note": "Scores rank vessels by unusual behaviour. They are not proof of illegal fishing.",
        "r_tag": "[ Ranked alerts ]",
        "r_sorted": "Sorted by risk, highest first",
        "th_vessel": "Vessel",
        "th_reason": "Top reason",
        "th_risk": "Risk",
        "th_action": "Action",
        "open": "Open",
        "open_arrow": "Open →",
        "radar_contact": "Radar contact · no AIS",
        "risk": "Risk",
        "w_empty": "No alerts match these filters.",

        # Computed values
        "level_high": "High",
        "level_med": "Medium",
        "level_low": "Low",
        "send_patrol": "Send patrol",
        "keep_watching": "Keep watching",
        "no_action": "No action",
        "gear_Longliner": "Longliner",
        "gear_Purse seiner": "Purse seiner",
        "gear_Carrier": "Carrier",
        "gear_Unknown": "Unknown",
    },
    "fr": {
        # Header
        "tab_watch": "Surveillance",
        "tab_alerts": "Alertes",
        "tab_validation": "Validation",
        "tab_method": "Méthode",
        "nav_label": "Principal",
        "lang_label": "Langue",
        "ops": "Opérations garde-côtes",
        "prototype": "Prototype",

        # Footer
        "footer_credit": "Nightwatch · Tech Wave AI Hackathon · Données : Global Fishing Watch",
        "footer_notice": "Prototype, ce n'est pas un outil officiel de contrôle.",
        "footer_ethics": "Éthique",
        "ethics_anchor": "ethique",

        # Page titles (browser tab) and headlines
        "title_landing": "Nightwatch, page d'accueil",
        "title_watch": "Nightwatch, tableau de bord",
        "title_alert": "Nightwatch, détail d'alerte",
        "title_validation": "Nightwatch, validation",
        "h1_watch": "Veille du matin",
        "h1_validation": "Ça marche ?",

        # Landing page
        "how_anchor": "comment",
        "l_nav_map": "Carte en direct",
        "l_nav_how": "Comment ça décide",
        "l_nav_works": "Ça marche ?",
        "l_nav_limits": "Limites",
        "l_eyebrow": "Zone économique exclusive de Maurice · 2,3 M km²",
        "l_h1": "Repérez les navires qui s'éteignent.",
        "l_lead": "Nightwatch croise l'imagerie radar satellite avec les signaux de suivi des navires, classe ceux au comportement suspect et explique pourquoi, en mots simples, pour envoyer les patrouilles là où il le faut.",
        "l_search_label": "Rechercher un navire, un MMSI ou une zone",
        "l_search_placeholder": "Rechercher un navire, un MMSI ou une zone...",
        "l_scan": "Analyser →",
        "l_sample_link": "Voir un exemple d'alerte →",
        "l_person_decides": "Une personne décide toujours.",
        "l_radar_label": "Écran radar centré sur Maurice, avec des contacts de navires et un contact signalé",
        "l_radar_tag": "SANS AIS · 87",
        "l_point_1": "Radar et AIS, côte à côte",
        "l_point_2": "Chaque alerte s'explique",
        "l_point_3": "Les agents confirment ou rejettent",

        "l_ex_tag": "[ 01 / Exemple d'alerte ]",
        "l_ex_h2": "Un score de risque ne sert à rien sans la raison.",
        "l_ex_lead": "Chaque alerte liste les trois comportements qui ont fait monter son score, et la suite à donner.",
        "l_sample_data": "Données d'exemple",
        "l_ex_vessel": "Navire 014",
        "l_ex_meta": "Palangrier · vu il y a 6 h",
        "l_ex_id": "Alerte #0014",
        "l_ex_r1_label": "Signal coupé près de la limite",
        "l_ex_r1_text": "AIS coupé pendant 31 heures, à 12 km de la limite de la ZEE.",
        "l_ex_r2_label": "Rencontre avec un transporteur",
        "l_ex_r2_text": "Côte à côte avec un cargo frigorifique pendant 3 heures après sa réapparition.",
        "l_ex_r3_label": "Longtemps loin du port",
        "l_ex_r3_text": "Aucune escale depuis 40 jours, plus que la plupart des palangriers de la zone.",
        "l_ex_risk": "Risque 82 / 100",
        "l_ex_action": "Envoyer une patrouille",
        "l_ex_open": "Ouvrir l'alerte →",

        "l_how_tag": "[ 02 / Comment ça décide ]",
        "l_how_h2a": "Le modèle classe l'océan.",
        "l_how_h2b": "Un agent prend la décision.",
        "l_step_1_title": "Détecter",
        "l_step_1_text": "Le radar satellite repère chaque coque. Un point radar sans signal AIS correspondant devient un contact « navire fantôme ».",
        "l_step_2_title": "Profiler",
        "l_step_2_text": "Coupures de signal, rencontres avec des transporteurs, errance et escales sont réunies dans un profil par navire.",
        "l_step_3_title": "Noter",
        "l_step_3_text": "Un modèle de détection d'anomalies apprend ce qui est normal ici et note chaque navire de 0 à 100, avec ses trois raisons principales.",
        "l_step_4_title": "Décider",
        "l_step_4_text": "Les agents confirment ou rejettent chaque alerte. Leurs retours sont enregistrés et servent à vérifier le modèle.",

        "l_works_tag": "[ 03 / Ça marche ? ]",
        "l_works_h2": "Comment nous vérifierons le classement",
        "l_works_lead": "Nous prévoyons de comparer les navires les mieux classés à la liste de pêche illicite de la CTOI et aux retours des officiers. Cette version utilise des données fictives ; la validation sur données réelles n’a pas encore été réalisée.",
        "l_works_cta": "Voir la validation",
        "l_stat_1_value": "Pas encore mesuré",
        "l_stat_1_text": "Vérification prévue : correspondances CTOI parmi les 20 premières alertes",
        "l_stat_2_value": "Pas encore mesuré",
        "l_stat_2_text": "Mesure prévue : part des alertes examinées classées comme fausses alertes",

        "l_limits_tag": "[ 04 / Les limites que nous prenons au sérieux ]",
        "l_limits_h2": "Une alerte est un indice, pas un verdict.",
        "l_limit_1_title": "Coupures innocentes",
        "l_limit_1_text": "Des navires coupent l'AIS pour éviter les pirates, et le signal se perd loin des côtes. Une coupure seule ne donne jamais un score élevé.",
        "l_limit_2_title": "Aucun profilage par pavillon",
        "l_limit_2_text": "Le pays du pavillon n'augmente jamais le score. Seul le comportement compte.",
        "l_limit_3_title": "Prototype",
        "l_limit_3_text": "Conçu pour le Tech Wave AI Hackathon. Ce n'est pas un outil officiel de contrôle. Données navires : Global Fishing Watch.",

        "l_cta_h2": "Deux millions de km². Une poignée de patrouilles.",
        "l_cta_lead": "Envoyez-les là où les preuves mènent.",
        "l_cta_how": "Comment ça marche",
        # Watch page
        "w_tag": "[ 72 dernières heures · Données d'exemple ]",
        "w_search_short": "Navire, MMSI ou zone...",
        "w_scan": "Analyser",
        "c_alerts": "Alertes",
        "c_high": "Risque élevé",
        "c_dark": "Navires fantômes",
        "c_awaiting": "En attente d'examen",
        "w_map_tag": "[ ZEE de Maurice ]",
        "w_map_label": "Carte de la ZEE de Maurice avec un point par alerte du tableau",
        "w_map_credit": "Données navires : Global Fishing Watch.",
        "no_ais": "Sans AIS",
        "f_tag": "[ Filtres ]",
        "f_min_risk": "Risque minimum",
        "f_dark_only": "Navires fantômes uniquement",
        "f_apply": "Appliquer",
        "f_note": "Les scores classent les navires selon un comportement inhabituel. Ce ne sont pas des preuves de pêche illicite.",
        "r_tag": "[ Alertes classées ]",
        "r_sorted": "Triées par risque, du plus élevé au plus faible",
        "th_vessel": "Navire",
        "th_reason": "Raison principale",
        "th_risk": "Risque",
        "th_action": "Action",
        "open": "Ouvrir",
        "open_arrow": "Ouvrir →",
        "radar_contact": "Contact radar · sans AIS",
        "risk": "Risque",
        "w_empty": "Aucune alerte ne correspond à ces filtres.",

        # Computed values
        "level_high": "Élevé",
        "level_med": "Moyen",
        "level_low": "Faible",
        "send_patrol": "Envoyer une patrouille",
        "keep_watching": "Surveiller",
        "no_action": "Aucune action",
        "gear_Longliner": "Palangrier",
        "gear_Purse seiner": "Senneur",
        "gear_Carrier": "Transporteur",
        "gear_Unknown": "Inconnu",
    },
}


# Validation describes planned checks; no performance figures have been measured yet.
T["en"]["validation"] = {
    "tag": "Validation · Sample data", "lead": "How do we check whether the highest-ranked alerts deserve a closer look? We compare the ranking with a reference list and, once available, officer feedback.",
    "status": "Not evaluated yet", "status_text": "This version uses sample vessel data. Real-data validation has not been run, so these cards do not report accuracy or measured results.",
    "unavailable": "Not measured", "metrics": [
        {"title": "IOTC list matches", "text": "Planned check: count vessels in the top 20 alerts that also appear on the Indian Ocean Tuna Commission (IOTC) illegal fishing list."},
        {"title": "Random baseline", "text": "Planned comparison: repeat the list check on 20 randomly selected vessels from the same dataset."},
        {"title": "Officer dismissals", "text": "Share of reviewed alerts marked as false alarms. Officer review forms and measured feedback are not available yet."},
        {"title": "Radar coverage", "text": "Share of the Mauritius Exclusive Economic Zone imaged during the evaluation period. Coverage measurements are not connected yet."},
    ],
    "method": "How validation will work", "steps": [
        {"title": "Use a real dataset", "text": "Run the ranking on Global Fishing Watch data for a documented area and time period. Sample data is only for demonstrating the interface."},
        {"title": "Compare against a baseline", "text": "Check whether listed vessels appear more often among the highest-ranked alerts than in a random selection. Report sample sizes and the reference-list date."},
        {"title": "Collect officer feedback", "text": "Let officers review the reasons and record their decisions. Report the number reviewed alongside the dismissal rate."},
        {"title": "Publish measured results", "text": "Add the evaluation date, data sources, results, and limitations here after a real run. An unlisted vessel is not automatically a safe vessel."},
    ],
    "limits": "What these checks cannot tell us", "limitations": [
        {"title": "A list match is not accuracy", "text": "A reference list covers only some known cases. Matches help assess ranking, but cannot establish overall accuracy or prove a current offence."},
        {"title": "Missing signals have other explanations", "text": "Tracking signals can be lost or switched off for legitimate reasons. Radar coverage also varies, so some contacts may be missed."},
        {"title": "Events are not complete tracks", "text": "Recorded gaps, encounters and port visits do not reveal every position or everything a vessel did between observations."},
        {"title": "People make the decision", "text": "An unusual pattern is a reason to investigate, not a verdict. Flag country must not increase a vessel’s score."},
    ],
    "cta_title": "Explore the evidence behind an alert", "cta_text": "Open a vessel in Watch to see its recorded position, risk reasons and activity. The current examples use sample data.", "cta": "Go to Watch →",
}
T["fr"]["validation"] = {
    "tag": "Validation · Données d’exemple", "lead": "Comment vérifier si les alertes les mieux classées méritent un examen ? Nous comparons le classement à une liste de référence et, lorsqu’ils seront disponibles, aux retours des officiers.",
    "status": "Pas encore évalué", "status_text": "Cette version utilise des données fictives de navires. La validation sur données réelles n’a pas été effectuée : ces cartes ne présentent ni précision ni résultats mesurés.",
    "unavailable": "Non mesuré", "metrics": [
        {"title": "Correspondances CTOI", "text": "Vérification prévue : compter les navires du top 20 figurant aussi sur la liste de pêche illicite de la Commission des thons de l’océan Indien (CTOI)."},
        {"title": "Référence aléatoire", "text": "Comparaison prévue : refaire cette vérification sur 20 navires tirés au hasard dans les mêmes données."},
        {"title": "Rejets par les officiers", "text": "Part des alertes examinées classées comme fausses alertes. Le formulaire de décision et les retours mesurés ne sont pas encore disponibles."},
        {"title": "Couverture radar", "text": "Part de la zone économique exclusive de Maurice observée pendant la période d’évaluation. Les mesures de couverture ne sont pas encore connectées."},
    ],
    "method": "Comment la validation sera réalisée", "steps": [
        {"title": "Utiliser des données réelles", "text": "Exécuter le classement sur les données de Global Fishing Watch pour une zone et une période documentées. Les données fictives servent uniquement à présenter l’interface."},
        {"title": "Comparer à une référence", "text": "Vérifier si les navires répertoriés sont plus fréquents parmi les premières alertes que dans une sélection aléatoire. Indiquer les effectifs et la date de la liste."},
        {"title": "Recueillir les retours des officiers", "text": "Permettre aux officiers d’examiner les raisons et d’enregistrer leurs décisions. Afficher le nombre d’alertes examinées avec le taux de rejet."},
        {"title": "Publier les résultats mesurés", "text": "Ajouter ici la date, les sources, les résultats et les limites après une évaluation réelle. Un navire absent de la liste n’est pas automatiquement sans risque."},
    ],
    "limits": "Ce que ces vérifications ne disent pas", "limitations": [
        {"title": "Une correspondance n’est pas la précision", "text": "La liste de référence ne couvre que certains cas connus. Les correspondances aident à évaluer le classement, sans mesurer la précision globale ni prouver une infraction actuelle."},
        {"title": "Un signal absent peut s’expliquer", "text": "Les signaux peuvent être perdus ou coupés pour des raisons légitimes. La couverture radar varie également : certains contacts peuvent manquer."},
        {"title": "Des événements, pas des trajectoires complètes", "text": "Les coupures, rencontres et escales enregistrées ne révèlent pas chaque position ni toutes les activités entre deux observations."},
        {"title": "Une personne décide", "text": "Un comportement inhabituel justifie un examen, pas un verdict. Le pays du pavillon ne doit pas augmenter le score."},
    ],
    "cta_title": "Explorer les éléments d’une alerte", "cta_text": "Ouvrez un navire dans Surveillance pour consulter sa position, les raisons du score et son activité. Les exemples actuels utilisent des données fictives.", "cta": "Voir la surveillance →",
}


# Vessel details labels. Timestamps are shown as recorded: the CSV has no timezone.
T["en"]["detail"] = {
    "back": "← Back to Watch", "why": "Why it was flagged", "score": "Risk score",
    "points": "pts", "action": "Suggested action", "profile": "Vessel information",
    "last_seen": "Last seen", "recorded": "Times shown as recorded; timezone not supplied.",
    "position": "Last recorded position", "activity": "Recent activity", "when": "When",
    "event": "Event", "coordinates": "Latitude / longitude", "gear": "Vessel type",
    "flag": "Flag", "id": "Vessel ID", "mmsi": "MMSI · tracking identifier",
    "unknown": "Unknown", "unidentified": "Unidentified radar contact", "no_mmsi": "No AIS match",
    "flag_note": "Flag is shown for context only and does not change the score.",
    "empty": "No activity events are available for this vessel.",
    "map_label": "Last recorded vessel position and activity locations",
    "map_note": "Markers show recorded locations, not a continuous vessel track.",
    "map_error": "Map unavailable. Coordinates remain available below and in the activity list.",
    "missing_title": "Vessel not found", "missing_text": "This vessel is not in the current dataset. Return to Watch to choose an available alert.",
    "events": {"AIS gap": "AIS gap", "Encounter": "Encounter", "Loitering": "Loitering", "Fishing": "Fishing", "Port visit": "Port visit"},
    "flags": {},
}
T["fr"]["detail"] = {
    "back": "← Retour à la surveillance", "why": "Pourquoi cette alerte", "score": "Score de risque",
    "points": "pts", "action": "Action suggérée", "profile": "Informations du navire",
    "last_seen": "Dernière observation", "recorded": "Heures telles qu’enregistrées ; fuseau horaire non fourni.",
    "position": "Dernière position enregistrée", "activity": "Activité récente", "when": "Date et heure",
    "event": "Événement", "coordinates": "Latitude / longitude", "gear": "Type de navire",
    "flag": "Pavillon", "id": "Identifiant du navire", "mmsi": "MMSI · identifiant de suivi",
    "unknown": "Inconnu", "unidentified": "Contact radar non identifié", "no_mmsi": "Sans correspondance AIS",
    "flag_note": "Le pavillon est affiché à titre indicatif et ne modifie pas le score.",
    "empty": "Aucun événement disponible pour ce navire.",
    "map_label": "Dernière position du navire et lieux des événements",
    "map_note": "Les marqueurs indiquent des positions enregistrées, pas une trajectoire continue.",
    "map_error": "Carte indisponible. Les coordonnées restent accessibles ci-dessous et dans la liste des événements.",
    "missing_title": "Navire introuvable", "missing_text": "Ce navire ne figure pas dans les données actuelles. Retournez à la surveillance pour choisir une alerte disponible.",
    "events": {"AIS gap": "Coupure AIS", "Encounter": "Rencontre", "Loitering": "Errance", "Fishing": "Pêche", "Port visit": "Escale"},
    "flags": {"China": "Chine", "Taiwan": "Taïwan", "Mauritius": "Maurice", "Unknown": "Inconnu", "Spain": "Espagne", "Comoros": "Comores"},
}


# Guided tour copy stays with the rest of the interface translations.
T["en"]["tour"] = {
    "replay": "Take a tour", "start": "Show me around", "explore": "Explore on my own",
    "next": "Next", "back": "Back", "skip": "Skip tour", "finish": "Finish", "step": "Step",
    "welcome_title": "Welcome to Nightwatch",
    "welcome_text": "Spot unusual vessel behaviour, understand the reasons, and decide what needs a closer look. Nightwatch ranks alerts; an officer makes the final decision. This prototype currently uses sample data.",
    "steps": [
        {"target": ".counters", "title": "Your watch at a glance", "text": "These counters summarize the vessels matching your filters: alerts, high risk, contacts without AIS, and alerts awaiting review."},
        {"target": ".map-card", "title": "Explore the map", "text": "Select a vessel marker to see its risk score and open its alert. Dashed rings mark radar contacts without an AIS match."},
        {"target": ".watch-search", "title": "Find a vessel", "text": "Search by vessel name, MMSI, or vessel ID. The search keeps your current filters."},
        {"target": ".filters", "title": "Focus your search", "text": "Adjust the minimum risk score or show only contacts without AIS. The map, counters, and list update together."},
        {"target": ".ranked", "title": "Read the ranked alerts", "text": "Vessels are ranked by risk, with a reason and suggested action. Open a row to visit its alert page. Open an alert to read its reasons, position, and activity. Officer reviews are still being built; a high score is not proof of illegal activity."},
    ],
}
T["fr"]["tour"] = {
    "replay": "Visite guidée", "start": "Me faire découvrir", "explore": "Explorer librement",
    "next": "Suivant", "back": "Retour", "skip": "Passer la visite", "finish": "Terminer", "step": "Étape",
    "welcome_title": "Bienvenue sur Nightwatch",
    "welcome_text": "Repérez les comportements inhabituels des navires, comprenez les raisons et choisissez les alertes à examiner. Nightwatch classe les alertes ; un officier prend la décision finale. Ce prototype utilise actuellement des données fictives.",
    "steps": [
        {"target": ".counters", "title": "Votre surveillance en bref", "text": "Ces compteurs résument les navires correspondant aux filtres : alertes, risque élevé, contacts sans AIS et alertes en attente d’examen."},
        {"target": ".map-card", "title": "Explorer la carte", "text": "Sélectionnez un navire pour voir son score de risque et ouvrir son alerte. Les cercles pointillés indiquent les contacts radar sans correspondance AIS."},
        {"target": ".watch-search", "title": "Trouver un navire", "text": "Recherchez par nom, MMSI ou identifiant du navire. La recherche conserve vos filtres actuels."},
        {"target": ".filters", "title": "Affiner la recherche", "text": "Réglez le risque minimum ou affichez uniquement les contacts sans AIS. La carte, les compteurs et la liste se mettent à jour ensemble."},
        {"target": ".ranked", "title": "Lire les alertes classées", "text": "Les navires sont classés par risque, avec une raison et une action suggérée. Ouvrez une ligne pour consulter son alerte. Consultez les raisons, la position et l’activité dans chaque alerte. Les décisions des officiers sont encore en développement ; un score élevé ne prouve pas une activité illégale."},
    ],
}


# Reasons are stored in English in alerts.csv, often with a number inside
# ("AIS off for 31 hours near EEZ edge"). Each pattern below matches one kind of
# sentence; (\d+) captures the number so the French sentence can reuse it.
# The pipeline (Phase 6) must write sentences in these same shapes.

REASONS_FR = [
    (r"AIS off for (\d+) hours near EEZ edge", "AIS coupé pendant {0} heures près de la limite de la ZEE"),
    (r"Met a refrigerated carrier at sea", "Rencontre avec un cargo frigorifique en mer"),
    (r"Loitered (\d+) days far from port", "{0} jours d'errance loin du port"),
    (r"No port visit in (\d+) days", "Aucune escale depuis {0} jours"),
    (r"Changed name or ID (\d+) times this year", "{0} changements de nom ou d'identifiant cette année"),
    (r"Fishing close to a protected area", "Pêche près d'une aire marine protégée"),
    (r"Radar detection with no AIS signal", "Détection radar sans signal AIS"),
]


def translate_reason(text, lang):
    """Show a stored English reason in the page language. Unknown sentences stay in English."""
    if lang == "en":
        return text
    for pattern, french in REASONS_FR:
        match = re.fullmatch(pattern, text)
        if match:
            return french.format(*match.groups())
    return text
