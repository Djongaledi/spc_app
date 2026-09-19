from fpdf import FPDF

class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'SMART PEOPLE CENTER (SPC)', 0, 1, 'C')
        self.set_font('Arial', 'I', 10)
        self.cell(0, 5, 'Registre des Apprenants / Presences', 0, 1, 'C')
        self.ln(8)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def clean_txt(text):
    if text is None:
        return ""
    return str(text).encode('latin-1', 'replace').decode('latin-1')

def generer_pdf_presences(df_presences, titre="Registre Global"):
    pdf = PDFReport()
    pdf.add_page()
    
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 8, clean_txt(titre), 0, 1, 'L')
    pdf.ln(3)

    # Entêtes du tableau
    pdf.set_font('Arial', 'B', 9)
    pdf.set_fill_color(230, 230, 230)
    
    # Largeurs de colonnes ajustées
    col_widths = [35, 55, 30, 45]
    headers = ["Matricule", "Nom", "Sexe", "Niveau"]
    
    # Si le DataFrame contient aussi les dates/heures, on adapte la mise en page
    if 'date_presence' in df_presences.columns:
        col_widths = [30, 45, 40, 20, 25, 25]
        headers = ["Matricule", "Nom", "Niveau", "Sexe", "Date", "Heure"]

    for i, h in enumerate(headers):
        pdf.cell(col_widths[i], 8, h, 1, 0, 'C', True)
    pdf.ln()

    # Données des lignes
    pdf.set_font('Arial', '', 8)
    for _, row in df_presences.iterrows():
        if 'date_presence' in df_presences.columns:
            pdf.cell(col_widths[0], 7, clean_txt(row.get('matricule', '')), 1, 0, 'C')
            pdf.cell(col_widths[1], 7, clean_txt(row.get('nom', ''))[:22], 1, 0, 'L')
            pdf.cell(col_widths[2], 7, clean_txt(row.get('niveau', ''))[:18], 1, 0, 'L')
            pdf.cell(col_widths[3], 7, clean_txt(row.get('sexe', '')), 1, 0, 'C')
            pdf.cell(col_widths[4], 7, clean_txt(row.get('date_presence', '')), 1, 0, 'C')
            pdf.cell(col_widths[5], 7, clean_txt(row.get('heure_presence', '')), 1, 0, 'C')
        else:
            pdf.cell(col_widths[0], 7, clean_txt(row.get('matricule', '')), 1, 0, 'C')
            pdf.cell(col_widths[1], 7, clean_txt(row.get('nom', ''))[:30], 1, 0, 'L')
            pdf.cell(col_widths[2], 7, clean_txt(row.get('sexe', '')), 1, 0, 'C')
            pdf.cell(col_widths[3], 7, clean_txt(row.get('niveau', ''))[:25], 1, 0, 'L')
        pdf.ln()

    # Rendu binaire garanti pour Streamlit
    pdf_output = pdf.output()
    if isinstance(pdf_output, str):
        return pdf_output.encode('latin1')
    return bytes(pdf_output)






