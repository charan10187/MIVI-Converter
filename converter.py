# app.py
import streamlit as st
from io import BytesIO
from PIL import Image
from PyPDF2 import PdfReader
from docx import Document
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import pandas as pd
import json

st.set_page_config(page_title="MIVI Converter - Rebuilt", page_icon="📁", layout="centered")
st.title("📂 MIVI Converter")
st.caption("Developed by S. Sri Charan — rebuilt for submission")

# ---------------------
# Helpers
# ---------------------
def detect_ext(name: str):
    if not name or "." not in name:
        return None
    return name.rsplit(".", 1)[1].lower()

def make_filename(orig_name: str, tag: str, ext: str):
    base = orig_name.rsplit(".", 1)[0]
    return f"{base}_{tag}.{ext}"

def bytes_from_uploaded(uploaded):
    uploaded.seek(0)
    return uploaded.read()

def pdf_text_from_bytes(pdf_bytes: bytes):
    reader = PdfReader(BytesIO(pdf_bytes))
    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return "\n\n".join(pages)

def docx_from_text(text: str) -> bytes:
    doc = Document()
    for block in text.split("\n\n"):
        doc.add_paragraph(block)
    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()

def pdf_from_text(text: str) -> bytes:
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    lines = text.splitlines()
    y = height - 40
    line_height = 12
    for line in lines:
        if y < 40:
            c.showPage()
            y = height - 40
        # wrap long lines simply
        if len(line) > 120:
            # naive wrap
            chunks = [line[i:i+120] for i in range(0, len(line), 120)]
            for ch in chunks:
                c.drawString(40, y, ch)
                y -= line_height
                if y < 40:
                    c.showPage()
                    y = height - 40
        else:
            c.drawString(40, y, line)
            y -= line_height
    c.save()
    buf.seek(0)
    return buf.getvalue()

# ---------------------
# UI
# ---------------------
tab1, tab2 = st.tabs(["File Converter", "Image Resizer"])

# -------- File Converter --------
with tab1:
    st.subheader("Smart File Converter")
    uploaded = st.file_uploader("Upload file", type=["pdf", "docx", "txt", "csv", "json", "xlsx"], key="file_uploader")
    if uploaded:
        ext = detect_ext(uploaded.name)
        st.markdown(f"**Detected:** `{ext}`")
        options = []
        if ext == "pdf":
            options = ["PDF ➜ Word (docx)", "PDF ➜ Text", "PDF ➜ PDF (same)"]
        elif ext == "docx":
            options = ["Word ➜ PDF", "Word ➜ Text", "Word ➜ DOCX (same)"]
        elif ext == "csv":
            options = ["CSV ➜ Excel", "CSV ➜ JSON", "CSV ➜ CSV (same)"]
        elif ext in ("xlsx", "xls"):
            options = ["Excel ➜ CSV", "Excel ➜ JSON", "Excel ➜ Excel (same)"]
        elif ext == "json":
            options = ["JSON ➜ CSV", "JSON ➜ Excel", "JSON ➜ JSON (same)"]
        else:
            st.error("Unsupported extension for converter.")
            options = []

        conversion = st.selectbox("Choose conversion", options)
        if st.button("Convert", key="convert"):
            try:
                prog = st.progress(0)
                status = st.empty()
                prog.progress(5)
                orig_bytes = bytes_from_uploaded(uploaded)
                prog.progress(15)

                out_bytes = None
                out_name = None

                # PDF conversions
                if conversion == "PDF ➜ Text":
                    status.text("Extracting text from PDF...")
                    text = pdf_text_from_bytes(orig_bytes)
                    out_bytes = text.encode("utf-8")
                    out_name = make_filename(uploaded.name, "converted", "txt")
                    prog.progress(90)

                elif conversion == "PDF ➜ Word (docx)":
                    status.text("Extracting text from PDF...")
                    text = pdf_text_from_bytes(orig_bytes)
                    prog.progress(50)
                    status.text("Generating DOCX...")
                    out_bytes = docx_from_text(text)
                    out_name = make_filename(uploaded.name, "converted", "docx")
                    prog.progress(95)

                elif conversion == "PDF ➜ PDF (same)":
                    out_bytes = orig_bytes
                    out_name = make_filename(uploaded.name, "copy", "pdf")
                    prog.progress(95)

                # Word conversions
                elif conversion == "Word ➜ Text":
                    status.text("Reading DOCX...")
                    doc = Document(BytesIO(orig_bytes))
                    text = "\n\n".join(p.text for p in doc.paragraphs)
                    out_bytes = text.encode("utf-8")
                    out_name = make_filename(uploaded.name, "converted", "txt")
                    prog.progress(95)

                elif conversion == "Word ➜ PDF":
                    status.text("Reading DOCX...")
                    doc = Document(BytesIO(orig_bytes))
                    text = "\n\n".join(p.text for p in doc.paragraphs)
                    status.text("Rendering PDF (text-only)...")
                    out_bytes = pdf_from_text(text)
                    out_name = make_filename(uploaded.name, "converted", "pdf")
                    prog.progress(95)

                elif conversion == "Word ➜ DOCX (same)":
                    out_bytes = orig_bytes
                    out_name = make_filename(uploaded.name, "copy", "docx")
                    prog.progress(95)

                # CSV / Excel / JSON conversions
                elif conversion == "CSV ➜ Excel":
                    status.text("Reading CSV...")
                    df = pd.read_csv(BytesIO(orig_bytes))
                    buf = BytesIO()
                    df.to_excel(buf, index=False)
                    out_bytes = buf.getvalue()
                    out_name = make_filename(uploaded.name, "converted", "xlsx")
                    prog.progress(95)

                elif conversion == "CSV ➜ JSON":
                    status.text("Reading CSV...")
                    df = pd.read_csv(BytesIO(orig_bytes))
                    out_bytes = df.to_json(orient="records", indent=2).encode("utf-8")
                    out_name = make_filename(uploaded.name, "converted", "json")
                    prog.progress(95)

                elif conversion == "CSV ➜ CSV (same)":
                    out_bytes = orig_bytes
                    out_name = make_filename(uploaded.name, "copy", "csv")
                    prog.progress(95)

                elif conversion == "Excel ➜ CSV":
                    status.text("Reading Excel...")
                    df = pd.read_excel(BytesIO(orig_bytes))
                    buf = BytesIO()
                    df.to_csv(buf, index=False)
                    out_bytes = buf.getvalue()
                    out_name = make_filename(uploaded.name, "converted", "csv")
                    prog.progress(95)

                elif conversion == "Excel ➜ JSON":
                    status.text("Reading Excel...")
                    df = pd.read_excel(BytesIO(orig_bytes))
                    out_bytes = df.to_json(orient="records", indent=2).encode("utf-8")
                    out_name = make_filename(uploaded.name, "converted", "json")
                    prog.progress(95)

                elif conversion == "Excel ➜ Excel (same)":
                    out_bytes = orig_bytes
                    out_name = make_filename(uploaded.name, "copy", ext)

                elif conversion == "JSON ➜ CSV":
                    status.text("Reading JSON...")
                    data = json.loads(orig_bytes.decode("utf-8"))
                    df = pd.DataFrame(data)
                    buf = BytesIO()
                    df.to_csv(buf, index=False)
                    out_bytes = buf.getvalue()
                    out_name = make_filename(uploaded.name, "converted", "csv")
                    prog.progress(95)

                elif conversion == "JSON ➜ Excel":
                    status.text("Reading JSON...")
                    data = json.loads(orig_bytes.decode("utf-8"))
                    df = pd.DataFrame(data)
                    buf = BytesIO()
                    df.to_excel(buf, index=False)
                    out_bytes = buf.getvalue()
                    out_name = make_filename(uploaded.name, "converted", "xlsx")
                    prog.progress(95)

                elif conversion == "JSON ➜ JSON (same)":
                    out_bytes = orig_bytes
                    out_name = make_filename(uploaded.name, "copy", "json")

                else:
                    st.error("Unsupported conversion selected.")
                    out_bytes = None

                prog.progress(100)
                status.text("Conversion complete.")
                if out_bytes:
                    st.download_button("Download", data=out_bytes, file_name=out_name, key="download_conv")
            except Exception as e:
                st.error(f"Conversion failed: {e}")

# -------- Image Resizer --------
with tab2:
    st.subheader("Image Resizer")
    img_uploaded = st.file_uploader("Upload image", type=["png", "jpg", "jpeg", "bmp", "tiff"], key="img")
    if img_uploaded:
        try:
            img_bytes = bytes_from_uploaded(img_uploaded)
            img = Image.open(BytesIO(img_bytes))
            st.image(img, caption="Original", use_column_width=True)

            mode = st.radio("Mode", ["By Dimensions", "By File Size (KB)"])
            if mode == "By Dimensions":
                width = st.number_input("Width (px)", value=img.width, min_value=1)
                height = st.number_input("Height (px)", value=img.height, min_value=1)
                maintain = st.checkbox("Maintain aspect ratio", value=True)
                if maintain:
                    height = int(img.height * (width / img.width))
                if st.button("Resize", key="resize_btn"):
                    prog = st.progress(0)
                    prog.progress(10)
                    resized = img.resize((int(width), int(height)))
                    prog.progress(60)
                    buf = BytesIO()
                    fmt = (img.format or "PNG").upper()
                    if fmt == "PNG":
                        resized.save(buf, format="PNG")
                        out_ext = "png"
                        mime = "image/png"
                    else:
                        # save JPEG for other formats
                        resized = resized.convert("RGB")
                        resized.save(buf, format="JPEG", quality=95)
                        out_ext = "jpg"
                        mime = "image/jpeg"
                    prog.progress(100)
                    st.image(Image.open(BytesIO(buf.getvalue())), caption="Resized preview", use_column_width=True)
                    st.download_button("Download Resized", data=buf.getvalue(),
                                       file_name=make_filename(img_uploaded.name, "resized", out_ext),
                                       mime=mime, key="download_resized")
            else:
                target_kb = st.number_input("Target size (KB)", min_value=10, max_value=10000, value=200)
                if st.button("Compress", key="compress_btn"):
                    prog = st.progress(0)
                    prog.progress(5)
                    working = img.convert("RGB")
                    buf = BytesIO()
                    quality = 95
                    size_kb = None
                    while quality > 5:
                        buf.truncate(0)
                        buf.seek(0)
                        working.save(buf, format="JPEG", quality=quality)
                        size_kb = len(buf.getvalue()) / 1024
                        prog.progress(int(5 + 90 * (95 - quality) / 90))
                        if size_kb <= target_kb:
                            break
                        quality -= 5
                    prog.progress(100)
                    st.success(f"Compressed to ~{int(size_kb)} KB at quality {quality}")
                    st.image(Image.open(BytesIO(buf.getvalue())), caption="Compressed preview", use_column_width=True)
                    st.download_button("Download Compressed", data=buf.getvalue(),
                                       file_name=make_filename(img_uploaded.name, "compressed", "jpg"),
                                       mime="image/jpeg", key="download_compressed")
        except Exception as e:
            st.error(f"Image processing failed: {e}")
