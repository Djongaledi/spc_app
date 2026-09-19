import streamlit as st
import sqlite3
import pandas as pd
import random
from datetime import datetime
import sys
import os
from io import BytesIO
from fpdf import FPDF

try:
    from streamlit_qrcode_scanner import qrcode_scanner
except ImportError:
    qrcode_scanner = None

sys.path.append(os.path.abspath(".."))
from database import NIVEAUX_SPC, DB_NAME
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

    # Génération binaire sécurisée
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
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT * FROM admin WHERE username = ? AND password = ?", (username, password))
            user = c.fetchone()
            conn.close()
            
            if user:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("❌ Identifiant ou mot de passe incorrect.")
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

    tab1, tab2, tab3, tab4 = st.tabs([
        "📷 Scanner & Présences", 
        "📊 Statistiques & Dashboard", 
        "➕ Inscrire un Apprenant", 
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
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            
            c.execute("SELECT nom, niveau FROM apprenants WHERE matricule = ?", (target_matricule,))
            apprenant = c.fetchone()
            
            if apprenant:
                nom, niveau = apprenant
                now = datetime.now()
                date_str = now.strftime("%Y-%m-%d")
                heure_str = now.strftime("%H:%M:%S")
                
                c.execute("SELECT id FROM presences WHERE matricule = ? AND date_presence = ?", (target_matricule, date_str))
                existe = c.fetchone()
                
                if existe:
                    st.warning(f"⚠️ **{nom}** ({niveau}) est DÉJÀ marqué(e) présent(e) aujourd'hui.")
                else:
                    c.execute("INSERT INTO presences (matricule, date_presence, heure_presence) VALUES (?, ?, ?)",
                              (target_matricule, date_str, heure_str))
                    conn.commit()
                    st.success(f"🎉 Présence enregistrée avec succès pour **{nom}** ({niveau}) à {heure_str} !")
            else:
                st.error(f"❌ Aucun apprenant trouvé avec le matricule '{target_matricule}'.")
            
            conn.close()

        st.write("---")
        st.markdown("### 📋 Liste des Présences du Jour")
        conn = sqlite3.connect(DB_NAME)
        query_today = """
            SELECT p.matricule AS Matricule, a.nom AS Nom, a.niveau AS Niveau, p.heure_presence AS Heure
            FROM presences p
            JOIN apprenants a ON p.matricule = a.matricule
            WHERE p.date_presence = ?
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
        conn = sqlite3.connect(DB_NAME)
        total_apprenants = pd.read_sql_query("SELECT COUNT(*) AS total FROM apprenants", conn).iloc[0]['total']
        today_str = datetime.now().strftime("%Y-%m-%d")
        presences_today = pd.read_sql_query("SELECT COUNT(*) AS total FROM presences WHERE date_presence = ?", conn, params=(today_str,)).iloc[0]['total']
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
            if nom.strip() != "":
                matricule = f"SPC-{random.randint(1000, 9999)}"
                date_inscription = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute(
                    "INSERT INTO apprenants (matricule, nom, sexe, niveau, qr_code_path, date_inscription) VALUES (?, ?, ?, ?, ?, ?)",
                    (matricule, nom, sexe, niveau, matricule, date_inscription)
                )
                conn.commit()
                conn.close()
                st.success(f"🎉 Apprenant **{nom}** inscrit avec succès ! Matricule attribué : **{matricule}**")
            else:
                st.error("Veuillez saisir un nom valide.")

    # --- TAB 4 : EXPORTS PDF & SUPPRESSIONS ---
    with tab4:
        subtab1, subtab2 = st.tabs(["👨🎓 Registre Global", "📅 Historique Filtré"])
        
        with subtab1:
            conn = sqlite3.connect(DB_NAME)
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
                    conn = sqlite3.connect(DB_NAME)
                    c = conn.cursor()
                    c.execute("DELETE FROM presences WHERE matricule = ?", (mat_del,))
                    c.execute("DELETE FROM apprenants WHERE matricule = ?", (mat_del,))
                    conn.commit()
                    conn.close()
                    st.success(f"✅ L'apprenant {mat_del} a été supprimé.")
                    st.rerun()

        with subtab2:
            conn = sqlite3.connect(DB_NAME)
            query = """
                SELECT p.id, p.matricule, a.nom, a.niveau, a.sexe, p.date_presence, p.heure_presence
                FROM presences p
                JOIN apprenants a ON p.matricule = a.matricule
                WHERE 1=1
            """
            
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                filter_niveau = st.selectbox("Filtrer par Niveau", ["Tous"] + NIVEAUX_SPC)
            with col_f2:
                filter_sexe = st.selectbox("Filtrer par Sexe", ["Tous", "Masculin", "Féminin"])
                
            params = []
            if filter_niveau != "Tous":
                query += " AND a.niveau = ?"
                params.append(filter_niveau)
            if filter_sexe != "Tous":
                query += " AND a.sexe = ?"
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
                    conn = sqlite3.connect(DB_NAME)
                    c = conn.cursor()
                    c.execute("DELETE FROM presences WHERE id = ?", (presence_id,))
                    conn.commit()
                    conn.close()
                    st.success("✅ La ligne de présence a été supprimée.")
                    st.rerun()






