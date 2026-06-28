from core.src.discovery.runtime_locator import RuntimeLocator

locator = RuntimeLocator("ubuntu")

runtime = locator.locate()

if runtime is None:
    print("Runtime not found")
else:
    print(f"\nRuntime: {runtime}")
