# 🏦 Financial RAG Assistant
[![Status](https://img.shields.io/badge/Status-Active-brightgreen)]()
[![Tech](https://img.shields.io/badge/Tech-Python%20|%20FAISS%20|%20Ollama-blue)]()

A state-of-the-art **Retrieval-Augmented Generation (RAG)** application designed for deep analysis of financial documents. This system combines the speed of **FAISS** vector search with the reasoning capabilities of **TinyLlama** to provide precise, context-aware answers to complex financial queries.

---

## 🚀 Quick Start

### 1. Prerequisites
- **Python 3.10+**
- **Ollama**: [Download here](https://ollama.com/)
- **Node.js**: (Optional, for frontend serving)

### 2. Setup Environment
```bash
# Setup Python environment
cd backend
python -m venv finenv
# Activate on Windows:
finenv\Scripts\activate
# Activate on Linux/Mac:
source finenv/bin/activate

pip install -r requirements.txt
```

### 3. Launch the Application

#### **Step A: Start Ollama**
Ensure the local inference engine is running and the model is pulled:
```bash
ollama run tinyllama
```

#### **Step B: Start Backend API**
In a new terminal (within the `backend` folder):
```bash
python app.py
```
*The server will start at `http://127.0.0.1:5000`*

#### **Step C: Start Frontend UI**
In a new terminal (within the `frontend` folder):
```bash
# Option 1: Simple Python server
python -m http.server 8000

# Option 2: Using NPM (Recommended)
npx serve .
```
*Navigate to `http://localhost:8000` or `http://localhost:3000`*

---

## 🛠️ Architecture

The system operates on a four-stage pipeline:

1.  **Ingestion**: PDF documents are parsed and cleaned using advanced text extractors.
2.  **Indexing**: Text is split into overlapping chunks and converted into 384-dimensional embeddings using `all-MiniLM-L6-v2`.
3.  **Retrieval**: Questions are vectorized and matched against the FAISS index using L2 distance.
4.  **Generation**: The top match results are fed into the LLM (Ollama) with a specialized "Financial Analyst" prompt.

---

## ✨ Key Features

-   **Dual Mode Retrieval**: Semantic search allows for understanding intent even without exact keyword matches.
-   **Analytics Dashboard**: Real-time monitoring of document coverage and query performance.
-   **Local-First Privacy**: Entire pipeline runs locally—your sensitive financial data never leaves your machine.
-   **Source Attribution**: Every answer comes with a list of source documents and relevance scores.

---

## 📂 Project Structure

```text
FinanceRAG/
├── backend/
│   ├── app.py                # Flask REST API
│   ├── rag_engine.py         # Vector search & LLM logic
│   ├── document_processor.py # PDF parsing & embedding
│   ├── analytics.py          # Statistics generator
│   ├── data/                 # Persistence layer (Documents & Indices)
│   └── requirements.txt      # Dependency list
├── frontend/
│   ├── index.html            # Premium UI Layout
│   ├── styles.css            # Glassmorphic Styling
│   └── app.js                # State management & API integration
├── reports/
│   └── lab3C_report.md       # Technical Analysis Report
└── .gitignore                # Repository hygiene
```

## 📈 Next Steps
- Implement **Hybrid Search** (Keyword + Semantic).
- Add support for **multi-turn conversations** (Chat History).
- Integrate **Table Extraction** optimizations.