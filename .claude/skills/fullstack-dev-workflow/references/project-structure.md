# 标准化项目目录结构

---

## 完整目录结构

```
project-root/
├── AGENTS.md               # AI Agent开发指导文档（阶段-1/阶段0生成）
├── docs/
│   ├── index.md            # 根索引文档
│   ├── .version-history/   # 版本历史备份目录
│   ├── doc-dependency-matrix.yaml  # 依赖矩阵
│   ├── phase-check-reports/       # 阶段完成检查报告目录
│   │   ├── index.md
│   │   ├── phase-1-check.md       # 阶段1完成检查报告
│   │   ├── phase-2-check.md       # 阶段2完成检查报告
│   │   └── phase-3-check.md       # 阶段3完成检查报告
│   ├── plans/                    # 实施计划目录
│   │   ├── index.md              # 计划索引文档
│   │   ├── .history/             # 计划历史版本备份
│   │   ├── active/               # 当前执行中的计划
│   │   │   └── index.md
│   │   └── archived/             # 已完成/已归档的计划
│   │       └── index.md
│   ├── 00-requirements/          # 需求文档
│   │   ├── index.md
│   │   ├── tech-selection-report.md  # 技术选型报告（新项目必有）
│   │   ├── prd.md                # 产品需求文档
│   │   ├── srs.md                # 软件需求规格
│   │   ├── change-logs/          # 变更记录
│   │   │   └── index.md
│   │   └── modules/              # 分模块需求
│   │       └── index.md
│   ├── 01-architecture/          # 架构设计
│   │   ├── index.md
│   │   └── system-architecture.md
│   ├── 02-frontend-design/       # 前端设计
│   │   ├── index.md
│   │   ├── design-system.md      # 设计系统
│   │   ├── design-check-report.md # 前端设计完成检查报告
│   │   ├── user-journey.md       # 用户旅程
│   │   ├── page-map.md           # 页面地图（含子页面）
│   │   ├── component-spec/       # 组件规范
│   │   │   └── index.md
│   │   └── pages/                # 页面设计（含子页面）
│   │       ├── index.md
│   │       ├── main/             # 主页面
│   │       │   └── index.md
│   │       └── sub/              # 子页面
│   │       │   └── index.md
│   │       └── modal/            # 弹窗/抽屉页面
│   │       │   └── index.md
│   ├── 03-backend-design/        # 后端设计
│   │   ├── index.md
│   │   ├── domain-model.md       # 领域模型
│   │   ├── api-global-standard.md # API全局标准
│   │   ├── database-design/      # 数据库设计
│   │   │   └ndex.md
│   │   └nd api-spec/             # API规范
│   │       └ndex.md
│   ├── 04-test-acceptance/       # 测试验收
│   │   ├── index.md
│   │   ├── unit/                 # 单元测试
│   │   │   └ndex.md
│   │   ├── integration/          # 集成测试
│   │   │   └ndex.md
│   │   ├── e2e/                  # E2E端到端测试
│   │   │   ├── index.md
│   │   │   ├── scenarios/        # 测试场景
│   │   │   │   └ndex.md
│   │   │   └nd data-flow/        # 数据流测试
│   │   │       └ndex.md
│   │   └nd cases/                # 测试用例
│   │       └ndex.md
│   ├── 05-smart-contract-design/ # 智能合约设计（Web3项目）
│   │   ├── index.md
│   │   ├── contract-architecture.md  # 合约架构
│   │   ├── state-variables.md    # 状态变量设计
│   │   ├── methods/              # 合约方法设计
│   │   │   └ndex.md
│   │   └nd security/             # 安全设计
│   │   │   └ndex.md
│   ├── 06-ai-design/             # AI/Prompt设计（AI应用项目）
│   │   ├── index.md
│   │   ├── prompt-library/       # Prompt库
│   │   │   ├── index.md
│   │   │   ├── system-prompts/   # 系统Prompt
│   │   │   │   └ndex.md
│   │   │   └nd user-prompts/     # 用户Prompt模板
│   │   │       └ndex.md
│   │   ├── agent-flow/           # Agent流程设计
│   │   │   └ndex.md
│   │   ├── rag-pipeline/         # RAG管道设计
│   │   │   └ndex.md
│   │   ├── model-config/         # 模型配置
│   │   │   └ndex.md
│   │   └nd token-optimization/   # Token优化策略
│   │       └ndex.md
│   ├── 07-mobile-design/         # 移动应用设计（App项目）
│   │   ├── index.md
│   │   ├── platform-adaptation.md    # 平台适配设计
│   │   ├── push-service.md       # 推送服务设计
│   │   ├── offline-strategy.md   # 离线策略
│   │   └nd native-bridge/        # 原生桥接
│   │       └ndex.md
│   ├── 08-cli-design/            # CLI工具设计（工具项目）
│   │   ├── index.md
│   │   ├── command-spec.md       # 命令规格
│   │   ├── argument-parser.md    # 参数解析
│   │   └nd output-format.md      # 输出格式规范
│   ├── 09-devops-design/         # DevOps设计
│   │   ├── index.md
│   │   ├── ci-pipeline.md        # CI流水线
│   │   ├── cd-strategy.md        # CD策略
│   │   ├── monitoring.md         # 监控设计
│   │   └nd logging.md            # 日志设计
│   ├── 10-security-design/       # 安全设计
│   │   ├── index.md
│   │   ├── auth-flow.md          # 认证流程
│   │   ├── encryption.md         # 加密策略
│   │   └nd access-control.md     # 访问控制
├── src/
│   ├── frontend/                 # 前端代码
│   │   └ndex.md              # 前端代码索引
│   └nd backend/                  # 后端代码
│       └ndex.md              # 后端代码索引
└nd version.json                  # 版本管控文件
```

---

## 目录职责说明

### docs/ 目录

| 子目录 | 职责 | 关键文件 |
|--------|------|----------|
| phase-check-reports/ | 阶段完成检查报告 | phase-1-check.md, phase-2-check.md, phase-3-check.md |
| plans/ | 存放实施计划 | active/执行中，archived/已完成 |
| 00-requirements/ | 需求相关文档 | prd.md, srs.md, tech-selection-report.md |
| 01-architecture/ | 系统架构设计 | system-architecture.md |
| 02-frontend-design/ | 前端UI/UX设计 | design-system.md, pages/, page-map.md, design-check-report.md |
| 03-backend-design/ | 后端数据与接口设计 | domain-model.md, api-spec/ |
| 04-test-acceptance/ | 测试验收文档 | unit/, integration/, e2e/, cases/ |
| 05-smart-contract-design/ | 智能合约设计（Web3项目） | contract-architecture.md, methods/, security/ |
| 06-ai-design/ | AI/Prompt设计（AI应用项目） | prompt-library/, agent-flow/, rag-pipeline/ |
| 07-mobile-design/ | 移动应用设计（App项目） | platform-adaptation.md, push-service.md |
| 08-cli-design/ | CLI工具设计（工具项目） | command-spec.md, argument-parser.md |
| 09-devops-design/ | DevOps设计 | ci-pipeline.md, cd-strategy.md, monitoring.md |
| 10-security-design/ | 安全设计 | auth-flow.md, encryption.md, access-control.md |

### src/ 目录

| 子目录 | 职责 |
|--------|------|
| frontend/ | 前端源代码，每个模块需要有 index.md |
| backend/ | 后端源代码，每个模块需要有 index.md |

---

## 按项目类型启用目录

不同项目类型启用不同的扩展目录：

| 项目类型 | 必备目录 | 可选启用目录 |
|----------|----------|--------------|
| Web应用 | 00-04基础目录 | 06-ai-design（AI功能时）, 09-devops, 10-security |
| API服务 | 00-03目录 | 06-ai-design（AI服务时）, 09-devops, 10-security |
| Web3/DApp | 00-04基础目录 | 05-smart-contract-design（必备）, 10-security |
| AI应用 | 00-04基础目录 | 06-ai-design（必备）, 09-devops |
| 移动应用 | 00-04基础目录 | 07-mobile-design（必备） |
| CLI工具 | 00-02目录 | 08-cli-design（必备） |
| 企业级系统 | 00-04基础目录 | 09-devops（必备）, 10-security（必备） |

---

## plans/ 目录详解

```
docs/plans/
├── index.md              # 所有计划的索引，记录计划ID、状态、路径
├── .history/             # 计划的历史版本备份
│   └ndex.md    # 历史版本文件
├── active/               # 当前正在执行的计划
│   ├── index.md          # 执行中计划索引
│   └ndex.md    # 具体计划文件
└nd archived/             # 已完成或取消的计划
    ├── index.md          # 已归档计划索引
    └ndex.md    # 具体计划文件
```

**计划状态与位置对应**：
- pending/in_progress → `active/`
- completed/cancelled → `archived/`

---

## phase-check-reports/ 目录详解

```
docs/phase-check-reports/
├── index.md              # 检查报告索引
├── phase-1-check.md      # 阶段1（需求标准化）完成检查报告
├── phase-2-check.md      # 阶段2（架构与设计）完成检查报告
├── phase-3-check.md      # 阶段3（模块化开发）完成检查报告
├── phase-4-check.md      # 阶段4（集成测试）完成检查报告
└nd phase-5-check.md      # 阶段5（变更闭环）完成检查报告
```

每个检查报告包含：
- 已完成文档清单
- 未完成项列表（如有）
- 检查时间戳
- 检查结果（通过/待补充）

---

## 索引文档模板

每个层级的 `index.md` 必须包含：

```markdown
# [目录名称]索引

## 文档列表

| 文档名称 | 文档路径 | 对应ID | 状态 | 更新时间 |
|----------|----------|--------|------|----------|
| [文档1] | [路径] | [ID] | [状态] | [时间] |

## 子目录列表

| 目录名称 | 目录路径 | 说明 |
|----------|----------|------|
| [目录1] | [路径] | [说明] |

## 变更记录

| 变更单号 | 变更内容 | 更新时间 |
|----------|----------|----------|
```

---

## version.json 格式

```json
{
  "project_name": "【项目名称】",
  "current_version": "v1.0.0",
  "last_updated": "YYYY-MM-DD HH:mm:ss",
  "change_history": [
    {
      "version": "v1.0.0",
      "change_no": "INIT-001",
      "change_type": "初始化",
      "change_time": "YYYY-MM-DD HH:mm:ss",
      "change_summary": "项目初始化"
    }
  ]
}
```