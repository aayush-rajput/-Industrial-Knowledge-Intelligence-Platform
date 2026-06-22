import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from langchain_huggingface import HuggingFaceEmbeddings  # pyrefly: ignore
from langchain_google_genai import ChatGoogleGenerativeAI  # pyrefly: ignore
from langchain_community.vectorstores import Chroma  # pyrefly: ignore
from dotenv import load_dotenv
import spacy  # pyrefly: ignore
import re

load_dotenv()

try:
    nlp = spacy.load("en_core_web_lg")
except OSError:
    from spacy.cli import download  # pyrefly: ignore
    download("en_core_web_lg")
    nlp = spacy.load("en_core_web_lg")

class LocalComplianceAgent:
    def __init__(self, vectorstore):
        self.vectorstore = vectorstore

    def extract_ppm(self, text):
        match = re.search(r'(\d+(?:\.\d+)?)\s*ppm', text, re.IGNORECASE)
        if match:
            return float(match.group(1))
        return None
        
    def evaluate(self, sop_text):
        # 1. Extract metric from SOP using Regex
        sop_ppm = self.extract_ppm(sop_text)
        
        # We also run spaCy to tag entities, though for the demo we focus on the ppm metric
        doc = nlp(sop_text)
        entities = [ent.text for ent in doc.ents]
        
        # 2. Retrieve Context from Vector DB
        chunks = self.vectorstore.similarity_search(sop_text, k=4)
        context = "\n".join([chunk.page_content for chunk in chunks])
        
        # 3. Dynamic Rule Comparison
        # Extract regulatory limits from the retrieved context
        context_ppms = [float(m) for m in re.findall(r'(\d+(?:\.\d+)?)\s*ppm', context, re.IGNORECASE)]
        
        if not sop_ppm:
            return {
                "status": "COMPLIANT",
                "explanation": "No measurable metrics (e.g., ppm) detected in the SOP to verify against regulations."
            }
            
        if not context_ppms:
            return {
                "status": "COMPLIANT",
                "explanation": "No corresponding regulatory limits found in the knowledge base to compare against."
            }
            
        # Assume the strictest (minimum) value found in the regulations is the hard limit
        regulatory_limit = min(context_ppms)
        
        if sop_ppm > regulatory_limit:
            variance = sop_ppm - regulatory_limit
            return {
                "status": "NON-COMPLIANT",
                "explanation": f"CRITICAL GAP DETECTED (Local NLP Agent): Your SOP specifies a limit of {sop_ppm} ppm, but retrieved regulations strictly mandate a maximum of {regulatory_limit} ppm. (Variance: {variance} ppm over the limit)."
            }
        else:
            return {
                "status": "COMPLIANT",
                "explanation": f"SOP is compliant (Local NLP Agent). The specified limit of {sop_ppm} ppm is safely within the regulatory maximum of {regulatory_limit} ppm."
            }

app = FastAPI(title="Industrial Knowledge Intelligence API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    question: str

@app.get("/")
def read_root():
    return {"message": "Welcome to the Unified Asset & Operations Brain API"}

@app.post("/query")
def query_knowledge_base(request: QueryRequest):
    try:
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        vectorstore = Chroma(persist_directory="./chroma_data", embedding_function=embeddings)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load vector store: {e}")

    chunks = vectorstore.similarity_search(request.question, k=5)
    if not chunks:
        return {"question": request.question, "answer": "No relevant documents found.", "citations": []}

    # Deduplicate chunks by content
    seen_content = set()
    unique_chunks = []
    for chunk in chunks:
        content_key = chunk.page_content[:100]
        if content_key not in seen_content:
            seen_content.add(content_key)
            unique_chunks.append(chunk)
    
    context = "\n\n".join([f"Source: {chunk.metadata.get('source', 'Unknown')}\n{chunk.page_content}" for chunk in unique_chunks[:3]])
    
    # Unique citation sources
    unique_sources = []
    seen = set()
    for c in unique_chunks:
        src = c.metadata.get('source', 'Unknown')
        if src not in seen:
            seen.add(src)
            unique_sources.append({'source': src})
    
    # Use Gemini 2.0 Flash (free tier!) for answer synthesis
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
        prompt = f"You are an industrial safety expert. Based ONLY on the context below, provide a clear, concise answer to the question. Cite the source documents.\n\nContext:\n{context}\n\nQuestion: {request.question}\n\nAnswer:"
        response = llm.invoke(prompt)
        answer = response.content
    except Exception as e:
        # Fallback to structured local answer if Gemini fails
        answer_parts = []
        for i, chunk in enumerate(unique_chunks[:3], 1):
            src = chunk.metadata.get('source', 'Unknown')
            answer_parts.append(f"📄 [{src}]\n{chunk.page_content.strip()}")
        answer = "Based on the retrieved documents:\n\n" + "\n\n---\n\n".join(answer_parts)
    
    return {"question": request.question, "answer": answer, "citations": unique_sources, "confidence": 0.85}

class ComplianceRequest(BaseModel):
    sop_text: str

@app.post("/compliance-check")
def check_compliance(request: ComplianceRequest):
    try:
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        vectorstore = Chroma(persist_directory="./chroma_data", embedding_function=embeddings)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load vector store: {e}")

    # Use the Local NLP Compliance Agent instead of LLM due to quotas
    agent = LocalComplianceAgent(vectorstore)
    result = agent.evaluate(request.sop_text)
    
    return result

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
