# AGENTS.md — Komari Next Stable 工作规则

本仓库是 `tonyliuzj/komari-next` 的稳定镜像，主要职责是可复现构建、主题包校验、供应链独立和必要的
兼容维护。默认不得修改 `src/` 下的 UI 或业务功能。

## 进入仓库后先读

1. `UPSTREAM.md`：基线、允许的 fork 差异与作者归属；
2. `SECURITY.md`、`komari-theme.json`；
3. `scripts/package-theme.sh`、`scripts/validate-theme-package.py` 和 stable CI/Release workflow。
4. 提交 / CI / 发布任务读取 `.github/REQUIRED_CHECKS.md` 以及安全、密钥扫描 workflow；
   Node / npm 与构建 workflow 保持一致，依赖版本以清单和锁文件为准。

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
- 保持 `next.config.ts` 的静态导出与 `images.unoptimized` 部署约定；生产兼容验证应通过
  Komari Server 安装主题，不能用 `next start` 代替静态主题验证。

## 提交前检查

```bash
npm ci
npm run lint
npm run test:plugin-hooks
npm run test:theme-version
npm run i18n:sync:dry
python3 -m unittest discover -s scripts/tests -p 'test_*.py'
npm run build
bash scripts/package-theme.sh
python3 scripts/validate-theme-package.py dist-release.zip
npm audit --omit=dev --audit-level=high
python3 .github/scripts/check-workflow-pins.py
gitleaks git . --log-opts="--all" --config .gitleaks.toml --redact
gitleaks dir . --config .gitleaks.toml --redact
```

当前上游基线自带 lint 问题，lint 只报告时必须明确记录；`npm run build`、主题包校验和密钥扫描仍是硬门禁。
lint 在干净检出、构建前执行；已有生成目录时排除 `.next/` 和 `dist/` 后比较源码基线。
不得把新增 lint 问题归入既有基线。生产 npm audit 通过不代表开发 / 构建依赖无漏洞，依赖维护
还需评估完整报告；不得批量漂移锁文件或依赖构建时临时安装来掩盖缺失的开发依赖。
fork 边界或产物来源变化时同步更新 `UPSTREAM.md`。

## 合并与发布

- 所有变更经 PR 进入 `stable`，等待 `.github/REQUIRED_CHECKS.md` 全部门禁成功；CodeQL
  不能代替 npm audit，失败、取消或跳过不算通过。发布前复核合并后精确 commit 的检查与 tag 目标。
- tag 必须严格等于 `v<komari-theme.json version>`，并通过发布 workflow 中的版本检查。
  通过 `scripts/publish-release-assets.py` 上传：已存在且字节一致则跳过，不一致则失败；
  只补缺失资产，禁止覆盖或先删除再上传。没有该守卫的历史 tag 不允许通过新流程自动重发。
- 发布后重新下载 ZIP，对照两份校验文件及实际 SHA256，验证包布局、版本和作者。
  在隔离 Server 中验证上传安装、主题启用、密码登录与页面；插件挂载合同不等同于真实
  OAuth / Passkey 端到端测试，未测试部分须说明。
- Server 随包主题需另行更新 `bundled-themes.lock.json` 并重新发布；已有站点主题不自动替换。
  推送、合并、发布与线上部署按本次任务明确授权的范围执行，已有授权无需重复确认。
