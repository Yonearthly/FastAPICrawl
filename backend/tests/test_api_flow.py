def register_admin(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "admin",
            "email": "admin@example.com",
            "password": "StrongPass123",
            "full_name": "测试管理员",
        },
    )
    assert response.status_code == 201
    assert response.json()["is_admin"] is True

    login = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "StrongPass123"},
    )
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_complete_user_news_favorite_history_flow(client):
    headers = register_admin(client)

    profile = client.patch(
        "/api/v1/auth/me",
        headers=headers,
        json={"full_name": "已更新管理员"},
    )
    assert profile.status_code == 200
    assert profile.json()["full_name"] == "已更新管理员"

    created = client.post(
        "/api/v1/news",
        headers=headers,
        json={
            "title": "用于自动化测试的新浪新闻",
            "content": "这是一段足够长的新闻正文，用于验证新闻发布、详情、收藏和浏览历史功能。",
            "category": "国内",
            "source_name": "新浪新闻",
            "source_url": "https://news.sina.com.cn/c/2026-09-09/doc-test0001.shtml?from=track",
        },
    )
    assert created.status_code == 201
    news_id = created.json()["id"]
    assert created.json()["source_url"].endswith("doc-test0001.shtml")

    listing = client.get("/api/v1/news", params={"keyword": "自动化测试"})
    assert listing.status_code == 200
    assert listing.json()["total"] == 1

    detail = client.get(f"/api/v1/news/{news_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["click_count"] == 1

    favorite = client.post(f"/api/v1/news/{news_id}/favorite", headers=headers)
    assert favorite.status_code == 201
    favorites = client.get("/api/v1/news/favorites", headers=headers)
    assert favorites.status_code == 200
    assert favorites.json()[0]["news"]["id"] == news_id

    history = client.get("/api/v1/news/history", headers=headers)
    assert history.status_code == 200
    assert history.json()[0]["news"]["id"] == news_id
    assert history.json()[0]["view_count"] == 1

    removed = client.delete(f"/api/v1/news/{news_id}/favorite", headers=headers)
    assert removed.status_code == 204
    deleted = client.delete(f"/api/v1/news/{news_id}", headers=headers)
    assert deleted.status_code == 204


def test_duplicate_source_url_is_rejected(client):
    headers = register_admin(client)
    payload = {
        "title": "重复测试新闻",
        "content": "用于确认数据库唯一索引能够阻止同一新浪新闻被重复写入。",
        "source_url": "https://news.sina.com.cn/w/2026-09-09/doc-duplicate.shtml",
    }
    assert client.post("/api/v1/news", headers=headers, json=payload).status_code == 201
    duplicate = client.post("/api/v1/news", headers=headers, json=payload)
    assert duplicate.status_code == 409


def test_ai_summary_requires_reserved_key(client):
    headers = register_admin(client)
    created = client.post(
        "/api/v1/news",
        headers=headers,
        json={
            "title": "AI 摘要密钥测试",
            "content": "当环境变量尚未填写密钥时，接口应返回清晰的配置提示，而不是导致服务崩溃。",
            "source_url": "https://news.sina.com.cn/c/2026-09-09/doc-ai-key.shtml",
        },
    )
    response = client.post(f"/api/v1/news/{created.json()['id']}/ai-summary", headers=headers)
    assert response.status_code == 503
    assert "OPENAI_API_KEY" in response.json()["detail"]
