"""
Prompt Book Generator for ComfyUI Analysis

Generates character-specific prompt Bibles and updates markdown files
with discovered insights.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd

from .template_analyzer import TemplateAnalyzer
from .analyzer import MetadataAnalyzer


class PromptBookGenerator:
    """Generates prompt books and updates markdown documentation."""

    def __init__(self):
        """Initialize the prompt book generator."""
        self.template_analyzer = TemplateAnalyzer()
        self.metadata_analyzer = MetadataAnalyzer()

    def generate_character_bible(
        self,
        df: pd.DataFrame,
        character_name: str,
        output_path: Optional[Path] = None,
        top_n: int = 20
    ) -> str:
        """
        Generate character-specific "Bible" markdown content.

        Args:
            df: DataFrame filtered for specific character
            character_name: Name of character (e.g., "Shay", "Lexie")
            output_path: Optional path to write markdown file
            top_n: Number of top prompts to include

        Returns:
            Markdown content string
        """
        character_lower = character_name.lower()
        
        # Filter for character cluster
        character_df = df[df['character_cluster'] == character_lower].copy()
        
        if character_df.empty:
            return f"# {character_name} Prompt Bible\n\nNo prompts found for {character_name}.\n"
        
        content_lines = [f"# {character_name} Prompt Bible"]
        content_lines.append("")
        content_lines.append("## Discovered Optimal Prompts")
        content_lines.append("")
        
        # Get top prompts (by some metric - here just by uniqueness or use full prompts)
        if 'positive_prompt' in character_df.columns:
            top_prompts = character_df['positive_prompt'].dropna().unique()[:top_n]
            for i, prompt in enumerate(top_prompts, 1):
                content_lines.append(f"{i}. {prompt}")
                content_lines.append("")
        
        # Optimal Settings
        content_lines.append("## Optimal Settings")
        content_lines.append("")
        optimal_settings = self.metadata_analyzer.optimal_settings_by_cluster(character_df)
        if not optimal_settings.empty and 'cluster' in optimal_settings.columns:
            for col in optimal_settings.columns:
                if col != 'cluster':
                    value = optimal_settings[col].iloc[0]
                    if pd.notna(value):
                        content_lines.append(f"- {col.replace('_', ' ').title()}: {value}")
        content_lines.append("")
        
        # Unique Token Analysis
        content_lines.append("## Unique Token Analysis")
        content_lines.append("")
        token_impact = self.template_analyzer.analyze_token_impact(df, cluster_col='character_cluster')
        if not token_impact.empty:
            unique_tokens = token_impact[token_impact.get('unique_to', '') == character_lower]
            if not unique_tokens.empty:
                for _, row in unique_tokens.head(20).iterrows():
                    token = row.get('token', '')
                    freq_col = f'{character_lower}_frequency'
                    freq = row.get(freq_col, 0)
                    if token and freq > 0:
                        content_lines.append(f"- `{token}`: {freq:.2%}")
            else:
                content_lines.append(f"No strongly unique tokens found for {character_name}.")
        content_lines.append("")
        
        # Template Variations
        content_lines.append("## Template Variations")
        content_lines.append("")
        if 'template' in character_df.columns:
            templates = character_df['template'].dropna().unique()
            for template in templates[:10]:
                if template:
                    content_lines.append(f"- {template}")
        content_lines.append("")
        
        content = "\n".join(content_lines)
        
        # Write to file if path provided
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content, encoding='utf-8')
        
        return content

    def generate_universal_assets(
        self,
        df: pd.DataFrame,
        output_path: Optional[Path] = None
    ) -> str:
        """
        Generate Universal Assets section.

        Args:
            df: Full DataFrame with all prompts
            output_path: Optional path to write markdown file

        Returns:
            Markdown content string
        """
        content_lines = ["# Universal Assets"]
        content_lines.append("")
        content_lines.append("Standardized templates and recommendations for all character prompts.")
        content_lines.append("")
        
        # Universal Negative Prompt
        content_lines.append("## Universal Negative Prompt")
        content_lines.append("")
        universal_negative = self.template_analyzer.find_universal_negative(df)
        if universal_negative:
            content_lines.append(f"```")
            content_lines.append(universal_negative)
            content_lines.append("```")
        else:
            content_lines.append("No universal negative prompt identified.")
        content_lines.append("")
        
        # Standardized Lighting Templates
        content_lines.append("## Standardized Lighting Templates")
        content_lines.append("")
        if 'template' in df.columns:
            # Extract lighting-related templates
            lighting_templates = df['template'].dropna()
            lighting_keywords = ['light', 'sun', 'moon', 'neon', 'lamp', 'bright', 'dark', 'shadow']
            lighting_matches = []
            for template in lighting_templates:
                template_lower = str(template).lower()
                if any(kw in template_lower for kw in lighting_keywords):
                    lighting_matches.append(template)
            
            for template in list(set(lighting_matches))[:10]:
                content_lines.append(f"- {template}")
        content_lines.append("")
        
        # Quality/Technical Token Recommendations
        content_lines.append("## Quality/Technical Token Recommendations")
        content_lines.append("")
        redundant_tokens = self.template_analyzer.identify_redundant_tokens(df, threshold=0.9)
        if not redundant_tokens.empty:
            content_lines.append("Tokens appearing in 90%+ of prompts (candidates for Style Model/LoRA):")
            content_lines.append("")
            for _, row in redundant_tokens.head(20).iterrows():
                token = row.get('token', '')
                freq = row.get('frequency', 0)
                if token:
                    content_lines.append(f"- `{token}`: {freq:.1%}")
        content_lines.append("")
        
        content = "\n".join(content_lines)
        
        # Write to file if path provided
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content, encoding='utf-8')
        
        return content

    def update_existing_markdown(
        self,
        shay_df: pd.DataFrame,
        lexie_df: pd.DataFrame,
        universal_df: pd.DataFrame,
        insights: Dict[str, Any],
        base_path: Path = Path("data/Prompts")
    ) -> None:
        """
        Update existing markdown files with discovered insights.

        Args:
            shay_df: DataFrame with Shay prompts
            lexie_df: DataFrame with Lexie prompts
            universal_df: DataFrame with Universal prompts
            insights: Dictionary with additional insights
            base_path: Base path for Prompts directory
        """
        base_path = Path(base_path)
        
        # Update Subject-Shay.md
        shay_path = base_path / "Subject-Shay.md"
        if shay_path.exists():
            self._append_insights_section(
                shay_path,
                shay_df,
                "Shay",
                insights.get('shay_insights', {})
            )
        
        # Create/update Subject-Lexie.md
        lexie_path = base_path / "Subject-Lexie.md"
        self._create_or_update_lexie_file(lexie_path, lexie_df, insights.get('lexie_insights', {}))
        
        # Update index.md
        index_path = base_path / "index.md"
        if index_path.exists():
            self._update_index_file(index_path, insights)

    def _append_insights_section(
        self,
        file_path: Path,
        df: pd.DataFrame,
        character_name: str,
        insights: Dict[str, Any]
    ) -> None:
        """Append discovered insights section to existing markdown file."""
        if df.empty:
            return
        
        content = file_path.read_text(encoding='utf-8')
        
        # Check if insights section already exists
        if "## Discovered Insights" in content:
            # Remove existing insights section
            content = re.sub(r'\n## Discovered Insights.*', '', content, flags=re.DOTALL)
        
        # Generate new insights section
        insights_lines = ["", "---", "", "## Discovered Insights"]
        insights_lines.append("")
        insights_lines.append("### Optimal Prompt Combinations")
        insights_lines.append("")
        
        if 'positive_prompt' in df.columns:
            top_prompts = df['positive_prompt'].dropna().unique()[:10]
            for i, prompt in enumerate(top_prompts, 1):
                insights_lines.append(f"{i}. {prompt}")
        
        insights_lines.append("")
        insights_lines.append("### Settings Recommendations")
        insights_lines.append("")
        optimal_settings = self.metadata_analyzer.optimal_settings_by_cluster(df)
        if not optimal_settings.empty:
            for col in optimal_settings.columns:
                if col != 'cluster':
                    value = optimal_settings[col].iloc[0]
                    if pd.notna(value):
                        insights_lines.append(f"- {col.replace('_', ' ').title()}: {value}")
        
        insights_section = "\n".join(insights_lines)
        
        # Append to file
        new_content = content.rstrip() + "\n" + insights_section + "\n"
        file_path.write_text(new_content, encoding='utf-8')

    def _create_or_update_lexie_file(
        self,
        file_path: Path,
        df: pd.DataFrame,
        insights: Dict[str, Any]
    ) -> None:
        """Create or update Subject-Lexie.md file."""
        if file_path.exists():
            # Update existing file
            self._append_insights_section(file_path, df, "Lexie", insights)
        else:
            # Create new file with discovered descriptors
            content_lines = ["# Pin & Consistency Lock"]
            content_lines.append("")
            content_lines.append("Character descriptors discovered from image analysis.")
            content_lines.append("")
            
            # Extract common descriptors from prompts
            if 'positive_prompt' in df.columns and not df.empty:
                content_lines.append("## Discovered Descriptors")
                content_lines.append("")
                content_lines.append("(Auto-generated from image metadata analysis)")
                content_lines.append("")
            
            # Add insights section
            insights_lines = ["", "---", "", "## Discovered Insights"]
            insights_lines.append("")
            
            if 'positive_prompt' in df.columns:
                insights_lines.append("### Optimal Prompt Combinations")
                insights_lines.append("")
                top_prompts = df['positive_prompt'].dropna().unique()[:10]
                for i, prompt in enumerate(top_prompts, 1):
                    insights_lines.append(f"{i}. {prompt}")
            
            content = "\n".join(content_lines + insights_lines) + "\n"
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding='utf-8')

    def _update_index_file(self, index_path: Path, insights: Dict[str, Any]) -> None:
        """Update index.md with new sections."""
        if not index_path.exists():
            return
        
        content = index_path.read_text(encoding='utf-8')
        
        # Add reference to Universal Assets if not present
        if "Universal-Assets.md" not in content:
            # Find a good place to insert (after existing sections)
            if "## " in content:
                # Insert before last section or at end
                content = content.rstrip() + "\n\n## Universal Assets\n\nSee [Universal Assets](Universal-Assets.md) for standardized templates and recommendations.\n"
                index_path.write_text(content, encoding='utf-8')

    def generate_insights_report(
        self,
        df: pd.DataFrame,
        output_path: Optional[Path] = None
    ) -> str:
        """
        Generate actionable insights report.

        Args:
            df: Full DataFrame with all analyzed data
            output_path: Optional path to write report

        Returns:
            Markdown report content
        """
        content_lines = ["# ComfyUI Prompt Analysis - Insights Report"]
        content_lines.append("")
        
        # Template Consistency
        content_lines.append("## Template Consistency Analysis")
        content_lines.append("")
        shay_df = df[df['character_cluster'] == 'shay']
        lexie_df = df[df['character_cluster'] == 'lexie']
        if not shay_df.empty and not lexie_df.empty:
            common_base = self.template_analyzer.find_common_base(shay_df, lexie_df)
            content_lines.append("### Common Base Template")
            content_lines.append("")
            if common_base:
                content_lines.append(f"Shared template elements between Shay and Lexie:")
                content_lines.append(f"```")
                content_lines.append(common_base)
                content_lines.append(f"```")
            else:
                content_lines.append("No significant common base template found.")
        content_lines.append("")
        
        # Optimal Settings per Cluster
        content_lines.append("## Optimal Settings by Cluster")
        content_lines.append("")
        optimal_settings = self.metadata_analyzer.optimal_settings_by_cluster(df)
        if not optimal_settings.empty:
            for _, row in optimal_settings.iterrows():
                cluster = row.get('cluster', 'unknown')
                content_lines.append(f"### {cluster.capitalize()}")
                content_lines.append("")
                for col, value in row.items():
                    if col != 'cluster' and pd.notna(value):
                        content_lines.append(f"- {col.replace('_', ' ').title()}: {value}")
                content_lines.append("")
        
        # Suggested Prompt Templates
        content_lines.append("## Suggested Prompt Templates")
        content_lines.append("")
        content_lines.append("(See individual character Bibles for detailed templates)")
        content_lines.append("")
        
        content = "\n".join(content_lines)
        
        # Write to file if path provided
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content, encoding='utf-8')
        
        return content

