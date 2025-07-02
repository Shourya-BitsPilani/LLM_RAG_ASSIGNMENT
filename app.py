from flask import Flask, request, jsonify, render_template_string
from chroma_setup import add_document, query_similar
import os, uuid, requests
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import PyPDF2, docx, chardet
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

app = Flask(__name__)

DATABASE_URL = 'sqlite:///instance/documents.db'
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

class Document(Base):
    __tablename__ = 'documents'
    doc_id = Column(String, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    upload_time = Column(DateTime, nullable=False)
    num_chunks = Column(Integer, nullable=False)

Base.metadata.create_all(bind=engine)

def extract_text(file_path, ext):
    if ext == "pdf":
        with open(file_path, "rb") as f:
            return "".join(page.extract_text() or "" for page in PyPDF2.PdfReader(f).pages)
    elif ext in ["docx", "doc"]:
        return "\n".join(para.text for para in docx.Document(file_path).paragraphs)
    elif ext == "txt":
        with open(file_path, "rb") as f:
            raw = f.read()
            encoding = chardet.detect(raw)["encoding"] or "utf-8"
            return raw.decode(encoding)
    return None

def chunk_text(text, chunk_size=200):
    words = text.split()
    return [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]

UPLOAD_FORM_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Upload Document</title>
</head>
<body>
    <h2>Upload a Document (PDF, DOCX, TXT)</h2>
    <form action="/upload" method="post" enctype="multipart/form-data">
        <input type="file" name="file" required>
        <button type="submit">Upload</button>
    </form>
</body>
</html>
'''

@app.route("/", methods=["GET"])
def upload_form():
    return render_template_string(UPLOAD_FORM_HTML)

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    if not file or not getattr(file, "filename", None):
        return jsonify({"error": "No file selected"}), 400
    filename = secure_filename(file.filename or "uploaded_file")
    ext = filename.rsplit(".", 1)[-1].lower()
    temp_path = f"temp_{uuid.uuid4()}_{filename}"
    file.save(temp_path)
    try:
        text = extract_text(temp_path, ext)
        if text is None:
            return jsonify({"error": "Unsupported file type"}), 400
        chunks = chunk_text(text)
        doc_id = str(uuid.uuid4())
        for i, chunk in enumerate(chunks):
            add_document(f"{doc_id}_{i}", chunk)
        with SessionLocal() as db:
            db.add(Document(doc_id=doc_id, filename=filename, upload_time=datetime.utcnow(), num_chunks=len(chunks)))
            db.commit()
        return jsonify({"message": "File uploaded and processed", "doc_id": doc_id, "num_chunks": len(chunks)})
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.route("/metadata", methods=["GET"])
def metadata():
    with SessionLocal() as db:
        docs = db.query(Document).all()
        result = [
            {
                "doc_id": d.doc_id,
                "filename": d.filename,
                "upload_time": d.upload_time.isoformat(),
                "num_chunks": d.num_chunks
            }
            for d in docs
        ]
    return jsonify(result)

@app.route("/add", methods=["POST"])
def add():
    text = (request.json or {}).get("text")
    if not text:
        return jsonify({"error": "No text provided"}), 400
    doc_id = str(uuid.uuid4())
    add_document(doc_id, text)
    return jsonify({"message": "Document added", "id": doc_id})

@app.route("/query", methods=["POST"])
def query():
    text = (request.json or {}).get("text")
    if not text:
        return jsonify({"error": "No text provided"}), 400
    results = query_similar(text)
    return jsonify(results)

@app.route("/generate", methods=["POST"])
def generate():
    prompt = (request.json or {}).get("prompt")
    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    response = requests.post(GEMINI_API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        result = response.json()
        try:
            text = result["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            text = result
        return jsonify({"response": text})
    else:
        return jsonify({"error": "Gemini API error", "details": response.text}), 500

@app.route("/rag_query", methods=["POST"])
def rag_query():
    data = request.json or {}
    query = data.get("query")
    doc_id = data.get("doc_id")
    if not query:
        return jsonify({"error": "No query provided"}), 400
    n_results = 5
    if doc_id:
        results = query_similar(query, n_results=20) or {}
        ids = results.get('ids', [[]])
        docs = results.get('documents', [[]])
        filtered = []
        for i, id_ in enumerate(ids[0] if ids and ids[0] else []):
            if id_.startswith(doc_id):
                filtered.append((id_, docs[0][i] if docs and docs[0] else ""))
            if len(filtered) >= n_results:
                break
        context_chunks = [chunk for _, chunk in filtered]
    else:
        results = query_similar(query, n_results=n_results) or {}
        docs = results.get('documents', [[]])
        context_chunks = docs[0] if docs and docs[0] else []
    if not context_chunks:
        return jsonify({"error": "No relevant context found"}), 404
    context = "\n".join(context_chunks)
    prompt = f"Answer the following question based on the provided context.\nContext:\n{context}\n\nQuestion: {query}"
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    response = requests.post(GEMINI_API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        result = response.json()
        try:
            answer = result["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            answer = result
        return jsonify({"answer": answer, "context": context_chunks})
    else:
        return jsonify({"error": "Gemini API error", "details": response.text}), 500

if __name__ == "__main__":
    app.run(debug=True) 