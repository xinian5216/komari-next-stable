import assert from "node:assert/strict";
import test from "node:test";

import {
  KOMARI_STABLE_RELEASES_API,
  compareStableVersions,
  isNewerStableVersion,
  parseStableVersion,
  selectNewerStableReleases,
  type GithubReleaseInfo,
} from "../src/utils/serverRelease.ts";

test("checks releases from the maintained server mirror", () => {
  assert.equal(
    KOMARI_STABLE_RELEASES_API,
    "https://api.github.com/repos/xinian5216/komari-stable/releases?per_page=100"
  );
});

test("parses the stable maintenance revision", () => {
  assert.deepEqual(parseStableVersion("1.5.0-stable.3"), [1, 5, 0, 3]);
  assert.deepEqual(parseStableVersion("v1.5.0-stable.5"), [1, 5, 0, 5]);
  assert.equal(parseStableVersion("1.5.0"), null);
  assert.equal(parseStableVersion("v1.5.0-beta.1"), null);
});

test("detects a newer stable revision with the same base version", () => {
  assert.equal(
    isNewerStableVersion("v1.5.0-stable.5", "1.5.0-stable.3"),
    true
  );
  assert.equal(
    isNewerStableVersion("v1.5.0-stable.3", "1.5.0-stable.3"),
    false
  );
  assert.equal(
    compareStableVersions("v1.6.0-stable.0", "v1.5.9-stable.99"),
    1
  );
});

test("filters and orders only newer production stable releases", () => {
  const release = (
    tag_name: string,
    overrides: Partial<GithubReleaseInfo> = {}
  ): GithubReleaseInfo => ({
    tag_name,
    html_url: `https://example.invalid/${tag_name}`,
    ...overrides,
  });

  const result = selectNewerStableReleases(
    [
      release("v1.5.0-stable.4"),
      release("v1.5.0-stable.5"),
      release("v1.5.0-stable.6", { draft: true }),
      release("v1.6.0-stable.0", { prerelease: true }),
      release("v1.5.0"),
      release("v1.5.0-stable.2"),
    ],
    "1.5.0-stable.3"
  );

  assert.deepEqual(
    result.map((item) => item.tag_name),
    ["v1.5.0-stable.5", "v1.5.0-stable.4"]
  );
});
