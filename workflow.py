# workflow.py

import asyncio
import os
import csv
import pandas as pd
import json
import ast
import itertools
from utils import convert_to_cn_term, convert_to_date, clean_stock_codes, get_prompt, call_llm, call_local_llm, extract_with_xml, split_to_sentences, save_as_txt, replace_year_with_2025, remove_year_at_start


def get_source_files() -> list[str]:
    """
    获取inputs文件夹中所有txt文件的文件名（不包含扩展名）
    
    Returns:
        list[str]: 文件名列表
    """
    file_names = []
    for filename in os.listdir("inputs"):
        if filename.endswith('.txt'):
            file_names.append(filename[:-4])
    return file_names

def get_source_text(file_name: str) -> str:
    """
    从inputs文件夹中读取指定的txt文件内容
    
    Args:
        file_name: 文件名（不包含.txt扩展名）
    Returns:
        str: 文件内容
    """
    with open(f"inputs/{file_name}.txt", 'r', encoding='utf-8') as file:
        return file.read()

async def interpret_source_text(source_text: str) -> str:
    """
    解读文章
    Args:
        source_text (str): 文章内容
    Returns:
        str: 对文章内容的解读
    """
    system_message = get_prompt('a_interpret_source_text')
    user_message = f"<source_text>\n{source_text}\n</source_text>"
    for attempt in range(3):
        try:
            llm_result = await call_llm(system_message, user_message, "deepseek/deepseek-chat-v3-0324", 0.1, 0.5, 0, 0)
            if interpretation := json.loads(extract_with_xml(llm_result, "interpretation")):
                published_date = replace_year_with_2025(interpretation.pop("新闻文章发布日期"))
                opinion_or_requirement = interpretation.pop("分析师的观点或分析要求")    
                return json.dumps(interpretation, ensure_ascii=False, indent=4), published_date, opinion_or_requirement
        except Exception:
            pass
    return None, None, None

async def draft_fact_paragraph(source_text: str, interpretation: str) -> str:
    """
    生成文章的事实段落
    Args:
        source_text (str): 文章内容
        interpretation (str): 对文章内容的解读
    Returns:
        str: 事实段落
    """
    system_message = get_prompt('b_draft_fact_paragraph')
    user_message = f"<source_text>\n{source_text}\n</source_text>\n<interpretation>\n{interpretation}\n</interpretation>"
    for attempt in range(3):
        try:
            llm_result = await call_llm(system_message, user_message, "deepseek/deepseek-chat-v3-0324", 0.3, 0.95, 0, 0)
            if fact_paragraph := extract_with_xml(llm_result, "fact_paragraph"):
                return fact_paragraph.replace('\n', '')
        except Exception:
            pass

async def review_fact_paragraph(source_text: str, fact_paragraph: str) -> str | None:
    """
    校对文章的事实段落
    Args:
        source_text (str): 文章内容
        fact_paragraph (str): 事实段落
    Returns:
        str | None: 如果需要修正则返回对事实段落的反馈，否则返回None
    """
    system_message = get_prompt('c_review_fact_paragraph')
    user_message = f"<source_text>\n{source_text}\n</source_text>\n<fact_paragraph>\n{fact_paragraph}\n</fact_paragraph>"
    for attempt in range(3):
        try:
            llm_result = await call_llm(system_message, user_message, "deepseek/deepseek-chat-v3-0324", 0.3, 0.95, 0, 0)
            feedback_on_fact_paragraph, corrections_required = extract_with_xml(llm_result, ["feedback_on_fact_paragraph", "corrections_required"])
            if feedback_on_fact_paragraph and corrections_required:
                if "True" in corrections_required or "true" in corrections_required:
                    return feedback_on_fact_paragraph
                else:
                    return None
        except Exception:
            pass
    return None

async def review_fact_sentences(source_text: str, fact_paragraph: str) -> str | None:
    """
    校对文章的事实句子
    Args:
        source_text (str): 文章内容
        fact_paragraph (str): 事实段落
    Returns:
        str | None: 如果需要修正则返回对事实句子的反馈，否则返回None
    """
    system_message = get_prompt('d_review_fact_sentences')
    user_message = f"<source_text>\n{source_text}\n</source_text>\n<fact_sentences>\n{split_to_sentences(fact_paragraph)}\n</fact_sentences>"
    for attempt in range(3):
        try:
            llm_result = await call_llm(system_message, user_message, "deepseek/deepseek-chat-v3-0324", 0.3, 0.95, 0, 0)
            feedback_on_fact_sentences, corrections_required = extract_with_xml(llm_result, ["feedback_on_fact_sentences", "corrections_required"])
            if feedback_on_fact_sentences and corrections_required:
                if "True" in corrections_required or "true" in corrections_required:
                    return feedback_on_fact_sentences
                else:
                    return None
        except Exception:
            pass
    return None

async def refine_fact_paragraph(fact_paragraph: str, feedback_on_fact_paragraph: str | None, feedback_on_fact_sentences: str | None) -> str:
    """
    修改文章的事实段落
    Args:
        fact_paragraph (str): 事实段落
        feedback_on_fact_paragraph (str): 对事实段落的反馈
        feedback_on_fact_sentences (str): 对事实句子的反馈
    Returns:                    
        str: 修改后的段落，如果无需修改则返回None
    """
    if not feedback_on_fact_paragraph and not feedback_on_fact_sentences:
        return None
    system_message = get_prompt('e_refine_fact_paragraph')
    user_message = f"<fact_paragraph>\n{fact_paragraph}\n</fact_paragraph>" + (f"\n<feedback_on_fact_paragraph>\n{feedback_on_fact_paragraph}\n</feedback_on_fact_paragraph>" if feedback_on_fact_paragraph else "") + (f"\n<feedback_on_fact_sentences>\n{feedback_on_fact_sentences}\n</feedback_on_fact_sentences>" if feedback_on_fact_sentences else "")
    for attempt in range(3):
        try:
            llm_result = await call_llm(system_message, user_message, "deepseek/deepseek-chat-v3-0324", 0.1, 0.5, 0, 0)
            if refined_fact_paragraph := extract_with_xml(llm_result, "refined_fact_paragraph"):
                return refined_fact_paragraph
        except Exception:
            pass
    return None

async def draft_and_refine_fact_paragraph(source_text: str, interpretation: str) -> str:
    """
    通过“撰写-校对-修改”的循环来创建并完善事实段落。
    该函数首先生成一个事实段落草稿，然后反复进行校对和修改，
    直到校对反馈表明无需任何修改为止。
    Args:
        source_text (str): 原始文章内容。
        interpretation (str): 对原始文章的解读。
    Returns:
        str: 最终完善后的事实段落。
    """
    fact_paragraph = await draft_fact_paragraph(source_text, interpretation)
    while True:
        feedback_on_fact_paragraph, feedback_on_fact_sentences = await asyncio.gather(review_fact_paragraph(source_text, fact_paragraph), review_fact_sentences(source_text, fact_paragraph))
        refined_fact_paragraph = await refine_fact_paragraph(fact_paragraph, feedback_on_fact_paragraph, feedback_on_fact_sentences)
        if refined_fact_paragraph is None:
            print("事实段落校对完成，无需进一步修改。")
            return fact_paragraph
        else:
            print("事实段落已根据反馈进行修改，将进行新一轮校对...")
            fact_paragraph = refined_fact_paragraph

async def draft_opinion_sentences(fact_paragraph: str, source_text: str) -> str:
    """
    生成文章的观点句子
    Args:
        fact_paragraph (str): 事实段落
        source_text (str): 文章内容
    Returns:
        str: 观点句子
    """
    system_message = get_prompt('f_draft_opinion_sentences')
    user_message = f"<fact_paragraph>\n{fact_paragraph}\n</fact_paragraph>\n<source_text>\n{source_text}\n</source_text>"
    for attempt in range(3):
        try:
            llm_result = await call_llm(system_message, user_message, "deepseek/deepseek-chat-v3-0324", 0.6, 0.95, 0, 0.5)
            if opinion_sentences := extract_with_xml(llm_result, "opinion_sentences"):
                return opinion_sentences
        except Exception:
            pass

async def draft_brief_title(brief_content: str) -> str:
    """
    生成文章的标题
    Args:
        brief_content (str): 简报内容
    Returns:
        str: 标题
    """
    system_message = get_prompt('g_draft_brief_title')
    user_message = f"<brief_content>\n{brief_content}\n</brief_content>"
    for attempt in range(3):
        try:
            llm_result = await call_llm(system_message, user_message, "deepseek/deepseek-chat-v3-0324", 0.3, 0.95, 0, 0.5)
            if brief_title := extract_with_xml(llm_result, "brief_title"):
                return brief_title
        except Exception:
            pass

async def review_brief_title(brief_content: str, brief_title: str) -> str | None:
    """
    校对文章的标题
    Args:
        brief_content (str): 简报内容
        brief_title (str): 简报标题
    Returns:
        str | None: 如果需要修正则返回对标题的反馈，否则返回None
    """
    system_message = get_prompt('h_review_brief_title')
    user_message = f"<brief_content>\n{brief_content}\n</brief_content>\n<brief_title>\n{brief_title}\n</brief_title>"
    for attempt in range(3):
        try:
            llm_result = await call_llm(system_message, user_message, "deepseek/deepseek-chat-v3-0324", 0.3, 0.95, 0, 0)
            feedback_on_brief_title, corrections_required = extract_with_xml(llm_result, ["feedback_on_brief_title", "corrections_required"])
            if feedback_on_brief_title and corrections_required:
                if "True" in corrections_required or "true" in corrections_required:
                    if adjust_length_prompt := get_prompt('k_adjust_length', text=brief_title):
                        print(adjust_length_prompt)
                        return feedback_on_brief_title + adjust_length_prompt
                    else:
                        return feedback_on_brief_title
                else:
                    if adjust_length_prompt := get_prompt('k_adjust_length', text=brief_title):
                        print(adjust_length_prompt)
                        return adjust_length_prompt
                    else:
                        return None
        except Exception:
            pass
    return None

async def refine_brief_title(brief_title: str, feedback_on_brief_title: str | None) -> str | None:
    """
    修改文章的标题
    Args:
        brief_title (str): 标题
        feedback_on_brief_title (str | None): 对标题的反馈
    Returns:                    
        str | None: 修改后的标题，如果无需修改则返回None
    """
    if not feedback_on_brief_title:
        return None
    system_message = get_prompt('i_refine_brief_title')
    user_message = f"<brief_title>\n{brief_title}\n</brief_title>\n<feedback_on_brief_title>\n{feedback_on_brief_title}\n</feedback_on_brief_title>"
    for attempt in range(3):
        try:
            llm_result = await call_llm(system_message, user_message, "deepseek/deepseek-chat-v3-0324", 0.1, 0.5, 0, 0)
            if refined_brief_title := extract_with_xml(llm_result, "refined_brief_title"):
                return refined_brief_title
        except Exception:
            pass
    return None

async def draft_and_refine_brief_title(brief_content: str) -> str:
    """
    通过"撰写-校对-修改"的循环来创建并完善标题。
    该函数首先生成一个标题草稿，然后反复进行校对和修改，
    直到校对反馈表明无需任何修改为止。
    Args:
        brief_content (str): 最终的简报内容。
    Returns:
        str: 最终完善后的标题。
    """
    brief_title = await draft_brief_title(brief_content)
    while True:
        feedback_on_brief_title = await review_brief_title(brief_content, brief_title)
        refined_brief_title = await refine_brief_title(brief_title, feedback_on_brief_title)
        if refined_brief_title is None:
            print("标题校对完成，无需进一步修改。")
            return brief_title
        else:
            print("标题已根据反馈进行修改，将进行新一轮校对...")
            brief_title = refined_brief_title

async def get_new_article_keywords_and_tags(article: str) -> set:
    """
    从单篇文章内容中提取关键词和标签，返回去重的统一集合
    
    Args:
        article (str): 文章内容
    Returns:
        set: 去重的关键词集合
    """
    system_message = get_prompt('j_generate_article_keywords_and_tags')
    user_message = f"<article>\n{article}\n</article>"
    for attempt in range(5):
        try:
            llm_result = await call_local_llm(system_message, user_message, "phi4:latest", 0.1, 0.5, 0, 0)
            if keywords_and_tags := json.loads(extract_with_xml(llm_result, "keywords_and_tags")):
                return set(itertools.chain(
                    keywords_and_tags["political_and_economic_terms"],
                    keywords_and_tags["technical_terms"],
                    keywords_and_tags["other_abstract_concepts"],
                    keywords_and_tags["organizations"],
                    keywords_and_tags["persons"],
                    keywords_and_tags["cities_or_districts"],
                    keywords_and_tags["other_concrete_entities"],
                    keywords_and_tags["other_tags_of_topic_or_points"]
                ))
        except Exception:
            pass
    return set()

def get_all_articles_keywords_and_tags(file_name: str) -> list:
    """
    从CSV文件中提取关键词和标签数据
    
    Args:
        file_name (str): 文件名（包含.csv扩展名）
    Returns:
        list: 包含每行数据字典的列表
    """
    results = []
    with open(f"{file_name}.csv", 'r', encoding='utf-8') as file:
        for row in csv.DictReader(file):
            results.append({
                "DataID": row["DataID"],
                "political_and_economic_terms": ast.literal_eval(row["political_and_economic_terms"]),
                "technical_terms": ast.literal_eval(row["technical_terms"]),
                "other_abstract_concepts": ast.literal_eval(row["other_abstract_concepts"]),
                "organizations": ast.literal_eval(row["organizations"]),
                "persons": ast.literal_eval(row["persons"]),
                "cities_or_districts": ast.literal_eval(row["cities_or_districts"]),
                "other_concrete_entities": ast.literal_eval(row["other_concrete_entities"]),
                "other_tags_of_topic_or_points": ast.literal_eval(row["other_tags_of_topic_or_points"])
            })
    return results

def get_matched_articles(new_article_keywords_and_tags: set, all_articles_keywords_and_tags: list, file_name: str) -> list:
    """
    计算新文章关键词与所有文章关键词的匹配程度，并返回匹配文章的详细信息
    
    Args:
        new_article_keywords_and_tags (set): 新文章的关键词和标签集合
        all_articles_keywords_and_tags (list): 所有文章的关键词和标签字典列表
        file_name (str): 文件名（不包含.csv扩展名）
    
    Returns:
        list: 按匹配分数从高到低排序的字典列表，包含DataID、InfoTitle、InfoContent
    """
    weights = {
        "political_and_economic_terms": 1,
        "technical_terms": 1,
        "other_abstract_concepts": 1,
        "organizations": 1,
        "persons": 1,
        "cities_or_districts": 0.5,
        "other_concrete_entities": 1,
        "other_tags_of_topic_or_points": 0.5
    }
    id_and_score_tuples = [(article_keywords_and_tags["DataID"], sum(len(new_article_keywords_and_tags.intersection(set(article_keywords_and_tags[aspect]))) * weight for aspect, weight in weights.items())) for article_keywords_and_tags in all_articles_keywords_and_tags]
    id_to_score = {id: score for id, score in id_and_score_tuples if score > 0}
    results = []
    with open(f"{file_name}.csv", 'r', encoding='utf-8') as file:
        for row in csv.DictReader(file):
            if row["DataID"] in id_to_score:
                results.append({
                    "DataID": row["DataID"],
                    "InfoTitle": row["InfoTitle"],
                    "InfoContent": row["InfoContent"],
                    "score": id_to_score[row["DataID"]]
                })
    results.sort(key=lambda x: x["score"], reverse=True)
    return results

async def match_articles(article: str, file_name: str) -> list:
    """
    匹配文章函数，传入文章字符串，返回匹配的文章结果
    
    Args:
        article (str): 输入的文章内容
        file_name (str): 要匹配的CSV文件名（不包含.csv扩展名），默认为"每日经济每日金融1-10"
    
    Returns:
        list: 按匹配分数从高到低排序的字典列表，包含DataID、InfoTitle、InfoContent、score
    """
    # 步骤1: 从新文章中提取关键词和标签
    new_article_keywords_and_tags = await get_new_article_keywords_and_tags(article)
    # 步骤2: 获取所有文章的关键词和标签数据
    all_articles_keywords_and_tags = get_all_articles_keywords_and_tags(file_name)
    # 步骤3: 计算匹配度并返回结果
    matched_articles = get_matched_articles(new_article_keywords_and_tags, all_articles_keywords_and_tags, file_name)
    return matched_articles

async def translate_to_other_languages(brief_title: str, brief_content: str) -> tuple[str, str, str, str, str, str, str, str]:
    """
    翻译为其它语言
    Args:
        brief_title (str): 简报标题
        brief_content (str): 简报内容
    Returns:
        tuple: 其它语言的简报的标题和内容
    """
    system_message = get_prompt('l_translate_to_other_languages')
    user_message = f"<chinese_title>\n{brief_title}\n</chinese_title>\n<chinese_content>\n{brief_content}\n</chinese_content>"
    for attempt in range(3):
        try:
            llm_result = await call_llm(system_message, user_message, "deepseek/deepseek-chat-v3-0324", 0.1, 0.5, 0, 0)
            if brief_in_other_languages := extract_with_xml(llm_result, ["english_title", "english_content", "german_title", "german_content", "french_title", "french_content", "japanese_title", "japanese_content"]):
                return tuple(brief_in_other_languages)
        except Exception:
            pass

async def generate_briefs() -> None:
    """
    执行完整的并行简报生成工作流，处理inputs文件夹中的所有txt文件
    Returns:
        None
    """
    async def generate_brief(file_name: str) -> None:
        """
        处理单个文件的完整简报生成工作流
        Args:
            file_name (str): 输入文件名 (不包含.txt扩展名)
        Returns:
            None
        """
        print(f"开始处理文件: {file_name}")
        print(f"[{file_name}] 1/6: 读取并解读原文")
        source_text = get_source_text(file_name)
        interpretation, published_date, opinion_or_requirement = await interpret_source_text(source_text)
        
        # 检查解读结果
        if interpretation is None or published_date is None or opinion_or_requirement is None:
            print(f"[{file_name}] 错误: 文章解读失败，跳过处理")
            return
        
        interpretation = convert_to_date(interpretation, published_date)
        source_text = convert_to_cn_term(source_text)
        source_text = clean_stock_codes(source_text)
        source_text = convert_to_date(source_text, published_date)
        print(f"[{file_name}] 2/6: 创建并完善事实段落")
        fact_paragraph = await draft_and_refine_fact_paragraph(source_text, interpretation)
        
        # 检查事实段落
        if fact_paragraph is None:
            print(f"[{file_name}] 错误: 事实段落生成失败，跳过处理")
            return
        
        fact_paragraph = remove_year_at_start(fact_paragraph)
        print(f"[{file_name}] 3/6: 撰写观点句")
        opinion_sentences = await draft_opinion_sentences(fact_paragraph, f"{source_text}\n\n{opinion_or_requirement}")
        
        # 检查观点句子
        if opinion_sentences is None:
            print(f"[{file_name}] 警告: 观点句子生成失败，使用空字符串")
            opinion_sentences = ""
        
        print(f"[{file_name}] 4/6: 创建并完善标题")
        brief_content = f"{fact_paragraph}{opinion_sentences}"
        brief_title = await draft_and_refine_brief_title(brief_content)
        
        # 检查标题
        if brief_title is None:
            print(f"[{file_name}] 警告: 标题生成失败，使用默认标题")
            brief_title = "简报标题生成失败"
        
        save_as_txt(f"{brief_title}\n\n{brief_content}", file_name)
        """
        print(f"[{file_name}] 5/6: 匹配历史文章")
        matched_articles = "\n\n\n\n".join([f"{article['InfoTitle']}\n\n{article['InfoContent']}" for article in await match_articles(f"{brief_title}\n\n{brief_content}", "每日经济每日金融1-10")])
        save_as_txt(f"{brief_title}\n\n{brief_content}\n\n{matched_articles}", f"{file_name} with matched articles")
        print(f"[{file_name}] 6/6: 翻译为其它语言")
        english_title, english_content, german_title, german_content, french_title, french_content, japanese_title, japanese_content = await translate_to_other_languages(brief_title, brief_content)
        save_as_txt(f"{brief_title}\n\n{brief_content}\n\n{english_title}\n\n{english_content}\n\n{german_title}\n\n{german_content}\n\n{french_title}\n\n{french_content}\n\n{japanese_title}\n\n{japanese_content}\n\n{matched_articles}", file_name)
        """
    if file_names := get_source_files():
        print(f"发现 {len(file_names)} 个文件，开始并行处理: {file_names}")
        await asyncio.gather(*[generate_brief(file_name) for file_name in file_names])
        print(f"所有 {len(file_names)} 个文件处理完成")
    return None

def get_reference_text(file_name: str) -> list:
    """
    从根目录读取指定的csv文件，提取特定条件下的行数据
    
    Args:
        file_name: 文件名（不包含.csv扩展名）
    Returns:
        list: 包含(index, article_content)元组的列表，仅包含所有指定标签列都为"None"或为空的行
    """    
    with open(f"{file_name}.csv", 'r', encoding='utf-8') as file:
        return [
            (index, f"{row['InfoTitle']}\n{row['InfoContent']}")
            for index, row in enumerate(csv.DictReader(file))
            if all(row[column] == "None" or row[column] == "" for column in [
                "political_and_economic_terms",
                "technical_terms", 
                "other_abstract_concepts",
                "organizations",
                "persons",
                "cities_or_districts",
                "other_concrete_entities",
                "other_tags_of_topic_or_points"
            ])
        ]

async def generate_article_keywords_and_tags(article: str) -> dict:
    """
    从单篇文章内容中提取关键词和标签
    
    Args:
        article (str): 文章内容
    Returns:
        dict: 关键词和标签字典
    """
    system_message = get_prompt('j_generate_article_keywords_and_tags')
    user_message = f"<article>\n{article}\n</article>"
    for attempt in range(5):
        try:
            llm_result = await call_local_llm(system_message, user_message, "phi4:latest", 0.1, 0.5, 0, 0)
            if keywords_and_tags := json.loads(extract_with_xml(llm_result, "keywords_and_tags")):
                if all(key in keywords_and_tags for key in [
                    "political_and_economic_terms",
                    "technical_terms", 
                    "other_abstract_concepts",
                    "organizations",
                    "persons",
                    "cities_or_districts",
                    "other_concrete_entities",
                    "other_tags_of_topic_or_points"
                ]):
                    return keywords_and_tags
        except Exception:
            pass
    return {
        "political_and_economic_terms": "",
        "technical_terms": "",
        "other_abstract_concepts": "",
        "organizations": "",
        "persons": "",
        "cities_or_districts": "",
        "other_concrete_entities": "",
        "other_tags_of_topic_or_points": ""
    }

def article_keywords_and_tags_to_csv(index: int, article_keywords_and_tags: dict, file_name: str):
    """
    将单篇文章的关键词和标签数据写入csv文件的指定行
    
    Args:
        index: 文章在列表中的索引（从0开始）
        article_keywords_and_tags: 单篇文章的关键词和标签字典
        file_name: 文件名（不包含.csv扩展名）
    """
    df = pd.read_csv(f"{file_name}.csv")
    for column in ['organizations', 'persons', 'cities_or_districts', 'other_concrete_entities', 'political_and_economic_terms', 'technical_terms', 'other_abstract_concepts', 'other_tags_of_topic_or_points']:
        df[column] = df[column].astype(str)
        df.at[index, column] = str(article_keywords_and_tags[column])
    df.to_csv(f"{file_name}.csv", index=False, encoding='utf-8')

async def label_articles(file_name: str):
    """
    为文章打标签并保存到CSV文件
    
    Args:
        file_name (str): 文件名（不包含.csv扩展名）
    """
    index_article_tuples = get_reference_text(file_name)
    print(f"开始处理 {len(index_article_tuples)} 篇文章")
    for i, article in index_article_tuples:
        print(f"正在处理索引 {i} 的文章...")
        article_keywords_and_tags = await generate_article_keywords_and_tags(article)
        article_keywords_and_tags_to_csv(i, article_keywords_and_tags, file_name)
        print(f"索引 {i} 的文章处理完成并已保存")

if __name__ == "__main__":
    asyncio.run(generate_briefs())
    # asyncio.run(label_articles("测试数据/每日经济每日金融83001-83100"))
