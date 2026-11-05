# 依赖清单与验证方法

以新项目实际选用的能力为准。初始化需要 Git、Python 3.10+、可写工作区和命令执行权限。飞书模式还需要官方 CLI 和新租户授权。每个平台各选一条公开数据检索路径，启动时默认接入 LibTV MCP，负责人明确只做图文时可跳过视频授权。旧项目的凭据、余额、用户身份和连接器授权均需在新环境独立核验。

## WorkBuddy 原版依赖

以已安装的 `self-media-leadgen` 1.0.0 专家定义、对应项目执行记录和供应商官方发布为依据。版本为盘点时的 WorkBuddy 本地版本。上游版本可能不同，安装后记录实际版本或 Git 提交。

| 原版组件 | 盘点状态 | 新环境接法 |
| --- | --- | --- |
| `scout-showcases`、`showcase-breakdown`、`produce-showcase-content`、`post-publication-review`、`manage-showcases` | 专家绑定的五项自制技能 | 随仓库提供，见 `.agents/skills/`。 |
| 飞书套件 `lark-unified` 2.3.0 | 专家绑定；原项目有官方 `lark-cli` 读写记录 | WorkBuddy 可从技能市场安装飞书套件。其他 Agent 使用官方 CLI 和它自带的 `lark-shared`、`lark-doc`、`lark-base`、`lark-drive`，使用 Wiki 时加 `lark-wiki`。见 [飞书初始化](feishu.md) 和 [官方 CLI](https://github.com/larksuite/cli)。 |
| 小红书关键词搜索、笔记详情获取、评论内容获取分析、博主作品监控助手 `xiaohongshu-search-tool-v4` 1.1.3 | 专家绑定；原项目调用过 GUAIKEI | `GUAIKEI_API_TOKEN`。从 [作者的小红书 CLI](https://github.com/um-why/xiaohongshu-openclaw-skill) 或 WorkBuddy SkillHub 的同名条目安装。 |
| 抖音内容洞察 `douyin-content-intelligence-guaikei` 1.0.0，包名 `guaikei-douyin-content-intelligence` | 专家绑定；原项目调用过 GUAIKEI，留有成功的结构化检索、作品与评论结果 | 使用同一供应商的 `GUAIKEI_API_TOKEN`，由供应商账户确认两个平台权限。从 [作者的抖音 CLI](https://github.com/um-why/douyin-search-openclaw) 或 WorkBuddy SkillHub 的同名条目安装。 |
| 抖音搜索分析 `douyin-search-and-analyze-guaikei`、抖音视频调研 `douyin-videos-for-research-guaikei`、抖音竞品监控 `guaikei-douyin-competitor-watch`、抖音智能爬虫 `douyin-zhineng-pachong`，均为 1.0.0 | WorkBuddy 另装的 GUAIKEI 相关技能。原检索技能提及「抖音搜索分析」，专家实际绑定的是「抖音内容洞察」 | 都声明使用 `GUAIKEI_API_TOKEN`，上游指向 [作者的抖音 CLI](https://github.com/um-why/douyin-search-openclaw)。按任务选一套所需能力。 |
| 抖音热榜 `douyin-hot-trend` 1.0.1、小红书作品爬取 `xiaohongshu-crawler` 1.0.0 | 原专家与检索技能列出的可选辅助；本次未验证成功调用 | 两项均使用 `REDFOX_API_KEY`。在 WorkBuddy 技能市场按名称安装，或按 [红狐热榜 Skill](https://github.com/redfox-data/redfox-community/tree/main/skills/douyin-hot-trend)、[红狐小红书作品爬取 Skill](https://github.com/redfox-data/redfox-community/tree/main/skills/xiaohongshu-crawler) 说明安装。 |
| 小红书爆款笔记查询 `xiaohongshu-search` 1.0.1、抖音热榜 / Douyin Hot `douyin-hot`（目录元数据 1.0.5，技能正文 1.0.1）、合一社媒数据 `heyi-paid-api` 1.1.1 | WorkBuddy 曾安装这些相近能力；专家未绑定，未找到相关项目的成功调用证据 | 前两项有需要时从 WorkBuddy 技能市场按准确名称查找。小红书爆款笔记查询使用 `REDFOX_API_KEY`。合一由其账户提供 `HEYI_API_KEY`，若本项目明确选用，从 [供应商站点](https://api.01011.top/) 或 SkillHub 同名条目查当前说明。 |
| 零一数科 `lingyi-wx-account-quick-analysis` 0.1.0（视频号账号极速拆解）、`lingyi-wx-video-decomposer-exp` 0.9.0（视频号短视频拆解）、`lingyi-wx-viral-script-generator` 0.7.0（视频号爆款脚本生成） | 本机安装；原检索技能把已知账号快拆和本地视频拆解列为下游能力。专家未绑定这三项，未找到相关项目成功调用证据 | WorkBuddy 技能市场按标识安装，也可从 [零一数科官方入口](https://claw.lingyishuke.com/skills/) 查询供给。账号快拆及脚本进阶档使用 `LY_API_KEY`。本地视频拆解使用 FFmpeg/ffprobe 和视觉模型，已装版本会将报告正文登记到供应商服务。脚本体验档也有内容登记。启用前核对当前版本的数据提交范围和费用。已授权的原帖或本地素材，可直接按仓库 `showcase-breakdown` 拆解并用 `produce-showcase-content` 出稿。 |
| `libtv@workbuddy-connector-plugins-official` 1.1.2 | 专家指定的普通视频生产连接器；本次未验证原项目成片或新账户配额 | 使用独立项目账号授权。支持 OAuth 的 Agent 可连接官方 HTTP MCP，Codex 可安装官方 `libtv@libtv`。详见下节与 [LibTV 官方插件](https://github.com/liblib-ai/marketplace)。 |
| `libtv-to-treatment`、`libtv-blender-live-action`、`music-driven-product-ad` | 原 LibTV 连接器随附专项技能，针对导演提案、Blender 运镜、配乐广告 | 仅在明确需要对应产物时，从 [LibTV 官方插件](https://github.com/liblib-ai/marketplace) 获取，并按其授权、运行环境和素材许可执行。 |
| WorkBuddy 内置 `expert-manager`，包名 `skill-expert-manager` 0.1.0 | 实际调用过，用于专家创建、挂载和安装管理 | WorkBuddy 原生提供。其他 Agent 用本仓库 `AGENTS.md` 做入口，原运行时没有自动发现时按阶段直接读取对应 Skill。参见 [WorkBuddy 专家结构](https://open.workbuddy.cn/docs/expert)。 |
| WorkBuddy 内置 `skill-creator`、`marketplace-skill-installer`、`recommend-connectors`、`buddy-multimodal-generation` | 原客户端可见的辅助技能，未找到它们是该专家运行的硬依赖 | WorkBuddy 自带。其他 Agent 分别使用自身的技能目录或本仓库的文件入口、供应商安装说明、工具发现和媒体生成能力。参见 [WorkBuddy 技能管理](https://indonesia.tencentcloud.com/document/product/1316/84503)。 |
| WorkBuddy 原生 `ToolSearch`、`DeferExecuteTool`、`ImageGen`、`WebFetch`、文件读写、Bash；官方插件 `playwright-cli@codebuddy-plugins-official` 0.1.0 | 历史任务用过工具发现、图片生成、网页读取和文件操作；相邻任务有 Playwright 调用 | 使用 Agent 的同等工具；浏览器可选，使用环境原生浏览器或 [Playwright 官方安装说明](https://playwright.dev/docs/intro)。图库、图像生成和检索连接器分别按权限预检。 |

从供应商入口安装第三方代码，本仓库提供依赖标识和迁移路径。GUAIKEI 是已核实的原项目采集供应商，历史充值金额、余额、额度和两个平台在新账户的授权需由负责人在供应商账户核验。

### WorkBuddy 客户端自带能力对照

以下来自本机 WorkBuddy 5.9.3 的内置包清单，覆盖 19 个 `skill` 条目和 5 个内置插件。面向本专家的初始化只启用上表中本项目实际选用的能力。清单中的通用能力随客户端分发，其他 Agent 可按实际工作选用对应能力。随客户端版本、租户与安装状态变化的所有动态技能、工具和连接器，以当前运行环境的清单为准。参见 [WorkBuddy 技能管理](https://indonesia.tencentcloud.com/document/product/1316/84503)。

| 用途 | 内置包（列出实际清单版本） | 跨 Agent 对接 |
| --- | --- | --- |
| 专家、技能和连接管理 | `skill-expert-manager` 0.1.0、`skill-skill-creator` 0.1.0、`skill-marketplace-skill-installer` 0.1.0、`skill-recommend-connectors` 0.1.1、`skill-recommend-experts` 0.1.1 | `AGENTS.md`、本地 `SKILL.md`、运行环境工具发现、供应商安装与授权。 |
| 设计和多媒体 | `skill-ardot-design-core` 0.1.4、`skill-ardot-design-router` 0.1.2、`skill-ardot-design-to-code` 0.1.2、`skill-ardot-ui-design` 0.1.1、`skill-ardot-poster` 0.1.1、`skill-ardot-slides` 0.1.2、`skill-livestream-poster` 0.1.2、`skill-buddy-multimodal-generation` 0.1.0 | 使用项目媒体工作流和宿主的图像、视频或设计工具。Ardot 的设计服务另有 `mcp-ardot-mcp-app` 0.1.0。 |
| 资料、办公和应用 | `skill-library` 0.5.13、`skill-tencent-docs-routing` 0.1.2、`skill-tencent-local-office-edit` 0.0.2、`skill-sites` 0.1.1；插件 `tencent-docs-plugin` 1.0.3、`sheetagent` 0.1.1787966564、`tencent-pptx` v20260825、`tencent-docx` 0.4.1 | 项目资料和案例按本仓库规则存入新飞书或项目目录。其他办公和网站任务使用 Agent 已获授权的同类工具。 |
| 行业与支付 | `skill-wb-finance-skill` 0.1.0、`skill-geo-map-compliance-guard` 0.1.0；插件 `weixinpay` 1.6.108 | 与本专家的日常获客工作分开接入，项目要求时使用相应领域工具。 |

## 检索能力安装和验收

1. 选择本轮覆盖的平台及其数据路径。结构化检索可选 GUAIKEI，红狐提供替代的作品搜索、账号搜索及详情能力。若账号尚未授权，可用公开网页、平台公开入口或负责人给出的链接开始。用可访问的原帖核验，按实际覆盖记录可见互动、评论及证据缺口，无法访问记为未知。
2. 使用 GUAIKEI 时，准备 Node.js 16.14.0 或以上。用上表的 GitHub 源将两个仓库分别检出到模板仓库之外的依赖目录，也可使用 WorkBuddy 官方技能市场。核对根目录 `SKILL.md`、`package.json`、下表脚本和实际提交。供应商声明两套工具使用同一个环境变量，通过 [GUAIKEI 官网](https://www.guaikei.com/) 开通并由负责人为当前项目授权。先执行 `node --version` 和 `node --check <入口脚本>` 检查本地运行环境。选了抖音或小红书时，Agent 主动请负责人通过安全凭据入口配置这把 Key，等待授权后核验。密钥存在性只报告有或无。
3. 从对应供应商仓库根目录按下表运行。下列真实查询可能消耗额度，先核对当前项目预算和授权。从一条公开搜索、少量结果开始，再按需抽查一个作品链接或公开评论。判断业务结果时检查返回 JSON 的 `status`、`error_code`、`results` 和来源可访问性。空结果与请求失败分别登记。遇鉴权错误先修正授权，避免重复请求。上游工具可能在自己的目录生成日志，保留在项目私有工作区或依赖目录。

| 平台 | 最小关键词查询示例 | 按需核验 |
| --- | --- | --- |
| 小红书 | `node src/xiaohongshu/search-cli.js --keyword "露营装备" --limit 5` | `detail-cli.js --url <原笔记链接>`、`comment-cli.js --url <原笔记链接> --limit 5`、`post-cli.js --url <公开主页链接> --limit 5`。笔记原链接保留平台要求的签名参数，只在授权项目里保存。 |
| 抖音 | `node src/douyin/search-cli.js --keyword "露营装备" --limit 5` | `post-cli.js --url <公开主页链接> --limit 5`、`comment-cli.js --url <原作品链接> --limit 5`。`detail-cli.js` 和 `hot-cli.js` 在上游有对应能力，按所安装版本核对入口。 |

如选红狐，优先按 [红狐官方文档](https://redfox.hk/) 接入对应平台 MCP 或 [官方 Python SDK](https://github.com/redfox-data/redfox-python-sdk)，从工具清单确认 `search_works`、`search_users`、`get_work` 等本轮所需能力。用 `REDFOX_API_KEY` 完成鉴权后，再按同样口径检查一条获授权的查询和原帖。热榜只用于拓词。合一仅在明确选用时按供应商当前目录确认接口及计费，用供应商提供的匿名目录检查，实际搜索再单独验收。视频号、Threads 或其他平台缺少授权数据源时，记录站内或公开索引的覆盖范围和不可见指标。

## 图文和视频能力

在 Codex 接入 LibTV 时，可运行供应商提供的两条安装命令，然后重新加载插件，在 MCP 连接管理中请负责人完成 OAuth。其他 Agent 用各自的 MCP 管理入口。 [LibTV 官方安装说明](https://github.com/liblib-ai/marketplace#安装)

```sh
codex plugin marketplace add https://github.com/liblib-ai/marketplace.git --ref main
codex plugin add libtv@libtv
```

- **图文**默认交付逐页制作包。能生成图像时用 Agent 原生生图或负责人已选的工具。可把同一制作包交给 Codex 的图像能力。选择直接调用 OpenAI API 时，单独配置 `OPENAI_API_KEY` 并核对额度授权。是否交付实图以实际输出为准。参见 [Codex 图像能力](https://openai.com/index/introducing-the-codex-app/) 和 [OpenAI 图像 API](https://developers.openai.com/learn/imagegen)。
- **LibTV HTTP MCP**使用 `https://mcp.liblib.tv/mcp`。WorkBuddy 在官方连接器市场接入，Codex 按供应商说明安装 `libtv@libtv`，支持 HTTP MCP 和 OAuth 的其他 Agent 在自身连接管理中填地址，由用户登录。初始化时主动发起连接和登录请求，收到用户确认后再核验，生产或扣费另按项目授权。接通后读取服务返回的 instructions 和 tools list。如工具清单提供 `doctor`，先用它或同等只读能力核验身份、可见项目和工具权限。逐项检查当前账号可否上传、生成、合成、导出。登录成功只证明连接，获授权的短样片完成并回放后才能报告成片链路已实测。[LibTV 官方插件](https://github.com/liblib-ai/marketplace)
- **LibTV CLI 备选**适用于没有 OAuth MCP 客户端的执行环境。供应商 [libtv-labs/libtv-skills](https://github.com/libtv-labs/libtv-skills) 的 `libtv-skill` 通过 `LIBTV_ACCESS_KEY` 提供素材上传、生成会话、进度查询与下载。先验证项目归属和当前账号配额。独立检查合成、时间轴和导出是否满足本项目验收。仅能生成片段时，按授权使用其他合成工具，或者交分镜、提示词、素材清单和待办。

凭据通过执行环境的凭据入口注入，飞书应用配置与 LibTV OAuth 按各自官方流程完成。只将依赖版本、能力、实测状态和非敏感故障摘要写入 `.project/readiness.md`。待审成品、平台发布、对外消息及定时任务分别按本项目授权处理。
