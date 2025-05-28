import streamlit as st
import os
from dotenv import load_dotenv

from utils.pdf_utils import (
    extract_text_from_pdf,
    summarize_text,
    create_vector_store,
    build_conversational_chain,
    is_question_relevant
)

# Cargar API Key de OpenAI desde .env o st.secrets
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")

st.set_page_config(page_title="PDF IA", layout="centered")
st.title("📄 PDF IA: Resumen y Consultas con Memoria")

uploaded_file = st.file_uploader("📎 Cargá un archivo PDF", type="pdf")

if uploaded_file:
    pdf_text = extract_text_from_pdf(uploaded_file)

    # Navegación
    st.sidebar.title("🔧 Secciones")
    section = st.sidebar.radio("Elegí una opción:", ["📌 Resumí acá", "🤖 Consultas"])

    # Vector store y cadena conversacional
    if "vectorstore" not in st.session_state:
        with st.spinner("🔍 Analizando el documento..."):
            st.session_state.vectorstore = create_vector_store(pdf_text, openai_api_key)
            st.session_state.qa_chain = build_conversational_chain(
                st.session_state.vectorstore, openai_api_key
            )
            st.success("✅ Documento procesado con éxito.")

    # Sección de resumen
    if section == "📌 Resumí acá":
        st.header("📝 Resumen del PDF")
        if st.button("Generar resumen"):
            with st.spinner("Resumiendo el contenido..."):
                resumen = summarize_text(pdf_text, openai_api_key)
                st.success("Resumen generado:")
                st.write(resumen)

    # Sección de consultas con memoria
    elif section == "🤖 Consultas":
        st.header("❓ Consultá el contenido del documento")
        user_query = st.text_input("Escribí tu pregunta:")
        show_score = st.checkbox("Mostrar score de relevancia", value=True)

        if user_query:
            with st.spinner("Analizando tu consulta..."):
                is_relevant, score = is_question_relevant(
                    st.session_state.vectorstore,
                    user_query,
                    openai_api_key
                )

            if show_score:
                st.info(f"📊 Score de relevancia: {score:.2f}")

            if not is_relevant:
                st.warning("🚫 Tu consulta no es pertinente con el documento.")
            else:
                with st.spinner("Generando respuesta..."):
                    response = st.session_state.qa_chain.run(user_query)
                    st.success("✅ Respuesta:")
                    st.write(response)
