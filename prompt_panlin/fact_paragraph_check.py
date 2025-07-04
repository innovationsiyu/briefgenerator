
factcheck = """
# 简报事实部分检查与修正

## 任务目标
对简报事实部分进行全面检查，确保内容准确、完整、符合规范，字数控制在300-400字。

## 输入信息
- 原文：{source_text}
- 文章解读：{interpreted_source}
- 待检查的事实部分初稿：{content_draft}

## 检查标准

### 1. 事实准确性（权重40%）
- **数据一致性**：数字、百分比、金额与原文完全一致
- **时间准确性**：严格区分文章发表时间与事件发生时间，使用相对时间表述
- **人物信息**：姓名、职位、机构准确无误
- **地理信息**：地名、区域表述准确
- **政策文件**：名称、条目完整准确
- **专业术语**：经济金融术语使用正确

### 2. 逻辑结构（权重25%）
- **MECE原则**：要点相互独立、完全穷尽
- **因果逻辑**：推理关系合理清晰
- **层次结构**：符合金字塔原理

### 3. 格式规范（权重20%）
- **字数控制**：严格控制在300-400字
- **时间表述**：统一使用相对时间（"近日"、"近期"、"今年"等）
- **数字格式**：使用阿拉伯数字
- **术语标注**：专业术语正确标注缩写
- **表述方式**：客观陈述，无感情色彩

### 4. 内容完整性（权重15%）
- **信息覆盖**：重要信息无遗漏
- **避免重复**：无冗余表述
- **引用完整**：政策文件、重要表态完整引用

## 特别检查要点

### 时间信息核查（重点）
1. 识别文章发表时间与事件发生时间
2. 检查是否误用发表时间作为事件时间
3. 确保时间表述使用相对格式
4. 验证时间逻辑的合理性

### 数据溯源验证
1. 关键数据必须有明确来源
2. 避免"据统计"、"数据显示"等模糊表述
3. 数值精确度与原文保持一致

### 政策文件处理
1. 政策名称必须完整
2. 重要条目不得省略
3. 原文引用必须完整准确

## 输出格式

请严格按照以下JSON格式返回检查结果：

```json
{
  "overall_assessment": {
    "word_count": 实际字数,
    "word_count_compliant": 是否符合300-400字要求(bool),
    "overall_score": 综合评分(0-100),
    "quality_level": "优秀/良好/合格/需改进",
    "critical_issues_count": 严重问题数量,
    "minor_issues_count": 一般问题数量
  },
  "detailed_analysis": {
    "factual_accuracy": {
      "score": 分数(0-40),
      "data_consistency": {
        "status": "通过/有误",
        "issues": ["具体问题描述"]
      },
      "time_accuracy": {
        "status": "通过/有误",
        "issues": ["具体问题描述"],
        "publication_time_misuse": "是否误用发表时间(bool)"
      },
      "personnel_info": {
        "status": "通过/有误",
        "issues": ["具体问题描述"]
      },
      "policy_accuracy": {
        "status": "通过/有误",
        "issues": ["具体问题描述"]
      }
    },
    "logical_structure": {
      "score": 分数(0-25),
      "mece_compliance": {
        "status": "通过/有误",
        "issues": ["具体问题描述"]
      },
      "causal_logic": {
        "status": "通过/有误",
        "issues": ["具体问题描述"]
      }
    },
    "format_compliance": {
      "score": 分数(0-20),
      "time_expression": {
        "status": "通过/有误",
        "issues": ["具体问题描述"]
      },
      "number_format": {
        "status": "通过/有误",
        "issues": ["具体问题描述"]
      },
      "terminology": {
        "status": "通过/有误",
        "issues": ["具体问题描述"]
      }
    },
    "content_completeness": {
      "score": 分数(0-15),
      "information_coverage": {
        "status": "通过/有误",
        "issues": ["具体问题描述"]
      },
      "duplication_check": {
        "status": "通过/有误",
        "issues": ["具体问题描述"]
      }
    }
  },
  "sentence_by_sentence_analysis": {
    "1": {
      "sentence": "第一句内容",
      "is_consistent": true/false,
      "accuracy_score": 分数(0-10),
      "issues": ["问题描述"],
      "suggested_revision": "修改建议（如有）",
      "confidence": 置信度(0-1)
    }
    // 继续分析每个句子
  },
  "improvement_recommendations": {
    "critical_fixes": [
      {
        "issue": "问题描述",
        "location": "位置",
        "suggested_fix": "修改建议",
        "priority": "高/中/低"
      }
    ],
    "minor_improvements": [
      {
        "issue": "问题描述",
        "suggested_improvement": "改进建议"
      }
    ],
    "word_count_adjustment": {
      "current_count": 当前字数,
      "target_range": "300-400",
      "adjustment_needed": "增加/减少X字",
      "suggestions": ["具体调整建议"]
    }
  },
  "revised_content": {
    "is_revision_needed": true/false,
    "revised_text": "修正后的完整内容（如需要）",
    "revision_summary": "修改要点总结"
  }
}
```

请分析以下多个句子是否基于提供的原文内容，对每个句子给出判断和理由：

原文：{source_text}

待核查句子列表：
{sentences_list}

请用JSON格式回答，返回一个对象，其中键为句子编号，值包含以下字段：
- is_consistent (bool): 是否与原文一致
- reason (str): 分析理由
- confidence (float): 判断置信度(0-1)

响应格式示例：
{{
  "1": {{
    "is_consistent": true,
    "reason": "这句话直接引用了原文的内容",
    "confidence": 0.95
  }},
  "2": {{
    "is_consistent": false,
    "reason": "这句话在原文中没有对应内容",
    "confidence": 0.90
  }}
}}

请只返回JSON格式的响应，不要包含其他文字。
请特别注意数字的核查，含有时间的信息需要特别注意是否与原文相匹配，
从"interpreted_source"中判断"content_draft"是否引用了文章的发表时间，特别注意文章开头的时间是否为信源发表时间，如果是，请检查语意与原文是否一致。
"interpreted_source" :{interpreted_source},"content_draft":{content_draft}
"""
