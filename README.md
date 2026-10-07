# TenderMind API & Pipeline (FastAPI + Local AI)

TenderMind is an AI-powered co-pilot for government procurement, now optimized for **local offline inference**.

## 🚀 Key Features
- **Local AI Orchestration**: Uses **FLAN-T5** for criteria extraction and evaluation (No API keys required).
- **ML Confidence Scoring**: uses **RandomForest** and **IsolationForest** (Scikit-learn) for verdict validation and anomaly detection.
- **Multilingual Support**: Local Hindi-to-English translation using Helsinki-NLP models.
- **Full Stack**: FastAPI, PostgreSQL, Celery, Redis, and React.

---

## 🚀 1. Quick Start (Docker)

1. **Prerequisites**: [Install Docker Desktop](https://docs.docker.com/get-docker/)
2. **Setup**: Run `setup.bat` (This will create your `.env` and verify Docker).
3. **Run**:
   ```bash
   docker-compose up -d
   ```

**Services available**:
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/api/docs
- **Flower (Monitoring)**: http://localhost:5555

> **Note**: On the first run, the system will download the local models (several GBs). Monitor progress with `docker-compose logs -f celery-worker`.

---

## 🛠️ 2. Technology Stack

- **AI Model**: `google/flan-t5-base` (Running locally via Transformers)
- **Embeddings**: `all-MiniLM-L6-v2` (Sentence-Transformers)
- **ML Logic**: Scikit-learn (RandomForestRegressor, IsolationForest)
- **OCR**: Tesseract (Local)
- **Backend**: FastAPI | PostgreSQL | Celery | Redis
- **Frontend**: React (Vite + Tailwind)

---

## 🧪 3. Pipeline Workflow

1. **Tender Ingestion**: Upload a tender PDF. The local AI extracts eligibility criteria.
2. **Bidder Evaluation**: Upload bidder documents. The system uses semantic search to find evidence and FLAN-T5 to verify compliance.
3. **ML Scoring**: A Random Forest model predicts the confidence of the AI's verdict, and an Isolation Forest flags any anomalous results for human review.
4. **Scorecard**: View the final ranked matrix of bidders.

---

## ⚠️ Important Notes
- **Hardware**: Local AI processing is CPU/RAM intensive. Ensure your Docker Desktop has at least 8GB RAM allocated.
- **Tesseract**: Scanned documents require Tesseract OCR. This is pre-installed in the Docker image.

<<<<<<< HEAD
## TEAM MEMBERS
=======
A virtual environment has been created for you. To activate it and ensure all dependencies are installed, open a terminal in the `backend/` folder:

```powershell
cd c:\Coding\AI4BHARAT\backend
venv\Scripts\activate
pip install -r requirements.txt
```

*Note: The system automatically installed this for you just now, but use this command to add new packages in the future.*

---

## 🏃 4. Running the Application Natively

You need **two** separate terminal windows to run the stack.

### Terminal 1: Start the FastAPI Server
This runs the main API that accepts uploads and serves the frontend.

```powershell
cd c:\Coding\AI4BHARAT\backend
venv\Scripts\activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
*(The first time you run this, it will automatically connect to your PostgreSQL database and create all necessary tables!)*

### Terminal 2: Start the Celery Worker
This background worker processes the heavy OCR and AI extraction tasks. Because you are on Windows, we must run Celery with the `--pool=solo` flag.

```powershell
cd c:\Coding\AI4BHARAT\backend
venv\Scripts\activate
celery -A workers.tasks worker --loglevel=info --pool=solo
```

---

## ✅ 5. Verify the System

1. **Deep Health Check:** Open [http://localhost:8000/health](http://localhost:8000/health)
   *(Should return `{"api":"ok","db":"ok","redis":"ok"}`. This confirms your Database and Redis connections are working!)*
2. **API Docs:** Open [http://localhost:8000/docs](http://localhost:8000/docs) to see your endpoints and test them.

---

## 🧪 How to Test the Pipeline

### Step 1: Upload a Tender
Using the Swagger UI at `http://localhost:8000/docs`, find the `POST /api/upload/tender` endpoint and upload a PDF. 
- Watch **Terminal 2** (Celery worker). You will see it ingest the document and call Gemini to extract criteria.

### Step 2: Upload Bidder Documents
Find the `POST /api/upload/bidder` endpoint. Enter the `tender_id` returned from Step 1, a `vendor_name`, and upload bidder PDFs.
- Watch **Terminal 2**. The worker will evaluate the bidder against the criteria.

### Step 3: View the Scorecard
Go to `GET /api/tenders/{id}/scorecard` and execute it. You will see a fully ranked compliance scorecard.

---

## ⚠️ Troubleshooting

- **Database SSL Error**: If you get a connection error about SSL, append `?sslmode=require` to your `DATABASE_URL`.
- **Tesseract Error**: If the Celery worker crashes when processing a scanned PDF, saying `tesseract is not installed`, you need to explicitly point Python to the `tesseract.exe` path. Add this to your `.env` file:
  `TESSERACT_CMD="C:\Program Files\Tesseract-OCR\tesseract.exe"`
  And modify `backend/ingestion/processor.py` to read it: `pytesseract.pytesseract.tesseract_cmd = os.getenv("TESSERACT_CMD")`


