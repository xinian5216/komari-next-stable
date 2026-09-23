# AGENTS.md — Komari Next Stable 工作规则

本仓库是 `tonyliuzj/komari-next` 的稳定镜像，主要职责是可复现构建、主题包校验、供应链独立和必要的
兼容维护。默认不得修改 `src/` 下的 UI 或业务功能。

## 进入仓库后先读

1. `UPSTREAM.md`：基线、允许的 fork 差异与作者归属；
2. `SECURITY.md`、`komari-theme.json`；
3. `scripts/package-theme.sh`、`scripts/validate-theme-package.py` 和 stable CI/Release workflow。

按任务定位文件，禁止无目的全仓库扫描或格式化。

## 红线

- 未经维护者明确确认，不得修改 `src/`、视觉表现、交互、翻译内容或 Komari API 调用。
- `komari-theme.json` 的 `short` 必须保持 `next`；作者、MIT License、Credits 和上游署名不得改动。
- `url` 必须指向 `xinian5216/komari-next-stable`，使后台更新跟随本镜像。
- 生产资产只从不可变 stable tag 构建；禁止依赖 `main`、`latest` 或未校验下载。
- 主题 ZIP 必须保持根目录 `komari-theme.json` / `preview.png` / `dist/` 布局，并通过路径穿越、
  符号链接、文件数和体积限制检查。
- Komari 模板占位符必须经过 `script/protect-komari-placeholders.mjs`（`npm run build` 已调用），不能被 Next.js 构建转义或改写。
- 不得覆盖既有 tag/Release；修复必须递增 stable tag。

## 提交前检查

```bash
npm ci
npm run lint
npm run test:plugin-hooks
npm run test:theme-version
npm run build
bash scripts/package-theme.sh
python3 scripts/validate-theme-package.py dist-release.zip
```

当前上游基线自带 lint 问题，lint 只报告时必须明确记录；`npm run build`、主题包校验和密钥扫描仍是硬门禁。
fork 边界或产物来源变化时同步更新 `UPSTREAM.md`。
