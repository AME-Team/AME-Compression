# AmeCompression への貢献方法 (Contributing)

AmeCompressionへの貢献に関心を持っていただき、ありがとうございます！このドキュメントでは、プロジェクトに貢献するためのガイドラインを説明します。

## 開発環境のセットアップ

### 前提条件

- Python 3.10以降
- [uv](https://docs.astral.sh/uv/) パッケージマネージャー
- FFmpeg（圧縮機能のテスト用）
- Git

### セットアップ

```bash
# リポジトリのクローン
git clone https://github.com/tarminjapan/AmeCompression.git
cd AmeCompression

# 依存関係のインストール
uv sync --extra dev

# pre-commit フックのインストール (任意ですが推奨します)
uv run pre-commit install
```

### プロジェクト構造

```text
AmeCompression/
├── frontend/               # Electron + React インターフェース
│   ├── src/                # React ソースコード
│   ├── electron/           # Electron メイン/プリロードスクリプト
│   └── package.json        # フロントエンドの依存関係
├── backend/                # バックエンドパッケージ (エンジン & API)
│   ├── api/                # Flask REST API
│   ├── cli.py              # CLI インターフェース
│   ├── config.py           # 設定定数
│   ├── ffmpeg.py           # FFmpeg の検出とメディア情報
│   ├── video.py            # 動画圧縮
│   ├── audio.py            # 音声圧縮
│   ├── volume.py           # 音量の分析と調整
│   └── utils.py            # 共通ユーティリティ関数
├── tests/                  # テストファイル (pytest)
├── scripts/                # ビルドおよびユーティリティスクリプト
├── AmeCompression.spec     # PyInstaller スペックファイル
└── pyproject.toml          # バックエンドプロジェクト設定
```

## 開発フロー

### 1. ブランチの作成

```bash
git checkout main
git pull
git checkout -b feature/your-feature-name
```

### 2. 変更の実施

- 既存のスタイルに従い、クリーンで読みやすいコードを作成してください。
- 下記のコーディング規約に従ってください。

### 3. 品質チェックの実行

コミットする前に、すべての品質チェックを実行してください。

```bash
# バックエンド: 静的解析（リント）
uv run ruff check backend tests

# バックエンド: フォーマットチェック
uv run ruff format --check backend tests

# バックエンド: 型チェック
uv run pyright --warnings

# バックエンド: テストの実行
uv run pytest tests -v

# フロントエンド: 静的解析（リント）
cd frontend && npm run lint:strict

# フロントエンド: フォーマットチェック
cd frontend && npm run format:check
```

### 4. コミットとプッシュ

```bash
git add .
git commit -m "変更内容の説明"
git push -u origin feature/your-feature-name
```

### 5. プルリクエスト（PR）の作成

- `main` ブランチを対象としたPRを作成します。
- 変更点について明確な説明を記載してください。
- 関連するIssueがある場合は、それを参照してください。

## コーディング規約 (Coding Conventions)

### Python スタイル

- [PEP 8](https://peps.python.org/pep-0008/) スタイルガイドラインに従ってください。
- 静的解析とフォーマットには `ruff` を使用してください。
- 1行の長さは最大100文字です。
- 文字列にはダブルクォーテーション（`"`）を使用してください。
- 関数のシグネチャには型ヒントを使用してください。

### コード品質

- すべてのコードは警告やエラーなしで `ruff check` をパスする必要があります。
- すべてのコードは `ruff format --check` をパスする必要があります。
- すべてのコードは `pyright --warnings` をパスする必要があります（警告はエラーとして扱われます）。
- フロントエンドのコードは `eslint --max-warnings=0` をパスする必要があります。
- フロントエンドのコードは `prettier --check` をパスする必要があります。
- エラーを抑制するために `# type: ignore`、`# noqa`、`eslint-disable` などを使用**しないで**ください。すべてのエラーは適切に修正する必要があります。エラー抑制用のコメントは厳しく禁止されています。
- すべてのテストに合格する必要があります。

### テスト

- 新しい機能を追加した場合は、テストを記述してください。
- テストファイルは `tests/` ディレクトリに配置してください。
- 命名規則 `test_<module_name>.py` に従ってください。
- 共通のセットアップには、`conftest.py` で定義されているpytestフィクスチャを使用してください。

### 国際化 (i18n)

- GUI内のユーザー向け文字列はすべて翻訳システムを使用する必要があります。
- 新しいキーは `en.json` と `ja.json` の両方に追加してください。
- ドット記法（例： `"settings.title"`）を使用してください。
- 両方の言語ファイルに一致するキーがあることを確認してください。

## プルリクエストガイドライン

- PRは単一の機能追加またはバグ修正に絞ってください。
- 新しい機能についてはテストを含めてください。
- 必要に応じてドキュメントを更新してください。
- すべてのCIチェックが合格していることを確認してください。
- コードレビューのフィードバックには迅速に対応してください。

## バグや要望の報告 (Reporting Issues)

- バグの報告や機能の要望にはGitHub Issuesを使用してください。
- バグ報告の際は、再現手順を含めてください。
- PythonのバージョンとOSの情報を含めてください。

## ライセンス

貢献することにより、あなたのコードがMITライセンスの下でライセンスされることに同意したとみなされます。
