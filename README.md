# Simple LLM App with Flask, ChromaDB, and Gemini API

## Project Structure

- `app.py`: Main Flask application with all endpoints and logic.
- `chroma_setup.py`: Handles ChromaDB vector store operations (add/query documents).
- `requirements.txt`: Python dependencies for the project.
- `Dockerfile`: Containerizes the Flask app for deployment.
- `docker-compose.yml`: Defines multi-container Docker applications (here, just the app).
- `instance/documents.db`: SQLite database for document metadata (auto-created).
- `test_app.py`: Unit tests for file upload, vector query, and Gemini API endpoints.
- `README.md`: Project documentation and usage instructions.
- `LLM_Specialist_Assignment_PanScience_Innovations.pdf`: Assignment brief (if present).

## Setup

1. Clone this repo and navigate to the folder.
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set your Gemini API key in the `.env` file:
   ```
   GEMINI_API_KEY=AIzaSyCdD4B8J5HA_nogQrxgZ9YMujEf9RFdW9M
   ```
4. (Optional): If your environment is not set up correctly after installing the packages from requirements.txt, you can extract the ".venv" (It contains a pre-configured Python virtual environment with all the necessary packages already installed.)

## Running the App

### Locally
```
python app.py
```

### With Docker
Build the Docker image:
```
docker build -t shor-flask-app .
```
Run the app:
```
docker run -p 5000:5000 shor-flask-app
```
Or use Docker Compose:
```
docker-compose up --build
```

## API Endpoints

### Add Document
- `POST /add`
- **Request JSON:**
  ```json
  { "text": "your text here" }
  ```
- **Response JSON:**
  ```json
  { "message": "Document added", "id": "<doc_id>" }
  ```

### Upload Document
- `POST /upload` (multipart/form-data)
- **Request:**
  - Form field: `file` (PDF, DOCX, or TXT)
- **Response JSON:**
  ```json
  { "message": "File uploaded and processed", "doc_id": "<doc_id>", "num_chunks": 3 }
  ```

### Query Similar Documents
- `POST /query`
- **Request JSON:**
  ```json
  { "text": "your query here" }
  ```
- **Response JSON:**
  ```json
  {
    "documents": [["Relevant chunk 1", "Relevant chunk 2"]],
    "ids": [["docid_0", "docid_1"]]
  }
  ```

### Generate with Gemini
- `POST /generate`
- **Request JSON:**
  ```json
  { "prompt": "your prompt here" }
  ```
- **Response JSON:**
  ```json
  { "response": "Gemini response text" }
  ```

### Retrieve Document Metadata
- `GET /metadata`
- **Response JSON:**
  ```json
  [
    {
      "doc_id": "<doc_id>",
      "filename": "example.pdf",
      "upload_time": "2024-05-01T12:34:56.789Z",
      "num_chunks": 3
    },
    ...
  ]
  ```

### RAG Query
- `POST /rag_query`
- **Request JSON:**
  ```json
  { "query": "your question", "doc_id": "<optional_doc_id>" }
  ```
- **Response JSON:**
  ```json
  {
    "answer": "...",
    "context": ["chunk1", "chunk2", ...]
  }
  ```

## Example Usage with curl.exe (Windows Command Prompt)

### Upload a Document
```sh
curl.exe -F "file=@yourfile.txt" http://localhost:5000/upload
```
- Replace `yourfile.txt` with the path to your document.
- The response will include a `doc_id`.

### RAG Query (Retrieval-Augmented Generation)
```sh
curl.exe -X POST http://localhost:5000/rag_query -H "Content-Type: application/json" -d "{\"query\": \"What is this document about?\", \"doc_id\": \"your-doc-id-here\"}"
```
- Replace `your-doc-id-here` with the `doc_id` from the upload response.
- Replace the query with your own question if desired.


## LLM Provider Configuration
- This app uses the Gemini API for LLM responses.
- Set your Gemini API key in a `.env` file as `GEMINI_API_KEY`.
- The app expects the environment variable to be available at runtime (see Docker and Compose examples above).

## Testing

Unit tests are provided in `test_app.py` for key endpoints:
- File upload (`/upload`)
- Vector store query (`/query`)
- Gemini API response generation (`/generate`)

To run all tests using `unittest`:
```
python -m unittest test_app.py
```
Or simply:
```
python test_app.py
```
