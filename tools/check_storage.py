from core.src.managers.storage_manager import StorageManager


def main():
    storage = StorageManager()

    print("=" * 50)
    print("JARVIS Storage Test")
    print("=" * 50)

    print(f"Runtime : {storage.runtime_path()}")
    print(f"Data    : {storage.data_path()}")

    print(f"Runtime mounted : {storage.runtime_ok()}")
    print(f"Data mounted    : {storage.data_ok()}")

    print(f"Knowledge : {storage.knowledge_path()}")
    print(f"Projects  : {storage.projects_path()}")
    print(f"Reports   : {storage.reports_path()}")

    print("=" * 50)


if __name__ == "__main__":
    main()
