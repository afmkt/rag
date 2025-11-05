#!/usr/bin/env python3
"""
Web API for RAG Queries and Document Uploads

This script provides REST API endpoints to query the RAG system
for pre (questionnaire), middle (clinical guidance), and post (medical records) collections,
and to upload .docx files for processing.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from langchain_postgres import PGVector
from langchain_huggingface import HuggingFaceEmbeddings
from openrouter_llm import OpenRouterLLM
from typing import Dict, Any
import os
import json
from pathlib import Path
from contextlib import asynccontextmanager
import logging
import sys

def get_log_lines(log_path: str = "api.log", max_lines: int = 200) -> list[str]:
    """Read the last max_lines from the log file as a list of lines."""
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        return [line.rstrip('\n') for line in lines[-max_lines:]]
    except Exception:
        return []

# Global variables for vectorstores and LLM
vectorstores: Dict[str, Any] = {}
llm: Any = None

# Set up logging to both console and file
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(console_handler)

# File handler
file_handler = logging.FileHandler("api.log")
file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(file_handler)

def initialize_rag():
    """Initialize the RAG components."""
    global vectorstores, llm
    if vectorstores:
        return  # Already initialized

    try:
        # Database connection
        connection_string = os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg://myuser:mypassword@localhost:5432/mydatabase"
        )
        logging.info(f"Using database connection: {connection_string}")

        # Embeddings model (multilingual for Chinese and English support)
        logging.info("Loading HuggingFace embeddings model...")
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        logging.info("Embeddings model loaded successfully")

        # Create PGVector stores for each collection
        collections = ["pre_docs", "middle_docs", "post_docs"]
        for collection in collections:
            logging.info(f"Initializing vectorstore for collection: {collection}")
            vectorstores[collection] = PGVector(
                embeddings=embeddings,
                connection=connection_string,
                collection_name=collection
            )
            logging.info(f"Vectorstore for {collection} initialized successfully")

        # LLM
        openrouter_api_key = os.getenv("OPEN_ROUTER_API_KEY")
        if not openrouter_api_key:
            raise ValueError("OPEN_ROUTER_API_KEY environment variable is required")
        
        openrouter_model = os.getenv("OPEN_ROUTER_MODEL", "openai/gpt-oss-safeguard-20b")
        logging.info(f"Initializing LLM with model: {openrouter_model}")
        llm = OpenRouterLLM(api_key=openrouter_api_key, model=openrouter_model)
        logging.info("LLM initialized successfully")

        logging.info("RAG system initialization completed successfully")
        
    except Exception as e:
        logging.error(f"Failed to initialize RAG system: {str(e)}")
        # Reset partially initialized components
        vectorstores = {}
        llm = None
        raise  # Re-raise the exception

def reload_vectorstore(collection: str):
    """Reload a specific vectorstore with updated data."""
    from langchain_core.documents import Document
    
    logging.info(f"Starting to reload vectorstore for collection: {collection}")
    
    data_dir = Path("data")
    file_map = {
        "pre_docs": "pre.json",
        "middle_docs": "middle.json", 
        "post_docs": "post.json"
    }
    
    file_path = data_dir / file_map[collection]
    if not file_path.exists():
        logging.warning(f"JSON file not found: {file_path}")
        return
    
    logging.info(f"Loading JSON data from: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    documents = []
    
    if collection == "pre_docs":
        questions = data.get("questions", [])
        logging.info(f"Processing {len(questions)} questions for pre_docs")
        for q in questions:
            content = f"Question: {q['question']}\nType: {q['type']}\nOptions: {q.get('options', [])}"
            doc = Document(
                page_content=content,
                metadata={"source": "pre", "type": "question", "question": q['question']}
            )
            documents.append(doc)
    
    elif collection == "middle_docs":
        logging.info(f"Processing {len(data)} items for middle_docs with structured array format")
        for item in data:
            if "semantic_json" in item:
                semantic_json = item["semantic_json"]
                
                # Handle array structure: list of {section, disease, treatment} objects
                if isinstance(semantic_json, list):
                    for entry in semantic_json:
                        if isinstance(entry, dict):
                            section = entry.get("section", "未知")
                            disease = entry.get("disease", "未知疾病")
                            treatment = entry.get("treatment", "无特定治疗建议")
                            
                            # Create focused content
                            content_parts = [f"科室: {section}", f"疾病: {disease}"]
                            if treatment:
                                content_parts.append(f"治疗方案: {treatment}")
                            
                            full_content = "\n".join(content_parts)
                            
                            # Create document with detailed metadata
                            doc = Document(
                                page_content=full_content,
                                metadata={
                                    "source": "middle",
                                    "piece_id": item.get("piece_id", ""),
                                    "section": section,
                                    "disease": disease,
                                    "has_treatment": bool(treatment and treatment != "无特定治疗建议")
                                }
                            )
                            documents.append(doc)
                else:
                    # Handle old single object format for backward compatibility
                    disease = semantic_json.get("disease", "未知疾病")
                    treatment = semantic_json.get("treatment", "无特定治疗建议")
                    
                    content_parts = [f"疾病: {disease}"]
                    if treatment:
                        content_parts.append(f"治疗方案: {treatment}")
                    
                    full_content = "\n".join(content_parts)
                    
                    doc = Document(
                        page_content=full_content,
                        metadata={
                            "source": "middle",
                            "piece_id": item.get("piece_id", ""),
                            "section": "未知",
                            "disease": disease,
                            "has_treatment": bool(treatment and treatment != "无特定治疗建议")
                        }
                    )
                    documents.append(doc)
            else:
                # Fallback for items without semantic_json
                content = json.dumps(item, ensure_ascii=False)
                doc = Document(
                    page_content=content,
                    metadata={
                        "source": "middle", 
                        "piece_id": item.get("piece_id", ""),
                        "section": "未知",
                        "disease": "未知",
                        "has_treatment": False
                    }
                )
                documents.append(doc)
    
    elif collection == "post_docs":
        content_items = data.get("content", [])
        logging.info(f"Processing {len(content_items)} content items for post_docs")
        for content_item in content_items:
            if content_item["type"] == "table":
                records = content_item["data"]
                logging.info(f"Processing {len(records)} table records for post_docs")
                for record in records:
                    content = json.dumps(record, ensure_ascii=False)
                    doc = Document(
                        page_content=content,
                        metadata={"source": "post", "table": True}
                    )
                    documents.append(doc)
    
    logging.info(f"Created {len(documents)} documents for collection: {collection}")
    
    # Reload the vectorstore
    connection_string = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://myuser:mypassword@localhost:5432/mydatabase"
    )
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    vectorstores[collection] = PGVector(
        embeddings=embeddings,
        connection=connection_string,
        collection_name=collection
    )
    if documents:
        logging.info(f"Adding {len(documents)} documents to PGVector collection: {collection}")
        vectorstores[collection].add_documents(documents)
        logging.info(f"Successfully loaded {len(documents)} documents into PGVector collection: {collection}")
    else:
        logging.info(f"No documents to add for collection: {collection}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logging.info("Starting RAG API server...")
    try:
        initialize_rag()
        logging.info("RAG system initialized successfully during startup")
    except Exception as e:
        logging.error(f"Failed to initialize RAG during startup: {e}")
        logging.error("Server will start but RAG functionality will be unavailable")
        logging.error("Use /initialize endpoint to retry initialization")
    yield
    # Shutdown
    logging.info("Shutting down RAG API server...")

app = FastAPI(title="RAG Query API", description="API for querying medical RAG system and uploading documents", lifespan=lifespan)

class QueryRequest(BaseModel):
    question: str

@app.get("/health")
async def health_check():
    """Health check endpoint to verify system status."""
    try:
        # Check environment variables
        db_url = os.getenv("DATABASE_URL")
        openrouter_key = os.getenv("OPEN_ROUTER_API_KEY")
        
        status = {
            "status": "healthy",
            "vectorstores_initialized": bool(vectorstores),
            "llm_initialized": bool(llm),
            "database_url_set": bool(db_url),
            "openrouter_key_set": bool(openrouter_key),
            "vectorstore_collections": list(vectorstores.keys()) if vectorstores else []
        }
        
        # Test database connection if vectorstores exist
        if vectorstores:
            try:
                # Try a simple operation on the first vectorstore
                first_collection = list(vectorstores.values())[0]
                # This will test the database connection
                first_collection.similarity_search("test", k=1)
                status["database_connection"] = "ok"
            except Exception as db_error:
                status["database_connection"] = f"error: {str(db_error)}"
                status["status"] = "degraded"
        else:
            status["database_connection"] = "not_tested"
            status["status"] = "error"
            
        return status
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "vectorstores_initialized": bool(vectorstores),
            "llm_initialized": bool(llm)
        }

@app.post("/initialize")
async def force_initialize():
    """Force re-initialization of the RAG system."""
    global vectorstores, llm
    try:
        vectorstores = {}  # Reset
        llm = None
        initialize_rag()
        return {
            "status": "success",
            "message": "RAG system re-initialized",
            "vectorstores": list(vectorstores.keys()),
            "llm_initialized": bool(llm)
        }
    except Exception as e:
        return {
            "status": "error", 
            "error": str(e),
            "vectorstores_initialized": bool(vectorstores),
            "llm_initialized": bool(llm)
        }

def query_rag(question: str, collection: str) -> str:
    """Query the RAG system with a question for a specific collection."""
    if not vectorstores or not llm:
        raise HTTPException(status_code=500, detail="RAG system not initialized")

    from retrieval import retrieve_relevant_docs
    from rich.console import Console
    from rich.pretty import pprint
    console = Console()
    result = retrieve_relevant_docs(vectorstores, llm, question)
    context = result["context"]
    topic = result["topic"]
    prompt = f"""Provide the exact relevant information from the context that answers the question, quoting it directly if possible. For treatment questions, also include the recommended actions if available in the context. Do not use any external knowledge or assumptions. If the context does not contain relevant information about {topic}, reply exactly with \"无法回答该问题，因为给定的上下文中没有包含关于{topic}的任何信息。\"

Context:
{context}

Question: {question}

Answer:"""
    console.rule("[bold blue]LLM: Final Answer Generation[/bold blue]")
    console.print("[yellow]Prompt:[/yellow]")
    pprint(prompt[:1000] + ("..." if len(prompt) > 1000 else ""))
    response = llm.invoke(prompt)
    console.print("[green]Response:[/green]", response.content)
    return str(response.content)

@app.post("/query/pre")
async def query_pre(request: QueryRequest):
    """Query the pre_docs collection (questionnaire questions)."""
    try:
        answer = query_rag(request.question, "pre_docs")
        log_lines = get_log_lines()
        # Print logs to console instead of returning them
        if log_lines:
            print("=== API Logs ===")
            for line in log_lines:
                print(line)
            print("=== End Logs ===")
        return {"answer": answer}
    except Exception as e:
        log_lines = get_log_lines()
        # Print logs to console
        if log_lines:
            print("=== API Error Logs ===")
            for line in log_lines:
                print(line)
            print("=== End Error Logs ===")
        raise HTTPException(status_code=500, detail={"error": str(e)})

@app.post("/query/middle")
async def query_middle(request: QueryRequest):
    """Query the middle_docs collection (clinical guidance and treatment)."""
    try:
        answer = query_rag(request.question, "middle_docs")
        log_lines = get_log_lines()
        # Print logs to console instead of returning them
        if log_lines:
            print("=== API Logs ===")
            for line in log_lines:
                print(line)
            print("=== End Logs ===")
        return {"answer": answer}
    except Exception as e:
        log_lines = get_log_lines()
        # Print logs to console
        if log_lines:
            print("=== API Error Logs ===")
            for line in log_lines:
                print(line)
            print("=== End Error Logs ===")
        raise HTTPException(status_code=500, detail={"error": str(e)})

@app.post("/query/post")
async def query_post(request: QueryRequest):
    """Query the post_docs collection (medical records tables)."""
    try:
        answer = query_rag(request.question, "post_docs")
        log_lines = get_log_lines()
        # Print logs to console instead of returning them
        if log_lines:
            print("=== API Logs ===")
            for line in log_lines:
                print(line)
            print("=== End Logs ===")
        return {"answer": answer}
    except Exception as e:
        log_lines = get_log_lines()
        # Print logs to console
        if log_lines:
            print("=== API Error Logs ===")
            for line in log_lines:
                print(line)
            print("=== End Error Logs ===")
        raise HTTPException(status_code=500, detail={"error": str(e)})



########################################################################################################################################################################







@app.post("/upload/pre")
async def upload_pre(file: UploadFile = File(...)):
    """Upload pre.docx file for processing."""
    logging.info(f"Starting upload of file: {file.filename}")

    if not file.filename or not file.filename.endswith('.docx'):
        logging.error(f"Invalid file: {file.filename} - must be a .docx file")
        raise HTTPException(status_code=400, detail="File must be a .docx file")

    try:
        # Save file to data/pre.docx
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        file_path = data_dir / "pre.docx"
        logging.info(f"Saving file to: {file_path}")

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        logging.info(f"File saved successfully, size: {len(content)} bytes")

        # Run pre.py to process - first run without capturing to show live output
        logging.info("Starting pre.py processing script")
        import subprocess
        
        # Run without capturing output first to show live progress
        print("=== Running pre.py (live output) ===")
        subprocess.run([sys.executable, "pre.py"], cwd=".")
        print("=== pre.py completed ===")
        
        # Then run again to capture output for logging
        result = subprocess.run([sys.executable, "pre.py"], capture_output=True, text=True, cwd=".")
        
        if result.returncode != 0:
            logging.error(f"pre.py failed with return code: {result.returncode}")
            raise Exception(f"pre.py failed: {result.stderr}")

        logging.info("pre.py completed successfully")

        # Log the script output to file as well
        with open("api.log", "a", encoding="utf-8") as log_file:
            if result.stdout:
                log_file.write(f"{logging.Formatter().formatTime(logging.LogRecord('api', logging.INFO, '', 0, '', (), None))} INFO pre.py stdout: {result.stdout}\n")
            if result.stderr:
                log_file.write(f"{logging.Formatter().formatTime(logging.LogRecord('api', logging.INFO, '', 0, '', (), None))} INFO pre.py stderr: {result.stderr}\n")
            log_file.flush()

        logging.info("Reloading vectorstore for pre_docs")
        try:
            reload_vectorstore("pre_docs")
            logging.info("Vectorstore reload completed successfully")
        except Exception as e:
            logging.error(f"Failed to reload vectorstore: {str(e)}")
            raise e

        logging.info("Upload and processing completed successfully")
        return {"message": "Pre document uploaded and processed successfully"}

    except Exception as e:
        logging.error(f"Upload failed with error: {str(e)}")
        raise HTTPException(status_code=500, detail={"error": str(e)})

@app.post("/upload/middle")
async def upload_middle(file: UploadFile = File(...)):
    """Upload middle.docx file for processing."""
    logging.info(f"Starting upload of file: {file.filename}")

    if not file.filename or not file.filename.endswith('.docx'):
        logging.error(f"Invalid file: {file.filename} - must be a .docx file")
        raise HTTPException(status_code=400, detail="File must be a .docx file")

    try:
        # Save file to data/middle.docx
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        file_path = data_dir / "middle.docx"
        logging.info(f"Saving file to: {file_path}")

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        logging.info(f"File saved successfully, size: {len(content)} bytes")

        # Run middle.py to process
        logging.info("Starting middle.py processing script")
        import subprocess
        
        # Run middle.py and wait for completion
        result = subprocess.run([sys.executable, "middle.py"], cwd=".")
        
        if result.returncode != 0:
            logging.error(f"middle.py failed with return code: {result.returncode}")
            raise Exception(f"middle.py failed with return code: {result.returncode}")

        logging.info("middle.py completed successfully")

        # Check if JSON file was created
        json_file = Path("data/middle.json")
        if not json_file.exists():
            logging.error("middle.json was not created by middle.py")
            raise Exception("middle.json was not created by middle.py")

        logging.info("JSON file created, proceeding with vectorstore reload")

        # Log the script output to file as well
        with open("api.log", "a", encoding="utf-8") as log_file:
            log_file.write(f"{logging.Formatter().formatTime(logging.LogRecord('api', logging.INFO, '', 0, '', (), None))} INFO middle.py completed successfully\n")
            log_file.flush()

        print("DEBUG: About to call reload_vectorstore")
        logging.info("Reloading vectorstore for middle_docs")
        try:
            reload_vectorstore("middle_docs")
            logging.info("Vectorstore reload completed successfully")
            print("DEBUG: reload_vectorstore completed successfully")
        except Exception as e:
            logging.error(f"Failed to reload vectorstore: {str(e)}")
            print(f"DEBUG: reload_vectorstore failed: {str(e)}")
            # Don't raise the exception - the upload was successful, just log the error
            logging.warning("Continuing despite vectorstore reload failure - data processing completed successfully")

        logging.info("Upload and processing completed successfully")
        return {"message": "Middle document uploaded and processed successfully"}

    except Exception as e:
        logging.error(f"Upload failed with error: {str(e)}")
        raise HTTPException(status_code=500, detail={"error": str(e)})

@app.post("/upload/post")
async def upload_post(file: UploadFile = File(...)):
    """Upload post.docx file for processing."""
    logging.info(f"Starting upload of file: {file.filename}")

    if not file.filename or not file.filename.endswith('.docx'):
        logging.error(f"Invalid file: {file.filename} - must be a .docx file")
        raise HTTPException(status_code=400, detail="File must be a .docx file")

    try:
        # Save file to data/post.docx
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        file_path = data_dir / "post.docx"
        logging.info(f"Saving file to: {file_path}")

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        logging.info(f"File saved successfully, size: {len(content)} bytes")

        # Run post.py to process - first run without capturing to show live output
        logging.info("Starting post.py processing script")
        import subprocess
        
        # Run without capturing output first to show live progress
        print("=== Running post.py (live output) ===")
        subprocess.run([sys.executable, "post.py"], cwd=".")
        print("=== post.py completed ===")
        
        # Then run again to capture output for logging
        result = subprocess.run([sys.executable, "post.py"], capture_output=True, text=True, cwd=".")
        
        if result.returncode != 0:
            logging.error(f"post.py failed with return code: {result.returncode}")
            raise Exception(f"post.py failed: {result.stderr}")

        logging.info("post.py completed successfully")

        # Log the script output to file as well
        with open("api.log", "a", encoding="utf-8") as log_file:
            if result.stdout:
                log_file.write(f"{logging.Formatter().formatTime(logging.LogRecord('api', logging.INFO, '', 0, '', (), None))} INFO post.py stdout: {result.stdout}\n")
            if result.stderr:
                log_file.write(f"{logging.Formatter().formatTime(logging.LogRecord('api', logging.INFO, '', 0, '', (), None))} INFO post.py stderr: {result.stderr}\n")
            log_file.flush()

        logging.info("Reloading vectorstore for post_docs")
        try:
            reload_vectorstore("post_docs")
            logging.info("Vectorstore reload completed successfully")
        except Exception as e:
            logging.error(f"Failed to reload vectorstore: {str(e)}")
            raise e

        logging.info("Upload and processing completed successfully")
        return {"message": "Post document uploaded and processed successfully"}

    except Exception as e:
        logging.error(f"Upload failed with error: {str(e)}")
        raise HTTPException(status_code=500, detail={"error": str(e)})

@app.post("/load/{collection}")
async def load_json_to_vectorstore(collection: str):
    """
    Load JSON data into pgvector for a specific collection.

    Supported collections: pre_docs, middle_docs, post_docs
    """
    try:
        # Validate collection name
        valid_collections = ["pre_docs", "middle_docs", "post_docs"]
        if collection not in valid_collections:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid collection. Supported collections: {', '.join(valid_collections)}"
            )

        logging.info(f"Loading JSON data into pgvector for collection: {collection}")

        # Call the existing reload_vectorstore function
        reload_vectorstore(collection)

        logging.info(f"Successfully loaded JSON data into pgvector for collection: {collection}")
        return {
            "message": f"Successfully loaded JSON data into pgvector for collection: {collection}",
            "collection": collection
        }

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Failed to load JSON data into pgvector: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load JSON data into pgvector: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
