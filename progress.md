# Coder-Factory 决策日志

## 项目概述
**项目名称**: Coder-Factory
**目标**: 构建 AI 自主代码工厂，实现从需求到交付的全自动化
**启动时间**: 2026-02-18

---

## 决策记录

### [2026-02-18] 项目初始化

#### 用户需求确认
- **输入**: 用户描述核心功能 - AI自主根据需求完成产品交付
- **能力要求**:
  1. 需求分解
  2. 交互确认
  3. 架构设计
  4. 编码实现
  5. 测试验证
  6. 部署交付
- **技术栈策略**: 动态匹配，根据具体需求选择最适合的技术

#### 架构决策
```
┌─────────────────────────────────────────────────────────────────┐
│                     Coder-Factory 架构                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│   │   用户界面    │───▶│  需求解析    │───▶│  交互确认    │     │
│   │   (CLI/Web)  │    │    引擎      │    │    系统      │     │
│   └──────────────┘    └──────────────┘    └──────────────┘     │
│                              │                    │             │
│                              ▼                    ▼             │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│   │   交付流水线  │◀───│  测试系统    │◀───│  架构设计    │     │
│   │              │    │              │    │    引擎      │     │
│   └──────────────┘    └──────────────┘    └──────────────┘     │
│         │                    │                    │             │
│         │                    ▼                    ▼             │
│         │            ┌──────────────┐    ┌──────────────┐      │
│         └───────────▶│  Docker部署  │◀───│  代码生成    │      │
│                      │    引擎      │    │    核心      │      │
│                      └──────────────┘    └──────────────┘      │
│                                                                 │
│   ┌────────────────────────────────────────────────────┐       │
│   │              状态管理 (features.json)               │       │
│   │              决策日志 (progress.md)                 │       │
│   └────────────────────────────────────────────────────┘       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 功能模块拆分 (7个核心模块)
| ID | 模块 | 优先级 | 状态 |
|----|------|--------|------|
| F001 | 需求解析引擎 | P0 | pending |
| F002 | 交互确认系统 | P0 | pending |
| F003 | 架构设计引擎 | P0 | pending |
| F004 | 代码生成核心 | P0 | pending |
| F005 | 自动化测试系统 | P1 | pending |
| F006 | 容器化部署引擎 | P1 | pending |
| F007 | 交付流水线 | P1 | pending |

#### 下一步行动
1. 选择首个功能点进行开发
2. 确定基础技术栈 (Python/Node.js)
3. ~~初始化项目骨架代码~~ ✅ 已完成

---

### [2026-02-18] 项目初始化完成

#### 已完成工作
1. **GitHub 仓库**: https://github.com/jyzhou2019/coder-factory
2. **项目骨架**:
   - `coder_factory/` - 核心包
   - `coder_factory/core/` - 工厂类和状态管理
   - `coder_factory/engines/` - 7个引擎模块 (待实现)
   - `coder_factory/utils/` - 工具模块
   - `tests/` - 测试目录
3. **CLI 框架**: 交互式命令行界面 (click + rich)
4. **Docker 配置**: Dockerfile + docker-compose.yml
5. **验证**: Docker 镜像构建成功 (169MB)，容器运行正常

#### 技术栈确定
- **运行时**: Python 3.11
- **CLI**: Click + Rich
- **AI**: Anthropic API / OpenAI API
- **容器**: Docker + Docker Compose
- **VCS**: Git + GitHub

#### 下一步行动
1. ~~实现 F001 - 需求解析引擎~~ ✅ 已完成
2. ~~实现 F002 - 交互确认系统~~ ✅ 已完成
3. ~~实现 F003 - 架构设计引擎~~ ✅ 已完成

---

### [2026-02-18] F003 架构设计引擎完成

#### 核心组件
1. **tech_stack_kb.py** - 技术栈知识库
   - `TechStackKnowledgeBase` - 知识库类
   - `TechOption` - 技术选项 (运行时/框架/数据库)
   - `TechStackTemplate` - 技术栈模板
   - `ProjectCategory` - 项目类型枚举
   - `ScaleLevel` - 规模级别枚举

2. **architecture_designer.py** - 架构设计器
   - `ArchitectureDesigner` - 主设计器类
   - `ArchitectureDesign` - 架构设计结果
   - `ArchitectureComponent` - 架构组件

#### 技术栈知识库内容
- **运行时**: Python, Node.js, Go, Rust
- **前端框架**: React, Vue, Svelte
- **后端框架**: FastAPI, Django, Express, NestJS
- **数据库**: PostgreSQL, MongoDB, SQLite, Redis

#### 技术栈模板
- Python FastAPI + React (Web 应用)
- Python Django 全栈 (内容管理)
- Node.js Express + React (MERN 栈)
- Node.js NestJS (企业级 API)
- Go Gin API (高性能服务)
- Python/Go CLI (命令行工具)

#### CLI 新命令
- `coder-factory design <需求>` - 设计系统架构
- `coder-factory tech` - 查看技术栈信息
- `coder-factory tech python` - 查看技术详情
- `coder-factory tech python,go` - 比较技术

#### 功能模块更新
| ID | 模块 | 状态 |
|----|------|------|
| F001 | 需求解析引擎 | ✅ passed |
| F002 | 交互确认系统 | ✅ passed |
| F003 | 架构设计引擎 | ✅ passed |
| F004 | 代码生成核心 | ✅ (Claude Code) |
| F005 | 自动化测试系统 | ✅ (Claude Code) |
| F006 | 容器化部署引擎 | pending |
| F007 | 交付流水线 | pending |

---

### [2026-02-18] F002 交互确认系统完成

#### 核心组件
1. **interaction_manager.py** - 交互管理器
   - `DialogStateMachine` - 对话状态机
   - `InteractionManager` - 交互管理器
   - `DialogTurn` - 对话轮次记录
   - `ChangeRecord` - 需求变更追踪

2. **confirmation_flow.py** - 确认流程协调器
   - `ConfirmationFlow` - 完整的交互确认流程
   - 自动生成确认问题
   - 支持需求修改和批准

3. **cli.py** - CLI 更新
   - 交互式问答界面
   - 多种问题类型支持 (confirm/choice/multi_select/text/number)
   - 需求修改功能

#### 对话状态机
```
IDLE → PARSING → CONFIRMING → CLARIFYING → REFINING → APPROVED
                       │                               │
                       └─────────── CANCELLED ←────────┘
```

#### 问题类型
- `CONFIRM` - 是/否确认
- `CHOICE` - 单选
- `MULTI_SELECT` - 多选
- `TEXT` - 文本输入
- `NUMBER` - 数字输入

#### Bug 修复
- Python 3.14 中 dataclass 字段名 `field` 与 `dataclasses.field` 函数冲突
- 将 `ChangeRecord.field` 重命名为 `ChangeRecord.field_name`

#### 功能模块更新
| ID | 模块 | 状态 |
|----|------|------|
| F001 | 需求解析引擎 | ✅ passed |
| F002 | 交互确认系统 | ✅ passed |
| F003 | 架构设计引擎 | pending |
| F004 | 代码生成核心 | ✅ (Claude Code) |
| F005 | 自动化测试系统 | ✅ (Claude Code) |
| F006 | 容器化部署引擎 | pending |
| F007 | 交付流水线 | pending |

---

### [2026-02-18] F001 需求解析引擎完成

#### 设计决策
用户要求底层直接使用 **Claude Code** 而非自建解析器。

#### 架构调整
```
┌─────────────────────────────────────────────────────┐
│                 Coder-Factory (编排层)               │
│   RequirementParser → ClaudeCodeClient              │
├─────────────────────────────────────────────────────┤
│                 Claude Code (执行层)                 │
│   - 需求解析                                         │
│   - 代码生成                                         │
│   - 测试执行                                         │
│   - 部署操作                                         │
└─────────────────────────────────────────────────────┘
```

#### 已实现模块
1. **claude_client.py** - Claude Code CLI 封装
   - `parse_requirement()` - 需求解析
   - `generate_code()` - 代码生成
   - `run_tests()` - 测试执行
   - `deploy()` - 部署操作

2. **requirement_parser.py** - 需求解析引擎
   - 调用 Claude Code 解析自然语言
   - 构建 TaskNode 任务树
   - 提取技术栈建议

3. **models/** - 数据模型
   - `Requirement` - 需求对象
   - `TaskNode` - 任务节点
   - `TechStack` - 技术栈
   - `ProjectSpec` - 项目规格

4. **cli.py** - CLI 更新
   - `parse` 命令 - 解析需求并显示任务分解
   - `generate` 命令 - 完整流程 (解析→生成→测试)
   - `status` 命令 - 显示模块状态

#### 验证结果
- Docker 构建成功
- 容器运行正常
- `coder-factory status` 显示模块状态

#### 功能模块更新
| ID | 模块 | 状态 |
|----|------|------|
| F001 | 需求解析引擎 | ✅ passed |
| F002 | 交互确认系统 | pending |
| F003 | 架构设计引擎 | pending |
| F004 | 代码生成核心 | ✅ (通过 Claude Code 实现) |
| F005 | 自动化测试系统 | ✅ (通过 Claude Code 实现) |
| F006 | 容器化部署引擎 | pending |
| F007 | 交付流水线 | pending |

---

## 环境状态
- **OS**: Windows 11 Home 10.0.26200
- **Docker**: v29.1.5
- **Docker Compose**: v5.0.1
- **GitHub**: jyzhou2019 (已认证)
- **工作目录**: D:\ai-program\coder-factory

---

## 错误与回滚记录
*暂无*

---

## 外部协助记录
*暂无*
