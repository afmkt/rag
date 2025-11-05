from langchain_postgres import PGVector
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
import os

def query_rag(question: str):
    """
    Query the RAG system with a question.
    """
    # Database connection
    connection_string = "postgresql+psycopg://myuser:mypassword@localhost:5432/mydatabase"

    # Embeddings model (multilingual for Chinese and English support)
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

    # Create PGVector store
    vectorstore = PGVector(
        embeddings=embeddings,
        connection=connection_string,
        collection_name="rag_docs"
    )

    # LLM
    from pydantic import SecretStr
    groq_api_key = os.getenv("GROQ_API_KEY")
    groq_model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
    llm = ChatGroq(api_key=SecretStr(groq_api_key) if groq_api_key else None, model=groq_model)

    # Retrieve relevant docs
    docs = vectorstore.similarity_search(question, k=5)
    context = "\n".join([doc.page_content for doc in docs])

    # Create prompt
    prompt = f"""Answer the question using ONLY the information from the context provided below. Do not use any external knowledge or assumptions. If the context does not contain sufficient information to answer the question, state that clearly.

Context:
{context}

Question: {question}

Answer:"""

    # Get response
    response = llm.invoke(prompt)
    return response.content

if __name__ == "__main__":
    question = "What are the critical abnormal results for blood pressure?"
    answer = query_rag(question)
    print(f"Question: {question}")
    print(f"Answer: {answer}")