<div align="center">

# 让 LLM 知道「这句话是谁说的」

<img src="https://count.getloli.com/@astrbot_plugin_sender_tag?name=astrbot_plugin_sender_tag&theme=rule34&padding=6&offset=0&align=top&scale=1&pixelated=1&darkmode=auto" alt="count" />

**AstrBot 群消息说话人标注插件：给进入会话历史的每条群聊消息加「昵称(QQ号): 」前缀，多人对话不再张冠李戴。**

![AstrBot](https://img.shields.io/badge/AstrBot-%3E%3D4.17-5865f2?style=flat-square)
![Version](https://img.shields.io/badge/version-1.1.0-22c55e?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776ab?style=flat-square)
![Platform](https://img.shields.io/badge/platform-aiocqhttp-f97316?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-3b82f6?style=flat-square)

简体中文 | [English](README_EN.md)

<img src="logo.png" alt="群消息说话人标注 Logo" width="180">

</div>

> 📦 **规范性说明**：本仓库是一个 [AstrBot](https://github.com/AstrBotDevs/AstrBot) **插件组件仓库**，仅作为 AstrBot 的插件使用，不能独立运行。请将本插件安装至 AstrBot 的 `data/plugins/` 目录，由 AstrBot 框架加载并调度。

---

## 目录

- [它解决什么问题](#它解决什么问题)
- [效果示例](#效果示例)
- [安装](#安装)
- [配置项](#配置项)
- [工作机制](#工作机制)
- [与其他插件的配合](#与其他插件的配合)
- [注意事项](#注意事项)
- [版本历史](#版本历史)

---

## 它解决什么问题

AstrBot 的会话历史是**按会话（群）存**的：同一个群里所有人的消息，进入历史后都只是一条条 `user` 消息，**不带说话人信息**。

单人群聊里没问题，多人聊天就会翻车：

- 张三说「我今天不想上班」，李四接一句「我也是」——模型分不清这两句是谁说的，回应时容易把情绪、身份、要求错配到别人身上；
- 群里同时在聊两三个话题，模型容易把 A 的提问答到 B 头上；
- 隔几轮之后，模型甚至会把某个人的口头禅当成另一个人的设定。

本插件在**发给 LLM 之前**给群聊消息加上 `昵称(QQ号): ` 前缀，并且这个前缀会**随会话历史一起持久化**——于是后续每一轮，历史里的每条消息都带着说话人标签，模型能稳定地区分「谁说了什么」。

---

## 效果示例

未开启：

```
user: 我今天不想上班
user: 我也是，昨天加班到十点
user: 你们公司还招人吗
```

开启后：

```
user: 张三(123456): 我今天不想上班
user: 李四(654321): 我也是，昨天加班到十点
user: 王五(112233): 你们公司还招人吗
```

模型从此能准确回答「王五问的招聘」而不是把话题接到张三身上。

---

## 安装

### 方式一：插件市场（推荐）

AstrBot WebUI → 插件管理 → 从插件市场安装，搜索 `astrbot_plugin_sender_tag` 或「群消息说话人标注」。

### 方式二：Releases 下载

前往 [Releases](../../releases) 页下载最新版安装包（`astrbot_plugin_sender_tag-vX.Y.Z.zip`），在 AstrBot WebUI「插件管理 → 上传安装」中导入。

### 方式三：手动克隆

```bash
cd AstrBot/data/plugins
git clone https://github.com/RandyLuaW/astrbot_plugin_sender_tag.git
```

> [!TIP]
> 无第三方依赖，装上即生效（群聊默认开启），不需要额外配置。

---

## 配置项

| 配置 | 说明 | 默认值 |
|------|------|--------|
| `enabled` | 总开关，关闭后不再修改 prompt | `true` |
| `include_qq` | 前缀是否附带 QQ 号（关闭后只用昵称，省 token） | `true` |
| `tag_private_chat` | 私聊是否也标注（私聊只有一人，默认关闭） | `false` |
| `max_name_len` | 昵称最大长度，超出截断，`0` = 不截断 | `0` |
| `separator` | 昵称与正文之间的分隔符 | `": "` |

---

## 工作机制

```
群消息 → AstrBot 组装 LLM 请求（req.prompt = 消息正文）
                │
                ├─ 命中跳过标记（sender_tag_skip）──► 不动（上游已自带说话人信息）
                ├─ 私聊且未开启 tag_private_chat ──► 不动
                ├─ prompt 为空（纯图片/语音）──► 不动
                └─ 其他 ──► req.prompt = "昵称(QQ号): " + 正文
                                    │
                                    └─ 随会话历史持久化，后续轮次依然带标注
```

实现要点：

- 使用 `@filter.on_llm_request()` 钩子，在请求真正发往模型前改写 `req.prompt`；
- **幂等**：若 prompt 已经以同样前缀开头，直接跳过，插件重载或多插件叠加都不会出现「张三(123): 张三(123): …」；
- **失败不影响主流程**：任何异常都只记日志，prompt 保持原样，绝不会因为标注失败而让 Bot 不回复。

---

## 与其他插件的配合

主动回复类插件（如 [astrbot_plugin_active_reply_ctl](https://github.com/RandyLuaW/astrbot_plugin_active_reply_ctl)）在触发时会自己拼一段模板文本，其中已经包含「成员【张三】发了一条消息」这类信息。若再叠加前缀，就会出现：

```
张三(123456): 群里张三发了一条没有 @ 你的消息，内容：……
```

这类请求只要在 `event.set_extra("sender_tag_skip", True)` 上打标记，本插件就会跳过，不再重复标注。上面提到的主动回复插件已内置该标记。

---

## 注意事项

> [!IMPORTANT]
> 本仓库仅为 AstrBot 插件组件，需随 AstrBot 一起使用，无法独立运行。

- 标注会**略微增加 token 消耗**（每条消息多几个字）。群很活跃、预算敏感时可关闭 `include_qq` 或调小 `max_name_len`
- 前缀会进入持久会话历史；若中途关闭本插件，历史里已有的前缀不会自动清除（一般无害，模型能理解）
- 只在有「群」概念的适配器下生效（`aiocqhttp` 已测试）；私聊需显式开启 `tag_private_chat`
- 昵称由平台上报，可能与群名片不一致；需要唯一识别时请保留 QQ 号

---

## 版本历史

### v1.1.0
- 新增 WebUI 可视化配置：总开关、是否带 QQ 号、私聊标注、昵称截断、分隔符
- 新增幂等保护（重复前缀不再叠加）与插件加载日志
- 完成插件市场适配（元数据、图标、双语 README）

### v1.0.0
- 首个版本：群聊 LLM 请求前注入「昵称(QQ号): 」前缀，随会话历史持久化；支持 `sender_tag_skip` 跳过标记

完整变更记录见 [CHANGELOG.md](CHANGELOG.md)。

---

## 致谢

- 主页排版参考同作者的 [astrbot_plugin_active_reply_ctl](https://github.com/RandyLuaW/astrbot_plugin_active_reply_ctl)
- 访客计数由 [Moe Counter](https://github.com/journey-ad/Moe-Counter) 提供

---

**🌟 如果这个插件对你有帮助，请给个 Star 支持一下！**

## 许可证

[MIT](LICENSE) © Randy Lua
