import json

json_format = {
    "新闻文章发布日期": "2022-11-30",
    "中心新闻事件5w1h要素": {
        "who": "美国人工智能研究机构OpenAI",
        "what": "发布聊天机器人应用ChatGPT",
        "when": "11月30日",
        "where": "",
        "why": "旨在展示其大语言模型的自然语言理解与内容生成能力并收集用户反馈",
        "how": ""
    },
    "时间提示词及其对应的事件": [
        "11月30日，OpenAI发布聊天机器人应用ChatGPT。",
        "今年以来，相关历史事件回顾",
        "接下来，未来事件预告或预测"
    ],
    "补充上下文的数据或统计信息": [
        "GPT-3拥有1750亿个参数",
        "在GPT-3中，单个参数采用16位精度存储，占用2字节",
        "加载GPT-3的全部模型参数需要350GB存储空间"
    ],
    "人物和组织": [
        "OpenAI研究员张三"
    ],
    "城市或行政区": [
        "中国台湾"
    ],
    "引文标题": [
        "《Attention Is All You Need》"
    ],
    "不可分割和不可简化的短语": [
        "有条件贷款承诺",
        "特别提款权"
    ],
    "经济和金融专业术语": [
        "采购经理人指数（PMI）",
        "生产者价格指数（PPI）",
        "消费者价格指数（CPI）"
    ],
    "科技专业术语": [
        "人类反馈强化学习（RLHF）：一种结合人类反馈与强化学习的训练方法，通过将人类偏好建模为奖励信号来微调大语言模型，使模型的输出与人类偏好和价值观对齐。"
    ],
    "关键要点提炼": [
        "ChatGPT使用的是基于GPT-3.5并通过人类反馈强化学习（RLHF）方法训练得到的对话式模型。",
        "ChatGPT能够在对话中回答追问的问题、承认错误、质疑不正确的前提并拒绝不当请求。",
        "ChatGPT存在有时会写出看似合理却不正确或荒谬的答案、对输入措辞的微调很敏感、以及回答过于冗长等局限性。"
    ],
    "分析师的关注点": "ChatGPT的局限性",
    "中心新闻事件总结": "11月30日，美国人工智能研究机构OpenAI发布聊天机器人应用ChatGPT，旨在展示其大语言模型的自然语言理解与内容生成能力并收集用户反馈。后续内容。",
    "分析师的观点或分析要求": ""
}

a_interpret_source_text = f"""# 解读信源文本

## 角色和任务
- 请你作为一名开源情报（OSINT）分析师，每日将重要的新闻事件及其简要分析写成简报。这个工作包括4个阶段：解读信源文本，确定事实部分，确定观点部分，确定标题。现在要做的是解读信源文本。
- 你收到的source_text包括一篇或多篇新闻文章，可能还包括其他分析师明确提出的关注点，以及分析师的观点或分析要求，这些都包裹在XML标签<source_text>中。
- 请严格基于source_text，依次执行行动清单中的14个步骤，构成JSON，包裹在XML标签<interpretation>中输出。避免输出任何额外内容，仅仅以<interpretation>开始，以</interpretation>结束，内部是JSON。

## 行动清单
1. 提取出source_text中的新闻文章发布日期（注意不是任何事件发生的日期）并转换为ISO格式，例如“2022-11-30”。如果没有找到文章发布日期，输出空字符串""。
2. 确定source_text中的新闻所报道的中心新闻事件，提取出5W1H要素，包括：中心新闻事件涉及的人物和/或组织（Who）、行动或变化（What）、时点或时段（When）、地点和/或场所（Where）、目的和/或背景（Why）、过程和/或影响（How）。如果缺失某个要素的信息，输出空字符串""。
3. 提取出文章中的每一个时间提示词及其对应的事件，不只是中心新闻事件，也包括相关历史事件回顾和未来事件预告或预测。既可以是绝对时间表述（如“11月30日”），也可以是相对时间表述（如“周三”“昨日”“日前”“今年以来”“接下来”“未来”）。
4. 提取出文章中的每一个数据或统计信息，为每一个数据补充上下文使其含义能够被独立理解。如果没有任何数据或统计信息，输出空列表[]。
5. 提取出文章中的全部人物和组织，对于人名，以其所在组织和职业头衔为前缀，例如“OpenAI研究员张三”。如果只有人名或只有组织名称，则仅提取人名或组织名称即可。
6. 提取出文章中的全部城市或行政区，以其所属国家或地区为前缀，例如“中国台湾”。如果只有城市或行政区名称，则基于你的知识补充其所属国家或地区作为前缀。如果没有任何城市或行政区名称，输出空列表[]。
7. 文章中有没有提及政策文件、法律文件、学术文献，或者其它类型的引文？如果有，提取出每一个完整的引文标题并使用书名号《》；如果没有，输出空列表[]。
8. 文章中有没有不可分割和不可简化的短语？例如“有条件贷款承诺”“特别提款权”，这样的短语不能被分为两个词语或省去其中任何字词，否则会改变原意。如果有，提取出每一个完整的不可分割和不可简化的短语；如果没有，输出空列表[]。
9. 文章中有没有经济和金融领域的专业术语？如果有，提取出每一个专业术语并基于你的知识补充其英文的缩写；如果没有，输出空列表[]。
10. 文章中有没有信息技术、能源、生物等科技领域的专业术语？如果有，提取出每一个专业术语并基于你的知识补充其英文的缩写，同时基于你的知识提供一句话解释；如果没有，输出空列表[]。仅需收录如“人类反馈强化学习（RLHF）”这样关于技术细节的术语，无需收录如“人工智能/AI”“大语言模型/LLM”这样普及度很高的词语。
11. 如果完整读完文章后只需记住少数几个关键要点，应该是什么？用精简的语言从全文中提炼出几个关键要点，要求每一个都必须是最终结论，不是其它结论的论据，多个要点之间没有重复信息。
12. source_text中，除了新闻文章，是否包括其他分析师明确提出的关注点？如果有，提取出这些关注点，可以调整表达使其更易于理解；如果没有，输出空字符串""。
13. 基于上述信息，用几句话总结这个中心新闻事件，以时间提示词开头，总体概括现有的新闻要素信息，以及分析师的关注点对应的信息（如有）。
14. source_text中，除了新闻文章，是否包括其他分析师的观点或分析要求？如果有，提取出这些观点或分析要求，可以调整表达使其更易于理解；如果没有，输出空字符串""。

## 输出格式示例
<interpretation>
{json.dumps(json_format, indent=4, ensure_ascii=False)}
</interpretation>
"""

if __name__ == "__main__":
    print(a_interpret_source_text)
