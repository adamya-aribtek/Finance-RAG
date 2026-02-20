import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List
from datetime import datetime
import json

class Analytics:
    def __init__(self):
        self.queries_log = []
        self.documents_log = []
    
    def log_query(self, query: str, response_time: float, sources_used: int):
        """Log a query"""
        self.queries_log.append({
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'response_time': response_time,
            'sources_used': sources_used
        })
    
    def log_document(self, doc_name: str, num_chunks: int):
        """Log a document upload"""
        self.documents_log.append({
            'timestamp': datetime.now().isoformat(),
            'document': doc_name,
            'chunks': num_chunks
        })
    
    def get_query_stats(self) -> Dict:
        """Get query statistics"""
        if not self.queries_log:
            return {
                'total_queries': 0,
                'avg_response_time': 0,
                'queries_by_hour': {}
            }
        
        df = pd.DataFrame(self.queries_log)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['hour'] = df['timestamp'].dt.hour
        
        queries_by_hour = df.groupby('hour').size().to_dict()
        
        return {
            'total_queries': len(self.queries_log),
            'avg_response_time': float(df['response_time'].mean()),
            'queries_by_hour': queries_by_hour
        }
    
    def generate_charts(self, vectorstore_stats: Dict) -> Dict:
        """Generate chart data for frontend"""
        
        # Document distribution chart
        doc_data = vectorstore_stats.get('documents', {})
        doc_chart = {
            'labels': list(doc_data.keys()),
            'values': list(doc_data.values())
        }
        
        # Query timeline chart
        query_stats = self.get_query_stats()
        timeline_data = query_stats.get('queries_by_hour', {})
        
        timeline_chart = {
            'hours': [f"{h}:00" for h in range(24)],
            'queries': [timeline_data.get(h, 0) for h in range(24)]
        }
        
        # Response time data
        response_times = [q['response_time'] for q in self.queries_log[-20:]]
        
        # Calculate stats safely
        avg_response = query_stats.get('avg_response_time', 0)
        if avg_response and not isinstance(avg_response, (int, float)):
            avg_response = 0
        
        return {
            'document_distribution': doc_chart,
            'query_timeline': timeline_chart,
            'recent_response_times': response_times,
            'stats': {
                'total_documents': vectorstore_stats.get('total_documents', 0),
                'total_chunks': vectorstore_stats.get('total_chunks', 0),
                'total_queries': query_stats['total_queries'],
                'avg_response_time': round(float(avg_response), 2) if avg_response else 0
            }
        }