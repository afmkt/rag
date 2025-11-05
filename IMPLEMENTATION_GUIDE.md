# Implementation Guide: Stabilizing middle.json Structure

## Quick Start

To stabilize your `middle.json` structure, follow these steps:

### 1. Update your existing middle.py

Replace your current `extract_semantic_json()` function with the improved version that includes:

- **Structured prompts with examples**
- **JSON schema validation** 
- **Response cleaning and sanitization**
- **Fallback error handling**

### 2. Key Improvements Made

#### Enhanced LLM Prompt
```python
# Old prompt (unstable)
prompt = "Convert this markdown content into a structured JSON representation..."

# New prompt (stable)
prompt = f"""
You are a medical document parser. Convert the following markdown content into a structured JSON representation following this EXACT schema:

REQUIRED JSON STRUCTURE:
{json.dumps(example_json, indent=2, ensure_ascii=False)}

CRITICAL RULES:
1. ALWAYS use the exact field names shown in the example
2. "type" must be one of: "medical_guide", "clinical_protocol", "diagnostic_criteria", "treatment_plan"
3. Each section MUST have at least a "title" field
...
"""
```

#### Response Sanitization
```python
def clean_llm_response(response_text: str) -> str:
    """Clean LLM response to extract valid JSON"""
    # Remove markdown code blocks
    # Remove language indicators  
    # Extract JSON between { and }
    return clean_response

def sanitize_and_fix_json(json_data: dict) -> dict:
    """Fix common JSON structure issues"""
    # Ensure required fields exist
    # Fix array/object types
    # Validate field constraints
    return fixed_data
```

#### Comprehensive Error Handling
```python
try:
    structure = json.loads(response_text)
    structure = sanitize_and_fix_json(structure)
    return json.dumps(structure, indent=2, ensure_ascii=False)
except json.JSONDecodeError as json_error:
    # Return structured fallback instead of raw error
    return json.dumps({
        "type": "text_content",
        "title": "Raw Content", 
        "sections": [...],  # Always include required fields
        "key_points": [],
        "relationships": []
    })
```

### 3. Configuration Options

You can choose different stabilization methods:

```python
# Method 1: Structured prompt with schema (Recommended)
result = extract_semantic_json_stable(content, "structured")

# Method 2: Few-shot learning with examples  
result = extract_semantic_json_stable(content, "few_shot")

# Method 3: Template-based extraction
result = extract_semantic_json_stable(content, "template")

# Method 4: Hybrid approach (tries multiple methods)
result = extract_semantic_json_stable(content, "hybrid")
```

### 4. Testing Stability

Run the test script to verify improvements:

```bash
python test_json_stability.py
```

This will:
- Test different extraction methods
- Compare consistency across multiple runs  
- Test edge cases and error handling
- Generate sample output files for inspection

### 5. Expected Improvements

**Before (Unstable):**
- JSON structure varies between runs
- Missing required fields
- Inconsistent field types (sometimes string, sometimes array)
- Parse errors cause complete failure
- No validation or sanitization

**After (Stable):**
- Consistent JSON structure across runs
- Required fields always present
- Predictable field types  
- Graceful error handling with structured fallbacks
- Automatic validation and fixing

### 6. Sample Stable Output

```json
{
  "type": "medical_guide",
  "title": "血压异常管理",
  "description": "血压异常的诊断和处理指南",
  "sections": [
    {
      "title": "低血压",
      "description": "血压低于正常范围的情况",
      "diagnostic_criteria": {
        "threshold": "<90/60mmHg",
        "duration": "长期"
      },
      "symptoms": ["头晕", "晕厥"],
      "key_points": ["低血压阈值：<90/60mmHg"],
      "recommendations": ["心内科门诊就诊"]
    }
  ],
  "key_points": ["血压正常范围：90/60-140/90mmHg"],
  "relationships": [
    {
      "type": "diagnostic_criteria", 
      "condition": "低血压",
      "threshold": "<90/60mmHg",
      "symptoms": ["头晕", "晕厥"]
    }
  ]
}
```

### 7. Installation Requirements

```bash
# Optional: For schema validation
pip install jsonschema

# Your existing dependencies should work
# openrouter_llm, rich, etc.
```

### 8. Monitoring and Maintenance

1. **Log validation results** to monitor JSON quality
2. **Track parsing success rates** across different document types
3. **Update examples** in prompts based on new document patterns
4. **Review and refine fallback structures** periodically

### 9. Integration with Existing Code

The improved functions are drop-in replacements:

```python
# Replace this line in your existing middle.py:
json_result = extract_semantic_json(piece['content'])

# With this (if using the stable version):
json_result = extract_semantic_json_stable(piece['content'], "structured")

# Or keep using the same function name after updating the implementation
json_result = extract_semantic_json(piece['content'])  # Now uses improved version
```

### 10. Performance Considerations

- **Structured prompts** may use more tokens but provide better consistency
- **Validation and sanitization** add minimal processing time
- **Fallback handling** prevents complete failures
- **Schema validation** helps catch issues early

The trade-off of slightly more processing time for significantly better stability is generally worthwhile for production systems.