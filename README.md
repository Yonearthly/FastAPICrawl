# AI掘金头条

这是一个按实训任务书完成的全栈新闻系统。后端使用 FastAPI，定时抓取新浪新闻并去重写入数据库；Redis 缓存热点查询；OpenAI 兼容接口生成新闻摘要；Vue 3 前端提供新闻浏览、搜索、收藏、历史、AI 摘要与爬虫管理页面。

## 已实现功能

- 新浪新闻首页、国内、国际频道定时抓取，可通过环境变量扩展入口
- URL 规范化与 SHA-256 指纹预检查，避免重复请求已有文章
- 数据库 `source_url` 与 `url_hash` 双唯一索引，避免并发重复入库
- APScheduler 定时任务，单实例、禁止重入、失败记录可追踪
- 新闻分页、搜索、分类、详情、发布、修改、删除 API
- 用户注册、登录、JWT 鉴权、个人信息接口
- 收藏、取消收藏、浏览历史、个性化推荐
- Redis 列表缓存与缓存失效；Redis 断开时健康接口会显示降级状态
- 通过 `https://api.openai-proxy.org/v1` 调用 OpenAI 兼容模型生成中文摘要
- Swagger UI、Pytest、Dockerfile、Docker Compose、MySQL 与 Redis
- Vue 3 响应式前端和管理员爬虫控制台

## 一键启动

1. 复制环境变量模板，并填写密钥：

   ```powershell
   Copy-Item .env.example .env
   ```

2. 编辑 `.env`，至少设置：

   ```dotenv
   SECRET_KEY=请替换为随机长字符串
   OPENAI_API_KEY=在这里填写密钥
   OPENAI_MODEL=你的模型名称
   ```

3. 启动完整环境：

   ```powershell
   docker compose up --build
   ```

4. 打开：

   - Vue 前端：http://localhost:8080
   - Swagger UI：http://localhost:8000/docs
   - 健康检查：http://localhost:8000/health

系统中注册的第一个用户自动成为管理员，可以在前端“采集管理”页面手动触发爬取。后台默认每 30 分钟增量抓取一次。

## 本地开发

后端：

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

前端：

```powershell
cd frontend
npm install
npm run dev
```

默认使用 `backend/data/news.db`。如本机没有 Redis，新闻接口仍可运行，但 `/health` 会显示缓存未连接；完整实训演示建议使用 Docker Compose。

## 去重策略

1. 删除 URL 片段、跟踪参数和默认端口，并统一主机名与路径。
2. 对规范化 URL 计算 SHA-256 指纹。
3. 发现链接后批量查询已有指纹，仅下载数据库中不存在的文章。
4. 写入时由 `source_url` 和 `url_hash` 唯一约束再次兜底。
5. 调度器设置 `max_instances=1`，进程内锁阻止手动任务与定时任务重叠。

## 测试与规范检查

```powershell
cd backend
pytest -q
ruff check app tests
```

自动化测试覆盖注册登录、新闻 CRUD、收藏/历史以及爬虫 URL 规范化和去重。

## 重要配置

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `OPENAI_BASE_URL` | `https://api.openai-proxy.org/v1` | OpenAI 兼容 API 根地址 |
| `OPENAI_API_KEY` | 空 | 预留的 API 密钥位置 |
| `OPENAI_MODEL` | `gpt-4o-mini` | 代理服务中可用的模型名 |
| `CRAWLER_INTERVAL_MINUTES` | `30` | 定时抓取间隔 |
| `CRAWLER_MAX_ARTICLES` | `30` | 单次最多抓取新文章数 |
| `CRAWLER_ENABLED` | `true` | 是否启动后台定时器 |
| `DATABASE_URL` | SQLite | SQLAlchemy 数据库 URL |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis 地址 |

请将爬取频率控制在合理范围内，并遵守目标网站的使用规则。生产部署时建议将调度器拆为独立进程，避免多 worker 重复启动调度任务；本项目容器按单 worker 运行。

