# Standard library imports
import sys
import os
import json
import logging
import subprocess
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

# Third-party imports
from rich.console import Console

# Local imports
from openrouter_llm import OpenRouterLLM

# Try to import jsonschema for validation
try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    print("Warning: jsonschema not installed. JSON validation will be skipped.")
    jsonschema = None
    HAS_JSONSCHEMA = False


# Simple JSON Schema for disease and treatments only
SIMPLE_MEDICAL_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "section": {
                "type": "string",
                "description": "Name of the medical section or category"
            },
            "disease": {
                "type": "string",
                "description": "Name of the disease or medical condition"
            },
            "treatment": {
                "type": "string", 
                "description": "Treatment recommendation as a single detailed string"
            }
        },
        "required": ["section", "disease", "treatment"],
        "additionalProperties": False
    }
}


def validate_json_structure(json_data) -> tuple[bool, str]:
    """Validate JSON against the simple medical schema (array of objects)"""
    if not HAS_JSONSCHEMA or jsonschema is None:
        return True, "Validation skipped - jsonschema not available"
    
    try:
        jsonschema.validate(json_data, SIMPLE_MEDICAL_SCHEMA)
        return True, "Valid"
    except Exception as e:  # Use generic Exception to handle all validation errors
        return False, str(e)


def create_example_json():
    """Create an example JSON structure for reference."""
    return [
        {
            "section": "血压异常",
            "disease": "血压偏低",
            "treatment": "若血压长期低于90/60mmHg，伴有头晕、晕厥等症状，请到心内科门诊进一步诊治。"
        },
        {
            "section": "血压异常", 
            "disease": "血压升高",
            "treatment": "低盐饮食，随访血压，若不同日3次测量血压均≥140/90mmHg可诊断为高血压病，心内科门诊就诊，口服降压药物治疗。"
        }
    ]


def clean_llm_response(response_text: str) -> str:
    """Clean LLM response to extract valid JSON"""
    
    # Remove markdown code blocks
    if response_text.startswith("```"):
        response_text = response_text[3:]
    if response_text.endswith("```"):
        response_text = response_text[:-3]
    
    # Remove "json" language indicator
    if response_text.startswith("json"):
        response_text = response_text[4:]
    
    response_text = response_text.strip()
    
    # Find JSON content - handle both objects and arrays
    # Look for array first (starts with [)
    if '[' in response_text and ']' in response_text:
        start_idx = response_text.find('[')
        end_idx = response_text.rfind(']')
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            response_text = response_text[start_idx:end_idx + 1]
            return response_text
    
    # Fallback to object (starts with {)
    start_idx = response_text.find('{')
    end_idx = response_text.rfind('}')
    
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        response_text = response_text[start_idx:end_idx + 1]
    
    return response_text


def sanitize_and_fix_json(json_obj):
    """Sanitize and fix JSON object to match the schema (array of section/disease/treatment objects)."""
    if not isinstance(json_obj, list):
        # Try to convert single object to array
        if isinstance(json_obj, dict):
            json_obj = [json_obj]
        else:
            return [{"section": "未知", "disease": "未知疾病", "treatment": "无特定治疗建议"}]
    
    sanitized_items = []
    for item in json_obj:
        if not isinstance(item, dict):
            continue
            
        # Extract section
        section = item.get("section", "")
        if not section or not isinstance(section, str):
            section = "未知"
        
        # Extract disease
        disease = item.get("disease", "")
        if not disease or not isinstance(disease, str):
            disease = "未知疾病"
        
        # Extract treatment
        treatment = item.get("treatment", "")
        if not treatment:
            # Check if old 'treatments' array exists for backward compatibility
            treatments_array = item.get("treatments", [])
            if treatments_array and isinstance(treatments_array, list):
                treatment = "; ".join(str(t) for t in treatments_array if t)
            else:
                treatment = "无特定治疗建议"
        
        sanitized_items.append({
            "section": section.strip(),
            "disease": disease.strip(),
            "treatment": treatment.strip()
        })
    
    return sanitized_items if sanitized_items else [{"section": "未知", "disease": "未知疾病", "treatment": "无特定治疗建议"}]



def docling_convert(input_path: str) -> str:
    """Convert a docx file to markdown using docling CLI tool.
    
    Args:
        input_path: Path to the docx file to convert
        
    Returns:
        Path to the generated markdown file
    """
    try:
        input_file = Path(input_path)
        if not input_file.exists():
            return f"Error: File {input_path} does not exist"
        
        output_file = input_file.with_suffix(".md")
        result = subprocess.run([
            "docling", "--to", "md", str(input_file), "--output", str(output_file)
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            return f"Successfully converted {input_path} to {output_file}"
        else:
            return f"Failed to convert {input_path}: {result.stderr}"
    except Exception as e:
        return f"Failed to convert {input_path}: {str(e)}"


def chunk_markdown_by_sections(content: str) -> list:
    """Split markdown content into chunks at section boundaries.
    
    Args:
        content: The full markdown content
        
    Returns:
        List of chunk dictionaries with title and content
    """
    lines = content.split('\n')
    chunks = []
    current_chunk:Any = []
    current_title = "Introduction"
    
    for line in lines:
        # Check if this is a section header (starts with ** and ends with **)
        if line.strip().startswith('**') and line.strip().endswith('**'):
            # Save previous chunk if it has content
            if current_chunk:
                chunk_content = '\n'.join(current_chunk).strip()
                if chunk_content:
                    chunks.append({
                        'title': current_title,
                        'content': chunk_content,
                        'structure_type': 'section'
                    })
            
            # Start new chunk with this header
            current_title = line.strip().strip('*')
            current_chunk = [line]  # Include the header in the chunk
        else:
            current_chunk.append(line)
    
    # Add the last chunk
    if current_chunk:
        chunk_content = '\n'.join(current_chunk).strip()
        if chunk_content:
            chunks.append({
                'title': current_title,
                'content': chunk_content,
                'structure_type': 'section'
            })
    
    return chunks


def analyze_markdown_structure(md_path: str) -> str:
    """Read markdown file and split it into semantic pieces based on section boundaries.
    
    Args:
        md_path: Path to the markdown file to analyze
        
    Returns:
        JSON string containing the split pieces
    """
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # First, chunk the markdown by section boundaries
        chunks = chunk_markdown_by_sections(content)
        
        # Validate that we have meaningful chunks
        if not chunks:
            return json.dumps([{
                "title": "Full Content",
                "content": content,
                "structure_type": "document"
            }])
        
        # For each chunk, we can optionally use LLM to further refine the structure
        # But for now, we'll use the section-based chunks directly
        pieces = []
        for chunk in chunks:
            # Skip empty chunks
            if not chunk['content'].strip():
                continue
                
            pieces.append({
                "title": chunk['title'],
                "content": chunk['content'],
                "structure_type": chunk['structure_type']
            })
        
        return json.dumps(pieces, indent=2, ensure_ascii=False)
        
    except Exception as e:
        return f"Error analyzing markdown: {str(e)}"


def extract_semantic_json(piece_content: str) -> str:
    """Extract semantic structure from a markdown piece as JSON with improved stability.
    
    Args:
        piece_content: The markdown content of a piece
        
    Returns:
        JSON representation of the semantic structure
    """

    try:
        openrouter_api_key = os.getenv("OPEN_ROUTER_API_KEY")
        openrouter_model = os.getenv("OPEN_ROUTER_MODEL", "openrouter/openchat-3.5-0106")
        llm = OpenRouterLLM(api_key=openrouter_api_key, model=openrouter_model)

        # Simple structured prompt focusing only on disease and treatments
        example_json = create_example_json()

        prompt = f"""
You are a medical document parser. Extract ALL diseases and treatments from the following content, organized by sections.

REQUIRED JSON STRUCTURE (follow this exactly):
{json.dumps(example_json, indent=2, ensure_ascii=False)}

PARSING RULES:
1. Look for section headers (often in **bold** format or standalone lines)
2. Under each section, identify all diseases/conditions and their treatments
3. Each disease gets its own object with section, disease, and treatment
4. "section": Name of the medical section/category (use Chinese)
5. "disease": Name of the specific disease or condition (use Chinese)  
6. "treatment": Complete treatment recommendation as a single string (use Chinese)
7. Extract ALL diseases from ALL sections - don't miss any
8. Return a JSON array with all extracted items
9. Return ONLY valid JSON, no explanations

CONTENT TO PROCESS:
{piece_content}

JSON OUTPUT:
"""

        console = Console()
        console.rule("[bold blue]LLM Interaction Start[/bold blue]")
        console.print("[bold yellow]Structured prompt sent to OpenRouter API:[/bold yellow]", style="yellow")
        console.print(prompt[:500] + "...", style="dim")  # Show partial prompt
        logging.info(f"OpenRouter API prompt: {prompt}")
        response = llm.invoke(prompt)
        console.print("[bold green]Response from OpenRouter API:[/bold green]", style="green")
        console.print(response.content, style="dim")
        console.rule("[bold blue]LLM Interaction End[/bold blue]")
        logging.info(f"OpenRouter API response: {response.content}")
        response_text = str(response.content).strip()

        # Enhanced response cleaning
        response_text = clean_llm_response(response_text)

        # If response is empty, return a basic structure
        if not response_text:
            return json.dumps([{
                "section": "未知",
                "disease": "未知疾病",
                "treatment": "无特定治疗建议"
            }])

        # Try to parse JSON
        try:
            structure = json.loads(response_text)
            
            # Sanitize and fix structure for better stability
            structure = sanitize_and_fix_json(structure)
            
            # Validate structure against schema
            is_valid, validation_msg = validate_json_structure(structure)
            if not is_valid:
                print(f"Warning: JSON validation failed: {validation_msg}")
                # Continue anyway with sanitized structure
            
            return json.dumps(structure, indent=2, ensure_ascii=False)
        except json.JSONDecodeError:
            # If JSON parsing fails, return a fallback structure
            return json.dumps([{
                "section": "解析错误",
                "disease": "解析错误",
                "treatment": f"请参考原始内容: {piece_content[:100]}..." if len(piece_content) > 100 else piece_content
            }])
    except Exception as e:
        print(f"Error in extract_semantic_json: {e}")
        return json.dumps([{
            "section": "处理错误",
            "disease": "处理错误",
            "treatment": f"错误信息: {str(e)}，请检查原始内容"
        }])






def process_document(docx_path: str):
    """Process a docx file through the complete pipeline."""
    print(f"Starting processing of {docx_path}")
    
    # Step 1: Convert to markdown
    print("Step 1: Converting docx to markdown...")
    conversion_result = docling_convert(docx_path)
    if "Error" in conversion_result or "Failed" in conversion_result:
        print(f"Conversion failed: {conversion_result}")
        return None
    
    print("Conversion successful")
    
    # Extract md path from result - docling creates a directory with the md file inside
    md_dir = Path(docx_path).with_suffix(".md")
    md_path = md_dir / Path(docx_path).stem
    md_path = md_path.with_suffix(".md")
    
    # Step 2: Analyze structure and split
    print("Step 2: Analyzing markdown structure and chunking by sections...")
    structure_result = analyze_markdown_structure(str(md_path))
    
    try:
        pieces = json.loads(structure_result)
        print(f"Successfully chunked into {len(pieces)} sections:")
        for i, piece in enumerate(pieces):
            print(f"  {i+1}. {piece.get('title', 'Unknown')}")
        
        results = []
        
        # Step 3: Extract JSON for each piece
        print(f"Step 3: Extracting semantic JSON for {len(pieces)} pieces...")
        for i, piece in enumerate(pieces):
            print(f"Processing piece {i+1}/{len(pieces)}: {piece.get('title', 'Unknown')}")
            json_result = extract_semantic_json(piece['content'])
            # json_result is already a JSON string, so parse it to validate
            try:
                parsed_json = json.loads(json_result)
                results.append({
                    "piece_id": i+1,
                    "title": piece.get('title', ''),
                    "structure_type": piece.get('structure_type', ''),
                    "semantic_json": parsed_json
                })
            except json.JSONDecodeError as parse_error:
                print(f"Warning: Failed to parse JSON for piece {i+1}: {parse_error}")
                results.append({
                    "piece_id": i+1,
                    "title": piece.get('title', ''),
                    "structure_type": piece.get('structure_type', ''),
                    "semantic_json": {
                        "type": "parsing_error",
                        "error": str(parse_error),
                        "raw_content": json_result
                    }
                })
        
        print(f"Processing complete. Generated {len(results)} semantic pieces.")
        return json.dumps(results, indent=2, ensure_ascii=False)
        
    except json.JSONDecodeError as e:
        print(f"Error parsing structure results: {str(e)}")
        return None


def main():
    # Check for help flag
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print("Usage: python main.py [input_file.docx] [output_file.json]")
        print("  input_file.docx: Path to the docx file to process (default: data/middle.docx)")
        print("  output_file.json: Path where to save the JSON results (default: same as input with .json extension)")
        print("Examples:")
        print("  python main.py                          # Process default file")
        print("  python main.py mydoc.docx               # Process mydoc.docx, save to mydoc.json")
        print("  python main.py mydoc.docx results.json  # Process mydoc.docx, save to results.json")
        return
    
    # Check for command line arguments
    if len(sys.argv) > 2:
        docx_file = sys.argv[1]
        output_file = sys.argv[2]
    elif len(sys.argv) > 1:
        docx_file = sys.argv[1]
        # Generate output filename based on input file
        input_path = Path(docx_file)
        output_file = input_path.with_suffix('.json')
    else:
        docx_file = "data/middle.docx"  # Default file
        output_file = "data/middle.json"  # Default output
    
    result = process_document(docx_file)
    
    if result is None:
        print("Processing failed. No output file generated.")
        return
    
    # Save the result to file
    try:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)  # Create directories if needed
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result)
        print(f"Processing complete. Results saved to: {output_path}")
        print(f"Generated {len(json.loads(result))} semantic pieces.")
    except Exception as e:
        print(f"Error saving results to file: {e}")
        print("Raw result:")
        print(result)


if __name__ == "__main__":
    main()
