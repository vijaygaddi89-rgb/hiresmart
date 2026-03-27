# backend/services/job_parser.py

import json
import os
import anthropic
from decouple import config

# Initialize Claude client once at module level
client = anthropic.Anthropic(api_key=config("ANTHROPIC_API_KEY"))

def extract_skills_from_jd(job_title: str, job_description: str) -> list[str]:
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

    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=500,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    # Extract text response
    response_text = message.content[0].text.strip()

    # Parse JSON array
    skills = json.loads(response_text)

    # Ensure it's a list of strings
    if not isinstance(skills, list):
        return []

    return [str(skill).lower().strip() for skill in skills]