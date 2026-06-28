from core.src.brain import route_question

questions = [
    "List the runtime directory",
    "Does the knowledge directory exist?",
    "How much free space is on the runtime drive?",
]

for q in questions:
    print("=" * 60)
    print("QUESTION:", q)
    print(route_question(q))
