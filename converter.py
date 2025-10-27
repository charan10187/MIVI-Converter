# converter.py
import streamlit as st
import os
import tempfile
import json
from pathlib import Path
from pdf2docx import Converter
from pdf2image import convert_from_path
from PyPDF2 import PdfReader
from PIL import Image
import pandas as pd
import shutil
from docx import Document
from fpdf import FPDF

st.set_page_config(page_title="MIVI Universal Converter", layout="wide")
st.title("📂 MIVI Universal File Converter 🗃️")
st.markdown("Developed by **S. Sri Charan** | 📧 [charan10187@gmail.com](mailto:charan10187@gmail.com)")

tab1, tab2 = st.tabs(["📄 File Converter", "🖼️ Image Resizer"])

# ---------- Helper ----------
def is_cloud_url(s: str) -> bool:
    if not s: 
        return False
    s = s.lower()
    return any(x in s for x in ["drive.google", "dropbox.com", "onedrive.live", "drive.googleusercontent", "googleusercontent"])

# ============================ FILE CONVERTER ============================ #
with tab1:
    st.header("📄 Smart File Converter")
    st.markdown("Upload a file from your device. If your file is on Google Drive/OneDrive/Dropbox, **download it first** to your device and then upload here.")
    cloud_url = st.text_input("Or paste cloud file link here (optional) — we'll explain how to use it", "")
    if cloud_url:
        if is_cloud_url(cloud_url):
            st.warning("Direct cloud links are **not** supported. Download the file to your device first (or use Google Drive API with OAuth). Then upload the downloaded file here.")
            st.info("Tip: In Google Drive, right-click → Download, then upload the downloaded file.")
        else:
            st.info("This URL doesn't look like a known cloud file link. Still, Streamlit requires an actual file upload — download first and upload.")

    uploaded_file = st.file_uploader("Upload any file (from your device)", type=None)
    if uploaded_file:
        input_name = uploaded_file.name
        input_ext = input_name.split(".")[-1].lower()

        # supported output options map
        format_map = {
            "pdf": ["docx", "txt", "jpg", "png"],
            "docx": ["pdf"],
            "png": ["pdf"],
            "jpg": ["pdf"],
            "jpeg": ["pdf"],
            "csv": ["json", "xlsx"],
            "json": ["csv", "xlsx"],
            "xlsx": ["csv", "json"],
        }
        options = format_map.get(input_ext, [])
        if not options:
            st.warning("Unsupported file type.")
        else:
            out_fmt = st.selectbox("Convert to", options)

            if st.button("🚀 Convert Now"):
                try:
                    with tempfile.TemporaryDirectory() as tmp:
                        in_path = os.path.join(tmp, input_name)
                        with open(in_path, "wb") as f:
                            f.write(uploaded_file.read())
                        out_path = os.path.join(tmp, Path(input_name).stem + f".{out_fmt}")

                        # PDF -> DOCX
                        if input_ext == "pdf" and out_fmt == "docx":
                            cv = Converter(in_path)
                            cv.convert(out_path)
                            cv.close()

                        # PDF -> TXT
                        elif input_ext == "pdf" and out_fmt == "txt":
                            reader = PdfReader(in_path)
                            text_parts = []
                            for page in reader.pages:
                                try:
                                    text_parts.append(page.extract_text() or "")
                                except Exception as e:
                                    text_parts.append(f"[Error reading page: {e}]")
                            text = "\n".join(text_parts)
                            with open(out_path, "w", encoding="utf-8", errors="ignore") as f:
                                f.write(text)

                        # PDF -> Image(s)
                        elif input_ext == "pdf" and out_fmt in ["jpg", "png"]:
                            pages = convert_from_path(in_path)
                            out_dir = os.path.join(tmp, "pdf_pages")
                            os.makedirs(out_dir, exist_ok=True)
                            for i, page in enumerate(pages):
                                page_path = os.path.join(out_dir, f"page_{i+1}.{out_fmt}")
                                page.save(page_path, out_fmt.upper())
                            # zip pages for single download
                            archive = shutil.make_archive(out_dir, "zip", out_dir)
                            out_path = archive

                        # DOCX -> PDF (simple text-preserving fallback)
                        elif input_ext == "docx" and out_fmt == "pdf":
                            doc = Document(in_path)
                            pdf = FPDF()
                            pdf.set_auto_page_break(auto=True, margin=15)
                            pdf.add_page()
                            pdf.set_font("Arial", size=12)
                            for para in doc.paragraphs:
                                # guard length
                                text = para.text or ""
                                pdf.multi_cell(0, 8, txt=text)
                            pdf.output(out_path)

                        # Image -> PDF
                        elif input_ext in ["png", "jpg", "jpeg"] and out_fmt == "pdf":
                            img = Image.open(in_path).convert("RGB")
                            img.save(out_path)

                        # CSV/JSON/XLSX conversions
                        elif input_ext == "csv" and out_fmt == "json":
                            df = pd.read_csv(in_path)
                            df.to_json(out_path, orient="records", indent=2)
                        elif input_ext == "csv" and out_fmt == "xlsx":
                            df = pd.read_csv(in_path)
                            df.to_excel(out_path, index=False)
                        elif input_ext == "json" and out_fmt == "csv":
                            df = pd.read_json(in_path)
                            df.to_csv(out_path, index=False)
                        elif input_ext == "json" and out_fmt == "xlsx":
                            df = pd.read_json(in_path)
                            df.to_excel(out_path, index=False)
                        elif input_ext == "xlsx" and out_fmt == "csv":
                            df = pd.read_excel(in_path)
                            df.to_csv(out_path, index=False)
                        elif input_ext == "xlsx" and out_fmt == "json":
                            df = pd.read_excel(in_path)
                            df.to_json(out_path, orient="records", indent=2)

                        else:
                            st.error("Conversion not supported yet for this combination.")

                        if os.path.exists(out_path):
                            with open(out_path, "rb") as f:
                                st.download_button(
                                    "📥 Download Converted File",
                                    f,
                                    file_name=os.path.basename(out_path),
                                    mime="application/octet-stream",
                                )
                        else:
                            st.error("❌ Output not found. Conversion may have failed.")

                except Exception as e:
                    st.error(f"❌ Error during conversion: {e}")

# ============================ IMAGE RESIZER ============================ #
with tab2:
    st.header("🖼️ Image Resizer")
    st.markdown("You can upload an image from device. Cloud links (Drive/Dropbox) are not supported — download first then upload.")
    cloud_img_url = st.text_input("Paste image cloud link (optional)")
    if cloud_img_url:
        if is_cloud_url(cloud_img_url):
            st.warning("Direct cloud upload is not supported. Please download the image to your device and then upload it here.")
        else:
            st.info("This doesn't look like a recognized cloud link. Still — Streamlit needs a file upload.")

    img_file = st.file_uploader("Upload an image (device only)", type=["png", "jpg", "jpeg", "bmp", "tiff"])
    if img_file:
        img = Image.open(img_file)
        st.image(img, caption="Original Image", use_container_width=True)

        resize_mode = st.radio("Resize Mode", ["By Dimensions", "By File Size (KB)"])

        # ---------- By Dimensions ----------
        if resize_mode == "By Dimensions":
            width = st.number_input("Width (px)", value=img.width, min_value=1)
            height = st.number_input("Height (px)", value=img.height, min_value=1)
            maintain = st.checkbox("Maintain aspect ratio", value=True)
            if maintain:
                height = int(img.height * (width / img.width))

            if st.button("Resize Now"):
                resized = img.resize((int(width), int(height)))
                st.image(resized, caption="Resized Image", use_container_width=True)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmpf:
                    # save as JPEG for consistent downloads
                    resized.save(tmpf.name, format="JPEG", quality=95)
                    tmpf.flush()
                    tmpf.seek(0)
                    with open(tmpf.name, "rb") as fd:
                        st.download_button("📥 Download Resized Image", fd, file_name=f"resized_{img_file.name}", mime="image/jpeg")

        # ---------- By File Size (KB) ----------
        else:
            target_kb = st.number_input("Target size (KB)", min_value=10, max_value=5000, value=200)
            if st.button("Compress Now"):
                # convert to JPEG if needed (PNG compression isn't quality-based)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmpf:
                    quality = 95
                    # Work on a copy to avoid corrupting original
                    working = img.convert("RGB")
                    # progressively reduce quality until size <= target_kb or quality too low
                    while quality >= 5:
                        working.save(tmpf.name, format="JPEG", quality=int(quality))
                        size_kb = os.path.getsize(tmpf.name) / 1024
                        if size_kb <= target_kb:
                            break
                        quality -= 5
                    # final check
                    size_kb = os.path.getsize(tmpf.name) / 1024
                    st.success(f"Compressed to ~{int(size_kb)} KB at quality {quality}")
                    with open(tmpf.name, "rb") as fd:
                        st.download_button("📥 Download Compressed Image", fd, file_name=f"compressed_{img_file.name}", mime="image/jpeg")
