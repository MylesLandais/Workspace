#!/usr/bin/env python3
"""
Character Card V3 Extractor and Validator
Extracts and validates character card data from PNG files against the CCv3 specification.
"""

import json
import base64
import struct
import zlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import argparse


@dataclass
class ValidationResult:
    """Stores validation results for a character card"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    spec_version: Optionqal[str] = None
    card_name: Optional[str] = None


class PNGChunkReader:
    """Reads and extracts tEXt chunks from PNG files"""
    
    PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'
    
    @staticmethod
    def read_png_chunks(filepath: Path) -> Dict[str, bytes]:
        """Extract all tEXt chunks from a PNG file"""
        chunks = {}
        
        with open(filepath, 'rb') as f:
            # Verify PNG signature
            signature = f.read(8)
            if signature != PNGChunkReader.PNG_SIGNATURE:
                raise ValueError(f"Not a valid PNG file: {filepath}")
            
            # Read chunks
            while True:
                # Read chunk length
                length_bytes = f.read(4)
                if len(length_bytes) < 4:
                    break
                    
                length = struct.unpack('>I', length_bytes)[0]
                
                # Read chunk type
                chunk_type = f.read(4)
                if len(chunk_type) < 4:
                    break
                
                # Read chunk data
                chunk_data = f.read(length)
                
                # Read CRC (skip validation for simplicity)
                crc = f.read(4)
                
                # Store tEXt chunks
                if chunk_type == b'tEXt':
                    # Parse tEXt chunk: keyword\0text
                    null_pos = chunk_data.find(b'\x00')
                    if null_pos != -1:
                        keyword = chunk_data[:null_pos].decode('latin-1')
                        text = chunk_data[null_pos + 1:]
                        chunks[keyword] = text
                
                # Check for IEND chunk
                if chunk_type == b'IEND':
                    break
        
        return chunks


class CharacterCardV3Validator:
    """Validates Character Card V3 data against the specification"""
    
    REQUIRED_FIELDS = {
        'spec': str,
        'spec_version': str,
        'data': dict
    }
    
    REQUIRED_DATA_FIELDS = {
        'name': str,
        'description': str,
        'tags': list,
        'creator': str,
        'character_version': str,
        'mes_example': str,
        'extensions': dict,
        'system_prompt': str,
        'post_history_instructions': str,
        'first_mes': str,
        'alternate_greetings': list,
        'personality': str,
        'scenario': str,
        'creator_notes': str,
        'group_only_greetings': list
    }
    
    OPTIONAL_DATA_FIELDS = {
        'character_book': dict,
        'assets': list,
        'nickname': str,
        'creator_notes_multilingual': dict,
        'source': list,
        'creation_date': (int, float),
        'modification_date': (int, float)
    }
    
    @staticmethod
    def validate_card(card_data: Dict[str, Any]) -> ValidationResult:
        """Validate a character card against the V3 specification"""
        result = ValidationResult(is_valid=True)
        
        # Check top-level required fields
        for field, expected_type in CharacterCardV3Validator.REQUIRED_FIELDS.items():
            if field not in card_data:
                result.errors.append(f"Missing required field: '{field}'")
                result.is_valid = False
            elif not isinstance(card_data[field], expected_type):
                result.errors.append(
                    f"Field '{field}' should be {expected_type.__name__}, "
                    f"got {type(card_data[field]).__name__}"
                )
                result.is_valid = False
        
        # Check spec field
        if 'spec' in card_data and card_data['spec'] != 'chara_card_v3':
            result.errors.append(
                f"Invalid spec value: '{card_data['spec']}' "
                "(should be 'chara_card_v3')"
            )
            result.is_valid = False
        
        # Check spec_version
        if 'spec_version' in card_data:
            result.spec_version = card_data['spec_version']
            try:
                version = float(card_data['spec_version'])
                if version < 3.0:
                    result.warnings.append(
                        f"Spec version {card_data['spec_version']} is older than 3.0"
                    )
                elif version > 3.0:
                    result.warnings.append(
                        f"Spec version {card_data['spec_version']} is newer than 3.0, "
                        "some features may not be validated"
                    )
            except ValueError:
                result.errors.append(
                    f"Invalid spec_version format: '{card_data['spec_version']}'"
                )
                result.is_valid = False
        
        # Validate data section
        if 'data' in card_data and isinstance(card_data['data'], dict):
            data = card_data['data']
            
            # Store card name for reporting
            if 'name' in data:
                result.card_name = data['name']
            
            # Check required data fields
            for field, expected_type in CharacterCardV3Validator.REQUIRED_DATA_FIELDS.items():
                if field not in data:
                    result.errors.append(f"Missing required data field: '{field}'")
                    result.is_valid = False
                elif not isinstance(data[field], expected_type):
                    result.errors.append(
                        f"Data field '{field}' should be {expected_type.__name__}, "
                        f"got {type(data[field]).__name__}"
                    )
                    result.is_valid = False
            
            # Validate optional fields if present
            CharacterCardV3Validator._validate_optional_fields(data, result)
            CharacterCardV3Validator._validate_assets(data, result)
            CharacterCardV3Validator._validate_lorebook(data, result)
        
        return result
    
    @staticmethod
    def _validate_optional_fields(data: Dict[str, Any], result: ValidationResult):
        """Validate optional fields in the data section"""
        for field, expected_type in CharacterCardV3Validator.OPTIONAL_DATA_FIELDS.items():
            if field in data and data[field] is not None:
                if isinstance(expected_type, tuple):
                    if not isinstance(data[field], expected_type):
                        result.warnings.append(
                            f"Optional field '{field}' has unexpected type: "
                            f"{type(data[field]).__name__}"
                        )
                elif not isinstance(data[field], expected_type):
                    result.warnings.append(
                        f"Optional field '{field}' should be {expected_type.__name__}, "
                        f"got {type(data[field]).__name__}"
                    )
    
    @staticmethod
    def _validate_assets(data: Dict[str, Any], result: ValidationResult):
        """Validate assets array"""
        if 'assets' not in data or data['assets'] is None:
            return
        
        assets = data['assets']
        if not isinstance(assets, list):
            result.errors.append("'assets' should be an array")
            result.is_valid = False
            return
        
        main_icon_count = 0
        main_bg_count = 0
        
        for i, asset in enumerate(assets):
            if not isinstance(asset, dict):
                result.errors.append(f"Asset at index {i} should be an object")
                result.is_valid = False
                continue
            
            # Check required asset fields
            for field in ['type', 'uri', 'name', 'ext']:
                if field not in asset:
                    result.errors.append(
                        f"Asset at index {i} missing required field: '{field}'"
                    )
                    result.is_valid = False
            
            # Count main assets
            if asset.get('type') == 'icon' and asset.get('name') == 'main':
                main_icon_count += 1
            if asset.get('type') == 'background' and asset.get('name') == 'main':
                main_bg_count += 1
        
        # Check for multiple main icons
        icon_assets = [a for a in assets if a.get('type') == 'icon']
        if len(icon_assets) > 1 and main_icon_count != 1:
            result.errors.append(
                "When multiple icon assets exist, exactly one must have name='main'"
            )
            result.is_valid = False
        
        # Check for multiple main backgrounds
        if main_bg_count > 1:
            result.errors.append(
                "Only one background asset can have name='main'"
            )
            result.is_valid = False
    
    @staticmethod
    def _validate_lorebook(data: Dict[str, Any], result: ValidationResult):
        """Validate lorebook (character_book) structure"""
        if 'character_book' not in data or data['character_book'] is None:
            return
        
        lorebook = data['character_book']
        if not isinstance(lorebook, dict):
            result.errors.append("'character_book' should be an object")
            result.is_valid = False
            return
        
        # Check for entries array
        if 'entries' not in lorebook:
            result.errors.append("Lorebook missing required field: 'entries'")
            result.is_valid = False
            return
        
        if not isinstance(lorebook['entries'], list):
            result.errors.append("Lorebook 'entries' should be an array")
            result.is_valid = False
            return
        
        # Validate each entry
        required_entry_fields = {
            'keys': list,
            'content': str,
            'extensions': dict,
            'enabled': bool,
            'insertion_order': (int, float),
            'use_regex': bool
        }
        
        for i, entry in enumerate(lorebook['entries']):
            if not isinstance(entry, dict):
                result.errors.append(f"Lorebook entry at index {i} should be an object")
                result.is_valid = False
                continue
            
            for field, expected_type in required_entry_fields.items():
                if field not in entry:
                    result.errors.append(
                        f"Lorebook entry at index {i} missing required field: '{field}'"
                    )
                    result.is_valid = False
                elif isinstance(expected_type, tuple):
                    if not isinstance(entry[field], expected_type):
                        result.warnings.append(
                            f"Lorebook entry {i} field '{field}' has unexpected type"
                        )
                elif not isinstance(entry[field], expected_type):
                    result.errors.append(
                        f"Lorebook entry {i} field '{field}' should be "
                        f"{expected_type.__name__}, got {type(entry[field]).__name__}"
                    )
                    result.is_valid = False


class CharacterCardExtractor:
    """Main class for extracting and processing character cards"""
    
    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or Path('extracted_cards')
        self.output_dir.mkdir(exist_ok=True)
    
    def extract_card_from_png(self, png_path: Path) -> Tuple[Optional[Dict], ValidationResult]:
        """Extract and validate character card from a PNG file"""
        result = ValidationResult(is_valid=False)
        
        try:
            # Read PNG chunks
            chunks = PNGChunkReader.read_png_chunks(png_path)
            
            # Check for ccv3 chunk
            if 'ccv3' not in chunks:
                # Try fallback to chara chunk (V2)
                if 'chara' in chunks:
                    result.warnings.append(
                        "Found 'chara' chunk (V2 format), attempting to decode"
                    )
                    card_data = self._decode_card_data(chunks['chara'])
                    result.warnings.append(
                        "This is a Character Card V2, not V3. "
                        "Validation may not be accurate."
                    )
                else:
                    result.errors.append("No 'ccv3' or 'chara' chunk found in PNG")
                    return None, result
            else:
                # Decode ccv3 chunk
                card_data = self._decode_card_data(chunks['ccv3'])
            
            # Validate the card
            result = CharacterCardV3Validator.validate_card(card_data)
            
            return card_data, result
            
        except Exception as e:
            result.errors.append(f"Error extracting card: {str(e)}")
            return None, result
    
    def _decode_card_data(self, chunk_data: bytes) -> Dict[str, Any]:
        """Decode base64 encoded character card data"""
        try:
            # Decode base64
            decoded = base64.b64decode(chunk_data)
            # Parse JSON
            card_data = json.loads(decoded.decode('utf-8'))
            return card_data
        except Exception as e:
            raise ValueError(f"Failed to decode card data: {str(e)}")
    
    def save_card_json(self, card_data: Dict[str, Any], original_filename: str):
        """Save extracted card data to JSON file"""
        output_filename = Path(original_filename).stem + '_card.json'
        output_path = self.output_dir / output_filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(card_data, f, indent=2, ensure_ascii=False)
        
        return output_path
    
    def process_batch(self, png_files: List[Path], verbose: bool = True) -> Dict[str, Any]:
        """Process a batch of PNG files"""
        results = {
            'total': len(png_files),
            'successful': 0,
            'failed': 0,
            'files': []
        }
        
        for png_file in png_files:
            if verbose:
                print(f"\nProcessing: {png_file.name}")
                print("-" * 60)
            
            card_data, validation = self.extract_card_from_png(png_file)
            
            file_result = {
                'filename': png_file.name,
                'valid': validation.is_valid,
                'card_name': validation.card_name,
                'spec_version': validation.spec_version,
                'errors': validation.errors,
                'warnings': validation.warnings,
                'extracted': card_data is not None
            }
            
            if card_data:
                try:
                    output_path = self.save_card_json(card_data, png_file.name)
                    file_result['output_file'] = str(output_path)
                    results['successful'] += 1
                    
                    if verbose:
                        print(f"✓ Extracted to: {output_path}")
                except Exception as e:
                    file_result['errors'].append(f"Failed to save JSON: {str(e)}")
                    results['failed'] += 1
            else:
                results['failed'] += 1
            
            # Print validation results
            if verbose:
                if validation.card_name:
                    print(f"Card Name: {validation.card_name}")
                if validation.spec_version:
                    print(f"Spec Version: {validation.spec_version}")
                
                if validation.is_valid:
                    print("✓ Validation: PASSED")
                else:
                    print("✗ Validation: FAILED")
                
                if validation.errors:
                    print("\nErrors:")
                    for error in validation.errors:
                        print(f"  • {error}")
                
                if validation.warnings:
                    print("\nWarnings:")
                    for warning in validation.warnings:
                        print(f"  • {warning}")
            
            results['files'].append(file_result)
        
        return results


def main():
    parser = argparse.ArgumentParser(
        description='Extract and validate Character Card V3 data from PNG files'
    )
    parser.add_argument(
        'files',
        nargs='+',
        type=Path,
        help='PNG files to process'
    )
    parser.add_argument(
        '-o', '--output',
        type=Path,
        default=Path('extracted_cards'),
        help='Output directory for extracted JSON files (default: extracted_cards)'
    )
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Suppress detailed output'
    )
    parser.add_argument(
        '--summary-only',
        action='store_true',
        help='Only show summary, not individual file results'
    )
    
    args = parser.parse_args()
    
    # Filter for PNG files only
    png_files = [f for f in args.files if f.suffix.lower() in ['.png', '.apng']]
    
    if not png_files:
        print("Error: No PNG files provided")
        return 1
    
    extractor = CharacterCardExtractor(output_dir=args.output)
    results = extractor.process_batch(
        png_files, 
        verbose=not args.quiet and not args.summary_only
    )
    
    # Print summary
    print("\n" + "=" * 60)
    print("BATCH PROCESSING SUMMARY")
    print("=" * 60)
    print(f"Total files processed: {results['total']}")
    print(f"Successfully extracted: {results['successful']}")
    print(f"Failed: {results['failed']}")
    print(f"Output directory: {args.output}")
    
    if not args.quiet:
        print("\nFile Results:")
        for file_result in results['files']:
            status = "✓" if file_result['valid'] else "✗"
            print(f"  {status} {file_result['filename']}")
            if file_result['card_name']:
                print(f"    Name: {file_result['card_name']}")
            if not file_result['valid'] and file_result['errors']:
                print(f"    Errors: {len(file_result['errors'])}")
    
    return 0 if results['failed'] == 0 else 1


if __name__ == '__main__':
    exit(main())
