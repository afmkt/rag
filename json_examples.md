# Enhanced JSON Schema and Examples for Stable middle.json Structure

## Method 1: Structured JSON Schema with Examples

### Medical Document JSON Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["type", "title", "sections"],
  "properties": {
    "type": {
      "type": "string",
      "enum": ["medical_guide", "clinical_protocol", "diagnostic_criteria", "treatment_plan"]
    },
    "title": {
      "type": "string",
      "description": "Main topic or condition name"
    },
    "description": {
      "type": "string",
      "description": "Optional overview description"
    },
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
              "unit": {"type": "string", "default": "mmHg"}
            }
          },
          "status": {"type": "string"},
          "evaluation": {"type": "string"},
          "symptoms": {
            "type": "array",
            "items": {"type": "string"}
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
          }
        }
      }
    },
    "key_points": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Overall key points for the entire document"
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
```

### Example 1: Blood Pressure Guide
```json
{
  "type": "medical_guide",
  "title": "血压异常管理",
  "description": "血压异常的诊断标准、症状识别和治疗建议",
  "sections": [
    {
      "title": "低血压",
      "description": "血压长期低于正常范围的情况",
      "diagnostic_criteria": {
        "threshold": "<90/60mmHg",
        "duration": "长期",
        "additional_tests": ["心电图", "血常规"]
      },
      "symptoms": ["头晕", "晕厥", "乏力"],
      "key_points": [
        "低血压阈值：<90/60mmHg",
        "常见症状：头晕、晕厥",
        "需要心内科门诊评估"
      ],
      "recommendations": [
        "心内科门诊就诊",
        "完善相关检查",
        "排除器质性疾病"
      ]
    },
    {
      "title": "高血压",
      "description": "血压持续升高的慢性疾病",
      "diagnostic_criteria": {
        "threshold": "≥140/90mmHg",
        "duration": "不同日3次测量",
        "additional_tests": ["24小时动态血压监测"]
      },
      "key_points": [
        "诊断标准：≥140/90mmHg",
        "需多次测量确认",
        "生活方式干预重要"
      ],
      "recommendations": [
        "低盐饮食",
        "适量运动", 
        "控制体重",
        "定期监测血压",
        "必要时药物治疗"
      ]
    }
  ],
  "key_points": [
    "血压正常范围：90/60-140/90mmHg",
    "诊断需要多次测量",
    "生活方式干预是基础治疗",
    "定期随访很重要"
  ],
  "relationships": [
    {
      "type": "diagnostic_criteria",
      "condition": "低血压",
      "threshold": "<90/60mmHg",
      "symptoms": ["头晕", "晕厥"]
    },
    {
      "type": "diagnostic_criteria", 
      "condition": "高血压",
      "threshold": "≥140/90mmHg",
      "related_conditions": ["心血管疾病", "肾脏疾病"]
    }
  ]
}
```

### Example 2: Cardiovascular Assessment
```json
{
  "type": "clinical_protocol",
  "title": "心血管系统评估",
  "description": "心血管系统常见异常的识别和处理",
  "sections": [
    {
      "title": "心律失常",
      "description": "心律不齐的评估和处理",
      "diagnostic_criteria": {
        "threshold": "心率<45次/min或>150次/min",
        "additional_tests": ["心电图", "24小时Holter监测"]
      },
      "symptoms": ["心悸", "胸闷", "头晕"],
      "key_points": [
        "心率正常范围：60-100次/min",
        "心律失常需心电图确诊",
        "严重心律失常需紧急处理"
      ],
      "recommendations": [
        "完善心电图检查",
        "心内科门诊就诊",
        "必要时24小时Holter监测",
        "避免诱发因素"
      ]
    },
    {
      "title": "心脏杂音",
      "description": "心脏听诊发现杂音的评估",
      "key_points": [
        "需要超声心动图评估",
        "区分生理性和病理性杂音",
        "注意是否伴有症状"
      ],
      "recommendations": [
        "超声心动图检查",
        "心内科门诊咨询",
        "定期随访"
      ]
    }
  ],
  "key_points": [
    "心血管评估需要综合分析",
    "心电图是基础检查",
    "症状和体征需要结合分析"
  ],
  "relationships": [
    {
      "type": "diagnostic_criteria",
      "condition": "心动过速",
      "threshold": ">100次/min",
      "related_conditions": ["甲亢", "焦虑", "发热"]
    },
    {
      "type": "diagnostic_criteria",
      "condition": "心动过缓", 
      "threshold": "<60次/min",
      "related_conditions": ["病态窦房结综合征", "房室传导阻滞"]
    }
  ]
}
```

### Example 3: Laboratory Results Interpretation
```json
{
  "type": "diagnostic_criteria",
  "title": "实验室检查结果解读",
  "description": "常见实验室检查异常值的临床意义",
  "sections": [
    {
      "title": "血脂异常",
      "description": "血脂各项指标异常的评估",
      "diagnostic_criteria": {
        "threshold": "总胆固醇>6.2mmol/L",
        "additional_tests": ["肝功能", "甲功能"]
      },
      "key_points": [
        "总胆固醇正常值：<5.2mmol/L",
        "LDL-C目标值因人而异",
        "需要评估心血管风险"
      ],
      "recommendations": [
        "饮食控制",
        "规律运动",
        "必要时他汀类药物",
        "定期复查血脂"
      ]
    },
    {
      "title": "血糖异常",
      "description": "血糖升高的评估和处理",
      "diagnostic_criteria": {
        "threshold": "空腹血糖≥7.0mmol/L",
        "additional_tests": ["糖化血红蛋白", "OGTT"]
      },
      "key_points": [
        "空腹血糖正常值：3.9-6.1mmol/L",
        "糖化血红蛋白反映长期血糖控制",
        "需要排除糖尿病"
      ],
      "recommendations": [
        "内分泌科门诊",
        "完善糖尿病相关检查",
        "饮食运动干预",
        "定期监测血糖"
      ]
    }
  ],
  "key_points": [
    "实验室检查需要结合临床",
    "异常值需要复查确认",
    "注意参考值范围差异"
  ],
  "relationships": [
    {
      "type": "risk_factor",
      "condition": "血脂异常",
      "related_conditions": ["冠心病", "脑卒中", "糖尿病"]
    },
    {
      "type": "complication",
      "condition": "糖尿病",
      "related_conditions": ["糖尿病肾病", "糖尿病视网膜病变", "糖尿病足"]
    }
  ]
}
```