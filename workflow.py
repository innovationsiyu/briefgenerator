# workflow.py

import asyncio
import json
from utils import convert_to_cn_term, convert_to_date, clean_stock_codes, get_prompt, call_llm, extract_with_xml, split_to_sentences, save_as_txt, remove_year_at_start


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
        llm_result = await call_llm(system_message, user_message)
        if interpretation := extract_with_xml(llm_result, "interpretation"):
            data = json.loads(interpretation)
            published_date = data.pop("新闻文章发布日期")
            opinion_or_requirement = data.pop("分析师的观点或分析要求")    
            return json.dumps(data, ensure_ascii=False, indent=4), published_date, opinion_or_requirement

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
        llm_result = await call_llm(system_message, user_message)
        if fact_paragraph := extract_with_xml(llm_result, "fact_paragraph"):
            return fact_paragraph

async def review_fact_paragraph(source_text: str, fact_paragraph: str) -> str:
    """
    校对文章的事实段落
    Args:
        source_text (str): 文章内容
        fact_paragraph (str): 事实段落
    Returns:
        str: 对事实段落的反馈
    """
    system_message = get_prompt('c_review_fact_paragraph')
    user_message = f"<source_text>\n{source_text}\n</source_text>\n<fact_paragraph>\n{fact_paragraph}\n</fact_paragraph>"
    for attempt in range(3):
        llm_result = await call_llm(system_message, user_message)
        if feedback_on_fact_paragraph := extract_with_xml(llm_result, "feedback_on_fact_paragraph"):
            return feedback_on_fact_paragraph

async def review_fact_sentences(source_text: str, fact_paragraph: str) -> str:
    """
    校对文章的事实句子
    Args:
        source_text (str): 文章内容
        fact_paragraph (str): 事实段落
    Returns:
        str: 对事实句子的反馈
    """
    system_message = get_prompt('d_review_fact_sentences')
    user_message = f"<source_text>\n{source_text}\n</source_text>\n<fact_sentences>\n{split_to_sentences(fact_paragraph)}\n</fact_sentences>"
    for attempt in range(3):
        llm_result = await call_llm(system_message, user_message)
        if feedback_on_fact_sentences := extract_with_xml(llm_result, "feedback_on_fact_sentences"):
            return feedback_on_fact_sentences

async def refine_fact_paragraph(fact_paragraph: str, feedback_on_fact_paragraph: str, feedback_on_fact_sentences: str) -> str:
    """
    修改文章的事实段落
    Args:
        fact_paragraph (str): 事实段落
        feedback_on_fact_paragraph (str): 对事实段落的反馈
        feedback_on_fact_sentences (str): 对事实句子的反馈
    Returns:                    
        str: 修改后的段落，如果无需修改则返回None
    """
    if "无需任何修改" in feedback_on_fact_paragraph and "无需任何修改" in feedback_on_fact_sentences:
        return None
    system_message = get_prompt('e_refine_fact_paragraph')
    user_message = f"<fact_paragraph>\n{fact_paragraph}\n</fact_paragraph>" + (f"\n<feedback_on_fact_paragraph>\n{feedback_on_fact_paragraph}\n</feedback_on_fact_paragraph>" if "无需任何修改" not in feedback_on_fact_paragraph else "") + (f"\n<feedback_on_fact_sentences>\n{feedback_on_fact_sentences}\n</feedback_on_fact_sentences>" if "无需任何修改" not in feedback_on_fact_sentences else "")
    for attempt in range(3):
        llm_result = await call_llm(system_message, user_message)
        if refined_fact_paragraph := extract_with_xml(llm_result, "refined_fact_paragraph"):
            return refined_fact_paragraph

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
        llm_result = await call_llm(system_message, user_message)
        if opinion_sentences := extract_with_xml(llm_result, "opinion_sentences"):
            return opinion_sentences

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
        llm_result = await call_llm(system_message, user_message, "google/gemini-2.5-flash")
        if brief_title := extract_with_xml(llm_result, "brief_title"):
            return brief_title

async def review_brief_title(brief_content: str, brief_title: str) -> str:
    """
    校对文章的标题
    Args:
        brief_content (str): 简报内容
        brief_title (str): 简报标题
    Returns:
        str: 对标题的反馈
    """
    system_message = get_prompt('h_review_brief_title')
    user_message = f"<brief_content>\n{brief_content}\n</brief_content>\n<brief_title>\n{brief_title}\n</brief_title>"
    for attempt in range(3):
        llm_result = await call_llm(system_message, user_message)
        if feedback_on_brief_title := extract_with_xml(llm_result, "feedback_on_brief_title"):
            return feedback_on_brief_title

async def refine_brief_title(brief_title: str, feedback_on_brief_title: str) -> str:
    """
    修改文章的标题
    Args:
        brief_title (str): 标题
        feedback_on_brief_title (str): 对标题的反馈
    Returns:                    
        str: 修改后的标题，如果无需修改则返回None
    """
    if "无需任何修改" in feedback_on_brief_title:
        return None
    system_message = get_prompt('i_refine_brief_title')
    user_message = f"<brief_title>\n{brief_title}\n</brief_title>\n<feedback_on_brief_title>\n{feedback_on_brief_title}\n</feedback_on_brief_title>"
    for attempt in range(3):
        llm_result = await call_llm(system_message, user_message)
        if refined_brief_title := extract_with_xml(llm_result, "refined_brief_title"):
            return refined_brief_title

async def draft_and_refine_brief_title(brief_content: str) -> str:
    """
    通过“撰写-校对-修改”的循环来创建并完善标题。
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
        llm_result = await call_llm(system_message, user_message)
        if brief_in_other_languages := extract_with_xml(llm_result, ["english_title", "english_content", "german_title", "german_content", "french_title", "french_content", "japanese_title", "japanese_content"]):
            return tuple(brief_in_other_languages)

async def generate_brief(file_name: str) -> tuple[str, str]:
    """
    执行完整的简报生成工作流，并将结果保存到文件。
    Args:
        file_name (str): 输入文件名 (不包含.txt扩展名)。
    Returns:
        tuple[str, str]: 一个包含标题和简报正文的元组。
    """
    print("1/6: 读取并解读原文")
    source_text = get_source_text(file_name)
    interpretation, published_date, opinion_or_requirement = await interpret_source_text(source_text)
    interpretation = convert_to_date(interpretation, published_date)
    source_text = convert_to_cn_term(source_text)
    source_text = clean_stock_codes(source_text)
    source_text = convert_to_date(source_text, published_date)
    print("2/6: 创建并完善事实段落")
    fact_paragraph = await draft_and_refine_fact_paragraph(source_text, interpretation)
    fact_paragraph = remove_year_at_start(fact_paragraph)
    print("3/6: 撰写观点句")
    source_text = f"{source_text}\n{opinion_or_requirement}"
    opinion_sentences = await draft_opinion_sentences(fact_paragraph, source_text)
    print("4/6: 创建并完善标题")
    brief_content = f"{fact_paragraph}{opinion_sentences}"
    brief_title = await draft_and_refine_brief_title(brief_content)
    print("5/6: 翻译为其它语言")
    brief_title_in_english, brief_content_in_english, brief_title_in_german, brief_content_in_german, brief_title_in_french, brief_content_in_french, brief_title_in_japanese, brief_content_in_japanese = await translate_to_other_languages(brief_title, brief_content)
    print("--- 简报生成完毕 ---")
    save_as_txt(f"{brief_title}\n\n{brief_content}\n\n{brief_title_in_english}\n\n{brief_content_in_english}\n\n{brief_title_in_german}\n\n{brief_content_in_german}\n\n{brief_title_in_french}\n\n{brief_content_in_french}\n\n{brief_title_in_japanese}\n\n{brief_content_in_japanese})", file_name)
    return brief_title, brief_content

if __name__ == "__main__":    
    file_name = "1"
    asyncio.run(generate_brief(file_name))
