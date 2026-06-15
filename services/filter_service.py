from urllib.parse import urlparse


BLACK_WORDS = [

    "众测",
    "评测",
    "专题",
    "直播",
    "活动",

    "登录",
    "注册",

    "首页",
    "关于",

    "English",
    "下载",

    "客户端",
    "微博",

    "视频",
    "图片",

    "博客",
    "邮箱"

]


def is_valid_news(item):

    title = item.get(
        "title",
        ""
    ).strip()

    url = item.get(
        "url",
        ""
    ).strip()

    if not title:
        return False

    if not url:
        return False

    # 标题长度

    if len(title) < 8:
        return False

    if len(title) > 80:
        return False

    # 黑名单

    for word in BLACK_WORDS:

        if word in title:
            return False

    # 过滤 javascript

    if url.startswith(
        "javascript"
    ):
        return False

    # 过滤锚点

    if url.startswith("#"):
        return False

    # 必须有域名

    parsed = urlparse(url)

    if not parsed.netloc:
        return False

    return True