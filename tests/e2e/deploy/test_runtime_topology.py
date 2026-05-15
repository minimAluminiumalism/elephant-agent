from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]


class RuntimeTopologySmokeTest(unittest.TestCase):
    def test_runtime_support_assets_are_present_and_truthful(self) -> None:
        dockerfile = ROOT / "deploy" / "docker" / "runtime-support.Dockerfile"
        compose = ROOT / "deploy" / "docker" / "docker-compose.runtime-support.yml"
        unit = ROOT / "deploy" / "systemd" / "elephant-runtime-support.service"
        deploy_readme = ROOT / "deploy" / "README.md"

        self.assertTrue(dockerfile.exists())
        self.assertTrue(compose.exists())
        self.assertTrue(unit.exists())

        dockerfile_text = dockerfile.read_text(encoding="utf-8")
        compose_text = compose.read_text(encoding="utf-8")
        unit_text = unit.read_text(encoding="utf-8")
        readme_text = deploy_readme.read_text(encoding="utf-8")

        self.assertIn("python3 -m pip install --no-cache-dir -e .", dockerfile_text)
        self.assertIn('ENTRYPOINT ["elephant"]', dockerfile_text)
        self.assertIn("runtime-support", compose_text)
        self.assertIn("ELEPHANT_HERD_DIR", compose_text)
        self.assertNotIn("ELEPHANT_PROFILE_DIR", compose_text)
        self.assertIn("docker-compose.runtime-support.yml", unit_text)
        self.assertIn("elephant-runtime.env", unit_text)
        self.assertIn("Operator runtime support baseline", readme_text)
        self.assertIn("docker-compose.runtime-support.yml", readme_text)
        self.assertIn("/etc/elephant/elephant-runtime.env", readme_text)


if __name__ == "__main__":
    unittest.main()
