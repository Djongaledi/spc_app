Import streamlit as st
Import sqlite3
Import pandas as pd
Import random
From datetime import datetime
Import sys
Import os
From io import BytesIO
From fpdf import FPDF

Try :
    From streamlit_qrcode_scanner import qrcode_scanner
Except ImportError :
    Qrcode_scanner = None

Sys.path.append(os.path.abspath(« .. »))
From database import NIVEAUX_SPC, DB_NAME
From utils_qr import generer_qr_code

# --- CLASSE ET FONCTION PDF ROBUSTES ---
Class PDFReport(FPDF) :
    Def header(self) :
        Self.set_font(‘Arial’, ‘B’, 14)
        Self.cell(0, 10, ‘SMART PEOPLE CENTER (SPC)’, 0, 1, ‘C’)
        Self.set_font(‘Arial’, ‘I’, 10)
        Self.cell(0, 5, ‘Rapport & Registre des Apprenants / Presences’, 0, 1, ‘C’)
        Self.ln(6)

    Def footer(self) :
        Self.set_y(-15)
        Self.set_font(‘Arial’, ‘I’, 8)
        Self.cell(0, 10, f’Page {self.page_no()}’, 0, 0, ‘C’)

Def clean_txt(text) :
    If text is None :
        Return « « 
    # Nettoyage des caractères non supportés par FPDF (latin-1)
    Return str(text).encode(‘latin-1’, ‘replace’).decode(‘latin-1’)

Def generer_pdf_presences(df_presences, titre= »Registre des Apprenants ») :
    Pdf = PDFReport()
    Pdf.set_auto_page_break(auto=True, margin=15)
    Pdf.add_page()
    
    Pdf.set_font(‘Arial’, ‘B’, 11)
    Pdf.cell(0, 8, clean_txt(titre), 0, 1, ‘L’)
    Pdf.ln(2)

    If df_presences.empty :
        Pdf.set_font(‘Arial’, ‘I’, 10)
        Pdf.cell(0, 8, « Aucune donnee disponible. », 0, 1, ‘L’)
    Else :
        Cols = [c for c in df_presences.columns if c.lower() != ‘id’]
        Nb_cols = len(cols)
        Col_width = 190 / nb_cols if nb_cols > 0 else 190

        Pdf.set_font(‘Arial’, ‘B’, 9)
        Pdf.set_fill_color(220, 220, 220)
        For col in cols :
            Pdf.cell(col_width, 8, clean_txt(col.upper()), 1, 0, ‘C’, True)
        Pdf.ln()

        Pdf.set_font(‘Arial’, ‘’, 8)
        For _, row in df_presences.iterrows() :
            For col in cols :
                Valeur = clean_txt(row.get(col, ‘’))
                If len(valeur) > 28 :
                    Valeur = valeur[ :25] + « … »
                Pdf.cell(col_width, 7, valeur, 1, 0, ‘C’)
            Pdf.ln()

    # Utilisation de BytesIO pour garantir une génération binaire parfaite
    Pdf_buffer = BytesIO()
    Pdf_output = pdf.output(dest=’S’)
    
    If isinstance(pdf_output, str) :
        Pdf_buffer.write(pdf_output.encode(‘latin-1’, ‘replace’))
    Elif isinstance(pdf_output, (bytes, bytearray)) :
        Pdf_buffer.write(pdf_output)
        
    Pdf_buffer.seek(0)
    Return pdf_buffer.getvalue()


# --- CONFIGURATION PAGE ET CSS ---
St.set_page_config(page_title= »Espace Administration – SPC », page_icon= »🛡️ », layout= »wide »)

St.markdown(« « « 
    <style>
    .stApp { background-color : #F8FAFC ; }
    
    /* MENU LATÉRAL FONCÉ ET SÉPARÉ */
    Section[data-testid= »stSidebar »] {
        Background-color : #0F172A !important ;
        Border-right : 3px solid #F59E0B !important ;
    }
    
    /* BOUTONS JAUNES PRINCIPAUX */
    .stButton>button, div[data-testid= »stFormSubmitButton »]>button, .stDownloadButton>button {
        Background : linear-gradient(135deg, #F59E0B 0%, #D97706 100%) !important ;
        Color : #0F172A !important ;
        Font-weight : 800 !important ;
        Border : none !important ;
        Border-radius : 8px !important ;
        Padding : 10px 20px !important ;
        Box-shadow : 0px 4px 10px rgba(245, 158, 11, 0.3) !important ;
    }
    /* EN-TÊTE ADMIN ENCADRÉ */
    .admin-header {
        Background : linear-gradient(135deg, #0F172A 0%, #1E3A8A 100%) ;
        Padding : 25px ;
        Border-radius : 14px ;
        Box-shadow : 0px 8px 20px rgba(15, 23, 42, 0.3) ;
        Color : white ;
        Text-align : center ;
        Margin-bottom : 25px ;
        Border : 2px solid #F59E0B ;
    }
    .login-box {
        Background : white ;
        Padding : 30px ;
        Border-radius : 16px ;
        Box-shadow : 0 10px 25px rgba(0,0,0,0.08) ;
        Border : 1px solid #E2E8F0 ;
        Max-width : 450px ;
        Margin : auto ;
    }
    Th {
        Background-color : #1E3A8A !important ;
        Color : #F59E0B !important ;
        Font-weight : bold !important ;
    }
    
    Button[data-baseweb= »tab »] {
        Font-weight : bold !important ;
        Color : #1E3A8A !important ;
    }
    Button[aria-selected= »true »] {
        Border-bottom-color : #F59E0B !important ;
        Color : #D97706 !important ;
    }
    </style>
« « « , unsafe_allow_html=True)

With st.sidebar :
    St.markdown(« « « 
        <div style= »text-align :center ; padding : 10px 0 ; »>
            <h2 style= »color :#F59E0B !important ; margin :0 ; font-size :1.3rem ; »>📍 NAVIGATION</h2>
        </div>
        <hr style= »border-color :#334155 ; »>
    « « « , unsafe_allow_html=True)

If « authenticated » not in st.session_state :
    St.session_state[« authenticated »] = False

Def login() :
    St.markdown(« « « 
        <div class= »admin-header »>
            <h1 style= »margin :0 ; font-size :2.2rem ; font-weight :800 ; »>🛡️ ESPACE ADMINISTRATION</h1>
            <p style= »margin :5px 0 0 0 ; color :#FBBF24 ; font-weight :600 ; »> »if you’re reach, be the bridge »</p>
        </div>
    « « « , unsafe_allow_html=True)
    
    St.markdown(‘<div class= »login-box »>’, unsafe_allow_html=True)
    With st.form(« form_login ») :
        St.subheader(« 🔑 Connexion Administrateur »)
        Username = st.text_input(« Identifiant »)
        Password = st.text_input(« Mot de passe », type= »password »)
        Submit = st.form_submit_button(« Se connecter »)
        
        If submit :
            Conn = sqlite3.connect(DB_NAME)
            C = conn.cursor()
            c.execute(« SELECT * FROM admin WHERE username = ? AND password = ? », (username, password))
            user = c.fetchone()
            conn.close()
            
            if user :
                st.session_state[« authenticated »] = True
                st.rerun()
            else :
                st.error(« ❌ Identifiant ou mot de passe incorrect. »)
    st.markdown(‘</div>’, unsafe_allow_html=True)

if not st.session_state[« authenticated »] :
    login()
else :
    st.markdown(« « « 
        <div class= »admin-header »>
            <h1 style= »margin :0 ; font-size :2rem ; font-weight :800 ; »>🛡️ PANNEAU DE CONTRÔLE ADMIN</h1>
            <p style= »margin :5px 0 0 0 ; color :#FBBF24 ; »> »if you’re reach, be the bridge »</p>
        </div>
    « « « , unsafe_allow_html=True)
    Col_space, col_logout = st.columns([5, 1])
    With col_logout :
        If st.button(« 🚪 Déconnexion ») :
            St.session_state[« authenticated »] = False
            St.rerun()

    Tab1, tab2, tab3, tab4 = st.tabs([
        « 📷 Scanner & Présences », 
        « 📊 Statistiques & Dashboard », 
        « ➕ Inscrire un Apprenant », 
        « 📋 Listes & Exports PDF »
    ])

    # --- TAB 1 : SCANNER ---
    With tab1 :
        St.subheader(« 📷 Contrôle des Entrées par QR Code »)
        Col_scan, col_manual = st.columns([3, 2])
        Matricule_scanne = None
        With col_scan :
            If qrcode_scanner is not None :
                Matricule_scanne = qrcode_scanner(key= »qr_scanner_admin »)
            Else :
                St.warning(« ⚠️ Installez le scanner : `pip install streamlit-qrcode-scanner` »)
        With col_manual :
            St.markdown(« ##### ⌨️ Saisie Manuelle de Secours »)
            With st.form(« form_presence_admin », clear_on_submit=True) :
                Matricule_saisi = st.text_input(« Saisir un matricule (ex : SPC-4825) »).strip()
                Submit_presence = st.form_submit_button(« ✅ Marquer Présent Manuellement »)

        Target_matricule = matricule_scanne if matricule_scanne else (matricule_saisi if submit_presence else None)
        If target_matricule :
            Target_matricule = target_matricule.strip()
            Conn = sqlite3.connect(DB_NAME)
            C = conn.cursor()
            
            c.execute(« SELECT nom, niveau FROM apprenants WHERE matricule = ? », (target_matricule,))
            apprenant = c.fetchone()
            
            if apprenant :
                nom, niveau = apprenant
                now = datetime.now()
                date_str = now.strftime(« %Y-%m-%d »)
                heure_str = now.strftime(« %H :%M :%S »)
                
                c.execute(« SELECT id FROM presences WHERE matricule = ? AND date_presence = ? », (target_matricule, date_str))
                existe = c.fetchone()
                
                if existe :
                    st.warning(f »⚠️ **{nom}** ({niveau}) est DÉJÀ marqué€ présent€ aujourd’hui. »)
                else :
                    c.execute(« INSERT INTO presences (matricule, date_presence, heure_presence) VALUES ( ?, ?, ?) »,
                              (target_matricule, date_str, heure_str))
                    Conn.commit()
                    St.success(f »🎉 Présence enregistrée avec succès pour **{nom}** ({niveau}) à {heure_str} ! »)
            Else :
                St.error(f »❌ Aucun apprenant trouvé avec le matricule ‘{target_matricule}’. »)
            
            Conn.close()

        St.write(« ---« )
        St.markdown(« <h4 style=’color :#1E3A8A ;’>📋 Liste des Présences du Jour</h4> », unsafe_allow_html=True)
        Conn = sqlite3.connect(DB_NAME)
        Query_today = « « « 
            SELECT p.matricule AS Matricule, a.nom AS Nom, a.niveau AS Niveau, p.heure_presence AS Heure
            FROM presences p
            JOIN apprenants a ON p.matricule = a.matricule
            WHERE p.date_presence = ?
            ORDER BY p.id DESC
        « « « 
        Df_today = pd.read_sql_query(query_today, conn, params=(datetime.now().strftime(« %Y-%m-%d »),))
        Conn.close()
        If not df_today.empty :
            St.dataframe(df_today, use_container_width=True)
        Else :
            St.info(« Aucune présence enregistrée pour aujourd’hui. »)

    # --- TAB 2 : DASHBOARD ---
    With tab2 :
        St.subheader(« 📊 Métriques Générales »)
        Conn = sqlite3.connect(DB_NAME)
        Total_apprenants = pd.read_sql_query(« SELECT COUNT(*) AS total FROM apprenants », conn).iloc[0][‘total’]
        Today_str = datetime.now().strftime(« %Y-%m-%d »)
        Presences_today = pd.read_sql_query(« SELECT COUNT(*) AS total FROM presences WHERE date_presence = ? », conn, params=(today_str,)).iloc[0][‘total’]
        Conn.close()
        C1, c2 = st.columns(2)
        C1.metric(label= »👥 Total Apprenants Inscrits », value=total_apprenants)
        C2.metric(label= »✅ Présences Enregistrées Aujourd’hui », value=presences_today)

    # --- TAB 3 : INSCRIPTION ---
    With tab3 :
        St.subheader(« ➕ Formulaire d’Inscription Apprenant »)
        With st.form(« form_admin_inscription », clear_on_submit=True) :
            Nom = st.text_input(« Nom complet de l’apprenant »)
            Sexe = st.selectbox(« Sexe », [« Masculin », « Féminin »])
            Niveau = st.selectbox(« Niveau d’étude / Groupe », NIVEAUX_SPC)
            Submitted = st.form_submit_button(« 💾 Enregistrer l’Inscription »)
        If submitted :
            If nom.strip() != « « :
                Matricule = f »SPC-{random.randint(1000, 9999)} »
                Date_inscription = datetime.now().strftime(« %Y-%m-%d %H :%M :%S »)
                Conn = sqlite3.connect(DB_NAME)
                C = conn.cursor()
                c.execute(
                    « INSERT INTO apprenants (matricule, nom, sexe, niveau, qr_code_path, date_inscription) VALUES ( ?, ?, ?, ?, ?, ?) »,
                    (matricule, nom, sexe, niveau, matricule, date_inscription)
                )
                Conn.commit()
                Conn.close()
                St.success(f »🎉 Apprenant **{nom}** inscrit avec succès ! Matricule attribué : **{matricule}** »)
            Else :
                St.error(« Veuillez saisir un nom valide. »)

    # --- TAB 4 : EXPORTS PDF & SUPPRESSIONS ---
    With tab4 :
        Subtab1, subtab2 = st.tabs([« 👨🎓 Registre Global », « 📅 Historique Filtré »])
        
        # --- SOUS-ONGLET 1 : REGISTRE GLOBAL ---
        With subtab1 :
            Conn = sqlite3.connect(DB_NAME)
            Df_apprenants = pd.read_sql_query(« SELECT matricule, nom, sexe, niveau, date_inscription FROM apprenants ORDER BY id DESC », conn)
            Conn.close()
            
            St.dataframe(df_apprenants, use_container_width=True)

            # BOUTON D’IMPRESSION PDF POUR LE REGISTRE GLOBAL
            If not df_apprenants.empty :
                Try :
                    Pdf_bytes = generer_pdf_presences(df_apprenants, titre= »Registre Global des Apprenants »)
                    St.download_button(
                        Label= »📄 Imprimer / Télécharger le Registre (PDF) »,
                        Data=pdf_bytes,
                        File_name=f »registre_global_SPC_{datetime.now().strftime(‘%Y%m%d’)}.pdf »,
                        Mime= »application/pdf »
                    )
                Except Exception as e :
                    St.error(f »Erreur lors de la génération du PDF du Registre : {e} »)

            # MODULE DE SUPPRESSION APPRENANTS
            St.write(« ---« )
            St.markdown(« <h4 style=’color :#DC2626 ;’>🗑️ Zone de Suppression d’un Apprenant</h4> », unsafe_allow_html=True)
            
            If not df_apprenants.empty :
                Col_del1, col_del2 = st.columns([3, 1])
                With col_del1 :
                    Apprenant_to_delete = st.selectbox(
                        « Sélectionnez l’apprenant à supprimer du système : »,
                        Options=df_apprenants[‘matricule’] + «  - «  + df_apprenants[‘nom’],
                        Key= »del_apprenant_select »
                    )
                With col_del2 :
                    St.write(«  « )
                    St.write(«  « )
                    Btn_delete_app = st.button(« 🗑️ Supprimer l’Apprenant », key= »btn_del_app »)
                
                If btn_delete_app :
                    Mat_del = apprenant_to_delete.split(«  - « )[0]
                    Conn = sqlite3.connect(DB_NAME)
                    C = conn.cursor()
                    c.execute(« DELETE FROM presences WHERE matricule = ? », (mat_del,))
                    c.execute(« DELETE FROM apprenants WHERE matricule = ? », (mat_del,))
                    conn.commit()
                    conn.close()
                    st.success(f »✅ L’apprenant avec le matricule **{mat_del}** et son historique ont été supprimés. »)
                    st.rerun()
            else :
                st.info(« Aucun apprenant enregistré. »)

        # --- SOUS-ONGLET 2 : HISTORIQUE FILTRÉ ---
        With subtab2 :
            Conn = sqlite3.connect(DB_NAME)
            Query = « « « 
                SELECT p.id, p.matricule, a.nom, a.niveau, a.sexe, p.date_presence, p.heure_presence
                FROM presences p
                JOIN apprenants a ON p.matricule = a.matricule
                WHERE 1=1
            « « « 
            
            Col_f1, col_f2 = st.columns(2)
            With col_f1 :
                Filter_niveau = st.selectbox(« Filtrer par Niveau », [« Tous »] + NIVEAUX_SPC)
            With col_f2 :
                Filter_sexe = st.selectbox(« Filtrer par Sexe », [« Tous », « Masculin », « Féminin »])
                
            Params = []
            If filter_niveau != « Tous » :
                Query += «  AND a.niveau = ? »
                Params.append(filter_niveau)
            If filter_sexe != « Tous » :
                Query += «  AND a.sexe = ? »
                Params.append(filter_sexe)
                
            Query += «  ORDER BY p.id DESC »
            
            Df_filtered = pd.read_sql_query(query, conn, params=params)
            Conn.close()
            
            Df_display = df_filtered.drop(columns=[‘id’]) if ‘id’ in df_filtered.columns else df_filtered
            St.dataframe(df_display, use_container_width=True)

            # BOUTON D’IMPRESSION PDF POUR L’HISTORIQUE FILTRÉ
            If not df_filtered.empty :
                Try :
                    Pdf_bytes_filtred = generer_pdf_presences(df_display, titre=f »Rapport des Presences ({filter_niveau}) »)
                    St.download_button(
                        Label= »📄 Télécharger le Rapport en PDF »,
                        Data=pdf_bytes_filtred,
                        File_name=f »presences_SPC_{datetime.now().strftime(‘%Y%m%d’)}.pdf »,
                        Mime= »application/pdf »
                    )
                Except Exception as e :
                    St.error(f »Erreur PDF : {e} »)

            # MODULE DE SUPPRESSION DES PRÉSENCES
            St.write(« ---« )
            St.markdown(« <h4 style=’color :#DC2626 ;’>🗑️ Zone de Suppression d’une Présence</h4> », unsafe_allow_html=True)
            
            If not df_filtered.empty :
                Col_p_del1, col_p_del2 = st.columns([3, 1])
                With col_p_del1 :
                    Options_presences = {
                        F »ID : {row[‘id’]} | {row[‘nom’]} ({row[‘matricule’]}) – {row[‘date_presence’]} à {row[‘heure_presence’]} » : row[‘id’]
                        For _, row in df_filtered.iterrows()
                    }
                    Selected_presence_label = st.selectbox(
                        « Sélectionnez la ligne de présence à retirer : »,
                        Options=list(options_presences.keys()),
                        Key= »del_presence_select »
                    )
                With col_p_del2 :
                    St.write(«  « )
                    St.write(«  « )
                    Btn_delete_presence = st.button(« 🗑️ Supprimer la Présence », key= »btn_del_presence »)
                If btn_delete_presence :
                    Presence_id = options_presences[selected_presence_label]
                    Conn = sqlite3.connect(DB_NAME)
                    C = conn.cursor()
                    c.execute(« DELETE FROM presences WHERE id = ? », (presence_id,))
                    conn.commit()
                    conn.close()
                    st.success(« ✅ La ligne de présence a été supprimée avec succès. »)
                    st.rerun()
            else :
                st.info(« Aucune présence enregistrée. »)






