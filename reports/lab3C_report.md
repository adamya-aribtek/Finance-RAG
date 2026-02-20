# Lab 3C Report: Financial Retrieval-Augmented Generation (RAG) System

## 1. Objective
The objective of this project is to develop an automated Financial Analysts Assistant using RAG (Retrieval-Augmented Generation) technology. Financial institutions and investors face an overwhelming volume of documents (SEC filings, annual reports, earnings calls) that are difficult to parse manually. 
- **Problem Solved**: High-latency information retrieval and the "needle in a haystack" problem in unstructured financial PDFs.
- **SDG/Industry Alignment**: Directly supports **SDG 9 (Industry, Innovation, and Infrastructure)** by enhancing digital financial infrastructure and **SDG 8 (Decent Work and Economic Growth)** by improving financial transparency and decision-making efficiency.

## 2. Dataset
- **Source**: Publicly available SEC filings (10-K, 10-Q) and standard financial reports.
- **Target Definition**: Extraction of precise quantitative metrics (e.g., Revenue, Net Income) and qualitative insights (e.g., Risk Factors).
- **Key Fields**: Page content, Document metadata (source name), Chunk ID.
- **PII Notes**: The system processes public filings; however, a regex-based PII scrubber is recommended for internal corporate documents to ensure compliance with GDPR/CCPA.

## 3. Method
- **Split Strategy**: Recursive Character Text Splitting with a chunk size of 1000 characters and an overlap of 200 characters. This ensures contextual continuity across chunk boundaries.
- **Baseline**: Static keyword-based search on raw PDF text.
- **Improved Model**: 
    - **Embeddings**: `all-MiniLM-L6-v2` (Sentence Transformers) for semantic vectorization.
    - **Vector Store**: FAISS (Facebook AI Similarity Search) FlatL2 index for low-latency retrieval.
    - **LLM**: TinyLlama (v1.1) via the Ollama local inference engine.
- **Hyperparameters Summary**:
    - Temperature: 0.3 (for deterministic/precise answers)
    - Top_p: 0.9
    - k (Retrieval): 5 chunks
- **Reproducibility Notes**: Fixed seed not explicitly set in inference, but deterministic retrieval ensured by FAISS index persistence. Environment controlled via `requirements.txt`.



## 4. Error Analysis
### Failure Taxonomy
1. **Retrieval Failure (Missed Context)**: Relevant information exists in the PDF but was not ranked in the top-k results.
2. **Context Overflow**: The answer requires context from more than 5 chunks, exceeding the prompt window.
3. **Hallucination (Faithfulness)**: The LLM generates numbers not present in the provided context (e.g., 2024 projections when context only has 2023).
4. **Formatting Issues**: Failure to parse table structures correctly within the PDF, leading to garbled numbers.

### Representative Failure Cases
- *Query*: "What was the growth rate of Tesla in 2024?" -> *Result*: Hallucinated 25% because the context only contained 2023 data.
- *Query*: "Summarize the risk factors." -> *Result*: Missing 2 items because they were located in chunk 7 (outside top-k).

## 5. Risks and Ethics
- **Potential Harms**: Financial misinformation leading to poor investment decisions.
- **Bias Risks**: Model may favor sentiment from larger, more formatted reports over smaller ones.
- **Mitigation**: 
    - Citations: Every answer must include accurate source metadata.
    - Disclaimer: "AI-generated output should be verified against the original filing."

## 6. Next Steps
1. **Hybrid Search (High Impact/Medium Effort)**: Combine BM25 keyword search with FAISS semantic search to improve retrieval of specific codes or dates.
2. **Table Parsing (High Impact/High Effort)**: Integrate `Unstructured` or `Camelot` to better capture financial tables.
3. **Query Expansion (Medium Impact/Low Effort)**: Implement "Multi-Query" retrieval to rephrase user questions into multiple perspectives.
4. **Metadata Filtering (Medium Impact/Medium Effort)**: Allow users to filter searches by "Year" or "Company" directly.
