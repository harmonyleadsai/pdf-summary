import json
import logging
from typing import List, Dict

from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

async def call_openai_summary_and_qa(text: str, questions: List[str]) -> Dict:
    max_chars = 2000_000
    short_text = text if len(text) < max_chars else text[:max_chars] + "\n\n[TRUNCATED]"

    system_prompt = (
        "You are a helpful assistant that summarizes PDF content and answers questions strictly using the provided PDF content. "
        "If the answer isn't present in the PDF, say 'Not found in document.' Keep answers concise."
    )

    prompt_parts = [
        "PDF CONTENT:",
        short_text,
        "",
        "TASK:",
        "1) Provide a short summary (3-6 sentences).",
        "2) Answer the following questions based only on the PDF content. "
        "If not present, respond 'Not found in document.'",
        "",
        "QUESTIONS:",
    ]

    # Append numbered questions
    for i, q in enumerate(json.loads(questions), start=1):
        prompt_parts.append(f"{i}. {q}")

    # Ask GPT to return a JSON response
    prompt_parts.append(
        "Generate a JSON response with two parts: "
        "1) 'summary' as text, "
        "2) 'qa' as an array of {question, answer} pairs."
    )

    user_prompt = "\n".join(prompt_parts)

    #print("user_prompt: ", user_prompt)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    resp = await client.chat.completions.create(
        model=settings.OPENAI_MODEL, messages = messages, temperature=0.0, max_tokens=2000,)

    content = resp.choices[0].message.content

    try:
        parsed = json.loads(content)   # Convert GPT string → dict
    except json.JSONDecodeError:
        logger.error("Failed to parse GPT response as JSON")
        parsed = {"summary": "", "qa": []}
    #print("ai content", content)
    return parsed
