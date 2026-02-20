import os
import re
from typing import List, Dict
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import numpy as np

class DocumentProcessor:
    def __init__(self):
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file"""
        try:
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"Error extracting text from {pdf_path}: {e}")
            return ""
    
    def clean_text(self, text: str) -> str:
        """Clean extracted text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep financial symbols
        text = re.sub(r'[^\w\s$%.,()-]', '', text)
        return text.strip()
    
    def chunk_text(self, text: str) -> List[str]:
        """Split text into chunks"""
        return self.text_splitter.split_text(text)
    
    def process_document(self, pdf_path: str, doc_name: str) -> Dict:
        """Process a single document"""
        print(f"Processing document: {doc_name}")
        
        # Extract text
        raw_text = self.extract_text_from_pdf(pdf_path)
        if not raw_text:
            return None
        
        # Clean text
        cleaned_text = self.clean_text(raw_text)
        
        # Chunk text
        chunks = self.chunk_text(cleaned_text)
        
        # Generate embeddings
        embeddings = self.embedding_model.encode(chunks, show_progress_bar=True)
        
        return {
            'document_name': doc_name,
            'chunks': chunks,
            'embeddings': embeddings,
            'metadata': {
                'num_chunks': len(chunks),
                'total_length': len(cleaned_text)
            }
        }
    
    def extract_financial_metrics(self, text: str) -> Dict:
        """Extract key financial metrics from text"""
        metrics = {
            'revenue': [],
            'profit': [],
            'assets': [],
            'liabilities': []
        }
        
        # Simple pattern matching for financial terms
        revenue_pattern = r'revenue[s]?\s*(?:of\s*)?\$?([\d,]+\.?\d*)\s*(?:million|billion)?'
        profit_pattern = r'(?:net\s*)?profit[s]?\s*(?:of\s*)?\$?([\d,]+\.?\d*)\s*(?:million|billion)?'
        
        metrics['revenue'] = re.findall(revenue_pattern, text.lower())
        metrics['profit'] = re.findall(profit_pattern, text.lower())
        
        return metrics