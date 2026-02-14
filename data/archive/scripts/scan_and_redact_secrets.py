#!/usr/bin/env python3
"""
Secret Scanner and Redactor
Scans for common API keys, tokens, and secrets in the repository and redacts them.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple, Dict


# Common secret patterns
SECRET_PATTERNS = {
    'huggingface_token': r'hf_[A-Za-z0-9]{20,}',
    'openai_api_key': r'sk-[A-Za-z0-9]{20,}',
    'runpod_api_key': r'rpa_[A-Za-z0-9]{20,}',
    'aws_access_key': r'AKIA[A-Z0-9]{16}',
    'google_api_key': r'AIza[A-Za-z0-9]{35}',
    'github_token': r'gh[pousr]_[A-Za-z0-9]{36}',
    'generic_api_key': r'["\']?[A-Za-z0-9_-]*[aA][pP][iI][_-]?[kK][eE][yY]["\']?\s*[:=]\s*["\']?[A-Za-z0-9]{20,}["\']?',
    'generic_secret': r'["\']?[A-Za-z0-9_-]*[sS][eE][cC][rR][eE][tT]["\']?\s*[:=]\s*["\']?[A-Za-z0-9]{20,}["\']?',
    'generic_token': r'["\']?[A-Za-z0-9_-]*[tT][oO][kK][eE][nN]["\']?\s*[:=]\s*["\']?[A-Za-z0-9]{20,}["\']?',
}

# Files to exclude from scanning
EXCLUDE_PATTERNS = [
    r'\.git/',
    r'\.venv/',
    r'__pycache__/',
    r'node_modules/',
    r'\.pyc$',
    r'\.jpg$',
    r'\.png$',
    r'\.mp3$',
    r'\.mp4$',
    r'\.wav$',
    r'\.webm$',
    r'results/',
    r'\.cache/',
]

# File extensions to scan
SCAN_EXTENSIONS = [
    '.py', '.md', '.txt', '.json', '.yaml', '.yml', 
    '.sh', '.env', '.cfg', '.conf', '.ini', '.toml'
]


def should_exclude_file(file_path: str) -> bool:
    """Check if file should be excluded from scanning."""
    for pattern in EXCLUDE_PATTERNS:
        if re.search(pattern, file_path):
            return True
    return False


def scan_file_for_secrets(file_path: Path) -> List[Tuple[str, int, str, str]]:
    """
    Scan a file for secrets.
    
    Returns:
        List of tuples: (secret_type, line_number, line_content, matched_secret)
    """
    secrets_found = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        for line_num, line in enumerate(lines, 1):
            for secret_type, pattern in SECRET_PATTERNS.items():
                matches = re.finditer(pattern, line, re.IGNORECASE)
                for match in matches:
                    secrets_found.append((
                        secret_type,
                        line_num,
                        line.strip(),
                        match.group()
                    ))
    
    except Exception as e:
        print(f"Error scanning {file_path}: {e}")
    
    return secrets_found


def redact_secrets_in_file(file_path: Path, secrets: List[Tuple[str, int, str, str]], dry_run: bool = True) -> bool:
    """
    Redact secrets in a file.
    
    Args:
        file_path: Path to the file
        secrets: List of secrets found in the file
        dry_run: If True, only show what would be changed
        
    Returns:
        True if file was modified (or would be modified in dry run)
    """
    if not secrets:
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Group secrets by type for better redaction
        secrets_by_type = {}
        for secret_type, line_num, line_content, matched_secret in secrets:
            if secret_type not in secrets_by_type:
                secrets_by_type[secret_type] = []
            secrets_by_type[secret_type].append(matched_secret)
        
        # Redact each type of secret
        for secret_type, secret_list in secrets_by_type.items():
            for secret in secret_list:
                if secret_type == 'huggingface_token':
                    redacted = 'hf_' + 'X' * (len(secret) - 3)
                elif secret_type in ['openai_api_key', 'runpod_api_key']:
                    prefix = secret.split('_')[0] + '_'
                    redacted = prefix + 'X' * (len(secret) - len(prefix))
                else:
                    # Generic redaction
                    redacted = 'X' * len(secret)
                
                content = content.replace(secret, redacted + ' # REDACTED')
        
        if dry_run:
            if content != original_content:
                print(f"  Would redact secrets in: {file_path}")
                return True
        else:
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"  Redacted secrets in: {file_path}")
                return True
    
    except Exception as e:
        print(f"Error redacting secrets in {file_path}: {e}")
    
    return False


def scan_repository(root_path: str = '.', dry_run: bool = True) -> Dict[str, List]:
    """
    Scan entire repository for secrets.
    
    Args:
        root_path: Root directory to scan
        dry_run: If True, only report findings without making changes
        
    Returns:
        Dictionary with scan results
    """
    root = Path(root_path)
    all_secrets = {}
    files_scanned = 0
    files_with_secrets = 0
    
    print(f"Scanning repository: {root.absolute()}")
    print(f"Mode: {'DRY RUN' if dry_run else 'REDACT'}")
    print("-" * 60)
    
    for file_path in root.rglob('*'):
        if not file_path.is_file():
            continue
        
        # Check if file should be excluded
        relative_path = str(file_path.relative_to(root))
        if should_exclude_file(relative_path):
            continue
        
        # Check file extension
        if file_path.suffix not in SCAN_EXTENSIONS:
            continue
        
        files_scanned += 1
        secrets = scan_file_for_secrets(file_path)
        
        if secrets:
            files_with_secrets += 1
            all_secrets[str(file_path)] = secrets
            
            print(f"\nSECRETS FOUND in {relative_path}:")
            for secret_type, line_num, line_content, matched_secret in secrets:
                print(f"  Line {line_num}: {secret_type}")
                print(f"    Secret: {matched_secret}")
                print(f"    Context: {line_content[:100]}...")
            
            # Redact if not dry run
            redact_secrets_in_file(file_path, secrets, dry_run)
    
    print(f"\n" + "=" * 60)
    print(f"SCAN SUMMARY:")
    print(f"Files scanned: {files_scanned}")
    print(f"Files with secrets: {files_with_secrets}")
    print(f"Total secrets found: {sum(len(secrets) for secrets in all_secrets.values())}")
    
    if all_secrets and dry_run:
        print(f"\nTo redact secrets, run: python {sys.argv[0]} --redact")
    
    return all_secrets


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Scan and redact secrets in repository')
    parser.add_argument('--redact', action='store_true', 
                       help='Actually redact secrets (default is dry run)')
    parser.add_argument('--path', default='.', 
                       help='Path to scan (default: current directory)')
    
    args = parser.parse_args()
    
    # Scan repository
    secrets_found = scan_repository(args.path, dry_run=not args.redact)
    
    # Exit with error code if secrets found
    if secrets_found:
        print(f"\nWARNING: Secrets detected in repository!")
        if not args.redact:
            print("Run with --redact to automatically redact them.")
        sys.exit(1)
    else:
        print(f"\nSUCCESS: No secrets detected in repository.")
        sys.exit(0)


if __name__ == '__main__':
    main()