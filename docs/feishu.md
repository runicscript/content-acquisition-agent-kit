# 为新项目配置飞书

每个项目使用独立仓库副本和独立飞书租户中的新应用。初始化会建立一个项目文件夹、一份产品与推广线说明、三份文档模板，以及包含「候选池」和「Showcase」的多维表格。模板的结构来自 [templates](../templates)，字段来自 [schema/feishu.json](../schema/feishu.json)。

## 本地预览

在仓库根目录执行，替换项目编号和名称。只有预览时无需飞书 CLI 或凭据。

```sh
python3 scripts/feishu_setup.py --project demo --project-name '新项目名称'
```

默认时区为 `Asia/Shanghai`。按项目需要使用 `--timezone Asia/Taipei` 等 IANA 时区。Python 缺少时区数据时，先安装系统时区数据库或 Python 的 `tzdata` 包。准备已获授权上传的产品简介 `.project/brief.md`。正文仅需产品事实、目标人群、推广线、真实入口、线索及业务结果定义，涉及客户或内部信息时先确认其可进入目标租户。

## 单独创建并授权应用

安装 [官方 lark-cli](https://github.com/larksuite/cli#install)。这套初始化使用 1.0.86 的本地 CLI 命令契约。可用 `npm install --global @larksuite/cli@1.0.86` 安装。没有全局安装权限时，可用 `npm install --prefix .project/tools @larksuite/cli@1.0.86`，将 `.project/tools/node_modules/.bin` 加到运行脚本的 `PATH`。使用其他版本时先用 `--help` 检查命令。通过内嵌技能获取对应版本的飞书用法。

```sh
lark-cli skills read lark-shared
lark-cli skills read lark-drive
lark-cli skills read lark-doc
lark-cli skills read lark-base
python3 scripts/feishu_setup.py --project demo --lark config init --new
```

Agent 在后台运行配置命令，将返回的原始验证链接及二维码交给用户。用户在浏览器选择**新项目的目标租户**完成应用创建。若使用已在新租户后台创建的项目专用应用，走以下方式。App Secret 由用户通过终端隐藏输入或通过运行环境的机密注入提供。

```sh
python3 -c 'import getpass; print(getpass.getpass("Feishu App Secret: "))' |
  python3 scripts/feishu_setup.py --project demo --lark profile add \
    --app-id "$NEW_FEISHU_APP_ID" --app-secret-stdin --brand feishu
```

CLI 配置位于忽略提交的 `.project/lark-cli/`，profile 名为 `acq-demo`。凭据由飞书 CLI 的机密存储管理。每次命令都显式指定 profile，脚本会清理继承的飞书 CLI 配置、凭据与代理变量，再使用本项目的目录。该入口固定使用独立项目配置，包括在 OpenClaw 或 Hermes 环境运行时。Lark 国际版使用手工创建应用的方式，并在注册 profile、检查身份及首次应用时传 `--brand lark`。

开通新应用的用户权限并发布可用版本。只为这套运营启用云空间、文档和多维表格所需权限。云空间需要列文件和建文件夹，文档需要创建、读取和定点更新，多维表格需要创建 Base、读写所需表结构及记录。初始 Base 命令会以自定义首表替换它本次新建的默认空表，因此需要该命令要求的表删除权限。CLI 返回 `missing_scopes` 时按提示给本应用补对应权限，再向同一用户补授权。授权只在目标新租户下完成。

```sh
python3 scripts/feishu_setup.py --project demo --lark auth login \
  --domain docs --domain drive --domain base --no-wait --json
python3 scripts/feishu_setup.py --project demo --lark auth qrcode \
  "$VERIFICATION_URL" --output .project/feishu-auth.png
```

将原始验证链接和二维码交给用户，等用户确认完成。随后在同一项目工作环境执行 `python3 scripts/feishu_setup.py --project demo --lark auth login --device-code "$DEVICE_CODE"`。配置或登录返回的短期设备码留在授权流程，勿写进 Git 或交付报告。

## 建立并回读项目

从新应用管理页确认 App ID。目标租户的 tenant key 需由负责人通过新租户的可信信息或有权管理员独立确认。若需要查看刚授权的实际租户，可先运行以下只读命令。请比对它与已知的目标租户，禁止把脚本读取到的租户值自动当作期望值。

```sh
python3 scripts/feishu_setup.py --project demo --identity --app-id "$NEW_FEISHU_APP_ID"

python3 scripts/feishu_setup.py --project demo --project-name '新项目名称' \
  --brief .project/brief.md --apply --app-id "$NEW_FEISHU_APP_ID" \
  --tenant-key "$NEW_FEISHU_TENANT_KEY"

python3 scripts/feishu_setup.py --project demo --verify
```

`--apply` 在写入前同时核对 profile、应用、租户和实际 OAuth 用户。首次绑定落在 `.project/feishu.json`，包含资源 ID、可获得的链接和表字段映射，后续仅复用已登记的资源。`--verify` 复核绑定、文件夹、Base、两张表的字段类型与 ID、四个文档可读性。上传简介只发生在首次创建对应文档时。后续变更从实际项目文档做定点更新。

中断后先按原参数重跑，脚本会逐项回读。同名资源只有当前步骤已记为待确认时才能恢复登记。如果上次创建结果不明且查询暂时没有结果，脚本会停止。先在新租户确认远端结果，只有核实上次请求未创建资源才加 `--retry-pending`。如果已创建却缺字段或保留默认表，先在新项目 Base 内核查，修正后重跑。保留状态文件以便恢复。若上次进程异常退出且锁文件残留，确认旧进程停止后再移除 `.project/feishu.lock`。

## 日常运营

所有飞书操作经过同一入口，例如：

```sh
python3 scripts/feishu_setup.py --project demo --lark base +record-list \
  --base-token "$PROJECT_BASE_TOKEN" --table-id "$CANDIDATE_TABLE_ID" --format json

python3 scripts/feishu_setup.py --project demo --lark docs +fetch \
  --doc "$PROJECT_DOC_ID" --doc-format markdown
```

映射中的 `folder`、`base`、`table.showcases`、`table.candidates` 与 `doc.*` 是唯一初始资源来源。包装入口会再次核对真实应用、租户与用户，数据表操作限制在登记的 Base 和表。文档新建必须在项目文件夹内，读取和更新必须传该目录直属文档 ID。包装入口自动加 `--as user`，允许文档创建、读取和追加或定点编辑，允许字段读取和记录读取、搜索、创建及更新。

候选池按「产品＋推广线 ID＋平台＋对象类型＋平台对象 ID 或稳定定位」去重，保留人工状态和备注。Showcase 一行一个选定作品，三列指向真实案例、拆解和方案文档，有效评级单列记录。发布和复盘归入实际使用的方案版本。写入前分页查重并核对字段，写后按返回的记录 ID 回读。更新时仅传已核实字段。CLI 的 `+record-upsert` 在省略 `--record-id` 时创建新行，业务键去重由运营流程负责。对于超时或受理后断线的创建，先按业务键查结果。

平台后台权限与第三方工具各自授权。完成飞书配置只意味着工作区可用。首次真实试跑由负责人确认推广线、平台读取权限及素材后开始。
