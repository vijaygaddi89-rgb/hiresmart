# backend/services/job_parser.py

import json
from anthropic import AsyncAnthropic
from decouple import config

# Async client for FastAPI compatibility
client = AsyncAnthropic(api_key=config("ANTHROPIC_API_KEY"))

async def extract_skills_from_jd(job_title: str, job_description: str) -> list[str]:
    """
    Use Claude to extract required skills from a job description.
    Returns a clean list of skill strings.
    """

    prompt = f"""You are an expert technical recruiter. Analyze the job description below and extract ALL required and preferred technical skills.

Job Title: {job_title}

Job Description:
{job_description}

Return ONLY a JSON array of skills. No explanation, no markdown, no extra text.
Example format: ["python", "fastapi", "postgresql", "docker", "aws"]

Rules:
- Lowercase all skills
- Include programming languages, frameworks, tools, platforms, methodologies
- Be specific (e.g. "pytorch" not just "deep learning frameworks")
- Include soft skills only if explicitly mentioned as requirements
- Max 30 skills

Return only the JSON array:"""

    message = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    response_text = message.content[0].text.strip()

    # Clean markdown if Claude wraps in backticks
    if response_text.startswith("```"):
        response_text = response_text.split("```")[1]
        if response_text.startswith("json"):
            response_text = response_text[4:]
    
    skills = json.loads(response_text)

    if not isinstance(skills, list):
        return []

    return [str(skill).lower().strip() for skill in skills]