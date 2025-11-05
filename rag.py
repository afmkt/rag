#!/usr/bin/env python3
"""
Standalone RAG Question/Answer Script

This script provides an interactive interface to query the RAG system
built with pgvector and Ollama. It retrieves relevant documents and
generates answers using the configured LLM.
"""

from langchain_postgres import PGVector
from langchain_huggingface import HuggingFaceEmbeddings
from openrouter_llm import OpenRouterLLM
from dotenv import load_dotenv
import os
import logging
from rich.console import Console
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

def initialize_rag():
    """Initialize the RAG components."""
    # Database connection
    connection_string = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://myuser:mypassword@localhost:5432/mydatabase"
    )

    # Embeddings model (multilingual for Chinese and English support)
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

    # Create PGVector stores for each collection
    vectorstores = {}
    collections = ["pre_docs", "middle_docs", "post_docs"]
    for collection in collections:
        vectorstores[collection] = PGVector(
            embeddings=embeddings,
            connection=connection_string,
            collection_name=collection
        )

    # LLM
    openrouter_api_key = os.getenv("OPEN_ROUTER_API_KEY")
    openrouter_model = os.getenv("OPEN_ROUTER_MODEL", "openrouter/openchat-3.5-0106")
    llm = OpenRouterLLM(api_key=openrouter_api_key, model=openrouter_model)

    return vectorstores, llm

def query_rag(vectorstores, llm, question: str) -> tuple[str, str, str]:
    console = Console()
    """Query the RAG system with a question."""
    # Extract keywords from the question
    keyword_prompt = f"Extract the main keywords from this question, separated by commas: {question}"
    console.rule("[bold blue]LLM: Keyword Extraction[/bold blue]")
    console.print("[yellow]Prompt:[/yellow]", keyword_prompt)
    keywords_response = llm.invoke(keyword_prompt)
    console.print("[green]Response:[/green]", keywords_response.content)
    keywords = keywords_response.content.strip()
    print(f"Extracted keywords: {keywords}")
    
    # Extract main topic from the question
    topic_prompt = f"Extract the main topic from this question: {question}"
    console.rule("[bold blue]LLM: Topic Extraction[/bold blue]")
    console.print("[yellow]Prompt:[/yellow]", topic_prompt)
    topic_response = llm.invoke(topic_prompt)
    console.print("[green]Response:[/green]", topic_response.content)
    topic = topic_response.content.strip()
    from retrieval import retrieve_relevant_docs
    result = retrieve_relevant_docs(vectorstores, llm, question)
    context = result["context"]
    keywords = result["keywords"]
    topic = result["topic"]
    # Compose the answer prompt
    prompt = f"""Provide the exact relevant information from the context that answers the question, quoting it directly if possible. For treatment questions, also include the recommended actions if available in the context. Do not use any external knowledge or assumptions. If the context does not contain relevant information about {topic}, reply exactly with \"无法回答该问题，因为给定的上下文中没有包含关于{topic}的任何信息。\"

Context:
{context}

Question: {question}

Answer:"""
    console = Console()
    from rich.pretty import pprint
    console.rule("[bold blue]LLM: Final Answer Generation[/bold blue]")
    console.print("[yellow]Prompt:[/yellow]")
    pprint(prompt[:1000] + ("..." if len(prompt) > 1000 else ""))
    response = llm.invoke(prompt)
    console.print("[green]Response:[/green]", response.content)
    return response.content, keywords, topic

def main():
    print("Initializing RAG system...")
    try:
        vectorstores, llm = initialize_rag()
        print("RAG system ready! Type 'quit' or 'exit' to stop.")
        print("-" * 50)

        while True:
            question = input("Ask a question: ").strip()
            if question.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            if not question:
                continue

            print("Thinking...")
            try:
                answer, keywords, topic = query_rag(vectorstores, llm, question)
                print(f"Extracted keywords: {keywords}")
                print(f"Extracted topic: {topic}")
                print(f"\nAnswer: {answer}\n")
                print("-" * 50)
            except Exception as e:
                print(f"Error processing question: {e}")
                print("-" * 50)

    except Exception as e:
        print(f"Failed to initialize RAG system: {e}")
        print("Make sure pgvector database is running and Ollama is available.")

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()