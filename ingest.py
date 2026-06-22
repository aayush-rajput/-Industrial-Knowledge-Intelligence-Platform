import os
# pyrefly: ignore [missing-import]
import fitz  # PyMuPDF
import pytesseract  # pyrefly: ignore
from PIL import Image  # pyrefly: ignore
import io
from docx import Document  # pyrefly: ignore
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter  # pyrefly: ignore
from langchain_huggingface import HuggingFaceEmbeddings  # pyrefly: ignore
from langchain_community.vectorstores import Chroma  # pyrefly: ignore
from dotenv import load_dotenv

load_dotenv()

# Uncomment and adjust path if Tesseract is not in your system PATH
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text_from_pdf(pdf_path: str) -> str:
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            page_text = str(page.get_text())
            if not page_text.strip():
                # Fallback to OCR if page has no text
                try:
                    pix = page.get_pixmap()
                    img = Image.open(io.BytesIO(pix.tobytes()))
                    page_text = str(pytesseract.image_to_string(img))
                except Exception as ocr_e:
                    print(f"OCR skipped for a page: {ocr_e}")
                    page_text = ""
            text += page_text + "\n"
    return text

def extract_text_from_docx(docx_path: str) -> str:
    doc = Document(docx_path)
    return "\n".join([para.text for para in doc.paragraphs])

def ingest_document(file_path: str) -> str:
    ext = Path(file_path).suffix.lower()
    if ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif ext == '.docx':
        return extract_text_from_docx(file_path)
    elif ext in ['.txt', '.md']:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        raise ValueError(f"Unsupported file format: {ext}")

def process_and_store_documents(data_dir: str):
    docs = []
    metadata = []
    
    print(f"Scanning directory: {data_dir}")
    for file_name in os.listdir(data_dir):
        file_path = os.path.join(data_dir, file_name)
        if os.path.isfile(file_path):
            print(f"Processing {file_name}...")
            try:
                text = ingest_document(file_path)
                docs.append(text)
                metadata.append({"source": file_name})
            except Exception as e:
                print(f"Failed to process {file_name}: {e}")
                
    if not docs:
        print("No documents found to process.")
        return

    print("Chunking documents...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=512,
        chunk_overlap=64,
        length_function=len
    )
    
    chunks = text_splitter.create_documents(docs, metadatas=metadata)
    
    print(f"Created {len(chunks)} chunks. Embedding and storing in ChromaDB...")
    
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # Use local persistent Chroma client instead of Docker container
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory="./chroma_data"
    )
    print("Ingestion and Vector Storage complete!")

if __name__ == "__main__":
    data_dir = "data"
    os.makedirs(data_dir, exist_ok=True)
    if not os.listdir(data_dir):
         print(f"Please add some sample PDFs or DOCX files to the '{data_dir}' directory before running.")
    else:
         process_and_store_documents(data_dir)
