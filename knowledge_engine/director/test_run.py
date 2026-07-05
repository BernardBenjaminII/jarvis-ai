from pathlib import Path

from knowledge_engine.storage.database import KnowledgeDatabase

from knowledge_engine.director.context import AssimilationContext

from knowledge_engine.director.director import AssimilationDirector

from knowledge_engine.director.registry import StageRegistry


def main():

    db = KnowledgeDatabase("/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite")

    ctx = AssimilationContext(

        root=Path("."),

        database=db,
    )

    registry = StageRegistry()

    registry.register_defaults()

    director = AssimilationDirector(registry)

    report = director.run(ctx)

    report.print()


if __name__ == "__main__":

    main()
