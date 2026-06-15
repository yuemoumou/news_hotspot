"""
新闻自动分类服务
- 规则匹配（关键词 -> 分类）
- 支持 AI 分类 + 规则分类双轨
- 批量分类
"""
from database.db import get_conn

# ============================================================
# 分类规则表
# ============================================================

CATEGORY_RULES = {
    "AI": [
        "OpenAI", "GPT", "ChatGPT", "Claude", "Gemini", "DeepSeek",
        "大模型", "大语言模型", "LLM", "AIGC", "AGI", "人工智能",
        "机器学习", "深度学习", "神经网络", "Transformer", "Copilot",
        "Sora", "DALL-E", "Midjourney", "Stable Diffusion",
        "文心一言", "通义千问", "讯飞星火", "Llama", "Copilot",
        "多模态", "强化学习", "自然语言", "计算机视觉", "语音识别",
        "生成式", "幻觉", "对齐", "微调", "预训练", "推理",
        "token", "Tokens", "GPU算力", "训练集群"
    ],
    "苹果": [
        "苹果", "Apple", "iPhone", "iPad", "Mac", "MacBook",
        "Apple Watch", "Vision Pro", "AirPods", "iOS", "iPadOS",
        "macOS", "watchOS", "tvOS", "Apple Intelligence",
        "M4", "M3", "M2", "A17", "A18", "A16", "WWDC",
        "App Store", "Apple Music", "iCloud", "Siri",
        "库克", "Tim Cook"
    ],
    "微软": [
        "微软", "Microsoft", "Windows", "Azure", "Office",
        "Surface", "Xbox", "GitHub", "Visual Studio",
        "Copilot", "Bing", "Edge", "Teams", "LinkedIn",
        "纳德拉", "Satya Nadella"
    ],
    "谷歌": [
        "谷歌", "Google", "Android", "Chrome", "Pixel",
        "YouTube", "Gmail", "Google Maps", "Google Cloud",
        "DeepMind", "Waymo", "Gemini", "Bard",
        "皮查伊", "Sundar Pichai"
    ],
    "芯片": [
        "芯片", "半导体", "CPU", "GPU", "NPU", "TPU",
        "英伟达", "NVIDIA", "英特尔", "Intel", "AMD",
        "高通", "Qualcomm", "联发科", "MediaTek",
        "台积电", "TSMC", "三星", "Samsung",
        "Arm", "RISC-V", "x86", "光刻机", "EUV",
        "制程", "3nm", "2nm", "5nm", "7nm",
        "CUDA", "TensorRT", "HBM", "显存",
        "摩尔线程", "寒武纪", "海光", "龙芯", "长江存储",
        "ASML", "SK海力士", "美光", "Micron",
        "Blackwell", "Hopper", "GeForce", "RTX"
    ],
    "汽车": [
        "汽车", "电动车", "电动汽车", "新能源车", "智能驾驶",
        "自动驾驶", "FSD", "激光雷达", "固态电池",
        "特斯拉", "Tesla", "Model Y", "Model 3", "Cybertruck",
        "比亚迪", "BYD", "蔚来", "NIO", "小鹏", "XPeng",
        "理想", "Li Auto", "小米汽车", "华为问界",
        "宁德时代", "CATL", "充电桩", "换电",
        "马斯克", "Elon Musk"
    ],
    "互联网": [
        "互联网", "社交", "电商", "外卖", "短视频", "直播",
        "字节跳动", "抖音", "TikTok", "今日头条",
        "阿里巴巴", "淘宝", "天猫", "阿里云",
        "腾讯", "微信", "QQ", "王者荣耀", "腾讯云",
        "美团", "拼多多", "京东", "小红书", "快手",
        "百度", "B站", "知乎", "微博",
        "马化腾", "张一鸣", "马云"
    ],
    "手机": [
        "手机", "智能手机", "折叠屏", "5G手机",
        "华为", "Mate", "Pura", "鸿蒙", "HarmonyOS",
        "小米", "Xiaomi", "Redmi", "OPPO", "vivo",
        "荣耀", "Honor", "一加", "OnePlus",
        "骁龙", "天玑", "卫星通信"
    ],
    "财经": [
        "股市", "股票", "A股", "港股", "美股", "IPO",
        "融资", "投资", "收购", "并购", "上市",
        "基金", "债券", "期货", "外汇", "加密货币",
        "比特币", "Bitcoin", "以太坊", "区块链",
        "GDP", "经济", "通胀", "加息", "降息",
        "华尔街", "美联储", "央行"
    ],
    "航天": [
        "航天", "火箭", "卫星", "空间站", "探月",
        "SpaceX", "星舰", "Starship", "Falcon",
        "NASA", "CNSA", "中国航天", "北斗",
        "火星", "登月", "星际", "轨道",
        "Blue Origin", "星链", "Starlink"
    ],
    "游戏": [
        "游戏", "电竞", "主机", "PlayStation", "Xbox",
        "Switch", "Steam", "手游", "网游",
        "原神", "崩坏", "王者荣耀", "英雄联盟",
        "赛博朋克", "黑神话", "3A", "独立游戏"
    ]
}


def classify_by_rules(title):
    """
    基于规则的关键词匹配分类
    返回: 分类名称 或 None
    """
    if not title:
        return None

    scores = {}
    for category, keywords in CATEGORY_RULES.items():
        score = 0
        for kw in keywords:
            if kw.lower() in title.lower():
                # 长关键词匹配权重更高
                score += len(kw)
        if score > 0:
            scores[category] = score

    if not scores:
        return None

    # 返回得分最高的分类
    return max(scores, key=scores.get)


def classify_batch(limit=100):
    """
    批量对未分类新闻进行规则分类
    """
    conn = get_conn()

    rows = conn.execute("""
        SELECT id, title
        FROM news
        WHERE (category IS NULL OR category = '')
          AND title IS NOT NULL
          AND title <> ''
        LIMIT ?
    """, (limit,)).fetchall()

    classified = 0
    for row in rows:
        cat = classify_by_rules(row["title"])
        if cat:
            conn.execute("""
                UPDATE news SET category = ? WHERE id = ?
            """, (cat, row["id"]))
            classified += 1

    conn.commit()
    conn.close()
    return classified


def get_category_stats():
    """获取分类统计"""
    conn = get_conn()
    rows = conn.execute("""
        SELECT category, COUNT(*) as cnt
        FROM news
        WHERE category IS NOT NULL AND category <> ''
        GROUP BY category
        ORDER BY cnt DESC
    """).fetchall()
    conn.close()
    return [(r["category"], r["cnt"]) for r in rows]


def get_category_list():
    """获取所有可用分类"""
    return list(CATEGORY_RULES.keys())
