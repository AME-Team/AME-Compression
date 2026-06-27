# AmeCompression Frontend

The desktop user interface for AmeCompression, built with Electron, React, and Vite.

## 🚀 Features

- **React 19**: Modern UI component architecture.
- **Electron**: Cross-platform desktop application shell.
- **Vite**: Ultra-fast development server and build tool.
- **Tailwind CSS**: Utility-first CSS framework for rapid UI development (if used).
- **Lucide React**: Beautiful & consistent iconography.
- **i18next**: Comprehensive internationalization support.

## 🛠️ Development

### Setup

```bash
# Install dependencies
npm install
```

### Run in Development Mode

Starts both the Vite dev server and the Electron application with HMR.

```bash
npm run electron:dev
```

### Build

Compiles the frontend assets and prepares them for production.

```bash
npm run build
```

## 🏗️ Architecture

- `src/`: React source code.
- `electron/`: Electron main and preload scripts.
- `public/`: Static assets.
- `dist/`: Compiled production build (generated after `npm run build`).
