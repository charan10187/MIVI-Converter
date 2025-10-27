import streamlit as st
import os
import tempfile
import shutil
from pathlib import Path
from docx2pdf import convert as docx2pdf_convert
from pdf2docx import Converter
from PIL import Image
import pythoncom
import win32com.client

st.set_page_config(page_title="EZIPZ File Converter", layout="wide")
st.title("📂 MIVI CONVERTED 🗃️")

tab1, tab2 = st.tabs(["📄 File Converter", "🖼️ Image Resizer"])

with tab1:
    st.header("📄 Smart File Converter")
    uploaded_file = st.file_uploader("Upload any file", type=None)

    if uploaded_file:
        input_name = uploaded_file.name
        input_ext = input_name.split(".")[-1].lower()
        options = []

        if input_ext in ["docx", "doc"]:
            options = ["pdf"]
        elif input_ext in ["pdf"]:
            options = ["docx"]
        elif input_ext in ["png", "jpg", "jpeg", "bmp", "tiff"]:
            options = ["pdf"]
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
                        output_path = os.path.join(tmpdir, Path(input_name).stem + ".pdf")
                        docx2pdf_convert(input_path, tmpdir)

                    # PDF → DOCX
                    elif input_ext == "pdf" and output_format == "docx":
                        output_path = os.path.join(tmpdir, Path(input_name).stem + ".docx")
                        cv = Converter(input_path)
                        cv.convert(output_path)
                        cv.close()

                    # Image → PDF
                    elif input_ext in ["png", "jpg", "jpeg", "bmp", "tiff"] and output_format == "pdf":
                        img = Image.open(input_path).convert("RGB")
                        output_path = os.path.join(tmpdir, Path(input_name).stem + ".pdf")
                        img.save(output_path)

                    if output_path and os.path.exists(output_path):
                        with open(output_path, "rb") as f:
                            st.download_button(
                                label="📥 Download Converted File",
                                data=f,
                                file_name=os.path.basename(output_path),
                                mime="application/octet-stream",
                            )
                    else:
                        st.error("❌ Conversion failed or output not found.")

            except Exception as e:
                st.error(f"❌ Error during conversion: {e}")
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

        else:  # By File Size
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
