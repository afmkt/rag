# Configuration for JSON Structure Stabilization
# Choose which method to use for converting DOCX to stable JSON

## Method Selection
EXTRACTION_METHOD = "structured"  # Options: "structured", "few_shot", "template", "hybrid"

## Validation Settings
ENABLE_SCHEMA_VALIDATION = True
MAX_RETRIES = 3
FALLBACK_ON_ERROR = True

## JSON Schema Enforcement
REQUIRED_FIELDS = {
    "type": "medical_guide",
    "title": "医疗信息",
    "sections": [],
    "key_points": [],
    "relationships": []
}

## Structure Constraints
MAX_SECTIONS = 20
MAX_KEY_POINTS_PER_SECTION = 10
MAX_RECOMMENDATIONS_PER_SECTION = 10
MAX_CONTENT_LENGTH = 1000

## Prompt Templates
STRUCTURED_PROMPT_TEMPLATE = """
You are a medical document parser. Convert the following markdown content into a structured JSON representation following this EXACT schema:

REQUIRED JSON STRUCTURE:
{example_json}

CRITICAL RULES:
1. ALWAYS use the exact field names shown in the example
2. "type" must be one of: "medical_guide", "clinical_protocol", "diagnostic_criteria", "treatment_plan"
3. Each section MUST have at least a "title" field
4. Arrays should contain strings, not nested objects unless specified
5. Use Chinese for content, English for field names
6. If a field is not applicable, use empty string "" or empty array []
7. DO NOT add extra fields not shown in the schema
8. Return ONLY valid JSON, no explanations or markdown

CONTENT: {content}
JSON OUTPUT:
"""

FEW_SHOT_PROMPT_TEMPLATE = """
Convert medical markdown content to structured JSON. Here are examples:

EXAMPLE 1:
Input: "血压偏低: 若血压长期低于90/60mmHg，伴有头晕、晕厥等症状，请到心内科门诊进一步诊治。"
Output:
{example_1}

EXAMPLE 2:
Input: "高血压病: 低盐饮食，适量运动，控制体重，劳逸结合，继续降压药物治疗，监测血压。"
Output:
{example_2}

Now convert this content following the same pattern:
{content}

Return ONLY the JSON structure:
"""

TEMPLATE_PROMPT = """
Fill in this JSON template with information from the medical content:

{template}

CONTENT: {content}

INSTRUCTIONS:
1. Replace ALL [PLACEHOLDER] values with actual extracted information
2. If information is not available, use empty string "" or empty array []
3. Keep numeric values as numbers, not strings
4. Return only the filled JSON, no explanations

FILLED JSON:
"""

## Default JSON Templates
DEFAULT_MEDICAL_TEMPLATE = {
    "type": "medical_guide",
    "title": "[EXTRACT_MAIN_TOPIC]",
    "description": "[OPTIONAL_OVERVIEW]",
    "sections": [
        {
            "title": "[SECTION_NAME]",
            "description": "[SECTION_DESCRIPTION]",
            "diagnostic_criteria": {
                "threshold": "[THRESHOLD_VALUES_IF_ANY]",
                "additional_tests": ["[TESTS_IF_MENTIONED]"]
            },
            "symptoms": ["[LIST_SYMPTOMS]"],
            "key_points": ["[IMPORTANT_POINTS]"],
            "recommendations": ["[TREATMENT_RECOMMENDATIONS]"],
            "measurement": {
                "systolic": "[NUMBER_IF_BLOOD_PRESSURE]",
                "diastolic": "[NUMBER_IF_BLOOD_PRESSURE]",
                "unit": "mmHg"
            },
            "status": "[CONDITION_STATUS]",
            "evaluation": "[CLINICAL_EVALUATION]"
        }
    ],
    "key_points": ["[OVERALL_KEY_POINTS]"],
    "relationships": [
        {
            "type": "diagnostic_criteria",
            "condition": "[CONDITION_NAME]",
            "threshold": "[THRESHOLD]",
            "symptoms": ["[ASSOCIATED_SYMPTOMS]"]
        }
    ]
}

## Quality Assurance Rules
QA_RULES = {
    "min_title_length": 2,
    "max_title_length": 100,
    "min_sections": 1,
    "max_sections": 20,
    "required_section_fields": ["title"],
    "allowed_types": ["medical_guide", "clinical_protocol", "diagnostic_criteria", "treatment_plan"],
    "max_array_length": 20,
    "numeric_fields": ["systolic", "diastolic"],
    "string_fields": ["title", "description", "threshold", "unit", "status", "evaluation"],
    "array_fields": ["key_points", "recommendations", "symptoms", "additional_tests", "related_conditions"]
}

## Error Handling
ERROR_RESPONSES = {
    "empty_content": {
        "type": "error",
        "title": "Empty Content",
        "error": "No content provided for processing",
        "sections": [],
        "key_points": [],
        "relationships": []
    },
    "parsing_error": {
        "type": "text_content", 
        "title": "Parsing Error",
        "error": "Failed to parse content into structured format",
        "sections": [],
        "key_points": [],
        "relationships": []
    },
    "llm_error": {
        "type": "error",
        "title": "Processing Error", 
        "error": "LLM failed to process content",
        "sections": [],
        "key_points": [],
        "relationships": []
    }
}

## Retry Strategy
RETRY_CONFIG = {
    "max_attempts": 3,
    "backoff_factor": 1.5,
    "fallback_methods": ["structured", "few_shot", "template"],
    "timeout_seconds": 30
}