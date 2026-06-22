import spacy  # pyrefly: ignore
from langchain_community.vectorstores import Chroma  # pyrefly: ignore
from langchain_huggingface import HuggingFaceEmbeddings  # pyrefly: ignore
import re
from neo4j import GraphDatabase
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

try:
    nlp = spacy.load("en_core_web_lg")
except OSError:
    print("Downloading spaCy model 'en_core_web_lg'...")
    from spacy.cli import download  # pyrefly: ignore
    download("en_core_web_lg")
    nlp = spacy.load("en_core_web_lg")

# Add EntityRuler for specific industrial formats
ruler = nlp.add_pipe("entity_ruler", before="ner")
patterns = [
    {"label": "EQUIPMENT", "pattern": [{"TEXT": {"REGEX": "^[A-Z]-[0-9]{3,}$"}}]},
    {"label": "REGULATION", "pattern": [{"TEXT": {"REGEX": "^OISD-[0-9]{3}$"}}]},
    {"label": "SOP", "pattern": [{"TEXT": {"REGEX": "^SOP-.*$"}}]},
]
ruler.add_patterns(patterns)  # pyrefly: ignore

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

class KnowledgeGraphBuilder:
    def __init__(self, uri, user, password):
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            self.driver.verify_connectivity()
            self.connected = True
            print("Connected to Neo4j successfully.")
        except Exception as e:
            print(f"\n[!] Could not connect to Neo4j. Check credentials or Aura Free connection string.\nError: {e}\n")
            self.driver: Optional[GraphDatabase] = None  # pyrefly: ignore
            self.connected = False

    def close(self):
        if self.driver:
            self.driver.close()
            
    def init_schema(self):
        if not self.connected: return
        with self.driver.session() as session:
            # Create constraints/indexes based on Section 4.3 Schema
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (e:Equipment) REQUIRE e.tag_id IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (s:SOP) REQUIRE s.sop_id IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (r:Regulation) REQUIRE r.reg_id IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (d:Document) REQUIRE d.doc_id IS UNIQUE")

    def add_entity_relations(self, doc_name, equipment_tags, regulations, sops):
        if not self.connected: return
        with self.driver.session() as session:
            session.run("MERGE (d:Document {doc_id: $doc_id})", doc_id=doc_name)
            
            for eq in equipment_tags:
                session.run("MERGE (e:Equipment {tag_id: $tag}) "
                            "MERGE (d:Document {doc_id: $doc_id}) "
                            "MERGE (d)-[:REFERENCES]->(e)", tag=eq, doc_id=doc_name)
            for reg in regulations:
                session.run("MERGE (r:Regulation {reg_id: $reg}) "
                            "MERGE (d:Document {doc_id: $doc_id}) "
                            "MERGE (d)-[:REFERENCES]->(r)", reg=reg, doc_id=doc_name)
            for sop in sops:
                session.run("MERGE (s:SOP {sop_id: $sop}) "
                            "MERGE (d:Document {doc_id: $doc_id}) "
                            "MERGE (d)-[:REFERENCES]->(s)", sop=sop, doc_id=doc_name)

def extract_and_seed():
    print("Loading local Chroma vectorstore...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = Chroma(persist_directory="./chroma_data", embedding_function=embeddings)
    
    results = vectorstore.get()
    documents = results.get("documents", [])
    metadatas = results.get("metadatas", [])
    
    kg = KnowledgeGraphBuilder(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    kg.init_schema()

    print(f"Processing {len(documents)} chunks for entities...")
    for doc_text, meta in zip(documents, metadatas):
        doc_source = meta.get("source", "Unknown")
        
        doc = nlp(doc_text)
        equipment, regulations, sops = set(), set(), set()
        
        # Regex fallback for strict industrial identifiers
        for match in re.finditer(r'\b[A-Z]-\d{3,}\b', doc_text):
            equipment.add(match.group())
        for match in re.finditer(r'\bOISD-\d{3}\b', doc_text):
            regulations.add(match.group())
        for match in re.finditer(r'\bSOP-[A-Z]+-\d{2,}\b', doc_text):
            sops.add(match.group())
            
        for ent in doc.ents:
            if ent.label_ == "EQUIPMENT": equipment.add(ent.text)
            if ent.label_ == "REGULATION": regulations.add(ent.text)
            if ent.label_ == "SOP": sops.add(ent.text)
            
        if equipment or regulations or sops:
            print(f"[{doc_source}] Found -> EQ: {equipment}, REG: {regulations}, SOP: {sops}")
            kg.add_entity_relations(doc_source, equipment, regulations, sops)

    kg.close()
    if not kg.connected:
        print("\nEntities were extracted locally, but NOT saved to Neo4j. Please configure NEO4J_URI in your .env file.")
    else:
        print("\nExtraction and Neo4j KG Seeding complete!")

if __name__ == "__main__":
    extract_and_seed()
