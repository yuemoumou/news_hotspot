import requests

from config import DEEPSEEK_API_KEY


def call_deepseek(prompt):

    try:

        response = requests.post(
            "https://api.deepseek.com/chat/completions",

            headers={
                "Authorization":
                f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type":
                "application/json"
            },

            json={
                "model":"deepseek-chat",

                "messages":[
                    {
                        "role":"user",
                        "content":prompt
                    }
                ],

                "temperature":0.3
            },

            timeout=60
        )

        result = response.json()

        return result["choices"][0]["message"]["content"]

    except Exception as e:

        print("DeepSeek错误:", e)

        return ""
    
def generate_ai_summary(title):

    prompt = f"""
请将下面新闻标题总结为一句话：

{title}

直接返回摘要。
"""

    return call_deepseek(prompt)


def classify_news(title):

    prompt = f"""
新闻分类：

科技
AI
财经
汽车
手机
互联网
其他

标题：

{title}

只返回分类名称。
"""

    return call_deepseek(prompt)


def extract_keywords(title):

    prompt = f"""
提取3个关键词：

{title}

格式：

关键词1,关键词2,关键词3
"""

    return call_deepseek(prompt)


def analyze_sentiment(title):

    prompt = f"""
判断新闻情绪：

正面
中性
负面

标题：

{title}

只返回一个词。
"""

    return call_deepseek(prompt)

def analyze_news(title):

    prompt = f"""
请分析下面新闻标题。

标题：
{title}

返回JSON：

{{
    "summary":"",
    "category":"",
    "keywords":"",
    "sentiment":""
}}

分类只能是：

科技
AI
财经
汽车
手机
互联网
其他

情感只能是：

正面
中性
负面

只返回JSON。
"""

    return call_deepseek(prompt)

def analyze_news(title):

    prompt = f"""
请分析下面新闻标题：

{title}

返回JSON：

{{
    "summary":"",
    "category":"",
    "keywords":"",
    "sentiment":""
}}

分类只能是：

科技
AI
财经
汽车
手机
互联网
其他

情感只能是：

正面
中性
负面

只返回JSON。
"""

    return call_deepseek(
        prompt
    )