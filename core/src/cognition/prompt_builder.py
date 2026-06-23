# core/src/cognition/prompt_builder.py

from .personas import PERSONAS


def build_prompt(context, question, intent="assistant"):

    environment = context["environment"]

    role = context["role"]

    mission = ", ".join(context["mission"])

    persona = PERSONAS.get(
        intent,
        PERSONAS["assistant"]
    )

    #
    # Specialist modes should NOT inherit
    # executive_assistant instructions.
    #

    if intent == "assistant":

        environment_section = f"""
Current Environment:
- OS Mode: {environment}
- Operational Role: {role}
- Mission Focus: {mission}
"""

    else:

        environment_section = f"""
Current Environment:
- OS Mode: {environment}
"""

    prompt = f"""
{persona}

{environment_section}

Capabilities:
{context['capabilities']}

System Information:
{context['system_info']}

Instructions:
- Follow the specialist persona above.
- Prioritize the user's request over environmental metadata.
- If the user requests code, provide code first.
- If the user requests a plan, provide actionable steps.
- If the user requests research, provide analysis and comparisons.
- Do not behave as an executive assistant unless the intent is assistant.

User Request:
{question}
"""

    return prompt
