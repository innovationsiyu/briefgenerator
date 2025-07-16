import pandas as pd
from utlis import call_llm
import asyncio
import re
import json
import os
from datetime import datetime
import aiohttp  # 添加这个导入

def extract_content_from_xml(text, tag):
    """
    从XML标签中提取内容，保持原始格式（包括方括号）
    """
    # 提取XML标签内的完整内容，包括方括号
    pattern = rf"<{tag}>\s*([^<]+)\s*</{tag}>"
    match = re.search(pattern, text)
    
    if match:
        content = match.group(1).strip()
        return content
    
    return ""

def parse_keywords_and_tags(response_text):
    """
    解析大模型返回的XML格式内容，只保留有具体内容的类别
    """
    try:
        print(f"\n=== 解析大模型响应 ===")
        print(f"原始响应：{response_text[:200]}{'...' if len(response_text) > 200 else ''}")
        
        # 定义所有需要提取的类别（按复杂度从简单到复杂排序）
        categories = {
            'basic_elements': 'basic_elements',
            'economy_and_industry': 'economy_and_industry',
            'policies_and_regulations': 'policies_and_regulations',
            'professional_terms': 'professional_terms',
            'people_and_organizations': 'people_and_organizations',
            'events_and_dynamics': 'events_and_dynamics',
            'analysis_and_judgment': 'analysis_and_judgment',
            'keywords': 'keywords',
            'tags': 'tags'
        }
        result = {}
        valid_content_count = 0
        
        # 提取每个类别的内容
        for category_key, xml_tag in categories.items():
            content = extract_content_from_xml(response_text, xml_tag)
            
            # 只保留有实际内容的类别
            if content and content.strip():
                cleaned_content = content.strip()
                
                # 过滤无意义的内容
                invalid_patterns = [
                    '', '无', '暂无', 'N/A', 'n/a', '未找到', '无相关内容', 
                    '无内容', '空', 'null', 'None', '无信息', '不适用', 
                    '无此类信息', '未涉及', '无相关', '无具体', '无明确'
                ]
                
                # 检查是否为无效内容
                is_invalid = False
                for pattern in invalid_patterns:
                    if cleaned_content.lower() == pattern.lower():
                        is_invalid = True
                        break
                
                if is_invalid:
                    continue
                
                # 对于keywords和tags，进行更严格的验证
                if category_key in ['keywords', 'tags']:
                    # 检查基本格式
                    if not ('"' in cleaned_content and '[' in cleaned_content and ']' in cleaned_content):
                        continue
                    
                    # 检查是否包含无效的列表
                    invalid_lists = [
                        '[]', '["无"]', '["暂无"]', '["N/A"]', '["无内容"]',
                        '["无相关内容"]', '["未找到"]', '["无信息"]'
                    ]
                    if cleaned_content in invalid_lists:
                        continue
                    
                    # 检查是否包含有效的分隔符和足够的内容
                    if ('、' in cleaned_content or ',' in cleaned_content) and len(cleaned_content) > 15:
                        result[category_key] = cleaned_content
                        valid_content_count += 1
                        print(f"提取的{category_key}：{cleaned_content[:50]}{'...' if len(cleaned_content) > 50 else ''}")
                else:
                    # 对于其他类别，检查内容长度和有效性
                    if len(cleaned_content) > 3:  # 至少4个字符
                        result[category_key] = cleaned_content
                        valid_content_count += 1
                        print(f"提取的{category_key}：{cleaned_content[:50]}{'...' if len(cleaned_content) > 50 else ''}")
            else:
                print(f"跳过{category_key}：无有效内容")
        
        print(f"总共提取到{valid_content_count}个有效类别")
        return result
        
    except Exception as e:
        print(f"解析信息失败：{e}")
        print(f"原始响应：{response_text}")
        return {}

def create_output_folder(input_path):
    """
    创建固定的输出文件夹：processed_text
    """
    # 获取输入文件的目录
    input_dir = os.path.dirname(input_path)
    
    # 创建固定的文件夹名
    output_folder = os.path.join(input_dir, "processed_text")
    
    # 创建文件夹
    os.makedirs(output_folder, exist_ok=True)
    print(f"使用输出文件夹：{output_folder}")
    
    return output_folder

def simple_read_excel(file_path):
    """
    简化的Excel读取函数，直接读取文件
    
    Args:
        file_path: Excel文件路径
    
    Returns:
        DataFrame: 处理后的数据框
    """
    print(f"\n=== 读取Excel文件 ===")
    print(f"文件路径：{file_path}")
    
    try:
        # 直接读取Excel文件，不使用header参数
        df = pd.read_excel(file_path, header=None)
        
        if df.empty:
            raise Exception("Excel文件为空")
        
        print(f"成功读取Excel文件，共{len(df)}行数据")
        print(f"列数：{len(df.columns)}")
        
        # 给列设置简单的名称
        df.columns = [f'列{i+1}' for i in range(len(df.columns))]
        
        return df
        
    except Exception as e:
        print(f"读取Excel文件失败：{e}")
        raise

def find_column(df, search_terms, search_rows=10):
    """
    查找包含指定关键词的列
    
    Args:
        df: DataFrame
        search_terms: 要搜索的关键词列表
        search_rows: 搜索的行数
    
    Returns:
        找到的列名，如果未找到返回None
    """
    # 在前几行数据中查找
    search_rows = min(search_rows, len(df))
    print(f"在前{search_rows}行中搜索包含{search_terms}的单元格...")
    
    for row_idx in range(search_rows):
        for col_idx, col_name in enumerate(df.columns):
            cell_value = df.iloc[row_idx, col_idx]
            if pd.notna(cell_value):
                for term in search_terms:
                    if term in str(cell_value):
                        print(f"在第{row_idx+1}行第{col_idx+1}列找到包含'{term}'的单元格：{cell_value}")
                        print(f"将使用列'{col_name}'作为{search_terms[0]}列")
                        return col_name
    
    return None

def detect_header_row(df, max_search_rows=10):
    """
    智能检测Excel中的标题行位置
    
    Args:
        df: DataFrame
        max_search_rows: 最大搜索行数
    
    Returns:
        int: 标题行的索引（0-based）
    """
    print(f"\n=== 智能检测标题行 ===")
    
    # 定义标题关键词
    header_keywords = [
        '观点内容', '原文', '内容', '正文', '文本',
        '主题', '标题', '题目', 'title', '主题词',
        '链接', '原文链接', 'URL', 'url', 'link', '网址', '地址',
        '关键词', 'keywords', '关键字',
        '标签', 'tags', '分类', '类别',
        '时间', '日期', 'date', 'time',
        '作者', '来源', 'source', 'author', '人物'
    ]
    
    search_rows = min(max_search_rows, len(df))
    
    # 查找包含最多关键词的行
    best_row_index = 0
    max_keyword_count = 0
    
    for row_idx in range(search_rows):
        keyword_count = 0
        
        for col_idx in range(len(df.columns)):
            cell_value = df.iloc[row_idx, col_idx]
            
            if pd.notna(cell_value) and str(cell_value).strip():
                cell_str = str(cell_value).strip()
                
                # 检查是否包含标题关键词
                for keyword in header_keywords:
                    if keyword in cell_str:
                        keyword_count += 1
                        break
        
        print(f"第{row_idx+1}行 - 关键词匹配数: {keyword_count}")
        
        if keyword_count > max_keyword_count:
            max_keyword_count = keyword_count
            best_row_index = row_idx
    
    print(f"\n检测结果：第{best_row_index+1}行被识别为标题行")
    print(f"标题行关键词匹配数：{max_keyword_count}")
    
    # 显示标题行内容
    print(f"标题行内容预览：")
    for col_idx, col_name in enumerate(df.columns):
        cell_value = df.iloc[best_row_index, col_idx]
        if pd.notna(cell_value) and str(cell_value).strip():
            print(f"  {col_name}: {str(cell_value)[:30]}{'...' if len(str(cell_value)) > 30 else ''}")
    
    return best_row_index

async def process_excel(input_path):
    # 简化读取Excel文件
    try:
        df = simple_read_excel(input_path)
    except Exception as e:
        print(f"读取Excel文件失败：{e}")
        return None
    
    # 智能检测标题行（包含原文、标题的行）
    header_row_index = detect_header_row(df)
    
    print(f"\n=== 数据处理范围 ===")
    print(f"检测到的标题行：第{header_row_index+1}行")
    
    # 查找各个列
    print("\n=== 开始识别列 ===")
    
    # 查找观点内容列
    content_column = find_column(df, ['观点内容', '原文'])
    if content_column is None:
        print(f"未找到包含'观点内容'或'原文'的列或单元格。")
        print("前5行数据预览：")
        print(df.head())
        return None
    
    # 查找主题列
    topic_column = find_column(df, ['主题', '标题', '题目', 'title'])
    
    # 查找原文链接列
    link_column = find_column(df, ['链接', '原文链接', 'URL', 'url', 'link', '网址'])
    
    # 定义所有需要的列及其中文名称（按复杂度从简单到复杂排序）
    required_columns = {
        'basic_elements': '基础要素',
        'economy_and_industry': '经济与产业分类',
        'policies_and_regulations': '政策与法规',
        'professional_terms': '专业术语与缩略词',
        'people_and_organizations': '人物与组织',
        'events_and_dynamics': '事件与动态',
        'analysis_and_judgment': '分析与判断',
        'keywords': '关键词',
        'tags': '标签'
    }
    
    # 检查并创建所有需要的列
    column_mapping = {}
    for eng_name, cn_name in required_columns.items():
        # 查找是否已存在该列
        existing_column = find_column(df, [cn_name, eng_name])
        
        if existing_column is None:
            # 添加新列
            new_col_name = f'列{len(df.columns)+1}'
            df[new_col_name] = ''
            column_mapping[eng_name] = new_col_name
            # 在标题行设置列名
            df.at[header_row_index, new_col_name] = cn_name
            print(f"已添加'{cn_name}'列并在标题行设置列名")
        else:
            column_mapping[eng_name] = existing_column
            print(f"找到现有的'{cn_name}'列：{existing_column}")
    
    print(f"\n=== 列识别结果 ===")
    print(f"观点内容列：{content_column}")
    print(f"主题列：{topic_column if topic_column else '未找到'}")
    print(f"链接列：{link_column if link_column else '未找到'}")
    for eng_name, cn_name in required_columns.items():
        print(f"{cn_name}列：{column_mapping[eng_name]}")
    
    # 重新整理DataFrame，将标题行移动到第一行
    print(f"\n=== 重新整理数据结构 ===")
    
    # 提取标题行
    header_row = df.iloc[header_row_index].copy()
    
    # 提取数据行（标题行之后的所有行）
    data_rows = df.iloc[header_row_index + 1:].copy()
    
    # 清空所有新增列的数据部分
    for eng_name in required_columns.keys():
        if eng_name in column_mapping:
            data_rows[column_mapping[eng_name]] = ''
    
    # 重新构建DataFrame：标题行在第一行，数据行从第二行开始
    new_df = pd.DataFrame([header_row] + [row for _, row in data_rows.iterrows()])
    new_df.columns = df.columns
    new_df.reset_index(drop=True, inplace=True)
    
    # 更新df引用
    df = new_df
    
    # 现在标题行在第0行，数据从第1行开始
    header_row_index = 0
    data_start_row = 1
    
    print(f"标题行已移动到第1行")
    print(f"数据开始行：第{data_start_row+1}行")
    print(f"总数据行数：{len(df) - data_start_row}行")
    
    # 处理所有数据行（从第2行开始）
    processed_count = 0
    failed_count = 0
    
    print(f"\n=== 开始处理数据（从第{data_start_row+1}行开始） ===")
    
    # 在process_excel函数中，替换大模型调用部分（约第358行开始）
    for index in range(data_start_row, len(df)):
        row = df.iloc[index]
        
        content = row[content_column]
        topic = row[topic_column] if topic_column else ""
        link = row[link_column] if link_column else ""
        
        # 检查观点内容是否为空
        if pd.isna(content) or not str(content).strip():
            print(f"跳过第{index+1}行：观点内容为空")
            continue
        
        # 检查是否是重复的标题行（包含标题关键词）
        content_str = str(content).strip()
        if any(keyword in content_str for keyword in ['观点内容', '原文', '主题', '标题', '关键词', '标签']):
            print(f"跳过第{index+1}行：包含标题关键词，可能是重复标题行")
            continue
        
        print(f"\n正在处理第{index+1}行（数据行{index-data_start_row+1}）...")
        print(f"主题：{str(topic)[:50]}{'...' if len(str(topic)) > 50 else ''}")
        print(f"观点内容：{str(content)[:100]}{'...' if len(str(content)) > 100 else ''}")
        print(f"链接：{str(link)[:50]}{'...' if len(str(link)) > 50 else ''}")
        
        # 从keywords_and_tags_prompts.py导入提示词
        try:
            from keywords_and_tags_prompts import extract_keywords_and_tags
            system_message = extract_keywords_and_tags()
        except ImportError:
            system_message = """
            请按照以下要求提取关键词(keywords)和标签(tags)：
            
            【输出格式要求】
            请严格按照以下XML标签格式输出，每个关键词和标签都要用双引号包裹，关键词和标签之间使用顿号"、"连接：
            
            <keywords>["关键词1"、"关键词2"、"关键词3"、"关键词4"、"关键词5"、"关键词6"、"关键词7"、"关键词8"、"关键词9"、"关键词10"]</keywords>
            <tags>["标签1"、"标签2"、"标签3"、"标签4"、"标签5"、"标签6"、"标签7"、"标签8"、"标签9"、"标签10"]</tags>
            
            关键词必须来自观点内容，标签可以是概括性分类。
            """
        
        # 无限重试机制：直到获得有效结果为止
        retry_count = 0
        parsed_result = None
        
        print(f"开始处理第{index+1}行，将无限重试直到获得有效结果...")
        
        while True:  # 无限循环，直到获得有效结果
            try:
                if retry_count == 0:
                    print(f"大模型调用开始")
                else:
                    print(f"第{retry_count+1}次重试调用大模型")
                
                response = await call_llm(
                    system_message=system_message,
                    user_message=str(content)
                )
                
                print(f"大模型调用结束")
                
                if response and response.strip():
                    # 解析大模型返回的所有类别内容
                    parsed_result = parse_keywords_and_tags(response)
                    
                    # 检查是否有有效内容
                    has_valid_content = False
                    valid_categories = []
                    
                    for category, content_data in parsed_result.items():
                        if content_data and content_data.strip():
                            # 进一步验证内容的有效性
                            cleaned_content = content_data.strip()
                            
                            # 对于keywords和tags，检查格式
                            if category in ['keywords', 'tags']:
                                if ('"' in cleaned_content and 
                                    ('、' in cleaned_content or ',' in cleaned_content) and 
                                    len(cleaned_content) > 10):  # 至少包含一些实际内容
                                    has_valid_content = True
                                    valid_categories.append(category)
                            else:
                                # 对于其他类别，检查长度和内容
                                if len(cleaned_content) > 3:  # 至少4个字符
                                    has_valid_content = True
                                    valid_categories.append(category)
                    
                    if has_valid_content:
                        print(f"✓ 获得有效响应！包含{len(valid_categories)}个有效类别：{', '.join(valid_categories)}")
                        print(f"第{index+1}行总共重试{retry_count}次")
                        break  # 跳出循环
                    else:
                        print(f"⚠ 响应无有效内容，继续重试...")
                        retry_count += 1
                else:
                    print(f"⚠ 未获得响应或响应为空，继续重试...")
                    retry_count += 1
                    
            except Exception as e:
                import aiohttp
                import json
                
                # 精细化错误分类
                if isinstance(e, aiohttp.ClientConnectorError):
                    print(f"⚠ 连接错误：{e}，检查ollama服务是否启动")
                elif isinstance(e, aiohttp.ServerTimeoutError):
                    print(f"⚠ 超时错误：{e}，可能需要增加超时时间")
                elif isinstance(e, json.JSONDecodeError):
                    print(f"⚠ JSON解析错误：{e}，响应格式异常")
                else:
                    print(f"⚠ 未知错误：{type(e).__name__}: {e}")
                
                retry_count += 1
                
                # 对于连续的连接错误，添加更长的等待时间
                if isinstance(e, aiohttp.ClientConnectorError):
                    print("检测到连接问题，等待10秒后重试...")
                    await asyncio.sleep(10)
            
            # 添加延迟，避免过于频繁的请求
            if retry_count > 0:  # 只有重试时才延迟
                await asyncio.sleep(min(retry_count * 0.5, 5))  # 递增延迟，最大5秒
        
        # 移除原来的重试失败处理代码，因为现在是无限重试
        # 保存有效结果到Excel
        if parsed_result:
            saved_categories = []
            for category, content_data in parsed_result.items():
                if category in column_mapping and content_data and content_data.strip():
                    df.at[index, column_mapping[category]] = content_data.strip()
                    saved_categories.append(required_columns[category])
                    print(f"✓ {required_columns[category]}已保存：{content_data[:50]}{'...' if len(content_data) > 50 else ''}")
            
            print(f"✓ 第{index+1}行处理完成！保存了{len(saved_categories)}个类别：{', '.join(saved_categories)}")
            processed_count += 1
        else:
            # 这种情况理论上不会发生，因为我们有无限重试
            print(f"✗ 第{index+1}行处理异常：未获得有效结果")
            failed_count += 1
    
    print(f"\n=== 处理完成 ===")
    print(f"成功处理：{processed_count}行数据")
    print(f"处理失败：{failed_count}行数据")
    
    # 确保输出文件夹为 processed_text
    output_folder = create_output_folder(input_path)
    
    # 生成具体时间格式的文件名
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"processed_{current_time}.xlsx"
    output_path = os.path.join(output_folder, output_filename)
    
    # 保存处理后的文件到指定文件夹
    print(f"\n=== 保存文件到：{output_path} ===")
    
    try:
        # 使用header=False确保第一行就是我们的标题行
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='处理结果', index=False, header=False)
            
            # 调整列宽
            worksheet = writer.sheets['处理结果']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)  # 最大宽度50
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        print(f"✓ 文件保存成功！")
        print(f"结果已保存到：{output_path}")
        
    except Exception as e:
        print(f"✗ 文件保存失败：{e}")
        return None
    
    return output_path

if __name__ == "__main__":
    # 更新为您的文件路径
    input_file = r"C:\Users\panlin\OneDrive\桌面\模糊搜索\张攀林-2025年安邦观点2.23-3.5总结.xlsx"
    output_file = asyncio.run(process_excel(input_file))
    if output_file:
        print(f"\n处理完成，结果已保存到: {output_file}")
        print(f"输出文件夹: {os.path.dirname(output_file)}")
    else:
        print("处理失败")