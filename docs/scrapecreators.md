# 海外社媒检索

ScrapeCreators 是 TikTok、YouTube、Facebook、Instagram、Threads 等海外平台的公开数据依赖。新项目先确认目标平台。选择相关平台时，在技能配置阶段安装上游包并主动请求负责人授权。抖音和小红书沿用各自的 GUAIKEI 路径。 [官方技能仓库](https://github.com/ScrapeCreators/social-media-research-skills) · [接口目录](https://docs.scrapecreators.com/)

## 安装与验收

在**目标 Agent 的项目环境**里确认有 Node.js 和 `npx`，执行供应商的安装命令。安装器询问目标时选当前项目和宿主。已有安装时先核对来源、技能目录和版本，确认符合要求即可复用。

```sh
npx skills add ScrapeCreators/social-media-research-skills
```

宿主支持技能发现时，核对 `scrapecreators-api` 和本轮选用技能的 `SKILL.md` 确实可读。无自动发现时，按上游目录取得所需技能及引用文件，用宿主的导入入口或让 Agent 按路径直接读取。安装是否完成，以目标 Agent 能读取对应技能为准。 [官方安装说明](https://docs.scrapecreators.com/integrations/agent-skill/)

主动请负责人从 [ScrapeCreators 控制台](https://app.scrapecreators.com) 获取 API Key，通过宿主的机密设置注入 `SCRAPECREATORS_API_KEY`，并确认本项目可使用多少现有额度。Key 只用于供应商 API 的鉴权请求，聊天、日志和 Git 文件均不保存明文。存在性检查只报告已设置或未设置。先查看当期接口费用，获得额度授权后再用一个请求验收本轮所需的搜索或字幕路径。请求耗用免费额度也算用量。记录「已安装」「已配置待实测」「已实测」或具体阻塞。额度用尽时停止请求，按项目许可使用公开网页、平台原生入口或用户提供的链接。 [官方认证与响应说明](https://docs.scrapecreators.com/)

### macOS zsh 中配置 Key

临时配置可在当前终端隐藏输入。然后从该终端启动 Agent，让它继承环境变量。

```zsh
read -rs 'SCRAPECREATORS_API_KEY?ScrapeCreators API Key: '
printf '\n'
export SCRAPECREATORS_API_KEY
```

长期配置可用 macOS「钥匙串访问」新建密码项目，项目名填 `ScrapeCreators`，账户填当前 macOS 用户名。把以下两行加入 `~/.zshrc`，让新的交互式 zsh 从钥匙串加载 Key。桌面或云端 Agent 使用自己的机密入口，因为它们未必继承终端环境。

```zsh
SCRAPECREATORS_API_KEY="$(security find-generic-password -a "$USER" -s ScrapeCreators -w 2>/dev/null)"
export SCRAPECREATORS_API_KEY
```

## 主要技能

| 上游 Skill | 何时调用 |
|---|---|
| `scrapecreators-api` | 核对指定平台的搜索、帖子、字幕或评论接口，确认参数、分页及用量。 |
| `outlier-post-finder` | 找明显高于同账号近期基准的作品，标注样本和实际可见指标。 |
| `transcript-intelligence` | 从可取得的字幕提取开头、论点、结构和行动引导，保留来源。 |
| `comment-mining` | 从授权可见的评论归纳提问、异议、需求和购买意向信号。 |
| `competitor-social-research`、`creator-profile-teardown` | 比较竞品账号与内容主题，找可借鉴的表现方式和成立条件。 |
| `trend-discovery`、`social-listening-brief`、`product-demand-research` | 发现趋势、整理公开讨论并提炼需求线索。 |
| `ad-library-teardown` | 研究广告素材、卖点和 CTA。广告库与自然内容分开取样。 |
| `influencer-prospecting`、`audience-research`、`content-repurposing` | 按需用于创作者筛选、受众适配分析和素材再创作。 |

直接描述任务即可触发。需要指定工具时，对 Agent 说「使用 `scout-showcases` 和 `scrapecreators-api`」，再点名需要的字幕或评论技能。候选保存和审核规则沿用本仓库业务技能。 [上游技能目录](https://github.com/ScrapeCreators/social-media-research-skills#available-skills)

## 可直接使用的提示词

1. **TikTok 搜索与分析**。用 ScrapeCreators 搜 TikTok 近 30 天的「[主题]」公开短视频，先取一页，最多交 5 个待选作品。标明原链接、作者、发布时间、可见指标和适合借鉴的获客机制。需要追加查询时先说明额度。 [TikTok 关键词搜索](https://docs.scrapecreators.com/v1/tiktok/search/keyword/)
2. **YouTube 字幕拆解**。用 `transcript-intelligence` 和 `showcase-breakdown` 读 [视频链接] 的公开字幕，按时间码拆开场、论证、演示话术和 CTA。画面证据单列，字幕不可用就标明缺口。 [YouTube 字幕接口](https://docs.scrapecreators.com/v1/youtube/video/transcript/)
3. **Facebook 内容检索**。用 ScrapeCreators 搜「[主题]」的公开 Facebook 视频和 Reels，先取一页，交原链接及可见互动。另有指定主页或群组链接时，可用对应公开帖子入口取样。文本和图片帖不属于这项关键词搜索的覆盖范围。 [Facebook 视频搜索接口](https://docs.scrapecreators.com/v1/facebook/search/videos/)
