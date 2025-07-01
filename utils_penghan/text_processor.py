import json
import re
from datetime import datetime, timedelta


word_mapping={
    "捷运":"地铁",
    "晶片": "芯片",
    "资讯": "信息",
    "讯息": "消息",
    "网路": "网络",
    "资安": "网安",
    "行动装置": "移动设备",
    "行动电话": "手机",
    "阵列": "数组",
    "运算": "计算",
    "撰写": "编写",
    "萤幕": "屏幕",
    "程式": "程序",
    "资料库": "数据库",
    "伺服器": "服务器",
    "档案": "文件",
    "硬碟": "硬盘",
    "光碟": "光盘",
    "软体": "软件",
    "硬体": "硬件",
    "记忆体": "内存",
    "滑鼠": "鼠标",
    "人工智慧": "人工智能",
    "巨量资料": "大数据",
    "云端运算": "云计算",
    "穿戴式装置": "可穿戴设备",
    "选择权": "期权",
    "衍生性金融商品": "金融衍生品",
    "避险": "对冲",
    "本益比": "市盈率",
    "殖利率": "收益率",
    "投资报酬率": "投资回报率",
    "风险控管": "风险管理",
    "信用评等": "信用评级",
    "金融风暴": "金融危机",
    "经济成长": "经济增长",
    "国内生产毛额": "国内生产总值",
    "通膨": "通胀",
    "通货膨胀": "通货膨胀",
    "通货紧缩": "通货紧缩",
    "汇率机制": "汇率制度",
    "利率自由化": "利率市场化",
    "财政短绌": "财政赤字",
    "预算法短绌": "财政赤字",
    "国家发展委员会": "国家发展改革委员会",
    "马克宏": "马克龙",
    "川普": "特朗普",
    "欧巴马": "奥巴马",
    "普丁": "普京",
    "梅伊": "特雷莎·梅",
    "梅尔茨":"默茨",
    "北韩":"朝鲜",
    "纽西兰":"新西兰",
    "沙乌地阿拉伯":"沙特阿拉伯",
    "实质经济": "实体经济",
    "三大动能": "三驾马车",
    "中共三中全会": "三中全会",
    "美国与中国共产党战略竞争特别委员会": "美中战略竞争特别委员会",
    "中华民国":"台湾当局"
}




WEEKDAY_PATTERN = re.compile(r'(上|这|本|下)(?:个)?周([一二三四五六日天])|(?:上|这|本|下)(?:个)?星期([一二三四五六日天])|周([一二三四五六日天])|星期([一二三四五六日天])')

weekday_mapping = {
    '一': 0,  # 星期一
    '二': 1,  # 星期二
    '三': 2,  # 星期三
    '四': 3,  # 星期四
    '五': 4,  # 星期五
    '六': 5,  # 星期六
    '日': 6,  # 星期日
    '天': 6   # 星期天（星期日的另一种表达）
}

# 时间限定词映射
time_modifier_mapping = {
    '上': -1,  # 上周
    '这': 0,   # 这周/本周
    '本': 0,   # 本周
    '下': 1    # 下周
}

DATE_REFERENCE_PATTERN = re.compile(r'(今日|今天|明日|明天|昨日|昨天|前日|前天|后日|后天|大前天|大后天)')

# 时间指代词映射
date_reference_mapping = {
    '今日': 0,
    '今天': 0,
    '明日': 1,
    '明天': 1,
    '昨日': -1,
    '昨天': -1,
    '前日': -1,
    '前天': -2,
    '后日': 1,
    '后天': 2,
    '大前天': -3,
    '大后天': 3
}

def text_processor(text, reference_date=None):
    """
    处理文本，进行台湾媒体用语编辑和日期替换，并输出准确性检查意见
    
    参数:
        text (str): 需要处理的文本
        reference_date (datetime, optional): 参考日期，用于周几替换，默认为当前日期
        
    返回:
        dict: 包含准确性检查意见的JSON对象
    """
    if not text:
        return {
            "reason": "输入文本为空",
        }
    

    # 初始化结果
    result = {
        "original_text": text,
        "processed_text": text,
        "modifications": [],
        "reason": "",
    }
    
    # 设置参考日期，默认为当前日期
    if reference_date is None:
        reference_date = datetime.now()
    
    # 1. 台湾媒体用语处理        
        processed_text = result["processed_text"]
        for tw_term, cn_term in word_mapping.items():
            if tw_term in processed_text:
                processed_text = processed_text.replace(tw_term, cn_term)
                result["modifications"].append({
                    "type": "taiwan_term",
                    "original": tw_term,
                    "replacement": cn_term
                })
                
        result["processed_text"] = processed_text
    
    # 2. 周几添加日期注释（修改版）
    current_text_for_date_processing = result["processed_text"]
    weekday_matches = list(WEEKDAY_PATTERN.finditer(current_text_for_date_processing))
    
    # 从后往前处理，避免位置偏移问题
    temp_processed_text_for_dates = current_text_for_date_processing 
    for match in reversed(weekday_matches):
        # 提取时间限定词和周几字符
        time_modifier = None
        weekday_char = None
        
        # 检查不同的捕获组
        if match.group(1) and match.group(2):  # (上|这|本|下)周([一二三四五六日天])
            time_modifier = match.group(1)
            weekday_char = match.group(2)
        elif match.group(1) and match.group(3):  # (上|这|本|下)星期([一二三四五六日天])
            time_modifier = match.group(1)
            weekday_char = match.group(3)
        elif match.group(4):  # 周([一二三四五六日天])
            weekday_char = match.group(4)
        elif match.group(5):  # 星期([一二三四五六日天])
            weekday_char = match.group(5)
        
        if weekday_char:
            weekday_num = weekday_mapping.get(weekday_char)
            
            if weekday_num is not None:
                # 计算目标日期
                target_date = calculate_target_date(reference_date, weekday_num, time_modifier)
                
                # 格式化日期，如"5月22日"
                date_str = f"{target_date.month}月{target_date.day}日"
                
                # 在原文本后添加括号注释，而不是替换
                original_text = match.group(0)
                annotated_text = f"{original_text}({date_str})"
                temp_processed_text_for_dates = temp_processed_text_for_dates.replace(original_text, annotated_text, 1)
                
                result["modifications"].append({
                    "type": "date_annotation",
                    "original": original_text,
                    "replacement": annotated_text
                })
    
    result["processed_text"] = temp_processed_text_for_dates


    current_text_for_date_ref = result["processed_text"]
    date_ref_matches = list(DATE_REFERENCE_PATTERN.finditer(current_text_for_date_ref))
    
    # 从后往前处理，避免位置偏移问题
    temp_processed_text_for_date_ref = current_text_for_date_ref
    for match in reversed(date_ref_matches):
        date_ref_word = match.group(1)
        
        if date_ref_word in date_reference_mapping:
            days_offset = date_reference_mapping[date_ref_word]
            target_date = reference_date + timedelta(days=days_offset)
            
            # 格式化日期，如"5月22日"
            date_str = f"{target_date.month}月{target_date.day}日"
            
            # 在原文本后添加括号注释
            original_text = match.group(0)
            annotated_text = f"{original_text}({date_str})"
            temp_processed_text_for_date_ref = temp_processed_text_for_date_ref[:match.start()] + annotated_text + temp_processed_text_for_date_ref[match.end():]
            
            result["modifications"].append({
                "type": "date_reference_annotation",
                "original": original_text,
                "replacement": annotated_text
            })
    
    result["processed_text"] = temp_processed_text_for_date_ref
    
    # 3.股票代码检测和移除
    stock_code_pattern = r'(?:\d{4,6}\.(?:SH|SZ|HK)|[A-Z]{1,4}\.[A-Z]{1,3})'
    
    # 查找所有股票代码（仅支持A股、港股）
    stock_matches = list(re.finditer(stock_code_pattern, result["processed_text"]))
    
    # 记录修改并移除股票代码
    for match in reversed(stock_matches):  # 反向处理避免索引问题
        stock_code = match.group(0)
        # 检查股票代码前后是否有逗号和空格，一并移除
        start = match.start()
        end = match.end()
        
        # 向前查找逗号和空格
        while start > 0 and result["processed_text"][start-1] in '，, ':
            start -= 1
        
        # 向后查找逗号和空格
        while end < len(result["processed_text"]) and result["processed_text"][end] in '，, ':
            end += 1
            
        result["processed_text"] = result["processed_text"][:start] + result["processed_text"][end:]
        
        # 记录修改
        result["modifications"].append({
            "type": "stock_code",
            "original": stock_code,
            "replacement": ""
        })
    
    # 4. 检查并移除空括号和仅包含无意义符号的括号
    # 定义无意义符号：空白字符、标点符号、分隔符等
    meaningless_chars = r'[\s，,、；;：:！!？?。.\-—_/\\|\*\+\=\~\`\^\&\%\$\#\@]'
    # 匹配括号内只包含无意义符号的情况
    empty_brackets_pattern = rf'[\(（]({meaningless_chars}*)[\)）]'
    result["processed_text"] = re.sub(empty_brackets_pattern, '', result["processed_text"])
    
    # 5. 准确性检查
    if result["modifications"]:
        result["reason"] = "文本中包含需要修改的内容"

    else:
        result["reason"] = "文本内容准确，无需修改"
    
    print(json.dumps(result, ensure_ascii=False, indent=2))

    return result["processed_text"]



def calculate_target_date(reference_date, target_weekday_num, time_modifier=None):
    """
    根据参考日期、目标周几和时间限定词计算目标日期
    
    参数:
        reference_date: 参考日期
        target_weekday_num: 目标周几的数字（0-6，0为周一）
        time_modifier: 时间限定词（'上'、'这'/'本'、'下'，或None）
    
    返回:
        datetime: 计算出的目标日期
    """
    current_weekday = reference_date.weekday()
    
    if time_modifier is None:
        # 没有时间限定词时，始终指向本周的对应日期（即使已经过去）
        days_diff = target_weekday_num - current_weekday
        return reference_date + timedelta(days=days_diff)
    else:
        # 有时间限定词
        week_offset = time_modifier_mapping.get(time_modifier, 0)
        
        if time_modifier in ['这', '本']:
            # 本周：找到本周内的目标日期
            days_diff = target_weekday_num - current_weekday
            return reference_date + timedelta(days=days_diff)
        else:
            # 上周或下周：先计算到目标周，再找到目标日期
            # 计算到本周目标日期的天数差
            days_to_target_in_current_week = target_weekday_num - current_weekday
            # 加上周偏移
            total_days = days_to_target_in_current_week + (week_offset * 7)
            return reference_date + timedelta(days=total_days)


if __name__ == "__main__":
    content = "今日，上证指数（000001.SH）的开盘价是3450点，收盘价是3455点。"
    result = text_processor(content)
    print(result)

