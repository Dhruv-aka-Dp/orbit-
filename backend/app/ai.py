"""Narrow, read-only AI drafting service.

The model receives only the caller's submitted goal and returns a draft. It has no
database, shell, HTTP, or outbound-action tools, so it cannot mutate workspace data.
"""
import os
from openai import AsyncOpenAI
from .config import get_settings

SYSTEM_INSTRUCTIONS = """You draft an execution plan for a productivity product.
Return concise Markdown with: assumptions, milestones, tasks, risks, and questions.
Do not claim work is complete. Do not issue commands or make external commitments.
This is a draft for a user to review, never an instruction to change records."""


async def draft_plan(goal: str, capacity_hours: float | None) -> tuple[str, str]:
    settings = get_settings()
    if not settings.openai_model or not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("AI model or OPENAI_API_KEY is not configured")
    prompt = f"Goal:\n{goal}\n\nAvailable weekly capacity: {capacity_hours if capacity_hours is not None else 'not provided'} hours."
    client = AsyncOpenAI()
    response = await client.responses.create(
        model=settings.openai_model,
        instructions=SYSTEM_INSTRUCTIONS,
        input=prompt,
        store=False,
    )
    return response.output_text, response.id
