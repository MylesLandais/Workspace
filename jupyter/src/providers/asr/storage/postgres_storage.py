"""
PostgreSQL storage for ASR evaluation results.
"""

import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import os

from asr_evaluation.core.interfaces import EvaluationResult


class PostgreSQLStorage:
    """PostgreSQL storage for evaluation results and experiments."""
    
    def __init__(self, 
                 host: str = "localhost",
                 port: int = 5432,
                 database: str = "jupyter-dev",
                 user: str = "postgres", 
                 password: str = "password"):
        """
        Initialize PostgreSQL connection.
        
        Args:
            host: Database host
            port: Database port  
            database: Database name
            user: Database user
            password: Database password
        """
        self.connection_params = {
            "host": host,
            "port": port,
            "database": database,
            "user": user,
            "password": password
        }
        self._connection = None
        self._ensure_tables()
    
    def _get_connection(self):
        """Get database connection, creating if needed."""
        if self._connection is None or self._connection.closed:
            self._connection = psycopg2.connect(**self.connection_params)
        return self._connection
    
    def _ensure_tables(self):
        """Create tables if they don't exist."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Create experiments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS asr_experiments (
                experiment_id UUID PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                dataset_name VARCHAR(255),
                audio_file VARCHAR(500),
                reference_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata JSONB
            )
        """)
        
        # Create responses table for model outputs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS asr_responses (
                response_id UUID PRIMARY KEY,
                experiment_id UUID REFERENCES asr_experiments(experiment_id),
                model_name VARCHAR(255) NOT NULL,
                model_version VARCHAR(100),
                model_type VARCHAR(50),
                
                -- Transcription results
                predicted_text TEXT,
                confidence_scores JSONB,
                
                -- Performance metrics
                wer FLOAT,
                cer FLOAT,
                bleu_score FLOAT,
                processing_time FLOAT,
                
                -- Audio metadata
                audio_duration FLOAT,
                audio_file VARCHAR(500),
                
                -- Model metadata
                device VARCHAR(50),
                model_parameters JSONB,
                
                -- Timestamps
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Additional metadata
                metadata JSONB
            )
        """)
        
        # Create indexes for better query performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_responses_experiment 
            ON asr_responses(experiment_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_responses_model 
            ON asr_responses(model_name, model_version)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_responses_wer 
            ON asr_responses(wer)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_responses_created 
            ON asr_responses(created_at)
        """)
        
        conn.commit()
        cursor.close()
    
    def create_experiment(self, 
                         name: str,
                         description: str = "",
                         dataset_name: str = "",
                         audio_file: str = "",
                         reference_text: str = "",
                         metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new experiment record.
        
        Args:
            name: Experiment name
            description: Experiment description
            dataset_name: Name of the dataset used
            audio_file: Path to audio file
            reference_text: Reference transcription
            metadata: Additional metadata
            
        Returns:
            experiment_id: UUID of created experiment
        """
        experiment_id = str(uuid.uuid4())
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO asr_experiments 
            (experiment_id, name, description, dataset_name, audio_file, reference_text, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            experiment_id,
            name,
            description,
            dataset_name,
            audio_file,
            reference_text,
            json.dumps(metadata) if metadata else None
        ))
        
        conn.commit()
        cursor.close()
        
        return experiment_id
    
    def save_response(self,
                     experiment_id: str,
                     model_name: str,
                     model_version: str,
                     model_type: str,
                     predicted_text: str,
                     wer: float,
                     cer: float,
                     processing_time: float,
                     audio_duration: float,
                     audio_file: str,
                     device: str = "",
                     confidence_scores: Optional[List[float]] = None,
                     bleu_score: Optional[float] = None,
                     model_parameters: Optional[Dict[str, Any]] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Save model response/transcription result.
        
        Returns:
            response_id: UUID of created response
        """
        response_id = str(uuid.uuid4())
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO asr_responses 
            (response_id, experiment_id, model_name, model_version, model_type,
             predicted_text, confidence_scores, wer, cer, bleu_score, processing_time,
             audio_duration, audio_file, device, model_parameters, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            response_id,
            experiment_id,
            model_name,
            model_version,
            model_type,
            predicted_text,
            json.dumps(confidence_scores) if confidence_scores else None,
            wer,
            cer,
            bleu_score,
            processing_time,
            audio_duration,
            audio_file,
            device,
            json.dumps(model_parameters) if model_parameters else None,
            json.dumps(metadata) if metadata else None
        ))
        
        conn.commit()
        cursor.close()
        
        return response_id
    
    def get_leaderboard(self, 
                       experiment_id: Optional[str] = None,
                       dataset_name: Optional[str] = None,
                       limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get leaderboard data sorted by WER.
        
        Args:
            experiment_id: Filter by specific experiment
            dataset_name: Filter by dataset name
            limit: Maximum number of results
            
        Returns:
            List of leaderboard entries
        """
        conn = self._get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT 
                r.model_name,
                r.model_version,
                r.model_type,
                AVG(r.wer) as avg_wer,
                AVG(r.cer) as avg_cer,
                AVG(r.processing_time) as avg_processing_time,
                COUNT(*) as evaluation_count,
                MIN(r.wer) as best_wer,
                MAX(r.created_at) as last_evaluation
            FROM asr_responses r
            JOIN asr_experiments e ON r.experiment_id = e.experiment_id
            WHERE 1=1
        """
        
        params = []
        
        if experiment_id:
            query += " AND r.experiment_id = %s"
            params.append(experiment_id)
        
        if dataset_name:
            query += " AND e.dataset_name = %s"
            params.append(dataset_name)
        
        query += """
            GROUP BY r.model_name, r.model_version, r.model_type
            ORDER BY avg_wer ASC
            LIMIT %s
        """
        params.append(limit)
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        cursor.close()
        
        return [dict(row) for row in results]
    
    def get_experiment_results(self, experiment_id: str) -> List[Dict[str, Any]]:
        """Get all results for a specific experiment."""
        conn = self._get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT 
                r.*,
                e.name as experiment_name,
                e.dataset_name,
                e.reference_text
            FROM asr_responses r
            JOIN asr_experiments e ON r.experiment_id = e.experiment_id
            WHERE r.experiment_id = %s
            ORDER BY r.wer ASC
        """, (experiment_id,))
        
        results = cursor.fetchall()
        cursor.close()
        
        return [dict(row) for row in results]
    
    def get_model_history(self, model_name: str, model_version: str = None) -> List[Dict[str, Any]]:
        """Get evaluation history for a specific model."""
        conn = self._get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT 
                r.*,
                e.name as experiment_name,
                e.dataset_name
            FROM asr_responses r
            JOIN asr_experiments e ON r.experiment_id = e.experiment_id
            WHERE r.model_name = %s
        """
        
        params = [model_name]
        
        if model_version:
            query += " AND r.model_version = %s"
            params.append(model_version)
        
        query += " ORDER BY r.created_at DESC"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        cursor.close()
        
        return [dict(row) for row in results]
    
    def get_dataset_stats(self, dataset_name: str) -> Dict[str, Any]:
        """Get statistics for a specific dataset."""
        conn = self._get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT r.model_name) as unique_models,
                COUNT(*) as total_evaluations,
                AVG(r.wer) as avg_wer,
                MIN(r.wer) as best_wer,
                MAX(r.wer) as worst_wer,
                AVG(r.processing_time) as avg_processing_time
            FROM asr_responses r
            JOIN asr_experiments e ON r.experiment_id = e.experiment_id
            WHERE e.dataset_name = %s
        """, (dataset_name,))
        
        result = cursor.fetchone()
        cursor.close()
        
        return dict(result) if result else {}
    
    def close(self):
        """Close database connection."""
        if self._connection and not self._connection.closed:
            self._connection.close()