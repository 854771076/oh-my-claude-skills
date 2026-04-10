# 技术栈调研矩阵

本文档提供各技术栈的调研对比矩阵，用于阶段-1技术选型决策。

---

## 前端技术栈调研矩阵

| 主语言 | 框架选项 | 适用场景 | 推荐指数 |
|--------|----------|----------|----------|
| TypeScript | Next.js (App Router) | SSR/SSG、SEO优化、企业级Web | ★★★★★ |
| TypeScript | Nuxt.js | Vue生态、SSR/SSG | ★★★★☆ |
| TypeScript | React + Vite | SPA、快速开发 | ★★★★☆ |
| TypeScript | Vue 3 + Vite | SPA、渐进式开发 | ★★★★☆ |
| TypeScript | Svelte/SvelteKit | 轻量、高性能 | ★★★☆☆ |
| JavaScript | React + Vite | 传统JS项目 | ★★★☆☆ |
| JavaScript | Vue 3 + Vite | 传统JS项目 | ★★★☆☆ |

---

## 后端技术栈调研矩阵

| 主语言 | 框架选项 | 适用场景 | 推荐指数 |
|--------|----------|----------|----------|
| Python | FastAPI | 高性能API、异步、自动文档 | ★★★★★ |
| Python | Flask | 轻量、灵活、快速原型 | ★★★★☆ |
| Python | Django | 全功能、ORM、企业级 | ★★★★☆ |
| Java | Spring Boot | 企业级、微服务生态 | ★★★★★ |
| Java | Quarkus | 云原生、低内存 | ★★★☆☆ |
| TypeScript | NestJS | 企业级、模块化、Angular风格 | ★★★★★ |
| TypeScript | Express/Fastify | 轻量、灵活 | ★★★★☆ |
| Go | Gin/Echo | 高性能、微服务 | ★★★★★ |
| Go | Fiber | Express风格、高性能 | ★★★★☆ |
| Rust | Actix-web | 极致性能、安全 | ★★★☆☆ |
| C# | ASP.NET Core | 企业级、微软生态 | ★★★★☆ |

---

## AI工作流技术栈调研矩阵

| 主语言 | 框架选项 | 适用场景 | 推荐指数 |
|--------|----------|----------|----------|
| Python | LangChain | LLM应用、链式调用 | ★★★★★ |
| Python | LangGraph | Agent工作流、状态管理 | ★★★★★ |
| Python | AutoGen | 多Agent协作 | ★★★★☆ |
| Python | CrewAI | Agent团队编排 | ★★★★☆ |
| TypeScript | LangChain.js | TypeScript生态AI应用 | ★★★★☆ |
| Python | LlamaIndex | RAG、文档索引 | ★★★★★ |
| Python | Haystack | NLP管道、RAG | ★★★★☆ |

---

## 数据存储技术栈调研矩阵

| 类型 | 技术选项 | 适用场景 | 推荐指数 |
|------|----------|----------|----------|
| 关系型 | PostgreSQL | 企业级、复杂查询、扩展性强 | ★★★★★ |
| 关系型 | MySQL | 传统、生态成熟 | ★★★★☆ |
| 关系型 | SQLite | 小型、嵌入式、开发测试 | ★★★☆☆ |
| 文档型 | MongoDB | 无固定Schema、高扩展 | ★★★★☆ |
| 缓存 | Redis | 高速缓存、会话、队列 | ★★★★★ |
| 向量库 | Pinecone/Milvus/Weaviate | AI应用、向量检索 | ★★★★★ |
| 搜索 | Elasticsearch | 全文搜索、日志分析 | ★★★★☆ |

---

## 其他技术栈调研

| 类别 | 技术选项 | 适用场景 |
|------|----------|----------|
| 消息队列 | RabbitMQ / Kafka / Redis Streams | 异步处理、事件驱动 |
| 容器化 | Docker / Docker Compose | 部署标准化 |
| CI/CD | GitHub Actions / GitLab CI / Jenkins | 自动化部署 |
| 监控 | Prometheus + Grafana / ELK | 可观测性 |
| 测试 | Jest / Vitest / pytest / Playwright | 自动化测试 |

---

## 主语言选择指南

| 选择项 | 子选项 | 适用场景 |
|--------|--------|----------|
| 前端主导 | JavaScript / TypeScript | Web应用、移动应用前端 |
| 后端主导 | Python / Java / JavaScript/TypeScript / Go / Rust / C# | API服务、微服务、AI应用后端 |
| AI工作流 | Python / JavaScript/TypeScript | AI Agent、RAG、LLM应用 |
| 全栈统一 | TypeScript（前后端统一） | 快速迭代、中小型项目 |
| 其他 | 用户自定义 | 特殊需求场景 |

---

## 项目规模与架构模式匹配

| 项目类型 | 推荐架构 | 说明 |
|----------|----------|------|
| 小型SPA | 单体分层 | 简单直接，快速交付 |
| 中型Web | 前后端分离 + 模块化 | 清晰边界，易于扩展 |
| 大型企业 | 微服务 + 领域驱动(DDD) | 高扩展，团队协作友好 |
| AI应用 | Agent编排 + RAG管道 | 工作流驱动，知识检索增强 |
| API服务 | RESTful + 版本控制 | 标准化接口，易于集成 |

---

## 设计规范调研

| 规范类别 | 推荐方案 |
|----------|----------|
| 代码风格 | ESLint + Prettier / Black / gofmt |
| 命名规范 | 文件：kebab-case，变量：camelCase，类：PascalCase |
| 目录规范 | 按功能/领域分层，src/[domain]/[layer] |
| API规范 | OpenAPI 3.0，版本化路由 /api/v1/ |
| 安全规范 | JWT/OAuth2，HTTPS强制，输入校验 |