from anthropic import AsyncAnthropic
from services.rag_service import build_vector_store, retrieve_context
from decouple import config

client = AsyncAnthropic(api_key=config("ANTHROPIC_API_KEY"))

async def generate_interview_questions(resume_text: str, job_description: str) -> list[str]:
    # Step 1: Build FAISS vector store from resume + JD
    vector_store = build_vector_store(resume_text, job_description, user_id=1)

    # Step 2: Retrieve relevant context for both angles
    resume_context = retrieve_context(vector_store, "candidate skills experience projects")
    jd_context = retrieve_context(vector_store, "job requirements responsibilities qualifications")

    # Step 3: Build prompt for Claude
    prompt = f"""You are an expert technical interviewer.

Based on the candidate's resume and job description below, generate exactly 8 personalized interview questions.

RESUME CONTEXT:
{resume_context}

JOB DESCRIPTION CONTEXT:
{jd_context}

Rules:
- Questions must be specific to the candidate's actual experience
- Mix of technical, behavioral, and situational questions
- Number each question (1. 2. 3. etc.)
- No generic questions like "Tell me about yourself"
- Return ONLY the numbered questions, nothing else

Generate 8 interview questions:"""

    # Step 4: Call Claude
    response = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    # Step 5: Parse response into list
    raw = response.content[0].text
    questions = []
    for line in raw.strip().split('\n'):
        line = line.strip()
        if line and line[0].isdigit():
            question = line.split('.', 1)[-1].strip()
            question = question.split(')', 1)[-1].strip()
            questions.append(question)

    return questions