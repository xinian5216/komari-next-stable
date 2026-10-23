"""Offline regression checks for immutable theme publication."""

from pathlib import Path
import hashlib
import importlib.util
import subprocess
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("publisher", ROOT / "scripts/publish-release-assets.py")
publisher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(publisher)
REPOSITORY = "example/komari-next-stable"
TAG = "v1.4.19-stable.8"


class FakeGitHub:
    def __init__(self, assets=None):
        self.assets = dict(assets or {})
        self.uploads = []
        self.reads = 0
        self.metadata = {}
        self.read_error = False
        self.download_error = False
        self.partial_failure = False
        self.race = False
        self.tamper = False

    def release(self, repository, tag):
        self.reads += 1
        if self.read_error:
            raise OSError("GitHub unavailable")
        return {
            "tag_name": tag, "draft": False, "prerelease": False,
            "assets": [{"id": publisher.ASSET_NAMES.index(name) + 1, "name": name, "state": "uploaded"}
                       for name in self.assets],
            **self.metadata,
        }

    def download(self, repository, asset_id):
        if self.download_error:
            raise OSError("asset download failed")
        return self.assets[publisher.ASSET_NAMES[asset_id - 1]]

    def upload(self, repository, tag, paths):
        self.uploads.append([p.name for p in paths])
        if self.race:
            self.assets["dist-release.zip"] = b"concurrent-published-build"
        for index, path in enumerate(paths):
            if path.name in self.assets:
                raise OSError("GitHub rejects duplicate asset name")
            self.assets[path.name] = path.read_bytes()
            if self.partial_failure and index == 0:
                raise OSError("connection lost during partial upload")
        if self.tamper:
            self.assets["dist-release.zip"] = b"unexpected-published-bytes"


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        payload = b"theme-build-fixture"
        digest = hashlib.sha256(payload).hexdigest()
        self.payloads = {
            "dist-release.zip": payload,
            "SHA256SUMS": f"{digest}  dist-release.zip\n".encode(),
            "dist-release.zip.sha256": f"{digest}\n".encode(),
        }
        for name, content in self.payloads.items():
            (self.directory / name).write_bytes(content)

    def publish(self, github, **kwargs):
        return publisher.publish(REPOSITORY, TAG, self.directory, github=github, **kwargs)

    def test_first_publication_uploads_and_verifies_three_assets(self):
        github = FakeGitHub()
        self.assertEqual(self.publish(github), list(publisher.ASSET_NAMES))
        self.assertEqual(github.assets, self.payloads)
        self.assertEqual(github.reads, 2)

    def test_identical_retry_performs_no_upload(self):
        github = FakeGitHub(self.payloads)
        self.assertEqual(self.publish(github), [])
        self.assertEqual(github.uploads, [])
        self.assertEqual(github.assets, self.payloads)

    def test_partial_release_only_uploads_missing_checksums(self):
        github = FakeGitHub({"dist-release.zip": self.payloads["dist-release.zip"]})
        self.assertEqual(self.publish(github), ["SHA256SUMS", "dist-release.zip.sha256"])
        self.assertEqual(github.uploads, [["SHA256SUMS", "dist-release.zip.sha256"]])
        self.assertEqual(github.assets, self.payloads)

    def test_any_changed_asset_fails_before_uploading_missing_assets(self):
        for name in publisher.ASSET_NAMES:
            with self.subTest(name=name):
                github = FakeGitHub({name: b"older-published-content"})
                with self.assertRaisesRegex(publisher.PublicationError, "immutable release asset mismatch"):
                    self.publish(github)
                self.assertEqual(github.uploads, [])
                self.assertEqual(github.assets, {name: b"older-published-content"})

    def test_read_and_download_errors_never_become_missing_assets(self):
        for failure in ("read_error", "download_error"):
            with self.subTest(failure=failure):
                github = FakeGitHub(self.payloads)
                setattr(github, failure, True)
                with self.assertRaises(OSError):
                    self.publish(github)
                self.assertEqual(github.uploads, [])

    def test_partial_upload_failure_can_resume_without_replacing_zip(self):
        github = FakeGitHub()
        github.partial_failure = True
        with self.assertRaises(OSError):
            self.publish(github)
        self.assertEqual(github.assets, {"dist-release.zip": self.payloads["dist-release.zip"]})
        github.partial_failure = False
        self.assertEqual(self.publish(github), ["SHA256SUMS", "dist-release.zip.sha256"])
        self.assertEqual(github.assets, self.payloads)

    def test_concurrent_publication_is_rejected_without_replacement(self):
        github = FakeGitHub()
        github.race = True
        with self.assertRaises(OSError):
            self.publish(github)
        self.assertEqual(github.assets, {"dist-release.zip": b"concurrent-published-build"})
        self.assertEqual(len(github.uploads), 1)

    def test_post_upload_changed_bytes_fail_verification(self):
        github = FakeGitHub()
        github.tamper = True
        with self.assertRaisesRegex(publisher.PublicationError, "immutable release asset mismatch"):
            self.publish(github)

    def test_invalid_release_metadata_is_rejected_without_upload(self):
        invalid = [
            {"draft": True}, {"prerelease": True}, {"tag_name": "v1.4.19-stable.0"},
            {"assets": None},
            {"assets": [{"id": 1, "name": "dist-release.zip", "state": "starter"}]},
            {"assets": [{"id": True, "name": "dist-release.zip", "state": "uploaded"}]},
            {"assets": [None]},
            {"assets": [{"id": 1, "name": "dist-release.zip", "state": "uploaded"}] * 2},
        ]
        for metadata in invalid:
            with self.subTest(metadata=metadata):
                github = FakeGitHub()
                github.metadata = metadata
                with self.assertRaises(publisher.PublicationError):
                    self.publish(github)
                self.assertEqual(github.uploads, [])

    def test_check_only_never_uploads(self):
        github = FakeGitHub()
        self.assertEqual(self.publish(github, check_only=True), list(publisher.ASSET_NAMES))
        self.assertEqual(github.uploads, [])
        self.assertEqual(github.assets, {})

    def test_missing_local_asset_fails_before_api_access(self):
        (self.directory / "dist-release.zip").unlink()
        github = FakeGitHub()
        with self.assertRaises(OSError):
            self.publish(github)
        self.assertEqual(github.reads, 0)
        self.assertEqual(github.uploads, [])

    def test_bad_local_checksums_fail_before_api_access(self):
        for name in ("SHA256SUMS", "dist-release.zip.sha256"):
            with self.subTest(name=name):
                (self.directory / name).write_text("bad checksum", encoding="ascii")
                github = FakeGitHub()
                with self.assertRaises(publisher.PublicationError):
                    self.publish(github)
                self.assertEqual(github.reads, 0)
                (self.directory / name).write_bytes(self.payloads[name])

    def test_invalid_repository_or_tag_never_calls_api(self):
        for repository, tag in ((REPOSITORY, "stable"), (REPOSITORY, "v1.4.19"), ("../invalid", TAG)):
            github = FakeGitHub()
            with self.assertRaises(publisher.PublicationError):
                publisher.publish(repository, tag, self.directory, github=github)
            self.assertEqual(github.reads, 0)

    def test_cli_upload_uses_plain_upload_and_propagates_duplicate_failure(self):
        github = publisher.GitHub()
        with patch.object(publisher.subprocess, "run") as run:
            run.side_effect = subprocess.CalledProcessError(1, "gh")
            with self.assertRaises(subprocess.CalledProcessError):
                github.upload(REPOSITORY, TAG, [self.directory / "dist-release.zip"])
            arguments = run.call_args.args[0]
            self.assertEqual(arguments[:4], ["gh", "release", "upload", TAG])
            self.assertNotIn("--clobber", arguments)
            self.assertEqual(run.call_count, 1)


class WorkflowContractTests(unittest.TestCase):
    def test_workflow_does_not_replace_assets(self):
        release = (ROOT / '.github/workflows/stable-release.yml').read_text(encoding='utf-8')
        self.assertNotIn('--clobber', release)
        self.assertIn('python3 scripts/publish-release-assets.py', release)
        self.assertLess(release.index('Require immutable publication guard'), release.index('Install dependencies'))
        ci = (ROOT / '.github/workflows/stable-ci.yml').read_text(encoding='utf-8')
        self.assertIn("python3 -m unittest discover -s scripts/tests -p 'test_*.py'", ci)


if __name__ == '__main__':
    unittest.main()
