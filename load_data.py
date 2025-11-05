from langchain_postgres import PGVector
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
import json
from pathlib import Path
from dotenv import load_dotenv
import logging
load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
def load_data():
    """
    Load JSON data from pre.json, middle.json, post.json into pgvector for RAG.
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

    # Load and process data
    data_dir = Path("data")
    files = ["pre.json", "middle.json", "post.json"]
    collection_names = {"pre.json": "pre_docs", "middle.json": "middle_docs", "post.json": "post_docs"}
    documents_by_collection = {name: [] for name in collection_names.values()}

    for file in files:
        file_path = data_dir / file
        if not file_path.exists():
            print(f"File {file} not found, skipping.")
            continue

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        collection_name = collection_names[file]
        documents = documents_by_collection[collection_name]

        if file == "pre.json":
            # Questions from questionnaire
            for q in data.get("questions", []):
                content = f"Question: {q['question']}\nType: {q['type']}\nOptions: {q.get('options', [])}"
                doc = Document(
                    page_content=content,
                    metadata={"source": "pre", "type": "question", "question": q['question']}
                )
                documents.append(doc)

        elif file == "middle.json":
            # Processing for structured array format: list of {section, disease, treatment} objects
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

        elif file == "post.json":
            # Handle post.json structure: list of dicts with 'type' and 'data' keys
            for content_item in data.get("content", []):
                item_type = content_item.get("type")
                item_data = content_item.get("data")
                if item_type == "table" and isinstance(item_data, list):
                    for record in item_data:
                        content = json.dumps(record, ensure_ascii=False)
                        doc = Document(
                            page_content=content,
                            metadata={"source": "post", "type": "table"}
                        )
                        documents.append(doc)
                elif item_type == "text" and isinstance(item_data, str):
                    doc = Document(
                        page_content=item_data,
                        metadata={"source": "post", "type": "text"}
                    )
                    documents.append(doc)

    # Add documents to respective vectorstores
    for collection_name, documents in documents_by_collection.items():
        if documents:
            vectorstore = PGVector(
                embeddings=embeddings,
                connection=connection_string,
                collection_name=collection_name
            )
            vectorstore.add_documents(documents)
            print(f"Loaded {len(documents)} documents into {collection_name}.")
        else:
            print(f"No documents to load for {collection_name}.")

if __name__ == "__main__":
    load_data()