import os

def text_processor(source_article: str) -> str:
    """
    处理原文文本，包括星期转具体日期、去除股票代码、台湾用语转大陆用语等

    返回:
        processed_text (str): 处理后的纯文本
    """
    input_path = os.path.join('inputs', 'source_article')
    output_path = os.path.join('processes', 'processed_text.txt')


    from utils_penghan.text_processor import text_processor as utils_text_processor

    # 调用utils_penghan/text_processor.py中的text_processor函数处理文本
    processed_text = utils_text_processor(source_article)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(processed_text)


    return processed_text