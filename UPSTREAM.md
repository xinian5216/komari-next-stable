# UPSTREAM.md — 上游来源与本 fork 关系（komari-next-stable）

> 溯源记录：任何时候都能据此判断"哪些是原项目代码，哪些是 Komari Stable 的改动"。

## 1. 原项目

| 项 | 值 |
| --- | --- |
| Original Project | **Komari Next**（Komari 的现代前端主题，Next.js + TypeScript + Tailwind + shadcn/ui，构建为静态站点作为 Komari 主题使用） |
| Original Repository | https://github.com/tonyliuzj/komari-next |
| Author / Credits | **Tony Liu**（`tonyliuzj`，<https://tony-liu.com>）及其贡献者 |
| Original License | **MIT**（`Copyright (c) 2025 Tony Liu (tonyliuzj, tony-liu.com)`），`LICENSE` 原样保留、未做任何修改 |
| 主题包声明 | `komari-theme.json`：`short = next`、`name = Komari Next`（保留原样） |

## 2. Fork 基线

| 项 | 值 |
| --- | --- |
| Fork 日期 | 2026-09-17 |
| 基线 ref | upstream tag `1.4.19` |
| 基线 commit | `914761b838d4b0f5c03a040debc0b79535be0669`（2026-07-23，`Bump version to 1.4.19`） |
| 维护分支 | `stable`（本仓库默认分支） |
| 只读镜像分支 | `upstream-baseline`（= 上述基线 commit，**永不修改**） |
| 固定 tag | `v1.4.19-stable.0` |
| 维护者 | `xinian5216`（Komari Stable） |
| 生产构建输入 | **只允许** `xinian5216/komari-next-stable@<不可变 stable tag>`；**禁止** `main` / `releases/latest` |

## 3. 本 fork 的改动（相对上游基线 `914761b`）

本 fork 以镜像、自持构建和供应链独立为主，只接受不改变既有视觉与业务逻辑的必要兼容修复。

1. **新增 CI**（`.github/workflows/stable-ci.yml`）：`npm ci` → `npm run lint` → `npm run build` →
   主题包校验 → 产出 `dist-release.zip` 与 `SHA256SUMS`。
2. **新增 Release 流程**（`.github/workflows/stable-release.yml`）：从 release tag 构建，
   校验通过后上传 `dist-release.zip`、`SHA256SUMS`、`dist-release.zip.sha256`。
3. **新增主题包校验器**（`scripts/validate-theme-package.py`）与打包脚本（`scripts/package-theme.sh`），
   校验规则与 Komari Server 端（`web/api/admin/theme.go`）一致：根布局（`komari-theme.json` /
   `preview.png` / `dist/`）、`short=next`、无符号链接、防路径穿越、文件数与大小上限。
4. **新增 Secret Scan**（`.github/workflows/secret-scan.yml` + `.gitleaks.toml`）：全历史扫描。
5. **删除与上游耦合、或依赖本 fork 不使用的密钥/分支的 workflow**：
   `build.yaml`（上游自带 Release 资产流程，已由本 fork 的 release 流程取代）、
   `i18n-sync.yml`（依赖上游 Crowdin 密钥并会自动提交）、
   `preview-theme.yaml`（仅针对上游 `radix` 分支）。均以普通提交删除，**保留 git 历史**。
6. **修正 `package.json` 的 lint 入口**：上游仍写 `next lint`，但 Next 16 已移除该命令
   （原脚本在本 fork 无法运行）。改为 `eslint .`（仓库自带 `eslint.config.js`，eslint ^9），
   **未触碰任何 lint 规则与业务源码**。上游 `src/` 在 `1.4.19` 基线自带 **23 error / 29 warning**，
   本 fork 不修改主题源码，因此 CI / Release 中 lint 以**报告模式**运行（产物 `lint-report.txt`），
   不作为硬门禁；`npm ci` / `npm run build` / 主题包校验 / secret scan 仍是硬门禁。
7. **新增文档**：本文件、`SECURITY.md`，以及 `README.md` / `README-CN.md` 顶部的 fork 说明。
8. **供应链接管（`v1.4.19-stable.1` 起）**：`komari-theme.json` 的 `url` 由上游仓库改为本镜像
   `https://github.com/xinian5216/komari-next-stable`，使 Komari 后台的"更新主题"跟随本镜像的
   Release，而不是上游 latest。**作者字段仍为 `tonyliuzj`，MIT 许可、署名与 Credits 全部未动**，
   也不涉及任何 UI / 主题业务源码改动。
9. **`README.md` / `README-CN.md` 的"下载主题文件"链接**改指本镜像 Releases 页（其余上游链接：
   预览图、跨语言链接、贡献者、Star History、页脚署名等**全部保留**）。
10. **Passkey 插件登录兼容（Issue #14）**：为 Next 登录对话框和表单容器补齐核心 Web 已有的
    `km-login-dialog` / `km-login-form` 稳定挂载类，使 `komari-passkey` 的 HTML 注入能够找到
    登录入口。该改动不改变密码/OAuth 流程、视觉布局、Komari API 或已注册凭据；CI 与 Release
    均运行 `test:plugin-hooks` 合同检查，防止后续重构误删挂载点。
11. **移除遗留生产 SSH 部署**：删除已停用但仍保留 `PRODUCTION_SSH_KEY`、root SSH 与
    `rsync --delete` 的 `development.yaml`；所有保留的第三方 Actions 固定到完整 commit SHA，
    stable CI 自动拒绝浮动 tag 和缺失精确版本注释的引用。
12. **主题 stable 版本可见性**（`v1.4.19-stable.5` 起）：`komari-theme.json` 使用完整的
    `X.Y.Z-stable.N` 版本，使主题管理页能显示已安装的维护修订号；CI 校验格式，Release 流程
    额外要求 tag 必须严格等于 `v<manifest version>`，防止发布标签与安装包显示不一致。

> `src/` 仅包含上述登录兼容类差异；`LICENSE`、作者署名与 Credits 未改动。`komari-theme.json`
> 仅把更新 URL 与版本切换到本镜像维护线，其余主题身份与配置保持上游原样。

## 4. 溯源方法

```bash
git diff upstream-baseline --stat     # 全部差异（还应包含已记录的登录挂载类与主题元数据变更）
git diff upstream-baseline -- <path>  # 单文件差异
git log --oneline upstream-baseline..stable
```
