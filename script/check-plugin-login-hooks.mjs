import { readFileSync } from "node:fs";

const source = readFileSync(
  new URL("../src/components/Login.tsx", import.meta.url),
  "utf8",
);

const contracts = [
  {
    name: "login dialog exposes the plugin mount hook",
    pattern:
      /<DialogContent\b[\s\S]*?className=["'][^"']*\bkm-login-dialog\b[^"']*["'][\s\S]*?>/,
  },
  {
    name: "login form exposes the plugin mount hook",
    pattern:
      /<Box\b[\s\S]*?className=["'][^"']*\bkm-login-form\b[^"']*["'][\s\S]*?>/,
  },
];

let failed = 0;
for (const contract of contracts) {
  if (contract.pattern.test(source)) {
    console.log(`ok - ${contract.name}`);
    continue;
  }
  failed += 1;
  console.error(`not ok - ${contract.name}`);
}

if (failed > 0) {
  console.error(`plugin login hook contract: ${failed} failed`);
  process.exit(1);
}

console.log(`plugin login hook contract: ${contracts.length} passed`);
