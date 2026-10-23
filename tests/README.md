# Passkey login UI regression

These tests run the built static Next theme with the unmodified browser JS/CSS
from Akizon77/komari-passkey v0.1.13. The fixture preparation script pins the
published ZIP by SHA256 and extracts only the two UI files into ignored storage.
Plugin author: Akizon77; source: https://github.com/Akizon77/komari-passkey/tree/v0.1.13.
No plugin code is committed or changed.

`python3 scripts/tests/prepare_passkey_fixture.py`, `npm run build`,
`npx playwright install chromium`, then `npm run test:plugin-ui`.
An existing browser can be selected with `KOMARI_TEST_CHROMIUM`; a previously
downloaded fixture ZIP can be supplied with `KOMARI_PASSKEY_ZIP`, subject to the
same hash check.

Tests verify real computed styles, placement, responsive/light/dark modes,
dialog reopening, disabled and Passkey-only configurations, and request failure.
Backend responses are test fixtures; this is not an authenticated WebAuthn or
OAuth ceremony. Installation/password regression against Komari Server is a
separate check. Use temporary data and never production credentials.
