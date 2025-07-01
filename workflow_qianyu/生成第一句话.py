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