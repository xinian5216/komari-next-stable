# Security Policy — Komari Next Stable

本仓库是 **Komari Next**（上游 `tonyliuzj/komari-next`）的社区维护镜像分支，只做稳定镜像、
自持构建与供应链独立，**不修改主题 UI 与业务功能**。

## 报告安全问题

- **上游本身的功能/安全问题**：请优先向上游报告 —— <https://github.com/tonyliuzj/komari-next/issues>。
- **本镜像引入的问题**（构建流程、打包产物、CI、依赖锁定等）：请在本仓库开 issue，
  或在无法公开讨论时通过维护者 GitHub 主页的联系方式私信（`xinian5216`）。

请不要在公开 issue 中粘贴真实密钥、token、账号或内部地址。

## 本仓库的安全实践

- 完整保留上游 Git 历史与署名；`upstream-baseline` 分支只读。
- Release 只从**不可变 tag** 构建；生产使用方必须 pin 到具体 tag 与 SHA256（禁止 `main` / `releases/latest`）。
- `npm ci` 安装（锁定 `package-lock.json`），不静默漂移。
- 每次 push / PR 做全历史 secret 扫描（gitleaks，见 `.github/workflows/secret-scan.yml`）。
- 发布产物附 `SHA256SUMS` 与 `dist-release.zip.sha256`。
- 主题包在发布前按 Komari Server 的规则校验：布局、`short=next`、无符号链接、防路径穿越、
  文件数与大小上限（见 `scripts/validate-theme-package.py`）。
