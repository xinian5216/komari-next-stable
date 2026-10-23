import { expect, test } from "@playwright/test";
import { resolve } from "node:path";

const fixture = resolve("tests/.fixtures/passkey-0.1.13");

async function openLogin(page, { oauth = true, enabled = true, password = true, dark = false } = {}) {
  await page.addInitScript(({ dark }) => {
    localStorage.setItem("theme", dark ? "dark" : "light");
    localStorage.setItem("komari-appearance", dark ? "dark" : "light");
    localStorage.setItem("i18nextLng", "zh_CN");
  }, { dark });
  await page.route("**/api/**", async route => {
    const pathname = new URL(route.request().url()).pathname;
    let body = { status: "success", data: [] };
    if (pathname === "/api/public") {
      body.data = { sitename: "Komari", theme: "next", theme_settings: {}, oauth_enable: oauth, oauth_provider: "github", disable_password_login: !password };
    } else if (pathname === "/api/me") {
      body = { logged_in: false };
    } else if (pathname === "/api/komari-passkey/status") {
      body = { ok: true, enabled };
    }
    await route.fulfill({ json: body });
  });
  await page.goto("/");
  await page.addStyleTag({ content: ".km-login-dialog { animation: none !important; transition: none !important; }" });
  await page.addStyleTag({ path: resolve(fixture, "passkey-ui.css") });
  await page.addScriptTag({ path: resolve(fixture, "passkey-ui.js") });
  await page.getByRole("button", { name: "登录", exact: true }).click();
  const dialog = page.locator(".km-login-dialog");
  await expect(dialog).toBeVisible();
  if (dark) await expect(page.locator("html")).toHaveClass(/dark/);
  else await expect(page.locator("html")).not.toHaveClass(/dark/);
  return dialog;
}

async function paintedStyle(locator) {
  return locator.evaluate(node => {
    const style = getComputedStyle(node);
    return { background: style.backgroundColor, fontSize: style.fontSize, radius: style.borderRadius };
  });
}

for (const width of [1440, 390]) {
  for (const dark of [false, true]) {
    test(`actual plugin: matched buttons, ${width}px, ${dark ? "dark" : "light"}`, async ({ page }, testInfo) => {
      await page.setViewportSize({ width, height: 900 });
      const dialog = await openLogin(page, { dark });
      const passkey = dialog.locator(".km-passkey-login");
      const oauth = dialog.getByRole("button", { name: "使用 Github 登录" });
      await expect(passkey).toHaveCount(1);
      await expect(passkey).toBeVisible();
      await expect(passkey.locator("..")).toHaveClass(/km-login-alternatives/);
      const key = await passkey.boundingBox();
      const github = await oauth.boundingBox();
      expect(Math.abs(key.height - github.height)).toBeLessThanOrEqual(1);
      expect(Math.abs(key.width - github.width)).toBeLessThanOrEqual(1);
      expect(Math.abs(key.x - github.x)).toBeLessThanOrEqual(1);
      expect(key.y - github.y - github.height).toBeGreaterThanOrEqual(8);
      expect(key.y + key.height).toBeLessThan(900);
      expect(await paintedStyle(passkey)).toEqual(await paintedStyle(oauth));
      await dialog.screenshot({ path: testInfo.outputPath("login.png") });
      await dialog.getByRole("button", { name: "Close" }).click();
      await page.getByRole("button", { name: "登录", exact: true }).click();
      await expect(page.locator(".km-passkey-login")).toHaveCount(1);
    });
  }
}

test("actual plugin: no OAuth, disabled plugin and password-only fallback", async ({ page }) => {
  const dialog = await openLogin(page, { oauth: false, enabled: false });
  await expect(dialog.locator(".km-login-alternatives")).toBeHidden();
  await expect(dialog.locator(".km-passkey-login")).toHaveCount(0);
  await dialog.getByPlaceholder("admin", { exact: true }).fill("test-user");
  await dialog.locator("input[type=password]").fill("fixture-password");
  await expect(dialog.getByRole("button", { name: "登录", exact: true })).toBeEnabled();
});

test("actual plugin: Passkey-only login remains a visible full-width button", async ({ page }) => {
  const dialog = await openLogin(page, { password: false, oauth: false });
  const passkey = dialog.locator(".km-passkey-login");
  await expect(passkey).toBeVisible();
  await expect(dialog.locator("input[type=password]")).toHaveCount(0);
  const box = await passkey.boundingBox();
  expect(box.height).toBe(36);
  expect(box.width).toBeGreaterThan(250);
});

test("actual plugin: request failure restores the button and preserves password login", async ({ page }) => {
  const dialog = await openLogin(page, { oauth: false });
  let releaseResponse;
  const response = new Promise(resolve => { releaseResponse = resolve; });
  await page.route("**/api/komari-passkey/authentication/options?**", async route => {
    await response;
    await route.fulfill({ status: 400, json: { ok: false, code: "verification_failed" } });
  });
  const button = dialog.locator(".km-passkey-login");
  await button.click();
  await expect(button).toBeDisabled();
  releaseResponse();
  await expect(dialog.getByRole("alert")).toBeVisible();
  await expect(button).toBeEnabled();
  await expect(button).toHaveText("通过通行密钥登录");
  await dialog.getByPlaceholder("admin", { exact: true }).fill("test-user");
  await dialog.locator("input[type=password]").fill("fixture-password");
  await expect(dialog.getByRole("button", { name: "登录", exact: true })).toBeEnabled();
});
