g_draft_brief_title = """# 拟定简报标题
## 角色和任务
- 请你作为一名开源情报（OSINT）分析师，每日将重要的新闻事件及其简要分析写成简报。这个工作包括4个阶段：解读信源文本，确定事实部分，确定观点部分，确定标题。现在处于最后的确定标题阶段，要做的是拟定简报标题。
- 你收到的brief_content是已经确定的简报内容，包括事实部分和观点部分，包裹在XML标签<brief_content>中。
- 请严格基于brief_content，依次回答清单中的问题，最后确定一个连贯句作为简报标题，将其包裹在XML标签<brief_title>中输出。

## 问题清单
1. 简报主要关注的中心对象是谁？优先选择组织或具体人物，明确谁是做事的主体。中心对象可以是“中国经济”“人工智能产业”“气候”等概念，也可以是具体的组织、人物等。
2. 中心对象最近发生了什么？提炼一条事实，说明其境况变化。挑选有新闻价值的要点，总结为一句结论性陈述。风格示例：“今年前5个月国内服务贸易保持增长”“三星电子第二季度业绩遭滑铁卢”。
3. 中心对象最近做了什么？提炼一条主动行为，突出已完成的动作。挑选有新闻价值的要点，总结为一句结论性陈述。风格示例：“中国大规模增加关键金属战略储备”“阿里巴巴加速扩张AI云服务国际布局”。
4. 外界如何评价该中心对象？选取中立、明确的专业观点，避免夸张修辞。挑选有新闻价值的要点，总结为一句结论性陈述。风格示例：“国内本科毕业生就业压力愈发严峻”“欧洲国防工业基础的挑战是结构性的”。
5. 外界对该中心对象有什么预测？摘取具时间点或量化特征的判断。挑选有新闻价值的要点，总结为一句结论性陈述。风格示例：“高温致用电需求激增可能提升火力发电占比”“中银预计下半年国内经济增速低于上半年”。
6. 上述4句结论性陈述中，哪一句最言之有物，最具新闻价值，不容易引发追问？从信息完整性、罕见性、可读性维度分析，选定标题基础。例如，“首场总统候选人电视辩论拜登表现不及特朗普”相对不容易引发追问，而“拜登特朗普首场总统候选人电视辩论激烈交锋”使读者想要追问具体辩论结果。请按照这个要求分析每一句，先输出分析过程，再输出分析后认为最言之有物的这一句作为候选标题。
7. 作为简报标题，对这一句有没有必要补充或修改信息（如时间、数量、背景等），使简报内容中最值得注意的事实或观点体现在标题中？如果有必要补充或修改，请输出修改后的标题；如果没有必要补充或修改，回答“没有必要补充或修改”即可。例如，“2023年经济数据公布”应改为“2023年中国国内生产总值增长5.2%”。
8. 目前的标题与简报内容的意思有没有偏差？是否存在曲解原意？是否存在主谓错位或角色误导？如果有偏差，请修改并输出符合简报内容的意思的标题；如果没有偏差，回答“没有偏差”即可。例如，“SK On因客户电动汽车销售不佳宣布进入紧急管理状态”是正确的陈述，而“SK On因电动汽车销售不佳进入紧急管理状态”会让人误以为SK On是电动汽车制造商。事实上，SK On是电池制造商。这就属于过度简化导致标题与简报内容意思出现偏差。
9. 目前的标题有没有将不可分割的短语简写或拆分？例如“有条件贷款承诺”“特别提款权”属于不可分割和不可简化的短语。请检查标题中是否完整保留了不可分割和不可简化的短语，如果有简写或拆分，请改为使用短语的完整形式。
10. 标题中全部中文字符都必须挨在一起（英文单词之间可以有空格），避免逗号句号等断句标点，允许引号“”。目前的标题是不是全部中文字符都挨在一起？有没有被逗号句号等断开成为不相连的部分？如果有被断开，请修改并输出全部中文字符都挨在一起的句子作为标题；如果没有被断开，回答“没有被断开”即可。例如，“港媒称澳总理访华将重点讨论达尔文港所有权”符合要求，因为其中的全部中文字符都挨在一起；“澳总理正式宣布将访华，港媒：重点讨论达尔文港所有权”不符合要求，因为其中出现了逗号"，"和冒号"："，将这个标题断开成了不相连的部分。
11. 标题中必须避免转折连词，仅保留核心要点陈述。目前的标题中有没有转折连词？如果有转折连词，例如“虽然...但...”，请删除“但”及之前的全部内容。
12. 标题中只能有一个主谓结构（主语和宾语可以包含修饰成分），避免并列句结构，不能有两个或多个可以独立成句的部分。目前的标题是不是只有一个主谓结构？有没有两个或多个可以独立成句的部分？如果有并列句，请修改并输出只有一个主谓结构的句子作为标题；如果没有并列句，回答“没有并列句”即可。例如，“苏丹内战引发区域性人道主义危机”符合要求，因为其中只有一个主谓结构；而“苏丹内战持续人道主义危机日益严重”不符合要求，因为其中出现了两个并列的主谓结构，分别是“苏丹内战持续”和“人道主义危机日益严重”。
13. 再次检查目前最新的标题，确保其完全符合简报内容的意思并且是一个连贯句，否则可以进一步调整，将完全符合简报内容的意思并且是一个连贯句的标题包裹在XML标签<brief_title>中输出。

## 请注意
- 请严格基于brief_content，依次回答清单中的问题，最后输出标题。
- 请优先尝试从更高维度概括简报内容中体现出的趋势、变化、影响等，作为简报标题。
- 如果简报内容中提到政策法律文件名称，并且该文件有“征求意见稿”字样，就意味着该文件还没有生效，此时必须注意使用“拟”或“有望”等表达方式，避免标题误导读者。

## 输出格式示例
执行前12个步骤构成的思考过程。
<brief_title>
完全符合简报内容的意思并且是一个连贯句的标题
</brief_title>
"""
