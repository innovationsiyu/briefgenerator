
factcheck = """
# 简报事实部分检查与修正

## 检查任务
请对提供的简报事实部分进行全面检查，识别并修正所有错误，确保内容准确、完整、符合规范。

## 输入信息
- 原文：{source_text}
- 文章解读：{interpreted_source}
- 待检查的事实部分初稿：{content_draft}

## 检查维度

### 1. 事实准确性检查
- **数据核实**：所有数字、百分比、金额是否与原文完全一致
- **时间核实**：日期、时间表述是否准确，是否误用了文章发表时间
- **人物信息**：姓名、职位、所属机构是否正确
- **地理信息**：城市、国家、地区名称是否准确
- **政策文件**：政策名称、措施条目是否完整准确
- **专业术语**：经济金融术语及缩写是否正确

### 2. 逻辑结构检查
- **MECE原则**：各要点是否相互独立、完全穷尽
- **因果关系**：逻辑推理是否合理
- **层次结构**：是否符合金字塔原理

### 3. 格式规范检查
- **字数控制**：是否严格控制在300-400字范围内
- **时间表述**：是否统一使用相对时间（"近日"、"近期"、"今年"等）
- **数字格式**：是否使用阿拉伯数字
- **专业术语**：经济金融术语后是否正确标注缩写
- **完整短语**：不可分割短语是否完整呈现
- **陈述方式**：是否为客观陈述句，无感情色彩

### 4. 内容完整性检查
- **信息遗漏**：是否遗漏重要信息
- **信息重复**：是否存在重复表述
- **引用完整**：政策文件、重要表态是否完整引用

## 特别关注点

### 时间信息核查
- 严格区分文章发表时间与事件发生时间
- 检查是否误将发表时间作为事件时间
- 确保所有时间表述使用相对时间格式

### 政策文件处理
- 政策文件名称必须完整呈现
- 政策措施条目必须完整列出，不得省略
- 原文引用必须完整，不得部分引用

### 数据溯源
- 关键统计数据需标注来源
- 避免使用"据统计"、"数据显示"等模糊表述

## 输出格式

请返回JSON格式的检查结果：

```json
{
  "overall_assessment": {
    "word_count": 实际字数,
    "word_count_compliant": 是否符合300-400字要求(bool),
    "overall_quality": "优秀/良好/需改进",
    "major_issues_count": 主要问题数量
  },
  "detailed_checks": {
    "factual_accuracy": {
      "data_accuracy": {
        "status": "通过/有误",
        "issues": ["具体问题描述"]
      },
      "time_accuracy": {
        "status": "通过/有误",
        "issues": ["具体问题描述"]
      },
      "personnel_accuracy": {
        "status": "通过/有误",
        "issues": ["具体问题描述"]
      },
      "policy_accuracy": {
        "status": "通过/有误",
        "issues": ["具体问题描述"]
      }
    },
    "logical_structure": {
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
  "sentence_analysis": {
    "1": {
      "sentence": "第一句内容",
      "is_consistent": true/false,
      "reason": "分析理由",
      "confidence": 0.95,
      "suggested_revision": "修改建议（如有）"
    }
    // 继续分析每个句子
  },
  "revision_suggestions": {
    "critical_fixes": ["必须修改的关键问题"],
    "minor_improvements": ["可优化的细节问题"],
    "word_count_adjustment": "字数调整建议"
  },
  "revised_content": "修正后的完整事实部分内容（如需要）"
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
