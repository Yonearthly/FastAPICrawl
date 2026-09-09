from app.services.crawler import (
    canonicalize_url,
    is_sina_article_url,
    parse_article,
    url_fingerprint,
)


def test_canonical_url_removes_tracking_and_fragment():
    first = "https://news.sina.com.cn/c/2026-09-09/doc-demo.shtml?from=wap#comments"
    second = "https://news.sina.com.cn/c/2026-09-09/doc-demo.shtml"
    assert canonicalize_url(first) == second
    assert url_fingerprint(first) == url_fingerprint(second)


def test_only_sina_article_urls_are_accepted():
    assert is_sina_article_url("https://news.sina.com.cn/w/2026-09-09/doc-inirensh4081713.shtml")
    assert not is_sina_article_url("https://news.sina.com.cn/world/")
    assert not is_sina_article_url("https://example.com/2026-09-09/doc-demo.shtml")


def test_parse_current_sina_article_structure():
    html = """
    <html><head>
      <meta property="og:title" content="测试新闻标题" />
      <meta property="article:published_time" content="2026-09-09 16:32:57" />
      <meta property="og:description" content="新闻描述" />
      <meta property="og:image" content="https://example.com/image.jpg" />
    </head><body>
      <div class="date-source"><a class="source">新华社</a></div>
      <div class="article" id="article">
        <p>第一段包含新闻的主要事实与事件背景，长度足够用于正文解析。</p>
        <p>第二段补充事件进展和最终结果，确保解析器能够合并多个段落。</p>
        <p class="show_author">责任编辑：测试</p>
      </div>
    </body></html>
    """
    article = parse_article(html, "https://news.sina.com.cn/c/2026-09-09/doc-demo.shtml")
    assert article is not None
    assert article.title == "测试新闻标题"
    assert article.category == "国内"
    assert article.source_author == "新华社"
    assert "责任编辑" not in article.content
