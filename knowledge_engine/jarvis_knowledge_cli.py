from __future__ import annotations

import argparse

from knowledge_engine.director.knowledge_director import KnowledgeDirector
from knowledge_engine.director.models import DirectorRequest
from knowledge_engine.director.router.intent_router import IntentRouter


def main() -> int:

    parser = argparse.ArgumentParser(
        description="JARVIS Knowledge natural command interface."
    )

    parser.add_argument(
        "text",
        nargs="*",
        help="Natural language request.",
    )

    parser.add_argument("--source", default="")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--show-route", action="store_true")

    args = parser.parse_args()

    user_text = " ".join(args.text).strip()

    routed = IntentRouter().route(
        user_text,
        source_path=args.source or None,
        limit=args.limit,
    )

    if args.show_route:

        print()
        print("=" * 70)
        print("INTENT ROUTER")
        print("=" * 70)
        print(f"Input      : {user_text}")
        print(f"Intent     : {routed.intent}")
        print(f"Confidence : {routed.confidence:.2f}")
        print(f"Reason     : {routed.reason}")
        print(f"Query      : {routed.query}")
        print(f"Source     : {routed.source_path}")

    if routed.intent == "unknown":

        print("Unable to determine intent.")

        return 1

    response = KnowledgeDirector().handle(

        DirectorRequest(

            intent=routed.intent,

            source_path=routed.source_path,

            query=routed.query,

            metadata=routed.metadata,

        )

    )

    print()
    print("=" * 70)
    print("JARVIS KNOWLEDGE")
    print("=" * 70)

    print(f"Intent   : {response.intent}")
    print(f"Workflow : {response.workflow}")
    print(f"Passed   : {response.passed}")
    print(f"Message  : {response.message}")

    metadata = response.metadata or {}

    results = metadata.get("results", [])

    if metadata:

        print()
        print("Metadata")
        print("-" * 70)

        for key, value in metadata.items():

            if key == "results":
                continue

            print(f"{key}: {value}")

    if results:

        print()
        print("Results")
        print("-" * 70)

        for index, item in enumerate(results, start=1):

            #
            # Production SearchResult dataclass
            #

            if hasattr(item, "score"):

                score = item.score
                file_path = item.file_path
                chunk_index = item.chunk_index
                text = item.text
                quality = item.quality.score

            #
            # Dictionary fallback
            #

            elif isinstance(item, dict):

                score = item.get("score", 0)
                file_path = item.get("file_path", "")
                chunk_index = item.get("chunk_index", "")
                text = item.get("text_preview", "")
                quality = item.get("quality", 0)

            #
            # Legacy tuple fallback
            #

            else:

                score, file_path, chunk_index, text, report = item
                quality = report.score

            print(f"{index}. Score   : {float(score):.4f}")
            print(f"   Quality : {quality}")
            print(f"   File    : {file_path}")
            print(f"   Chunk   : {chunk_index}")
            print()
            print(str(text)[:500])
            print()

    if response.errors:

        print()
        print("Errors")
        print("-" * 70)

        for error in response.errors:

            print(error)

    return 0 if response.passed else 1


if __name__ == "__main__":

    raise SystemExit(main())
