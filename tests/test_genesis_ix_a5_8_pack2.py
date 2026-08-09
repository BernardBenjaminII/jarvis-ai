import sqlite3, tempfile, unittest
from pathlib import Path
from dev.materializer_eligibility.audit import MaterializerEligibilityAudit

class Tests(unittest.TestCase):
    def make(self, root: Path):
        knowledge = root / "Knowledge"
        knowledge.mkdir()
        good = knowledge / "good.txt"
        good.write_text("hello", encoding="utf-8")
        missing = knowledge / "missing.txt"

        runtime = root / "runtime.sqlite"
        c = sqlite3.connect(runtime)
        c.execute("CREATE TABLE knowledge_classifications(id INTEGER PRIMARY KEY,file_path TEXT,status TEXT)")
        c.execute("CREATE TABLE runtime_documents(id INTEGER PRIMARY KEY,file_path TEXT)")
        c.executemany(
            "INSERT INTO knowledge_classifications(file_path,status) VALUES(?,?)",
            [(str(good), "classified"), (str(missing), "classified")]
        )
        c.execute("INSERT INTO runtime_documents(file_path) VALUES(?)", (str(good),))
        c.commit(); c.close()

        inventory = root / "inventory.sqlite"
        c = sqlite3.connect(inventory)
        c.execute("CREATE TABLE documents(id INTEGER PRIMARY KEY,path TEXT)")
        c.commit(); c.close()
        return knowledge, runtime, inventory

    def test_dispositions(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            knowledge, runtime, inventory = self.make(root)
            report = MaterializerEligibilityAudit(
                project_root=root,
                runtime_catalog=runtime,
                inventory_catalog=inventory,
                knowledge_root=knowledge,
            ).execute()
            counts = report.summary["disposition_counts"]
            self.assertEqual(counts["ALREADY_MATERIALIZED"], 1)
            self.assertEqual(counts["MISSING_SOURCE_FILE"], 1)

    def test_read_only(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            knowledge, runtime, inventory = self.make(root)
            before = runtime.read_bytes()
            MaterializerEligibilityAudit(
                project_root=root,
                runtime_catalog=runtime,
                inventory_catalog=inventory,
                knowledge_root=knowledge,
            ).execute()
            self.assertEqual(before, runtime.read_bytes())

if __name__ == "__main__":
    unittest.main()
