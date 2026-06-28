# AmeCompression フロントエンド (Frontend)

Electron、React、およびViteで構築されたAmeCompressionのデスクトップユーザーインターフェース。

## 🚀 主な特徴

- **React 19**: モダンなUIコンポーネントアーキテクチャ。
- **Electron**: クロスプラットフォームに対応したデスクトップアプリケーションシェル。
- **Vite**: 超高速な開発サーバーおよびビルドツール。
- **Tailwind CSS**: 迅速なUI開発のためのユーティリティファーストなCSSフレームワーク（使用されている場合）。
- **Lucide React**: 美しく一貫性のあるアイコンセット。
- **i18next**: 包括的な国際化（多言語対応）サポート。

## 🛠️ 開発方法

### セットアップ

```bash
# 依存関係のインストール
npm install
```

### 開発モードでの実行

Vite開発サーバーとElectronアプリケーションの両方をホットモジュールリプレースメント (HMR) 有効で起動します。

```bash
npm run electron:dev
```

### ビルド

フロントエンドのアセットをコンパイルし、本番環境向けの準備を行います。

```bash
npm run build
```

## 🏗️ アーキテクチャ

- `src/`: Reactのソースコード。
- `electron/`: Electronのメインおよびプリロードスクリプト。
- `public/`: 静的アセット。
- `dist/`: コンパイルされた本番用ビルド（`npm run build` 実行後に生成）。
