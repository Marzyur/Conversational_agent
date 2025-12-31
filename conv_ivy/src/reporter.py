from fpdf import FPDF
import io

def generate_career_pdf(scribe):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(200, 10, "HelloIvy Career Discovery Report", ln=True, align='C')
    
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, f"Student: {scribe['name']} (Grade {scribe['grade']})", ln=True)
    
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, "Top Interests:", ln=True)
    pdf.set_font("Arial", '', 12)
    for i in scribe['interests']:
        pdf.cell(200, 8, f"- {i}", ln=True)

    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, "Key Strengths:", ln=True)
    pdf.set_font("Arial", '', 12)
    for s in scribe['strengths']:
        pdf.cell(200, 8, f"- {s}", ln=True)

    # Return a bytes object suitable for Streamlit's download_button
    pdf_out = pdf.output(dest='S')
    # pdf.output may return str, bytes, or bytearray depending on FPDF version
    if isinstance(pdf_out, str):
        return pdf_out.encode('latin-1')
    elif isinstance(pdf_out, (bytes, bytearray)):
        return bytes(pdf_out)
    else:
        # Fallback: convert to string then encode
        return str(pdf_out).encode('latin-1')