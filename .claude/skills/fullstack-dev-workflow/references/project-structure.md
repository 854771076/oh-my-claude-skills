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
│   │   ├── user-journey.md       # 用户旅程
│   │   ├── component-spec/       # 组件规范
│   │   │   └── index.md
│   │   └── pages/                # 页面设计
│   │       └── index.md
│   ├── 03-backend-design/        # 后端设计
│   │   ├── index.md
│   │   ├── domain-model.md       # 领域模型
│   │   ├── api-global-standard.md # API全局标准
│   │   ├── database-design/      # 数据库设计
│   │   │   └── index.md
│   │   └── api-spec/             # API规范
│   │       └── index.md
│   └── 04-test-acceptance/       # 测试验收
│       ├── index.md
│       └── cases/                # 测试用例
│           └── index.md
├── src/
│   ├── frontend/                 # 前端代码
│   │   └── index.md              # 前端代码索引
│   └── backend/                  # 后端代码
│       └── index.md              # 后端代码索引
└── version.json                  # 版本管控文件
```

---

## 目录职责说明

### docs/ 目录

| 子目录 | 职责 | 关键文件 |
|--------|------|----------|
| plans/ | 存放实施计划 | active/执行中，archived/已完成 |
| 00-requirements/ | 需求相关文档 | prd.md, srs.md, tech-selection-report.md |
| 01-architecture/ | 系统架构设计 | system-architecture.md |
| 02-frontend-design/ | 前端UI/UX设计 | design-system.md, pages/ |
| 03-backend-design/ | 后端数据与接口设计 | domain-model.md, api-spec/ |
| 04-test-acceptance/ | 测试验收文档 | cases/ |

### src/ 目录

| 子目录 | 职责 |
|--------|------|
| frontend/ | 前端源代码，每个模块需要有 index.md |
| backend/ | 后端源代码，每个模块需要有 index.md |

---

## plans/ 目录详解

```
docs/plans/
├── index.md              # 所有计划的索引，记录计划ID、状态、路径
├── .history/             # 计划的历史版本备份
│   └── PLAN-xxx-v1.md    # 历史版本文件
├── active/               # 当前正在执行的计划
│   ├── index.md          # 执行中计划索引
│   └── PLAN-FE-xxx.md    # 具体计划文件
└── archived/             # 已完成或取消的计划
    ├── index.md          # 已归档计划索引
    └── PLAN-FE-xxx.md    # 具体计划文件
```

**计划状态与位置对应**：
- pending/in_progress → `active/`
- completed/cancelled → `archived/`

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