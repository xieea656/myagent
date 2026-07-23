# myagent

CLI AI Agent，支持多模型、工具调用、持久记忆、计划模式。

## 快速开始

```bash
pip install rich openai pyyaml prompt_toolkit tiktoken
python xlink.py
```

首次运行会自动引导配置凭据。

## 命令

| 命令 | 说明 |
|------|------|
| `/help` | 帮助 |
| `/status` | 当前状态 |
| `/model` | 切换模型 |
| `/provider` | 切换提供商 |
| `/persona` | 人格管理 |
| `/plan` | 计划模式 |
| `/tools` | 列出工具 |
| `/notools` | 工具开关 |
| `/mode` | 权限模式 (yolo/auto/manual) |
| `/debug` | 调试 (context/build/compress) |
| `/history` | 查看历史消息 |
| `/search` | 搜索历史消息 |
| `/memory` | 查看持久记忆 |
| `/config` | 查看/设置配置 |
| `/protect` | 保护消息不被压缩 |
| `/credential` | 添加凭据 |
| `/clear` | 重置会话 |
| `/resume` | 恢复历史会话 |
| `/exit` | 退出 |

## 功能

- **多模型切换** — 多 provider（mimo/deepseek/qwen），运行时切换
- **工具调用** — 读写文件、执行命令、搜索网页、编辑文件
- **图片 OCR** — 自动检测用户输入和工具结果中的图片，用 tesseract 提取文字
- **计划模式** — 先出方案，确认后执行
- **持久记忆** — 跨会话保留，工作记忆 3000 token / 30 条
- **上下文压缩** — 一次性 LLM 压缩，保留关键信息，保留最近 4 轮
- **权限系统** — 三级模式 (yolo/auto/manual)，危险操作二次确认
- **会话管理** — 自动保存，可恢复，可搜索
- **工具日志** — 每次调用记录到文件，L2 简略格式，可回溯查看
- **终端美化** — rich 排版，Markdown 渲染，状态栏

## 配置

`config.yaml` 位于 `.xlink/` 目录，支持多 provider：

```yaml
providers:
  deepseek:
    api_key_env: API_KEY
    base_url: https://api.deepseek.com
    default_model: deepseek-v4-flash
  mimo:
    api_key_env: MIMO_API_KEY
    base_url: https://token-plan-cn.xiaomimimo.com/v1
    default_model: mimo-v2.5-pro
```

凭据管理使用 `~/.config/xlink/credentials.yaml`，支持 `api-key` 和 `env` 类型。

## 项目结构

```
myagent/
├── xlink.py              # CLI 入口
├── agent.py              # Agent 核心（循环、上下文、工具调度）
├── tools.py              # 工具定义
├── config.py             # 配置加载
├── system_prompt.py      # 系统提示词
├── log.py                # 工具日志
├── events.py             # 事件系统
├── message.py            # AgentMessage 定义
├── memory_index.py       # 持久记忆索引
├── persona.py            # 人格管理
├── .xlink/
│   ├── config.yaml       # 多 provider 配置
│   ├── .env              # API 密钥
│   ├── sessions/         # 会话历史
│   ├── logs/             # 工具日志
│   └── compressed/       # 压缩存档
└── personas/             # 人格文件
```