import streamlit as st
from PIL import Image
import io
from PyPDF2 import PdfReader
from docx import Document
import pandas as pd
import json

st.set_page_config(page_title="MIVI Converter", page_icon="📁", layout="centered")

st.title("📂 Converter")
st.caption("Developed by **S. Sri Charan** | 📧 charan10187@gmail.com")

tab1, tab2 = st.tabs(["File Converter", "Image Resizer"])

# ==============================
# FILE CONVERTER TAB
# ==============================
with tab1:
    st.subheader("Convert Files")
    file = st.file_uploader("Upload your file", type=["pdf", "docx", "txt", "csv", "json", "xlsx", "jpg", "png"])
    conversion_type = st.selectbox("Choose conversion type", [
        "PDF ➜ Word",
        "PDF ➜ Text",
        "Word ➜ PDF",
        "CSV ➜ Excel",
        "Excel ➜ CSV",
        "CSV ➜ JSON",
        "JSON ➜ CSV"
    ])

    if st.button("Convert"):
        if file is None:
            st.error("Please upload a file first!")
        else:
            try:
                if conversion_type == "PDF ➜ Text":
                    reader = PdfReader(file)
                    text = "\n".join(page.extract_text() or "" for page in reader.pages)
                    st.download_button("Download TXT", text, file_name="converted.txt")

                elif conversion_type == "PDF ➜ Word":
                    reader = PdfReader(file)
                    text = "\n".join(page.extract_text() or "" for page in reader.pages)
                    doc = Document()
                    doc.add_paragraph(text)
                    buf = io.BytesIO()
                    doc.save(buf)
                    st.download_button("Download DOCX", buf.getvalue(), file_name="converted.docx")

                elif conversion_type == "Word ➜ PDF":
                    doc = Document(file)
                    text = "\n".join([p.text for p in doc.paragraphs])
                    pdf_bytes = text.encode("utf-8")
                    st.download_button("Download PDF", pdf_bytes, file_name="converted.pdf")

                elif conversion_type == "CSV ➜ Excel":
                    df = pd.read_csv(file)
                    buf = io.BytesIO()
                    df.to_excel(buf, index=False)
                    st.download_button("Download XLSX", buf.getvalue(), file_name="converted.xlsx")

                elif conversion_type == "Excel ➜ CSV":
                    df = pd.read_excel(file)
                    buf = io.BytesIO()
                    df.to_csv(buf, index=False)
                    st.download_button("Download CSV", buf.getvalue(), file_name="converted.csv")

                elif conversion_type == "CSV ➜ JSON":
                    df = pd.read_csv(file)
                    json_str = df.to_json(orient="records", indent=2)
                    st.download_button("Download JSON", json_str, file_name="converted.json")

                elif conversion_type == "JSON ➜ CSV":
                    data = json.load(file)
                    df = pd.DataFrame(data)
                    buf = io.BytesIO()
                    df.to_csv(buf, index=False)
                    st.download_button("Download CSV", buf.getvalue(), file_name="converted.csv")

            except Exception as e:
                st.error(f"Error: {str(e)}")

# ==============================
# IMAGE RESIZER TAB
# ==============================
with tab2:
    st.subheader("Image Resizer")
    img_file = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg", "bmp", "tiff"])
    width = st.number_input("Width", min_value=1, value=300)
    height = st.number_input("Height", min_value=1, value=300)

    if img_file:
        try:
            image = Image.open(img_file)
            resized = image.resize((width, height))
            buf = io.BytesIO()
            resized.save(buf, format=image.format or "PNG")
            st.image(resized, caption="Resized Image", use_column_width=True)
            st.download_button("Download Image", buf.getvalue(), file_name=f"resized.{image.format.lower()}")
        except Exception as e:
            st.error(f"Error resizing image: {e}")
