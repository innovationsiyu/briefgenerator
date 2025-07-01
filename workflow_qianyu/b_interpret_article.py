import os
os.environ["OPENROUTER_API_KEY"] = "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"
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def interpret_article(
        system_prompt: str,
        processed_text: str) -> str:
    """

    参数:
        system_prompt (str): 系统级提示词，定义模型的角色和任务要求
        processed_text (str): 处理后的新闻文本

    返回:
        article_interpretation: 模型生成的解读结果文本（json字符串）
    """
    from utils_penghan.utils import call_llm

    # 读取 interpret_text.py 中的提示词
    with open('prompt_panlin/interpret_text.py', 'r', encoding='utf-8') as f:
        prompt_content = f.read()

    # 构造大模型输入
    llm_input = f"{system_prompt}\n{prompt_content}\n{processed_text}"

    # 调用大模型
    article_interpretation = call_llm(llm_input)

    # 以json格式封装输出
    output_json = json.dumps({"article_interpretation": article_interpretation}, ensure_ascii=False)

    # 输出到指定文件
    output_path = 'processes/processed_text/article_interpretation'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output_json)

    return output_json

if __name__ == "__main__":
    # 读取处理后的新闻文本
    with open('processes/processed_text.txt', 'r', encoding='utf-8') as f:
        processed_text = f.read()

    # 假设有一个系统提示词
    system_prompt = "请解读以下新闻内容："

    # 调用解读函数
    result_json = interpret_article(system_prompt, processed_text)
    print(result_json)  # 可选：打印到终端
