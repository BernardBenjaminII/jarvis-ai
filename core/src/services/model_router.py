def choose_model(intent):
    if intent in ["status", "classification", "routing"]:
        return "tinyllama"

    if intent in ["coding", "linux", "git", "python"]:
        return "phi3"

    return "mistral"
