import streamlit as st
from PIL import Image
import io
from PyPDF2 import PdfReader
from docx import Document
import pandas as pd
import json

st.set_page_config(page_title="MIVI Universal Converter", page_icon="📁", layout="wide")
st.title("📂 MIVI Universal File Converter 🗃️")
st.markdown("Developed by **S. Sri Charan** | 📧 [charan10187@gmail.com](mailto:charan10187@gmail.com)")
st.markdown("⚠️ **Note:** Only local files are supported. Cloud links (Google Drive, Dropbox, OneDrive) are not accepted — please download them first.")
tab1, tab2 = st.tabs(["File Converter", "Image Resizer"])

# =======================================
# FILE CONVERTER TAB
# =======================================
with tab1:
    st.subheader("Smart File Converter")

    file = st.file_uploader("Upload your file", type=["pdf", "docx", "txt", "csv", "json", "xlsx", "jpg", "png"])

    if file:
        ext = file.name.split(".")[-1].lower()

        # Auto-select conversion options based on file type
        if ext == "pdf":
            conversions = ["PDF ➜ Word", "PDF ➜ Text"]
        elif ext == "docx":
            conversions = ["Word ➜ PDF"]
        elif ext == "csv":
            conversions = ["CSV ➜ Excel", "CSV ➜ JSON"]
        elif ext == "xlsx":
            conversions = ["Excel ➜ CSV"]
        elif ext == "json":
            conversions = ["JSON ➜ CSV"]
        else:
            conversions = ["Unsupported conversion"]

        conversion_type = st.selectbox("Detected file type and possible conversions:", conversions)

        if "Unsupported" not in conversion_type:
            if st.button("Convert Now"):
                try:
                    base_name = file.name.rsplit('.', 1)[0]

                    if conversion_type == "PDF ➜ Text":
                        reader = PdfReader(file)
                        text = "\n".join(page.extract_text() or "" for page in reader.pages)
                        st.download_button(
                            "Download TXT",
                            text,
                            file_name=f"{base_name}_converted.txt"
                        )

                    elif conversion_type == "PDF ➜ Word":
                        reader = PdfReader(file)
                        text = "\n".join(page.extract_text() or "" for page in reader.pages)
                        doc = Document()
                        doc.add_paragraph(text)
                        buf = io.BytesIO()
                        doc.save(buf)
                        st.download_button(
                            "Download DOCX",
                            buf.getvalue(),
                            file_name=f"{base_name}_converted.docx"
                        )

                    elif conversion_type == "Word ➜ PDF":
                        doc = Document(file)
                        text = "\n".join([p.text for p in doc.paragraphs])
                        pdf_bytes = text.encode("utf-8")
                        st.download_button(
                            "Download PDF",
                            pdf_bytes,
                            file_name=f"{base_name}_converted.pdf"
                        )

                    elif conversion_type == "CSV ➜ Excel":
                        df = pd.read_csv(file)
                        buf = io.BytesIO()
                        df.to_excel(buf, index=False)
                        st.download_button(
                            "Download XLSX",
                            buf.getvalue(),
                            file_name=f"{base_name}_converted.xlsx"
                        )

                    elif conversion_type == "Excel ➜ CSV":
                        df = pd.read_excel(file)
                        buf = io.BytesIO()
                        df.to_csv(buf, index=False)
                        st.download_button(
                            "Download CSV",
                            buf.getvalue(),
                            file_name=f"{base_name}_converted.csv"
                        )

                    elif conversion_type == "CSV ➜ JSON":
                        df = pd.read_csv(file)
                        json_str = df.to_json(orient="records", indent=2)
                        st.download_button(
                            "Download JSON",
                            json_str,
                            file_name=f"{base_name}_converted.json"
                        )

                    elif conversion_type == "JSON ➜ CSV":
                        data = json.load(file)
                        df = pd.DataFrame(data)
                        buf = io.BytesIO()
                        df.to_csv(buf, index=False)
                        st.download_button(
                            "Download CSV",
                            buf.getvalue(),
                            file_name=f"{base_name}_converted.csv"
                        )

                except Exception as e:
                    st.error(f"Error: {str(e)}")

# =======================================
# IMAGE RESIZER TAB
# =======================================
with tab2:
    st.subheader("Image Resizer")

    img_file = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg", "bmp", "tiff"])
    resize_mode = st.radio("Resize mode", ["By Dimensions", "By File Size (KB)"])

    if img_file:
        try:
            image = Image.open(img_file)

            # --- Resize by Dimensions ---
            if resize_mode == "By Dimensions":
                width = st.number_input("Width", min_value=1, value=image.width)
                height = st.number_input("Height", min_value=1, value=image.height)
                maintain_ratio = st.checkbox("Maintain aspect ratio", value=True)

                if maintain_ratio:
                    height = int(image.height * (width / image.width))

                if st.button("Resize Now"):
                    resized = image.resize((int(width), int(height)))
                    buf = io.BytesIO()
                    resized.save(buf, format=image.format or "PNG")
                    st.image(resized, caption="Resized Image", use_column_width=True)
                    st.download_button(
                        "Download Image",
                        buf.getvalue(),
                        file_name=f"{img_file.name.rsplit('.',1)[0]}_resized.{(image.format or 'png').lower()}"
                    )

            # --- Resize by File Size (KB) ---
            elif resize_mode == "By File Size (KB)":
                target_kb = st.number_input("Target Size (KB)", min_value=10, max_value=5000, value=200)
                if st.button("Compress Now"):
                    buf = io.BytesIO()
                    quality = 95
                    image = image.convert("RGB")

                    while quality > 5:
                        buf.truncate(0)
                        buf.seek(0)
                        image.save(buf, format="JPEG", quality=quality)
                        size_kb = len(buf.getvalue()) / 1024
                        if size_kb <= target_kb:
                            break
                        quality -= 5

                    st.success(f"Compressed to ~{int(size_kb)} KB at quality {quality}")
                    st.image(image, caption="Compressed Image", use_column_width=True)
                    st.download_button(
                        "Download Compressed Image",
                        buf.getvalue(),
                        file_name=f"{img_file.name.rsplit('.',1)[0]}_compressed.jpg",
                        mime="image/jpeg"
                    )

        except Exception as e:
            st.error(f"Error processing image: {e}")
