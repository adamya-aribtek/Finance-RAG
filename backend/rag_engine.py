import faiss
import numpy as np
import pickle
import os
from typing import List, Dict, Tuple
from sentence_transformers import SentenceTransformer
import requests
import json

class RAGEngine:
    def __init__(self, vectorstore_path: str = "data/vectorstore"):
        self.vectorstore_path = vectorstore_path
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.index = None
        self.chunks = []
        self.metadata = []
        self.ollama_url = "http://127.0.0.1:11434/api/generate"
        
        os.makedirs(vectorstore_path, exist_ok=True)
        self.load_vectorstore()
    
    def create_vectorstore(self, documents: List[Dict]):
        """Create FAISS vectorstore from documents"""
        all_chunks = []
        all_embeddings = []
        all_metadata = []
        
        for doc in documents:
            if doc:
                chunks = doc['chunks']
                embeddings = doc['embeddings']
                doc_name = doc['document_name']
                
                all_chunks.extend(chunks)
                all_embeddings.append(embeddings)
                all_metadata.extend([{'source': doc_name, 'chunk_id': i} 
                                    for i in range(len(chunks))])
        
        if not all_embeddings:
            print("No embeddings to add")
            return
        
        # Concatenate all embeddings
        embeddings_array = np.vstack(all_embeddings).astype('float32')
        
        # Create FAISS index
        dimension = embeddings_array.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings_array)
        
        self.chunks = all_chunks
        self.metadata = all_metadata
        
        # Save vectorstore
        self.save_vectorstore()
        print(f"Vectorstore created with {len(all_chunks)} chunks")
    
    def add_documents(self, documents: List[Dict]):
        """Add new documents to existing vectorstore"""
        if self.index is None:
            self.create_vectorstore(documents)
            return
        
        for doc in documents:
            if doc:
                chunks = doc['chunks']
                embeddings = doc['embeddings']
                doc_name = doc['document_name']
                
                self.chunks.extend(chunks)
                self.metadata.extend([{'source': doc_name, 'chunk_id': i} 
                                     for i in range(len(chunks))])
                
                embeddings_array = embeddings.astype('float32')
                self.index.add(embeddings_array)
        
        self.save_vectorstore()
        print(f"Added documents. Total chunks: {len(self.chunks)}")
    
    def search(self, query: str, k: int = 4) -> List[Tuple[str, Dict, float]]:
        """Search for relevant chunks"""
        if self.index is None or len(self.chunks) == 0:
            return []
        
        # Encode query
        query_embedding = self.embedding_model.encode([query]).astype('float32')
        
        # Search
        distances, indices = self.index.search(query_embedding, min(k, len(self.chunks)))
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.chunks):
                results.append((
                    self.chunks[idx],
                    self.metadata[idx],
                    float(dist)
                ))
        
        return results
    
    def generate_answer(self, query: str, context: str) -> str:
        """Generate answer using Ollama Mistral"""
        prompt = f"""You are a financial analyst assistant. Answer the question based on the provided context from SEC filings.

Context:
{context}

Question: {query}

Instructions:
- Provide a clear, concise answer based on the context
- If the context doesn't contain enough information, say so
- Include specific numbers and metrics when available
- Be professional and precise

Answer:"""

        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": "tinyllama",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "top_p": 0.9,
                        "num_predict": 400  # Changed from max_tokens to num_predict
                    }
                },
                timeout=120  # Increased timeout to 2 minutes for CPU processing
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', 'Unable to generate answer')
            else:
                return f"Error: Unable to reach Ollama (Status {response.status_code})"
        
        except requests.exceptions.Timeout:
            return "Error: The request timed out. The model is taking too long to respond on CPU. Consider using a smaller model or enabling GPU acceleration."
        except Exception as e:
            return f"Error generating answer: {str(e)}"
    
    def query(self, question: str, k: int = 5) -> Dict:
        """Query the RAG system"""
        # Search for relevant chunks
        search_results = self.search(question, k)
        
        if not search_results:
            return {
                'answer': 'No relevant information found in the knowledge base.',
                'sources': [],
                'context_used': ''
            }
        
        # Prepare context
        context = "\n\n".join([f"[From {meta['source']}]\n{chunk}" 
                               for chunk, meta, _ in search_results])
        
        # Generate answer
        answer = self.generate_answer(question, context)
        
        # Prepare sources
        sources = [{'source': meta['source'], 'score': score} 
                   for _, meta, score in search_results]
        
        return {
            'answer': answer,
            'sources': sources,
            'context_used': context
        }
    
    def save_vectorstore(self):
        """Save vectorstore to disk"""
        if self.index is not None:
            faiss.write_index(self.index, os.path.join(self.vectorstore_path, "index.faiss"))
            
            with open(os.path.join(self.vectorstore_path, "chunks.pkl"), 'wb') as f:
                pickle.dump(self.chunks, f)
            
            with open(os.path.join(self.vectorstore_path, "metadata.pkl"), 'wb') as f:
                pickle.dump(self.metadata, f)
    
    def load_vectorstore(self):
        """Load vectorstore from disk"""
        index_path = os.path.join(self.vectorstore_path, "index.faiss")
        chunks_path = os.path.join(self.vectorstore_path, "chunks.pkl")
        metadata_path = os.path.join(self.vectorstore_path, "metadata.pkl")
        
        if os.path.exists(index_path):
            self.index = faiss.read_index(index_path)
            
            with open(chunks_path, 'rb') as f:
                self.chunks = pickle.load(f)
            
            with open(metadata_path, 'rb') as f:
                self.metadata = pickle.load(f)
            
            print(f"Loaded vectorstore with {len(self.chunks)} chunks")
        else:
            print("No existing vectorstore found")
    
    def get_stats(self) -> Dict:
        """Get statistics about the vectorstore"""
        sources = {}
        for meta in self.metadata:
            source = meta['source']
            sources[source] = sources.get(source, 0) + 1
        
        return {
            'total_chunks': len(self.chunks),
            'total_documents': len(sources),
            'documents': sources
        }