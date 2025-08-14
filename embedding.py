# embedding.py

import os
import time
from datetime import datetime
import json
import numpy as np
from openai import OpenAI
from typing import List, Union, Dict
import pandas as pd
import faiss
import pickle
import ast


DASHSCOPE_API_KEY = "sk-684a3a134fbf49af8818a88260778df3"

# 全局复用 OpenAI 客户端
client = OpenAI(api_key=DASHSCOPE_API_KEY, base_url="https://dashscope.aliyuncs.com/compatible-mode/v1", timeout=60)

def vectorize(texts: Union[str, List[str]]) -> List[Dict]:
    """
    向量化输入文本（支持单个字符串或字符串列表）。
    包含重试机制和超时设置。
    
    参数:
    - texts (str or List[str]): 要向量化的文本内容
    
    返回:
    - List[Dict]: 包含向量信息的字典列表
    """
    for attempt in range(3):
        try:
            completion = client.embeddings.create(model="text-embedding-v4", input=texts, dimensions=1024, encoding_format="float")
            return json.loads(completion.model_dump_json())['data']
        except Exception as e:
            if attempt < 2:
                print(f"API调用失败，立即重试... (尝试 {attempt + 1}/3)")
            else:
                print(f"API调用失败，已达到最大重试次数: {e}")
                raise

def merge_tags_to_csv(csv_path: str) -> None:
    """
    处理CSV文件，将多个标签列合并成一个article_tags列
    
    参数:
    - csv_path (str): CSV文件路径
    """
    # 读取CSV文件
    df = pd.read_csv(csv_path)
    # 定义需要处理的列
    columns = [
        "political_and_economic_terms",
        "technical_terms", 
        "other_abstract_concepts",
        "organizations",
        "persons",
        "cities_or_districts",
        "other_concrete_entities",
        "other_tags_of_topic_or_points"
    ]
    # 定义需要过滤掉的标签
    filter_tags = {'安邦咨询', '安邦智库', 'ANBOUND', '陈功'}
    # 使用推导式创建article_tags列，并过滤掉指定标签
    df['article_tags'] = [
        [tag for column in columns 
         if isinstance(row[column], str) 
         for tag in ast.literal_eval(row[column]) 
         if tag not in filter_tags] 
        for i, row in df.iterrows()
    ]
    # 将更新后的数据框保存回CSV文件
    df.to_csv(csv_path, index=False)

def vectorize_tags_to_csv(csv_path: str) -> None:
    """
    处理CSV文件，将每一行的article_tags列表向量化并转换为字典格式
    
    参数:
    - csv_path (str): CSV文件路径
    """
    df = pd.read_csv(csv_path)
    tag_vecs_list = []
    for _, row in df.iterrows():
        article_tags = ast.literal_eval(row["article_tags"])
        if article_tags:
            embeddings = []
            for start in range(0, len(article_tags), 10):  # 每批最多 10 条，避免接口报错
                embeddings.extend(vectorize(article_tags[start:start + 10]))
                time.sleep(0.2)  # 节流：每次API调用后等待0.2秒
            tag_vecs_list.append({tag: vec["embedding"] for tag, vec in zip(article_tags, embeddings)})
        else:
            tag_vecs_list.append({})
    df["article_tags"] = tag_vecs_list
    df.to_csv(csv_path, index=False)

def merge_and_vectorize_tags_to_csv(data_folder: str = "/Users/siyu/Documents/briefgenerator/测试数据") -> None:
    """
    从指定文件夹筛选出修改日期在2025年8月6日及以后的CSV文件，
    先调用merge_tags_to_csv函数，再调用vectorize_tags_to_csv函数
    
    参数:
    - data_folder (str): 数据文件夹路径
    """
    # 获取文件夹中所有CSV文件
    csv_files = [f for f in os.listdir(data_folder) if f.endswith('.csv')]
    # 筛选出修改日期在阈值日期及以后的文件
    recent_files = []
    for csv_file in csv_files:
        file_path = os.path.join(data_folder, csv_file)
        # 获取文件修改时间
        modification_time = datetime.fromtimestamp(os.path.getmtime(file_path))
        if modification_time >= datetime(2025, 8, 6): # 设定筛选的日期阈值（2025年8月6日）
            recent_files.append(file_path)
    print(f"找到 {len(recent_files)} 个符合条件的CSV文件（修改日期在2025年8月6日及以后）")
    # 对每个符合条件的文件执行处理
    for i, file_path in enumerate(recent_files, 1):
        print(f"正在处理文件 {i}/{len(recent_files)}: {os.path.basename(file_path)}")
        # 步骤1：合并标签
        # print(f"  - 合并标签...")
        # merge_tags_to_csv(file_path)
        # 步骤2：向量化标签
        # print(f"  - 向量化标签...")
        # vectorize_tags_to_csv(file_path)
        print(f"  - 文件处理完成")
    print(f"所有 {len(recent_files)} 个文件处理完成")

def build_ann_index(data_folder: str = "/Users/siyu/Documents/briefgenerator/temp测试数据") -> dict:
    """从CSV文件中提取标签向量，构建FAISS索引并保存到文件"""
    csv_files = [f for f in os.listdir(data_folder) if f.endswith('.csv')]
    recent_files = [
        os.path.join(data_folder, csv_file) 
        for csv_file in csv_files 
        if datetime.fromtimestamp(os.path.getmtime(os.path.join(data_folder, csv_file))) >= datetime(2025, 8, 5)
    ]
    all_tag_vecs = {}
    for file_path in recent_files:
        df = pd.read_csv(file_path)
        for _, row in df.iterrows():
            tag_dict = ast.literal_eval(row['article_tags'])
            all_tag_vecs.update(tag_dict)
    tags = list(all_tag_vecs.keys())
    vectors = np.array([all_tag_vecs[tag] for tag in tags], dtype='float32')
    faiss.normalize_L2(vectors)
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)
    ann_data = {"index": index, "tags": tags}
    with open('all_tag_vecs.txt', 'wb') as f:
        pickle.dump(ann_data, f)
    return ann_data

def remove_filter_tags_from_csv(data_folder: str = "/Users/siyu/Documents/briefgenerator/测试数据") -> None:
    """
    批量处理CSV文件，从article_tags字典中去除指定的键值对
    仅处理修改日期为2025年8月5日的文件
    """
    filter_tags = {'安邦咨询', '安邦智库', 'ANBOUND', '陈功'}
    csv_files = [f for f in os.listdir(data_folder) if f.endswith('.csv')]
    target_files = [
        os.path.join(data_folder, csv_file) 
        for csv_file in csv_files 
        if datetime.fromtimestamp(os.path.getmtime(os.path.join(data_folder, csv_file))).date() == datetime(2025, 8, 5).date()
    ]
    
    for file_path in target_files:
        df = pd.read_csv(file_path)
        df['article_tags'] = [
            {k: v for k, v in ast.literal_eval(row['article_tags']).items() if k not in filter_tags}
            for _, row in df.iterrows()
        ]
        df.to_csv(file_path, index=False)

def get_similar_tags(query: str, top_n: int = 100) -> set:
    """对查询文本进行向量化，并从预先构建的索引中查找最相似的标签，返回标签集合"""
    query_vec = vectorize([query])[0]
    with open('all_tag_vecs.txt', 'rb') as f:
        ann_data = pickle.load(f)
    query_array = np.asarray(query_vec['embedding'], dtype='float32').reshape(1, -1)
    faiss.normalize_L2(query_array)
    distances, indices = ann_data["index"].search(query_array, top_n)
    similar_tags = [ann_data["tags"][i] for i in indices[0]]
    return set(similar_tags)

if __name__ == "__main__":
    # 如果需要处理新文件，取消下面这行的注释
    # merge_and_vectorize_tags_to_csv()
    build_ann_index()
    
    # 运行主函数进行标签相似度查询
    # query = """
# 近日，比亚迪股份在港交所公告称，公司成功完成了一项大规模的港股配售。这也是近四年来香港股市规模最大的一次融资活动。比亚迪公告称，假设配售股份全数配售，配售所得款项总额预计约为435.09亿港元（约合人民币407.48亿元），于扣除佣金和估计费用后，配售所得款项净额预计约为433.83亿港元（约合人民币406.30亿元）。而最新数据显示，截至2024年三季度，比亚迪的所有者权益总额为1688亿元，足可以看出本次融资的规模之大。比亚迪计划将新筹集的资金用于多个关键领域，包括扩大海外业务、投资研发、补充营运资金以及一般企业用途。花旗集团分析师Jeff Chung表示：“我们视此次股权融资为积极之举。”彭博情报分析师Joanna Chen也指出，此次配售将有助于比亚迪加速海外工厂的建设，这在关税风险不断增加的背景下显得更加迫切。目前比亚迪依然在扩大本地化生产来对抗关税，其位于匈牙利的工厂计划在今年晚些时候投产，另一家在土耳其的工厂正在筹建中，同时还在考虑设立第三家欧洲工厂。值得注意的是，安邦智库（ANBOUND）的研究人员曾提到，目前以比亚迪为代表的新能源车企负债率整体处于较高水平，这也凸显了本次股权融资的重要性。市场对本次配股的反应偏中性，配售定价较3月3日的收盘价折价7.8%，而3月4日港股收盘比亚迪股份下跌约6.8%。（PMS）
# """
    # 运行主函数进行标签相似度查询
    # get_similar_tags(query)
