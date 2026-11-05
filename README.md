# 自媒体获客运营 Agent 启动包

给 Agent 一个新产品或服务的资料和这个仓库，它可以沿同一套流程配置项目，初始化新的飞书文档和多维表格，然后开始搜对标、拆案例、做内容和复盘。每个项目单独准备飞书租户、应用授权及所需第三方能力。Grokbot、WorkBuddy、Codex 或其他 Agent 共用 [AGENTS.md](AGENTS.md) 和五个业务技能。

## 新项目怎么用

给 Agent 仓库读取权限，并在一个新项目目录打开或检出仓库。需要单独托管项目时，在 GitHub 使用 **Use this template** 创建项目仓库。把下面这段与产品资料一起发给它。

> 读取本仓库的 AGENTS.md，给我的新项目初始化自媒体获客运营 Agent。先从我给的产品资料提取已知信息，一次列齐还缺的项目口径和需要我登录授权的项目。飞书使用全新的租户、应用和独立 CLI profile，创建项目文档、候选池和 Showcase 表。验证选用的工具和实际资源后回报项目状态。第一轮先做我指定平台的对标检索，交待挑选清单，由我选要拆的案例。

能直接运行初始化的 Agent 需要 Git 或仓库读取权限、终端、Python 3.10+、独立可写目录，以及对已授权服务的访问能力。私有仓库需让运行环境获得读取权限。产品简报和运行记录放在当前项目的 `.project/`。浏览器登录、组织管理员审批和凭据注入按目标租户及工具要求完成。

## 仓库里有什么

| 路径 | 内容 |
|---|---|
| [AGENTS.md](AGENTS.md) | 新项目接手、补齐输入、开通验证、阶段路由 |
| [.agents/skills](.agents/skills) | 五个迁移后的技能，覆盖检索、案例管理、拆解与方案、生产、复盘 |
| [docs/runtimes.md](docs/runtimes.md) | Grokbot、WorkBuddy、Codex 及通用环境接入 |
| [docs/dependencies.md](docs/dependencies.md) | WorkBuddy 原技能、内置能力、外部服务与付费依赖的迁移清单 |
| [docs/feishu.md](docs/feishu.md) | 新租户 CLI 授权、自动建表建文档、读写与恢复 |
| [templates](templates) | 案例、拆解和版本化内容方案模板 |
| [scripts](scripts) | 本地项目检查及飞书初始化工具 |

## 先本地检查

```sh
python3 scripts/project_setup.py init --slug my-project --name '新产品'
python3 scripts/project_setup.py doctor
python3 -m unittest discover -s tests
```

`doctor` 列出缺失的项目资料及本机是否有飞书 CLI。飞书资源和平台接口在目标环境独立验证。检索、视频和定时能力按项目选配。图文可直接产出制作包，视频需接入可生成和导出成片的工具。
