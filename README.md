# Industrial Knowledge Intelligence Platform

## Overview
The Industrial Knowledge Intelligence Platform is a comprehensive, AI-driven system designed to handle complex industrial compliance, Standard Operating Procedure (SOP) evaluations, and advanced technical querying. Built for industrial environments, it automates the ingestion, contextualization, and verification of dense safety manuals and regulations (such as OISD guidelines).

## Core Architecture and Features

### 1. Retrieval-Augmented Generation (RAG) Engine
The platform features a local vector database built on ChromaDB, which stores semantic embeddings of complex industrial documents. When a user queries the system, the RAG engine retrieves the most relevant context and synthesizes it using the Google Gemini generative model to produce concise, highly accurate answers backed by source citations.

### 2. Multi-format Document Ingestion and OCR
The backend includes a robust data pipeline capable of parsing text from standard digital formats (Markdown, Word Documents, readable PDFs) as well as utilizing Tesseract OCR to extract text from scanned documents and images.

### 3. Knowledge Graph Integration
The system employs Natural Language Processing (spaCy) for Named Entity Recognition. It intelligently parses texts to identify specific equipment tags (e.g., Pump P-101), regulations, and SOPs. These relationships are mapped into a Neo4j graph database, establishing a structured industrial knowledge graph.

### 4. Local NLP Compliance Agent
To circumvent potential LLM quota limitations and reduce latency, the system features a dedicated deterministic NLP Compliance Agent. When evaluating a user's proposed SOP, the agent uses regex and spaCy to dynamically extract numerical safety limits from the text. It then cross-references these limits against retrieved safety regulations from the database to flag non-compliance gaps and calculate exact variances locally.

### 5. Frontend Dashboard
A modern React and Vite based user interface featuring a sophisticated aesthetic. The application provides two main workflows: Knowledge Querying for searching the industrial database, and Compliance Checking for running an SOP gap analysis.

## Technology Stack
- Frontend: React.js, Vite, Vanilla CSS
- Backend: FastAPI, Python
- AI and NLP: LangChain, Google Gemini API, HuggingFace Embeddings (all-MiniLM-L6-v2), spaCy
- Databases: ChromaDB (Vector Search), Neo4j (Graph Database)
- Document Processing: PyMuPDF, PyTesseract

## Setup Instructions

### Prerequisites
- Python 3.10 or higher
- Node.js and npm
- Tesseract OCR installed on the host machine
- An active Neo4j Aura database instance (or local Neo4j)

### Environment Setup
Create a `.env` file in the root directory. Note that the `.env` file is included in `.gitignore` to prevent sensitive credentials from being uploaded to source control.

Populate the `.env` file with the following variables:
OPENAI_API_KEY=your_openai_key_here
GOOGLE_API_KEY=your_gemini_key_here
NEO4J_URI=bolt://your-neo4j-uri:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password

### Backend Execution
1. Create a virtual environment: `python -m venv venv`
2. Activate the virtual environment: `.\venv\Scripts\Activate` (Windows)
3. Install dependencies: `pip install -r requirements.txt`
4. Download the spaCy model: `python -m spacy download en_core_web_lg`
5. Start the backend server: `uvicorn main:app --host 0.0.0.0 --port 8080 --reload`

### Frontend Execution
1. Navigate to the frontend directory: `cd frontend`
2. Install dependencies: `npm install`
3. Start the development server: `npm run dev`

### Data Ingestion
To populate the local ChromaDB and Neo4j graph database:
1. Place source documents inside the `data/` directory.
2. Run the ingestion script: `python ingest.py`
3. Run the entity extraction script: `python extract_entities.py`
