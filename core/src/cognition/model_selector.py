def select_model(context, intent):

    ram = context["system_info"]["ram_gb"]

    environment = context["environment"]

    if ram < 8:
        return "tinyllama"

    if environment == "ubuntu":
        return "phi3"

    if environment == "kali":
        return "mistral"

    return "mistral"
