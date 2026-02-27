"""
Enhanced Analyzer for ComfyUI Metadata

Provides cluster-aware analysis methods for character-specific data.
"""

import pandas as pd
from typing import Dict, Any
from collections import Counter


class MetadataAnalyzer:
    """Analyzes ComfyUI metadata with cluster-aware methods."""

    def __init__(self):
        """Initialize the analyzer."""
        pass

    def word_frequency_analysis_by_cluster(
        self,
        df: pd.DataFrame,
        cluster_col: str = 'character_cluster',
        prompt_col: str = 'positive_prompt'
    ) -> pd.DataFrame:
        """
        Analyze word frequencies per character cluster.

        Args:
            df: DataFrame with prompts and cluster labels
            cluster_col: Column name containing cluster labels
            prompt_col: Column name containing prompt text

        Returns:
            DataFrame with token frequencies per cluster
        """
        if cluster_col not in df.columns or prompt_col not in df.columns:
            return pd.DataFrame()
        
        clusters = df[cluster_col].unique()
        result_data = []
        
        for cluster in clusters:
            cluster_df = df[df[cluster_col] == cluster]
            all_words = []
            
            for prompt in cluster_df[prompt_col].dropna():
                words = str(prompt).lower().split()
                all_words.extend([w.strip('.,!?;:()[]{}') for w in words if len(w.strip()) > 2])
            
            word_counter = Counter(all_words)
            total_words = len(all_words)
            
            for word, count in word_counter.most_common(50):  # Top 50 per cluster
                result_data.append({
                    'cluster': cluster,
                    'word': word,
                    'count': count,
                    'frequency': count / total_words if total_words > 0 else 0
                })
        
        return pd.DataFrame(result_data)

    def model_usage_by_cluster(
        self,
        df: pd.DataFrame,
        cluster_col: str = 'character_cluster',
        model_col: str = 'model_name'
    ) -> pd.DataFrame:
        """
        Analyze model distribution per character cluster.

        Args:
            df: DataFrame with model and cluster information
            cluster_col: Column name containing cluster labels
            model_col: Column name containing model names

        Returns:
            DataFrame with model usage statistics per cluster
        """
        if cluster_col not in df.columns or model_col not in df.columns:
            return pd.DataFrame()
        
        return df.groupby([cluster_col, model_col]).size().reset_index(name='count')

    def prompt_length_by_cluster(
        self,
        df: pd.DataFrame,
        cluster_col: str = 'character_cluster',
        prompt_col: str = 'positive_prompt'
    ) -> pd.DataFrame:
        """
        Analyze prompt length statistics per cluster.

        Args:
            df: DataFrame with prompts and cluster labels
            cluster_col: Column name containing cluster labels
            prompt_col: Column name containing prompt text

        Returns:
            DataFrame with length statistics per cluster
        """
        if cluster_col not in df.columns or prompt_col not in df.columns:
            return pd.DataFrame()
        
        df_with_length = df.copy()
        df_with_length['prompt_length'] = df_with_length[prompt_col].apply(
            lambda x: len(str(x)) if pd.notna(x) else 0
        )
        df_with_length['word_count'] = df_with_length[prompt_col].apply(
            lambda x: len(str(x).split()) if pd.notna(x) else 0
        )
        
        stats = df_with_length.groupby(cluster_col).agg({
            'prompt_length': ['mean', 'median', 'std', 'min', 'max'],
            'word_count': ['mean', 'median', 'std', 'min', 'max']
        }).reset_index()
        
        # Flatten column names
        stats.columns = ['_'.join(col).strip('_') if col[1] else col[0] 
                        for col in stats.columns.values]
        
        return stats

    def optimal_settings_by_cluster(
        self,
        df: pd.DataFrame,
        cluster_col: str = 'character_cluster'
    ) -> pd.DataFrame:
        """
        Calculate optimal settings (CFG, sampler, steps) per cluster.

        Args:
            df: DataFrame with settings and cluster information
            cluster_col: Column name containing cluster labels

        Returns:
            DataFrame with optimal settings recommendations
        """
        if cluster_col not in df.columns:
            return pd.DataFrame()
        
        numeric_cols = ['cfg', 'steps']
        categorical_cols = ['sampler_name', 'scheduler']
        
        result_data = []
        clusters = df[cluster_col].unique()
        
        for cluster in clusters:
            cluster_df = df[df[cluster_col] == cluster]
            
            row = {'cluster': cluster}
            
            # Average for numeric columns
            for col in numeric_cols:
                if col in cluster_df.columns:
                    values = cluster_df[col].dropna()
                    if len(values) > 0:
                        row[f'{col}_mean'] = values.mean()
                        row[f'{col}_median'] = values.median()
                        row[f'{col}_std'] = values.std()
            
            # Most common for categorical columns
            for col in categorical_cols:
                if col in cluster_df.columns:
                    values = cluster_df[col].dropna()
                    if len(values) > 0:
                        most_common = values.mode()
                        row[f'{col}_most_common'] = most_common.iloc[0] if len(most_common) > 0 else None
            
            result_data.append(row)
        
        return pd.DataFrame(result_data)









