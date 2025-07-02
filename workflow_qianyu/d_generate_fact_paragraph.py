from utils_penghan.utils import call_llm
import os

def generate_fact_paragraph(source_article: str, interpretation: str, first_sentence: str) -> str:
    # 读取 fact_paragraph_draft.py 中的提示词
    with open('prompt_panlin/fact_generation_draft.py', 'r', encoding='utf-8') as f:
        prompt_content = f.read()

    # 构造用户输入
    user_prompt = f"信源文章：{source_article}\n\n解读结果：{interpretation}\n\n开篇句：{first_sentence}"

    # 系统提示词直接写死
    # system_prompt = "请生成事实段落："

    # 调用大模型
    result = call_llm(f"{prompt_content}\n\n{user_prompt}")

    # 用xml标签包裹结果
    xml_result = f"<fact_paragraph>\n{result}\n</fact_paragraph>"

    # 保存到文件
    output_path = os.path.join('processes', 'fact_paragraph_draft')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(xml_result)

    return xml_result

if __name__ == "__main__":
    # 读取输入文件
    with open('inputs/source_article', 'r', encoding='utf-8') as f:
        source_article = f.read()
    with open('processes/processed_text/article_interpretation', 'r', encoding='utf-8') as f:
        interpretation = f.read()
    with open('processes/first_sentence.txt', 'r', encoding='utf-8') as f:
        first_sentence = f.read()

    result = generate_fact_paragraph(source_article, interpretation, first_sentence)
    print(result)
