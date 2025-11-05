"""
retrieval.py: Shared retrieval logic for RAG system
Encapsulates heading/disease extraction, semantic fallback, and debug output.
"""
import re
from rich.console import Console
from rich.pretty import pprint

def retrieve_relevant_docs(vectorstores, llm, question: str):
    console = Console()
    # Step 1: Extract keywords
    keyword_prompt = f"Extract the main keywords from this question, separated by commas: {question}"
    console.rule("[bold blue]LLM: Keyword Extraction[/bold blue]")
    console.print("[yellow]Prompt:[/yellow]", keyword_prompt)
    keywords_response = llm.invoke(keyword_prompt)
    console.print("[green]Response:[/green]", keywords_response.content)
    keywords = keywords_response.content.strip()

    # Step 2: Extract main topic
    topic_prompt = f"Extract the main topic from this question: {question}"
    console.rule("[bold blue]LLM: Topic Extraction[/bold blue]")
    console.print("[yellow]Prompt:[/yellow]", topic_prompt)
    topic_response = llm.invoke(topic_prompt)
    console.print("[green]Response:[/green]", topic_response.content)
    topic = topic_response.content.strip()
    topic = re.sub(r'\*\*|\*', '', topic).replace('主要话题：', '').replace('主題：', '').replace('主题：', '').replace('Main topic:', '').strip()

    # Step 3: Classify question type
    classify_prompt = f"Classify this question into one of: pre (questionnaire questions), middle (clinical guidance and treatment), post (medical records tables). Question: {question}"
    console.rule("[bold blue]LLM: Question Type Classification[/bold blue]")
    console.print("[yellow]Prompt:[/yellow]", classify_prompt)
    classify_response = llm.invoke(classify_prompt)
    console.print("[green]Response:[/green]", classify_response.content)
    question_type = classify_response.content.strip().lower()

    filter_dict = None
    selected_collections = []
    disease = None
    if "middle" in question_type:
        disease_prompt = f"Extract the disease or condition name from this question, using the exact term as it appears in medical documents, such as '血压偏低' for low blood pressure: {question}"
        console.rule("[bold blue]LLM: Disease Extraction[/bold blue]")
        console.print("[yellow]Prompt:[/yellow]", disease_prompt)
        disease_response = llm.invoke(disease_prompt)
        console.print("[green]Response:[/green]", disease_response.content)
        disease = disease_response.content.strip()
        console.print(f"[magenta]Extracted disease/heading:[/magenta] {disease}")
        if disease.lower() != 'none' and disease:
            disease = re.sub(r'[^\w\u4e00-\u9fff]', '', disease)
            # Use new metadata field 'disease' 
            filter_dict = {"disease": disease}
            console.print(f"[magenta]Filter dict for disease:[/magenta] {filter_dict}")
        selected_collections = ["middle_docs"]
    elif "pre" in question_type:
        selected_collections = ["pre_docs"]
    elif "post" in question_type:
        selected_collections = ["post_docs"]
    else:
        selected_collections = ["pre_docs", "middle_docs", "post_docs"]

    console.rule("[bold blue]Retrieval/Filtering Criteria[/bold blue]")
    console.print(f"[cyan]Selected collections:[/cyan] {selected_collections}")
    console.print(f"[cyan]Filter dict:[/cyan] {filter_dict}")

    all_docs_with_scores = []
    for name in selected_collections:
        vectorstore = vectorstores[name]
        console.print(f"[blue]Attempting filtered search in {name} with topic:[/blue] {topic} and filter: {filter_dict}")
        docs_with_scores = vectorstore.similarity_search_with_score(topic, k=50, filter=filter_dict)
        # Fallback: if 'middle' and filter_dict is set and no docs found, do semantic search with disease as query
        if (
            "middle" in question_type and filter_dict is not None and not docs_with_scores
        ):
            console.print(f"[yellow]No docs found for exact heading '{disease}'. Trying semantic fallback with query: {disease} ...[/yellow]")
            docs_with_scores = vectorstore.similarity_search_with_score(disease, k=5)
            if docs_with_scores:
                console.print(f"[green]Semantic fallback found {len(docs_with_scores)} docs.[/green]")
            else:
                console.print(f"[red]Semantic fallback also found no docs for: {disease}[/red]")
        console.rule(f"[bold blue]Docs Retrieved from {name}[/bold blue]")
        if docs_with_scores:
            for i, (doc, score) in enumerate(docs_with_scores):
                console.print(f"Doc {i+1} (score: {score:.3f}):")
                pprint(doc.page_content[:300])
        else:
            console.print("[red]No docs retrieved.[/red]")
        all_docs_with_scores.extend(docs_with_scores)
    all_docs_with_scores.sort(key=lambda x: x[1], reverse=True)
    docs_with_scores = all_docs_with_scores[:20]
    context = "\n".join([doc.page_content for doc, _ in docs_with_scores])
    return {
        "context": context,
        "keywords": keywords,
        "topic": topic,
        "question_type": question_type,
        "disease": disease,
        "docs_with_scores": docs_with_scores,
    }
