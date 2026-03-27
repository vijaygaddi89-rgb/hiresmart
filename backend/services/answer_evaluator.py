from anthropic import AsyncAnthropic
from decouple import config

client = AsyncAnthropic(api_key=config("ANTHROPIC_API_KEY"))

async def evaluate_answer(
    question: str,
    answer: str,
    resume_text: str,
    job_description: str
) -> dict:

    prompt = f"""You are an expert interview coach evaluating a candidate's answer.

QUESTION ASKED:
{question}

CANDIDATE'S ANSWER:
{answer}

CANDIDATE'S RESUME CONTEXT:
{resume_text[:1000]}

JOB DESCRIPTION CONTEXT:
{job_description[:500]}

Evaluate the answer and respond in this EXACT format with no extra text before or after:
SCORE: [number 1-10]
STRENGTHS: [what the candidate did well — keep to one paragraph]
IMPROVEMENTS: [what was missing or could be better — keep to one paragraph]
IDEAL_ANSWER: [a strong sample answer — keep to one paragraph]

Be specific, honest, and constructive. Each section must be on a single line."""

    response = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text.strip()

    # Default values
    result = {
        "score": 5,
        "strengths": "",
        "improvements": "",
        "ideal_answer": ""
    }

    # Robust multi-line parser
    current_key = None
    buffer = []

    for line in raw.split('\n'):
        line = line.strip()
        if not line:
            continue

        if line.startswith("SCORE:"):
            try:
                result["score"] = int(line.replace("SCORE:", "").strip())
            except:
                result["score"] = 5
            current_key = None

        elif line.startswith("STRENGTHS:"):
            if current_key and buffer:
                result[current_key] = " ".join(buffer).strip()
            current_key = "strengths"
            buffer = [line.replace("STRENGTHS:", "").strip()]

        elif line.startswith("IMPROVEMENTS:"):
            if current_key and buffer:
                result[current_key] = " ".join(buffer).strip()
            current_key = "improvements"
            buffer = [line.replace("IMPROVEMENTS:", "").strip()]

        elif line.startswith("IDEAL_ANSWER:"):
            if current_key and buffer:
                result[current_key] = " ".join(buffer).strip()
            current_key = "ideal_answer"
            buffer = [line.replace("IDEAL_ANSWER:", "").strip()]

        else:
            # continuation of current section
            if current_key:
                buffer.append(line)

    # flush last section
    if current_key and buffer:
        result[current_key] = " ".join(buffer).strip()

    return result