export const KOMARI_STABLE_RELEASES_API =
  "https://api.github.com/repos/xinian5216/komari-stable/releases?per_page=100";

export interface GithubReleaseInfo {
  tag_name: string;
  name?: string;
  body?: string;
  html_url: string;
  published_at?: string;
  draft?: boolean;
  prerelease?: boolean;
}

type StableVersion = [number, number, number, number];

/**
 * Parse the Komari Stable maintenance version scheme.
 *
 * `stable.N` is a fork maintenance revision and therefore participates in
 * ordering after major/minor/patch instead of being treated as a SemVer
 * prerelease suffix.
 */
export function parseStableVersion(
  input?: string | null
): StableVersion | null {
  if (!input) return null;

  const match = String(input)
    .trim()
    .match(/^v?(\d+)\.(\d+)\.(\d+)-stable\.(\d+)$/i);
  if (!match) return null;

  return [
    Number(match[1]),
    Number(match[2]),
    Number(match[3]),
    Number(match[4]),
  ];
}

export function compareStableVersions(
  left?: string | null,
  right?: string | null
): number | null {
  const a = parseStableVersion(left);
  const b = parseStableVersion(right);
  if (!a || !b) return null;

  for (let i = 0; i < a.length; i += 1) {
    if (a[i] > b[i]) return 1;
    if (a[i] < b[i]) return -1;
  }
  return 0;
}

export function isNewerStableVersion(
  latest?: string | null,
  current?: string | null
): boolean {
  return compareStableVersions(latest, current) === 1;
}

export function selectNewerStableReleases(
  releases: GithubReleaseInfo[],
  currentVersion: string
): GithubReleaseInfo[] {
  return releases
    .filter((release) => !release.draft && !release.prerelease)
    .filter((release) =>
      isNewerStableVersion(release.tag_name, currentVersion)
    )
    .sort(
      (left, right) =>
        compareStableVersions(right.tag_name, left.tag_name) ?? 0
    );
}
