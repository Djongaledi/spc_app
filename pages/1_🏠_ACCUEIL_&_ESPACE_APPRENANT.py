import streamlit as st
import sqlite3
import pandas as pd
import sys
import os

sys.path.append(os.path.abspath(".."))
from database import DB_NAME
from utils_qr import generer_qr_code

st.set_page_config(page_title="Espace Apprenant - SPC", page_icon="🎓", layout="wide")

# CSS Apprenant
st.markdown("""
    <style>
    .stApp { background-color: #F8FAFC; }
    
    /* MENU LATÉRAL FONCÉ */
    section[data-testid="stSidebar"] {
        background-color: #0F172A !important;
        border-right: 3px solid #F59E0B !important;
    }
    section[data-testid="stSidebar"] * { color: #F8FAFC !important; }
    
    /* BOUTONS JAUNES */
    .stButton>button, div[data-testid="stFormSubmitButton"]>button, .stDownloadButton>button {
        background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%) !important;
        color: #0F172A !important;
        font-weight: 800 !important;
        border: none !important;
        border-radius: 8px !important;
        box-shadow: 0px 4px 10px rgba(245, 158, 11, 0.3) !important;
    }

    /* EN-TÊTE APPRENANT ENCADRÉ */
    .student-header {
        background: linear-gradient(135deg, #1E3A8A 0%, #1E40AF 100%);
        padding: 25px;
        border-radius: 14px;
        box-shadow: 0px 8px 20px rgba(30, 58, 138, 0.2);
        color: white;
        text-align: center;
        margin-bottom: 25px;
        border: 2px solid #F59E0B;
    }
    
    .profile-card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        border: 1px solid #E2E8F0;
    }

    /* EN-TÊTES DE TABLEAUX EN COULEUR */
    th {
        background-color: #1E3A8A !important;
        color: #F59E0B !important;
        font-size: 1rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# Menu latéral
with st.sidebar:
    st.markdown("""
        <div style="text-align:center; padding: 10px 0;">
            <h2 style="color:#F59E0B !important; margin:0; font-size:1.4rem;">📍 NAVIGATION</h2>
        </div>
        <hr style="border-color:#334155;">
    """, unsafe_allow_html=True)

# Titre encadré
st.markdown("""
    <div class="student-header">
        <h1 style="margin:0; font-size:2.2rem; font-weight:800;">👨🎓 ESPACE APPRENANT</h1>
        <p style="margin:5px 0 0 0; color:#FBBF24; font-weight:500;">"if you're reach, be the bridge"</p>
    </div>
""", unsafe_allow_html=True)

st.markdown("### 🔑 Identification")
matricule_input = st.text_input("", placeholder="Entrez votre Matricule (ex: SPC-4825)").strip()

if matricule_input:
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT nom, sexe, niveau, date_inscription FROM apprenants WHERE matricule = ?", (matricule_input,))
    apprenant = c.fetchone()
    conn.close()

    if apprenant:
        nom, sexe, niveau, date_inscription = apprenant
        
        st.success(f"🎉 Bienvenue dans votre espace, **{nom}** !")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("<div class='profile-card' style='text-align:center;'>", unsafe_allow_html=True)
            st.markdown("<h3 style='color:#1E3A8A;'>🪪 Badge Virtuel</h3>", unsafe_allow_html=True)
            qr_bytes = generer_qr_code(matricule_input)
            
            st.image(qr_bytes, caption=f"Matricule : {matricule_input}", width=190)
            
            st.download_button(
                label="📥 Télécharger QR Code",
                data=qr_bytes,
                file_name=f"QR_Code_{matricule_input}.png",
                mime="image/png"
            )
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col2:
            st.markdown("<div class='profile-card'>", unsafe_allow_html=True)
            st.markdown("<h3 style='color:#1E3A8A;'>📌 Informations Personnelles</h3>", unsafe_allow_html=True)
            st.markdown(f"**👤 Nom complet :** `{nom}`")
            st.markdown(f"**🚻 Sexe :** `{sexe}`")
            st.markdown(f"**📚 Niveau :** `{niveau}`")
            st.markdown(f"**📅 Date d'inscription :** `{date_inscription}`")
            st.markdown("</div>", unsafe_allow_html=True)

        st.write("---")
        st.markdown("<h3 style='color:#1E3A8A;'>📅 Historique de vos Présences</h3>", unsafe_allow_html=True)
        
        conn = sqlite3.connect(DB_NAME)
        query_presences = """
            SELECT date_presence AS Date, heure_presence AS Heure
            FROM presences
            WHERE matricule = ?
            ORDER BY id DESC
        """
        df_presences = pd.read_sql_query(query_presences, conn, params=(matricule_input,))
        conn.close()

        if not df_presences.empty:
            st.dataframe(df_presences, use_container_width=True)
            st.info(f"📊 Total cumulé : **{len(df_presences)}** séance(s) effectuée(s).")
        else:
            st.warning("Aucune présence enregistrée pour ce matricule pour le moment.")
    else:
        st.error("❌ Matricule introuvable. Veuillez vérifier votre saisie.")
else:
    st.info("💡 Tapez votre matricule ci-dessus pour afficher vos informations.")





