import streamlit as st
import os
import tempfile
from pathlib import Path
from docx2pdf import convert as docx2pdf_convert
from pdf2docx import Converter
from pdf2image import convert_from_path
from PyPDF2 import PdfReader
from PIL import Image
import pandas as pd
import json
import shutil
import sys

# Auto-configure Poppler path if on Windows
if sys.platform.startswith("win"):
    poppler_path = Path("C:/poppler/Library/bin")
    if not poppler_path.exists():
        os.makedirs(poppler_path, exist_ok=True)
    os.environ["PATH"] += os.pathsep + str(poppler_path)

st.set_page_config(page_title="EZIPZ Universal Converter", layout="wide")
st.title("📂 EZIPZ Universal File Converter 🗃️")

tab1, tab2 = st.tabs(["📄 File Converter", "🖼️ Image Resizer"])

# ============================ FILE CONVERTER ============================ #
with tab1:
    st.header("📄 Smart File Converter")
    uploaded_file = st.file_uploader("Upload any file", type=None)

    if uploaded_file:
        input_name = uploaded_file.name
        input_ext = input_name.split(".")[-1].lower()

        options = []
        if input_ext in ["pdf"]:
            options = ["docx", "jpg", "png", "txt"]
        elif input_ext in ["docx", "doc"]:
            options = ["pdf"]
        elif input_ext in ["png", "jpg", "jpeg", "bmp", "tiff"]:
            options = ["pdf"]
        elif input_ext in ["csv"]:
            options = ["xlsx", "json"]
        elif input_ext in ["json"]:
            options = ["xlsx", "csv"]
        else:
            options = ["pdf"]

        output_format = st.selectbox("Choose output format", options)

        if st.button("Convert Now"):
            try:
                with tempfile.TemporaryDirectory() as tmpdir:
                    input_path = os.path.join(tmpdir, input_name)
                    with open(input_path, "wb") as f:
                        f.write(uploaded_file.read())

                    output_path = None

                    # DOCX → PDF
                    if input_ext in ["docx", "doc"] and output_format == "pdf":
                        docx2pdf_convert(input_path, tmpdir)
                        output_path = os.path.join(tmpdir, Path(input_name).stem + ".pdf")

                    # PDF → DOCX
                    elif input_ext == "pdf" and output_format == "docx":
                        output_path = os.path.join(tmpdir, Path(input_name).stem + ".docx")
                        cv = Converter(input_path)
                        cv.convert(output_path)
                        cv.close()

                    # PDF → Images (JPG/PNG)
                    elif input_ext == "pdf" and output_format in ["jpg", "png"]:
                        pages = convert_from_path(input_path, poppler_path=poppler_path)
                        output_dir = os.path.join(tmpdir, "pdf_images")
                        os.makedirs(output_dir, exist_ok=True)
                        for i, page in enumerate(pages):
                            page_path = os.path.join(output_dir, f"page_{i+1}.{output_format}")
                            page.save(page_path, output_format.upper())
                        shutil.make_archive(output_dir, 'zip', output_dir)
                        output_path = output_dir + ".zip"

                    # PDF → Text
                    elif input_ext == "pdf" and output_format == "txt":
                        reader = PdfReader(input_path)
                        text = "\n".join([page.extract_text() or "" for page in reader.pages])
                        output_path = os.path.join(tmpdir, Path(input_name).stem + ".txt")
                        with open(output_path, "w", encoding="utf-8") as f:
                            f.write(text)

                    # Image → PDF
                    elif input_ext in ["png", "jpg", "jpeg", "bmp", "tiff"] and output_format == "pdf":
                        img = Image.open(input_path).convert("RGB")
                        output_path = os.path.join(tmpdir, Path(input_name).stem + ".pdf")
                        img.save(output_path)

                    # CSV → Excel or JSON
                    elif input_ext == "csv" and output_format == "xlsx":
                        df = pd.read_csv(input_path)
                        output_path = os.path.join(tmpdir, Path(input_name).stem + ".xlsx")
                        df.to_excel(output_path, index=False)
                    elif input_ext == "csv" and output_format == "json":
                        df = pd.read_csv(input_path)
                        output_path = os.path.join(tmpdir, Path(input_name).stem + ".json")
                        df.to_json(output_path, orient="records", indent=2)

                    # JSON → Excel or CSV
                    elif input_ext == "json" and output_format in ["xlsx", "csv"]:
                        with open(input_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        df = pd.DataFrame(data)
                        if output_format == "xlsx":
                            output_path = os.path.join(tmpdir, Path(input_name).stem + ".xlsx")
                            df.to_excel(output_path, index=False)
                        else:
                            output_path = os.path.join(tmpdir, Path(input_name).stem + ".csv")
                            df.to_csv(output_path, index=False)

                    if output_path and os.path.exists(output_path):
                        with open(output_path, "rb") as f:
                            st.download_button(
                                label="📥 Download Converted File",
                                data=f,
                                file_name=os.path.basename(output_path),
                                mime="application/octet-stream",
                            )
                    else:
                        st.error("❌ Conversion failed or file not found.")

            except Exception as e:
                st.error(f"❌ Error during conversion: {e}")

# ============================ IMAGE RESIZER ============================ #
with tab2:
    st.header("🖼️ Image Resizer")
    img_file = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg", "bmp", "tiff"])

    if img_file:
        img = Image.open(img_file)
        st.image(img, caption="Original Image", use_container_width=True)

        resize_type = st.radio("Resize Type", ["By Dimensions", "By File Size (KB)"])

        if resize_type == "By Dimensions":
            width = st.number_input("Width (px)", value=img.width, min_value=1)
            height = st.number_input("Height (px)", value=img.height, min_value=1)
            maintain_ratio = st.checkbox("Maintain aspect ratio", value=True)
            if maintain_ratio:
                height = int(img.height * (width / img.width))

            if st.button("Resize Now"):
                resized_img = img.resize((int(width), int(height)))
                st.image(resized_img, caption="Resized Image", use_container_width=True)

                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmpfile:
                    resized_img.save(tmpfile.name, format="JPEG", quality=95)
                    with open(tmpfile.name, "rb") as f:
                        st.download_button(
                            "📥 Download Resized Image",
                            f,
                            file_name=f"resized_{img_file.name}",
                            mime="image/jpeg",
                        )

        else:
            target_kb = st.number_input("Target size (KB)", min_value=10, max_value=5000, value=200)
            if st.button("Compress Now"):
                temp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                quality = 95
                while quality > 5:
                    img.save(temp.name, format="JPEG", quality=quality)
                    size_kb = os.path.getsize(temp.name) / 1024
                    if size_kb <= target_kb:
                        break
                    quality -= 5

                st.success(f"✅ Compressed to ~{int(size_kb)} KB at quality {quality}")
                with open(temp.name, "rb") as f:
                    st.download_button(
                        "📥 Download Compressed Image",
                        f,
                        file_name=f"compressed_{img_file.name}",
                        mime="image/jpeg",
                    )
