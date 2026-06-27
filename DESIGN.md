# DESIGN.md — AmeCompression デザイン仕様書

> AmeCompression の UI/UX デザイン、カラーパレット、タイポグラフィ、コンポーネント設計を定義する。
> 本ドキュメントはデザインに関する唯一の正情報源（Single Source of Truth）とする。

---

## 1. デザインフィロソフィー

- **Apple レベルの品質** — すべてのUIコンポーネントは、Apple製品と同等の洗練さと使いやすさを目指す。
- **ダークモードファースト** — ダークモードを基準として設計し、ライトモードは派生として実装する。
- **グラスモーフィズム** — ダークモードでは `backdrop-filter: blur(24px)` を用いた半透明ガラス効果を基本とする。
- **即時フィードバック** — すべてのユーザーアクションに対して、視覚的なフィードバックを即座に返す。

---

## 2. デザイントークン

デザイントークンは `frontend/src/index.css` の `@theme {}` ブロックで一元管理する。

### 2.1 プライマリカラー

| トークン                | 値                         | 用途                                       |
| ----------------------- | -------------------------- | ------------------------------------------ |
| `--color-primary`       | `#a855f7`                  | プライマリボタン、リンク、フォーカスリング |
| `--color-primary-hover` | `#9333ea`                  | ホバー状態                                 |
| `--color-primary-muted` | `rgba(168, 85, 247, 0.15)` | 背景、セカンダリホバー                     |

### 2.2 サーフェスカラー

| トークン           | ダーク                         | ライト                |
| ------------------ | ------------------------------ | --------------------- |
| 背景サーフェス     | `#0a0a0a`（グラデーション）    | `#f9fafb`（フラット） |
| カード背景         | `rgba(12, 12, 12, 0.9)` + blur | `#ffffff`             |
| サイドバー背景     | `rgba(12, 12, 12, 0.9)` + blur | `#ffffff`             |
| 入力欄背景         | `rgba(255, 255, 255, 0.04)`    | `#f9fafb`             |
| ドロップダウン背景 | `#1a1a1a`                      | `#ffffff`             |
| Electron 背景      | `#111827`                      | `#f9fafb`             |

### 2.3 ボーダーカラー

| トークン                | ダーク                      | ライト    |
| ----------------------- | --------------------------- | --------- |
| `--color-border-subtle` | `rgba(255, 255, 255, 0.08)` | `#e5e7eb` |

### 2.4 テキストカラー

| トークン                 | ダーク    | ライト    | 用途                   |
| ------------------------ | --------- | --------- | ---------------------- |
| `--color-text-primary`   | `#f5f5f5` | `#1f2937` | 見出し、本文           |
| `--color-text-secondary` | `#d4d4d4` | `#4b5563` | サブテキスト           |
| `--color-text-meta`      | `#a3a3a3` | `#6b7280` | メタ情報、キャプション |

### 2.5 セマンティックカラー

| トークン             | 値                          | 用途                       |
| -------------------- | --------------------------- | -------------------------- |
| `--color-success`    | `#34d399`                   | 成功メッセージ、完了状態   |
| `--color-success-bg` | `rgba(52, 211, 153, 0.15)`  | 成功背景                   |
| `--color-error`      | `#f87171`                   | エラーメッセージ、失敗状態 |
| `--color-error-bg`   | `rgba(248, 113, 113, 0.15)` | エラー背景                 |
| `--color-warning`    | `#fbbf24`                   | 警告メッセージ             |
| `--color-info`       | `#60a5fa`                   | 情報メッセージ             |

### 2.6 無効状態

| プロパティ         | 値     |
| ------------------ | ------ |
| 不透明度           | `0.5`  |
| ポインターイベント | `none` |

---

## 3. タイポグラフィ

### 3.1 フォントスタック

```css
--font-sans: -apple-system, "Hiragino Kaku Gothic ProN", "Hiragino Sans", "Noto Sans JP", sans-serif;
--font-mono: ui-monospace, "Cascadia Code", "Source Code Pro", Consolas, monospace;
```

### 3.2 タイポグラフィスケール

| 用途                | サイズ          | ウェイト | 備考                             |
| ------------------- | --------------- | -------- | -------------------------------- |
| ページ見出し (h1)   | `1.5rem`        | 700      | ページタイトル                   |
| カード見出し (h2)   | `1rem`          | 700      | セクション見出し                 |
| モーダル見出し (h3) | `0.875–0.9rem`  | 600      | ダイアログタイトル               |
| 本文                | `0.85–0.875rem` | 400      | 一般テキスト                     |
| セクションタイトル  | `0.8rem`        | 700      | 大文字、`letter-spacing: 0.05em` |
| 小テキスト / メタ   | `0.7–0.75rem`   | 400      | キャプション、注釈               |
| 等幅テキスト        | `--font-mono`   | —        | ファイル名、パス                 |

### 3.3 ベース設定

```css
font: 16px/1.5 var(--font-sans);
letter-spacing: 0.18px;
```

1024px以下の画面では `font-size: 14px` に縮小。

---

## 4. レイアウト

### 4.1 アプリケーションシェル

```text
┌──────────────────────────────────────────────┐
│ Sidebar (240px) │  Main Content              │
│ ┌──────────────┐│ ┌──────────────────────────┐│
│ │ Logo         ││ │  (max-width: 900px)      ││
│ │ Nav Items    ││ │  padding: 32px           ││
│ │              ││ │  padding-bottom: 80px    ││
│ │ Version      ││ │                          ││
│ └──────────────┘│ └──────────────────────────┘│
│                 │  ┌── Floating Bar (56px) ──┐│
│                 │  └─────────────────────────┘│
└──────────────────────────────────────────────┘
```

### 4.2 CSS レイアウト変数

| 変数                   | 値      | 用途                        |
| ---------------------- | ------- | --------------------------- |
| `--sidebar-width`      | `240px` | サイドバー固定幅            |
| メインコンテンツ最大幅 | `900px` | 中央寄せコンテナ            |
| メインパディング       | `32px`  | コンテンツ余白              |
| 下部パディング         | `80px`  | Floating Bar のクリアランス |

### 4.3 スペーシング

| 要素                             | 値       |
| -------------------------------- | -------- |
| カードパディング                 | `24px`   |
| ボーダー半径（入力・ボタン）     | `8px`    |
| ボーダー半径（カード・モーダル） | `12px`   |
| ボーダー半径（小要素）           | `4px`    |
| ボーダー半径（ピル・バッジ）     | `9999px` |

---

## 5. コンポーネント設計

### 5.1 コンポーネント一覧

| コンポーネント     | ファイル                          | 概要                                                                         |
| ------------------ | --------------------------------- | ---------------------------------------------------------------------------- |
| `Layout`           | `components/Layout.tsx`           | アプリシェル。サイドバー + メインコンテンツ + アクセシビリティスキップリンク |
| `Sidebar`          | `components/Sidebar.tsx`          | ナビゲーションサイドバー。ロゴ + ナビ項目 + バージョン情報                   |
| `FloatingBar`      | `components/FloatingBar.tsx`      | 下部ツールバー。プロファイル・進捗モーダル、バッジカウント、スピンローダー   |
| `ProgressPanel`    | `components/ProgressPanel.tsx`    | ジョブ進捗表示。グラデーション + シマーのプログレスバー、ステータスバッジ    |
| `SelectDropdown`   | `components/SelectDropdown.tsx`   | カスタムセレクト。トリガーボタン + ドロップダウンリスト、紫ハイライト        |
| `ComboBox`         | `MediaView.tsx` 内                | 編集可能ドロップダウン。インラインドロップダウン付き                         |
| `ToastProvider`    | `components/ToastProvider.tsx`    | トースト通知。3 バリアント（success/error/info）、自動非表示                 |
| `ConfirmModal`     | `components/ConfirmModal.tsx`     | 確認ダイアログ。3 バリアント（warning/danger/info）、フォーカストラップ      |
| `CommandPalette`   | `components/CommandPalette.tsx`   | コマンド検索パレット (`Ctrl+K`)。キーボードナビゲーション                    |
| `ComparisonSlider` | `components/ComparisonSlider.tsx` | Before/After 画像比較スライダー。キーボード対応                              |

### 5.2 ビュー一覧

| ビュー         | ファイル                 | 概要                                                                  |
| -------------- | ------------------------ | --------------------------------------------------------------------- |
| `MediaView`    | `views/MediaView.tsx`    | メインの圧縮設定画面。ファイルドロップゾーン、動画/音声設定、品質分析 |
| `SettingsView` | `views/SettingsView.tsx` | アプリ設定。言語、テーマ切替、FFmpeg パス、出力ディレクトリ           |

---

## 6. テーマシステム

### 6.1 テーマ切替フロー

1. バックエンドは `appearance_mode`（`'light'` | `'dark'` | `'system'`）を `backend/settings.py` で永続化
2. フロントエンド起動時（`App.tsx`）、設定を取得し `document.documentElement.setAttribute('data-theme', ...)` で適用
3. `'system'` 選択時は `window.matchMedia('(prefers-color-scheme: dark)')` で実際のテーマを解決
4. ElectronメインプロセスはIPC経由で背景色を同期（`setThemeColor`）
   - ダーク： `#111827`
   - ライト： `#f9fafb`

### 6.2 CSS テーマ切替

テーマは `[data-theme='dark']` / `[data-theme='light']` 属性セレクタで切り替える。

---

## 7. アニメーション

### 7.1 定義済みキーフレーム

| 名前                | 動作                                     | 用途                                          |
| ------------------- | ---------------------------------------- | --------------------------------------------- |
| `progress-shimmer`  | `translateX(-100%)` → `translateX(100%)` | プログレスバーの輝きエフェクト（2s infinite） |
| `spin`              | `rotate(0deg)` → `rotate(360deg)`        | ローディングスピナー（1s linear infinite）    |
| `toast-in`          | `translateY(8px) scale(0.96)` → 正位置   | トースト登場                                  |
| `toast-out`         | 正位置 → `translateY(8px) scale(0.96)`   | トースト退場                                  |
| `modal-backdrop-in` | `opacity: 0` → `opacity: 1`              | モーダル背景登場                              |
| `modal-content-in`  | `scale(0.96) translateY(8px)` → 正位置   | モーダル内容登場                              |

### 7.2 トランジションパターン

| 用途                       | トランジション                          |
| -------------------------- | --------------------------------------- |
| デフォルト                 | `all 0.15s ease`                        |
| ドロップゾーン             | `all 0.3s cubic-bezier(0.4, 0, 0.2, 1)` |
| ボタン押下                 | `transform: scale(0.98)`                |
| プロファイルアイテムホバー | `transform: translateX(4px)`            |

### 7.3 フォーカスリング

すべてのインタラクティブ要素で統一：

```css
box-shadow:
  0 0 0 2px var(--color-primary),
  0 0 0 4px rgba(168, 85, 247, 0.2);
```

### 7.4 グラスモーフィズム（ダークモード）

```css
background: rgba(12, 12, 12, 0.9);
backdrop-filter: blur(24px);
-webkit-backdrop-filter: blur(24px);
```

---

## 8. アイコンライブラリ

すべてのアイコンは **lucide-React**（`lucide-react@^1.11.0`）を使用。

### 使用カテゴリ

| カテゴリ       | アイコン                                                            |
| -------------- | ------------------------------------------------------------------- |
| ナビゲーション | `Settings`, `Layers`                                                |
| アクション     | `Play`, `Save`, `RefreshCw`, `Download`, `RotateCcw`, `Trash2`, `X` |
| ファイル操作   | `Upload`, `FileSearch`                                              |
| ステータス     | `CheckCircle`, `XCircle`, `Loader2`, `Clock`, `AlertCircle`, `Info` |
| 品質           | `Sparkles`, `Search`, `ChevronDown`                                 |
| テーマ         | `Sun`, `Moon`, `Monitor`                                            |

---

## 9. アセット

| ファイル                       | 用途                                                     |
| ------------------------------ | -------------------------------------------------------- |
| `frontend/src/assets/logo.svg` | アプリロゴ。青（`#2563EB`）の角丸四角 + 白の幾何学図形   |
| `frontend/public/favicon.svg`  | ロゴと同一                                               |
| `frontend/public/icon.png`     | Electron ウィンドウ用アプリアイコン                      |
| `frontend/public/icons.svg`    | ソーシャル/リンクアイコン（Bluesky, Discord, GitHub 等） |

---

## 10. アクセシビリティ

- **スキップリンク**: `.skip-to-content` でメインコンテンツへのスキップを提供
- **フォーカス管理**: フォーカスリングは全インタラクティブ要素で統一
- **キーボードナビゲーション**: `CommandPalette` および `ComparisonSlider` は矢印キーに対応
- **ARIA ラベル**: 各コンポーネントに適切なARIA属性を設定

---

## 11. CSS アーキテクチャ

### 11.1 ファイル構成

| ファイル                 | 役割                                                   | 行数     |
| ------------------------ | ------------------------------------------------------ | -------- |
| `frontend/src/index.css` | デザイントークン定義、グローバルスタイル、キーフレーム | ~166 行  |
| `frontend/src/App.css`   | 全コンポーネントのスタイル（ダーク/ライトテーマ含む）  | ~1882 行 |

### 11.2 スタイルガイドライン

- Tailwind CSS v4（`@tailwindcss/vite` プラグイン）を使用
- デザイントークンは `index.css` の `@theme {}` で一元管理
- コンポーネントスタイルは `App.css` に集約（スコープ付きクラス）
- `[data-theme='dark']` / `[data-theme='light']` セレクタでテーマ切替
- インラインスタイルは可能な限り避け、CSSクラスを使用

### 11.3 フォーマット設定

```json
{
  "semi": false,
  "singleQuote": true,
  "printWidth": 100,
  "tabWidth": 2
}
```
