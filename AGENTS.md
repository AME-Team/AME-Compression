# AGENTS.md — AmeCompression AI エージェントプロトコル

> **このドキュメントは、このプロジェクトで作業するすべての AI エージェントにとっての絶対的なルールです。**
> 内容を理解し、内面化し、一切の妥協なく実行してください。

---

## 0. 単一の指令 (THE SINGLE DIRECTIVE)

**このプロジェクトは、世界最高のビデオおよびオーディオ圧縮アプリケーションにならなければなりません。**

「世界クラス」でも「競争力がある」でもありません。**世界ナンバーワン (World's #1)** です。すべてのコード、すべてのUIピクセル、すべてのエラーメッセージ、すべてのミリ秒の応答時間 — そのすべてがこの目標に寄与しなければなりません。

もし、あなたの成果物がこの基準を満たしているか確信が持てない場合は、満たしていません。

書き直してください。

---

## 1. プロジェクトのアイデンティティ (PROJECT IDENTITY)

| 項目                       | 値                                                                             |
| -------------------------- | ------------------------------------------------------------------------------ |
| **名前**                   | AmeCompression (雨 Compression)                                                |
| **目的**                   | FFmpeg を使用したビデオ (SVT-AV1) およびオーディオ (MP3) の圧縮                |
| **技術スタック**           | Electron + React + TypeScript (フロントエンド) / Python + Flask (バックエンド) |
| **リポジトリ**             | `tarminjapan/amecompression`                                                   |
| **ライセンス**             | MIT                                                                            |
| **Python バージョン**      | >= 3.10                                                                        |
| **パッケージマネージャー** | `uv` (バックエンド), `npm` (フロントエンド)                                    |

---

## 2. アーキテクチャマップ (ARCHITECTURE MAP)

```text
AmeCompression/
├── frontend/                  # Electron + React + Vite
│   ├── electron/              #   Electron メイン＆プリロードスクリプト
│   ├── src/
│   │   ├── components/        #   Layout, Sidebar, FloatingBar, ProgressPanel
│   │   ├── views/             #   MediaView, SettingsView
│   │   ├── hooks/             #   useJobs (ジョブステータスのポーリング)
│   │   ├── services/          #   api.ts (Axios → Flask)
│   │   ├── types/             #   TypeScript 型定義
│   │   ├── i18n/              #   en.json, ja.json 翻訳ファイル
│   │   ├── profiles.ts        #   圧縮プロファイルプリセット
│   │   └── App.tsx             #   ルートコンポーネント、状態管理
│   └── package.json
│
├── backend/                   # Python パッケージ
│   ├── api/                   #   Flask REST API
│   │   ├── app.py             #     Flask アプリファクトリ、CORS、ブループリント登録
│   │   ├── config.py          #     Flask 設定 (dev/prod/test)
│   │   ├── job_runner.py      #     バックグラウンドジョブ実行エンジン
│   │   └── blueprints/        #     jobs, media, settings エンドポイント
│   ├── video.py               #   ビデオ圧縮 (SVT-AV1 via FFmpeg)
│   ├── audio.py               #   オーディオ圧縮 (MP3 via FFmpeg)
│   ├── ffmpeg.py              #   FFmpeg/ffprobe の検出とメディア情報取得
│   ├── volume.py              #   音量の分析とノーマライズ
│   ├── config.py              #   コーデック定数、解像度制限、ファイル拡張子
│   ├── models.py              #   データクラス: パラメータ、結果、進捗イベント
│   ├── progress_handler.py    #   FFmpeg 出力パーサー、キャンセル制御
│   ├── settings.py            #   永続的な設定管理（JSON、クロスプラットフォーム）
│   └── utils.py               #   ビットレート解析、解像度スケーリング
│
├── tests/                     # pytest テストスイート
├── scripts/                   # ビルド＆ユーティリティスクリプト
├── documents/                 # 移行ガイド、仕様書
├── pyproject.toml             # バックエンド設定 (ruff, pyright, mypy, pytest)
└── AGENTS.md                  # ← 現在地
```

---

## 3. 世界第1位の品質基準 (WORLD'S #1 QUALITY STANDARDS)

### 3.1 UI / UX — ピクセルパーフェクト＆直感的

- **レイアウトのバグはゼロ。** 位置ズレ、不整合な余白、不自然な折り返しなどは一切許されません。
- **軽快なフィードバック。** すべてのユーザー操作（ボタン押下、ファイルのドロップ、スライダーのドラッグ）に対して、即座に視覚的フィードバックを返さなければなりません。ローディング状態、プログレスバー、成功/エラーのトースト通知は必須です — ユーザーを不安にさせてはいけません。
- **アニメーション。** スムーズで意味のあるものであるべきで、過剰であってはなりません。CSSのトランジションやトランスフォームを使用し、レイアウトスラッシングを避けてください。
- **ダーク/ライトテーマ。** 両方のテーマを意図的かつ美しく設計する必要があります（単に色を反転させただけのものでは不可）。すべてのコンポーネントを両方のモードでテストしてください。
- **国際化 (i18n)。** ユーザー向けの文字列はすべて `react-i18next` を通します。`en.json` と `ja.json` の両方にキーを追加してください。キーはドット記法（例： `"settings.title"`）のみを使用し、テキストをハードコードしないでください。
- **アクセシビリティ。** 適切なARIAラベル、キーボードナビゲーション、フォーカス管理を行ってください。

### 3.2 安定性 — あらゆる状況下で堅牢

- **絶対にクラッシュしない。** 破損したファイル、FFmpegの欠落、ネットワーク障害、権限エラー、0バイトファイル、極端に大きなファイルなど、あらゆるエッジケースを処理しなければなりません。
- **エラーメッセージ。** 具体的で、ユーザーが何をすべきか分かりやすく、人間に読める内容にしてください。生のエラースタックトレースをユーザーに表示してはいけません。一般的な「エラーが発生しました」というメッセージは避けてください。
- **FFmpeg のプロセス管理。** 子プロセスは常に `finally` ブロックで確実に終了させてください。キャンセル用トークンを適切に処理し、ゾンビプロセスを残さないでください。
- **型安全性。** すべての関数のシグネチャに型ヒントを記述します。`None` になる可能性はすべてガードしてください。ガードなしで `Optional` を使用しないでください。

### 3.3 圧縮品質 — 業界最高クラスの出力

- **SVT-AV1** をビデオに使用（CRFベースの品質制御、設定可能なプリセット0-13）。
- **AAC** をビデオ内のオーディオトラックに使用。オーディオ専用ファイルは **libmp3lame** を使用。
- **音量のノーマライズ**。FFmpegの `volumedetect` を使用した自動ゲイン分析。ターゲット： クリッピング防止付きでスピーチ/会話向けに -16 dB。
- **ノイズ除去**。設定可能なレベル（0.0〜1.0）の `afftdn` フィルター。
  UI側の値（0.0〜1.0）は、`nr = max(0.01, denoise_level * 97)` に変換してFFmpegの `nr` パラメータ（0.01〜97 dB）にマッピングされます（`backend/volume.py:build_audio_filter()` を参照）。
  **絶対に** UIの生値をそのまま `nr` として渡さないでください。常にこの変換を適用してください。
- **解像度スケーリング**。アスペクト比を維持し、エンコード効率のために偶数の寸法を強制します。最大： 4K (3840×2160)。

---

## 4. 絶対的禁止事項 (ABSOLUTE PROHIBITIONS)

### 4.1 エラー抑制コメント — 厳格に禁止

以下は、いかなる場合でも**絶対に禁止**されています。

```python
# ❌ 絶対に禁止
x = risky()  # type: ignore
# noqa: E501
# mypy: ignore
```

```typescript
// ❌ 絶対に禁止
// eslint-disable-next-line
// @ts-ignore
// @ts-nocheck
/* eslint-disable */
```

**型エラーやリント警告が発生した場合は、その根本原因を修正してください。** コードを再構築する、`frontend/src/types/index.ts` や `backend/models.py` の型定義を修正する、あるいはコードを書き直してください。

エラー抑制コメントを使用するいかなる理由も認められません。

### 4.2 その他の禁止事項

- **本番用コード内での `console.log` の使用禁止。** 構造化ロギングを使用してください。
- **バックエンド API コード内での `print()` の使用禁止。** `cli.py` のようなCLI専用コードでのみ許容されます。
- **URLやファイルパスのハードコード禁止。** 設定ファイルを利用してください。
- **`any` 型の使用禁止。** 本当に避けられない場合を除き、その場合はTODOコメントを記述してください。
- **コメントアウトされたコードを残さないこと。** 削除してください。Gitがすべてを記憶しています。
- **コードやコミットメッセージ内で絵文字を使用しないこと。** 明示的に要求された場合を除きます。

---

## 5. 必須の開発ワークフロー (MANDATORY WORKFLOW)

### 5.1 コードを記述する前に

1. **このファイル** (`AGENTS.md`) と `CONTRIBUTING.md` をすべて通読してください。
2. **`.gemini/styleguide.md`** を読み、プロジェクト特有の規約を確認してください。
3. **周囲のコードを理解してください。** 新しいコードを導入する前に、隣接するファイルを確認し、インポートをチェックし、既存のパターンを学んでください。
4. **既存の型を確認してください。** 新しい型を作成する前に、`frontend/src/types/index.ts` と `backend/models.py` を確認してください。

### 5.2 コードジェネレーションチェックリスト

生成するすべてのコードは、以下のすべてをクリアしなければなりません：

- [ ] **リントエラーなし:** `ruff check` / `eslint --max-warnings=0` — 警告ゼロ、エラーゼロ
- [ ] **フォーマットエラーなし:** `ruff format --check` / `prettier --check` — 差分ゼロ
- [ ] **型エラーなし:** `pyright --warnings` / `tsc --noEmit` — エラーゼロ、警告ゼロ
- [ ] **テスト通過:** `pytest tests -v` / 関連するフロントエンドテストの合格
- [ ] **エラー抑制コメントなし:** `# type: ignore`, `# noqa`, `eslint-disable`, `@ts-ignore` がゼロであること
- [ ] **国際化 (i18n) の完了:** 新しく追加されたすべての表示文字列が `en.json` と `ja.json` の両方に定義されていること
- [ ] **エラーハンドリング:** 外部呼び出し（サブプロセス、HTTP、ファイルI/O）はすべてtry-except等で囲み、個別の例外処理を行うこと
- [ ] **クラッシュ防止:** 破損した入力、ファイル欠落、各種エッジケースに対するロジックが考慮されていること

### 5.3 品質チェック用コマンド

```bash
# バックエンド
uv run ruff check backend tests
uv run ruff format --check backend tests
uv run pyright --warnings
uv run pytest tests -v

# フロントエンド
cd frontend && npm run lint:strict
cd frontend && npm run format:check
cd frontend && npm run typecheck
```

**コードを完了とするには、これらすべてがエラーや警告なしでパスしている必要があります。**

---

## 6. コーディング規約 (CODING CONVENTIONS)

### 6.1 Python (バックエンド)

- **スタイル:** PEP 8に準拠。`ruff` で強制（最大行長： 100）
- **クォーテーション:** ダブルクォーテーション（`"`）
- **型ヒント:** すべての関数署名およびパブリック変数に必須
- **インポート順序:** `ruff` のisortルールに準拠（標準ライブラリ → サードパーティ → ローカル）
- **ドキュメント文字列:** すべてのパブリック関数/クラスにGoogleスタイルのdocstringを記述
- **命名規則:**
  - 関数/変数： `snake_case`
  - クラス： `PascalCase`
  - 定数： `UPPER_SNAKE_CASE`
- **エラーハンドリング:** 具体的な例外クラスを指定すること。裸の `except:` は禁止。常に有益なエラーメッセージを含めること
- **パス操作:** `os.path` ではなく `pathlib.Path` を使用すること

### 6.2 TypeScript / React (フロントエンド)

- **スタイル:** ESLint + Prettierで強制
- **コンポーネント:** フックを使用した関数型コンポーネント。クラスコンポーネントは使用しない。
- **型定義:** `frontend/src/types/index.ts` に定義し、そこからエクスポートする。
- **状態管理:** ローカル状態には `useState`、ミュータブルな参照に `useRef`、共有状態にContextまたはPropsを使用
- **命名規則:**
  - コンポーネント： `PascalCase`（ファイル名とエクスポート名）
  - 関数/変数： `camelCase`
  - 型/インターフェース： `PascalCase`
  - 定数： `UPPER_SNAKE_CASE`
- **CSS:** スコープされたコンポーネントCSSを使用。`App.css` および `index.css` の既存クラス命名パターンに従うこと
- **API 呼び出し:** `services/api.ts` で定義されている共有 `api` Axiosインスタンスを使用し、必ずエラーハンドリングを行うこと

### 6.3 Git 規約

- **ブランチ名:** `feature/<説明>`, `fix/<説明>`, `refactor/<説明>`
- **コミットメッセージ:** 命令形、簡潔に記述（例： `feat: add audio denoise slider`, `fix: handle corrupt file input`）
- **PRの範囲:** 1つのPRにつき1つの機能または修正に絞ること。焦点を絞って維持する

### 6.4 言語とコミュニケーション規約

- **デフォルト言語:** PRの説明、PRコメント、Issueの説明、およびAIエージェントのレビュー結果は**日本語** (`ja`) で生成すること。
- **ユーザーとの対話:** ユーザーに対するすべての説明、進捗状況の更新、およびコード変更の報告は**日本語**で記述すること。

---

## 7. 主要データフロー (KEY DATA FLOWS)

### 7.1 圧縮ジョブのライフサイクル

```text
ユーザーがファイルを選択 (MediaView)
  → FloatingBar の「圧縮開始」をクリック
    → POST /api/jobs (backend/api/blueprints/jobs)
      → job_runner がバックグラウンドスレッドを開始
        → video.py: compress_video_service() または audio.py: compress_audio_service()
          → subprocess.Popen(ffmpeg ...)
            → ProgressParser が標準出力を1行ずつ読み込む
              → コールバック経由で ProgressEvent を発行
                → job_runner の状態に保存
  → フロントエンドが 1 秒ごとに GET /api/jobs をポーリング (useJobs フック)
    → UI（ProgressPanel, FloatingBar）を更新
      → 完了時: electronAPI を経由して Electron 通知を表示
```

### 7.2 設定のフロー

```text
SettingsView (React)
  → GET/PUT /api/settings (backend/api/blueprints/settings)
    → SettingsManager (シングルトン、ディスク上の JSON ファイル)
      → クロスプラットフォーム設定ディレクトリ: %APPDATA% / ~/Library/Application Support / ~/.config/AmeCompression
```

### 7.3 プロファイルシステム

```text
MediaProfile (TypeScript インターフェース、profiles.ts)
  → localStorage (ブラウザ/Electron) に保存
  → loadProfiles() / saveProfiles() を使用してロード/保存
  → MediaView の設定に適用され、圧縮時に API へ渡される
```

---

## 8. API エンドポイント (API ENDPOINTS)

| メソッド | パス                        | 目的                                  |
| -------- | --------------------------- | ------------------------------------- |
| POST     | `/api/jobs`                 | 新しい圧縮ジョブの開始                |
| GET      | `/api/jobs`                 | ステータス/進捗を含むジョブ一覧の取得 |
| DELETE   | `/api/jobs/:id`             | 実行中のジョブのキャンセル            |
| GET      | `/api/media/info`           | メディアファイル情報の取得 (FFprobe)  |
| POST     | `/api/media/volume-analyze` | 音量レベルの分析                      |
| GET      | `/api/settings`             | すべての設定の取得                    |
| PUT      | `/api/settings`             | 設定の更新                            |

---

## 9. FFmpeg コマンドパターン (FFmpeg COMMAND PATTERNS)

### ビデオ圧縮

```bash
ffmpeg -i <入力> -y \
  -vf "scale=W:H,fps=FPS" \
  -c:v libsvtav1 -crf <0-63> -b:v 0 -preset <0-13> \
  [-af "afftdn=nr=N,volume=GdB"] -c:a aac -b:a <ビットレート> \
  <出力>
```

### オーディオ圧縮

```bash
ffmpeg -i <入力> -y \
  [-af "afftdn=nr=N,volume=GdB"] \
  -c:a libmp3lame -b:a <ビットレート> \
  -map_metadata 0 \
  <出力>
```

### 音量分析

```bash
ffmpeg -i <入力> -af volumedetect -vn -sn -dn -f null -
```

---

## 10. デフォルト設定値 (DEFAULT CONFIGURATION VALUES)

| パラメータ                         | デフォルト値 | 範囲     |
| ---------------------------------- | ------------ | -------- |
| ビデオコーデック                   | `libsvtav1`  | —        |
| CRF                                | `25`         | 0–63     |
| プリセット                         | `6`          | 0–13     |
| オーディオコーデック（ビデオ）     | `aac`        | —        |
| オーディオコーデック（オーディオ） | `libmp3lame` | —        |
| オーディオビットレート             | `192k`       | 16k–320k |
| 最大解像度                         | `3840×2160`  | —        |
| ターゲット音量                     | `-16 dB`     | —        |
| 最大音量                           | `-1 dB`      | —        |
| ノイズ除去レベル                   | `0.15`       | 0.0–1.0  |

---

## 11. セルフレビュープロトコル (SELF-REVIEW PROTOCOL)

成果物を確定させる前に、以下の質問に答えてください：

1. **Apple がこの UI をリリースするでしょうか？** もし「はい」と即答できない場合は、デザインを洗練させてください。
2. **このコードがクラッシュする可能性はありますか？** すべてのエラーパスを追跡してください。未処理の例外につながるパスがある場合は、修正してください。
3. **すべての型定義は正しいですか？** `any` やエラー抑制コメントはなく、曖昧な想定も排除されていますか。
4. **ユーザーは今何が起きているかを理解できますか？** ローディング状態、進捗、エラーの表示が明確で、分かりやすくなっている必要があります。
5. **地球上で最高のエンジニアがこの PR を承認するでしょうか？** そう思えないなら、まだ完了していません。

---

## 12. GEMINI CODE ASSIST 連携 (GEMINI CODE ASSIST INTEGRATION)

実装が完了したら、検証のために以下のコマンドを使用してください：

| コマンド                           | 目的                             |
| ---------------------------------- | -------------------------------- |
| `/gemini review`                   | コード品質と UX の完全なレビュー |
| `/gemini summary`                  | 実装ステータスの概要確認         |
| `/gemini`                          | 一般的な開発サポート             |
| `/gemini help`                     | コマンド仕様の参照               |
| `@gemini-code-assist <ファイル名>` | モジュール特有の最適化提案       |

---

## 13. AI レビュー＆ CI 修正ループプロトコル (AI REVIEW & CI ITERATION PROTOCOL)

開発ワークフローにおいて品質と堅牢性を最大化するため、以下のループ手順を必ず遵守してください：

1. **プルリクエスト（PR）の作成**: 実装が完了したら、PRを作成します。
2. **AI レビューと CI チェックの実行**: AI（Gemini Code Assistなど）によるコードレビューの指摘、およびGitHub ActionsなどのCIで実行される静的解析やテスト結果を確認します。
3. **指摘・エラーの修正**: レビューのすべての指摘事項、提案、およびCIの静的解析エラーに対して誠実に対応し、修正します。
4. **再 Push と再検証**: 修正をコミット・プッシュし、再度レビューとCIの検証を受けます。
5. **完了条件**:
   - レビューによる指摘やサジェスチョン、およびCIの静的解析でのNG項目が完全になくなるまで、この修正ループを繰り返します。
   - **無限ループ回避のため、この繰り返し対応は最大5回まで**とします。

---

## 14. 最後に (FINAL REMINDER)

あなたは趣味のプロジェクトのコードを書いているのではありません。**世界最高の圧縮アプリケーション**を構築しているのです。変数名、エラーハンドリング、ピクセルの配置にいたるまで、すべての決定がこの基準を反映したものでなければなりません。

**「十分良い」は「世界一」の敵です。完璧なものを届けてください。**
