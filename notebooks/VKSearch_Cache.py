import os
import numpy as np
import redis
from redis.commands.search.field import VectorField, TagField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query
from types import SimpleNamespace
from datetime import datetime

# --- Configuration ---
# Assuming 'docs' is defined elsewhere as in your snippet
VALKEY_HOST = 'localhost'
VALKEY_PORT = 6379
INDEX_NAME = "clip_embeddings_idx"
VECTOR_DIM = 512
DOC_PREFIX = "img:"

# Initialize Client
r = redis.Redis(host=VALKEY_HOST, port=VALKEY_PORT)

def create_index(r, idx_name, dim):
    """Creates the ValkeySearch index if it doesn't exist."""
    try:
        r.ft(idx_name).info()
        print(f"Index '{idx_name}' already exists.")
    except redis.exceptions.ResponseError:
        # Index does not exist, create it
        schema = (
            TagField("id"),
            VectorField("embedding",
                "HNSW", {
                    "TYPE": "FLOAT32",
                    "DIM": dim,
                    "DISTANCE_METRIC": "COSINE"
                }
            )
        )
        definition = IndexDefinition(prefix=[DOC_PREFIX], index_type=IndexType.HASH)
        r.ft(idx_name).create_index(schema, definition=definition)
        print(f"Created index '{idx_name}'.")

def get_cache_stats(r, idx_name):
    """Checks if cache is valid and consistent with current docs."""
    try:
        info = r.ft(idx_name).info()
        num_docs_in_cache = int(info['num_docs'])
        return True, num_docs_in_cache
    except redis.exceptions.ResponseError:
        return False, 0

# --- Main Logic ---

embeddings = None
cache_valid = False

# Phase 1: Check Valkey Cache
print("Connecting to Valkey Cache...")
create_index(r, INDEX_NAME, VECTOR_DIM)
index_exists, cached_count = get_cache_stats(r, INDEX_NAME)

# Phase 2: Validate Consistency
if index_exists:
    if cached_count == len(docs):
        print("Cache validated successfully!")
        print(f"  - Count: {cached_count} vectors")
        
        # OPTION A: If you just need to search, you are done. 
        # OPTION B: If your code strictly needs the numpy array in memory (like the pickle version):
        print("  - Loading vectors into memory (Lazy loading recommended instead)...")
        
        # Note: Fetching all vectors can be slow for massive datasets. 
        # Usually, you keep them in Valkey and only query.
        # But to replicate your pickle logic exactly:
        all_vectors = []
        pipeline = r.pipeline()
        for i in range(len(docs)):
            pipeline.hget(f"{DOC_PREFIX}{i}", "embedding")
        
        results = pipeline.execute()
        
        # Convert bytes back to numpy
        try:
            arrays = [np.frombuffer(res, dtype=np.float32) for res in results if res]
            if len(arrays) == len(docs):
                full_matrix = np.vstack(arrays)
                embeddings = SimpleNamespace(embeddings=full_matrix)
                cache_valid = True
            else:
                print("Cache corrupted (missing keys). Will regenerate.")
        except Exception as e:
            print(f"Error deserializing cache: {e}")
            
    else:
        print(f"Cache dimension mismatch:")
        print(f"   Valkey Index contains: {cached_count} vectors")
        print(f"   Current dataset: {len(docs)} images")
        print(f"   Cache will be regenerated/upserted.")
        # Optional: Flush DB if you want a clean slate
        # r.flushdb() 
        # create_index(r, INDEX_NAME, VECTOR_DIM)

# Encoding phase - only if cache validation failed
if not cache_valid:
    print(f"\n{'='*60}")
    print(f"Encoding {len(docs)} images with CLIP")
    print(f"{'='*60}")
    
    # Assuming c.encode and data_generator exist as in your snippet
    embeddings = c.encode(
        data_generator(docs),
        batch_size=16,
        show_progress=True,
        length=len(docs)
    )
    
    print(f"\n Encoding complete! Shape: {embeddings.embeddings.shape}")
    
    # Phase 3: Persist to Valkey
    print("Hydrating Valkey Cache...")
    pipeline = r.pipeline(transaction=False)
    
    for i, vector in enumerate(embeddings.embeddings):
        # Convert numpy float32 array to bytes
        vector_bytes = vector.astype(np.float32).tobytes()
        
        # We use the index 'i' to map back to your docs list
        # If your docs have unique IDs (e.g., filenames), use those instead of i
        key = f"{DOC_PREFIX}{i}"
        
        pipeline.hset(key, mapping={
            "id": i,
            "embedding": vector_bytes,
            "timestamp": datetime.now().isoformat(),
            # Add Neo4j ID here if available, e.g., "neo4j_id": docs[i].id
        })
        
        # Execute in chunks to prevent buffer overload
        if i % 100 == 0:
            pipeline.execute()
            
    pipeline.execute() # Final batch
    print(f"Cache persisted successfully to index '{INDEX_NAME}'")

print(f"\n{'='*60}")
if embeddings:
    print(f"Ready! Embeddings shape: {embeddings.embeddings.shape}")
else:
    print("Ready! Vectors stored in Valkey (Memory mapping skipped).")
print(f"{'='*60}")

def search_similar(query_vector_numpy, k=5):
    query_bytes = query_vector_numpy.astype(np.float32).tobytes()
    
    q = Query(f"*=>[KNN {k} @embedding $vec AS score]")\
        .sort_by("score")\
        .return_fields("id", "score")\
        .dialect(2)
        
    res = r.ft(INDEX_NAME).search(q, query_params={"vec": query_bytes})
    
    for doc in res.docs:
        print(f"Found Image ID: {doc.id}, Score: {doc.score}")
        # Here you would fetch the full node from Neo4j using doc.id