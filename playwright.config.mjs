import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  timeout: 30000,
  expect: { timeout: 10000 },
  workers: 1,
  reporter: "list",
  use: {
    baseURL: "http://127.0.0.1:4178",
    locale: "zh-CN",
    trace: "retain-on-failure",
    launchOptions: process.env.KOMARI_TEST_CHROMIUM
      ? { executablePath: process.env.KOMARI_TEST_CHROMIUM }
      : {},
  },
  webServer: {
    command: "node tests/static-server.mjs",
    url: "http://127.0.0.1:4178",
    reuseExistingServer: false,
  },
});
