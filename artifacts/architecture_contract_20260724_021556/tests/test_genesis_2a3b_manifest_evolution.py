import unittest

from dev.verification.genesis_manifest import (
    CERTIFIED_BASELINE,
    GenesisManifestError,
    parse_phase,
    validate_entries,
)

class TestGenesis2A3B(unittest.TestCase):
    def test_phase_parse(self):
        self.assertEqual(parse_phase("dev/verify_genesis_2a3b.sh").label,"2-A3B")

    def test_baseline(self):
        r=validate_entries(CERTIFIED_BASELINE)
        self.assertEqual(r.extension_count,0)

    def test_ordered_extensions(self):
        r=validate_entries((*CERTIFIED_BASELINE,
            "dev/verify_genesis_2a3b.sh",
            "dev/verify_genesis_2a4.sh"))
        self.assertEqual(r.extension_count,2)

    def test_duplicate_path(self):
        with self.assertRaises(GenesisManifestError):
            validate_entries((*CERTIFIED_BASELINE,
                "dev/verify_genesis_2a3b.sh",
                "dev/verify_genesis_2a3b.sh"))

    def test_out_of_order(self):
        with self.assertRaises(GenesisManifestError):
            validate_entries((*CERTIFIED_BASELINE,
                "dev/verify_genesis_2a4.sh",
                "dev/verify_genesis_2a3b.sh"))

    def test_fingerprint_stable(self):
        a=validate_entries(CERTIFIED_BASELINE).fingerprint
        b=validate_entries(CERTIFIED_BASELINE).fingerprint
        self.assertEqual(a,b)

    def test_invalid_path(self):
        with self.assertRaises(GenesisManifestError):
            validate_entries((*CERTIFIED_BASELINE,"verify.sh"))

if __name__=="__main__":
    unittest.main()
