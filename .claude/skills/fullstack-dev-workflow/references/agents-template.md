# AGENTS.md - AI Agent 开发指导文档

> 本文档由 fullstack-dev-workflow skill 自动生成，用于指导AI Agent（Claude Code、Cursor等）进行项目开发。所有技术栈和规范已锁定，AI Agent必须严格遵守。

---

## 项目概述

| 属性 | 内容 |
|------|------|
| 项目名称 | 【项目名称】 |
| 项目类型 | 【Web应用/API服务/AI应用/移动应用/工具类】 |
| 项目规模 | 【小型/中型/大型/超大型】 |
| 核心目标 | 【项目核心目标描述】 |
| 文档生成时间 | 【YYYY-MM-DD HH:mm:ss】 |

---

## 技术栈锁定（禁止更改）

> ⚠️ 以下技术栈已锁定，AI Agent不得擅自更改版本或替换技术方案

### 前端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| 框架 | 【框架名】v【版本号】 | 【用途说明】 |
| 语言 | 【TypeScript/JavaScript】v【版本号】 | 【用途说明】 |
| 状态管理 | 【Redux/Zustand/Pinia/Vuex】 | 【用途说明】 |
| UI组件库 | 【Ant Design/Shadcn/Tailwind CSS】 | 【用途说明】 |
| CSS方案 | 【Tailwind/CSS Modules/Styled-components】 | 【用途说明】 |
| 构建工具 | 【Vite/Next.js内置/Webpack】 | 【用途说明】 |
| 测试框架 | 【Jest/Vitest/Playwright】 | 【用途说明】 |

### 后端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| 框架 | 【框架名】v【版本号】 | 【用途说明】 |
| 语言 | 【Python/Java/TypeScript/Go】v【版本号】 | 【用途说明】 |
| 数据库 | 【PostgreSQL/MySQL/MongoDB】v【版本号】 | 【用途说明】 |
| ORM | 【Prisma/TypeORM/Drizzle/SQLAlchemy】 | 【用途说明】 |
| 缓存 | 【Redis】v【版本号】 | 【用途说明】 |
| 测试框架 | 【pytest/Jest/Vitest】 | 【用途说明】 |

### AI技术栈（如涉及）

| 技术 | 版本 | 用途 |
|------|------|------|
| Agent框架 | 【LangChain/LangGraph/AutoGen】v【版本号】 | 【用途说明】 |
| 向量数据库 | 【Pinecone/Milvus/Weaviate】 | 【用途说明】 |
| LLM接口 | 【OpenAI/Anthropic/本地模型】 | 【用途说明】 |
| Embedding模型 | 【text-embedding-3-small/其他】 | 【用途说明】 |

### 基础设施

| 技术 | 版本 | 用途 |
|------|------|------|
| 容器化 | Docker v【版本号】 + Docker Compose | 部署标准化 |
| 版本控制 | Git + GitHub/GitLab | 代码版本管理 |
| CI/CD | GitHub Actions/GitLab CI | 自动化部署 |
| 监控 | Prometheus + Grafana/其他 | 可观测性 |

---

## 架构模式

### 整体架构

| 属性 | 内容 |
|------|------|
| 架构模式 | 【单体分层/前后端分离/微服务/Serverless/Agent编排】 |
| 选择理由 | 【选择该架构的理由】 |

### 分层结构

```
【根据实际架构填写，示例】
├── 表现层 (Presentation Layer)
│   ├── 前端页面组件
│   └── API Controller
├── 业务层 (Business Layer)
│   ├── 服务层 (Service)
│   └── 领域逻辑 (Domain)
├── 数据层 (Data Layer)
│   ├── 数据访问层 (Repository/DAO)
│   └── 数据模型 (Model/Entity)
└── 基础设施层 (Infrastructure Layer)
    ├── 数据库连接
    ├── 缓存服务
    └── 外部服务集成
```

### 模块划分

| 模块名称 | 职责 | 核心文件路径 |
|----------|------|--------------|
| 【模块1】 | 【职责描述】 | 【路径】 |
| 【模块2】 | 【职责描述】 | 【路径】 |

---

## 编码规范

### 命名规范

| 类别 | 规范 | 示例 |
|------|------|------|
| 文件命名 | kebab-case | `user-service.ts`, `api-handler.go` |
| 变量命名 | camelCase | `userInfo`, `requestData` |
| 常量命名 | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT`, `API_BASE_URL` |
| 类/组件命名 | PascalCase | `UserService`, `UserProfile` |
| 接口命名 | I前缀或无前缀 | `IUserService` 或 `UserService` |
| 函数命名 | camelCase + 动词开头 | `getUserById`, `createOrder` |
| 数据库表名 | snake_case（复数） | `users`, `order_items` |
| 数据库字段 | snake_case | `created_at`, `user_id` |

### 目录规范

```
【根据实际项目填写，示例】
src/
├── frontend/                  # 前端代码
│   ├── components/           # 公共组件
│   │   ├── ui/              # 基础UI组件
│   │   └── business/        # 业务组件
│   ├── pages/               # 页面组件
│   ├── hooks/               # 自定义hooks
│   ├── services/            # API服务层
│   ├── stores/              # 状态管理
│   ├── utils/               # 工具函数
│   └── types/               # 类型定义
├── backend/                  # 后端代码
│   ├── controllers/         # 控制器层
│   ├── services/            # 服务层
│   ├── models/              # 数据模型
│   ├── repositories/        # 数据访问层
│   ├── middlewares/         # 中间件
│   ├── utils/               # 工具函数
│   └── types/               # 类型定义
└── shared/                   # 前后端共享代码
    ├── types/               # 共享类型
    └── constants/           # 共享常量
```

### 代码风格

| 配置项 | 配置值 |
|--------|--------|
| 格式化工具 | 【ESLint + Prettier / Black / gofmt】 |
| 配置文件路径 | 【.eslintrc.js / pyproject.toml / .golangci.yml】 |
| 自动格式化 | 开启（保存时自动格式化） |
| pre-commit hook | 【husky / pre-commit】 |

### 注释规范

| 类型 | 规范 |
|------|------|
| 文件头注释 | 文件功能说明、作者、创建时间 |
| 函数注释 | 参数说明、返回值说明、异常说明 |
| 复杂逻辑注释 | 必须添加说明注释 |
| TODO注释 | 格式：`// TODO: [描述] - [负责人] - [日期]` |

---

## API规范

### 路由规范

| 规范项 | 规范内容 |
|--------|----------|
| 版本控制 | URL路径版本化 `/api/v1/` |
| 资源命名 | 复数名词 `/api/v1/users`, `/api/v1/orders` |
| HTTP方法 | GET查询, POST创建, PUT全量更新, PATCH部分更新, DELETE删除 |

### 响应格式

```json
// 成功响应
{
  "code": 0,
  "message": "success",
  "data": {
    // 具体数据
  }
}

// 失败响应
{
  "code": 10001,
  "message": "用户不存在",
  "data": null
}
```

### 认证方式

| 认证类型 | 说明 |
|----------|------|
| 认证方式 | 【JWT / OAuth2 / Session】 |
| Token位置 | Authorization Header: `Bearer <token>` |
| Token过期时间 | 【时间】 |
| 刷新机制 | 【刷新Token的方式】 |

### 错误码体系

| 错误码范围 | 含义 |
|------------|------|
| 0 | 成功 |
| 10000-19999 | 通用错误（参数错误、系统错误等） |
| 20000-29999 | 用户相关错误（登录失败、权限不足等） |
| 30000-39999 | 业务错误（订单失败、库存不足等） |

---

## 安全规范

### 传输安全

| 规范项 | 要求 |
|--------|------|
| HTTPS | 强制HTTPS，禁止HTTP |
| 敏感数据传输 | 加密传输 |

### 认证授权

| 规范项 | 要求 |
|--------|------|
| 密码存储 | bcrypt / argon2 加密存储 |
| 密码强度 | 最小8位，包含大小写字母和数字 |
| 登录限制 | 失败N次后锁定账户 |

### 输入校验

| 规范项 | 要求 |
|--------|------|
| 参数类型校验 | 严格类型校验 |
| 参数范围校验 | 必须校验范围 |
| SQL注入防护 | ORM参数化查询，禁止字符串拼接 |
| XSS防护 | 输出编码 + CSP策略 |
| CSRF防护 | Token校验 |

### 日志安全

| 规范项 | 要求 |
|--------|------|
| 敏感字段脱敏 | 密码、token、身份证等不记录 |
| 日志级别 | ERROR/WARN/INFO/DEBUG |
| 日志保留 | 【保留天数】 |

---

## 数据库规范

### 表设计规范

| 规范项 | 要求 |
|--------|------|
| 主键 | 自增ID或UUID，统一命名为 `id` |
| 时间字段 | `created_at`, `updated_at`, `deleted_at`（软删除） |
| 状态字段 | 使用枚举或数字状态码 |
| 外键命名 | `{关联表}_id` |

### 索引规范

| 规范项 | 要求 |
|--------|------|
| 主键索引 | 自动创建 |
| 唯一索引 | 唯一约束字段 |
| 普通索引 | 高频查询字段 |
| 组合索引 | 多字段组合查询，注意字段顺序 |

### 查询规范

| 规范项 | 要求 |
|--------|------|
| 禁止操作 | 禁止 `SELECT *`，禁止无WHERE的UPDATE/DELETE |
| 分页查询 | 必须使用分页，默认每页20条 |
| 大批量操作 | 分批处理，每批不超过1000条 |

---

## 测试规范

### 测试覆盖要求

| 测试类型 | 覆盖率要求 |
|----------|------------|
| 单元测试 | 核心业务逻辑100%覆盖 |
| 集成测试 | 主要接口100%覆盖 |
| E2E测试 | 核心用户流程覆盖 |

### 测试命名规范

| 测试类型 | 命名规范 |
|----------|----------|
| 单元测试 | `{文件名}.test.{ts/js/py/go}` |
| 集成测试 | `{文件名}.integration.test.{ext}` |
| E2E测试 | `{功能名}.e2e.test.{ext}` |

---

## 文档驱动开发规范

### 核心原则

| 原则 | 说明 |
|------|------|
| 文档先行 | 无文档不开发，无设计不编码 |
| 索引闭环 | 每层级目录必须有 `index.md` |
| 变更备份 | 任何修改前必须触发全量快照备份 |
| 关联同步 | 需求变更后必须同步所有下游文档 |
| 一致性校验 | 每环节完成后必须AI自检 |

### 文档目录结构

```
docs/
├── index.md                    # 根索引文档
├── doc-dependency-matrix.yaml  # 依赖矩阵
├── 00-requirements/            # 需求文档
├── 01-architecture/            # 架构设计
├── 02-frontend-design/         # 前端设计
├── 03-backend-design/          # 后端设计
└── 04-test-acceptance/         # 测试验收
```

### ID命名规范

| ID类型 | 格式 | 示例 |
|--------|------|------|
| 需求ID | REQ-{模块}-{序号} | REQ-USER-001 |
| 接口ID | API-{模块}-{序号} | API-USER-001 |
| 页面ID | PAGE-{模块}-{序号} | PAGE-USER-001 |
| 变更单号 | CHG-{日期}-{序号} | CHG-20260409-001 |

---

## 禁止事项

> ⚠️ AI Agent必须严格遵守以下禁止事项，违反将导致流程终止

1. **禁止擅自更改技术栈**：所有技术选型已锁定，不得替换框架、库版本
2. **禁止超范围开发**：所有开发必须严格限定在需求文档范围内
3. **禁止自由发挥**：所有代码必须基于设计文档，不得自行设计
4. **禁止跳过文档**：禁止先写代码后补文档
5. **禁止跨环节执行**：上一环节未通过校验不得进入下一环节
6. **禁止修改历史版本**：历史备份文件只读，不得修改
7. **禁止无备份修改**：任何文档/代码修改前必须先备份

---

## 开发流程速查

### 新功能开发流程

```
1. 需求文档化（阶段1）→ prd.md, srs.md
2. 架构设计（阶段2.1）→ system-architecture.md
3. 前端设计（阶段2.2）→ 页面设计文档
4. 后端设计（阶段2.3）→ 接口设计文档
5. 代码开发（阶段3）→ 基于设计文档编码
6. 测试验收（阶段4）→ 测试报告
```

### 需求变更流程

```
1. 变更申请 → 分配变更单号
2. 全量备份 → .version-history/
3. 影响分析 → 依赖矩阵查询
4. 文档更新 → 按优先级同步
5. 一致性校验 → 校验报告
6. 代码变更 → 基于新文档编码
```

---

## 常用命令

### 项目启动

```bash
# 前端
【前端启动命令，如 npm run dev】

# 后端
【后端启动命令，如 npm run start:dev】

# 数据库
【数据库启动命令，如 docker-compose up -d db】
```

### 测试命令

```bash
# 单元测试
【测试命令，如 npm run test】

# 测试覆盖率
【覆盖率命令，如 npm run test:cov】

# E2E测试
【E2E测试命令，如 npm run test:e2e】
```

### 构建/部署

```bash
# 构建
【构建命令，如 npm run build】

# Docker构建
【Docker命令，如 docker-compose up --build】
```

---

**文档版本**: v1.0.0
**最后更新**: 【YYYY-MM-DD】
**维护者**: AI Agent 自动生成