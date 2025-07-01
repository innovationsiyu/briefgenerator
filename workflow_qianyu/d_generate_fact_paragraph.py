def generate_fact_paragraph(
        system_prompt: str,
        source_article: str,
        interpretation: str,
        first_sentence: str) -> str:
    # return

    # 使用示例
    if __name__ == "__main__":
        generate_fact_paragraph("system_prompt", "source_article", "interpretation", "first_sentence")


def check_fact_paragraph(
        fact_paragraph: str,
        source_article: str,
        interpretation: str,
        first_sentence: str) -> dict:
    """
    调用LLM检查事实部分

    参数:
        fact_paragraph (str): 事实部分内容
        source_article (str): 原文内容
        interpretation (str): 原文解读
        first_sentence (str): 第一段内容

    返回:
        dict: 检查结果，包含是否通过和问题描述
    """
    system_prompt = get_system_prompt("检查事实部分内容的提示词")
    user_prompt = f"事实部分：{fact_paragraph}\n原文：{source_article}\n解读：{interpretation}\n第一句话：{first_sentence}"
    result = call_llm(system_prompt, user_prompt)
    check_result = parse_json(result)
    return check_result

def correct_fact_paragraph(
        fact_paragraph: str,
        check_result: dict,
        source_article: str,
        interpretation: str,
        first_sentence: str,
        mode: str = "normal") -> str:
    """
    调用LLM修正事实部分（mode可选：normal/expand/shorten）

    参数:
        fact_paragraph (str): 原始事实部分内容
        check_result (dict): 检查结果
        source_article (str): 原文内容
        interpretation (str): 原文解读
        first_sentence (str): 第一段内容
        mode (str): 修正模式，normal为常规，expand为扩展字数，shorten为精简字数

    返回:
        str: 修正后的事实部分内容
    """
    prompt_map = {
        "normal": "修正事实部分的提示词",
        "expand": "生成事实部分（扩展字数版）的提示词",
        "shorten": "生成事实部分（精简字数版）的提示词"
    }
    system_prompt = get_system_prompt(prompt_map.get(mode, "修正事实部分的提示词"))
    user_prompt = f"原始事实部分：{fact_paragraph}\n检查结果：{check_result}\n原文：{source_article}\n解读：{interpretation}\n第一句话：{first_sentence}"
    result = call_llm(system_prompt, user_prompt)
    corrected_paragraph = extract_from_xml("fact_paragraph", result)
    return corrected_paragraph