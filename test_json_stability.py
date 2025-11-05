#!/usr/bin/env python3
"""
Example usage of stabilized JSON extraction methods for middle.json
Run this to test different approaches for stable DOCX to JSON conversion
"""

import json
import sys
from pathlib import Path

# Add current directory to path to import local modules
sys.path.append(str(Path(__file__).parent))

from middle_stable import (
    extract_semantic_json_stable,
    validate_json_structure,
    sanitize_and_fix_json,
    create_fallback_structure
)


def test_sample_content():
    """Test with sample medical content"""
    
    sample_content = """
# 血压异常管理

## 血压偏低
若血压长期低于90/60mmHg，伴有头晕、晕厥等症状，请到心内科门诊进一步诊治。

**症状：** 头晕、晕厥、乏力
**建议：** 心内科门诊就诊、完善相关检查

## 血压升高  
低盐饮食，随访血压，若不同日3次测量血压均≥140/90mmHg可诊断为高血压病，心内科门诊就诊，口服降压药物治疗。

**关键点：**
- 高血压诊断标准：≥140/90mmHg
- 需要多次测量确认
- 生活方式干预重要

**治疗建议：**
- 低盐饮食
- 适量运动
- 控制体重
- 定期监测血压
- 必要时药物治疗
"""
    
    print("=" * 80)
    print("TESTING STABLE JSON EXTRACTION METHODS")
    print("=" * 80)
    
    methods = ["structured", "few_shot", "template", "hybrid"]
    
    for method in methods:
        print(f"\n--- Testing Method: {method.upper()} ---")
        
        try:
            result_json = extract_semantic_json_stable(sample_content, method)
            result_data = json.loads(result_json)
            
            # Validate structure
            is_valid, validation_msg = validate_json_structure(result_data)
            
            print(f"✓ Method: {method}")
            print(f"✓ Valid JSON: {is_valid}")
            print(f"✓ Validation: {validation_msg}")
            print(f"✓ Type: {result_data.get('type', 'Unknown')}")
            print(f"✓ Title: {result_data.get('title', 'Unknown')}")
            print(f"✓ Sections count: {len(result_data.get('sections', []))}")
            print(f"✓ Key points count: {len(result_data.get('key_points', []))}")
            
            # Show first section as example
            if result_data.get('sections'):
                first_section = result_data['sections'][0]
                print(f"✓ First section title: {first_section.get('title', 'Unknown')}")
                print(f"✓ First section recommendations: {len(first_section.get('recommendations', []))}")
            
            # Save result for inspection
            output_file = f"test_output_{method}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, indent=2, ensure_ascii=False)
            print(f"✓ Saved to: {output_file}")
            
        except Exception as e:
            print(f"✗ Method {method} failed: {e}")
        
        print("-" * 60)


def compare_stability():
    """Compare stability across multiple runs"""
    
    content = """
高血压病 155/82mmHg
血压偏高，结合既往血压升高史，建议心内科门诊就诊，监测血压，明确有无高血压病。
治疗建议：降压药物治疗、低盐饮食、适量运动、控制体重、劳逸结合、随访血压。
"""
    
    print("\n" + "=" * 80)
    print("STABILITY COMPARISON - Multiple Runs")
    print("=" * 80)
    
    method = "structured"  # Use most stable method
    runs = 3
    
    results = []
    
    for i in range(runs):
        print(f"\nRun {i+1}/{runs}:")
        try:
            result = extract_semantic_json_stable(content, method)
            result_data = json.loads(result)
            results.append(result_data)
            
            print(f"  Type: {result_data.get('type')}")
            print(f"  Title: {result_data.get('title')}")
            print(f"  Sections: {len(result_data.get('sections', []))}")
            
            if result_data.get('sections'):
                section = result_data['sections'][0]
                print(f"  First section title: {section.get('title')}")
                print(f"  Recommendations count: {len(section.get('recommendations', []))}")
                
        except Exception as e:
            print(f"  Error: {e}")
    
    # Compare consistency
    print(f"\n--- Consistency Analysis ---")
    if len(results) > 1:
        # Check if titles are consistent
        titles = [r.get('title') for r in results]
        types = [r.get('type') for r in results]
        section_counts = [len(r.get('sections', [])) for r in results]
        
        print(f"Title consistency: {len(set(titles)) == 1}")
        print(f"Type consistency: {len(set(types)) == 1}")
        print(f"Section count consistency: {len(set(section_counts)) == 1}")
        print(f"Titles: {titles}")
        print(f"Types: {types}")
        print(f"Section counts: {section_counts}")


def test_edge_cases():
    """Test edge cases and error handling"""
    
    print("\n" + "=" * 80)
    print("EDGE CASE TESTING")
    print("=" * 80)
    
    test_cases = [
        ("Empty content", ""),
        ("Very short content", "血压高"),
        ("Only numbers", "155/82"),
        ("Mixed format", "血压：155/82mmHg\n建议：就诊"),
        ("Special characters", "血压≥140/90mmHg，症状：头晕、心悸等。"),
    ]
    
    for case_name, content in test_cases:
        print(f"\n--- {case_name} ---")
        try:
            result = extract_semantic_json_stable(content, "structured")
            result_data = json.loads(result)
            
            is_valid, msg = validate_json_structure(result_data)
            print(f"✓ Valid: {is_valid}")
            print(f"✓ Type: {result_data.get('type')}")
            print(f"✓ Has sections: {len(result_data.get('sections', [])) > 0}")
            
        except Exception as e:
            print(f"✗ Failed: {e}")


def main():
    """Main test runner"""
    
    print("Starting JSON Stabilization Tests...")
    
    # Test 1: Different methods
    test_sample_content()
    
    # Test 2: Stability comparison  
    compare_stability()
    
    # Test 3: Edge cases
    test_edge_cases()
    
    print("\n" + "=" * 80)
    print("TESTING COMPLETE")
    print("=" * 80)
    print("\nCheck the generated test_output_*.json files to see the results.")
    print("Run this script multiple times to test consistency.")


if __name__ == "__main__":
    main()