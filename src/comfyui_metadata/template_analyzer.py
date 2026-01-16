"""
Template Analyzer for ComfyUI Prompts

Analyzes prompt templates for consistency, token impact, and redundancy.
"""

import re
from typing import Dict, List, Tuple, Optional
from collections import Counter
import pandas as pd


class TemplateAnalyzer:
    """Analyzes prompt templates and token usage patterns."""

    def __init__(self):
        """Initialize the template analyzer."""
        pass

    def _tokenize_prompt(self, prompt: str) -> List[str]:
        """
        Tokenize a prompt into words and phrases.

        Args:
            prompt: Prompt text

        Returns:
            List of tokens (words and common phrases)
        """
        if not prompt:
            return []
        
        # Simple tokenization: split by common separators
        # Split by commas, periods, and whitespace
        tokens = re.split(r'[,\s\.]+', prompt.lower())
        # Remove empty strings and very short tokens
        tokens = [t.strip() for t in tokens if len(t.strip()) > 2]
        
        return tokens

    def find_common_base(self, shay_df: pd.DataFrame, lexie_df: pd.DataFrame) -> str:
        """
        Identify shared template strings between Shay and Lexie prompts.

        Args:
            shay_df: DataFrame with Shay prompts (must have 'template' column)
            lexie_df: DataFrame with Lexie prompts (must have 'template' column)

        Returns:
            Common base template string
        """
        if 'template' not in shay_df.columns or 'template' not in lexie_df.columns:
            return ""
        
        # Get all templates
        shay_templates = shay_df['template'].dropna().tolist()
        lexie_templates = lexie_df['template'].dropna().tolist()
        
        if not shay_templates or not lexie_templates:
            return ""
        
        # Tokenize all templates
        shay_tokens = []
        for template in shay_templates:
            shay_tokens.extend(self._tokenize_prompt(template))
        
        lexie_tokens = []
        for template in lexie_templates:
            lexie_tokens.extend(self._tokenize_prompt(template))
        
        # Find common tokens
        shay_counter = Counter(shay_tokens)
        lexie_counter = Counter(lexie_tokens)
        
        # Calculate frequency for each token
        total_shay = len(shay_tokens)
        total_lexie = len(lexie_tokens)
        
        common_tokens = []
        for token in set(shay_tokens) & set(lexie_tokens):
            shay_freq = shay_counter[token] / total_shay if total_shay > 0 else 0
            lexie_freq = lexie_counter[token] / total_lexie if total_lexie > 0 else 0
            # Token must appear in at least 30% of both clusters
            if shay_freq >= 0.3 and lexie_freq >= 0.3:
                common_tokens.append((token, (shay_freq + lexie_freq) / 2))
        
        # Sort by average frequency
        common_tokens.sort(key=lambda x: x[1], reverse=True)
        
        # Return top 20 common tokens as base template
        base_tokens = [token for token, _ in common_tokens[:20]]
        return ', '.join(base_tokens)

    def analyze_token_impact(
        self, 
        df: pd.DataFrame, 
        cluster_col: str = 'character_cluster'
    ) -> pd.DataFrame:
        """
        Identify keywords unique to successful outputs per cluster.

        Args:
            df: DataFrame with prompts and cluster labels
            cluster_col: Column name containing cluster labels

        Returns:
            DataFrame with token impact analysis
        """
        if cluster_col not in df.columns or 'positive_prompt' not in df.columns:
            return pd.DataFrame()
        
        # Separate by cluster
        clusters = df[cluster_col].unique()
        cluster_tokens = {}
        
        for cluster in clusters:
            cluster_df = df[df[cluster_col] == cluster]
            all_tokens = []
            for prompt in cluster_df['positive_prompt'].dropna():
                all_tokens.extend(self._tokenize_prompt(str(prompt)))
            cluster_tokens[cluster] = Counter(all_tokens)
        
        # Calculate token frequencies per cluster
        result_data = []
        all_unique_tokens = set()
        for tokens in cluster_tokens.values():
            all_unique_tokens.update(tokens.keys())
        
        total_counts = {cluster: sum(tokens.values()) for cluster, tokens in cluster_tokens.items()}
        
        for token in all_unique_tokens:
            row = {'token': token}
            max_freq = 0
            max_cluster = None
            
            for cluster in clusters:
                count = cluster_tokens[cluster].get(token, 0)
                total = total_counts[cluster] if total_counts[cluster] > 0 else 1
                freq = count / total
                row[f'{cluster}_frequency'] = freq
                
                if freq > max_freq:
                    max_freq = freq
                    max_cluster = cluster
            
            # Determine if token is unique to a cluster
            # Unique if frequency in one cluster is >2x the average of others
            other_freqs = [row[f'{c}_frequency'] for c in clusters if c != max_cluster]
            avg_other = sum(other_freqs) / len(other_freqs) if other_freqs else 0
            
            if max_freq > 0.1 and max_freq > 2 * avg_other:  # At least 10% in one, 2x others
                row['unique_to'] = max_cluster
            else:
                row['unique_to'] = 'shared'
            
            result_data.append(row)
        
        result_df = pd.DataFrame(result_data)
        
        # Sort by maximum frequency
        freq_cols = [f'{c}_frequency' for c in clusters]
        if freq_cols:
            result_df['max_frequency'] = result_df[freq_cols].max(axis=1)
            result_df = result_df.sort_values('max_frequency', ascending=False)
        
        return result_df

    def find_universal_negative(self, df: pd.DataFrame) -> str:
        """
        Identify redundant/universal negative prompts.

        Args:
            df: DataFrame with negative prompts

        Returns:
            Universal negative prompt string
        """
        if 'negative_prompt' not in df.columns:
            return ""
        
        negative_prompts = df['negative_prompt'].dropna().tolist()
        if not negative_prompts:
            return ""
        
        # Tokenize all negative prompts
        all_tokens = []
        for prompt in negative_prompts:
            all_tokens.extend(self._tokenize_prompt(str(prompt)))
        
        # Count token frequencies
        token_counter = Counter(all_tokens)
        total = len(all_tokens)
        
        # Find tokens appearing in 90%+ of prompts
        universal_tokens = []
        for token, count in token_counter.items():
            # Estimate: token appears in prompt if count >= num_prompts * 0.9
            # Rough heuristic: if token frequency is high enough
            freq = count / total
            # If token appears very frequently, it's likely universal
            if freq >= 0.15:  # Appears in roughly 90% if each prompt has ~6-7 tokens
                universal_tokens.append((token, freq))
        
        # Sort by frequency
        universal_tokens.sort(key=lambda x: x[1], reverse=True)
        
        # Return top tokens as universal negative prompt
        universal_list = [token for token, _ in universal_tokens[:30]]
        return ', '.join(universal_list)

    def identify_redundant_tokens(
        self, 
        df: pd.DataFrame, 
        threshold: float = 0.9
    ) -> pd.DataFrame:
        """
        Find tokens appearing in threshold%+ of prompts.

        Args:
            df: DataFrame with prompts
            threshold: Minimum frequency threshold (default 0.9)

        Returns:
            DataFrame with redundant tokens and statistics
        """
        if 'positive_prompt' not in df.columns:
            return pd.DataFrame()
        
        prompts = df['positive_prompt'].dropna().tolist()
        if not prompts:
            return pd.DataFrame()
        
        # Tokenize all prompts
        all_tokens = []
        prompt_token_sets = []
        for prompt in prompts:
            tokens = self._tokenize_prompt(str(prompt))
            all_tokens.extend(tokens)
            prompt_token_sets.append(set(tokens))
        
        # Count how many prompts contain each token
        token_counter = Counter(all_tokens)
        token_appearance = Counter()
        for token_set in prompt_token_sets:
            for token in token_set:
                token_appearance[token] += 1
        
        total_prompts = len(prompts)
        result_data = []
        
        for token, appearance_count in token_appearance.items():
            frequency = appearance_count / total_prompts if total_prompts > 0 else 0
            
            if frequency >= threshold:
                result_data.append({
                    'token': token,
                    'frequency': frequency,
                    'appearance_count': appearance_count,
                    'total_count': token_counter[token],
                    'avg_per_prompt': token_counter[token] / appearance_count if appearance_count > 0 else 0
                })
        
        result_df = pd.DataFrame(result_data)
        result_df = result_df.sort_values('frequency', ascending=False)
        
        return result_df









