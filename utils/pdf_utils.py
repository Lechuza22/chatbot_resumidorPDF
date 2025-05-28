import PyPDF2
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.docstore.document import Document
from openai import OpenAI


def extract_text_from_pdf(uploaded_file):
    reader = PyPDF2.PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text


def summarize_text(text, openai_api_key):
    client = OpenAI(api_key=openai_api_key)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Sos un asistente que resume documentos."},
            {"role": "user", "content": f"Resumí el siguiente texto:\n\n{text[:3000]}"}
        ]
    )
    return response.choices[0].message.content.strip()


def create_vector_store(text, openai_api_key):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    docs = [Document(page_content=chunk) for chunk in text_splitter.split_text(text)]
    embeddings = OpenAIEmbeddings(api_key=openai_api_key)
    return FAISS.from_documents(docs, embeddings)


def build_conversational_chain(vectorstore, openai_api_key):
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, api_key=openai_api_key)
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    return ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(search_kwargs={"k": 4}),
        memory=memory,
        return_source_documents=False
    )


def is_question_relevant(vectorstore, question, openai_api_key, threshold=0.75):
    embeddings = OpenAIEmbeddings(api_key=openai_api_key)
    question_embedding = embeddings.embed_query(question)
    docs_and_scores = vectorstore.similarity_search_with_score_by_vector(question_embedding, k=1)
    if not docs_and_scores:
        return False, 0.0
    top_score = docs_and_scores[0][1]
    return top_score >= threshold, top_score
