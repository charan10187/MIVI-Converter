import streamlit as st
from pathlib import Path
from pdf2docx import Converter
from PIL import Image
import pandas as pd
import json
import tempfile
import os
from docx import Document
from fpdf import FPDF
from pdf2image import convert_from_path

st.set_page_config(page_title="EZIPZ File Converter", layout="wide")
st.title("📂 MIVI CONVERTER 🗃️")
st.markdown("Developed by **S. Sri Charan** | 📧 [charan10187@gmail.com](mailto:charan10187@gmail.com)")

tab1, tab2 = st.tabs(["📄 File Converter", "🖼️ Image Resizer"])

# ========== FILE CONVERTER ==========
with tab1:
    st.header("📄 Smart File Converter")
    uploaded = st.file_uploader("Upload any file", type=None)

    if uploaded:
        in_name = uploaded.name
        in_ext = in_name.split(".")[-1].lower()

        # Dynamic output options
        format_map = {
            "pdf": ["docx", "txt", "jpg"],
            "docx": ["pdf"],
            "png": ["pdf"],
            "jpg": ["pdf"],
            "jpeg": ["pdf"],
            "csv": ["json", "xlsx"],
            "json": ["csv", "xlsx"],
            "xlsx": ["csv", "json"],
        }
        options = format_map.get(in_ext, [])
        if not options:
            st.warning("⚠️ Unsupported file type.")
        else:
            out_fmt = st.selectbox("Convert to", options)

            if st.button("🚀 Convert Now"):
                try:
                    with tempfile.TemporaryDirectory() as tmp:
                        in_path = os.path.join(tmp, in_name)
                        with open(in_path, "wb") as f:
                            f.write(uploaded.read())

                        out_path = os.path.join(tmp, Path(in_name).stem + f".{out_fmt}")

                        # ========== Conversion Logic ==========
                        # PDF → DOCX
                        if in_ext == "pdf" and out_fmt == "docx":
                            cv = Converter(in_path)
                            cv.convert(out_path)
                            cv.close()

                        # PDF → TXT
                        elif in_ext == "pdf" and out_fmt == "txt":
                            from PyPDF2 import PdfReader
                            reader = PdfReader(in_path)
                            text = "\n".join(page.extract_text() or "" for page in reader.pages)
                            with open(out_path, "w", encoding="utf-8") as f:
                                f.write(text)

                        # PDF → Image (JPG)
                        elif in_ext == "pdf" and out_fmt == "jpg":
                            pages = convert_from_path(in_path, 300)
                            pages[0].save(out_path, "JPEG")

                        # DOCX → PDF
                        elif in_ext == "docx" and out_fmt == "pdf":
                            doc = Document(in_path)
                            pdf = FPDF()
                            pdf.add_page()
                            pdf.set_font("Arial", size=12)
                            for para in doc.paragraphs:
                                pdf.multi_cell(0, 10, para.text)
                            pdf.output(out_path)

                        # Image → PDF
                        elif in_ext in ["png", "jpg", "jpeg"] and out_fmt == "pdf":
                            img = Image.open(in_path).convert("RGB")
                            img.save(out_path)

                        # CSV ↔ JSON ↔ XLSX
                        elif in_ext == "csv" and out_fmt == "json":
                            df = pd.read_csv(in_path)
                            df.to_json(out_path, orient="records", indent=4)

                        elif in_ext == "json" and out_fmt == "csv":
                            df = pd.read_json(in_path)
                            df.to_csv(out_path, index=False)

                        elif in_ext == "csv" and out_fmt == "xlsx":
                            df = pd.read_csv(in_path)
                            df.to_excel(out_path, index=False)

                        elif in_ext == "xlsx" and out_fmt == "csv":
                            df = pd.read_excel(in_path)
                            df.to_csv(out_path, index=False)

                        elif in_ext == "json" and out_fmt == "xlsx":
                            df = pd.read_json(in_path)
                            df.to_excel(out_path, index=False)

                        elif in_ext == "xlsx" and out_fmt == "json":
                            df = pd.read_excel(in_path)
                            df.to_json(out_path, orient="records", indent=4)

                        # =====================================

                        if os.path.exists(out_path):
                            with open(out_path, "rb") as f:
                                st.download_button(
                                    label="📥 Download Converted File",
                                    data=f,
                                    file_name=os.path.basename(out_path),
                                    mime="application/octet-stream",
                                )
                        else:
                            st.error("❌ Conversion failed.")
                except Exception as e:
                    st.error(f"❌ Error: {e}")

# ========== IMAGE RESIZER ==========
with tab2:
    st.header("🖼️ Image Resizer")
    img_file = st.file_uploader("Upload image", type=["png", "jpg", "jpeg", "bmp", "tiff"])
    if img_file:
        img = Image.open(img_file)
        st.image(img, caption="Original", use_container_width=True)

        mode = st.radio("Resize mode", ["By Dimensions", "By File Size (KB)"])

        if mode == "By Dimensions":
            w = st.number_input("Width (px)", value=img.width, min_value=1)
            h = st.number_input("Height (px)", value=img.height, min_value=1)
            keep_ratio = st.checkbox("Keep aspect ratio", True)

            if keep_ratio:
                h = int(img.height * (w / img.width))

            if st.button("Resize"):
                resized = img.resize((int(w), int(h)))
                st.image(resized, caption="Resized", use_container_width=True)

                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                resized.save(tmp.name, "JPEG", quality=95)
                with open(tmp.name, "rb") as f:
                    st.download_button("📥 Download Resized Image", f, file_name="resized.jpg")

        else:
            target_kb = st.number_input("Target Size (KB)", 10, 5000, 200)
            if st.button("Compress"):
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                q = 95
                while q > 5:
                    img.save(tmp.name, "JPEG", quality=q)
                    if os.path.getsize(tmp.name) / 1024 <= target_kb:
                        break
                    q -= 5
                with open(tmp.name, "rb") as f:
                    st.download_button("📥 Download Compressed", f, file_name="compressed.jpg")
