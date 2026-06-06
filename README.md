# AME Compression

FFmpeg (SVT-AV1) を使用した高性能な動画・音声圧縮ツール。
Electron、React、および Flask を活用した、モダンで直感的なインターフェースを提供します。

## 🚀 主な機能

- **モダンな Web インターフェース**: Electron + React により、洗練されたレスポンシブな操作感を実現。
- **動画圧縮**: SVT-AV1 を採用し、高い圧縮率と画質を両立。
- **音声圧縮**: 各種フォーマットを高品質な MP3 (libmp3lame) へ変換。
- **スマートツール**: 自動音量調整（ノーマライズ）およびノイズ除去機能を搭載。
- **バッチ処理**: 複数ファイルを同時に、進捗を確認しながら一括処理可能。
- **多言語対応**: 日本語と英語をサポート。

## 📥 インストール

### 1. 前提条件 (FFmpeg)

AmeCompression は 2 種類のビルド形態で配布されています。

| ビルド種別 | 説明 | 対応プラットフォーム |
|---|---|---|
| **バンドル版** | FFmpeg バイナリ同梱 — 個別のインストール不要。 | Windows |
| **非バンドル版** | システムに FFmpeg のインストールが必要。 | Windows / macOS / Linux |

**非バンドル版**を使用する場合は、システムに FFmpeg をインストールしてください。

- **Windows**: `choco install ffmpeg` または [ffmpeg.org](https://ffmpeg.org/download.html) からダウンロード
- **macOS**: `brew install ffmpeg`
- **Linux**: `sudo apt install ffmpeg libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libgtk-3-0 libgbm1 libasound2`

または、プロジェクトルートの `bin/` フォルダ内に `ffmpeg` と `ffprobe` の実行ファイルを配置することでも動作します（実行時に自動検出されます）。

### 2. ソースから実行

アプリケーションのルートディレクトリで以下のコマンドを実行します。

**macOS / Linux の場合:**

```bash
make dev
```

**Windows の場合:**

```bat
dev.bat
```

## 📄 ドキュメント

- [移行ガイド](documents/migration_guide.md) - アーキテクチャとセットアップの詳細。
- [開発計画](documents/development_plan.md) - プロジェクトのロードマップと目標。

## 🖥️ GUI の使い方

1. **起動**: `npm run electron:dev` (開発時) またはビルド済みの実行ファイルを起動します。
2. **ファイルの追加**: 動画または音声ファイルをウィンドウにドラッグ＆ドロップします。
3. **設定**: CRF（品質）、プリセット（速度）、ノイズ除去や音量調整を設定します。
4. **実行**: 出力先フォルダを選択し、**開始** ボタンをクリックします。

## 🛠️ 開発とビルド

```bash
# バックエンド
uv sync --extra dev

# フロントエンド
cd frontend
npm install
npm run build

# スタンドアロンビルド (PyInstaller を使用)

# 非バンドルビルド（デフォルト — 実行時にシステムの FFmpeg を使用）
uv run scripts/build.py

# バンドルビルド（bin/ 内の FFmpeg バイナリを同梱）
# 事前に bin/ ディレクトリに ffmpeg / ffprobe の実行ファイルを配置してください
uv run scripts/build.py --with-ffmpeg
```

## 🧪 テスト

```bash
# 全テストの実行
uv run pytest

# カバレッジレポート付きで実行
uv run pytest --cov

# リント・フォーマットチェック
uv run ruff check
uv run ruff format --check

# 厳格な型チェック（warningも失敗扱い）
uv run pyright --warnings

# フロントエンドの厳格チェック
npm --prefix frontend run lint:strict
npm --prefix frontend run format:check
```

## 📄 ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。

**バンドル版**を使用する場合は、FFmpeg のライセンス情報 (LGPL v2.1+) について `LICENSE_FFMPEG.txt` も併せて確認してください。
