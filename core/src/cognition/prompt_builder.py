def build_prompt(context, question):

    environment = context["environment"]

    role = context["role"]

    mission = ", ".join(context["mission"])

    prompt = f"""
You are JARVIS.

Current Environment:
- OS Mode: {environment}
- Operational Role: {role}
- Mission Focus: {mission}

Capabilities:
{context['capabilities']}

System Information:
{context['system_info']}

User Request:
{question}
"""

    return prompt
