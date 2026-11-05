# 自媒体获客运营 Agent 启动包

给 Agent 一个新产品或服务的资料和这个仓库，它可以沿同一套流程配置项目，初始化新的飞书文档和多维表格，然后开始搜对标、拆案例、做内容和复盘。每个项目单独准备飞书租户、应用授权及所需第三方能力。Grokbot、WorkBuddy、Codex 或其他 Agent 共用 [AGENTS.md](AGENTS.md) 和五个业务技能。

## 新项目怎么用

给 Agent 仓库读取权限，并在一个新项目目录打开或检出仓库。需要单独托管项目时，在 GitHub 使用 **Use this template** 创建项目仓库。把下面这段与产品资料一起发给它。

> 读取本仓库的 AGENTS.md，给我初始化自媒体获客运营 Agent。先问我要推广什么产品，再配置检索 Skill 和 LibTV，主动发起需要我完成的安全授权。接着请我完成新租户的飞书 CLI 授权，验证通过后再问我要工作的 Wiki 页面链接。收到链接后，在该 Wiki 下建项目文档、候选池和 Showcase 表，回读后汇报。

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

`doctor` 列出缺失的项目资料及本机是否有飞书 CLI。飞书资源和平台接口在目标环境独立验证。默认在指定 Wiki 初始化，默认接入 LibTV MCP，图文项目可明确跳过视频。发布后复盘 Skill 标记为「未完待续」，根据实际发布与验证结果迭代。

## 许可证

仓库内的原创内容采用 [MIT 许可证](LICENSE)。文档引用的第三方工具按各自的许可证和服务条款提供。
