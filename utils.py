import aiohttp
import os
import re
import time
import requests
import random
from typing import Optional, Dict, Any, Union, List
import importlib
import json

OPENROUTER_API_KEY = "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"

async def call_llm(system_message: str, user_message: str, model="mistralai/mistral-small-3.2-24b-instruct:free", temperature=0.5, top_p=0.95, frequency_penalty=0, presence_penalty=0) -> Optional[str]:
    api_key = OPENROUTER_API_KEY
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
    }
    data = {
        "messages": [{"role": "system", "content": system_message}, {"role": "user", "content": user_message}],
        "model": model,
        "max_tokens": 8192,
        "temperature": temperature,
        "top_p": top_p,
        "frequency_penalty": frequency_penalty,
        "presence_penalty": presence_penalty
    }
    async with aiohttp.ClientSession() as session:
        for attempt in range(3):
            try:
                print(f"Sending request to {url} with {data}")
                async with session.post(url, headers=headers, json=data, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    response = await response.json()
                print(response)
                if message := response.get("choices", [{}])[0].get("message", {}):
                    if content := message.get("content"):
                        return content
            except Exception:
                if attempt < 2:
                    continue
    return None


def get_prompt(name: str, **arguments) -> str:
    prompt = getattr(importlib.import_module(f"prompts.{name}"), name)
    if arguments:
        if callable(prompt):
            return prompt(**arguments)
        else:
            return prompt.format(**arguments)
    else:
        if callable(prompt):
            return prompt()
        else:
            return prompt


def extract_from_json(text, keys):
    keys = keys if isinstance(keys, list) else [keys]
    data = json.loads(text)
    results = []
    for key in keys:
        if key in data:
            results.append(data[key])
        else:
            results.append(None)
    return tuple(results) if len(keys) > 1 else results[0]


def extract_with_xml(text, tags):
    tags = tags if isinstance(tags, list) else [tags]
    results = []
    for tag in tags:
        if matched := re.search(rf"<{tag}>(?P<result>[\s\S]*)</{tag}>", text):
            results.append(matched.group("result").strip())
        else:
            results.append(re.sub(r"<[^>]+>", "\n", text).strip())
    return tuple(results) if len(tags) > 1 else results[0]


def save_as_txt(text, file_name):
    """
    统一的文本文件保存函数
    
    Args:
        text: 要保存的文本内容
        file_name: 文件名（不包含.txt扩展名）
    """
    # 确保outputs目录存在
    os.makedirs("outputs", exist_ok=True)
    file_path = f"outputs/{f"{file_name}_{random.randint(100000, 999999)}.txt"}"
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

def split_to_sentences(text):
    positions = [i for i, char in enumerate(text) if char == '。'] + [len(text) - 1]
    return "\n\n".join(f"{i + 1}. {text[start:end + 1].strip()}" for i, (start, end) in enumerate(zip([0] + [position + 1 for position in positions[:-1]], positions)) if text[start:end + 1].strip())

# 使用示例
if __name__ == "__main__":
    result=split_to_sentences("这是第一句话！这是第二句话。这是第三句话。这是第四句话？")
    print(result)
