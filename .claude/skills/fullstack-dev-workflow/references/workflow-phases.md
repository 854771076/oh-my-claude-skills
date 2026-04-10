# 全栈开发工作流阶段详细说明

本文档详细描述各阶段的执行目标、步骤和输出物。

---

## 阶段-1：技术栈调研与选型（新项目专属前置阶段）

### 执行目标

根据用户需求智能调研最适合的技术栈、架构模式、设计规范，输出完整的技术选型报告，为后续项目初始化提供锁定依据。

### 前置输入

用户原始需求描述、项目核心目标、预期规模、团队技术背景（可选）

### 标准执行步骤

#### 步骤1：用户需求解析与项目定位

1. 解析用户原始需求，明确项目类型：
   - Web应用（SPA/MPA/PWA）
   - API服务（RESTful/GraphQL/gRPC）
   - AI应用（AI Agent/RAG/LLM应用）
   - 移动应用（原生/混合/小程序）
   - 工具类/CLI工具
   - 行业解决方案

2. 明确项目规模等级：
   - 小型：单功能/工具类，开发周期<2周
   - 中型：多模块/SaaS产品，开发周期2-8周
   - 大型：企业级解决方案，开发周期>8周
   - 超大型：分布式系统，多团队协作

#### 步骤2：主语言选择交互

**必须通过 AskUserQuestion 工具让用户选择主语言方向**

| 选择项 | 子选项 | 适用场景 |
|--------|--------|----------|
| 前端主导 | JavaScript / TypeScript | Web应用、移动应用前端 |
| 后端主导 | Python / Java / JavaScript/TypeScript / Go / Rust / C# | API服务、微服务、AI应用后端 |
| AI工作流 | Python / JavaScript/TypeScript | AI Agent、RAG、LLM应用 |
| 全栈统一 | TypeScript（前后端统一） | 快速迭代、中小型项目 |
| 其他 | 用户自定义 | 特殊需求场景 |

#### 步骤3：技术栈智能调研（基于用户选择）

参见 [tech-stack-matrix.md](tech-stack-matrix.md) 获取完整调研矩阵。

#### 步骤4：技术选型决策（用户确认）

**基于步骤3调研结果，使用 AskUserQuestion 让用户确认最终技术栈**

输出格式示例：
```
## 技术栈选型方案

### 前端技术栈
- 框架：[选定框架] v[版本号]
- 语言：[TypeScript/JavaScript]
- 状态管理：[Redux/Zustand/Pinia/Vuex]
- UI组件库：[Ant Design/Shadcn/Tailwind CSS]
- 构建工具：[Vite/Next.js内置]

### 后端技术栈
- 框架：[选定框架] v[版本号]
- 语言：[Python/Java/TypeScript/Go]
- 数据库：[PostgreSQL/MySQL/MongoDB]
- ORM：[Prisma/TypeORM/Drizzle/ SQLAlchemy]
- API规范：[RESTful/OpenAPI 3.0]

### AI技术栈（如涉及）
- Agent框架：[LangChain/LangGraph/AutoGen]
- 向量数据库：[Pinecone/Milvus]
- LLM接口：[OpenAI/Anthropic/本地模型]

### 基础设施
- 容器化：Docker + Docker Compose
- 版本控制：Git + GitHub/GitLab
- CI/CD：GitHub Actions
```

#### 步骤5：架构模式与设计规范调研

**架构模式调研矩阵**

| 项目类型 | 推荐架构 | 说明 |
|----------|----------|------|
| 小型SPA | 单体分层 | 简单直接，快速交付 |
| 中型Web | 前后端分离 + 模块化 | 清晰边界，易于扩展 |
| 大型企业 | 微服务 + 领域驱动(DDD) | 高扩展，团队协作友好 |
| AI应用 | Agent编排 + RAG管道 | 工作流驱动，知识检索增强 |
| API服务 | RESTful + 版本控制 | 标准化接口，易于集成 |

**设计规范调研**

| 规范类别 | 推荐方案 |
|----------|----------|
| 代码风格 | ESLint + Prettier / Black / gofmt |
| 命名规范 | 文件：kebab-case，变量：camelCase，类：PascalCase |
| 目录规范 | 按功能/领域分层，src/[domain]/[layer] |
| API规范 | OpenAPI 3.0，版本化路由 /api/v1/ |
| 安全规范 | JWT/OAuth2，HTTPS强制，输入校验 |

#### 步骤6：生成技术选型报告文档

生成 `docs/00-requirements/tech-selection-report.md`，参见 [tech-selection-report-template.md](tech-selection-report-template.md)

#### 步骤7：生成 AGENTS.md（AI Agent开发指导文档）

参见 [agents-template.md](agents-template.md) 获取完整模板。

#### 步骤8：自动搜索技术栈 Skills（关键步骤）

**AGENTS.md 生成后，必须自动搜索并引入相关技术栈规范 Skills**

1. **解析 AGENTS.md 中的技术栈清单**

   从 AGENTS.md 中提取所有锁定的技术栈：
   - 前端框架（Next.js/React/Vue/Nuxt 等）
   - 后端框架（FastAPI/NestJS/Spring Boot/Express/Gin 等）
   - ORM（Prisma/TypeORM/SQLAlchemy 等）
   - 数据库（PostgreSQL/MySQL/MongoDB 等）
   - AI框架（LangChain/LangGraph 等）
   - 编程语言（TypeScript/Python/Go 等）

2. **执行 find-skills 搜索**

   对每项技术执行 `/find-skills <技术关键词>` 指令：

   ```
   示例：
   /find-skills nextjs
   /find-skills typescript
   /find-skills prisma
   /find-skills fastapi
   ```

3. **技术栈搜索映射表**

   | 技术栈类型 | 锁定技术 | 自动搜索指令 |
   |------------|----------|--------------|
   | 前端框架 | Next.js | `/find-skills nextjs` |
   | 前端框架 | React | `/find-skills react` |
   | 前端框架 | Vue | `/find-skills vue` |
   | 后端框架 | FastAPI | `/find-skills fastapi` |
   | 后端框架 | NestJS | `/find-skills nestjs` |
   | 后端框架 | Spring Boot | `/find-skills spring-boot` |
   | ORM | Prisma | `/find-skills prisma` |
   | 数据库 | PostgreSQL | `/find-skills postgresql` |
   | AI框架 | LangChain | `/find-skills langchain` |
   | 语言 | TypeScript | `/find-skills typescript` |

4. **用户确认引入 Skills**

   搜索结果汇总后，使用 AskUserQuestion 让用户选择需要引入的 Skills

5. **安装选定的 Skills**

   根据用户选择安装相关 Skills，确保后续开发符合最佳实践

### 强制输出物

1. 技术选型报告文档：`docs/00-requirements/tech-selection-report.md`
2. **AGENTS.md**：项目根目录下的AI Agent开发指导文档
3. 用户确认的技术栈清单（已锁定版本）
4. 架构模式与设计规范文档
5. **已安装的技术栈规范 Skills**（通过 find-skills 引入）

### AI准出校验规则

- 技术栈调研覆盖所有关键组件（前端/后端/数据/AI/基础设施）
- 所有技术选型均有明确的适用场景说明和推荐理由
- 用户已通过 AskUserQuestion 确认最终技术栈方案
- 技术栈版本号已明确锁定，无模糊版本（如"最新版"）
- **AGENTS.md 已生成并包含完整的技术栈锁定信息**
- 架构模式与项目规模匹配
- 设计规范完整可执行
- **已完成技术栈 Skills 搜索，用户已确认是否引入**

---

## 阶段0：项目初始化与自动化底座搭建

### 执行目标

完成标准化骨架搭建、全局规范定义、AI执行边界锁定，同时搭建依赖矩阵和备份体系两大核心自动化底座。

**关键**：无论新项目还是老项目，阶段0完成后都必须生成/更新 `AGENTS.md`

### 前置输入

**新项目**：阶段-1输出的技术选型报告 + AGENTS.md（已生成）
**老项目**：需要先分析现有代码结构，推断技术栈和规范，再生成 AGENTS.md

### 新项目执行流程

1. **定义全局规范**（基于阶段-1技术选型）：
   - 技术栈锁定：明确前后端框架、版本号、核心依赖
   - 编码规范：命名规则、注释规范、代码分层规则、格式化标准
   - 版本规则：语义化版本号规范、分支管理规则
   - 安全基线：鉴权规则、数据加密规则、接口安全规范
   - 文档规范：统一文档模板、命名规则、变更标记规范

2. 按标准目录结构搭建项目骨架（参见 [project-structure.md](project-structure.md)）

3. 生成根索引文档 `docs/index.md`

4. 搭建依赖矩阵 `doc-dependency-matrix.yaml`

5. 搭建自动化版本备份体系

6. 完成首次全量快照备份，生成初始版本v1.0.0

7. **确认 AGENTS.md 已正确生成**（阶段-1已完成）

### 老项目执行流程

1. **分析现有项目结构**：
   - 检查 `package.json` / `requirements.txt` / `go.mod` / `pom.xml` 等依赖文件
   - 分析目录结构，推断分层架构
   - 检查配置文件（ESLint、Prettier、tsconfig、pyproject.toml等）
   - 检查现有代码风格和命名规范

2. **推断技术栈**：

| 分析项 | 检查文件/方式 |
|--------|---------------|
| 前端框架 | package.json 中的 dependencies |
| 后端框架 | requirements.txt / go.mod / pom.xml |
| 数据库 | 配置文件、ORM文件、migration文件 |
| 语言版本 | tsconfig / pyproject.toml / go.mod |
| 构建工具 | package.json scripts / Makefile |
| 测试框架 | 测试文件、配置文件 |

3. **生成/更新 AGENTS.md**：基于分析结果生成完整文件

4. **搭建docs文档体系**：创建标准目录结构和索引文档，包括 `docs/plans/` 目录

5. **搭建依赖矩阵和备份体系**

6. **完成首次全量快照备份**

### 强制输出物

1. 100%符合标准的项目目录结构（新项目）或补充docs体系（老项目）
2. 根索引文档、全局规范文档
3. 依赖矩阵文件
4. 完整的备份体系
5. `version.json`版本管控文件
6. 项目初始化全量快照备份
7. **AGENTS.md**（新项目确认已有，老项目新生成）

---

## 阶段1：需求全链路标准化文档化

### 执行目标

将模糊需求转化为结构化、可量化、可追溯的标准化文档

### 标准执行步骤

1. 需求拆解：业务目标、核心功能、非功能需求、约束条件、异常场景、验收标准
2. 分配唯一需求ID（格式：REQ-模块编码-序号）
3. 生成顶层文档 `prd.md`、`srs.md`
4. 分模块拆解最小单元需求文档
5. 搭建需求域索引体系
6. 同步更新依赖矩阵
7. AI自检

### 准出校验

所有需求点有唯一ID、验收标准可量化、无业务矛盾、索引闭环

---

## 阶段2：系统架构与分端设计

### 子流程2.1 系统架构设计

基于阶段1需求文档和阶段-1技术选型，完成架构设计

### 子流程2.2 前端UI/UX全链路设计

基于设计系统完成单页面精细化设计，参见 [page-design-template.md](page-design-template.md)

### 子流程2.3 后端数据与接口设计

完成领域模型、数据结构、接口规范设计，参见 [api-design-template.md](api-design-template.md)

---

## 阶段3：分端模块化自动化开发

### 执行目标

基于校验通过的设计文档，按模块完成代码自动化生成。

**关键**：开发代码前必须先生成实施计划（PLAN），无计划不编码！

### 前置输入

阶段2所有子流程校验通过的设计文档、阶段0的全局编码规范、全链路依赖矩阵

### 标准执行步骤

#### 步骤1：生成实施计划（PLAN）- 强制前置步骤

参见 [plan-template.md](plan-template.md) 获取完整计划模板。

**计划文件命名规则**：
- 格式：`PLAN-{类型}-{模块名}-{日期}-{序号}.md`
- 示例：`PLAN-FE-user-module-20260409-001.md`（前端用户模块开发计划）

**计划存档**：
- 新计划存入 `docs/plans/active/`
- 更新 `docs/plans/index.md` 索引
- 计划状态：pending（待执行）、in_progress（执行中）、completed（已完成）、cancelled（已取消）

**用户确认计划**：使用 AskUserQuestion 让用户确认计划是否可行

#### 步骤2：开发前前置校验

AI再次校验对应设计文档的有效性，确认文档已纳入索引、已通过校验、为最新版本

#### 步骤3：标记计划状态为 in_progress

#### 步骤4：模块化拆分开发

严格按照「先底层公共模块、后业务模块；先数据层、后服务层、再接口层；先组件开发、后页面开发」的顺序

#### 步骤5：前端开发执行规范

- 第一步：基于设计系统文档，开发全局样式、基础组件库
- 第二步：基于页面地图文档，搭建路由架构、权限控制框架、全局状态管理
- 第三步：基于单页面设计文档，逐页面开发
- 第四步：页面开发完成后，AI自检

#### 步骤6：后端开发执行规范

- 第一步：基于库表设计文档，生成数据库表结构、初始化SQL
- 第二步：基于领域模型设计文档，开发领域服务、业务规则
- 第三步：基于单接口设计文档，逐接口开发
- 第四步：接口开发完成后，AI自检

#### 步骤7：代码索引体系搭建

完善 `src/frontend/index.md`和 `src/backend/index.md`

#### 步骤8：单元测试自动化生成

核心逻辑覆盖率100%

#### 步骤9：标记计划状态为 completed

#### 步骤10：计划归档与备份

将已完成的计划从 `docs/plans/active/` 移动到 `docs/plans/archived/`

### 强制输出物

1. **实施计划文档**：`docs/plans/active/PLAN-xxx.md` 或 `docs/plans/archived/PLAN-xxx.md`
2. 全量可运行的前端/后端源代码
3. 代码模块两级索引体系
4. 数据库初始化SQL脚本
5. 单元测试代码
6. 更新后的全链路依赖矩阵
7. 开发完成全量快照备份

### AI准出校验规则

- **计划已生成并存档**：无计划不得进入开发阶段
- 计划已通过用户确认
- 代码100%符合对应设计文档的要求
- 所有代码均已纳入索引体系
- 代码符合全局编码规范
- 单元测试覆盖核心业务逻辑，测试通过率100%
- 项目可正常编译、启动
- **计划状态已更新为 completed 并归档**

---

## 阶段4：自动化集成测试与交付

完成集成联调、全量测试验证、上线交付

---

## 阶段5：需求变更与代码重构全闭环管控

需求变更后自动完成备份→影响分析→关联文档同步更新→校验→代码开发

参见 [change-impact-report-template.md](change-impact-report-template.md) 获取变更影响分析报告模板。