import streamlit as st
from pypdf import PdfReader

st.title("🧠 AI Quiz Generator")

st.write("Upload your study material and generate a quiz!")

uploaded_file = st.file_uploader(
    "Upload your PDF",
    type=["pdf"]
)

if uploaded_file is not None:
    reader = PdfReader(uploaded_file)

    text = ""

    for page in reader.pages:
        text += page.extract_text() or ""

    st.success("PDF uploaded successfully!")

    st.write("### Extracted Text")

    st.text_area(
        "Your PDF content:",
        text,
        height=300
    )