
factcheck = """
# 简报事实部分检查与修正（从第二句话开始）

## 任务目标
对简报事实部分进行全面检查，**重要：只检查从第二句话开始的内容，跳过第一句话**，确保内容准确、完整、符合规范，字数控制在300-400字。

## 输入信息
- 原文：{source_text}
- 文章解读：{interpreted_source}
- 待检查的事实部分初稿：{content_draft}

## 检查范围说明
**重要提醒：本检查只针对事实部分的第二句话及之后的内容，第一句话由专门的第一句话检查模块负责，请勿重复检查。**

在进行检查前，请先识别并跳过第一句话，然后对剩余内容进行以下标准的检查。

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
- **时间表述**：统一使用相对时间（\"近日\"、\"近期\"、\"今年\"等）
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
2. 避免\"据统计\"、\"数据显示\"等模糊表述
3. 数值精确度与原文保持一致

### 政策文件处理
1. 政策名称必须完整
2. 重要条目不得省略
3. 原文引用必须完整准确

## 检查流程

### 第零步：内容范围确定
**首先识别并跳过第一句话，只对第二句话及之后的内容进行检查。**

### 第一步：全面检查（仅针对第二句话及之后内容）
1. **事实准确性检查**：
   - 逐一核对所有数据、时间、人物、地理信息
   - 特别关注时间信息，确保不误用文章发表时间
   - 验证政策文件名称和条目的完整性

2. **逻辑结构检查**：
   - 验证要点是否符合MECE原则
   - 检查因果逻辑关系的合理性
   - 确认层次结构的清晰性

3. **格式规范检查**：
   - 统计字数是否在300-400字范围内
   - 检查时间表述是否使用相对格式
   - 验证数字格式和术语标注的规范性

4. **内容完整性检查**：
   - 确认重要信息无遗漏
   - 检查是否存在冗余表述
   - 验证引用的完整性

### 第二步：问题识别与分类
1. **严重问题**：事实错误、时间混淆、数据不一致
2. **一般问题**：格式不规范、表述不够客观、字数超标
3. **轻微问题**：术语标注不完整、表述可优化

### 第三步：修改建议生成
1. **针对性建议**：为每个问题提供具体的修改方案
2. **优先级排序**：按问题严重程度排序修改建议
3. **整体优化**：提供整体改进的方向性建议

## 输出要求

**重要：请根据检查结果以字符串形式输出修改建议，如果检查完美则输出\"完全正确\"。**

### 输出规则：
1. **问题导向**：如果发现问题，输出具体的修改建议
2. **完美通过**：如果没有任何问题，输出\"完全正确\"
3. **字符串格式**：直接输出修改建议文本，不包含JSON或其他格式
4. **具体明确**：修改建议要具体、可操作
5. **范围明确**：修改建议只针对第二句话及之后的内容

### 修改建议格式：
当发现问题时，按以下格式输出：
### 常见问题类型及修改建议示例：

**时间问题**：
- 问题：使用了文章发表时间\"12月25日\"作为事件时间
- 修改建议：将\"12月25日\"改为\"近日\"或\"近期\"

**数据问题**：
- 问题：数值与原文不一致
- 修改建议：将错误数值修正为原文中的准确数值

**格式问题**：
- 问题：字数超出400字限制
- 修改建议：删除冗余表述，精简至400字以内

**表述问题**：
- 问题：使用了\"据统计\"等模糊表述
- 修改建议：删除模糊表述，直接陈述具体数据

**逻辑问题**：
- 问题：要点之间存在重复或遗漏
- 修改建议：重新组织要点，确保符合MECE原则

**术语问题**：
- 问题：专业术语缺少规范标注
- 修改建议：为专业术语添加正确的缩写标注

### 特殊情况处理：
- **无问题情况**：如果内容完全符合所有检查标准，直接输出\"完全正确\"
- **轻微问题**：如果只有很轻微的格式问题，可以输出\"基本正确，建议微调：[具体建议]\"
- **严重问题**：如果存在事实错误等严重问题，必须提供详细的修改建议

## 执行指令

请严格按照以上标准对事实部分进行检查，**重要：只检查从第二句话开始的内容，跳过第一句话**，并根据检查结果以字符串形式输出相应的修改建议。如果内容完全正确，请输出\"完全正确\"。

特别注意：
1. **检查范围**：只检查第二句话及之后的内容，第一句话由专门模块负责
2. 重点检查时间信息，确保不误用文章发表时间
3. 核对所有数据的准确性
4. 验证字数是否在300-400字范围内
5. 确保表述客观、规范
6. 从\"interpreted_source\"中判断\"content_draft\"是否引用了文章的发表时间，特别注意文章开头的时间是否为信源发表时间
7. 输出格式必须为纯字符串，不得包含任何JSON格式
8. **再次强调**：检查时请先识别第一句话的结束位置，然后只对后续内容进行检查
"""
