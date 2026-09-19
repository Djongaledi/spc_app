import streamlit as st
import sqlite3
import pandas as pd
import datetime
import sys
import os

sys.path.append(os.path.abspath(".."))
from database import DB_NAME, NIVEAUX_SPC
from utils_pdf import generer_pdf_presences

# Importation sécurisée du scanner QR code
try:
    from streamlit_qrcode_scanner import qrcode_scanner
    HAS_SCANNER = True
except ImportError:
    HAS_SCANNER = False

st.set_page_config(page_title="Espace Administration - SPC", page_icon="🔐", layout="wide")

# Style CSS du menu et de l'interface
st.markdown("""
    <style>
    .stApp { background-color: #F8FAFC; }
    
    section[data-testid="stSidebar"] {
        background-color: #0F172A !important;
        border-right: 3px solid #F59E0B !important;
    }
    section[data-testid="stSidebar"] * { color: #FFFFFF !important; }

    section[data-testid="stSidebar"] a {
        background-color: #1E293B !important;
        color: #FFFFFF !important;
        font-size: 0.95rem !important;
        font-weight: 700 !important;
        padding: 12px 16px !important;
        border-radius: 8px !important;
        border-left: 4px solid #F59E0B !important;
    }

    .stButton>button, div[data-testid="stFormSubmitButton"]>button, .stDownloadButton>button {
        background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%) !important;
        color: #0F172A !important;
        font-weight: 800 !important;
        border: none !important;
        border-radius: 8px !important;
    }

    .admin-header {
        background: linear-gradient(135deg, #1E3A8A 0%, #0F172A 100%);
        padding: 20px;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
        border: 2px solid #F59E0B;
    }
    </style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("""
        <div style="text-align:center; padding: 10px 0;">
            <h2 style="color:#F59E0B !important; margin:0; font-size:1.3rem;">📍 NAVIGATION</h2>
        </div>
        <hr style="border-color:#334155;">
    """, unsafe_allow_html=True)

st.markdown("""
    <div class="admin-header">
        <h1 style="margin:0; font-size:2rem; font-weight:800;">🔐 ESPACE ADMINISTRATION</h1>
        <p style="margin:5px 0 0 0; color:#FBBF24;">Gestion des présences, scans et rapports PDF</p>
    </div>
""", unsafe_allow_html=True)

tab_scan, tab_registre = st.tabs(["📷 Contrôle des Entrées (Scan)", "🤝 Registre Global & Historique"])

# --- ONGLET 1 : SCANNER ET MARQUAGE DES PRÉSENCES ---
with tab_scan:
    st.markdown("### 📷 Contrôle des Entrées par QR Code")
    col_scan, col_manuel = st.columns([2, 1])

    with col_scan:
        st.subheader("Scanner la carte/badge")
        if HAS_SCANNER:
            qr_code_scanne = qrcode_scanner(key="qr_scanner_admin")
            if qr_code_scanne:
                matricule_clean = qr_code_scanne.strip()
                
                # Vérifier si l'apprenant existe
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute("SELECT nom FROM apprenants WHERE matricule = ?", (matricule_clean,))
                apprenant = c.fetchone()
                
                if apprenant:
                    date_jour = datetime.date.today().strftime("%Y-%m-%d")
                    heure_actuelle = datetime.datetime.now().strftime("%H:%M:%S")
                    
                    # Vérifier si la présence est déjà marquée aujourd'hui
                    c.execute("SELECT id FROM presences WHERE matricule = ? AND date_presence = ?", (matricule_clean, date_jour))
                    deja_present = c.fetchone()
                    
                    if not deja_present:
                        c.execute("INSERT INTO presences (matricule, date_presence, heure_presence) VALUES (?, ?, ?)",
                                  (matricule_clean, date_jour, heure_actuelle))
                        conn.commit()
                        st.success(f"✅ Présence enregistrée pour **{apprenant[0]}** (`{matricule_clean}`) à {heure_actuelle}")
                    else:
                        st.warning(f"⚠️ **{apprenant[0]}** a déjà été marqué(e) présent(e) aujourd'hui.")
                else:
                    st.error(f"❌ Matricule `{matricule_clean}` inconnu dans la base de données.")
                conn.close()
        else:
            st.warning("⚠️ Module de scan indisponible. Installez `streamlit-qrcode-scanner` dans `requirements.txt`.")

    with col_manuel:
        st.subheader("Saisie Manuelle de Secours")
        with st.form("form_saisie_manuelle", clear_on_submit=True):
            matricule_manuel = st.text_input("Saisir un matricule (ex: SPC-4825)").strip()
            submit_manuel = st.form_submit_button("✅ Marquer Présent Manuellement")

        if submit_manuel and matricule_manuel:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT nom FROM apprenants WHERE matricule = ?", (matricule_manuel,))
            apprenant = c.fetchone()

            if apprenant:
                date_jour = datetime.date.today().strftime("%Y-%m-%d")
                heure_actuelle = datetime.datetime.now().strftime("%H:%M:%S")
                
                c.execute("SELECT id FROM presences WHERE matricule = ? AND date_presence = ?", (matricule_manuel, date_jour))
                deja_present = c.fetchone()
                
                if not deja_present:
                    c.execute("INSERT INTO presences (matricule, date_presence, heure_presence) VALUES (?, ?, ?)",
                              (matricule_manuel, date_jour, heure_actuelle))
                    conn.commit()
                    st.success(f"✅ Présence manuelle enregistrée pour **{apprenant[0]}** !")
                else:
                    st.warning(f"⚠️ **{apprenant[0]}** est déjà marqué(e) présent(e) aujourd'hui.")
            else:
                st.error("❌ Aucun apprenant trouvé avec ce matricule.")
            conn.close()

    st.write("---")
    st.markdown("### 📋 Liste des Présences du Jour")
    conn = sqlite3.connect(DB_NAME)
    date_aujourdhui = datetime.date.today().strftime("%Y-%m-%d")
    query_jour = """
        SELECT p.matricule, a.nom, a.niveau, a.sexe, p.heure_presence
        FROM presences p
        LEFT JOIN apprenants a ON p.matricule = a.matricule
        WHERE p.date_presence = ?
        ORDER BY p.id DESC
    """
    df_jour = pd.read_sql_query(query_jour, conn, params=(date_aujourdhui,))
    conn.close()
    st.dataframe(df_jour, use_container_width=True)

# --- ONGLET 2 : REGISTRE GLOBAL & FILTRES & IMPRESSION PDF ---
with tab_registre:
    st.markdown("### 🤝 Registre Global & Historique des Présences")

    # --- SECTION FILTRES ---
    col_f1, col_f2, col_f3 = st.columns(3)

    with col_f1:
        filtre_niveau = st.selectbox("Filtrer par Niveau", ["Tous"] + NIVEAUX_SPC)

    with col_f2:
        filtre_sexe = st.selectbox("Filtrer par Sexe", ["Tous", "Masculin", "Féminin"])

    with col_f3:
        filtre_date = st.date_input("Filtrer par Date", value=None)

    # --- REQUÊTE BASE DE DONNÉES ---
    conn = sqlite3.connect(DB_NAME)
    query = """
        SELECT p.matricule, a.nom, a.niveau, a.sexe, p.date_presence, p.heure_presence
        FROM presences p
        LEFT JOIN apprenants a ON p.matricule = a.matricule
        WHERE 1=1
    """
    params = []

    if filtre_niveau != "Tous":
        query += " AND a.niveau = ?"
        params.append(filtre_niveau)

    if filtre_sexe != "Tous":
        query += " AND a.sexe = ?"
        params.append(filtre_sexe)

    if filtre_date is not None:
        query += " AND p.date_presence = ?"
        params.append(str(filtre_date))

    query += " ORDER BY p.id DESC"

    df_historique = pd.read_sql_query(query, conn, params=params)
    conn.close()

    # --- AFFICHAGE TABLEAU ---
    st.dataframe(df_historique, use_container_width=True)

    # --- BOUTON DE TÉLÉCHARGEMENT PDF ---
    if not df_historique.empty:
        try:
            pdf_bytes = generer_pdf_presences(df_historique, titre="Registre des Presences Filtre")
            
            st.download_button(
                label="📄 Imprimer / Télécharger la liste en PDF",
                data=pdf_bytes,
                file_name=f"presences_spc_{datetime.date.today()}.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"Erreur lors de la génération du PDF : {e}")
    else:
        st.info("Aucun enregistrement ne correspond aux filtres sélectionnés.")







