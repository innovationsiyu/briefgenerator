def generate_title(
        system_prompt: str,
        interpretation: str,
        first_sentence: str,
        fact_paragraph: str,
        opinion_sentence: str,
) -> str:
    # return

    # 使用示例
    if __name__ == "__main__":
        generate_title("system_prompt", "interpretation", "first_sentence", "fact_paragraph", "opinion_sentence")


def check_title(
        title: str,
        interpretation: str,
        first_sentence: str,
        fact_paragraph: str,
        opinion_sentence: str) -> dict:
    """
    调用LLM检查标题

    参数:
        title (str): 待检查的标题
        interpretation (str): 原文解读
        first_sentence (str): 第一句话
        fact_paragraph (str): 事实部分
        opinion_sentence (str): 观点部分

    返回:
        dict: 检查结果，包含是否通过和问题描述
    """
    system_prompt = get_system_prompt("检查简报标题内容的提示词")
    user_prompt = f"标题：{title}\n解读：{interpretation}\n第一句话：{first_sentence}\n事实部分：{fact_paragraph}\n观点部分：{opinion_sentence}"
    result = call_llm(system_prompt, user_prompt)
    check_result = parse_json(result)
    return check_result


def correct_title(
        title: str,
        check_result: dict,
        interpretation: str,
        first_sentence: str,
        fact_paragraph: str,
        opinion_sentence: str) -> str:
    """
    调用LLM修正标题

    参数:
        title (str): 原始标题
        check_result (dict): 检查结果
        interpretation (str): 原文解读
        first_sentence (str): 第一句话
        fact_paragraph (str): 事实部分
        opinion_sentence (str): 观点部分

    返回:
        str: 修正后的标题
    """
    system_prompt = get_system_prompt("修正简报标题的提示词")
    user_prompt = f"原始标题：{title}\n检查结果：{check_result}\n解读：{interpretation}\n第一句话：{first_sentence}\n事实部分：{fact_paragraph}\n观点部分：{opinion_sentence}"
    result = call_llm(system_prompt, user_prompt)
    corrected_title = extract_from_xml("title", result)
    return corrected_title