import streamlit as st
import pandas as pd
import random
from datetime import datetime
import sys
import os
import base64
from io import BytesIO
from fpdf import FPDF

try:
    from streamlit_qrcode_scanner import qrcode_scanner
except ImportError:
    qrcode_scanner = None

sys.path.append(os.path.abspath(".."))
from database import NIVEAUX_SPC, get_connection
from utils_qr import generer_qr_code

# --- CLASSE ET FONCTION PDF ---
class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'SMART PEOPLE CENTER (SPC)', 0, 1, 'C')
        self.set_font('Arial', 'I', 10)
        self.cell(0, 5, 'Rapport & Registre des Apprenants / Presences', 0, 1, 'C')
        self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def clean_txt(text):
    if text is None:
        return ""
    return str(text).encode('latin-1', 'replace').decode('latin-1')

def generer_pdf_presences(df_presences, titre="Registre des Apprenants"):
    pdf = PDFReport()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 8, clean_txt(titre), 0, 1, 'L')
    pdf.ln(2)

    if df_presences.empty:
        pdf.set_font('Arial', 'I', 10)
        pdf.cell(0, 8, "Aucune donnee disponible.", 0, 1, 'L')
    else:
        cols = [c for c in df_presences.columns if c.lower() != 'id']
        nb_cols = len(cols)
        col_width = 190 / nb_cols if nb_cols > 0 else 190

        pdf.set_font('Arial', 'B', 9)
        pdf.set_fill_color(220, 220, 220)
        for col in cols:
            pdf.cell(col_width, 8, clean_txt(col.upper()), 1, 0, 'C', True)
        pdf.ln()

        pdf.set_font('Arial', '', 8)
        for _, row in df_presences.iterrows():
            for col in cols:
                valeur = clean_txt(row.get(col, ''))
                if len(valeur) > 28:
                    valeur = valeur[:25] + "..."
                pdf.cell(col_width, 7, valeur, 1, 0, 'C')
            pdf.ln()

    pdf_output = pdf.output(dest='S')
    if isinstance(pdf_output, str):
        return pdf_output.encode('latin-1', 'replace')
    return bytes(pdf_output)


# --- CONFIGURATION PAGE ET CSS ---
st.set_page_config(page_title="Espace Administration - SPC", page_icon="🛡️", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #F8FAFC; }
    
    section[data-testid="stSidebar"] {
        background-color: #0F172A !important;
        border-right: 3px solid #F59E0B !important;
    }
    
    .stButton>button, div[data-testid="stFormSubmitButton"]>button, .stDownloadButton>button {
        background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%) !important;
        color: #0F172A !important;
        font-weight: 800 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 20px !important;
    }
    .admin-header {
        background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 100%);
        padding: 25px;
        border-radius: 14px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
        border: 2px solid #F59E0B;
    }
    .login-box {
        background: white;
        padding: 30px;
        border-radius: 16px;
        border: 1px solid #E2E8F0;
        max-width: 450px;
        margin: auto;
    }
    </style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 📍 NAVIGATION")
    st.write("---")

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

def login():
    st.markdown("""
        <div class="admin-header">
            <h1 style="margin:0; font-size:2.2rem; font-weight:800;">🛡️ ESPACE ADMINISTRATION</h1>
            <p style="margin:5px 0 0 0; color:#FBBF24;">"if you're reach, be the bridge"</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    with st.form("form_login"):
        st.subheader("🔑 Connexion Administrateur")
        username = st.text_input("Identifiant")
        password = st.text_input("Mot de passe", type="password")
        submit = st.form_submit_button("Se connecter")
        
        if submit:
            try:
                conn = get_connection()
                c = conn.cursor()
                c.execute("SELECT * FROM admin WHERE username = %s AND password = %s", (username, password))
                user = c.fetchone()
                c.close()
                conn.close()
                
                if user:
                    st.session_state["authenticated"] = True
                    st.rerun()
                else:
                    st.error("❌ Identifiant ou mot de passe incorrect.")
            except Exception as e:
                st.error(f"Erreur de connexion à la base de données : {e}")
    st.markdown('</div>', unsafe_allow_html=True)

if not st.session_state["authenticated"]:
    login()
else:
    st.markdown("""
        <div class="admin-header">
            <h1 style="margin:0; font-size:2rem; font-weight:800;">🛡️ PANNEAU DE CONTRÔLE ADMIN</h1>
            <p style="margin:5px 0 0 0; color:#FBBF24;">"if you're reach, be the bridge"</p>
        </div>
    """, unsafe_allow_html=True)
    
    col_space, col_logout = st.columns([5, 1])
    with col_logout:
        if st.button("🚪 Déconnexion"):
            st.session_state["authenticated"] = False
            st.rerun()

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📷 Scanner & Présences", 
        "📊 Statistiques & Dashboard", 
        "➕ Inscrire un Apprenant", 
        "🪪 Imprimer Carte Apprenant",
        "📋 Listes & Exports PDF"
    ])

    # --- TAB 1 : SCANNER ---
    with tab1:
        st.subheader("📷 Contrôle des Entrées par QR Code")
        col_scan, col_manual = st.columns([3, 2])
        matricule_scanne = None
        with col_scan:
            if qrcode_scanner is not None:
                matricule_scanne = qrcode_scanner(key="qr_scanner_admin")
            else:
                st.warning("⚠️ Installez le scanner : pip install streamlit-qrcode-scanner")
        with col_manual:
            st.markdown("##### ⌨️ Saisie Manuelle de Secours")
            with st.form("form_presence_admin", clear_on_submit=True):
                matricule_saisi = st.text_input("Saisir un matricule (ex: SPC-4825)").strip()
                submit_presence = st.form_submit_button("✅ Marquer Présent Manuellement")

        target_matricule = matricule_scanne if matricule_scanne else (matricule_saisi if submit_presence else None)
        if target_matricule:
            target_matricule = target_matricule.strip()
            conn = get_connection()
            c = conn.cursor()
            
            c.execute("SELECT nom, niveau FROM apprenants WHERE matricule = %s", (target_matricule,))
            apprenant = c.fetchone()
            
            if apprenant:
                nom, niveau = apprenant
                now = datetime.now()
                date_str = now.strftime("%Y-%m-%d")
                heure_str = now.strftime("%H:%M:%S")
                
                c.execute("SELECT id FROM presences WHERE matricule = %s AND date_presence = %s", (target_matricule, date_str))
                existe = c.fetchone()
                
                if existe:
                    st.warning(f"⚠️ **{nom}** ({niveau}) est DÉJÀ marqué(e) présent(e) aujourd'hui.")
                else:
                    c.execute("INSERT INTO presences (matricule, date_presence, heure_presence) VALUES (%s, %s, %s)",
                              (target_matricule, date_str, heure_str))
                    conn.commit()
                    st.success(f"🎉 Présence enregistrée avec succès pour **{nom}** ({niveau}) à {heure_str} !")
            else:
                st.error(f"❌ Aucun apprenant trouvé avec le matricule '{target_matricule}'.")
            
            c.close()
            conn.close()

        st.write("---")
        st.markdown("### 📋 Liste des Présences du Jour")
        conn = get_connection()
        query_today = """
            SELECT p.matricule AS "Matricule", a.nom AS "Nom", a.niveau AS "Niveau", p.heure_presence AS "Heure"
            FROM presences p
            JOIN apprenants a ON p.matricule = a.matricule
            WHERE p.date_presence = %s
            ORDER BY p.id DESC
        """
        df_today = pd.read_sql_query(query_today, conn, params=(datetime.now().strftime("%Y-%m-%d"),))
        conn.close()
        if not df_today.empty:
            st.dataframe(df_today, use_container_width=True)
        else:
            st.info("Aucune présence enregistrée pour aujourd'hui.")

    # --- TAB 2 : DASHBOARD ---
    with tab2:
        st.subheader("📊 Métriques Générales")
        conn = get_connection()
        total_apprenants = pd.read_sql_query("SELECT COUNT(*) AS total FROM apprenants", conn).iloc[0]['total']
        today_str = datetime.now().strftime("%Y-%m-%d")
        presences_today = pd.read_sql_query("SELECT COUNT(*) AS total FROM presences WHERE date_presence = %s", conn, params=(today_str,)).iloc[0]['total']
        conn.close()
        c1, c2 = st.columns(2)
        c1.metric(label="👥 Total Apprenants Inscrits", value=total_apprenants)
        c2.metric(label="✅ Présences Enregistrées Aujourd'hui", value=presences_today)

    # --- TAB 3 : INSCRIPTION ---
    with tab3:
        st.subheader("➕ Formulaire d'Inscription Apprenant")
        with st.form("form_admin_inscription", clear_on_submit=True):
            nom = st.text_input("Nom complet de l'apprenant")
            sexe = st.selectbox("Sexe", ["Masculin", "Féminin"])
            niveau = st.selectbox("Niveau d'étude / Groupe", NIVEAUX_SPC)
            submitted = st.form_submit_button("💾 Enregistrer l'Inscription")
        
        if submitted:
            nom_clean = nom.strip()
            if nom_clean != "":
                conn = get_connection()
                c = conn.cursor()
                
                c.execute("SELECT matricule FROM apprenants WHERE LOWER(nom) = LOWER(%s)", (nom_clean,))
                existe_deja = c.fetchone()
                
                if existe_deja:
                    st.error(f"⚠️ **Inscription refusée** : Un apprenant du nom de **'{nom_clean}'** existe déjà avec le matricule **{existe_deja[0]}**.")
                    c.close()
                    conn.close()
                else:
                    matricule = f"SPC-{random.randint(1000, 9999)}"
                    date_inscription = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    c.execute(
                        "INSERT INTO apprenants (matricule, nom, sexe, niveau, qr_code_path, date_inscription) VALUES (%s, %s, %s, %s, %s, %s)",
                        (matricule, nom_clean, sexe, niveau, matricule, date_inscription)
                    )
                    conn.commit()
                    c.close()
                    conn.close()
                    st.success(f"🎉 Apprenant **{nom_clean}** inscrit avec succès ! Matricule attribué : **{matricule}**")
            else:
                st.error("Veuillez saisir un nom valide.")

    # --- TAB 4 : IMPRESSION DE LA CARTE APPRENANT ---
    with tab4:
        st.subheader("🪪 Générer et Imprimer la Carte d'Apprenant")
        
        conn = get_connection()
        df_apprenants_carte = pd.read_sql_query("SELECT matricule, nom FROM apprenants ORDER BY nom ASC", conn)
        conn.close()

        if not df_apprenants_carte.empty:
            col_sel, col_photo, col_logo = st.columns([2, 1, 1])
            
            with col_sel:
                options = [f"{row['nom']} ({row['matricule']})" for _, row in df_apprenants_carte.iterrows()]
                choix = st.selectbox("Sélectionnez l'apprenant :", options, key="select_carte_apprenant")
            
            with col_photo:
                uploaded_photo = st.file_uploader("📷 Photo d'identité", type=["jpg", "png", "jpeg"], key="upload_photo_carte")

            with col_logo:
                uploaded_logo = st.file_uploader("🖼️ Logo SPC", type=["jpg", "png", "jpeg"], key="upload_logo_carte")

            if choix:
                mat_sel = choix.split("(")[-1].replace(")", "").strip()
                
                conn = get_connection()
                c = conn.cursor()
                c.execute("SELECT matricule, nom, sexe, niveau FROM apprenants WHERE matricule = %s", (mat_sel,))
                app_data = c.fetchone()
                c.close()
                conn.close()

                if app_data:
                    mat, nom_app, sexe_app, niv_app = app_data
                    
                    # Photo d'identité de l'apprenant
                    if uploaded_photo:
                        photo_bytes = uploaded_photo.getvalue()
                        b64_photo = f"data:image/png;base64,{base64.b64encode(photo_bytes).decode()}"
                    else:
                        b64_photo = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='100' height='100' viewBox='0 0 24 24' fill='%2394A3B8'><path d='M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z'/></svg>"

                    # Logo SPC uploadé
                    if uploaded_logo:
                        logo_bytes = uploaded_logo.getvalue()
                        b64_logo = f"data:image/png;base64,{base64.b64encode(logo_bytes).decode()}"
                    else:
                        b64_logo = ""

                    bg_style = f"background-image: url('{b64_logo}');" if b64_logo else ""

                    # Génération du QR code en base64
                    qr_img = generer_qr_code(mat)
                    b64_qr = f"data:image/png;base64,{base64.b64encode(qr_img).decode()}"

                    annee_scolaire = "2025-2026"

                    carte_html = f"""
                    <div id="carte-print" style="
                        width: 360px;
                        height: 560px;
                        border: 2px solid #0F172A;
                        border-radius: 16px;
                        background-color: #FFFFFF;
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        box-shadow: 0px 8px 20px rgba(15, 23, 42, 0.15);
                        position: relative;
                        margin: 10px auto;
                        overflow: hidden;
                        color: #0F172A;
                    ">
                        <!-- LOGO BLASON EN ARRIÈRE-PLAN (FILIGRANE CENTRÉ ET AJUSTÉ) -->
                        <div style="
                            position: absolute;
                            top: 50%;
                            left: 50%;
                            transform: translate(-50%, -50%);
                            width: 300px;
                            height: 380px;
                            {bg_style}
                            background-size: contain;
                            background-repeat: no-repeat;
                            background-position: center;
                            opacity: 0.15;
                            z-index: 1;
                            pointer-events: none;
                        "></div>

                        <!-- CONTENU DE LA CARTE -->
                        <div style="position: relative; z-index: 2; height: 100%;">
                            <!-- BANDEAU SUPÉRIEUR AVEC LOGO ICÔNE AGRANDI À GAUCHE -->
                            <div style="
                                background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 100%);
                                padding: 12px 14px;
                                border-bottom: 4px solid #F59E0B;
                                display: flex;
                                align-items: center;
                                justify-content: flex-start;
                                gap: 12px;
                            ">
                                <!-- ICÔNE LOGO SPC AGRANDIE -->
                                <div style="
                                    width: 54px;
                                    height: 54px;
                                    border-radius: 10px;
                                    background: #FFFFFF;
                                    padding: 2px;
                                    display: flex;
                                    align-items: center;
                                    justify-content: center;
                                    box-shadow: 0px 3px 8px rgba(0,0,0,0.25);
                                    flex-shrink: 0;
                                ">
                                    <img src="{b64_logo}" style="max-width: 100%; max-height: 100%; object-fit: contain;">
                                </div>

                                <!-- TEXTES EN-TÊTE -->
                                <div style="text-align: left; color: #FFFFFF;">
                                    <div style="font-size: 10px; font-weight: 700; letter-spacing: 1.2px; opacity: 0.9; text-transform: uppercase;">TRAINING CENTER</div>
                                    <div style="font-size: 15px; font-weight: 900; color: #F59E0B; letter-spacing: 0.5px; line-height: 1.1;">SMART PEOPLE CENTER</div>
                                    <div style="font-size: 9px; font-weight: 800; color: #0F172A; background: #FBBF24; display: inline-block; padding: 1px 8px; border-radius: 12px; margin-top: 3px; text-transform: uppercase;">
                                        LEARNER CARD
                                    </div>
                                </div>
                            </div>

                            <!-- PHOTO ET ANNÉE -->
                            <div style="display: flex; justify-content: space-between; align-items: center; padding: 16px 20px 10px 20px;">
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

                                <div style="text-align: right; background: rgba(241, 245, 249, 0.85); padding: 10px 14px; border-radius: 10px; border-left: 3px solid #1E3A8A;">
                                    <div style="font-size: 10px; font-weight: 700; color: #64748B; text-transform: uppercase;">Year of Study</div>
                                    <div style="font-size: 15px; font-weight: 900; color: #0F172A; margin-top: 2px;">{annee_scolaire}</div>
                                </div>
                            </div>

                            <!-- INFORMATIONS -->
                            <div style="padding: 0 20px; font-size: 12px;">
                                <div style="margin-bottom: 12px;">
                                    <div style="font-size: 10px; font-weight: 700; color: #64748B; text-transform: uppercase;">Full Name</div>
                                    <div style="font-size: 14px; font-weight: 900; color: #1E3A8A; text-transform: uppercase; line-height: 1.2;">{nom_app}</div>
                                </div>

                                <div style="display: flex; justify-content: space-between; margin-bottom: 12px; background: rgba(250, 245, 255, 0.85); padding: 8px 12px; border-radius: 8px; border: 1px solid #F3E8FF;">
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

                            <!-- QR CODE ET BAS DE PAGE -->
                            <div style="
                                position: absolute;
                                bottom: 0;
                                left: 0;
                                right: 0;
                                background: rgba(248, 250, 252, 0.95);
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

    # --- TAB 5 : EXPORTS PDF & SUPPRESSIONS ---
    with tab5:
        subtab1, subtab2 = st.tabs(["👨🎓 Registre Global", "📅 Historique Filtré"])
        
        with subtab1:
            conn = get_connection()
            df_apprenants = pd.read_sql_query("SELECT matricule, nom, sexe, niveau, date_inscription FROM apprenants ORDER BY id DESC", conn)
            conn.close()
            
            st.dataframe(df_apprenants, use_container_width=True)

            if not df_apprenants.empty:
                try:
                    pdf_bytes = generer_pdf_presences(df_apprenants, titre="Registre Global des Apprenants")
                    st.download_button(
                        label="📄 Imprimer / Télécharger le Registre (PDF)",
                        data=pdf_bytes,
                        file_name="registre_global_SPC.pdf",
                        mime="application/pdf"
                    )
                except Exception as e:
                    st.error(f"Erreur lors de la génération du PDF : {e}")

            st.write("---")
            st.markdown("### 🗑️ Zone de Suppression d'un Apprenant")
            
            if not df_apprenants.empty:
                col_del1, col_del2 = st.columns([3, 1])
                with col_del1:
                    apprenant_to_delete = st.selectbox(
                        "Sélectionnez l'apprenant à supprimer :",
                        options=df_apprenants['matricule'] + " - " + df_apprenants['nom'],
                        key="del_apprenant_select"
                    )
                with col_del2:
                    st.write(" ")
                    st.write(" ")
                    btn_delete_app = st.button("🗑️ Supprimer l'Apprenant", key="btn_del_app")
                
                if btn_delete_app:
                    mat_del = apprenant_to_delete.split(" - ")[0]
                    conn = get_connection()
                    c = conn.cursor()
                    c.execute("DELETE FROM presences WHERE matricule = %s", (mat_del,))
                    c.execute("DELETE FROM apprenants WHERE matricule = %s", (mat_del,))
                    conn.commit()
                    c.close()
                    conn.close()
                    st.success(f"✅ L'apprenant {mat_del} a été supprimé.")
                    st.rerun()

        with subtab2:
            conn = get_connection()
            query = """
                SELECT p.id, p.matricule, a.nom, a.niveau, a.sexe, p.date_presence, p.heure_presence
                FROM presences p
                JOIN apprenants a ON p.matricule = a.matricule
                WHERE 1=1
            """
            
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                filter_niveau = st.selectbox("Filtrer par Niveau", ["Tous"] + list(NIVEAUX_SPC))
            with col_f2:
                filter_sexe = st.selectbox("Filtrer par Sexe", ["Tous", "Masculin", "Féminin"])
                
            params = []
            if filter_niveau != "Tous":
                query += " AND a.niveau = %s"
                params.append(filter_niveau)
            if filter_sexe != "Tous":
                query += " AND a.sexe = %s"
                params.append(filter_sexe)
                
            query += " ORDER BY p.id DESC"
            
            df_filtered = pd.read_sql_query(query, conn, params=params)
            conn.close()
            
            df_display = df_filtered.drop(columns=['id']) if 'id' in df_filtered.columns else df_filtered
            st.dataframe(df_display, use_container_width=True)

            if not df_filtered.empty:
                try:
                    pdf_bytes_filtred = generer_pdf_presences(df_display, titre=f"Rapport des Presences ({filter_niveau})")
                    st.download_button(
                        label="📄 Télécharger le Rapport en PDF",
                        data=pdf_bytes_filtred,
                        file_name="presences_SPC.pdf",
                        mime="application/pdf"
                    )
                except Exception as e:
                    st.error(f"Erreur PDF : {e}")

            st.write("---")
            st.markdown("### 🗑️ Zone de Suppression d'une Présence")
            
            if not df_filtered.empty:
                col_p_del1, col_p_del2 = st.columns([3, 1])
                with col_p_del1:
                    options_presences = {
                        f"ID: {row['id']} | {row['nom']} ({row['matricule']}) - {row['date_presence']} à {row['heure_presence']}": row['id']
                        for _, row in df_filtered.iterrows()
                    }
                    selected_presence_label = st.selectbox(
                        "Sélectionnez la ligne de présence à retirer :",
                        options=list(options_presences.keys()),
                        key="del_presence_select"
                    )
                with col_p_del2:
                    st.write(" ")
                    st.write(" ")
                    btn_delete_presence = st.button("🗑️ Supprimer la Présence", key="btn_del_presence")
                if btn_delete_presence:
                    presence_id = options_presences[selected_presence_label]
                    conn = get_connection()
                    c = conn.cursor()
                    c.execute("DELETE FROM presences WHERE id = %s", (presence_id,))
                    conn.commit()
                    c.close()
                    conn.close()
                    st.success("✅ La ligne de présence a été supprimée.")
                    st.rerun()
