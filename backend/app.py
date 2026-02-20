from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import time
from werkzeug.utils import secure_filename
from document_processor import DocumentProcessor
from rag_engine import RAGEngine
from analytics import Analytics

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'data/documents'
ALLOWED_EXTENSIONS = {'pdf'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize components
doc_processor = DocumentProcessor()
rag_engine = RAGEngine()
analytics = Analytics()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'RAG system is running'})

@app.route('/api/initialize', methods=['POST'])
def initialize_system():
    """Initialize system with default documents"""
    try:
        # Check if vectorstore already exists
        stats = rag_engine.get_stats()
        if stats['total_chunks'] > 0:
            return jsonify({
                'success': True,
                'message': 'System already initialized',
                'stats': stats
            })
        
        # Process default documents (if they exist)
        documents_path = UPLOAD_FOLDER
        processed_docs = []
        
        for filename in os.listdir(documents_path):
            if filename.endswith('.pdf'):
                pdf_path = os.path.join(documents_path, filename)
                doc_data = doc_processor.process_document(pdf_path, filename)
                if doc_data:
                    processed_docs.append(doc_data)
                    analytics.log_document(filename, doc_data['metadata']['num_chunks'])
        
        if processed_docs:
            rag_engine.create_vectorstore(processed_docs)
            stats = rag_engine.get_stats()
            return jsonify({
                'success': True,
                'message': f'Initialized with {len(processed_docs)} documents',
                'stats': stats
            })
        else:
            return jsonify({
                'success': True,
                'message': 'No documents found to initialize',
                'stats': {'total_chunks': 0, 'total_documents': 0, 'documents': {}}
            })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_document():
    """Upload and process a new document"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Only PDF files are allowed'}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Process document
        doc_data = doc_processor.process_document(filepath, filename)
        
        if not doc_data:
            return jsonify({'success': False, 'error': 'Failed to process document'}), 500
        
        # Add to vectorstore
        rag_engine.add_documents([doc_data])
        analytics.log_document(filename, doc_data['metadata']['num_chunks'])
        
        return jsonify({
            'success': True,
            'message': f'Document "{filename}" processed successfully',
            'chunks': doc_data['metadata']['num_chunks']
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/query', methods=['POST'])
def query_system():
    """Query the RAG system"""
    try:
        data = request.json
        question = data.get('question', '')
        
        if not question:
            return jsonify({'success': False, 'error': 'No question provided'}), 400
        
        # Check if system is initialized
        stats = rag_engine.get_stats()
        if stats['total_chunks'] == 0:
            return jsonify({
                'success': False,
                'error': 'System not initialized. Please upload documents first.'
            }), 400
        
        # Query the system
        start_time = time.time()
        result = rag_engine.query(question)
        response_time = time.time() - start_time
        
        # Log query
        analytics.log_query(question, response_time, len(result['sources']))
        
        return jsonify({
            'success': True,
            'answer': result['answer'],
            'sources': result['sources'],
            'response_time': round(response_time, 2)
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get system statistics"""
    try:
        vectorstore_stats = rag_engine.get_stats()
        return jsonify({
            'success': True,
            'stats': vectorstore_stats
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    """Get analytics data"""
    try:
        vectorstore_stats = rag_engine.get_stats()
        charts_data = analytics.generate_charts(vectorstore_stats)
        
        return jsonify({
            'success': True,
            'analytics': charts_data
        })
    except Exception as e:
        print(f"Analytics error: {str(e)}")  # Debug print
        import traceback
        traceback.print_exc()  # Print full traceback
        return jsonify({
            'success': False, 
            'error': str(e),
            'analytics': {
                'document_distribution': {'labels': [], 'values': []},
                'query_timeline': {'hours': [f"{h}:00" for h in range(24)], 'queries': [0]*24},
                'recent_response_times': [],
                'stats': {
                    'total_documents': 0,
                    'total_chunks': 0,
                    'total_queries': 0,
                    'avg_response_time': 0
                }
            }
        }), 200  # Return 200 even on error with empty data

@app.route('/api/documents', methods=['GET'])
def list_documents():
    """List all documents in the system"""
    try:
        stats = rag_engine.get_stats()
        documents = [{'name': name, 'chunks': count} 
                    for name, count in stats.get('documents', {}).items()]
        
        return jsonify({
            'success': True,
            'documents': documents
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("Starting Financial RAG Application...")
    print("Make sure Ollama is running with Mistral model!")
    app.run(debug=True, host='0.0.0.0', port=5000)