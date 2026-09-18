import qrcode
from io import BytesIO

def generer_qr_code(data_str):
    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=2,
    )
    qr.add_data(data_str)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Conversion en buffer BytesIO pour Streamlit
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()






