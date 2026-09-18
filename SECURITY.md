# Security Policy — Komari Next Stable

本仓库是 **Komari Next**（上游 `tonyliuzj/komari-next`）的社区维护镜像分支，只做稳定镜像、
自持构建与供应链独立，**不修改主题 UI 与业务功能**。

## 报告安全问题

- **上游本身的功能/安全问题**：请优先向上游私密报告；不要把未公开 PoC 直接发到公开 Issue。
- **本镜像引入的问题**（构建流程、打包产物、CI、依赖锁定、发布来源等）：请使用本仓库的
  [Private Security Advisory](https://github.com/xinian5216/komari-next-stable/security/advisories/new)。
- 跨 Server/Web/Agent/Next 的问题按
  [Komari Stable 安全响应流程](https://github.com/xinian5216/komari-stable/blob/stable/SECURITY_RESPONSE.md)
  统一协调。

请不要在公开 Issue、PR 或 Actions 日志中粘贴真实密钥、Token、账号、内部地址或可直接滥用的 PoC。

## 自动安全检查

- 每次相关 PR / `stable` 推送及每日定时任务运行 CodeQL；
- 对 production npm 依赖运行 high/critical 门禁，开发依赖告警单独评估；
- Dependabot 常规更新仅分组 minor/patch，不自动执行破坏性 major 升级；
- 扫描结果进入 GitHub Security / Code scanning，不自动公开漏洞细节。

## 本仓库的安全实践

- 完整保留上游 Git 历史与署名；`upstream-baseline` 分支只读。
- Release 只从**不可变 tag** 构建；生产使用方必须 pin 到具体 tag 与 SHA256（禁止 `main` / `releases/latest`）。
- `npm ci` 安装（锁定 `package-lock.json`），不静默漂移。
- 每次 push / PR 做全历史 secret 扫描（gitleaks，见 `.github/workflows/secret-scan.yml`）。
- 发布产物附 `SHA256SUMS` 与 `dist-release.zip.sha256`。
- 主题包在发布前按 Komari Server 的规则校验：布局、`short=next`、无符号链接、防路径穿越、
  文件数与大小上限（见 `scripts/validate-theme-package.py`）。
