import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
from database import get_connection

st.set_page_config(
    page_title="SPC - Espace Administration",
    page_icon="⚙️",
    layout="wide"
)

st.title("⚙️ Espace Administration")

# Onglets principaux de l'administration
tab_inscription, tab_apprenants, tab_presences, tab_gestion = st.tabs([
    "➕ Inscription Apprenant",
    "👥 Liste des Apprenants & Cartes",
    "📊 Historique des Présences",
    "🛠️ Gestion des Données"
])

# ---------------------------------------------------------
# 1. ONGLET : INSCRIPTION APPRENANT
# ---------------------------------------------------------
with tab_inscription:
    st.header("Inscription d'un nouvel apprenant")
    
    with st.form("form_inscription", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            matricule = st.text_input("Matricule / Identifiant unique *")
            nom = st.text_input("Nom *")
            postnom = st.text_input("Postnom")
            prenom = st.text_input("Prénom *")
            
        with col2:
            filiere = st.selectbox("Filière / Option", [
                "Informatique de Gestion",
                "Réseaux & Télécoms",
                "Design & Graphisme",
                "Marketing Digital",
                "Autre"
            ])
            niveau = st.selectbox("Niveau / Promotion", [
                "Niveau 1",
                "Niveau 2",
                "Niveau 3",
                "Professionnel"
            ])
            photo_url = st.text_input("Lien photo (Optionnel)", placeholder="https://...")
            
        submitted = st.form_submit_button("Enregistrer l'apprenant")
        
        if submitted:
            if not matricule or not nom or not prenom:
                st.error("Veuillez remplir les champs obligatoires (*).")
            else:
                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO apprenants (matricule, nom, postnom, prenom, filiere, niveau, photo)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (matricule.strip(), nom.strip(), postnom.strip(), prenom.strip(), filiere, niveau, photo_url))
                    conn.commit()
                    cursor.close()
                    conn.close()
                    st.success(f"L'apprenant {prenom} {nom} ({matricule}) a été inscrit avec succès !")
                except Exception as e:
                    st.error(f"Erreur lors de l'enregistrement (Matricule déjà utilisé ?) : {e}")

# ---------------------------------------------------------
# 2. ONGLET : LISTE DES APPRENANTS & GENERATION DE CARTE QR
# ---------------------------------------------------------
with tab_apprenants:
    st.header("Liste des Apprenants & Génération de QR Code")
    
    conn = get_connection()
    df_apprenants = pd.read_sql_query("SELECT * FROM apprenants ORDER BY nom ASC", conn)
    conn.close()
    
    if df_apprenants.empty:
        st.info("Aucun apprenant enregistré pour le moment.")
    else:
        st.dataframe(df_apprenants, use_container_width=True)
        
        st.subheader("📇 Générer la carte QR Code d'un apprenant")
        selected_matricule = st.selectbox(
            "Sélectionnez un apprenant par son matricule :",
            options=df_apprenants["matricule"].tolist(),
            format_func=lambda m: f"{m} - {df_apprenants[df_apprenants['matricule'] == m]['nom'].values[0]} {df_apprenants[df_apprenants['matricule'] == m]['prenom'].values[0]}"
        )
        
        if selected_matricule:
            student = df_apprenants[df_apprenants["matricule"] == selected_matricule].iloc[0]
            
            col_info, col_qr = st.columns([2, 1])
            
            with col_info:
                st.write(f"**Matricule :** {student['matricule']}")
                st.write(f"**Nom complet :** {student['nom']} {student['postnom']} {student['prenom']}")
                st.write(f"**Filière :** {student['filiere']}")
                st.write(f"**Niveau :** {student['niveau']}")
                
            with col_qr:
                # Génération du QR Code
                qr = qrcode.QRCode(version=1, box_size=8, border=2)
                qr.add_data(student['matricule'])
                qr.make(fit=True)
                img_qr = qr.make_image(fill_color="black", back_color="white")
                
                buf = BytesIO()
                img_qr.save(buf, format="PNG")
                byte_im = buf.getvalue()
                
                st.image(byte_im, caption=f"QR Code : {student['matricule']}", width=180)
                
                st.download_button(
                    label="📥 Télécharger le QR Code",
                    data=byte_im,
                    file_name=f"QR_{student['matricule']}.png",
                    mime="image/png"
                )

# ---------------------------------------------------------
# 3. ONGLET : HISTORIQUE DES PRESENCES
# ---------------------------------------------------------
with tab_presences:
    st.header("Historique et Rapport des Présences")
    
    conn = get_connection()
    query_presences = """
        SELECT p.id, p.matricule, a.nom, a.postnom, a.prenom, a.filiere, p.date, p.heure, p.statut
        FROM presences p
        LEFT JOIN apprenants a ON p.matricule = a.matricule
        ORDER BY p.id DESC
    """
    df_presences = pd.read_sql_query(query_presences, conn)
    conn.close()
    
    if df_presences.empty:
        st.info("Aucune présence enregistrée.")
    else:
        # Filtres
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filtre_filiere = st.multiselect("Filtrer par filière :", options=df_presences["filiere"].dropna().unique())
        with col_f2:
            filtre_date = st.text_input("Filtrer par date (AAAA-MM-JJ) :")
            
        df_filtered = df_presences.copy()
        if filtre_filiere:
            df_filtered = df_filtered[df_filtered["filiere"].isin(filtre_filiere)]
        if filtre_date:
            df_filtered = df_filtered[df_filtered["date"].str.contains(filtre_date, na=False)]
            
        st.dataframe(df_filtered, use_container_width=True)
        
        # Bouton d'export Excel / CSV
        csv_data = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Exporter le rapport (CSV)",
            data=csv_data,
            file_name="rapport_presences_spc.csv",
            mime="text/csv"
        )

# ---------------------------------------------------------
# 4. ONGLET : GESTION ET SUPPRESSION
# ---------------------------------------------------------
with tab_gestion:
    st.header("Gestion & Maintenance")
    st.warning("⚠️ Attention : Les actions de suppression sont irréversibles !")
    
    conn = get_connection()
    df_del = pd.read_sql_query("SELECT matricule, nom, prenom FROM apprenants ORDER BY nom ASC", conn)
    conn.close()
    
    if not df_del.empty:
        apprenant_to_del = st.selectbox(
            "Sélectionner un apprenant à supprimer :",
            options=df_del["matricule"].tolist(),
            format_func=lambda m: f"{m} - {df_del[df_del['matricule'] == m]['nom'].values[0]} {df_del[df_del['matricule'] == m]['prenom'].values[0]}"
        )
        
        if st.button("❌ Supprimer cet apprenant", type="primary"):
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM apprenants WHERE matricule = %s", (apprenant_to_del,))
                conn.commit()
                cursor.close()
                conn.close()
                st.success(f"Apprenant {apprenant_to_del} et ses historiques de présence ont été supprimés.")
                st.rerun()
            except Exception as e:
                st.error(f"Erreur lors de la suppression : {e}")
