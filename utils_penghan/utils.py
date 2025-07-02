import os
import re
import time
import requests
import json
from typing import Union, Dict, List
from dotenv import load_dotenv
load_dotenv()


def call_llm(prompt, model="deepseek/deepseek-chat-v3-0324", temperature=0.7, max_retries=3, retry_delay=1):
    """
    调用OpenRouter LLM的简化函数，支持重试机制和温度参数
    
    Args:
        prompt (str): 用户提示词
        model (str): 模型名称，默认为deepseek/deepseek-chat-v3-0324
        temperature (float): 温度参数，控制输出的随机性，范围0-2，默认0.7
        max_retries (int): 最大重试次数，默认3次
        retry_delay (float): 重试间隔时间（秒），默认1秒
    
    Returns:
        str: LLM的回复内容
    """
    api_key = os.getenv('OPENROUTER_API_KEY')
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature
    }
    
    # 重试机制
    for attempt in range(max_retries + 1):
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            elif response.status_code == 429:  # 速率限制
                if attempt < max_retries:
                    wait_time = retry_delay * (2 ** attempt)  # 指数退避
                    print(f"遇到速率限制，等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                    continue
            elif response.status_code >= 500:  # 服务器错误
                if attempt < max_retries:
                    wait_time = retry_delay * (2 ** attempt)
                    print(f"服务器错误，等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                    continue
            
            # 其他错误直接抛出
            raise Exception(f"API调用失败: {response.status_code} - {response.text}")
            
        except requests.exceptions.RequestException as e:
            if attempt < max_retries:
                wait_time = retry_delay * (2 ** attempt)
                print(f"网络错误，等待 {wait_time} 秒后重试: {e}")
                time.sleep(wait_time)
                continue
            else:
                raise Exception(f"网络请求失败: {e}")
    
    raise Exception(f"重试 {max_retries} 次后仍然失败")


def get_prompt(file_path: str) -> str:
    """
    从文件中读取提示内容
    
    Args:
        file_path (str): 包含提示的文件路径
    
    Returns:
        str: 从文件中读取的提示内容
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read().strip()



def parse_json(llm_output: str) -> Union[Dict, List]:
    """
    清理LLM输出的JSON字符串，返回纯净的Python字典或列表
    
    参数:
        llm_output: LLM输出的可能包含JSON的字符串
        
    返回:
        解析后的Python字典或列表
        
    异常:
        ValueError: 当无法提取有效JSON时抛出
    """
    # 常见预处理步骤
    cleaned = llm_output.strip()
    
    # 情况1：输出直接是JSON字符串（可能被Markdown代码块包裹）
    json_patterns = [
        r'```(?:json)?\n?(.*?)\n```',  # 匹配Markdown代码块
        r'\{(.*)\}',                    # 匹配花括号内容
        r'\[(.*)\]'                     # 匹配方括号内容
    ]
    
    for pattern in json_patterns:
        match = re.search(pattern, cleaned, re.DOTALL)
        if match:
            try:
                # 提取最可能JSON部分
                json_str = match.group(1) if match.groups() else match.group(0)
                return json.loads(json_str)
            except json.JSONDecodeError:
                continue
    
    # 情况2：输出是纯JSON但没有代码块标记
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    
    # 情况3：输出包含JSON但可能有其他文本
    # 尝试找到最长的可能JSON子串
    json_candidates = []
    for start in ['{', '[']:
        for end in ['}', ']']:
            start_idx = cleaned.find(start)
            end_idx = cleaned.rfind(end)
            if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
                candidate = cleaned[start_idx:end_idx+1]
                try:
                    parsed = json.loads(candidate)
                    json_candidates.append((len(candidate), parsed))
                except json.JSONDecodeError:
                    continue
    
    if json_candidates:
        # 返回最长的有效JSON
        return max(json_candidates, key=lambda x: x[0])[1]
    
    # 如果所有尝试都失败
    raise ValueError("无法从LLM输出中提取有效的JSON内容")


def extract_xml_content(text: str, tag_name: str) -> str:
    """
    从文本中提取指定XML标签的内容
    
    参数:
        text: 包含XML标签的文本
        tag_name: 要提取的XML标签名称
        
    返回:
        提取到的纯净字符串内容，如果未找到则返回空字符串
    """
    # 构建正则表达式模式，匹配开始和结束标签
    pattern = re.compile(rf'<{tag_name}>(.*?)</{tag_name}>', re.DOTALL)
    
    # 搜索匹配的内容
    match = pattern.search(text)
    
    if match:
        # 返回匹配到的内容，去除前后空白
        return match.group(1).strip()
    return ""



def save_json_to_file(data, file_path, ensure_ascii=False, indent=2):
    """
    统一的JSON文件保存函数
    
    Args:
        data: 要保存的数据
        file_path: 文件路径
        ensure_ascii: 是否确保ASCII编码，默认False
        indent: 缩进空格数，默认2
    """
    # 确保目录存在
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=ensure_ascii, indent=indent)
    
    print(f"数据已保存到: {file_path}")


def save_text_to_file(text, file_path):
    """
    统一的文本文件保存函数
    
    Args:
        text: 要保存的文本内容
        file_path: 文件路径
    """
    # 确保目录存在
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(text)
    
    print(f"文本已保存到: {file_path}")


def count_chars(text):
    """
    统计字符数
    :param text: 输入字符串
    :return: 字符数量统计字典
    """
    # 使用Unicode编码表示中文标点
    chinese_punct = (
        "\uFF02\uFF03\uFF04\uFF05\uFF06\uFF07\uFF08\uFF09\uFF0A\uFF0B\uFF0C"
        "\uFF0D\uFF0F\uFF1A\uFF1B\uFF1C\uFF1D\uFF1E\uFF20\uFF3B\uFF3C\uFF3D"
        "\uFF3E\uFF3F\uFF40\uFF5B\uFF5C\uFF5D\uFF5E\uFF5F\uFF60\u3000\u3001"
        "\u3002\u3008\u3009\u300A\u300B\u300C\u300D\u300E\u300F\u3010\u3011"
        "\u3014\u3015\u3016\u3017\u3018\u3019\u301A\u301B\u301C\u301D\u301E"
        "\u301F\u3030\u2013\u2014\u2018\u2019\u201C\u201D\u2026\u2027\uFE4F"
        "\uFE50\uFE51\uFE52\uFF01\uFF1F"
    )
    
    # 英文标点使用ASCII表示
    english_punct = "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"
    
    # 统计中文字符（Unicode范围：4E00-9FFF）
    chinese_chars = re.findall(r"[\u4e00-\u9fa5]", text)
    
    # 统计英文单词（按空格分隔）
    english_words = re.findall(r"[a-zA-Z]+", text)
    
    # 修改：统计数字和百分比为单个单位
    # 匹配百分比（如：54.8%、100%、0.5%）
    percentages = re.findall(r"\d+(?:\.\d+)?%", text)
    
    # 匹配小数（如：54.8、100.0、0.5）- 排除已匹配的百分比
    temp_text = text
    for percentage in percentages:
        temp_text = temp_text.replace(percentage, "", 1)
    decimals = re.findall(r"\d+\.\d+", temp_text)
    
    # 匹配整数（排除已匹配的百分比和小数）
    for decimal in decimals:
        temp_text = temp_text.replace(decimal, "", 1)
    integers = re.findall(r"\d+", temp_text)
    
    # 统计标点符号（排除百分号，因为已在百分比中计算）
    temp_text_for_punct = text
    for percentage in percentages:
        temp_text_for_punct = temp_text_for_punct.replace(percentage, "", 1)
    punct_chars = re.findall(f"[{chinese_punct + english_punct}]", temp_text_for_punct)
    
    # 返回总字符数：中文字符 + 英文单词 + 百分比 + 小数 + 整数 + 标点符号
    total_count = (
        len(chinese_chars) + 
        len(english_words) + 
        len(percentages) + 
        len(decimals) + 
        len(integers) + 
        len(punct_chars)
    )
    
    return total_count


def split_sentences(text: str) -> list:
    """
    通过句号和换行符拆分文本为句子列表
    
    参数:
        text: 要拆分的文本
        
    返回:
        拆分后的句子列表，去除空字符串
    """
    # 使用正则表达式匹配一个或多个句号或换行符作为分隔符
    sentences = re.split(r'[。？！!?\n]+', text)
    
    # 去除空字符串并返回
    return [s.strip() for s in sentences if s.strip()]




# 使用示例
if __name__ == "__main__":
    result=split_sentences("这是第一句话!这是第二句话\n\n这是第三句话。这是第四句话")
    print(result)

