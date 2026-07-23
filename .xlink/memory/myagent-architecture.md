---
name: myagent-architecture
description: myagent 项目架构概览：模块职责、数据流、技术栈
metadata:
  type: project
---

# myagent 架构概览

## 项目定位
CLI AI Agent，支持多模型、多人格、工具调用、计划模式、三层记忆系统。
暑假项目，目标是做出自己的 Agent 雏形。

## 模块职责
| 模块 | 文件 | 职责 |
|------|------|------|
| CLI 入口 | xlink.py (407行) | REPL 循环、命令分发、prompt_toolkit UI、事件绑定 |
| 核心引擎 | agent.py (588行) | 消息循环、上下文构建、工具调度、记忆管理、压缩 |
| 工具集 | tools.py (778行) | 20+ 工具：文件/命令/搜索/时区/记忆 |
| 配置 | config.py (128行) | provider/model 切换、凭证管理 |
| 消息类 | message.py (39行) | AgentMessage 序列化/反序列化 |
| 记忆索引 | memory_index.py (67行) | SQLite + FTS5 全文检索 |
| 日志 | log.py (41行) | 工具调用 JSONL 日志 + L2 简略摘要 |
| 事件总线 | events.py (15行) | 解耦 UI 和核心逻辑 |
| 人格 | persona.py (12行) | YAML 人格文件加载 |
| 提示词 | system_prompt.py (96行) | 系统提示词 + 压缩提示词 |

## 关键设计决策
- **零框架依赖**：纯 Python + OpenAI 兼容 API，不用 LangChain
- **Agentic Loop**：while 循环 + function calling，最多 25 轮迭代
- **10 段上下文架构**：静态区(①-⑥)命中缓存 + 动态区(⑦-⑪)不缓存
- **L2 简略日志**：大输出只存日志引用，上下文放摘要，按需读取全文
- **多 provider 配置**：20+ 预设提供商，.xlink/config.yaml + .env 双层加载

## 数据目录 (.xlink/)
- sessions/*.jsonl — 会话历史
- logs/*_tools.jsonl — 工具日志（按日期）
- memory/*.md — 持久记忆（Markdown + YAML frontmatter）
- memory.db — SQLite FTS5 全文索引
- config.yaml — provider 配置
- .env — API keys
- personas/*.yaml — 人格定义