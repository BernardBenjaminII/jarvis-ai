from pathlib import Path


class StorageManager:

    def __init__(self):
        self.runtime = Path("/mnt/jarvis_runtime")
        self.data = Path("/mnt/jarvis_data")

    def runtime_path(self):
        return self.runtime

    def data_path(self):
        return self.data

    def knowledge_path(self):
        return self.data / "Knowledge"

    def projects_path(self):
        return self.data / "Projects"

    def reports_path(self):
        return self.data / "Reports"

    def notes_path(self):
        return self.data / "Notes"

    def runtime_ok(self):
        return self.runtime.is_mount()

    def data_ok(self):
        return self.data.is_mount()
