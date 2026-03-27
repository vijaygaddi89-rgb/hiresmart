import os
import json
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
# ── Embedding model (runs locally, no API cost) ──────────────────────────
embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"}
)

# ── Text splitter config ──────────────────────────────────────────────────
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,       # each chunk = ~500 characters
    chunk_overlap=50,     # 50 char overlap so context doesn't get cut off
    separators=["\n\n", "\n", ".", " "]
)


def build_vector_store(resume_text: str, jd_text: str, user_id: int) -> FAISS:
    """
    Takes resume text + JD text, splits into chunks,
    embeds them, stores in FAISS. Returns the vector store.
    """
    # Wrap text in LangChain Document objects (metadata tracks the source)
    resume_doc = Document(
        page_content=resume_text,
        metadata={"source": "resume", "user_id": user_id}
    )
    jd_doc = Document(
        page_content=jd_text,
        metadata={"source": "job_description", "user_id": user_id}
    )

    # Split both documents into chunks
    resume_chunks = text_splitter.split_documents([resume_doc])
    jd_chunks = text_splitter.split_documents([jd_doc])

    all_chunks = resume_chunks + jd_chunks

    print(f"[RAG] Resume chunks: {len(resume_chunks)}")
    print(f"[RAG] JD chunks:     {len(jd_chunks)}")
    print(f"[RAG] Total chunks:  {len(all_chunks)}")

    # Build FAISS index from chunks
    vector_store = FAISS.from_documents(all_chunks, embeddings)
    return vector_store


def retrieve_context(vector_store: FAISS, query: str, k: int = 4) -> str:
    """
    Given a query string, finds the top-k most relevant chunks
    from the FAISS index. Returns them as a single combined string.
    """
    docs = vector_store.similarity_search(query, k=k)
    context = "\n\n---\n\n".join([doc.page_content for doc in docs])
    return context


def test_rag_pipeline(resume_text: str, jd_text: str, user_id: int = 1):
    """
    Quick test function — builds index, runs a sample query,
    prints retrieved context. Call this to verify setup works.
    """
    print("\n[RAG TEST] Building vector store...")
    vs = build_vector_store(resume_text, jd_text, user_id)

    print("\n[RAG TEST] Running similarity search...")
    query = "What are the candidate's main technical skills?"
    context = retrieve_context(vs, query)

    print(f"\n[RAG TEST] Query: {query}")
    print(f"\n[RAG TEST] Retrieved context:\n{context}")
    print("\n[RAG TEST] ✅ RAG pipeline working correctly!")
    return vs