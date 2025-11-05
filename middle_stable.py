"""
Enhanced middle.py with stabilized JSON structure
Provides multiple methods for stable DOCX to JSON conversion
"""

import json
import os
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    print("Warning: jsonschema not installed. Validation will be skipped.")
    jsonschema = None
    HAS_JSONSCHEMA = False


@dataclass
class MedicalSection:
    """Structured representation of a medical section"""
    title: str
    description: str = ""
    key_points: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None
    diagnostic_criteria: Optional[Dict[str, Any]] = None
    symptoms: Optional[List[str]] = None
    measurement: Optional[Dict[str, Any]] = None
    status: str = ""
    evaluation: str = ""

    def __post_init__(self):
        if self.key_points is None:
            self.key_points = []
        if self.recommendations is None:
            self.recommendations = []
        if self.diagnostic_criteria is None:
            self.diagnostic_criteria = {}
        if self.symptoms is None:
            self.symptoms = []
        if self.measurement is None:
            self.measurement = {}


# JSON Schema for validation
MEDICAL_JSON_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["type", "title", "sections"],
    "properties": {
        "type": {
            "type": "string",
            "enum": ["medical_guide", "clinical_protocol", "diagnostic_criteria", "treatment_plan"]
        },
        "title": {"type": "string"},
        "description": {"type": "string"},
        "sections": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["title"],
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "key_points": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "recommendations": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "measurement": {
                        "type": "object",
                        "properties": {
                            "systolic": {"type": "number"},
                            "diastolic": {"type": "number"},
                            "unit": {"type": "string"}
                        }
                    },
                    "diagnostic_criteria": {
                        "type": "object",
                        "properties": {
                            "threshold": {"type": "string"},
                            "duration": {"type": "string"},
                            "additional_tests": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        }
                    },
                    "symptoms": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "status": {"type": "string"},
                    "evaluation": {"type": "string"}
                }
            }
        },
        "key_points": {
            "type": "array",
            "items": {"type": "string"}
        },
        "relationships": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["type", "condition"],
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": ["diagnostic_criteria", "treatment_relationship", "risk_factor", "complication"]
                    },
                    "condition": {"type": "string"},
                    "threshold": {"type": "string"},
                    "symptoms": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "related_conditions": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                }
            }
        }
    }
}


def create_structured_prompt_with_examples(piece_content: str) -> str:
    """Create a structured prompt with JSON schema and examples"""
    
    example_json = {
        "type": "medical_guide",
        "title": "血压管理",
        "description": "血压异常的诊断和处理指南",
        "sections": [
            {
                "title": "低血压",
                "description": "血压低于正常范围的情况",
                "diagnostic_criteria": {
                    "threshold": "<90/60mmHg",
                    "duration": "长期",
                    "additional_tests": ["心电图", "血常规"]
                },
                "symptoms": ["头晕", "晕厥"],
                "key_points": [
                    "低血压阈值：<90/60mmHg",
                    "常见症状：头晕、晕厥"
                ],
                "recommendations": [
                    "心内科门诊就诊",
                    "完善相关检查"
                ]
            }
        ],
        "key_points": [
            "血压正常范围：90/60-140/90mmHg",
            "诊断需要多次测量"
        ],
        "relationships": [
            {
                "type": "diagnostic_criteria",
                "condition": "低血压",
                "threshold": "<90/60mmHg",
                "symptoms": ["头晕", "晕厥"]
            }
        ]
    }
    
    prompt = f"""
You are a medical document parser. Convert the following markdown content into a structured JSON representation following this EXACT schema:

REQUIRED JSON STRUCTURE:
{json.dumps(example_json, indent=2, ensure_ascii=False)}

RULES:
1. ALWAYS use the exact field names shown in the example
2. "type" must be one of: "medical_guide", "clinical_protocol", "diagnostic_criteria", "treatment_plan"
3. Each section MUST have at least a "title" field
4. Arrays should contain strings, not nested objects unless specified
5. Use Chinese for content, English for field names
6. If a field is not applicable, use empty string "" or empty array []
7. DO NOT add extra fields not shown in the schema
8. Return ONLY valid JSON, no explanations or markdown

CONTENT TO PROCESS:
{piece_content}

JSON OUTPUT:
"""
    return prompt


def create_few_shot_prompt(piece_content: str) -> str:
    """Create a few-shot prompt with multiple examples"""
    
    prompt = f"""
Convert medical markdown content to structured JSON. Here are examples:

EXAMPLE 1:
Input: "血压偏低: 若血压长期低于90/60mmHg，伴有头晕、晕厥等症状，请到心内科门诊进一步诊治。"
Output:
{{
  "type": "medical_guide",
  "title": "血压偏低",
  "sections": [
    {{
      "title": "血压偏低",
      "description": "若血压长期低于90/60mmHg，伴有头晕、晕厥等症状，请到心内科门诊进一步诊治。",
      "diagnostic_criteria": {{
        "threshold": "<90/60mmHg",
        "duration": "长期"
      }},
      "symptoms": ["头晕", "晕厥"],
      "recommendations": ["心内科门诊就诊"]
    }}
  ],
  "key_points": ["低血压阈值：<90/60mmHg", "常见症状：头晕、晕厥"]
}}

EXAMPLE 2:
Input: "高血压病: 低盐饮食，适量运动，控制体重，劳逸结合，继续降压药物治疗，监测血压。"
Output:
{{
  "type": "treatment_plan",
  "title": "高血压病",
  "sections": [
    {{
      "title": "高血压病治疗",
      "description": "高血压的综合管理方案",
      "recommendations": ["低盐饮食", "适量运动", "控制体重", "劳逸结合", "继续降压药物治疗", "监测血压"]
    }}
  ],
  "key_points": ["生活方式干预", "药物治疗", "定期监测"]
}}

Now convert this content following the same pattern:
{piece_content}

Return ONLY the JSON structure:
"""
    return prompt


def create_template_based_prompt(piece_content: str) -> str:
    """Create a template-based prompt with strict structure"""
    
    prompt = f"""
Fill in this JSON template with information from the medical content:

{{
  "type": "medical_guide",
  "title": "[EXTRACT_MAIN_TOPIC]",
  "description": "[OPTIONAL_OVERVIEW]",
  "sections": [
    {{
      "title": "[SECTION_NAME]",
      "description": "[SECTION_DESCRIPTION]",
      "diagnostic_criteria": {{
        "threshold": "[THRESHOLD_VALUES_IF_ANY]",
        "additional_tests": ["[TESTS_IF_MENTIONED]"]
      }},
      "symptoms": ["[LIST_SYMPTOMS]"],
      "key_points": ["[IMPORTANT_POINTS]"],
      "recommendations": ["[TREATMENT_RECOMMENDATIONS]"],
      "measurement": {{
        "systolic": [NUMBER_IF_BLOOD_PRESSURE],
        "diastolic": [NUMBER_IF_BLOOD_PRESSURE],
        "unit": "mmHg"
      }},
      "status": "[CONDITION_STATUS]",
      "evaluation": "[CLINICAL_EVALUATION]"
    }}
  ],
  "key_points": ["[OVERALL_KEY_POINTS]"],
  "relationships": [
    {{
      "type": "diagnostic_criteria",
      "condition": "[CONDITION_NAME]",
      "threshold": "[THRESHOLD]",
      "symptoms": ["[ASSOCIATED_SYMPTOMS]"]
    }}
  ]
}}

CONTENT:
{piece_content}

INSTRUCTIONS:
1. Replace ALL [PLACEHOLDER] values with actual extracted information
2. If information is not available, use empty string "" or empty array []
3. Keep numeric values as numbers, not strings
4. Ensure all arrays contain only strings unless specified otherwise
5. Return only the filled JSON, no explanations

FILLED JSON:
"""
    return prompt


def validate_json_structure(json_data: Dict[str, Any]) -> tuple[bool, str]:
    """Validate JSON against the medical schema"""
    if not HAS_JSONSCHEMA:
        return True, "Validation skipped - jsonschema not available"
    
    try:
        jsonschema.validate(json_data, MEDICAL_JSON_SCHEMA)
        return True, "Valid"
    except jsonschema.ValidationError as e:
        return False, str(e)


def sanitize_and_fix_json(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """Fix common JSON structure issues"""
    
    # Ensure required fields exist
    if "type" not in json_data:
        json_data["type"] = "medical_guide"
    
    if "title" not in json_data:
        json_data["title"] = "医疗信息"
    
    if "sections" not in json_data:
        json_data["sections"] = []
    
    # Fix sections structure
    for section in json_data.get("sections", []):
        if "title" not in section:
            section["title"] = "未知章节"
        
        # Ensure arrays are actually arrays
        for array_field in ["key_points", "recommendations", "symptoms"]:
            if array_field in section and not isinstance(section[array_field], list):
                if isinstance(section[array_field], str):
                    section[array_field] = [section[array_field]]
                else:
                    section[array_field] = []
        
        # Ensure measurement is an object
        if "measurement" in section and not isinstance(section["measurement"], dict):
            section["measurement"] = {}
        
        # Ensure diagnostic_criteria is an object
        if "diagnostic_criteria" in section and not isinstance(section["diagnostic_criteria"], dict):
            section["diagnostic_criteria"] = {}
    
    # Ensure top-level arrays
    for array_field in ["key_points", "relationships"]:
        if array_field in json_data and not isinstance(json_data[array_field], list):
            if isinstance(json_data[array_field], str):
                json_data[array_field] = [json_data[array_field]]
            else:
                json_data[array_field] = []
    
    return json_data


def extract_semantic_json_stable(piece_content: str, method: str = "structured") -> str:
    """
    Extract semantic JSON with stable structure using different methods
    
    Args:
        piece_content: The markdown content
        method: "structured", "few_shot", "template", or "hybrid"
    
    Returns:
        JSON string with stable structure
    """
    
    methods = {
        "structured": create_structured_prompt_with_examples,
        "few_shot": create_few_shot_prompt,
        "template": create_template_based_prompt
    }
    
    if method == "hybrid":
        # Try multiple methods and pick the best result
        for method_name in ["structured", "few_shot", "template"]:
            try:
                result = extract_semantic_json_stable(piece_content, method_name)
                json_data = json.loads(result)
                is_valid, error = validate_json_structure(json_data)
                if is_valid:
                    return result
            except Exception as e:
                print(f"Method {method_name} failed: {e}")
                continue
        
        # If all methods fail, return fallback
        return create_fallback_structure(piece_content)
    
    if method not in methods:
        method = "structured"
    
    prompt = methods[method](piece_content)
    
    try:
        # Here you would call your LLM
        # For this example, I'll show the structure
        openrouter_api_key = os.getenv("OPEN_ROUTER_API_KEY")
        openrouter_model = os.getenv("OPEN_ROUTER_MODEL", "openrouter/openchat-3.5-0106")
        from openrouter_llm import OpenRouterLLM
        llm = OpenRouterLLM(api_key=openrouter_api_key, model=openrouter_model)
        
        response = llm.invoke(prompt)
        response_text = str(response.content).strip()
        
        # Clean up response
        response_text = clean_llm_response(response_text)
        
        # Parse and validate
        json_data = json.loads(response_text)
        
        # Sanitize structure
        json_data = sanitize_and_fix_json(json_data)
        
        # Final validation
        is_valid, error = validate_json_structure(json_data)
        if not is_valid:
            print(f"Validation error: {error}")
            # Try to fix and re-validate
            json_data = sanitize_and_fix_json(json_data)
        
        return json.dumps(json_data, indent=2, ensure_ascii=False)
        
    except Exception as e:
        print(f"Error in stable extraction: {e}")
        return create_fallback_structure(piece_content)


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
    
    # Find JSON content between { and }
    start_idx = response_text.find('{')
    end_idx = response_text.rfind('}')
    
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        response_text = response_text[start_idx:end_idx + 1]
    
    return response_text


def create_fallback_structure(piece_content: str) -> str:
    """Create a fallback structure when LLM fails"""
    
    # Extract basic information using regex
    title = extract_title_from_content(piece_content)
    sections = extract_sections_from_content(piece_content)
    
    fallback_structure = {
        "type": "medical_guide",
        "title": title,
        "description": "自动提取的医疗信息",
        "sections": sections,
        "key_points": extract_key_points_regex(piece_content),
        "relationships": []
    }
    
    return json.dumps(fallback_structure, indent=2, ensure_ascii=False)


def extract_title_from_content(content: str) -> str:
    """Extract title using regex patterns"""
    
    # Look for markdown headers
    header_match = re.search(r'^#{1,3}\s*(.+)$', content, re.MULTILINE)
    if header_match:
        return header_match.group(1).strip()
    
    # Look for bold text at the beginning
    bold_match = re.search(r'^\*\*(.+?)\*\*', content)
    if bold_match:
        return bold_match.group(1).strip()
    
    # Extract first line as title
    lines = content.split('\n')
    for line in lines:
        if line.strip():
            return line.strip()[:50]  # Limit length
    
    return "医疗信息"


def extract_sections_from_content(content: str) -> List[Dict[str, Any]]:
    """Extract sections using regex patterns"""
    
    sections = []
    
    # Split by headers or bold text
    section_pattern = r'(?:^#{1,3}\s*(.+?)$|^\*\*(.+?)\*\*)'
    matches = list(re.finditer(section_pattern, content, re.MULTILINE))
    
    for i, match in enumerate(matches):
        title = (match.group(1) or match.group(2)).strip()
        
        # Extract content until next section
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        section_content = content[start:end].strip()
        
        section = {
            "title": title,
            "description": section_content[:200] + "..." if len(section_content) > 200 else section_content,
            "key_points": extract_key_points_from_section(section_content),
            "recommendations": extract_recommendations_from_section(section_content)
        }
        
        sections.append(section)
    
    if not sections:
        # If no sections found, create one section with all content
        sections.append({
            "title": "主要内容",
            "description": content[:300] + "..." if len(content) > 300 else content,
            "key_points": extract_key_points_regex(content),
            "recommendations": []
        })
    
    return sections


def extract_key_points_regex(content: str) -> List[str]:
    """Extract key points using regex"""
    
    key_points = []
    
    # Look for numbered lists
    numbered_pattern = r'^\d+\.\s*(.+)$'
    numbered_matches = re.findall(numbered_pattern, content, re.MULTILINE)
    key_points.extend(numbered_matches)
    
    # Look for bullet points
    bullet_pattern = r'^[-*]\s*(.+)$'
    bullet_matches = re.findall(bullet_pattern, content, re.MULTILINE)
    key_points.extend(bullet_matches)
    
    # Look for medical thresholds
    threshold_pattern = r'([<>≥≤]\s*\d+[./]\d*\s*\w+)'
    threshold_matches = re.findall(threshold_pattern, content)
    key_points.extend([f"阈值：{match}" for match in threshold_matches])
    
    return key_points[:10]  # Limit to 10 key points


def extract_key_points_from_section(content: str) -> List[str]:
    """Extract key points from a specific section"""
    return extract_key_points_regex(content)[:5]  # Limit to 5 per section


def extract_recommendations_from_section(content: str) -> List[str]:
    """Extract recommendations from section content"""
    
    recommendations = []
    
    # Look for recommendation keywords
    recommendation_keywords = [
        "建议", "推荐", "应该", "需要", "门诊", "就诊", "治疗", "监测", "随访", "复查"
    ]
    
    sentences = re.split(r'[。！？；]', content)
    for sentence in sentences:
        for keyword in recommendation_keywords:
            if keyword in sentence and len(sentence.strip()) > 5:
                recommendations.append(sentence.strip())
                break
    
    return recommendations[:5]  # Limit to 5 recommendations