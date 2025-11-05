import subprocess
import json
from pathlib import Path
from dotenv import load_dotenv
import logging
load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

def parse_markdown_table(table_lines):
    """
    Parse a markdown table into a list of records (one per row).
    Assumes standard table format with header.
    """
    if len(table_lines) < 3:  # header, separator, at least one row
        return None
    # Check if first row is uniform (like title repeated)
    first_row_cells = [cell.strip() for cell in table_lines[0].split('|')[1:-1]]
    if len(set(first_row_cells)) == 1:  # All cells identical, treat as title
        # Use third row as header
        header_line = table_lines[2]
        headers = [cell.strip() for cell in header_line.split('|')[1:-1]]
        start_row = 3  # Skip title, separator, header
    else:
        header_line = table_lines[0]
        headers = [cell.strip() for cell in header_line.split('|')[1:-1]]
        start_row = 2
    # Skip separator line
    rows = []
    for line in table_lines[start_row:]:
        line = line.strip()
        if not line:
            continue
        cells = [cell.strip() for cell in line.split('|')[1:-1]]
        if len(cells) == len(headers):
            row_dict = dict(zip(headers, cells))
            rows.append(row_dict)
    return rows if rows else None

def process_post():
    """
    Convert data/post.docx to markdown using docling,
    analyze the markdown to organize information into JSON,
    and save the JSON to data/post.json.
    """
    input_file = Path("data/post.docx")
    output_dir = Path("data")
    md_file = output_dir / "post.md"
    json_file = output_dir / "post.json"

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

    # Parse markdown into structured JSON
    lines = md_content.split('\n')
    parsed_content = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith('|') and '|' in line:
            # Start of table
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                table_lines.append(lines[i])
                i += 1
            # Parse table
            table_data = parse_markdown_table(table_lines)
            if table_data:
                parsed_content.append({"type": "table", "data": table_data})
            else:
                # If parsing failed, add as text
                parsed_content.append({"type": "text", "data": '\n'.join(table_lines)})
        else:
            # Collect text until next table or end
            text_lines = []
            while i < len(lines) and not (lines[i].strip().startswith('|') and '|' in lines[i]):
                text_lines.append(lines[i])
                i += 1
            text = '\n'.join(text_lines).strip()
            if text:
                parsed_content.append({"type": "text", "data": text})

    # Organize into JSON
    result = {"content": parsed_content}

    # Step 3: Save to JSON
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Processed {input_file} -> {md_file} -> {json_file}")

if __name__ == "__main__":
    process_post()