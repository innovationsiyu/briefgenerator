def interpret_article(
        system_prompt: str,
        processed_text: str) -> str:
    """
    模拟大模型对文章的解读（实际调用大模型API的过程省略）

    参数:
        system_prompt (str): 系统级提示词，定义模型的角色和任务要求
        user_prompt   (str): 用户提供的提示词，包含待解读的文章内容或具体要求

    返回:
        article_interpretation: 模型生成的解读结果文本
    """
    # return


# 使用示例
if __name__ == "__main__":
    interpret_article("system_prompt", "source_article")


#json格式不解析，直接把大语言模型的json解读当作一个整体输入给下一个环节