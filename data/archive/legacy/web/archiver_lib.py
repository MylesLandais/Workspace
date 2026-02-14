import pandas as pd
import hashlib
import requests
import re
import os
from pathlib import Path
from typing import Optional, Set, Tuple

class ArchiveLibrary:
    def __init__(self, parquet_path: str, curation_db_config: Optional[dict] = None, postgres_config: Optional[dict] = None):
        self.parquet_path = Path(parquet_path)
        self.db_config = curation_db_config
        self.pg_config = postgres_config
        self._df = None
        self._last_loaded = None

    def load_data(self, force: bool = False) -> pd.DataFrame:
        """Load the parquet dataset with caching and basic cleanup."""
        if not self.parquet_path.exists():
            return pd.DataFrame()
        
        mtime = self.parquet_path.stat().st_mtime
        if self._df is not None and not force and mtime == self._last_loaded:
            return self._df

        try:
            df = pd.read_parquet(self.parquet_path)
            self._last_loaded = mtime
        except Exception as e:
            print(f"Error loading parquet: {e}")
            return pd.DataFrame()

        # Normalize timestamp
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            df['timestamp_str'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')

        # Defensive column handling
        for col in ['subject', 'comment', 'local_path', 'filename', 'is_op']:
            if col in df.columns:
                df[col] = df[col].fillna(False if col == 'is_op' else '')
            else:
                df[col] = False if col == 'is_op' else ''

        # Context mapping (thread subjects)
        if 'thread_id' in df.columns and 'is_op' in df.columns:
            op_subjects = df[df['is_op'] == True][['thread_id', 'subject']].drop_duplicates('thread_id')
            op_subjects = op_subjects.rename(columns={'subject': 'thread_subject'})
            df = df.merge(op_subjects, on='thread_id', how='left')
            df['thread_subject'] = df['thread_subject'].fillna('')
        else:
            df['thread_subject'] = ''

        # Apply soft-deletes from Postgres (preferred) or MySQL (legacy)
        if self.pg_config:
            del_threads, del_posts = self._get_soft_deleted_ids_pg()
            if del_threads:
                df = df[~df['thread_id'].astype(str).isin(del_threads)]
            if del_posts:
                df = df[~df['post_no'].astype(str).isin(del_posts)]
        elif self.db_config:
            del_threads, del_posts = self._get_soft_deleted_ids()
            if del_threads:
                df = df[~df['thread_id'].astype(str).isin(del_threads)]
            if del_posts:
                df = df[~df['post_no'].astype(str).isin(del_posts)]

        self._df = df
        return df

    def _get_soft_deleted_ids_pg(self) -> Tuple[Set[str], Set[str]]:
        """Fetch soft-deleted IDs from PostgreSQL."""
        if not self.pg_config:
            return set(), set()
            
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            # Standardize key for psycopg2
            pg_args = self.pg_config.copy()
            if 'database' in pg_args and 'dbname' not in pg_args:
                pg_args['dbname'] = pg_args.pop('database')
            
            conn = psycopg2.connect(**pg_args)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT item_id, item_type FROM control.curation WHERE action = 'soft_delete'")
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            
            threads = {str(r['item_id']) for r in rows if r['item_type'] == 'thread'}
            posts = {str(r['item_id']) for r in rows if r['item_type'] == 'post'}
            return threads, posts
        except Exception as e:
            print(f"Postgres curation lookup failed: {e}")
            return set(), set()

    def _get_soft_deleted_ids(self) -> Tuple[Set[str], Set[str]]:
        """Fetch soft-deleted IDs from MySQL."""
        if not self.db_config:
            return set(), set()
            
        try:
            import mysql.connector
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT item_id, item_type FROM imageboard_curation WHERE action = 'soft_delete'")
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            
            threads = {str(r['item_id']) for r in rows if r['item_type'] == 'thread'}
            posts = {str(r['item_id']) for r in rows if r['item_type'] == 'post'}
            return threads, posts
        except Exception as e:
            print(f"Curation lookup failed: {e}")
            return set(), set()

    def search(self, query: str, board: Optional[str] = None) -> pd.DataFrame:
        """Perform a smart search across text and IDs."""
        df = self.load_data()
        if df.empty: return df
        
        filtered = df[df['board'] == board] if board else df
        q = query.strip().lower()
        if not q: return filtered

        # 1. Fuzzy ID / URL / Path search
        id_match = re.search(r'(\d+)', q)
        id_mask = pd.Series(False, index=filtered.index)
        if id_match:
            target = id_match.group(1)
            if len(target) > 5:
                # Robust matching for large IDs that might be floats in pandas
                id_mask = filtered['image_id'].astype(str).str.contains(target, na=False) | \
                          filtered['image_id'].fillna(0).apply(lambda x: f"{int(x)}" if x > 0 else "").str.contains(target, na=False) | \
                          filtered['post_no'].astype(str).str.contains(target, na=False)
        
        # 2. Text search
        text_mask = filtered['comment'].str.lower().str.contains(q, na=False) | \
                    filtered['subject'].str.lower().str.contains(q, na=False) | \
                    filtered['thread_subject'].str.lower().str.contains(q, na=False)

        return filtered[id_mask | text_mask]


    def find_by_image(self, image_content: bytes) -> pd.DataFrame:
        """Reverse image lookup by SHA256 hash."""
        df = self.load_data()
        if df.empty: return df
        
        target_hash = hashlib.sha256(image_content).hexdigest()
        # image_sha256 in our dataset is just the hash part
        return df[df['image_sha256'] == target_hash]

    def find_by_image_url(self, url: str) -> pd.DataFrame:
        """Download image from URL and perform reverse lookup."""
        try:
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                return self.find_by_image(resp.content)
        except Exception as e:
            print(f"Failed to download image for lookup: {e}")
        return pd.DataFrame()
