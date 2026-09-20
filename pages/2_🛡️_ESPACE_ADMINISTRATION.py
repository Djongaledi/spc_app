import streamlit as st
import sqlite3
import pandas as pd
import random
from datetime import datetime
import base64

from database import DB_NAME, NIVEAUX_SPC
from utils_qr import generer_qr_code

st.set_page_config(page_title="Espace Administration - SPC", page_icon="🔑", layout="wide")

# --- STYLES CSS PERSONNALISÉS DE L'APPLICATION ---
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

# --- ONGLET 1 : SCANNER & PRÉSENCES ---
with tab_scan:
    st.subheader("📸 Saisie des Présences via QR Code ou Matricule")
    
    col_input, col_action = st.columns([2, 1])
    with col_input:
        mat_scan = st.text_input("Saisir ou scanner le Matricule (ex: SPC-1234)").strip()
    
    if st.button("✅ Enregistrer Présence"):
        if mat_scan:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT matricule, nom, niveau FROM apprenants WHERE UPPER(matricule) = UPPER(?)", (mat_scan,))
            apprenant = c.fetchone()

            if apprenant:
                mat_found, nom_app, niv_app = apprenant
                date_jour = datetime.now().strftime("%Y-%m-%d")
                heure_actuelle = datetime.now().strftime("%H:%M:%S")

                c.execute("SELECT id FROM presences WHERE matricule = ? AND date_presence = ?", (mat_found, date_jour))
                deja_present = c.fetchone()

                if deja_present:
                    st.warning(f"⚠️ **{nom_app}** est déjà marqué présent aujourd'hui ({date_jour}).")
                else:
                    c.execute(
                        "INSERT INTO presences (matricule, date_presence, heure_presence) VALUES (?, ?, ?)",
                        (mat_found, date_jour, heure_actuelle)
                    )
                    conn.commit()
                    st.success(f"🎉 Présence enregistrée avec succès pour **{nom_app}** à {heure_actuelle} !")
            else:
                st.error("❌ Aucun apprenant trouvé avec ce matricule.")
            conn.close()
        else:
            st.warning("Veuillez saisir un matricule.")

    st.markdown("---")
    st.write("### 📅 Registre des Présences du Jour")
    conn = sqlite3.connect(DB_NAME)
    date_jour = datetime.now().strftime("%Y-%m-%d")
    df_presences = pd.read_sql_query("""
        SELECT p.id, a.matricule, a.nom, a.niveau, p.date_presence, p.heure_presence 
        FROM presences p
        JOIN apprenants a ON p.matricule = a.matricule
        WHERE p.date_presence = ?
        ORDER BY p.heure_presence DESC
    """, conn, params=(date_jour,))
    conn.close()

    if not df_presences.empty:
        st.dataframe(df_presences, use_container_width=True)
    else:
        st.info("Aucune présence enregistrée aujourd'hui.")

# --- ONGLET 2 : STATISTIQUES & DASHBOARD ---
with tab_stats:
    st.subheader("📊 Tableau de Bord & Statistiques")
    
    conn = sqlite3.connect(DB_NAME)
    total_apprenants = pd.read_sql_query("SELECT COUNT(*) as total FROM apprenants", conn).iloc[0]['total']
    
    date_jour = datetime.now().strftime("%Y-%m-%d")
    presences_today = pd.read_sql_query("SELECT COUNT(*) as total FROM presences WHERE date_presence = ?", conn, params=(date_jour,)).iloc[0]['total']
    
    col1, col2 = st.columns(2)
    col1.metric("Total Apprenants Inscrits", total_apprenants)
    col2.metric("Présences Aujourd'hui", presences_today)

    st.markdown("---")
    st.write("### 📈 Répartition des Apprenants par Niveau")
    df_niveaux = pd.read_sql_query("SELECT niveau, COUNT(*) as Effectif FROM apprenants GROUP BY niveau", conn)
    conn.close()

    if not df_niveaux.empty:
        st.bar_chart(df_niveaux.set_index("niveau"))
    else:
        st.info("Aucune donnée disponible.")

# --- ONGLET 3 : INSCRIPTION APPRENANT ---
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

# --- ONGLET 4 : IMPRESSION DE LA CARTE APPRENANT DESIGN PERFECTIONNÉ ---
with tab_cartes:
    st.subheader("🪪 Générer et Imprimer la Carte d'Apprenant")
    
    conn = sqlite3.connect(DB_NAME)
    df_apprenants = pd.read_sql_query("SELECT matricule, nom FROM apprenants ORDER BY nom ASC", conn)
    conn.close()

    if not df_apprenants.empty:
        col_sel, col_photo = st.columns([2, 1])
        
        with col_sel:
            options = [f"{row['nom']} ({row['matricule']})" for _, row in df_apprenants.iterrows()]
            choix = st.selectbox("Sélectionnez l'apprenant :", options)
        
        with col_photo:
            uploaded_photo = st.file_uploader("📷 Charger la photo d'identité", type=["jpg", "png", "jpeg"])

        if choix:
            mat_sel = choix.split("(")[-1].replace(")", "").strip()
            
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT matricule, nom, sexe, niveau, date_inscription FROM apprenants WHERE matricule = ?", (mat_sel,))
            app_data = c.fetchone()
            conn.close()

            if app_data:
                mat, nom_app, sexe_app, niv_app, date_ins = app_data
                
                # Traitement de la Photo d'identité
                if uploaded_photo:
                    photo_bytes = uploaded_photo.getvalue()
                    b64_photo = f"data:image/png;base64,{base64.b64encode(photo_bytes).decode()}"
                else:
                    # Silhouette par défaut professionnelle
                    b64_photo = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='100' height='100' viewBox='0 0 24 24' fill='%2394A3B8'><path d='M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z'/></svg>"

                # Génération QR Code en Base64
                qr_img = generer_qr_code(mat)
                b64_qr = f"data:image/png;base64,{base64.b64encode(qr_img).decode()}"

                annee_scolaire = "2025-2026"

                # CODE HTML DE LA CARTE AVEC DESIGN AVANCÉ
                carte_html = f"""
                <div id="carte-print" style="
                    width: 360px;
                    height: 560px;
                    border: 2px solid #0F172A;
                    border-radius: 16px;
                    background: #FFFFFF;
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    box-shadow: 0px 8px 20px rgba(15, 23, 42, 0.15);
                    position: relative;
                    margin: 10px auto;
                    overflow: hidden;
                    color: #0F172A;
                ">
                    <!-- BANDEAU SUPÉRIEUR -->
                    <div style="
                        background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 100%);
                        padding: 16px 10px 12px 10px;
                        text-align: center;
                        color: #FFFFFF;
                        border-bottom: 4px solid #F59E0B;
                    ">
                        <div style="font-size: 11px; font-weight: 700; letter-spacing: 1.5px; opacity: 0.9; text-transform: uppercase;">TRAINING CENTER</div>
                        <div style="font-size: 17px; font-weight: 900; color: #F59E0B; margin-top: 2px; letter-spacing: 0.5px;">SMART PEOPLE CENTER</div>
                        <div style="font-size: 10px; font-weight: 800; color: #0F172A; background: #FBBF24; display: inline-block; padding: 2px 10px; border-radius: 20px; margin-top: 6px; text-transform: uppercase;">
                            LEARNER CARD
                        </div>
                    </div>

                    <!-- BLOC CORPS : PHOTO & ANNÉE ACADÉMIQUE -->
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 16px 20px 10px 20px;">
                        <!-- CADRE PHOTO -->
                        <div style="
                            width: 105px;
                            height: 125px;
                            border: 3px solid #E2E8F0;
                            border-radius: 10px;
                            overflow: hidden;
                            background: #F8FAFC;
                            box-shadow: inset 0px 0px 5px rgba(0,0,0,0.05);
                            display: flex;
                            align-items: center;
                            justify-content: center;
                        ">
                            <img src="{b64_photo}" style="width: 100%; height: 100%; object-fit: cover;">
                        </div>

                        <!-- BLOC ANNÉE D'ÉTUDE -->
                        <div style="text-align: right; background: #F1F5F9; padding: 10px 14px; border-radius: 10px; border-left: 3px solid #1E3A8A;">
                            <div style="font-size: 10px; font-weight: 700; color: #64748B; text-transform: uppercase;">Year of Study</div>
                            <div style="font-size: 15px; font-weight: 900; color: #0F172A; margin-top: 2px;">{annee_scolaire}</div>
                        </div>
                    </div>

                    <!-- BLOC INFORMATIONS APPRENANT -->
                    <div style="padding: 0 20px; font-size: 12px;">
                        <div style="margin-bottom: 12px;">
                            <div style="font-size: 10px; font-weight: 700; color: #64748B; text-transform: uppercase;">Full Name</div>
                            <div style="font-size: 14px; font-weight: 900; color: #1E3A8A; text-transform: uppercase; line-height: 1.2;">{nom_app}</div>
                        </div>

                        <div style="display: flex; justify-content: space-between; margin-bottom: 12px; background: #FAF5FF; padding: 8px 12px; border-radius: 8px; border: 1px solid #F3E8FF;">
                            <div>
                                <div style="font-size: 9px; font-weight: 700; color: #64748B; text-transform: uppercase;">Registration No</div>
                                <div style="font-size: 13px; font-weight: 900; color: #D97706;">{mat}</div>
                            </div>
                            <div style="text-align: right;">
                                <div style="font-size: 9px; font-weight: 700; color: #64748B; text-transform: uppercase;">Sex</div>
                                <div style="font-size: 13px; font-weight: 800; color: #0F172A;">{sexe_app}</div>
                            </div>
                        </div>

                        <div style="margin-bottom: 10px;">
                            <div style="font-size: 10px; font-weight: 700; color: #64748B; text-transform: uppercase;">Level / Program</div>
                            <div style="font-size: 12px; font-weight: 800; color: #0F172A;">{niv_app}</div>
                        </div>
                    </div>

                    <!-- PIED DE PAGE ET QR CODE -->
                    <div style="
                        position: absolute;
                        bottom: 0;
                        left: 0;
                        right: 0;
                        background: #F8FAFC;
                        border-top: 1px dashed #CBD5E1;
                        padding: 10px 20px;
                        display: flex;
                        align-items: center;
                        justify-content: space-between;
                    ">
                        <div style="text-align: left; max-width: 180px;">
                            <div style="font-size: 8px; color: #64748B; font-weight: 600; line-height: 1.3;">
                                Official identification card for Smart People Center attendance and verification.
                            </div>
                        </div>
                        <div style="text-align: center;">
                            <img src="{b64_qr}" style="width: 70px; height: 70px; border-radius: 4px; border: 1px solid #CBD5E1; background: white; padding: 2px;">
                        </div>
                    </div>
                </div>
                """

                st.write("### 🖨️ Aperçu de la Carte D'Apprenant")
                st.components.v1.html(carte_html, height=600)

                st.download_button(
                    label="📥 Télécharger la Carte (Fichier HTML Imprimable)",
                    data=carte_html,
                    file_name=f"Carte_SPC_{mat}.html",
                    mime="text/html"
                )
    else:
        st.info("Aucun apprenant enregistré dans la base de données pour l'instant.")

# --- ONGLET 5 : LISTES & EXPORTS PDF ---
with tab_lists:
    st.subheader("📋 Consultation des Listes & Exports")
    
    conn = sqlite3.connect(DB_NAME)
    df_all_apprenants = pd.read_sql_query("SELECT matricule, nom, sexe, niveau, date_inscription FROM apprenants ORDER BY nom ASC", conn)
    conn.close()

    if not df_all_apprenants.empty:
        st.write("#### 👨🎓 Liste Complète des Apprenants")
        st.dataframe(df_all_apprenants, use_container_width=True)

        csv_data = df_all_apprenants.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Exporter la Liste en CSV / Excel",
            data=csv_data,
            file_name=f"liste_apprenants_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        st.info("Aucun apprenant inscrit pour le moment.")






