<p align="center">
  <img src="../assets/session-alarm-logo.svg" width="176" alt="Session Alarm 标志">
</p>

<h1 align="center">Session Alarm</h1>

<p align="center">
  <strong>不必一直盯着你的编程智能体。</strong><br>
  当 Codex 或 Claude Code 需要你时，用动物声音提醒你。
</p>

<p align="center">
  <a href="https://github.com/djfksjd/session-alarm/actions/workflows/ci.yml"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/djfksjd/session-alarm/ci.yml?branch=main&style=flat-square&label=CI"></a>
  <a href="../LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/license-MIT-2EC4B6?style=flat-square"></a>
  <img alt="Python 3.9+" src="https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat-square&logo=python&logoColor=white">
  <img alt="12 sounds" src="https://img.shields.io/badge/真实动物声音-12-FFB703?style=flat-square">
</p>

<p align="center">
  <a href="../README.md">English</a> ·
  <a href="README.ko.md">한국어</a> ·
  <a href="README.ja.md">日本語</a> · 简体中文 ·
  <a href="README.es.md">Español</a>
</p>

---

Session Alarm 是专为 **Codex 和 Claude Code** 设计的生命周期钩子通知插件。当智能体
需要输入、完成当前轮次、因错误停止或结束会话时，它会播放声音，并可显示桌面通知。

内置 12 种声音都是真实动物的短录音。每个选定声音在获取时都由其 Freesound 独立页面
标记为 CC0 1.0 Universal；清单记录准确页面、贡献者、公开预览和处理后 WAV 的 SHA-256。
也可以添加自己制作或已获授权的 WAV；用户文件始终保存在本机。

<table>
  <tr>
    <td width="25%" align="center"><strong>🔔 确定性触发</strong><br>由生命周期钩子运行，不依赖模型记忆。</td>
    <td width="25%" align="center"><strong>🐈 12 种动物</strong><br>选择真实动物录音或添加自己的 WAV。</td>
    <td width="25%" align="center"><strong>🛡️ 许可已核验</strong><br>公开商业使用条件、来源、核验日期和校验和。</td>
    <td width="25%" align="center"><strong>🏠 完全本地</strong><br>无账户、服务器、分析、遥测或网络请求。</td>
  </tr>
</table>

## 何时提醒

| 事件 | Codex | Claude Code | 默认声音 |
|---|---|---|---|
| 需要输入 | 权限请求或以问题结束的响应 | 权限、选择对话框、后台智能体输入请求或问题 | 猫 |
| 工作完成 | 当前响应停止 | 当前响应停止或后台智能体完成 | 公鸡 |
| 错误 | 可用的错误事件 | `StopFailure` | 乌鸦 |
| 会话结束 | `SessionEnd` | `SessionEnd` | 猫头鹰 |

> [!NOTE]
> “工作完成”表示智能体完成了当前轮次。检测到后台任务或会话计划仍在运行时，
> Session Alarm 会抑制完成提示音。

## 安装

### Codex

```bash
codex plugin marketplace add djfksjd/session-alarm
codex plugin add session-alarm@session-alarm
```

打开新的 Codex 线程，在 `/hooks` 中检查并信任 Session Alarm 的命令。随时可运行：

```text
$session-alarm
```

### Claude Code

```bash
claude plugin marketplace add djfksjd/session-alarm
claude plugin install session-alarm@session-alarm
```

启动新会话或运行 `/reload-plugins`，然后配置：

```text
/session-alarm:session-alarm
```

### 本地运行

```bash
git clone https://github.com/djfksjd/session-alarm.git
cd session-alarm
python3 plugins/session-alarm/scripts/session_alarm.py setup
```

需要 Python 3.9 或更高版本。macOS 使用 `afplay`，Linux 使用
`paplay`、`aplay` 或 `ffplay`，Windows 使用 `winsound`。

## 首次配置

首次设置向导可以浏览并试听完整目录、添加自己的 WAV，分别选择“需要输入、完成、错误、会话结束”的声音，
设置音量、桌面通知和可跨越午夜的免打扰时段。Codex 与 Claude Code 共享同一份本地配置。

```bash
# 查看目录
python3 plugins/session-alarm/scripts/session_alarm.py catalog

# 试听猫
python3 plugins/session-alarm/scripts/session_alarm.py preview cat --volume 70

# 按顺序试听全部 12 种声音（停止：Ctrl+C）
python3 plugins/session-alarm/scripts/session_alarm.py preview-all --volume 40

# 添加并试听自己的 WAV（最长 30 秒 / 32 MB）
python3 plugins/session-alarm/scripts/session_alarm.py custom add "./my-sound.wav" \
  --name "My Sound" --id my-sound --preview

# 测试全部四个事件
python3 plugins/session-alarm/scripts/session_alarm.py test all
```

## 12 种真实动物声音

| 类别 | 动物 |
|---|---|
| 宠物 | 猫、狗 |
| 农场 | 牛、马、猪、山羊、绵羊、公鸡 |
| 鸟类 | 猫头鹰、乌鸦 |
| 小型生物 | 青蛙、蟋蟀 |

音频已针对短通知进行标准化。请参阅[声音来源与许可](../SOUND_LICENSE.md)。

## 隐私与许可

配置、导入的 WAV 和生成缓存只保存在 macOS/Linux 的 `~/.config/session-alarm/` 或 Windows 的
`%APPDATA%\session-alarm\`。本项目不保存或传输对话和文件内容，也不发起网络请求。
详见[隐私说明](../PRIVACY.md)和[安全策略](../SECURITY.md)。

导入音频的权利不会改变；请仅使用自己制作或已获授权的音频。

代码和文档采用 [MIT 许可证](../LICENSE)。12 个内置录音的 CC0 文件级来源记录在
[声音来源与许可](../SOUND_LICENSE.md)中。
本项目是独立开源项目，与 OpenAI 或 Anthropic 没有关联、认可或赞助关系。
