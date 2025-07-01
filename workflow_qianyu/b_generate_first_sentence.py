from utils_penghan.utils import call_llm, get_system_prompt

def generate_first_sentence(
        source_article: str,
        interpretation: str) -> str:
    """
    生成引人入胜的文章开篇句（实际调用大模型API的过程省略）

    参数:
        system_prompt (str): 定义写作风格和目标的系统提示
        user_prompt   (str): 包含文章主题和具体要求的内容

    返回:
        result (str): 生成的1-2句开篇段落（包含<START>标记）
    """
    # source_article字符串与解析后的interpretation字符串结合在一起得到user_prompt
    system_prompt = get_system_prompt("生成第一句话的提示词")
    result = call_llm(system_prompt, user_prompt)
    first_sentence = extract_from_xml("first_sentence", result)
    # 对result做一些字符串的处理
    # return


# 使用示例
if __name__ == "__main__":
    generate_first_sentence("system_prompt", "source_article", "interpretation")


def check_first_sentence(
        first_sentence: str,
        source_article: str,
        interpretation: str) -> dict:
    """
    调用LLM检查第一句话
    
    参数:
        first_sentence (str): 待检查的第一句话
        source_article (str): 原文内容
        interpretation (str): 原文解读
        
    返回:
        dict: 检查结果，包含是否通过和问题描述
    """
    system_prompt = get_system_prompt("检查第一句话的提示词")
    user_prompt = f"第一句话：{first_sentence}\n原文：{source_article}\n解读：{interpretation}"
    result = call_llm(system_prompt, user_prompt)
    check_result = parse_json(result)
    return check_result


def correct_first_sentence(
        first_sentence: str,
        check_result: dict,
        source_article: str,
        interpretation: str) -> str:
    """
    调用LLM修正第一句话
    
    参数:
        first_sentence (str): 原始第一句话
        check_result (dict): 检查结果
        source_article (str): 原文内容
        interpretation (str): 原文解读
        
    返回:
        str: 修正后的第一句话
    """
    system_prompt = get_system_prompt("修正第一句话的提示词")
    user_prompt = f"原始句子：{first_sentence}\n检查结果：{check_result}\n原文：{source_article}\n解读：{interpretation}"
    result = call_llm(system_prompt, user_prompt)
    corrected_sentence = extract_from_xml("corrected_sentence", result)