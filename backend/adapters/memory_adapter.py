"""Memory adapter - interfaces with vector_memory via subprocess"""
import subprocess
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from ..config import settings


def _get_paths():
    """Get workspace and vector memory paths from settings"""
    workspace = Path(settings.workspace_path).expanduser()
    vector_memory = Path(settings.vector_memory_path).expanduser()
    return workspace, vector_memory


class MemoryAdapter:
    """Adapter for vector_memory system"""
    
    def search(self, query: str, n: int = 5) -> list[dict]:
        """Search vector memory for chunks matching query"""
        return self._chromadb_search(query, n)
    
    def _chromadb_search(self, query: str, n: int) -> list[dict]:
        """Execute chromadb search via subprocess"""
        workspace, vector_memory = _get_paths()
        venv_python = str(vector_memory / "venv/bin/python")
        
        # Build script with NO user input interpolated - use env vars
        script = f"""
import sys
import os
sys.path.insert(0, '{vector_memory}')
import chromadb
from sentence_transformers import SentenceTransformer
import json

try:
    query = os.environ["SEARCH_QUERY"]
    n_results = int(os.environ.get("SEARCH_N", "5"))
    
    client = chromadb.PersistentClient(path='{vector_memory}/chroma_db')
    collections = client.list_collections()
    if not collections:
        print(json.dumps([]))
        sys.exit(0)
    
    collection = collections[0]
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    embedding = model.encode([query]).tolist()
    results = collection.query(
        query_embeddings=embedding,
        n_results=n_results,
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
            # Pass user input via environment variables
            env = {**os.environ, "SEARCH_QUERY": query, "SEARCH_N": str(n)}
            result = subprocess.run(
                [venv_python, '-c', script],
                capture_output=True,
                text=True,
                timeout=30,
                env=env
            )
            if result.stderr:
                print(f"[memory_adapter] stderr: {result.stderr[:300]}", file=sys.stderr)
            if result.returncode != 0:
                return [{"error": "subprocess_failed", "detail": result.stderr[:200] if result.stderr else "unknown"}]
            return json.loads(result.stdout)
        except subprocess.TimeoutExpired:
            return [{"error": "timeout", "detail": "Search timed out after 30s"}]
        except json.JSONDecodeError as e:
            return [{"error": "parse_failed", "detail": str(e)}]
        except Exception as e:
            return [{"error": "exception", "detail": str(e)}]
    
    def get_status(self) -> dict:
        """Get memory system status"""
        workspace, vector_memory = _get_paths()
        venv_python = str(vector_memory / "venv/bin/python")
        
        script = f"""
import sys
import json
sys.path.insert(0, '{vector_memory}')
import chromadb
import os

try:
    client = chromadb.PersistentClient(path='{vector_memory}/chroma_db')
    collections = client.list_collections()
    chunk_count = 0
    if collections:
        chunk_count = collections[0].count()
    
    # Try graph
    graph_path = '{vector_memory}/memory_graph.json'
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
                [venv_python, '-c', script],
                capture_output=True,
                text=True,
                timeout=15
            )
            if result.stderr:
                print(f"[memory_adapter] stderr: {result.stderr[:300]}", file=sys.stderr)
            if result.returncode != 0:
                return {'chunks': 0, 'nodes': 0, 'edges': 0}
            return json.loads(result.stdout)
        except Exception:
            return {'chunks': 0, 'nodes': 0, 'edges': 0}
    
    def list_files(self) -> list[str]:
        """List indexed markdown files in workspace"""
        workspace, _ = _get_paths()
        files = []
        patterns = ['*.md', 'memory/*.md', 'reference/*.md', 'skills/*/*.md']
        for pattern in patterns:
            for p in workspace.glob(pattern):
                if p.is_file():
                    files.append(str(p.relative_to(workspace)))
        return sorted(set(files))
    
    def get_last_sync(self) -> tuple[str, str]:
        """Get last sync timestamp from auto_retrieve.py status"""
        workspace, vector_memory = _get_paths()
        venv_python = str(vector_memory / "venv/bin/python")
        
        try:
            result = subprocess.run(
                [venv_python, str(vector_memory / "auto_retrieve.py"), "--status"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.stderr:
                print(f"[memory_adapter] stderr: {result.stderr[:300]}", file=sys.stderr)
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
            _, vector_memory = _get_paths()
            db_path = vector_memory / "chroma_db"
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
    
    # Phase 2 additions
    def read_file(self, relative_path: str) -> dict:
        """Read a file from workspace with path traversal protection"""
        workspace, _ = _get_paths()
        
        # Resolve and validate path stays within workspace
        resolved = (workspace / relative_path).resolve()
        if not resolved.is_relative_to(workspace):
            raise ValueError(f"Path traversal denied: {relative_path}")
        
        if not resolved.exists():
            raise FileNotFoundError(f"File not found: {relative_path}")
        
        if not resolved.is_file():
            raise ValueError(f"Not a file: {relative_path}")
        
        content = resolved.read_text(encoding='utf-8', errors='replace')
        size_bytes = resolved.stat().st_size
        
        return {
            'path': str(resolved.relative_to(workspace)),
            'content': content,
            'size_bytes': size_bytes
        }
    
    def delete_chunk(self, chunk_id: str) -> bool:
        """Delete a chunk from ChromaDB"""
        print(f"[memory_adapter] DELETE_CHUNK requested: {chunk_id}", file=sys.stderr)
        workspace, vector_memory = _get_paths()
        venv_python = str(vector_memory / "venv/bin/python")
        
        script = f"""
import sys
import os
import json
sys.path.insert(0, '{vector_memory}')
import chromadb

try:
    chunk_id = os.environ["CHUNK_ID"]
    client = chromadb.PersistentClient(path='{vector_memory}/chroma_db')
    collections = client.list_collections()
    
    if not collections:
        print(json.dumps({{"deleted": False, "reason": "no_collections"}}))
        sys.exit(0)
    
    collection = collections[0]
    
    # Check if chunk exists
    existing = collection.get(ids=[chunk_id])
    if not existing["ids"]:
        print(json.dumps({{"deleted": False, "reason": "not_found"}}))
        sys.exit(0)
    
    collection.delete(ids=[chunk_id])
    print(json.dumps({{"deleted": True}}))
except Exception as e:
    print(json.dumps({{"deleted": False, "error": str(e)}}))
"""
        try:
            env = {**os.environ, "CHUNK_ID": chunk_id}
            result = subprocess.run(
                [venv_python, '-c', script],
                capture_output=True,
                text=True,
                timeout=30,
                env=env
            )
            if result.returncode != 0:
                print(f"[memory_adapter] DELETE_CHUNK completed: {chunk_id} deleted=False", file=sys.stderr)
                return False
            data = json.loads(result.stdout)
            deleted = data.get("deleted", False)
            print(f"[memory_adapter] DELETE_CHUNK completed: {chunk_id} deleted={deleted}", file=sys.stderr)
            return deleted
        except Exception:
            print(f"[memory_adapter] DELETE_CHUNK completed: {chunk_id} deleted=False", file=sys.stderr)
            return False
    
    def reindex(self) -> dict:
        """Run the vector memory indexer"""
        import time
        workspace, vector_memory = _get_paths()
        venv_python = str(vector_memory / "venv/bin/python")
        indexer_path = vector_memory / "indexer.py"
        
        job_id = f"reindex_{int(time.time())}"
        started_at = datetime.now().isoformat()
        
        if not indexer_path.exists():
            return {
                'job_id': job_id,
                'status': 'failed',
                'started_at': started_at,
                'completed_at': datetime.now().isoformat(),
                'chunks_indexed': None,
                'error': f"Indexer not found: {indexer_path}"
            }
        
        try:
            result = subprocess.run(
                [venv_python, str(indexer_path)],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(vector_memory)
            )
            
            completed_at = datetime.now().isoformat()
            
            # Parse chunks count from output if possible
            chunks_indexed = None
            for line in result.stdout.split('\n'):
                if 'chunk' in line.lower():
                    # Try to extract a number
                    import re
                    nums = re.findall(r'\d+', line)
                    if nums:
                        chunks_indexed = int(nums[0])
                        break
            
            if result.returncode == 0:
                return {
                    'job_id': job_id,
                    'status': 'complete',
                    'started_at': started_at,
                    'completed_at': completed_at,
                    'chunks_indexed': chunks_indexed,
                    'error': None
                }
            else:
                return {
                    'job_id': job_id,
                    'status': 'failed',
                    'started_at': started_at,
                    'completed_at': completed_at,
                    'chunks_indexed': None,
                    'error': result.stderr[:500] if result.stderr else "Unknown error"
                }
        except subprocess.TimeoutExpired:
            return {
                'job_id': job_id,
                'status': 'failed',
                'started_at': started_at,
                'completed_at': datetime.now().isoformat(),
                'chunks_indexed': None,
                'error': "Reindex timed out after 120s"
            }
        except Exception as e:
            return {
                'job_id': job_id,
                'status': 'failed',
                'started_at': started_at,
                'completed_at': datetime.now().isoformat(),
                'chunks_indexed': None,
                'error': str(e)
            }
    
    def get_graph(self) -> dict:
        """Get the knowledge graph data"""
        _, vector_memory = _get_paths()
        graph_path = vector_memory / "memory_graph.json"
        
        if not graph_path.exists():
            return {'nodes': 0, 'edges': 0, 'data': {}}
        
        try:
            with open(graph_path, 'r') as f:
                data = json.load(f)
            
            nodes = len(data.get('nodes', []))
            edges = len(data.get('links', data.get('edges', [])))
            
            return {
                'nodes': nodes,
                'edges': edges,
                'data': data
            }
        except Exception:
            return {'nodes': 0, 'edges': 0, 'data': {}}
