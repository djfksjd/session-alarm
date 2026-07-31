<p align="center">
  <img src="../assets/session-alarm-logo.svg" width="176" alt="Session Alarm ロゴ">
</p>

<h1 align="center">Session Alarm</h1>

<p align="center">
  <strong>コーディングエージェントを見張り続ける必要はありません。</strong><br>
  Codex または Claude Code があなたを必要としたら、動物の音で知らせます。
</p>

<p align="center">
  <a href="https://github.com/djfksjd/session-alarm/actions/workflows/ci.yml"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/djfksjd/session-alarm/ci.yml?branch=main&style=flat-square&label=CI"></a>
  <a href="../LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/license-MIT-2EC4B6?style=flat-square"></a>
  <img alt="Python 3.9+" src="https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat-square&logo=python&logoColor=white">
  <img alt="12 sounds" src="https://img.shields.io/badge/実際の動物サウンド-12-FFB703?style=flat-square">
</p>

<p align="center">
  <a href="../README.md">English</a> ·
  <a href="README.ko.md">한국어</a> · 日本語 ·
  <a href="README.zh-CN.md">简体中文</a> ·
  <a href="README.es.md">Español</a>
</p>

---

Session Alarm は、**Codex と Claude Code 専用のフックベース通知プラグイン**です。
エージェントが入力を必要とした時、現在のターンを完了した時、エラーで停止した時、
またはセッションを終了した時に、音と任意のデスクトップ通知で知らせます。

内蔵 12 種類は実際の動物を録音した短い通知音です。取得時に各 Freesound 個別ページで
CC0 1.0 Universal と表示されていた音源のみを選び、正確なページ、投稿者、公開プレビュー
および加工 WAV の SHA-256 を記録しています。自作または利用許諾を得た WAV も追加できます。

<table>
  <tr>
    <td width="25%" align="center"><strong>🔔 確実</strong><br>モデルの記憶ではなくライフサイクルフックで動作します。</td>
    <td width="25%" align="center"><strong>🐈 12 種類</strong><br>実際の動物録音を選ぶか独自 WAV を追加できます。</td>
    <td width="25%" align="center"><strong>🛡️ ライセンス確認</strong><br>商用利用条件、出典、確認日、チェックサムを公開します。</td>
    <td width="25%" align="center"><strong>🏠 ローカルのみ</strong><br>アカウント、サーバー、解析、テレメトリー、通信はありません。</td>
  </tr>
</table>

## 通知イベント

| イベント | Codex | Claude Code | デフォルト |
|---|---|---|---|
| 入力が必要 | 権限要求、または質問で終わる応答 | 権限・選択ダイアログ・バックグラウンドエージェントの入力要求・質問 | 猫 |
| 作業完了 | 現在の応答終了 | 現在の応答、またはバックグラウンドエージェント完了 | ニワトリ |
| エラー | 利用可能なエラーイベント | `StopFailure` | カラス |
| セッション終了 | `SessionEnd` | `SessionEnd` | フクロウ |

> [!NOTE]
> 「作業完了」は現在のターンが終了したことを意味します。既知のバックグラウンド
> タスクやセッションスケジュールが残っている場合、完了音は抑制されます。

## インストール

### Codex

```bash
codex plugin marketplace add djfksjd/session-alarm
codex plugin add session-alarm@session-alarm
```

新しい Codex スレッドを開始し、`/hooks` でコマンドを確認して信頼してください。
設定スキルはいつでも実行できます。

```text
$session-alarm
```

### Claude Code

```bash
claude plugin marketplace add djfksjd/session-alarm
claude plugin install session-alarm@session-alarm
```

新しいセッションを開始するか `/reload-plugins` を実行し、次のコマンドで設定します。

```text
/session-alarm:session-alarm
```

### ローカル実行

```bash
git clone https://github.com/djfksjd/session-alarm.git
cd session-alarm
python3 plugins/session-alarm/scripts/session_alarm.py setup
```

Python 3.9 以上が必要です。macOS では `afplay`、Linux では
`paplay`・`aplay`・`ffplay`、Windows では `winsound` を使用します。

## 初回設定

初回ウィザードでは、全サウンドの確認と試聴、独自 WAV の追加、4 イベントそれぞれの音、音量、
デスクトップ通知、深夜をまたぐ静音時間を設定できます。設定は同じマシン上の
Codex と Claude Code で共有されます。

```bash
# カタログ
python3 plugins/session-alarm/scripts/session_alarm.py catalog

# 猫を試聴
python3 plugins/session-alarm/scripts/session_alarm.py preview cat --volume 70

# 12 種類を順番に試聴（停止: Ctrl+C）
python3 plugins/session-alarm/scripts/session_alarm.py preview-all --volume 40

# 独自 WAV を追加して試聴（最大 30 秒 / 32 MB）
python3 plugins/session-alarm/scripts/session_alarm.py custom add "./my-sound.wav" \
  --name "My Sound" --id my-sound --preview

# すべてのイベントをテスト
python3 plugins/session-alarm/scripts/session_alarm.py test all
```

## 12 種類の実際の動物サウンド

| 分類 | 動物 |
|---|---|
| ペット | 猫、犬 |
| 牧場 | 牛、馬、豚、ヤギ、羊、雄鶏 |
| 鳥 | フクロウ、カラス |
| 小さな生物 | カエル、コオロギ |

音声は短い通知向けに正規化されています。
[音源の由来とライセンス](../SOUND_LICENSE.md)をご覧ください。

## プライバシーとライセンス

設定、追加した WAV、生成キャッシュは macOS/Linux の `~/.config/session-alarm/` または Windows の
`%APPDATA%\session-alarm\` にのみ保存されます。会話やファイルの内容を保存・送信せず、
ネットワーク要求も行いません。詳細は[プライバシー](../PRIVACY.md)と
[セキュリティポリシー](../SECURITY.md)をご覧ください。

追加した音声の権利は変更されません。自作または利用許諾を得た音声のみを使用してください。

コードと文書は [MIT](../LICENSE) です。内蔵録音 12 種類の CC0 出典は
[音源の由来とライセンス](../SOUND_LICENSE.md)に記録されています。
本プロジェクトは OpenAI または Anthropic と提携・後援関係にない独立した
オープンソースプロジェクトです。
