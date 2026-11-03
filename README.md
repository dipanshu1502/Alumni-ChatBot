# Akal University Document Reader

A document question-answering assistant for Akal University PDFs. The project extracts text from PDFs, splits it into overlapping chunks, embeds those chunks, and searches them with FAISS. A Groq chat model answers questions using the retrieved document text and returns the source filenames.

## Project structure

```text
data/              Source PDF documents
frontend/          React + Vite chat interface
src/
  api.py           FastAPI endpoints for the React interface
  embeddings.py    Sentence Transformers embedding model
  pdf_loader.py   PDF text extraction
  chunking.py     Text chunking
  process_documents.py
  vector_store.py Builds the FAISS index and chunk metadata
  retriever.py    Finds relevant document chunks
  rag_pipeline.py Generates document-grounded answers
vector_db/         Generated FAISS index and chunk metadata
app.py             Streamlit chat interface
requirements.txt   Python dependencies
```

## Requirements

- Python with the packages listed in `requirements.txt`
- Node.js and npm for the React frontend
- A Groq API key and a model name

## Setup

From the project root, create and activate a Python virtual environment, then install the dependencies:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Create a `.env` file in the project root with your Groq credentials:

```dotenv
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=your_groq_model_name
```

Keep the API key private; do not commit `.env` to source control.

Install the frontend dependencies:

```powershell
Set-Location frontend
npm ci
Copy-Item .env.example .env
```

The frontend `.env` file can use the default API URL:

```dotenv
VITE_API_URL=http://127.0.0.1:8000
```

## Build or refresh the document index

PDFs in `data/` are used to create `vector_db/index.faiss` and `vector_db/chunks.pkl`. Rebuild the index after adding or changing documents. Run this from the project root so the relative `data/` and `vector_db/` paths resolve correctly:

```powershell
.\venv\Scripts\python.exe .\retrain.py
```

This rebuilds the PDF chunks, embeddings, and FAISS index. It refreshes the chatbot's document knowledge; it does not fine-tune the hosted Groq language model.

The embedding model `all-MiniLM-L6-v2` is downloaded by Sentence Transformers when first needed.
PDF match filtering uses cosine similarity. Set `PDF_MIN_SIMILARITY` in the root `.env` to tune the cutoff (valid range: `-1` to `1`; default: `0.35`). After changing the cutoff, compare representative questions and adjust based on missed or irrelevant matches.
Rebuild the vector store after this update to include PDF page numbers in source citations.

## Run the application

### React frontend with FastAPI

After completing setup, run `run.bat` from the project root to start the API and frontend in separate terminal windows. Open the Vite URL shown in the frontend terminal (normally `http://localhost:5173`).

You can also start each service manually:

Start the API from the project root:

```powershell
$env:PYTHONPATH = "$PWD\src"
.\venv\Scripts\python.exe -m uvicorn api:app --reload
```

The API is available at `http://127.0.0.1:8000`; its interactive documentation is at `http://127.0.0.1:8000/docs`.

In another terminal, start the frontend:

```powershell
Set-Location frontend
npm run dev
```

Open the Vite URL printed in the terminal (normally `http://localhost:5173`).

### Streamlit interface

Alternatively, run the Streamlit app from the project root:

```powershell
.\venv\Scripts\python.exe -m streamlit run app.py
```

## Hybrid AI architecture

The assistant now combines two sources:

- University PDF retrieval from the local `data/` documents and `vector_db/` index.
- Live, allowlisted public data from the CodeIgniter 4 API at `http://localhost:8080/api` when the endpoint is available. Supported data includes alumni, events, jobs, chapters, stories, news, gallery albums, donation campaigns, and approved aggregate statistics.

The chatbot routes questions to relevant API categories and searches all supported public categories when a question does not identify one. It also searches the PDF knowledge base for every question. Multi-category public API lookups run concurrently. Set `CI4_API_BASE_URL` in the root `.env` file when the website API is hosted somewhere other than the local default.

Only fields explicitly allowlisted by the chatbot are sent to the language model. It does not call authenticated/admin endpoints, the unsafe alumni-detail route, or unreviewed public settings. The public API must be running and return the data for it to be available in chat. Some API collections have no pagination, and public records not exposed by the documented API cannot be retrieved by the chatbot; add a reviewed public API route for those website sections rather than scraping the frontend or connecting the chatbot directly to MySQL.

## API

### `GET /`

Returns a message indicating that the API is running.

### `GET /health`

Reports Groq configuration and whether either the PDF index or live portal is available. `status` is `ok` when Groq is configured and at least one knowledge source is ready; otherwise it is `degraded`.

### `POST /chat`

Request:

```json
{
  "question": "How can I collect my DMC?"
}
```

Successful response:

```json
{
  "answer": "Answer based on the retrieved university documents.",
  "sources": ["document.pdf"]
}
```

The answer is generated from retrieved PDF content. If no relevant chunks are found, the API reports that it could not find relevant information in the documents.

## Troubleshooting

- **Frontend reports that the API is unavailable:** Start the FastAPI server and confirm that `VITE_API_URL` points to it.
- **No relevant information is found:** Confirm the PDFs are in `data/` and rebuild the FAISS index.
- **Missing Groq credentials:** Check that `GROQ_API_KEY` and `GROQ_MODEL` are set in the root `.env` file.
- **PyTorch or model-loading errors:** Embeddings rely on PyTorch through Sentence Transformers. On Windows, an incompatible or incomplete PyTorch runtime can prevent the model from loading; resolve that environment issue before indexing or answering questions.


Run Directly:
1.
$env:PYTHONPATH = "$PWD\src"
.\venv\Scripts\python.exe -m uvicorn api:app --reload

2.
Set-Location frontend
npm run dev
