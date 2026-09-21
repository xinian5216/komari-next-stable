#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const manifest = JSON.parse(
  fs.readFileSync(path.join(root, "komari-theme.json"), "utf8"),
);
const version = manifest.version;

if (typeof version !== "string" || !/^\d+\.\d+\.\d+-stable\.\d+$/.test(version)) {
  throw new Error(
    `komari-theme.json version must use X.Y.Z-stable.N, received ${JSON.stringify(version)}`,
  );
}

const releaseTag = process.env.RELEASE_TAG;
if (releaseTag && releaseTag !== `v${version}`) {
  throw new Error(
    `release tag ${releaseTag} does not match manifest version v${version}`,
  );
}

console.log(
  releaseTag
    ? `theme version ${version} matches ${releaseTag}`
    : `theme version ${version} is valid`,
);
