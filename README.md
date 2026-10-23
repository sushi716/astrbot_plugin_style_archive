# astrbot_plugin_style_archive

**语料归档器**：把机器人看到的文字消息按天写成 JSONL，并标记出哪些是"账号主人"自己发的。
用途：攒够语料后做"学我说话"的风格微调 / few-shot 提取。

## 输出格式

`<archive_dir>/2026-10-23.jsonl`，每行一条：

```json
{"ts": "2026-10-23 21:14:02", "umo": "group:123456789", "kind": "group",
 "group": "123456789", "sender": "100000000", "name": "示例用户",
 "is_owner": true, "scene": "group", "text": "今天累死了"}
```

| 字段 | 说明 |
|---|---|
| `ts` | 本地时间 |
| `umo` | 会话唯一标识（AstrBot 的 unified_msg_origin） |
| `kind` | `group` / `friend` |
| `group` | 群号（私聊为空串） |
| `sender` | 发送者 QQ |
| `name` | 发送者昵称（截断 32 字） |
| `is_owner` | 这条是不是"你"（`OWNER_QQ` 里）写的 |
| `scene` | `group` / `chat` |
| `text` | 正文 |

## 过滤规则

- 机器人**自己**发的消息跳过（`sender == self_id`）
- 纯图片 / 语音 / 表情包没有文字 → 跳过
- 长度不在 2–2000 字之间 → 跳过

## 安装

```bash
cd <AstrBot>/data/plugins
git clone https://github.com/sushi716/astrbot_plugin_style_archive
```

## 配置（环境变量，在 AstrBot 进程环境里设）

| 变量 | 默认 | 说明 |
|---|---|---|
| `STYLE_ARCHIVE_DIR` | `<插件目录>/archive` | 归档目录 |
| `OWNER_QQ` | 空 | 你自己的 QQ，多个用逗号分隔；这些消息标 `is_owner=true` |

## ⚠️ 隐私提示

这个插件会把**聊天原文落盘**。请：

- 只在自己的机器上开
- 定期清理归档目录
- 不要把 `archive/` 提交进任何公开仓库（`.gitignore` 已默认排除）

## 兼容性

AstrBot v4.x（实测 v4.27.2）。纯本地写文件，无网络请求。

## 许可

MIT
