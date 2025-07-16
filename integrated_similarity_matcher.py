import pandas as pd
import json
import os
import re
import asyncio
from typing import List, Dict, Tuple
from datetime import datetime
from utlis import call_llm
from keywords_and_tags_prompts import extract_keywords_and_tags

class IntegratedSimilarityMatcher:
    def __init__(self):
        """
        初始化集成相似度匹配器
        """
        self.source_file = r"c:\Users\panlin\OneDrive\桌面\模糊搜索\source_text.txt"
        self.source_processed_folder = r"c:\Users\panlin\OneDrive\桌面\模糊搜索\source_text_processed"
        self.processed_text_folder = r"c:\Users\panlin\OneDrive\桌面\模糊搜索\processed_text"
        # 添加结果输出文件夹
        self.results_folder = r"c:\Users\panlin\OneDrive\桌面\模糊搜索\integrated_similarity_results"
        self.processed_excel_files = []
        self.load_processed_excel_files()
    
    def load_processed_excel_files(self):
        """
        加载processed_text文件夹中最新的Excel文件
        """
        try:
            # 添加调试信息
            print(f"正在扫描文件夹：{self.processed_text_folder}")
            all_files = os.listdir(self.processed_text_folder)
            print(f"文件夹中的所有文件：{all_files}")
            
            # 过滤Excel文件，排除临时文件
            files = [f for f in all_files if f.endswith('.xlsx') and not f.startswith('~$')]
            print(f"有效的Excel文件：{files}")
            
            if not files:
                print("未找到有效的Excel文件")
                return
            
            # 按文件名中的时间戳排序，获取最新的文件
            # 文件名格式：processed_YYYYMMDD_HHMMSS.xlsx
            def extract_timestamp(filename):
                try:
                    # 提取时间戳部分：YYYYMMDD_HHMMSS
                    timestamp_part = filename.replace('processed_', '').replace('.xlsx', '')
                    return timestamp_part
                except:
                    return '00000000_000000'  # 如果解析失败，返回最小值
            
            # 按时间戳降序排序，最新的在前面
            files.sort(key=extract_timestamp, reverse=True)
            latest_file = files[0]
            
            print(f"找到{len(files)}个Excel文件，选择最新的：{latest_file}")
            
            # 只加载最新的文件
            file_path = os.path.join(self.processed_text_folder, latest_file)
            try:
                print(f"尝试读取文件：{file_path}")
                df = pd.read_excel(file_path)
                self.processed_excel_files.append({
                    'filename': latest_file,
                    'filepath': file_path,
                    'dataframe': df
                })
                print(f"成功加载最新Excel文件：{latest_file}，共{len(df)}行")
            except Exception as e:
                print(f"加载Excel文件{latest_file}失败：{e}")
                print(f"错误详情：{type(e).__name__}: {str(e)}")
            
        except Exception as e:
            print(f"加载processed_text文件夹失败：{e}")
            print(f"错误详情：{type(e).__name__}: {str(e)}")
    
    def extract_content_from_xml(self, text, tag):
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
    
    def parse_keywords_and_tags(self, response_text):
        """
        解析大模型返回的XML格式内容，提取所有10个信息类别（按新的结构）
        """
        try:
            print(f"\n=== 解析大模型响应 ===")
            print(f"原始响应：{response_text[:200]}{'...' if len(response_text) > 200 else ''}")
            
            # 定义所有需要提取的类别（按复杂度从简单到复杂排序，与keywords_and_tags_process.py保持一致）
            categories = {
                'basic_elements': 'basic_elements',
                'geographical_information': 'geographical_information',
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
                content = self.extract_content_from_xml(response_text, xml_tag)
                
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
                        if len(cleaned_content) > 3:  # 至少4个字符才认为有效
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
    
    def parse_keyword_tag_string(self, text):
        """
        解析关键词或标签字符串，提取列表
        支持新的格式：["关键词1"、"关键词2"、"关键词3"]
        """
        if not text or pd.isna(text):
            return []
        
        text = str(text).strip()
        if not text:
            return []
        
        # 尝试解析新的格式：["关键词1"、"关键词2"、"关键词3"]
        try:
            if text.startswith('[') and text.endswith(']'):
                # 处理可能的格式问题，将顿号替换为逗号
                text_processed = text.replace('"', '"').replace('"', '"').replace('、', '","')
                # 如果没有逗号分隔，尝试直接解析
                if ',' not in text_processed and '、' in text:
                    # 手动处理顿号分隔的情况
                    content = text[1:-1]  # 去掉方括号
                    items = content.split('、')
                    result = []
                    for item in items:
                        item = item.strip().strip('"').strip('"').strip('"')
                        if item:
                            result.append(item)
                    return result
                else:
                    items = json.loads(text_processed)
                    return [item.strip() for item in items if item.strip()]
        except:
            pass
        
        # 按常见分隔符分割
        for separator in ['、', ',', '，', ';', '；']:
            if separator in text:
                return [item.strip().strip('"').strip('"').strip('"') for item in text.split(separator) if item.strip()]
        
        # 如果是单个项目，去掉引号
        return [text.strip().strip('"').strip('"').strip('"')]
    
    def calculate_similarity(self, source_keywords, source_tags, article_keywords, article_tags):
        """
        计算关键词和标签的相似度
        """
        if not source_keywords and not source_tags:
            return 0.0
        
        # 计算关键词相似度
        keyword_similarity = 0.0
        if source_keywords and article_keywords:
            common_keywords = set(source_keywords) & set(article_keywords)
            keyword_similarity = len(common_keywords) / max(len(source_keywords), len(article_keywords))
        
        # 计算标签相似度
        tag_similarity = 0.0
        if source_tags and article_tags:
            common_tags = set(source_tags) & set(article_tags)
            tag_similarity = len(common_tags) / max(len(source_tags), len(article_tags))
        
        # 综合相似度（关键词权重0.6，标签权重0.4）
        total_similarity = keyword_similarity * 0.6 + tag_similarity * 0.4
        return total_similarity
    
    async def process_source_text(self):
        """
        处理源文本，提取关键词和标签
        """
        print("\n=== 步骤1：处理源文本 ===")
        
        # 读取源文本
        try:
            with open(self.source_file, 'r', encoding='utf-8') as f:
                source_text = f.read().strip()
            print(f"源文本内容：{source_text[:100]}{'...' if len(source_text) > 100 else ''}")
        except Exception as e:
            print(f"读取源文本失败：{e}")
            return None
        
        # 调用大模型处理
        try:
            system_message = extract_keywords_and_tags()
            response = await call_llm(system_message=system_message, user_message=source_text)
            
            if response:
                # 解析结果
                result = self.parse_keywords_and_tags(response)
                
                # 保存结果
                os.makedirs(self.source_processed_folder, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = os.path.join(self.source_processed_folder, f"source_text_keywords_tags_{timestamp}.json")
                
                save_data = {
                    'source_text': source_text,
                    'timestamp': timestamp,
                    **result
                }
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(save_data, f, ensure_ascii=False, indent=2)
                
                print(f"源文本处理结果已保存到：{output_file}")
                return result
            else:
                print("大模型处理失败")
                return None
                
        except Exception as e:
            print(f"处理源文本时出错：{e}")
            return None
    
    def match_articles_from_excel(self, source_result: Dict) -> List[Dict]:
        """
        从最新的Excel文件中匹配文章并计算相似度
        """
        print("\n=== 步骤2：匹配最新Excel文件中的文章 ===")
        
        if not self.processed_excel_files:
            print("没有可用的Excel文件")
            return []
        
        # 解析源文本的关键词和标签
        source_keywords = self.parse_keyword_tag_string(source_result.get('keywords', ''))
        source_tags = self.parse_keyword_tag_string(source_result.get('tags', ''))
        
        print(f"源文本关键词：{source_keywords}")
        print(f"源文本标签：{source_tags}")
        
        all_matched_articles = []
        
        # 处理最新的Excel文件
        excel_file = self.processed_excel_files[0]
        df = excel_file['dataframe']
        
        print(f"正在处理文件：{excel_file['filename']}")
        print(f"文件包含{len(df)}行数据")
        
        # 查找相关列（适应新的列名）
        content_column = None
        title_column = None
        link_column = None
        keywords_column = None
        tags_column = None
        
        # 查找列
        for col in df.columns:
            col_str = str(col).lower()
            if any(keyword in col_str for keyword in ['观点内容', '原文', '内容']):
                content_column = col
            elif any(keyword in col_str for keyword in ['主题', '标题', 'title']):
                title_column = col
            elif any(keyword in col_str for keyword in ['链接', 'url', 'link']):
                link_column = col
            elif any(keyword in col_str for keyword in ['关键词', 'keywords']):
                keywords_column = col
            elif any(keyword in col_str for keyword in ['标签', 'tags']):
                tags_column = col
        
        if not content_column:
            print("未找到内容列")
            return []
        
        print(f"找到列：内容={content_column}, 标题={title_column}, 链接={link_column}, 关键词={keywords_column}, 标签={tags_column}")
        
        # 计算每篇文章的相似度
        for index, row in df.iterrows():
            content = row[content_column]
            
            # 跳过空行或标题行
            if pd.isna(content) or not str(content).strip() or '观点内容' in str(content) or '原文' in str(content):
                continue
            
            # 获取文章信息
            title = row[title_column] if title_column and pd.notna(row[title_column]) else "无标题"
            link = row[link_column] if link_column and pd.notna(row[link_column]) else ""
            
            # 获取关键词和标签
            article_keywords = []
            article_tags = []
            
            if keywords_column and pd.notna(row[keywords_column]):
                article_keywords = self.parse_keyword_tag_string(row[keywords_column])
            
            if tags_column and pd.notna(row[tags_column]):
                article_tags = self.parse_keyword_tag_string(row[tags_column])
            
            # 计算相似度
            similarity = self.calculate_similarity(
                source_keywords, source_tags,
                article_keywords, article_tags
            )
            
            # 只保留有一定相似度的文章
            if similarity > 0:
                all_matched_articles.append({
                    'source_file': excel_file['filename'],
                    'index': index,
                    'title': title,
                    'content': str(content),
                    'link': link,
                    'keywords': article_keywords,
                    'tags': article_tags,
                    'similarity': similarity
                })
        
        # 按相似度降序排序
        all_matched_articles.sort(key=lambda x: x['similarity'], reverse=True)
        
        print(f"找到{len(all_matched_articles)}篇相关文章")
        return all_matched_articles
    
    def display_results(self, matched_articles: List[Dict], top_n: int = None):
        """
        显示匹配结果
        
        Args:
            matched_articles: 匹配的文章列表
            top_n: 显示前N篇文章，None表示显示全部
        """
        if not matched_articles:
            print("未找到匹配的文章")
            return
        
        display_articles = matched_articles[:top_n] if top_n else matched_articles
        
        print(f"\n=== 匹配结果 (共找到{len(matched_articles)}篇相关文章) ===")
        if top_n:
            print(f"显示前{len(display_articles)}篇：")
        
        for i, article in enumerate(display_articles, 1):
            print(f"\n【第{i}名】相似度：{article['similarity']:.4f}")
            print(f"来源文件：{article['source_file']}")
            print(f"标题：{article['title']}")
            
            # 显示内容摘要
            content = article['content']
            if len(content) > 200:
                print(f"正文：{content[:200]}...")
            else:
                print(f"正文：{content}")
            
            if article['link']:
                print(f"链接：{article['link']}")
            
            if article['keywords']:
                print(f"关键词：{article['keywords']}")
            
            if article['tags']:
                print(f"标签：{article['tags']}")
            
            print("-" * 80)
    
    def save_results(self, matched_articles: List[Dict], output_file: str = None):
        """
        保存匹配结果到文件
        
        Args:
            matched_articles: 匹配的文章列表
            output_file: 输出文件路径
        """
        # 确保结果文件夹存在
        os.makedirs(self.results_folder, exist_ok=True)
        
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(self.results_folder, f"integrated_similarity_results_{timestamp}.json")
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(matched_articles, f, ensure_ascii=False, indent=2)
            print(f"匹配结果已保存到：{output_file}")
        except Exception as e:
            print(f"保存结果失败：{e}")
    
    async def run_complete_process(self):
        """
        运行完整的处理流程
        """
        print("=== 开始集成处理流程 ===")
        
        # 步骤1：处理源文本
        source_result = await self.process_source_text()
        
        if not source_result:
            print("源文本处理失败，程序终止")
            return
        
        # 步骤2：匹配文章
        matched_articles = self.match_articles_from_excel(source_result)
        
        # 步骤3：显示结果
        print("\n=== 步骤3：显示匹配结果 ===")
        self.display_results(matched_articles)
        
        # 步骤4：保存结果
        print("\n=== 步骤4：保存结果 ===")
        # 确保结果文件夹存在
        os.makedirs(self.results_folder, exist_ok=True)
        output_file = os.path.join(self.results_folder, "integrated_similarity_results.json")
        self.save_results(matched_articles, output_file)
        
        print(f"\n=== 处理完成 ===")
        print(f"共找到{len(matched_articles)}篇相关文章")
        print(f"详细结果已保存到：{output_file}")
        
        return matched_articles

async def main():
    """
    主函数
    """
    matcher = IntegratedSimilarityMatcher()
    await matcher.run_complete_process()

if __name__ == "__main__":
    asyncio.run(main())