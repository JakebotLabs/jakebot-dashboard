"""Memory adapter - interfaces with vector_memory via subprocess"""
import subprocess
import json
import os
from pathlib import Path
from datetime import datetime


WORKSPACE = Path("/home/jakebot/.openclaw/workspace")
VECTOR_MEMORY = WORKSPACE / "vector_memory"
VENV_PYTHON = str(VECTOR_MEMORY / "venv/bin/python")


class MemoryAdapter:
    """Adapter for vector_memory system"""
    
    def search(self, query: str, n: int = 5) -> list[dict]:
        """Search vector memory for chunks matching query"""
        return self._chromadb_search(query, n)
    
    def _chromadb_search(self, query: str, n: int) -> list[dict]:
        """Execute chromadb search via subprocess"""
        # Escape single quotes in query
        escaped_query = query.replace("'", "\\'")
        
        script = f"""
import sys
sys.path.insert(0, '{VECTOR_MEMORY}')
import chromadb
from sentence_transformers import SentenceTransformer
import json

try:
    client = chromadb.PersistentClient(path='{VECTOR_MEMORY}/chroma_db')
    collections = client.list_collections()
    if not collections:
        print(json.dumps([]))
        sys.exit(0)
    
    collection = collections[0]
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    embedding = model.encode(['{escaped_query}']).tolist()
    results = collection.query(
        query_embeddings=embedding,
        n_results={n},
        include=['documents', 'metadatas', 'distances']
    )
    
    output = []
    for i, doc in enumerate(results['documents'][0]):
        meta = results['metadatas'][0][i] if results['metadatas'] else {{}}
        dist = results['distances'][0][i] if results['distances'] else 0
        output.append({{
            'chunk_id': results['ids'][0][i],
            'content': doc[:500],
            'source': meta.get('source', ''),
            'section': meta.get('section', ''),
            'score': round(1 - dist, 3)
        }})
    print(json.dumps(output))
except Exception as e:
    print(json.dumps({{"error": str(e)}}), file=sys.stderr)
    print(json.dumps([]))
"""
        try:
            result = subprocess.run(
                [VENV_PYTHON, '-c', script],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode != 0:
                return []
            return json.loads(result.stdout)
        except Exception:
            return []
    
    def get_status(self) -> dict:
        """Get memory system status"""
        script = f"""
import sys
import json
sys.path.insert(0, '{VECTOR_MEMORY}')
import chromadb
import os

try:
    client = chromadb.PersistentClient(path='{VECTOR_MEMORY}/chroma_db')
    collections = client.list_collections()
    chunk_count = 0
    if collections:
        chunk_count = collections[0].count()
    
    # Try graph
    graph_path = '{VECTOR_MEMORY}/memory_graph.json'
    nodes, edges = 0, 0
    if os.path.exists(graph_path):
        with open(graph_path) as f:
            g = json.load(f)
        nodes = len(g.get('nodes', []))
        edges = len(g.get('links', g.get('edges', [])))
    
    print(json.dumps({{'chunks': chunk_count, 'nodes': nodes, 'edges': edges}}))
except Exception as e:
    print(json.dumps({{'chunks': 0, 'nodes': 0, 'edges': 0}}))
"""
        try:
            result = subprocess.run(
                [VENV_PYTHON, '-c', script],
                capture_output=True,
                text=True,
                timeout=15
            )
            if result.returncode != 0:
                return {'chunks': 0, 'nodes': 0, 'edges': 0}
            return json.loads(result.stdout)
        except Exception:
            return {'chunks': 0, 'nodes': 0, 'edges': 0}
    
    def list_files(self) -> list[str]:
        """List indexed markdown files in workspace"""
        files = []
        patterns = ['*.md', 'memory/*.md', 'reference/*.md', 'skills/*/*.md']
        for pattern in patterns:
            for p in WORKSPACE.glob(pattern):
                if p.is_file():
                    files.append(str(p.relative_to(WORKSPACE)))
        return sorted(set(files))
    
    def get_last_sync(self) -> tuple[str, str]:
        """Get last sync timestamp from auto_retrieve.py status"""
        try:
            result = subprocess.run(
                [VENV_PYTHON, str(VECTOR_MEMORY / "auto_retrieve.py"), "--status"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'Last sync:' in line:
                        # Parse timestamp
                        parts = line.split('Last sync:')
                        if len(parts) > 1:
                            timestamp = parts[1].strip()
                            # Calculate ago
                            try:
                                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                                delta = datetime.now() - dt.replace(tzinfo=None)
                                hours = delta.total_seconds() / 3600
                                if hours < 1:
                                    ago = f"{int(delta.total_seconds() / 60)}m ago"
                                elif hours < 24:
                                    ago = f"{int(hours)}h ago"
                                else:
                                    ago = f"{int(hours / 24)}d ago"
                                return timestamp, ago
                            except Exception:
                                return timestamp, "unknown"
        except Exception:
            pass
        return "never", "never"
    
    def get_db_size(self) -> float:
        """Get ChromaDB size in MB"""
        try:
            db_path = VECTOR_MEMORY / "chroma_db"
            if not db_path.exists():
                return 0.0
            
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(db_path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if os.path.exists(fp):
                        total_size += os.path.getsize(fp)
            
            return round(total_size / (1024 * 1024), 2)
        except Exception:
            return 0.0
