import sys
sys.path.append(".")

from services.rag_service import test_rag_pipeline

# Sample resume text (simulating a parsed resume)
resume_text = """
Vijay Gaddi — Software Engineer
Email: vijay@gmail.com | Phone: 9999999999

Experience:
5 years of Python development experience.
Built REST APIs using FastAPI and Flask.
Deployed applications on AWS using Docker and Kubernetes.
Worked with PostgreSQL, Redis, and MongoDB databases.
Experience with machine learning using scikit-learn and pandas.

Skills:
Python, FastAPI, Flask, Docker, AWS, PostgreSQL, Redis,
MongoDB, Git, LangChain, FAISS, REST APIs, JWT Authentication

Education:
B.Tech Computer Science — 2019
"""

# Sample job description
jd_text = """
Senior Backend Engineer — Fintech Startup

Requirements:
- 4+ years Python experience
- Strong FastAPI or Django REST framework
- Experience with microservices and Docker
- PostgreSQL and Redis knowledge required
- Familiarity with LLMs or AI integrations is a plus
- AWS deployment experience
- Strong understanding of JWT and OAuth2

Responsibilities:
- Design and build scalable REST APIs
- Maintain and improve existing backend services
- Collaborate with frontend and ML teams
"""

# Run the test
test_rag_pipeline(resume_text, jd_text, user_id=1)