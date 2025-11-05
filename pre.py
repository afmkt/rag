import subprocess
import json
import re
from pathlib import Path
from dotenv import load_dotenv
import logging
load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
def process_pre():
    """
    Convert data/pre.docx to markdown using docling,
    analyze the markdown to organize information as question-answer pairs,
    and save the JSON to data/pre.json.
    """
    input_file = Path("data/pre.docx")
    output_dir = Path("data")
    md_file = output_dir / "pre.md"
    json_file = output_dir / "pre.json"

    # Step 1: Call docling to convert docx to markdown
    cmd = [
        "docling",
        str(input_file),
        "--to", "md",
        "--output", str(output_dir)
    ]
    subprocess.run(cmd, check=True)

    # Step 2: Read and analyze the markdown file
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # Parse for question-answer pairs
    lines = md_content.split('\n')
    questions = []
    for line in lines:
        if '**' in line:
            # Find question between **
            matches = re.findall(r'\*\*(.*?)\*\*', line)
            for match in matches:
                question = match.strip()
                # Find options after the **
                # The options are in the same line after the **
                parts = line.split('**')
                # Find the part after the question
                idx = 0
                for i, part in enumerate(parts):
                    if question in part:
                        idx = i + 1
                        break
                if idx < len(parts):
                    rest = parts[idx].split('|')[0].strip()
                    if '□' in rest:
                        # Multiple choice
                        options = [opt.strip() for opt in re.split(r'□', rest) if opt.strip()]
                        q_type = "multiple_choice"
                    else:
                        # Text input
                        options = None
                        q_type = "text"
                    questions.append({"question": question, "type": q_type, "options": options})

    # Organize into JSON
    result = {"questions": questions}

    # Step 3: Save to JSON
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Processed {input_file} -> {md_file} -> {json_file}")

if __name__ == "__main__":
    process_pre()