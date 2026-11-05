# 在不同 Agent 上运行

每个新产品或服务使用独立的仓库工作目录。仓库根目录的 `AGENTS.md` 是初始化和运营入口，`.agents/skills/<技能名>/SKILL.md` 是技能源文件，`.project/project.json` 保存该项目的业务配置。Agent 可以用客户端的技能发现功能，也可以直接读取对应的 `SKILL.md` 和它引用的文件。

## Agent 需要的能力

| 能力 | 接入时要验证 | 缺失时的处理 |
| --- | --- | --- |
| 仓库访问 | 能读取私有仓库的实际文件，能说明当前检出版本 | 由用户在受信任环境检出仓库并提供目录，或授予仅限该仓库的读取权限。收到链接后应实际确认可读 |
| 工作目录和终端 | 能在项目目录读写文件、运行 Python 3.10+、保留 `.project/` 供后续任务接着用 | 移到带终端和持久目录的执行环境。纯对话客户端可以整理项目资料和输出草稿 |
| 飞书接入 | 终端能运行官方 `lark-cli`，可以访问目标飞书或 Lark，用户能在新组织完成登录与授权 | 先完成业务配置与本地草稿，标记飞书待接入。由新组织成员完成授权后，在同一项目目录继续 |
| 检索与证据 | 能打开目标平台或访问已授权的数据来源，保留原始链接、取数时间和指标口径 | 请用户提供链接、截图或导出，并标注证据覆盖范围。缺失字段留空 |
| 可选执行能力 | 视频生成、额外模型、发布或定时任务有各自可用的服务、权限和可验收的结果 | 把相应步骤列为待接入，先交付能验证的成果。媒体服务的 Key 和平台授权各自配置 |

Agent 从仓库根目录检查环境与当前版本即可。初次配置按 `AGENTS.md` 建立项目简报后，可用以下命令检查本地准备情况。

```sh
git rev-parse --show-toplevel
git rev-parse --short HEAD
python3 --version
python3 scripts/project_setup.py doctor
```

`doctor` 检查项目资料和本机是否找到飞书 CLI。远程状态以新租户的身份、文档和 Base 的实际读回结果为准。飞书配置和验证见 [新租户飞书接入](feishu.md)。

需要用户介入时，在原任务对话里一次说明缺什么、在哪完成、完成后回复什么。普通对话只传产品资料、目标组织等非密钥信息。登录、扫码和密钥录入用客户端安全入口、服务商授权页或本地受信任的交互终端。

## Codex

1. 在 Codex 桌面应用打开该项目的本地目录，或从仓库根目录启动 `codex`。
2. 发送 README 的启动指令和新项目资料。Codex 会读取仓库 `AGENTS.md`，并从 `.agents/skills/` 发现项目技能。需要核对选中的技能时，让 Agent 报出它实际读取的仓库路径。
3. 新租户授权若需要用户操作，在可交互的终端或官方授权页完成，回到当前任务继续。云端工作区也需逐项核对网络和配置持久性。 [Codex 项目指令](https://developers.openai.com/codex/guides/agents-md) · [Codex 技能](https://developers.openai.com/codex/skills)

## WorkBuddy

1. 新建本地任务，把该项目的仓库根目录设为工作目录，选用允许读写和运行命令的任务模式。
2. 发送 README 的启动指令，让 WorkBuddy 显式读取 `AGENTS.md` 和本次需要的项目技能。技能面板也可以导入本地技能包。导入时保留技能整个目录及引用文件，用仓库源文件核对版本。
3. 若在专家中心使用这套流程，把同一启动指令作为任务说明。专家、技能和连接器各自配置。飞书仍按项目的专用 CLI 身份初始化。 [WorkBuddy 本地任务](https://www.codebuddy.ai/docs/zh/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Task-Bar) · [技能导入](https://www.codebuddy.ai/docs/zh/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills) · [专家中心](https://www.codebuddy.ai/docs/zh/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Expert-Center)

## Grokbot

若使用的是带云电脑的 Grok Bot，向 Bot 发仓库链接和 README 的启动指令，让它在云电脑上检出到该项目的独立目录，并明确读取 `AGENTS.md` 和仓库技能文件。若私有仓库不可读，请用户在受信任的环境完成 GitHub 授权或提供已检出的目录。官方资料确认云电脑提供终端和文件系统。技能按仓库路径读取即可。 [Grok Bot 产品说明](https://docs.x.ai/grok-bot/overview) · [Grok Bot 技能和例行任务](https://docs.x.ai/grok-bot/skills-routines-and-automations)

完成飞书扫码或网页登录时，可用安全表单或用户接管。使用密钥时按客户端文档通过安全卡录入，并验证对应工具确实获得授权。同一账号的 Bots 共享一台云电脑及其命令行登录状态，项目应使用独立工作目录和飞书配置。需要阻止同账号下其他 Bot 接触项目凭证时，应在独立账号或受控执行环境运行。 [Grok Bot 云电脑](https://docs.x.ai/grok-bot/computer-and-apps) · [Grok Bot 安全录入](https://docs.x.ai/grok-bot/vault)

其他名为 Grokbot 的客户端可按上面的能力表接入。仓库文件读取、命令执行和凭证交互都通过后，再进入飞书初始化。

## 其他 Agent

从能访问项目仓库的会话开始，使用 README 的同一条启动指令。若客户端支持上传技能，导入该阶段所需的技能目录。若支持 MCP，把它用于已授权的检索或其他工具能力，并在报告里记录实际使用的来源。使用飞书时，按仓库的 CLI 流程完成新租户校验。

换 Agent 继续同一项目时，给新会话打开原项目目录，读项目简报、已交付成果与飞书验证状态。换了机器时，按目标组织重新建立飞书认证，并在接续前核对项目资源归属。新产品或服务从独立工作目录开始。
