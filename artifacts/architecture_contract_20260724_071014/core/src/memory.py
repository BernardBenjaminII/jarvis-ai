memory_store = []

def save_interaction(question: str, response: str):
    memory_store.append({
        "question": question,
        "response": response
    })

def get_recent_context(limit: int = 3):
    return memory_store[-limit:]
