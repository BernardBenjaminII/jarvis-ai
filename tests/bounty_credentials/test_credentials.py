import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from core.bounty_catalog import credentials as c
from core.bounty_catalog.hackerone import DiscoveryError

class CredentialTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'private/hackerone.json'

    def test_save_load_replace_forget(self):
        self.assertIsNone(c.load(self.path))
        c.save('test-user','fake-token',self.path)
        self.assertEqual(c.load(self.path),('test-user','fake-token'))
        self.assertEqual(self.path.stat().st_mode & 0o777,0o600)
        self.assertEqual(self.path.parent.stat().st_mode & 0o777,0o700)
        c.save('test-user','new-fake-token',self.path)
        self.assertEqual(c.load(self.path)[1],'new-fake-token')
        c.forget(self.path)
        self.assertIsNone(c.load(self.path))

    def test_saved_credentials_do_not_prompt(self):
        with patch.object(c,'load',return_value=('test-user','fake-token')), patch.object(c,'prompt') as prompt:
            self.assertEqual(c.resolve(),('test-user','fake-token'))
            prompt.assert_not_called()

    def test_missing_falls_back_to_prompt(self):
        with patch.object(c,'load',return_value=None), patch.object(c,'prompt',return_value=('test-user','fake-token')) as prompt:
            self.assertEqual(c.resolve(),('test-user','fake-token'))
            prompt.assert_called_once()

    def test_reject_open_permissions(self):
        c.save('test-user','fake-token',self.path)
        self.path.chmod(0o644)
        with self.assertRaises(DiscoveryError): c.load(self.path)
        self.path.chmod(0o600)
        self.path.parent.chmod(0o755)
        with self.assertRaises(DiscoveryError): c.load(self.path)

    def test_reject_symlink(self):
        self.path.parent.mkdir(mode=0o700)
        self.path.symlink_to(Path(self.tmp.name)/'elsewhere')
        with self.assertRaises(DiscoveryError): c.save('test-user','fake-token',self.path)
        with self.assertRaises(DiscoveryError): c.load(self.path)

    def test_invalid_data_does_not_leak(self):
        c.save('test-user','fake-token',self.path)
        self.path.write_text('{"token":"private-value"}')
        with self.assertRaises(DiscoveryError) as err: c.load(self.path)
        self.assertNotIn('private-value',str(err.exception))
        with self.assertRaises(DiscoveryError): c.save('user','bad\ntoken',self.path)

    def test_status_contains_no_secret(self):
        from core.bounty_catalog.__main__ import main
        import io
        with patch('sys.argv',['catalog','auth','status']), patch.object(c,'load',return_value=('test-user','fake-token')), patch('sys.stdout',new_callable=io.StringIO) as out:
            self.assertEqual(main(),0)
            self.assertEqual(json.loads(out.getvalue()),{'credentials_saved':True,'encrypted':False})

if __name__=='__main__': unittest.main()
