from fpdf import FPDF
from datetime import datetime

class PDFReport(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 14)
        self.cell(0, 10, 'SMART PEOPLE CENTER (SPC)', border=False, ln=True, align='C')
        self.set_font('Helvetica', 'I', 10)
        self.cell(0, 5, '"If you reach, be the bridge"', border=False, ln=True, align='C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')

def generer_pdf_presences(df, titre_rapport="Rapport des Presences"):
    pdf = PDFReport()
    pdf.add_page()
    
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 10, titre_rapport, ln=True, align='L')
    pdf.set_font("Helvetica", size=9)
    pdf.cell(0, 5, f"Genere le : {datetime.now().strftime('%d/%m/%Y a %H:%M')}", ln=True, align='L')
    pdf.ln(5)
    
    col_widths = [30, 50, 40, 20, 25, 25]
    headers = ["Matricule", "Nom", "Niveau", "Sexe", "Date", "Heure"]
    
    pdf.set_fill_color(30, 58, 138)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", 'B', 9)
    
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 8, header, border=1, align='C', fill=True)
    pdf.ln()
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", size=8)
    
    for _, row in df.iterrows():
        pdf.cell(col_widths[0], 7, str(row.get('matricule', '')), border=1)
        pdf.cell(col_widths[1], 7, str(row.get('nom', ''))[:24], border=1)
        pdf.cell(col_widths[2], 7, str(row.get('niveau', '')), border=1)
        pdf.cell(col_widths[3], 7, str(row.get('sexe', '')), border=1)
        pdf.cell(col_widths[4], 7, str(row.get('date_presence', '')), border=1, align='C')
        pdf.cell(col_widths[5], 7, str(row.get('heure_presence', '')), border=1, align='C')
        pdf.ln()

    # Retourne directement les bytes générés
    return bytes(pdf.output())






