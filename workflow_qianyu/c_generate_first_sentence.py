import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils_penghan.utils import call_llm

def generate_first_sentence(
        source_article: str,
        interpretation: str) -> str:
    """
    生成引人入胜的文章开篇句（实际调用大模型API的过程省略）

    参数:
        source_article (str): 原始文章内容
        interpretation (str): 文章解读结果

    返回:
        result (str): 生成的1-2句开篇段落（包含<START>标记）
    """
    # 读取 first_generation_draft.py 中的提示词
    with open('prompt_panlin/first_generation_draft.py', 'r', encoding='utf-8') as f:
        prompt_content = f.read()
    
    # 提取 prompt_content 变量中的内容
    # 假设提示词存储在 prompt_content 变量中
    import re
    prompt_match = re.search(r'prompt_content = """(.*?)"""', prompt_content, re.DOTALL)
    if prompt_match:
        system_prompt = prompt_match.group(1)
    else:
        # 如果无法提取，使用默认提示词
        system_prompt = "请根据提供的信源文章和解读结果，生成简报的引言部分。"
    
    # 构造用户输入，将原文和解读结果结合
    user_prompt = f"信源文章：{source_article}\n\n解读结果：{interpretation}"
    
    # 调用大模型
    result = call_llm(f"{system_prompt}\n\n{user_prompt}")
    
    # 对result做一些字符串的处理
    # 这里可以添加XML标签提取或其他处理逻辑
    
    return result


# 使用示例
if __name__ == "__main__":
    # 读取测试数据
    with open('inputs/source_article', 'r', encoding='utf-8') as f:
        source_article = f.read()
    
    with open('processes/processed_text/article_interpretation', 'r', encoding='utf-8') as f:
        interpretation = f.read()
    
    result = generate_first_sentence(source_article, interpretation)
    
    # 保存结果到文件
    output_path = 'processes/first_sentence.txt'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(result)
    
    print(f"结果已保存到: {output_path}")
    print("\n生成的内容:")
    print(result)
