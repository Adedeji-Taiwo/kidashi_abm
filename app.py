"""
KidashiSim -- public landing page
==================================

Structure copied deliberately from the GROCERYsim reference (hero with
a live figure, a Case Studies grid, a Documentation view, an About
modal) -- NOT its slider-and-card simulator. The only "engine" here is
FIG 01 in components/live_figure.py; everything else is presentation.

Run:
    pip install streamlit
    streamlit run app.py

Three things to edit before you publish, all marked EDIT ME below:
    1. GITHUB_URL              -- your real repo
    2. CASE_STUDIES "soon"     -- placeholder roadmap cards, swap for real ones
    3. STRINGS["EN"]["about_citation"] etc. -- confirm citation format

TRANSLATIONS: FR/ES/HA cover all navigation, hero copy, headings and
labels. Table data (agent names, shock-regime IDs), the author bio,
citation and license are kept in English/original form in every
language on purpose -- they're identifiers or academic conventions,
not prose. FR/ES are solid; HA is a first-pass machine draft and
should get a native-speaker pass before this goes fully public.
"""


from __future__ import annotations
from model.model import KidashiModel
from components.live_figure import render_kidashi_live_figure
import streamlit as st
from matplotlib.ticker import FuncFormatter
import matplotlib.pyplot as plt
from pathlib import Path

import matplotlib
# headless backend -- no display server on a Streamlit host
matplotlib.use("Agg")


# ---------------------------------------------------------------------------
# EDIT ME
GITHUB_URL = "https://github.com/Adedeji-Taiwo/kidashi_abm"
MANUAL_PDF_PATH = Path(__file__).parent / "KidashiSim_User_Manual.pdf"
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="KidashiSim \u00b7 ABM",
    page_icon="\U0001f33e",
    layout="wide",
    initial_sidebar_state="collapsed",
)

LANGS = ["EN", "FR", "ES", "HA"]

STRINGS = {
    "EN": {
        "crumb_back": "\u2039 BACK TO OVERVIEW",
        "hero_eyebrow": "FINTECH \u00b7 STAPLE VALUE CHAINS",
        "hero_lead": "Agent-Based Model for Fintech Liquidity, Farmgate Price Resilience &amp; Smallholder Welfare.",
        "hero_copy": "Simulate how Kidashi trust-circle credit, crop diversity, traders and shocks reshape Nigerian staple value chains &mdash; from distress sales and payment delays to liquidity-backed market resilience.",
        "btn_cases": "Case studies \u2192",
        "btn_docs": "Documentation",
        "btn_about": "About",
        "cases_eyebrow": "SECUREVALUE",
        "cases_title": "Case Studies",
        "cases_sub": "Select a market context to explore.",
        "badge_live": "LIVE",
        "badge_soon": "SOON",
        "coming_soon": "Coming soon",
        "launch_simulator": "Launch simulator \u2192",
        "sim_eyebrow": "LIVE SIMULATOR",
        "sim_title": "Kidashi Simulator",
        "sim_sub": "Configure a scenario, run the model, and inspect the headline indicators.",
        "sim_controls_h": "Scenario controls",
        "sim_steps": "Simulation steps (seasons)",
        "sim_num_farmers": "Farmer agents",
        "sim_num_traders": "Trader agents",
        "sim_fintech": "Fintech penetration",
        "sim_trade_openness": "Trade openness",
        "sim_diversity_policy": "Diversity policy",
        "sim_shock_regime": "Shock regime",
        "sim_seed": "Random seed",
        "sim_run_btn": "Run simulation",
        "sim_running": "Running simulation \u2026",
        "sim_results_eyebrow": "SIMULATION RESULTS",
        "sim_results_title": "Results",
        "sim_empty_state": "Set your parameters above and click \u201cRun simulation\u201d to see results here.",
        "metric_wealth": "Mean farmer wealth",
        "metric_maize": "Maize price",
        "metric_sorghum": "Sorghum price",
        "metric_tomato": "Tomato price",
        "metric_diversity": "Diversity index",
        "metric_par30": "PAR30 (credit risk)",
        "chart_prices_title": "Farmgate prices over time",
        "chart_wealth_title": "Mean farmer wealth over time",
        "chart_diversity_title": "Diversity index over time",
        "axis_step": "Step (season)",
        "axis_price": "Farmgate price (NGN/MT)",
        "axis_wealth": "Mean farmer wealth (NGN)",
        "axis_diversity": "Mean diversity index (H\u2032)",
        "crop_maize": "Maize",
        "crop_sorghum": "Sorghum",
        "crop_tomato": "Tomato",
        "docs_eyebrow": "MODEL ARCHITECTURE",
        "docs_title": "Documentation",
        "docs_sub": "A short reference. Full method notes and code live in the GitHub repository.",
        "docs_download": "Download the full User Manual (PDF)",
        "docs_download_missing": "Full PDF manual not found \u2014 place KidashiSim_User_Manual.pdf next to app.py to enable this download.",
        "docs_overview_h": "Overview",
        "docs_overview_p": "An Agent-Based Model investigating how fintech-led liquidity provision (the Kidashi trust-circle credit product) and production diversity jointly shape farmgate price resilience and smallholder welfare under domestic supply shocks and international market disruption.",
        "stat1": "Post-harvest spoilage reduction with fintech",
        "stat2": "Profit uplift under financial liquidity",
        "stat3": "Payment cycle vs. 60\u201390 days baseline",
        "docs_agents_h": "Agents",
        "docs_shocks_h": "Shock regimes",
        "docs_policy_h": "Diversity policies",
        "policy_none": "no intervention; portfolio shaped by expected utility alone.",
        "policy_incentive": "diversified farmers (Shannon H' above threshold) receive a 5% price premium.",
        "policy_mandate": "minimum crop-share floor raised to equal weighting across all three crops.",
        "docs_github": "Full README &amp; source on GitHub \u2192",
        "th_agent": "Agent", "th_count": "Count", "th_behaviours": "Key behaviours",
        "th_regime": "Regime", "th_weather": "Weather volatility",
        "th_trade": "Trade shock probability", "th_magnitude": "Magnitude",
        "about_kicker": "ABOUT KIDASHISIM",
        "about_title": "Kidashi ABM",
        "about_intro": "This application showcases an academic Agent-Based Model exploring how fintech-led liquidity and crop-diversification policy shape farmgate price resilience and smallholder welfare in Nigerian staple value chains. All figures shown are illustrative simulation output.",
        "about_author_label": "AUTHOR",
        "about_citation_label": "CITATION",
        "about_license_label": "LICENSE",
        "about_license": "MIT License.",
    },
    "FR": {
        "crumb_back": "\u2039 RETOUR \u00c0 L'APER\u00c7U",
        "hero_eyebrow": "FINTECH \u00b7 CHA\u00cENES DE VALEUR VIVRI\u00c8RES",
        "hero_lead": "Mod\u00e8le multi-agents pour la liquidit\u00e9 fintech, la r\u00e9silience des prix au champ et le bien-\u00eatre des petits exploitants.",
        "hero_copy": "Simulez comment le cr\u00e9dit de cercle de confiance Kidashi, la diversit\u00e9 des cultures, les commer\u00e7ants et les chocs transforment les cha\u00eenes de valeur vivri\u00e8res nig\u00e9rianes &mdash; des ventes de d\u00e9tresse et retards de paiement \u00e0 la r\u00e9silience du march\u00e9 gr\u00e2ce \u00e0 la liquidit\u00e9.",
        "btn_cases": "\u00c9tudes de cas \u2192",
        "btn_docs": "Documentation",
        "btn_about": "\u00c0 propos",
        "cases_eyebrow": "CHA\u00cENE DE VALEUR S\u00c9CURIS\u00c9E",
        "cases_title": "\u00c9tudes de cas",
        "cases_sub": "S\u00e9lectionnez un contexte de march\u00e9 \u00e0 explorer.",
        "badge_live": "EN DIRECT",
        "badge_soon": "BIENT\u00d4T",
        "coming_soon": "Bient\u00f4t disponible",
        "launch_simulator": "Lancer le simulateur \u2192",
        "sim_eyebrow": "SIMULATEUR EN DIRECT",
        "sim_title": "Simulateur Kidashi",
        "sim_sub": "Configurez un sc\u00e9nario, ex\u00e9cutez le mod\u00e8le et consultez les indicateurs cl\u00e9s.",
        "sim_controls_h": "Param\u00e8tres du sc\u00e9nario",
        "sim_steps": "\u00c9tapes de simulation (saisons)",
        "sim_num_farmers": "Agriculteurs (agents)",
        "sim_num_traders": "Commer\u00e7ants (agents)",
        "sim_fintech": "P\u00e9n\u00e9tration fintech",
        "sim_trade_openness": "Ouverture commerciale",
        "sim_diversity_policy": "Politique de diversit\u00e9",
        "sim_shock_regime": "R\u00e9gime de choc",
        "sim_seed": "Graine al\u00e9atoire",
        "sim_run_btn": "Lancer la simulation",
        "sim_running": "Simulation en cours \u2026",
        "sim_results_eyebrow": "R\u00c9SULTATS DE LA SIMULATION",
        "sim_results_title": "R\u00e9sultats",
        "sim_empty_state": "D\u00e9finissez vos param\u00e8tres ci-dessus puis cliquez sur \u00ab\u00a0Lancer la simulation\u00a0\u00bb pour voir les r\u00e9sultats.",
        "metric_wealth": "Richesse moyenne des agriculteurs",
        "metric_maize": "Prix du ma\u00efs",
        "metric_sorghum": "Prix du sorgho",
        "metric_tomato": "Prix de la tomate",
        "metric_diversity": "Indice de diversit\u00e9",
        "metric_par30": "PAR30 (risque de cr\u00e9dit)",
        "chart_prices_title": "Prix au champ dans le temps",
        "chart_wealth_title": "Richesse moyenne des agriculteurs dans le temps",
        "chart_diversity_title": "Indice de diversit\u00e9 dans le temps",
        "axis_step": "\u00c9tape (saison)",
        "axis_price": "Prix au champ (NGN/MT)",
        "axis_wealth": "Richesse moyenne des agriculteurs (NGN)",
        "axis_diversity": "Indice de diversit\u00e9 moyen (H\u2032)",
        "crop_maize": "Ma\u00efs",
        "crop_sorghum": "Sorgho",
        "crop_tomato": "Tomate",
        "docs_eyebrow": "ARCHITECTURE DU MOD\u00c8LE",
        "docs_title": "Documentation",
        "docs_sub": "R\u00e9f\u00e9rence succincte. Les notes m\u00e9thodologiques compl\u00e8tes et le code se trouvent sur le d\u00e9p\u00f4t GitHub.",
        "docs_download": "T\u00e9l\u00e9charger le manuel complet (PDF)",
        "docs_download_missing": "Manuel PDF introuvable \u2014 placez KidashiSim_User_Manual.pdf \u00e0 c\u00f4t\u00e9 de app.py pour activer ce t\u00e9l\u00e9chargement.",
        "docs_overview_h": "Aper\u00e7u",
        "docs_overview_p": "Un mod\u00e8le multi-agents \u00e9tudiant comment la fourniture de liquidit\u00e9 fintech (le produit de cr\u00e9dit de cercle de confiance Kidashi) et la diversit\u00e9 de production fa\u00e7onnent conjointement la r\u00e9silience des prix au champ et le bien-\u00eatre des petits exploitants face aux chocs d'approvisionnement domestiques et aux perturbations du march\u00e9 international.",
        "stat1": "R\u00e9duction du gaspillage post-r\u00e9colte gr\u00e2ce \u00e0 la fintech",
        "stat2": "Hausse de profit gr\u00e2ce \u00e0 la liquidit\u00e9 financi\u00e8re",
        "stat3": "Cycle de paiement contre une base de 60 \u00e0 90 jours",
        "docs_agents_h": "Agents",
        "docs_shocks_h": "R\u00e9gimes de choc",
        "docs_policy_h": "Politiques de diversit\u00e9",
        "policy_none": "aucune intervention\u00a0; le portefeuille est fa\u00e7onn\u00e9 par la seule utilit\u00e9 esp\u00e9r\u00e9e.",
        "policy_incentive": "les agriculteurs diversifi\u00e9s (H' de Shannon au-dessus du seuil) re\u00e7oivent une prime de prix de 5\u00a0%.",
        "policy_mandate": "le seuil minimal de r\u00e9partition des cultures est relev\u00e9 \u00e0 une pond\u00e9ration \u00e9gale entre les trois cultures.",
        "docs_github": "README complet &amp; code source sur GitHub \u2192",
        "th_agent": "Agent", "th_count": "Nombre", "th_behaviours": "Comportements cl\u00e9s",
        "th_regime": "R\u00e9gime", "th_weather": "Volatilit\u00e9 m\u00e9t\u00e9orologique",
        "th_trade": "Probabilit\u00e9 de choc commercial", "th_magnitude": "Ampleur",
        "about_kicker": "\u00c0 PROPOS DE KIDASHISIM",
        "about_title": "Kidashi ABM",
        "about_intro": "Cette application pr\u00e9sente un mod\u00e8le multi-agents acad\u00e9mico explorant comment la liquidit\u00e9 fintech et la politique de diversification des cultures fa\u00e7onnent la r\u00e9silience des prix au champ et le bien-\u00eatre des petits exploitants dans les cha\u00eenes de valeur vivri\u00e8res nig\u00e9rianes. Tous les chiffres affich\u00e9s sont des r\u00e9sultats de simulation illustratifs.",
        "about_author_label": "AUTEUR",
        "about_citation_label": "CITATION",
        "about_license_label": "LICENCE",
        "about_license": "Licence MIT.",
    },
    "ES": {
        "crumb_back": "\u2039 VOLVER AL RESUMEN",
        "hero_eyebrow": "FINTECH \u00b7 CADENAS DE VALOR DE ALIMENTOS B\u00c1SICOS",
        "hero_lead": "Modelo basado en agentes para la liquidez fintech, la resiliencia de precios en finca y el bienestar de los peque\u00f1os agricultores.",
        "hero_copy": "Simule c\u00f3mo el cr\u00e9dito de c\u00edrculo de confianza Kidashi, la diversidad de cultivos, los comerciantes y los choques transforman las cadenas de valor de alimentos b\u00e1sicos nigerianas &mdash; desde ventas de emergencia y retrasos de pago hasta la resiliencia del mercado respaldada por liquidez.",
        "btn_cases": "Casos de estudio \u2192",
        "btn_docs": "Documentaci\u00f3n",
        "btn_about": "Acerca de",
        "cases_eyebrow": "CADENA DE VALOR SEGURA",
        "cases_title": "Casos de estudio",
        "cases_sub": "Seleccione un contexto de mercado para explorar.",
        "badge_live": "EN VIVO",
        "badge_soon": "PR\u00d3XIMAMENTE",
        "coming_soon": "Pr\u00f3ximamente",
        "launch_simulator": "Iniciar el simulador \u2192",
        "sim_eyebrow": "SIMULADOR EN VIVO",
        "sim_title": "Simulador Kidashi",
        "sim_sub": "Configure un escenario, ejecute el modelo y consulte los indicadores clave.",
        "sim_controls_h": "Par\u00e1metros del escenario",
        "sim_steps": "Pasos de simulaci\u00f3n (temporadas)",
        "sim_num_farmers": "Agricultores (agentes)",
        "sim_num_traders": "Comerciantes (agentes)",
        "sim_fintech": "Penetraci\u00f3n fintech",
        "sim_trade_openness": "Apertura comercial",
        "sim_diversity_policy": "Pol\u00edtica de diversidad",
        "sim_shock_regime": "R\u00e9gimen de choque",
        "sim_seed": "Semilla aleatoria",
        "sim_run_btn": "Ejecutar simulaci\u00f3n",
        "sim_running": "Ejecutando simulaci\u00f3n \u2026",
        "sim_results_eyebrow": "RESULTADOS DE LA SIMULACI\u00d3N",
        "sim_results_title": "Resultados",
        "sim_empty_state": "Defina sus par\u00e1metros arriba y haga clic en \u00abEjecutar simulaci\u00f3n\u00bb para ver los resultados.",
        "metric_wealth": "Riqueza media del agricultor",
        "metric_maize": "Precio del ma\u00edz",
        "metric_sorghum": "Precio del sorgo",
        "metric_tomato": "Precio del tomate",
        "metric_diversity": "\u00cdndice de diversidad",
        "metric_par30": "PAR30 (riesgo crediticio)",
        "chart_prices_title": "Precios en finca a lo largo del tiempo",
        "chart_wealth_title": "Riqueza media del agricultor a lo largo del tiempo",
        "chart_diversity_title": "\u00cdndice de diversidad a lo largo del tiempo",
        "axis_step": "Paso (temporada)",
        "axis_price": "Precio en finca (NGN/MT)",
        "axis_wealth": "Riqueza media del agricultor (NGN)",
        "axis_diversity": "\u00cdndice de diversidad medio (H\u2032)",
        "crop_maize": "Ma\u00edz",
        "crop_sorghum": "Sorgo",
        "crop_tomato": "Tomate",
        "docs_eyebrow": "ARQUITECTURA DEL MODELO",
        "docs_title": "Documentaci\u00f3n",
        "docs_sub": "Una referencia breve. Las notas metodol\u00f3gicas completas y el c\u00f3digo est\u00e1n en el repositorio de GitHub.",
        "docs_download": "Descargar el manual completo (PDF)",
        "docs_download_missing": "No se encontr\u00f3 el manual en PDF \u2014 coloque KidashiSim_User_Manual.pdf junto a app.py para habilitar esta descarga.",
        "docs_overview_h": "Resumen",
        "docs_overview_p": "Un modelo basado en agentes que investiga c\u00f3mo la provisi\u00f3n de liquidez fintech (el producto de cr\u00e9dito de c\u00edrculo de confianza Kidashi) y la diversidad de producci\u00f3n configuran conjuntamente la resiliencia de precios en finca y el bienestar de los peque\u00f1os agricultores ante choques de suministro internos y perturbaciones del mercado internacional.",
        "stat1": "Reducci\u00f3n de mermas poscosecha con fintech",
        "stat2": "Aumento de beneficios con liquidez financiera",
        "stat3": "Ciclo de pago frente a una base de 60 a 90 d\u00edas",
        "docs_agents_h": "Agentes",
        "docs_shocks_h": "Reg\u00edmenes de choque",
        "docs_policy_h": "Pol\u00edticas de diversidad",
        "policy_none": "sin intervenci\u00f3n; la cartera se determina solo por la utilidad esperada.",
        "policy_incentive": "los agricultores diversificados (H' de Shannon por encima del umbral) reciben una prima de precio del 5\u00a0%.",
        "policy_mandate": "el piso m\u00ednimo de reparto de cultivos se eleva a una ponderaci\u00f3n igual entre los tres cultivos.",
        "docs_github": "README completo y c\u00f3digo fuente en GitHub \u2192",
        "th_agent": "Agente", "th_count": "Cantidad", "th_behaviours": "Comportamientos clave",
        "th_regime": "Reg\u00edmen", "th_weather": "Volatilidad clim\u00e1tica",
        "th_trade": "Probabilidad de choque comercial", "th_magnitude": "Magnitud",
        "about_kicker": "ACERCA DE KIDASHISIM",
        "about_title": "Kidashi ABM",
        "about_intro": "Esta aplicaci\u00f3n presenta un modelo acad\u00e9mico basado en agentes que explora c\u00f3mo la liquidez fintech y la pol\u00edtica de diversificaci\u00f3n de cultivos configuran la resiliencia de precios en finca y el bienestar de los peque\u00f1os agricultores en las cadenas de valor de alimentos b\u00e1sicos nigerianas. Todas las cifras mostradas son resultados de simulaci\u00f3n ilustrativos.",
        "about_author_label": "AUTOR",
        "about_citation_label": "CITA",
        "about_license_label": "LICENCIA",
        "about_license": "Licencia MIT.",
    },
    "HA": {
        "crumb_back": "\u2039 KOMA BAYANI",
        "hero_eyebrow": "FINTECH \u00b7 SARKAR AMFANIN GONA",
        "hero_lead": "Tsarin Wakili don Ruwan Ku\u0257i na Fintech, Karko na Farashin Gona, da Jin Da\u0257in Manoma \u0198an\u0257an\u0257a.",
        "hero_copy": "Ka gwada yadda bashin da'irar amana ta Kidashi, bambancin amfanin gona, \u2018yan kasuwa, da girgizar kasuwa ke canza sarkar amfanin gona ta Najeriya &mdash; daga sayarwa cikin tsananin bukata da jinkirin biya, zuwa \u0199arko na kasuwa ta hanyar ruwan ku\u0257i.",
        "btn_cases": "Nazarce-nazarce \u2192",
        "btn_docs": "Takardun Bayani",
        "btn_about": "Game da Mu",
        "cases_eyebrow": "SARKAR AMINCI",
        "cases_title": "Nazarce-nazarce",
        "cases_sub": "Za\u0253i wurin kasuwa da za a bincika.",
        "badge_live": "MAI GUDANA",
        "badge_soon": "NAN BA DA JIMAWA BA",
        "coming_soon": "Nan ba da jimawa ba",
        "launch_simulator": "Fara kwaikwayo \u2192",
        "sim_eyebrow": "KWAIKWAYO KAI TSAYE",
        "sim_title": "Na\u2019urar Kwaikwayo ta Kidashi",
        "sim_sub": "Saita yanayin gwaji, gudanar da samfurin, sannan ka duba manyan alkaluma.",
        "sim_controls_h": "Ma\u2019aunan yanayin gwaji",
        "sim_steps": "Matakan kwaikwayo (lokutan noma)",
        "sim_num_farmers": "Wakilan manoma",
        "sim_num_traders": "Wakilan \u2019yan kasuwa",
        "sim_fintech": "Yaduwar fintech",
        "sim_trade_openness": "Bu\u0257ewar kasuwanci",
        "sim_diversity_policy": "Manufar bambanci",
        "sim_shock_regime": "Nau\u2019in girgiza",
        "sim_seed": "Iri na bazuwar lamba",
        "sim_run_btn": "Gudanar da kwaikwayo",
        "sim_running": "Ana gudanar da kwaikwayo \u2026",
        "sim_results_eyebrow": "SAKAMAKON KWAIKWAYO",
        "sim_results_title": "Sakamako",
        "sim_empty_state": "Saita ma\u2019aunanka a sama sannan ka danna \u201cGudanar da kwaikwayo\u201d domin ganin sakamako a nan.",
        "metric_wealth": "Matsakaicin dukiyar manomi",
        "metric_maize": "Farashin masara",
        "metric_sorghum": "Farashin dawa",
        "metric_tomato": "Farashin tumatir",
        "metric_diversity": "Alamar bambanci",
        "metric_par30": "PAR30 (ha\u0257arin bashi)",
        "chart_prices_title": "Farashin gona cikin lokaci",
        "chart_wealth_title": "Matsakaicin dukiyar manomi cikin lokaci",
        "chart_diversity_title": "Alamar bambanci cikin lokaci",
        "axis_step": "Mataki (lokacin noma)",
        "axis_price": "Farashin gona (NGN/MT)",
        "axis_wealth": "Matsakaicin dukiyar manomi (NGN)",
        "axis_diversity": "Matsakaicin alamar bambanci (H\u2032)",
        "crop_maize": "Masara",
        "crop_sorghum": "Dawa",
        "crop_tomato": "Tumatir",
        "docs_eyebrow": "TSARIN SAMFURI",
        "docs_title": "Takardun Bayani",
        "docs_sub": "Ta\u0199aitaccen bayani. Cikakken bayani da lambar shirin suna nan a shafin GitHub.",
        "docs_download": "Sauke Cikakken Littafin Jagora (PDF)",
        "docs_download_missing": "Ba a sami littafin PDF ba \u2014 sanya KidashiSim_User_Manual.pdf kusa da app.py domin kunna saukewa.",
        "docs_overview_h": "Bayanin Gaba \u00d0aya",
        "docs_overview_p": "Tsarin wakili wanda ke nazarin yadda samar da ruwan ku\u0257i ta fintech (kayayyakin bashin da'irar amana na Kidashi) da bambancin noma ke tasiri tare a kan \u0199arko na farashin gona da jin da\u0257in manoma \u0199anana a lokatim matsalar samar da kaya da rikicin kasuwar duniya.",
        "stat1": "Ragewar \u0253arna bayan girbi ta hanyar fintech",
        "stat2": "\u0198arin riba ta hanyar ruwan ku\u0257i",
        "stat3": "Zagayen biya idan aka kwatanta da kwanaki 60\u201390",
        "docs_agents_h": "Wakilai",
        "docs_shocks_h": "Nau'ikan Girgiza",
        "docs_policy_h": "Manufofin Bambanci",
        "policy_none": "babu shiga tsakani; jarin manomi yana bin amfanin da ake tsammani kawai.",
        "policy_incentive": "manoma masu bambancin amfanin gona (H' na Shannon sama da iyaka) suna samun \u0199arin farashi na kashi 5%.",
        "policy_mandate": "an \u0257aga iyakar rabon amfanin gona zuwa daidaito tsakanin dukkan amfanin guda uku.",
        "docs_github": "Cikakken README &amp; lambar shiri a GitHub \u2192",
        "th_agent": "Wakili", "th_count": "Yawa", "th_behaviours": "Manyan Halaye",
        "th_regime": "Nau'i", "th_weather": "Sauyin Yanayi",
        "th_trade": "Yiwuwar Girgizar Kasuwanci", "th_magnitude": "Girma",
        "about_kicker": "GAME DA KIDASHISIM",
        "about_title": "Kidashi ABM",
        "about_intro": "Wannan manhaja tana nuna tsarin wakili na ilimi wanda ke nazarin yadda ruwan ku\u0257i na fintech da manufar bambanta amfanin gona ke tasiri kan \u0199arko na farashin gona da jin da\u0257in manoma \u0199anana a sarkar amfanin gona ta Najeriya. Duk lambobin da aka nuna misalai ne kawai na sakamakon kwaikwayo.",
        "about_author_label": "MARUBUCI",
        "about_citation_label": "AMBATO",
        "about_license_label": "LASISI",
        "about_license": "Lasisin MIT.",
    },
}


def nav_url(*, lang: str, view: str = "home", about: bool = False) -> str:
    """Build a temporary internal navigation signal."""
    params = [f"nav_view={view}", f"nav_lang={lang}"]
    if about:
        params.append("nav_about=1")
    return "?" + "&".join(params)


def init_navigation_state() -> None:
    if "view" not in st.session_state:
        st.session_state["view"] = "home"

    if "lang" not in st.session_state:
        st.session_state["lang"] = "EN"

    if "about_open" not in st.session_state:
        st.session_state["about_open"] = False

    incoming_view = st.query_params.get(
        "nav_view") or st.query_params.get("view")
    incoming_lang = st.query_params.get(
        "nav_lang") or st.query_params.get("lang")
    incoming_about = st.query_params.get(
        "nav_about") or st.query_params.get("about")

    has_navigation_signal = any(
        key in st.query_params
        for key in ("nav_view", "nav_lang", "nav_about", "view", "lang", "about")
    )

    if incoming_lang:
        incoming_lang = incoming_lang.upper()
        if incoming_lang in STRINGS:
            st.session_state["lang"] = incoming_lang

    if incoming_view in ("home", "cases", "docs", "simulator"):
        st.session_state["view"] = incoming_view

    if has_navigation_signal:
        st.session_state["about_open"] = incoming_about == "1"
        st.query_params.clear()
        st.rerun()


# ---------------------------------------------------------------------------
# Design system
# ---------------------------------------------------------------------------

def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg: #0b3a40;
            --bg2: #082a30;
            --panel: rgba(6, 31, 37, 0.60);
            --line: rgba(126, 223, 224, 0.18);
            --line-strong: rgba(126, 223, 224, 0.32);
            --cyan: #7edfe0;
            --cyan-strong: #00d4ff;
            --cream: #f3efe4;
            --orange: #eba654;
            --gold: #f2b84b;
            --green: #3fbd7a;
            --red: #ef4444;
            --muted: rgba(220, 236, 235, 0.70);
        }

        html, body, .stApp, [data-testid="stAppViewContainer"] {
            background:
              radial-gradient(circle at 24% 18%, rgba(126, 223, 224, 0.10), transparent 28%),
              linear-gradient(180deg, var(--bg) 0%, var(--bg2) 100%);
            color: var(--cream);
        }
        [data-testid="stHeader"] { background: transparent; }
        [data-testid="stToolbar"] { visibility: hidden; }
        #MainMenu, footer { visibility: hidden; }
        .block-container { max-width: 1180px; padding-top: 1.2rem; padding-bottom: 3rem; }

        /* ---------- top bar ---------- */
        .top {
            height: 78px;
            display: flex; align-items: center; justify-content: space-between;
            border-bottom: 1px solid var(--line);
            margin-bottom: 3.4rem;
        }
        .langs {
            display: flex; border: 1px solid var(--line-strong); border-radius: 4px; overflow: hidden;
        }
        .langs a {
            padding: 0.55rem 0.82rem; border-right: 1px solid var(--line);
            color: rgba(220,236,235,0.65); font-size: 0.76rem; font-weight: 900; letter-spacing: 0.08em;
            text-decoration: none; display: inline-block;
        }
        .langs a:last-child { border-right: 0; }
        .langs a.active { color: var(--orange); background: rgba(235,166,84,0.10); }

        .crumb { color: var(--cyan); font: 800 0.74rem ui-monospace, Consolas, monospace; letter-spacing: 0.1em;
                 text-decoration: none; }
        .crumb:hover { color: var(--cream); }

        /* ---------- hero ---------- */
        .eyebrow {
            display: flex; align-items: center; gap: 0.9rem; color: var(--cyan);
            font-size: 0.72rem; font-weight: 900; letter-spacing: 0.19em; margin-bottom: 1.7rem;
        }
        .eyebrow::before { content: ""; width: 28px; height: 1px; background: var(--cyan); opacity: 0.75; }
        .title { margin: 0; font-size: clamp(3.2rem, 7vw, 5.6rem); line-height: 0.90; letter-spacing: -0.06em;
                  font-weight: 950; color: var(--cream); }
        .title span { color: var(--orange); font-weight: 500; font-style: italic; letter-spacing: -0.08em; }
        .abm-badge { display: inline-flex; margin: 1.3rem 0 1.2rem; padding: 0.32rem 0.9rem;
                     border: 1px solid var(--cyan); color: var(--cyan); font-size: 1.15rem; font-weight: 900;
                     letter-spacing: 0.22em; }
        .lead { max-width: 460px; color: var(--cream); font-size: 1.0rem; line-height: 1.45; font-weight: 720;
                margin-bottom: 1.3rem; }
        .copy { max-width: 500px; color: var(--muted); font-size: 0.92rem; line-height: 1.62; margin-bottom: 1.6rem; }

        /* Style native Streamlit buttons to match design */
        div[data-testid="stButton"] button, .stButton > button,
        div[data-testid="stDownloadButton"] button {
            height: 48px !important; min-width: 135px !important;
            background: rgba(5,25,31,0.28) !important; border: 1px solid var(--line-strong) !important;
            color: var(--cream) !important; font-weight: 850 !important; border-radius: 3px !important;
        }
        div[data-testid="stButton"] button:hover, .stButton > button:hover,
        div[data-testid="stDownloadButton"] button:hover {
            border-color: var(--cyan) !important; color: var(--cyan) !important;
        }
        div[data-testid="stButton"] button:disabled, .stButton > button:disabled,
        div[data-testid="stDownloadButton"] button:disabled { opacity: 0.4 !important; }

        /* Primary Button Match (.btn.primary) */
        div[data-testid="stButton"] button[kind="primary"] {
            background: var(--orange) !important; 
            border-color: var(--orange) !important; 
            color: #07131c !important;
        }
        div[data-testid="stButton"] button[kind="primary"]:hover {
            background: #f3b869 !important; 
            border-color: #f3b869 !important; 
            color: #07131c !important;
        }

        div[data-testid="stLinkButton"] { width: 100% !important; }
        div[data-testid="stLinkButton"] a {
            width: 100% !important; min-width: 100% !important; height: 48px !important;
            box-sizing: border-box !important; display: inline-flex !important; align-items: center !important;
            justify-content: center !important; background: var(--orange) !important; border: 1px solid var(--orange) !important;
            color: #07131c !important; font-weight: 850 !important; font-size: 0.86rem !important;
            border-radius: 3px !important; text-decoration: none !important; white-space: nowrap !important;
        }
        div[data-testid="stLinkButton"] a:hover {
            background: #f3b869 !important; border-color: #f3b869 !important; color: #07131c !important; text-decoration: none !important;
        }

        /* ---------- case studies ---------- */
        .page-head { margin-bottom: 2.2rem; }
        .page-head h1 { color: var(--cream); font-size: 2.1rem; font-weight: 900; letter-spacing: -0.02em; margin: 0.5rem 0 0.3rem; }
        .page-head p { color: var(--muted); margin: 0; }
        .case-card {
            background: var(--panel); border: 1px solid var(--line); border-radius: 10px;
            padding: 1.15rem 1.15rem 0.2rem; min-height: 232px; display: flex; flex-direction: column;
        }
        .case-card-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; }
        .case-flag { display: inline-flex; align-items: center; justify-content: center; font-size: 1.3rem; }
        .case-flag img { width: 34px; height: 24px; object-fit: cover; border-radius: 4px; display: block; }
        .case-badge { font-size: 0.62rem; font-weight: 900; letter-spacing: 0.12em; padding: 0.2rem 0.55rem; border-radius: 999px; }
        .case-badge.live { background: rgba(63,189,122,0.18); color: var(--green); border: 1px solid rgba(63,189,122,0.4); }
        .case-badge.soon { background: rgba(220,236,235,0.07); color: var(--muted); border: 1px solid var(--line); }
        .case-icon { color: var(--cyan); margin: 0.2rem 0 0.5rem; }
        .case-tag { color: var(--cyan); font: 800 0.66rem ui-monospace, Consolas, monospace; letter-spacing: 0.13em; margin-bottom: 0.3rem; }
        .case-title { color: var(--cream); font-weight: 850; font-size: 1.0rem; margin-bottom: 0.35rem; line-height: 1.25; }
        .case-desc { color: var(--muted); font-size: 0.80rem; line-height: 1.45; }

        /* ---------- documentation ---------- */
        .docs-section { margin-bottom: 2.1rem; }
        .docs-section h3 { color: var(--cyan); font-size: 0.88rem; letter-spacing: 0.08em; text-transform: uppercase;
                            border-bottom: 1px solid var(--line); padding-bottom: 0.55rem; margin-bottom: 0.9rem; }
        .docs-stat { display: inline-block; background: var(--panel); border: 1px solid var(--line); border-radius: 10px;
                     padding: 0.9rem 1.15rem; margin: 0 0.6rem 0.6rem 0; min-width: 150px; }
        .docs-stat b { color: var(--orange); font-size: 1.35rem; display: block; }
        .docs-stat span { color: var(--muted); font-size: 0.74rem; }
        .docs-table { width: 100%; border-collapse: collapse; font-size: 0.86rem; }
        .docs-table th { color: var(--cyan); text-align: left; font-size: 0.68rem; letter-spacing: 0.08em;
                          text-transform: uppercase; padding: 0.4rem 0.7rem; border-bottom: 1px solid var(--line-strong); }
        .docs-table td { color: var(--muted); padding: 0.5rem 0.7rem; border-bottom: 1px solid var(--line); vertical-align: top; }
        .docs-table td:first-child { color: var(--cream); font-weight: 700; white-space: nowrap; }

        /* ---------- about dialog ---------- */
        div[data-testid="stDialog"] { color: var(--cream); }
        .about-label { color: var(--orange); font-weight: 900; font-size: 0.7rem; letter-spacing: 0.14em; margin: 1rem 0 0.35rem; }
        .about-citation { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 0.85rem;
                           font-style: italic; color: var(--muted); font-size: 0.85rem; line-height: 1.5; }

        /* ---------- FINAL LAYOUT OVERRIDES ---------- */
        html, body, .stApp, [data-testid="stAppViewContainer"] {
            background:
              radial-gradient(circle at 24% 18%, rgba(126, 223, 224, 0.055), transparent 30%),
              radial-gradient(circle at 90% 10%, rgba(63, 189, 122, 0.035), transparent 34%),
              linear-gradient(180deg, #041e24 0%, #03151a 100%) !important;
        }
        [data-testid="stAppViewContainer"] { height: auto !important; }

        .block-container,
        [data-testid="stMainBlockContainer"] {
            box-sizing: border-box !important;
            width: min(1320px, calc(100vw - 96px)) !important;
            max-width: 1320px !important;
            margin: 2rem auto 3rem auto !important;
            height: auto !important;
            padding: 1.4rem 1.55rem 3rem !important;
            border-radius: 18px !important;
            border: 1px solid rgba(126, 223, 224, 0.16) !important;
            background:
              radial-gradient(circle at 24% 18%, rgba(126, 223, 224, 0.10), transparent 28%),
              linear-gradient(180deg, #0b3a40 0%, #082a30 100%) !important;
            box-shadow:
              0 32px 90px rgba(0, 0, 0, 0.32),
              inset 0 1px 0 rgba(255, 255, 255, 0.035) !important;
        }

        .top-right {
            display: flex;
            align-items: center;
            gap: 1.4rem;
        }

        /* custom About overlay */
        .about-overlay {
            position: fixed; inset: 0; z-index: 999999; display: flex; align-items: center; justify-content: center;
            background: rgba(3, 21, 26, 0.66); backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);
        }
        .about-card {
            position: relative; width: min(50vw, 640px); min-width: 390px; max-height: 82vh; overflow-y: auto;
            background: #f7f4ec; color: #17252b; border-radius: 18px; border: 1px solid rgba(11, 58, 64, 0.18);
            padding: 1.45rem 1.45rem 1.35rem; box-shadow: 0 32px 90px rgba(0, 0, 0, 0.46), 0 0 0 1px rgba(255, 255, 255, 0.65) inset;
        }
        .about-card h2 { margin: 0.2rem 0 0.9rem; color: #17252b; font-size: 1.55rem; letter-spacing: -0.03em; }
        .about-card p { color: #52636b; line-height: 1.6; font-size: 0.92rem; }
        .about-kicker, .about-label {
            color: #0b3a40; font-family: "IBM Plex Mono", ui-monospace, Consolas, monospace;
            font-size: 0.72rem; font-weight: 900; letter-spacing: 0.14em;
        }
        .about-label { margin: 1rem 0 0.35rem; }
        .about-citation {
            background: #ffffff; border: 1px solid rgba(11, 58, 64, 0.18); border-radius: 10px;
            padding: 0.9rem; font-style: italic; color: #52636b; font-size: 0.85rem; line-height: 1.5;
        }
        .about-close {
            position: absolute; top: 0.85rem; right: 1rem; color: #17252b; text-decoration: none;
            font-size: 1.45rem; line-height: 1; font-weight: 700;
        }
        .about-close:hover { color: #0b3a40; }

        /* ---------- simulator: metric cards ---------- */
        .metric-card {
            background: var(--panel); border: 1px solid var(--line); border-radius: 10px;
            padding: 1.05rem 1.2rem; height: 100%; box-sizing: border-box;
        }
        .metric-card .metric-label {
            display: block; color: var(--cyan); font-size: 0.68rem; font-weight: 800;
            letter-spacing: 0.10em; text-transform: uppercase; margin-bottom: 0.45rem;
        }
        .metric-card .metric-value {
            display: block; color: var(--gold); font-size: 1.5rem; font-weight: 900;
            letter-spacing: -0.01em; line-height: 1.15;
        }
        .metric-card .metric-unit { color: var(--muted); font-size: 0.7rem; font-weight: 700; margin-left: 0.25rem; }

        /* ---------- simulator: theme native input widgets ---------- */
        [data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] label {
            color: var(--cream) !important; font-weight: 700 !important; font-size: 0.82rem !important;
        }
        [data-baseweb="input"], [data-baseweb="select"] > div {
            background: rgba(5,25,31,0.45) !important; border-color: var(--line-strong) !important;
            color: var(--cream) !important; border-radius: 3px !important;
        }
        [data-baseweb="select"] div, [data-baseweb="select"] span { color: var(--cream) !important; }
        [role="listbox"] { background: #0a2c32 !important; border: 1px solid var(--line-strong) !important; }
        [role="option"] { color: var(--cream) !important; }
        [role="option"]:hover, [aria-selected="true"][role="option"] { background: rgba(126,223,224,0.14) !important; }
        [data-testid="stNumberInputStepUp"], [data-testid="stNumberInputStepDown"] {
            background: rgba(5,25,31,0.45) !important; border-color: var(--line-strong) !important; color: var(--cream) !important;
        }
        [data-baseweb="slider"] div[style*="background-color"] { background-color: var(--gold) !important; }
        [data-baseweb="slider"] [role="slider"] {
            background-color: var(--gold) !important; border-color: var(--gold) !important;
            box-shadow: 0 0 0 3px rgba(242, 184, 75, 0.25) !important;
        }
        [data-testid="stSlider"] [data-testid="stTickBarMin"],
        [data-testid="stSlider"] [data-testid="stTickBarMax"],
        [data-testid="stThumbValue"] { color: var(--muted) !important; }

        @media (max-width: 900px) {
            .block-container,
            [data-testid="stMainBlockContainer"] {
                width: min(100vw - 28px, 1320px) !important; margin: 0.75rem auto !important; padding: 1rem !important;
            }
            .about-card { width: min(92vw, 520px); min-width: 0; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def logo_svg(width: int = 196, height: int = 54) -> str:
    return f"""
    <svg width="{width}" height="{height}" viewBox="0 0 214 58" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="KidashiSim">
      <defs>
        <linearGradient id="kdRing" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="#7edfe0"/>
          <stop offset="55%" stop-color="#3fbd7a"/>
          <stop offset="100%" stop-color="#eba654"/>
        </linearGradient>
        <radialGradient id="kdCoin" cx="35%" cy="30%" r="80%">
          <stop offset="0%" stop-color="#d6f7f6"/>
          <stop offset="55%" stop-color="#7edfe0"/>
          <stop offset="100%" stop-color="#1c6f72"/>
        </radialGradient>
      </defs>
      <rect x="1.5" y="1.5" width="211" height="55" rx="27.5" fill="rgba(6,31,37,0.70)" stroke="url(#kdRing)" stroke-width="1.6"/>
      <g transform="translate(29,29)">
        <circle r="17" fill="url(#kdCoin)"/>
        <circle r="17" fill="none" stroke="rgba(255,255,255,0.30)" stroke-width="1"/>
        <g transform="translate(5,-6) rotate(18)">
          <path d="M0,-9 C6,-6 6,4 0,9 C-6,4 -6,-6 0,-9 Z" fill="#3fbd7a" stroke="#0b3a40" stroke-width="1"/>
          <line x1="0" y1="-7" x2="0" y2="7" stroke="#0b3a40" stroke-width="0.8"/>
        </g>
      </g>
      <text x="58" y="34" font-family="Inter, ui-sans-serif, sans-serif" font-size="19" letter-spacing="-0.02em">
        <tspan font-weight="900" fill="#f3efe4">KIDASHI</tspan><tspan font-weight="700" font-style="italic" fill="#eba654">sim</tspan>
      </text>
    </svg>
    """


def top_bar(lang: str, view: str, about_open: bool = False, show_crumb: bool = False) -> None:
    # EXPLICITLY set target="_self" so Streamlit never pushes these out to a new tab
    crumb_html = (
        f'<a class="crumb" href="{nav_url(lang=lang, view="home")}" target="_self">{STRINGS[lang]["crumb_back"]}</a>'
        if show_crumb else ""
    )
    lang_links = "".join(
        f'<a class="{"active" if code == lang else ""}" '
        f'href="{nav_url(lang=code, view=view, about=about_open)}" target="_self">{code}</a>'
        for code in LANGS
    )
    st.markdown(
        '<div class="top">'
        f'<div>{logo_svg()}</div>'
        '<div class="top-right">'
        f'{crumb_html}'
        f'<div class="langs">{lang_links}</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# About overlay
# ---------------------------------------------------------------------------

def render_about_overlay(lang: str, view: str) -> None:
    S = STRINGS[lang]
    close_href = nav_url(lang=lang, view=view)
    st.markdown(
        '<div class="about-overlay"><div class="about-card">'
        f'<a class="about-close" href="{close_href}" target="_self">\u00d7</a>'
        f'<div class="about-kicker">{S["about_kicker"]}</div>'
        f'<h2>{S["about_title"]}</h2>'
        f'<p>{S["about_intro"]}</p>'
        f'<div class="about-label">{S["about_author_label"]}</div>'
        '<p>Taiwo Adedeji Michael<br/>'
        'M.Sc. Agribusiness and Innovation, Mohammed VI Polytechnic University (UM6P)<br/>'
        'Agri-Food Systems &amp; Financial Inclusion Specialist, XchangeBox Solutions Ltd.</p>'
        f'<div class="about-label">{S["about_citation_label"]}</div>'
        '<div class="about-citation">Adedeji, Taiwo M. (2026). <i>KidashiABM \u2014 Agent-Based '
        'Modelling of Fintech-Led Liquidity Provision and Farmgate Price Resilience in Nigerian '
        'Staple Value Chains.</i> Source: github.com/Adedeji-Taiwo/kidashi_abm.</div>'
        f'<div class="about-label">{S["about_license_label"]}</div>'
        f'<p>{S["about_license"]}</p>'
        '</div></div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

def render_home(lang: str) -> None:
    S = STRINGS[lang]
    top_bar(lang, view="home")
    left, right = st.columns([1.05, 0.95], gap="large")

    with left:
        st.markdown(
            f'<div class="eyebrow">{S["hero_eyebrow"]}</div>'
            '<h1 class="title">KIDASHI<span>sim</span></h1>'
            '<div class="abm-badge">ABM</div>'
            f'<div class="lead">{S["hero_lead"]}</div>'
            f'<div class="copy">{S["hero_copy"]}</div>',
            unsafe_allow_html=True,
        )

        # -------------------------------------------------------------------------
        # THE FIX: By utilizing Streamlit's native button routing rather than HTML
        # hrefs, there are ZERO new tabs opened and ZERO query strings printed
        # in the address bar. It functions seamlessly inline.
        # -------------------------------------------------------------------------
        btn_col1, btn_col2, btn_col3, _ = st.columns([1, 1, 1, 1.2])

        with btn_col1:
            if st.button(S["btn_cases"], type="primary", use_container_width=True):
                st.session_state["view"] = "cases"
                st.rerun()

        with btn_col2:
            if st.button(S["btn_docs"], use_container_width=True):
                st.session_state["view"] = "docs"
                st.rerun()

        with btn_col3:
            if st.button(S["btn_about"], use_container_width=True):
                st.session_state["about_open"] = True
                st.rerun()

    with right:
        render_kidashi_live_figure(
            farmers=54,
            fintech_rate=0.41,
            shock_regime="baseline",
            maize_price=310_000,
            tomato_price=420_000,
            height=470,
        )


CASE_STUDIES = [
    {
        "flag": '<img class="flag-img" src="https://flagcdn.com/w40/ng.png" alt="Nigeria flag">',
        "status": "live",
        "tag": "FINTECH \u00b7 WEST AFRICA",
        "title": "Nigeria \u2014 Staple Value Chains",
        "desc": "Kidashi trust-circle credit, crop diversification and farmgate "
                "price resilience for selected crops under climate & trade shocks.",
        "icon": """<svg viewBox="0 0 64 64" width="34" height="34" fill="none" stroke="currentColor" stroke-width="1.6">
            <line x1="32" y1="10" x2="32" y2="52"/>
            <path d="M32,18 C38,15 42,19 40,24 C36,22 33,20 32,18Z" fill="currentColor" opacity="0.35"/>
            <path d="M32,18 C26,15 22,19 24,24 C28,22 31,20 32,18Z" fill="currentColor" opacity="0.35"/>
            <path d="M32,28 C38,25 42,29 40,34 C36,32 33,30 32,28Z" fill="currentColor" opacity="0.35"/>
            <path d="M32,28 C26,25 22,29 24,34 C28,32 31,30 32,28Z" fill="currentColor" opacity="0.35"/>
            <circle cx="32" cy="46" r="7"/>
        </svg>""",
    },
    {
        "flag": '<img class="flag-img" src="https://flagcdn.com/w40/gh.png" alt="Ghana flag">', "status": "soon", "tag": "FINTECH \u00b7 WEST AFRICA",
        "title": "Ghana \u2014 Cocoa Value Chain",
        "desc": "Simulate liquidity access, aggregator financing and farmgate "
                "price pass-through for smallholder cocoa producers.",
        "icon": """<svg viewBox="0 0 64 64" width="34" height="34" fill="none" stroke="currentColor" stroke-width="1.6">
            <path d="M32,10 C44,14 46,32 38,48 C35,54 29,54 26,48 C18,32 20,14 32,10Z"/>
            <line x1="32" y1="14" x2="32" y2="48"/>
            <line x1="26" y1="22" x2="38" y2="22"/>
            <line x1="24" y1="30" x2="40" y2="30"/>
            <line x1="24" y1="38" x2="40" y2="38"/>
        </svg>""",
    },
    {
        "flag": '<img class="flag-img" src="https://flagcdn.com/w40/ke.png" alt="Kenya flag">', "status": "soon", "tag": "FINTECH \u00b7 EAST AFRICA",
        "title": "Kenya \u2014 Horticulture Export",
        "desc": "Model cold-chain financing and export-channel liquidity for "
                "smallholder horticulture cooperatives.",
        "icon": """<svg viewBox="0 0 64 64" width="34" height="34" fill="none" stroke="currentColor" stroke-width="1.6">
            <circle cx="32" cy="24" r="6"/>
            <path d="M32,30 C32,40 28,46 24,52"/>
            <path d="M24,40 C18,38 16,32 20,28"/>
            <path d="M32,40 C36,44 42,44 46,40"/>
        </svg>""",
    },
    {
        "flag": '<img class="flag-img" src="https://flagcdn.com/w40/ma.png" alt="Morocco flag">', "status": "soon", "tag": "FINTECH · NORTH AFRICA",
        "title": "Morocco \u2014 Olive Value Chain",
        "desc": "Explore trust-circle credit uptake and distress-sale pressure "
                "across olive cooperatives under trade shocks.",
        "icon": """<svg viewBox="0 0 64 64" width="34" height="34" fill="none" stroke="currentColor" stroke-width="1.6">
            <ellipse cx="32" cy="20" rx="10" ry="12"/>
            <ellipse cx="32" cy="44" rx="10" ry="12"/>
        </svg>""",
    },
]


def render_cases(lang: str) -> None:
    S = STRINGS[lang]
    top_bar(lang, view="cases", show_crumb=True)
    st.markdown(
        f'<div class="page-head"><div class="eyebrow">{S["cases_eyebrow"]}</div>'
        f'<h1>{S["cases_title"]}</h1><p>{S["cases_sub"]}</p></div>',
        unsafe_allow_html=True,
    )
    cols = st.columns(4, gap="medium")
    for col, study in zip(cols, CASE_STUDIES):
        with col:
            badge = (f'<span class="case-badge live">{S["badge_live"]}</span>' if study["status"] == "live"
                     else f'<span class="case-badge soon">{S["badge_soon"]}</span>')
            st.markdown(
                '<div class="case-card">'
                f'<div class="case-card-top"><span class="case-flag">{study["flag"]}</span>{badge}</div>'
                f'<div class="case-icon">{study["icon"]}</div>'
                f'<div class="case-tag">{study["tag"]}</div>'
                f'<div class="case-title">{study["title"]}</div>'
                f'<div class="case-desc">{study["desc"]}</div>'
                '</div>',
                unsafe_allow_html=True,
            )
            st.write("")
            if study["status"] == "live":
                # In-page navigation (same pattern as the hero buttons) --
                # this intentionally does NOT use st.link_button, so it
                # never opens a new tab and never prints a query string.
                if st.button(
                    S["launch_simulator"],
                    key=f"launch_{study['title']}",
                    type="primary",
                    use_container_width=True,
                ):
                    st.session_state["view"] = "simulator"
                    st.rerun()
            else:
                st.button(
                    S["coming_soon"],
                    key=f"soon_{study['title']}",
                    disabled=True,
                    use_container_width=True,
                )


def render_docs(lang: str) -> None:
    S = STRINGS[lang]
    top_bar(lang, view="docs", show_crumb=True)
    st.markdown(
        f'<div class="page-head"><div class="eyebrow">{S["docs_eyebrow"]}</div>'
        f'<h1>{S["docs_title"]}</h1><p>{S["docs_sub"]}</p></div>',
        unsafe_allow_html=True,
    )

    if MANUAL_PDF_PATH.exists():
        st.download_button(
            S["docs_download"],
            data=MANUAL_PDF_PATH.read_bytes(),
            file_name=MANUAL_PDF_PATH.name,
            mime="application/pdf",
        )
    else:
        st.caption(S["docs_download_missing"])
    st.write("")

    st.markdown(
        f'<div class="docs-section"><h3>{S["docs_overview_h"]}</h3>', unsafe_allow_html=True)
    st.markdown(S["docs_overview_p"])
    c1, c2, c3 = st.columns(3)
    c1.markdown(
        f'<div class="docs-stat"><b>55%</b><span>{S["stat1"]}</span></div>', unsafe_allow_html=True)
    c2.markdown(
        f'<div class="docs-stat"><b>18.6%</b><span>{S["stat2"]}</span></div>', unsafe_allow_html=True)
    c3.markdown(
        f'<div class="docs-stat"><b>&lt;72h</b><span>{S["stat3"]}</span></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(
        f'<div class="docs-section"><h3>{S["docs_agents_h"]}</h3>', unsafe_allow_html=True)
    st.markdown(
        '<table class="docs-table">'
        f'<tr><th>{S["th_agent"]}</th><th>{S["th_count"]}</th><th>{S["th_behaviours"]}</th></tr>'
        '<tr><td>Farmer</td><td>100&ndash;1000</td><td>Adaptive mean-variance crop allocation (maize/sorghum/tomato); weather-correlated stochastic production; multi-channel sales with distress-discount mechanism</td></tr>'
        '<tr><td>FintechProvider</td><td>1</td><td>Trust-circle credit scoring; Kidashi / Farm-to-Factory disbursement logic; Portfolio-at-Risk (PAR30) tracking</td></tr>'
        '<tr><td>Trader</td><td>5&ndash;20</td><td>Aggregator/processor procurement; two-scenario spoilage modelling; export-channel price transmission</td></tr>'
        '</table>',
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(
        f'<div class="docs-section"><h3>{S["docs_shocks_h"]}</h3>', unsafe_allow_html=True)
    st.markdown(
        '<table class="docs-table">'
        f'<tr><th>{S["th_regime"]}</th><th>{S["th_weather"]}</th><th>{S["th_trade"]}</th><th>{S["th_magnitude"]}</th></tr>'
        '<tr><td>baseline</td><td>Low (\u03c3=0.20)</td><td>Low (8%)</td><td>&plusmn;15%</td></tr>'
        '<tr><td>climate_stress</td><td>High (\u03c3=0.45)</td><td>Low (8%)</td><td>&plusmn;15%</td></tr>'
        '<tr><td>trade_disruption</td><td>Low (\u03c3=0.20)</td><td>High (25%)</td><td>&plusmn;35%</td></tr>'
        '<tr><td>compound</td><td>High (\u03c3=0.45)</td><td>High (25%)</td><td>&plusmn;35%</td></tr>'
        '</table>',
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(
        f'<div class="docs-section"><h3>{S["docs_policy_h"]}</h3>', unsafe_allow_html=True)
    st.markdown(
        f"- **none** \u2014 {S['policy_none']}\n"
        f"- **incentive** \u2014 {S['policy_incentive']}\n"
        f"- **mandate** \u2014 {S['policy_mandate']}"
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # GitHub links correctly pop into new tabs
    st.link_button(S["docs_github"].replace("&amp;", "&"), GITHUB_URL)


# ---------------------------------------------------------------------------
# Simulator: chart theming helpers
# ---------------------------------------------------------------------------

_CHART_BG = "#0a2c32"
_CHART_GRID = "#1c4a50"
_CHART_TEXT = "#dcecEB"
_CHART_MUTED = "#93b3b1"
_CHART_GOLD = "#f2b84b"
_CHART_CYAN = "#7edfe0"
_CHART_GREEN = "#3fbd7a"
_CHART_ORANGE = "#eba654"


def _themed_fig(figsize: tuple = (9, 3.2)):
    """A matplotlib figure/axes pair pre-styled to match the app's dark palette."""
    fig, ax = plt.subplots(figsize=figsize, dpi=140)
    fig.patch.set_facecolor(_CHART_BG)
    ax.set_facecolor(_CHART_BG)
    ax.tick_params(colors=_CHART_MUTED, labelsize=8.5)
    for spine in ax.spines.values():
        spine.set_color(_CHART_GRID)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, color=_CHART_GRID, linewidth=0.7, alpha=0.6)
    ax.set_axisbelow(True)
    return fig, ax


def _style_legend(ax):
    # loc="best" (rather than a fixed corner) because the data shape varies
    # scenario to scenario -- and it stays inside the axes bbox on purpose,
    # so it can never be clipped regardless of how the host crops the figure.
    leg = ax.legend(loc="best", frameon=True, fontsize=8.5,
                    labelcolor=_CHART_TEXT, handlelength=1.4)
    leg.get_frame().set_facecolor(_CHART_BG)
    leg.get_frame().set_edgecolor(_CHART_GRID)
    leg.get_frame().set_alpha(0.88)
    return leg


def _scaled_ngn_formatter(max_val: float) -> FuncFormatter:
    """Y-axis tick formatter that scales to k/M so labels stay readable."""
    if max_val >= 1_000_000:
        return FuncFormatter(lambda x, _pos: f"{x/1_000_000:,.1f}M")
    if max_val >= 1_000:
        return FuncFormatter(lambda x, _pos: f"{x/1_000:,.0f}k")
    return FuncFormatter(lambda x, _pos: f"{x:,.0f}")


def _format_ngn(value: float) -> str:
    """Compact Naira string for metric cards, e.g. 105154855 -> '\u20a6105.2M'."""
    sign = "-" if value < 0 else ""
    value = abs(value)
    if value >= 1_000_000:
        return f"{sign}\u20a6{value/1_000_000:,.1f}M"
    if value >= 1_000:
        return f"{sign}\u20a6{value/1_000:,.1f}k"
    return f"{sign}\u20a6{value:,.0f}"


def _metric_card(label: str, value: str, unit: str = "") -> str:
    unit_html = f'<span class="metric-unit">{unit}</span>' if unit else ""
    return (
        '<div class="metric-card">'
        f'<span class="metric-label">{label}</span>'
        f'<span class="metric-value">{value}{unit_html}</span>'
        '</div>'
    )


# ---------------------------------------------------------------------------
# Simulator: cached model run
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def run_simulation(
    steps: int,
    num_farmers: int,
    num_traders: int,
    fintech_penetration: float,
    diversity_policy: str,
    shock_regime: str,
    trade_openness: float,
    seed: int,
):
    """Run KidashiModel for `steps` seasons and return the model-level dataframe.

    Cached on its (scalar, hashable) arguments -- re-running the exact same
    scenario again is instant instead of re-simulating from scratch.
    """
    model = KidashiModel(
        num_farmers=num_farmers,
        num_traders=num_traders,
        fintech_penetration=fintech_penetration,
        diversity_policy=diversity_policy,
        shock_regime=shock_regime,
        trade_openness=trade_openness,
        seed=seed,
    )
    for _ in range(steps):
        model.step()
    return model.datacollector.get_model_vars_dataframe()


# ---------------------------------------------------------------------------
# Simulator view
# ---------------------------------------------------------------------------

def render_simulator(lang: str) -> None:
    S = STRINGS[lang]
    top_bar(lang, view="simulator", show_crumb=True)
    st.markdown(
        f'<div class="page-head"><div class="eyebrow">{S["sim_eyebrow"]}</div>'
        f'<h1>{S["sim_title"]}</h1><p>{S["sim_sub"]}</p></div>',
        unsafe_allow_html=True,
    )

    # -- Controls -----------------------------------------------------------
    st.markdown(
        f'<div class="docs-section"><h3>{S["sim_controls_h"]}</h3>', unsafe_allow_html=True)

    r1c1, r1c2, r1c3, r1c4 = st.columns(4)
    with r1c1:
        steps = st.slider(S["sim_steps"], 10, 80, 40)
    with r1c2:
        num_farmers = st.slider(S["sim_num_farmers"], 50, 500, 100)
    with r1c3:
        num_traders = st.slider(S["sim_num_traders"], 5, 20, 10)
    with r1c4:
        seed = int(st.number_input(S["sim_seed"], value=42, step=1))

    r2c1, r2c2, r2c3, r2c4 = st.columns(4)
    with r2c1:
        fintech_penetration = st.slider(S["sim_fintech"], 0.0, 1.0, 0.40)
    with r2c2:
        trade_openness = st.slider(S["sim_trade_openness"], 0.0, 1.0, 0.20)
    with r2c3:
        diversity_policy = st.selectbox(
            S["sim_diversity_policy"], ["none", "incentive", "mandate"])
    with r2c4:
        shock_regime = st.selectbox(
            S["sim_shock_regime"],
            ["baseline", "climate_stress", "trade_disruption", "compound"])

    st.markdown('</div>', unsafe_allow_html=True)

    run_clicked = st.button(S["sim_run_btn"], type="primary")

    if run_clicked:
        with st.spinner(S["sim_running"]):
            model_df = run_simulation(
                steps=steps,
                num_farmers=num_farmers,
                num_traders=num_traders,
                fintech_penetration=fintech_penetration,
                diversity_policy=diversity_policy,
                shock_regime=shock_regime,
                trade_openness=trade_openness,
                seed=seed,
            )
        st.session_state["sim_model_df"] = model_df
        st.session_state["sim_last_params"] = dict(
            steps=steps, num_farmers=num_farmers, num_traders=num_traders,
            shock_regime=shock_regime, diversity_policy=diversity_policy, seed=seed,
        )

    model_df = st.session_state.get("sim_model_df")

    # -- Results --------------------------------------------------------
    st.markdown(
        '<div class="page-head" style="margin-top:2.2rem;">'
        f'<div class="eyebrow">{S["sim_results_eyebrow"]}</div>'
        f'<h1>{S["sim_results_title"]}</h1></div>',
        unsafe_allow_html=True,
    )

    if model_df is None or model_df.empty:
        st.caption(S["sim_empty_state"])
        return

    p = st.session_state["sim_last_params"]
    st.caption(
        f"{S['sim_steps']}: {p['steps']}  \u00b7  {S['sim_num_farmers']}: {p['num_farmers']}  \u00b7  "
        f"{S['sim_num_traders']}: {p['num_traders']}  \u00b7  {S['sim_shock_regime']}: {p['shock_regime']}  \u00b7  "
        f"{S['sim_diversity_policy']}: {p['diversity_policy']}  \u00b7  {S['sim_seed']}: {p['seed']}"
    )

    last = model_df.iloc[-1]

    # -- Metric cards -----------------------------------------------------
    cards = [
        (S["metric_wealth"], _format_ngn(last["mean_wealth"]), ""),
        (S["metric_maize"], _format_ngn(last["price_maize"]), "/MT"),
        (S["metric_sorghum"], _format_ngn(last["price_sorghum"]), "/MT"),
        (S["metric_tomato"], _format_ngn(last["price_tomato"]), "/MT"),
        (S["metric_diversity"], f"{last['mean_diversity_index']:.2f}", ""),
        (S["metric_par30"], f"{last['par30'] * 100:.1f}%", ""),
    ]
    row1 = st.columns(3, gap="medium")
    for col, (label, value, unit) in zip(row1, cards[:3]):
        col.markdown(_metric_card(label, value, unit), unsafe_allow_html=True)
    row2 = st.columns(3, gap="medium")
    for col, (label, value, unit) in zip(row2, cards[3:]):
        col.markdown(_metric_card(label, value, unit), unsafe_allow_html=True)

    st.write("")

    # -- Chart 1: farmgate prices over time --------------------------------
    st.markdown(
        f'<div class="docs-section"><h3>{S["chart_prices_title"]}</h3>', unsafe_allow_html=True)
    fig, ax = _themed_fig()
    price_cols = ["price_maize", "price_sorghum", "price_tomato"]
    fmt = _scaled_ngn_formatter(float(model_df[price_cols].values.max()))
    ax.plot(model_df["step"], model_df["price_maize"],
            color=_CHART_GOLD, linewidth=2, label=S["crop_maize"])
    ax.plot(model_df["step"], model_df["price_sorghum"],
            color=_CHART_CYAN, linewidth=2, label=S["crop_sorghum"])
    ax.plot(model_df["step"], model_df["price_tomato"],
            color=_CHART_GREEN, linewidth=2, label=S["crop_tomato"])
    ax.yaxis.set_major_formatter(fmt)
    ax.set_xlabel(S["axis_step"], color=_CHART_MUTED, fontsize=9)
    ax.set_ylabel(S["axis_price"], color=_CHART_MUTED, fontsize=9)
    _style_legend(ax)
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)
    st.markdown('</div>', unsafe_allow_html=True)

    # -- Chart 2: mean farmer wealth over time -----------------------------
    st.markdown(
        f'<div class="docs-section"><h3>{S["chart_wealth_title"]}</h3>', unsafe_allow_html=True)
    fig, ax = _themed_fig()
    fmt = _scaled_ngn_formatter(float(model_df["mean_wealth"].values.max()))
    ax.plot(model_df["step"], model_df["mean_wealth"],
            color=_CHART_ORANGE, linewidth=2.2)
    ax.fill_between(model_df["step"], model_df["mean_wealth"],
                    color=_CHART_ORANGE, alpha=0.10)
    ax.yaxis.set_major_formatter(fmt)
    ax.set_xlabel(S["axis_step"], color=_CHART_MUTED, fontsize=9)
    ax.set_ylabel(S["axis_wealth"], color=_CHART_MUTED, fontsize=9)
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)
    st.markdown('</div>', unsafe_allow_html=True)

    # -- Chart 3: diversity index over time ---------------------------------
    st.markdown(
        f'<div class="docs-section"><h3>{S["chart_diversity_title"]}</h3>', unsafe_allow_html=True)
    fig, ax = _themed_fig()
    ax.plot(model_df["step"], model_df["mean_diversity_index"],
            color=_CHART_GREEN, linewidth=2.2)
    ax.fill_between(
        model_df["step"], model_df["mean_diversity_index"], color=_CHART_GREEN, alpha=0.10)
    ax.set_ylim(bottom=0)
    ax.set_xlabel(S["axis_step"], color=_CHART_MUTED, fontsize=9)
    ax.set_ylabel(S["axis_diversity"], color=_CHART_MUTED, fontsize=9)
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)
    st.markdown('</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

def main() -> None:
    # 1. Initialize State & Clear URL signals
    init_navigation_state()

    # 2. Inject CSS
    inject_css()

    # 3. Pull current navigation state from session
    lang = st.session_state["lang"]
    view = st.session_state["view"]
    about_open = st.session_state["about_open"]

    # 4. Route to Views
    if view == "cases":
        render_cases(lang)
    elif view == "docs":
        render_docs(lang)
    elif view == "simulator":
        render_simulator(lang)
    else:
        render_home(lang)

    # 5. Render Modal (if active)
    if about_open:
        render_about_overlay(lang, view)


if __name__ == "__main__":
    main()
