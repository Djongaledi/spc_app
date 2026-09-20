import streamlit as st
import sqlite3
import pandas as pd
import random
from datetime import datetime
import base64
from io import BytesIO

from database import DB_NAME, NIVEAUX_SPC
from utils_qr import generer_qr_code

st.set_page_config(page_title="Espace Administration - SPC", page_icon="🔑", layout="wide")

# CSS de la barre latérale et des éléments de page
st.markdown("""
    <style>
    .stApp { background-color: #F8FAFC; }
    
    section[data-testid="stSidebar"] {
        background-color: #0F172A !important;
        border-right: 3px solid #F59E0B !important;
    }

    section[data-testid="stSidebar"] *, 
    section[data-testid="stSidebar"] p, 
    section[data-testid="stSidebar"] span, 
    section[data-testid="stSidebar"] div {
        color: #FFFFFF !important;
    }

    section[data-testid="stSidebar"] ul li div a {
        background-color: #1E293B !important;
        border-radius: 8px !important;
        padding: 10px 14px !important;
        margin-bottom: 8px !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }

    section[data-testid="stSidebar"] ul li div a[aria-current="page"] {
        background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%) !important;
        color: #0F172A !important;
        font-weight: 800 !important;
        border-left: 4px solid #FFFFFF !important;
    }

    .stButton>button, div[data-testid="stFormSubmitButton"]>button {
        background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%) !important;
        color: #0F172A !important;
        font-weight: 800 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 20px !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🔑 ESPACE ADMINISTRATION")

tab_scan, tab_stats, tab_inscrire, tab_cartes, tab_lists = st.tabs([
    "📸 Scanner & Présences", 
    "📊 Statistiques & Dashboard", 
    "➕ Inscrire un Apprenant", 
    "🪪 Imprimer Carte Apprenant",
    "📋 Listes & Exports PDF"
])

# --- ONGLET 3 : INSCRIPTION APPRENANT (RÉSERVÉ À L'ADMIN) ---
with tab_inscrire:
    st.subheader("➕ Formulaire d'Inscription Apprenant")
    
    with st.form("form_admin_inscription", clear_on_submit=True):
        nom = st.text_input("Nom complet de l'apprenant (Nom, Postnom, Prénom)")
        sexe = st.selectbox("Sexe", ["Masculin", "Féminin"])
        niveau = st.selectbox("Niveau d'étude / Groupe", NIVEAUX_SPC)
        submitted = st.form_submit_button("💾 Enregistrer l'Inscription")

    if submitted:
        nom_clean = nom.strip()
        if nom_clean != "":
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT matricule FROM apprenants WHERE LOWER(nom) = LOWER(?)", (nom_clean,))
            existe = c.fetchone()

            if existe:
                st.error(f"⚠️ L'apprenant **'{nom_clean}'** existe déjà avec le matricule **{existe[0]}**.")
                conn.close()
            else:
                matricule = f"SPC-{random.randint(1000, 9999)}"
                date_inscription = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                c.execute(
                    "INSERT INTO apprenants (matricule, nom, sexe, niveau, qr_code_path, date_inscription) VALUES (?, ?, ?, ?, ?, ?)",
                    (matricule, nom_clean, sexe, niveau, matricule, date_inscription)
                )
                conn.commit()
                conn.close()
                st.success(f"🎉 Apprenant **{nom_clean}** inscrit avec succès ! Matricule : **{matricule}**")
        else:
            st.error("❌ Veuillez saisir le nom complet.")

# --- ONGLET 4 : IMPRESSION DE LA CARTE APPRENANT (STYLE CARTE D'ÉTUDIANT) ---
with tab_cartes:
    st.subheader("🪪 Générer et Imprimer la Carte de l'Apprenant")
    
    conn = sqlite3.connect(DB_NAME)
    df_apprenants = pd.read_sql_query("SELECT matricule, nom FROM apprenants ORDER BY nom ASC", conn)
    conn.close()

    if not df_apprenants.empty:
        options = [f"{row['nom']} ({row['matricule']})" for _, row in df_apprenants.iterrows()]
        choix = st.selectbox("Sélectionnez l'apprenant :", options)
        
        if choix:
            mat_sel = choix.split("(")[-1].replace(")", "").strip()
            
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT matricule, nom, sexe, niveau, date_inscription FROM apprenants WHERE matricule = ?", (mat_sel,))
            app_data = c.fetchone()
            conn.close()

            if app_data:
                mat, nom_app, sexe_app, niv_app, date_ins = app_data
                
                # Option photo d'identité
                uploaded_photo = st.file_uploader("📷 Charger la photo d'identité de l'apprenant (optionnel)", type=["jpg", "png", "jpeg"])
                
                if uploaded_photo:
                    photo_bytes = uploaded_photo.getvalue()
                    b64_photo = f"data:image/png;base64,{base64.b64encode(photo_bytes).decode()}"
                else:
                    # Photo par défaut si aucune photo n'est chargée
                    b64_photo = "https://via.placeholder.com/110x130?text=PHOTO"

                # Génération QR Code en Base64
                qr_img = generer_qr_code(mat)
                b64_qr = f"data:image/png;base64,{base64.b64encode(qr_img).decode()}"

                annee_scolaire = "2025-2026"

                # Structure de la Carte D'étudiant / Apprenant (CSS HTML inspiré du modèle)
                carte_html = f"""
                <div id="carte-print" style="
                    width: 380px;
                    height: 580px;
                    border: 2px solid #1E3A8A;
                    border-radius: 12px;
                    background: #FFFFFF;
                    font-family: 'Arial', sans-serif;
                    padding: 15px;
                    box-shadow: 0px 4px 12px rgba(0,0,0,0.15);
                    position: relative;
                    margin: auto;
                    color: #0F172A;
                ">
                    <!-- EN-TÊTE -->
                    <div style="text-align: center; border-bottom: 2px solid #1E3A8A; padding-bottom: 8px;">
                        <div style="font-weight: 900; font-size: 14px; color: #1E3A8A; letter-spacing: 0.5px;">CENTRE DE FORMATION</div>
                        <div style="font-weight: 800; font-size: 16px; color: #F59E0B;">SMART PEOPLE CENTER</div>
                        <div style="font-size: 11px; font-weight: bold; color: #1E3A8A; margin-top: 4px; text-transform: uppercase; background: #EEF2FF; padding: 2px 6px; border-radius: 4px; display: inline-block;">
                            CARTE D'APPRENANT
                        </div>
                    </div>

                    <!-- PHOTO & ANNÉE ACADÉMIQUE -->
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 15px; padding: 0 10px;">
                        <div style="width: 110px; height: 130px; border: 2px solid #CBD5E1; border-radius: 6px; overflow: hidden; background: #F1F5F9;">
                            <img src="{b64_photo}" style="width: 100%; height: 100%; object-fit: cover;">
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 12px; font-weight: bold; color: #64748B;">Année d'étude</div>
                            <div style="font-size: 15px; font-weight: 900; color: #0F172A;">{annee_scolaire}</div>
                        </div>
                    </div>

                    <!-- INFORMATIONS PERSONNELLES -->
                    <div style="margin-top: 15px; font-size: 12px; line-height: 1.5;">
                        <div style="font-size: 11px; font-weight: bold; color: #64748B;">Nom / Postnom / Prénom</div>
                        <div style="font-weight: 800; font-size: 13px; color: #1E3A8A; margin-bottom: 6px;">{nom_app.upper()}</div>

                        <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                            <div>
                                <span style="font-size: 11px; font-weight: bold; color: #64748B;">Matricule : </span>
                                <span style="font-weight: 800; color: #D97706;">{mat}</span>
                            </div>
                            <div>
                                <span style="font-size: 11px; font-weight: bold; color: #64748B;">Sexe : </span>
                                <span style="font-weight: 800;">{sexe_app}</span>
                            </div>
                        </div>

                        <div style="margin-bottom: 6px;">
                            <span style="font-size: 11px; font-weight: bold; color: #64748B;">Niveau / Programme : </span><br>
                            <span style="font-weight: 800; color: #0F172A;">{niv_app}</span>
                        </div>
                    </div>

                    <!-- QR CODE & PIED DE PAGE -->
                    <div style="position: absolute; bottom: 15px; left: 15px; right: 15px; text-align: center; border-top: 1px dashed #CBD5E1; padding-top: 10px;">
                        <img src="{b64_qr}" style="width: 80px; height: 80px;">
                        <div style="font-size: 9px; color: #64748B; margin-top: 4px;">Valide pour l'année académique en cours</div>
                    </div>
                </div>
                """

                # Aperçu visuel de la carte dans Streamlit
                st.write("### 🖨️ Aperçu de la Carte")
                st.components.v1.html(carte_html, height=620)

                # Bouton pour imprimer la carte directement
                st.download_button(
                    label="📥 Télécharger la Carte (HTML/Imprimable)",
                    data=carte_html,
                    file_name=f"Carte_{mat}.html",
                    mime="text/html"
                )
    else:
        st.info("Aucun apprenant enregistré dans la base de données pour l'instant.")






