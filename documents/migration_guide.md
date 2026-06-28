# AmeCompression 移行＆リリースガイド (Issue #50)

このドキュメントでは、CustomTkinterベースのGUIから新しいElectron + React + Flaskアーキテクチャへの移行について、運用上の要件や開発セットアップ手順を含めて説明します。

## 🏗️ 新しいアーキテクチャの概要

本アプリケーションは、純粋なPython GUI（CustomTkinter）から、Web技術を用いたモダンなデスクトップアプリケーションへと移行しました。

- **フロントエンド**: Electron + React (TypeScript) + Vite
- **バックエンド**: Flask API (Python)
- **通信方式**: REST API (localhost:5000)

この移行により、UIの応答性が向上し、クロスプラットフォームにおける一貫性が向上しました。また、メディア処理ロジックとユーザーインターフェースの間で、関心の分離がより堅牢に行われています。

## 🛠️ 開発者向けセットアップ手順

新しいアーキテクチャの開発環境をセットアップするには、以下の手順に従ってください。

### 1. Python環境 (バックエンド)

Pythonの依存関係の管理には `uv` を使用することを推奨します。

```bash
# 依存関係のインストール
uv sync --extra dev

# APIサーバーを手動で起動（オプション、Electronが自動で起動します）
uv run python -m backend --api --port 5000 --config dev
```

### 2. Node.js環境 (フロントエンド)

Node.js（v18以降）がインストールされていることを確認してください。

```bash
# フロントエンドディレクトリへ移動
cd frontend

# 依存関係のインストール
npm install

# 開発モードの起動（Vite + Electron）
npm run electron:dev
```

## ⚙️ FFmpeg の配置と設定

アプリケーションの動作には `ffmpeg` および `ffprobe` が必要です。これらを提供する方法は2つあります。

1. **システム環境変数 PATH**: コマンドラインからアクセスできるように、システム全体にFFmpegをインストールします。
2. **ローカルの `bin/` ディレクトリ**: **プロジェクトリポジトリのルート**にある `bin` という名前のディレクトリに、`ffmpeg` と `ffprobe`（Windowsの場合は `ffmpeg.exe` と `ffprobe.exe`）の実行ファイルを配置します。

バックエンドは、システムのPATHをフォールバックとして使用する前に、`bin/` フォルダ内のローカル実行ファイルを自動的に検出します。

## ⚠️ 互換性と制約事項

- **CLI モード**: CLIバージョン（`uv run python -m backend <input>`）は、引き続き完全な互換性を維持し動作します。
- **ポートの競合**: Flaskバックエンドはデフォルトでポート `5000` を使用します。このポートが他のサービス（macOSのAirPlayレシーバーなど）によって使用されていないことを確認してください。
- **CORS**: APIは、Electronアプリ（`app://.`）およびVite開発サーバー（`http://localhost:5173`）からのリクエストのみを許可するように設定されています。

## 🚀 リリース手順

1. **バージョン更新**: `pyproject.toml` と `frontend/package.json` のバージョンをインクリメントします。
2. **フロントエンドのビルド**: `frontend` ディレクトリで `npm run build` を実行します。
3. **実行ファイルのビルド**: `uv run scripts/build.py` を実行して、スタンドアロンの実行ファイルを作成します。
4. **動作検証**:
    - すべてのPythonテストを実行： `uv run pytest tests`。
    - 設定画面でFFmpegの検出ステータスを確認します。
    - 動画と音声の両方で、圧縮処理のテストフローを実行します。
