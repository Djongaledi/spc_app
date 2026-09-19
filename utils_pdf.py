from fpdf import FPDF

class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'SMART PEOPLE CENTER (SPC)', 0, 1, 'C')
        self.set_font('Arial', 'I', 10)
        self.cell(0, 5, 'Rapport des Presences', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generer_pdf_presences(df_presences, titre="Liste des Presences"):
    pdf = PDFReport()
    pdf.add_page()
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, titre, 0, 1, 'L')
    pdf.ln(5)

    # Entêtes du tableau
    pdf.set_font('Arial', 'B', 9)
    pdf.set_fill_color(240, 240, 240)
    
    col_widths = [30, 50, 40, 25, 25, 20]
    headers = ["Matricule", "Nom", "Niveau", "Sexe", "Date", "Heure"]
    
    for i, h in enumerate(headers):
        pdf.cell(col_widths[i], 8, h, 1, 0, 'C', True)
    pdf.ln()

    # Données
    pdf.set_font('Arial', '', 8)
    for _, row in df_presences.iterrows():
        # Nettoyage des caractères spéciaux pour éviter les erreurs d'encodage
        nom = str(row.get('nom', '')).encode('latin-1', 'replace').decode('latin-1')
        niveau = str(row.get('niveau', '')).encode('latin-1', 'replace').decode('latin-1')
        
        pdf.cell(col_widths[0], 7, str(row.get('matricule', '')), 1, 0, 'C')
        pdf.cell(col_widths[1], 7, nom[:25], 1, 0, 'L')
        pdf.cell(col_widths[2], 7, niveau[:20], 1, 0, 'L')
        pdf.cell(col_widths[3], 7, str(row.get('sexe', '')), 1, 0, 'C')
        pdf.cell(col_widths[4], 7, str(row.get('date_presence', '')), 1, 0, 'C')
        pdf.cell(col_widths[5], 7, str(row.get('heure_presence', '')), 1, 0, 'C')
        pdf.ln()

    # Correction de l'erreur : fpdf2 renvoie directement un bytearray/bytes
    output_pdf = pdf.output()
    if isinstance(output_pdf, str):
        return output_pdf.encode('latin1')
    return bytes(output_pdf)







