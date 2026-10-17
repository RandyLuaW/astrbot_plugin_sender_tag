# 更新日志

所有重要变更记录于此。格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循[语义化版本](https://semver.org/lang/zh-CN/)。

## [1.1.0] - 2026-10-17

首个开源版本（GitHub 公开 + AstrBot 插件市场适配）。

### 新增

- **WebUI 可视化配置**（`_conf_schema.json`）：`enabled` 总开关、`include_qq` 是否附 QQ 号、`tag_private_chat` 私聊是否标注、`max_name_len` 昵称截断、`separator` 分隔符。
- **幂等保护**：prompt 已以同样前缀开头时跳过，插件重载或多插件叠加都不会出现重复前缀。
- 插件加载日志：启动时输出当前生效的标注策略，便于排查。
- 插件市场元数据（`display_name` / `repo` / `astrbot_version` / `support_platforms` / `tags`）与插件图标 `logo.png`。

### 变更

- 默认行为保持与 v1.0.0 一致：群聊标注、带 QQ 号、私聊不标注、昵称不截断。

## [1.0.0] - 2026-10-16

### 新增

- 首个版本：在 LLM 请求前给群聊消息注入「昵称(QQ号): 」前缀，随会话历史持久化。
- 支持 `sender_tag_skip` extra 标记：上游已自带说话人信息时跳过标注，避免前缀叠加。
- 标注失败只记日志，不影响主流程回复。
