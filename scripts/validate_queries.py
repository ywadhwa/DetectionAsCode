#!/usr/bin/env python3
"""
Validate Splunk and KQL query syntax.
"""
import os
import sys
import argparse
import re
from pathlib import Path
from typing import List, Tuple

def validate_splunk_query(query: str) -> Tuple[bool, List[str]]:
    """
    Basic Splunk query syntax validation.
    
    Args:
        query: Splunk query string
    
    Returns:
        (is_valid, list_of_errors)
    """
    errors = []
    
    # Remove comments
    query_clean = re.sub(r'<!--.*?-->', '', query, flags=re.DOTALL)
    
    # Basic checks
    if not query_clean.strip():
        errors.append("Query is empty")
        return False, errors
    
    # Check for balanced parentheses
    open_parens = query_clean.count('(')
    close_parens = query_clean.count(')')
    if open_parens != close_parens:
        errors.append(f"Unbalanced parentheses: {open_parens} open, {close_parens} close")
    
    # Check for balanced brackets
    open_brackets = query_clean.count('[')
    close_brackets = query_clean.count(']')
    if open_brackets != close_brackets:
        errors.append(f"Unbalanced brackets: {open_brackets} open, {close_brackets} close")
    
    # Check for balanced braces
    open_braces = query_clean.count('{')
    close_braces = query_clean.count('}')
    if open_braces != close_braces:
        errors.append(f"Unbalanced braces: {open_braces} open, {close_braces} close")
    
    # Check for common Splunk commands
    # This is a basic check - full validation would require Splunk SDK
    splunk_commands = ['index', 'search', 'where', 'stats', 'eval', 'rex', 'table']
    has_command = any(cmd in query_clean.lower() for cmd in splunk_commands)
    
    if not has_command and len(query_clean) > 10:
        # Might be a valid query without explicit commands
        pass
    
    return len(errors) == 0, errors

def validate_kql_query(query: str) -> Tuple[bool, List[str]]:
    """
    Basic KQL query syntax validation.
    
    Args:
        query: KQL query string
    
    Returns:
        (is_valid, list_of_errors)
    """
    errors = []
    
    # Remove comments
    query_clean = re.sub(r'//.*?$', '', query, flags=re.MULTILINE)
    query_clean = re.sub(r'/\*.*?\*/', '', query_clean, flags=re.DOTALL)
    
    # Basic checks
    if not query_clean.strip():
        errors.append("Query is empty")
        return False, errors
    
    # Check for balanced parentheses
    open_parens = query_clean.count('(')
    close_parens = query_clean.count(')')
    if open_parens != close_parens:
        errors.append(f"Unbalanced parentheses: {open_parens} open, {close_parens} close")
    
    # Check for balanced brackets
    open_brackets = query_clean.count('[')
    close_brackets = query_clean.count(']')
    if open_brackets != close_brackets:
        errors.append(f"Unbalanced brackets: {open_brackets} open, {close_brackets} close")
    
    # Check for balanced braces
    open_braces = query_clean.count('{')
    close_braces = query_clean.count('}')
    if open_braces != close_braces:
        errors.append(f"Unbalanced braces: {open_braces} open, {close_braces} close")
    
    # Check for common KQL operators
    kql_operators = ['where', 'project', 'summarize', 'extend', 'join', 'union']
    has_operator = any(op in query_clean.lower() for op in kql_operators)
    
    # KQL queries often start with a table name
    if not has_operator and len(query_clean) > 10:
        # Might be a valid query
        pass
    
    return len(errors) == 0, errors

def validate_query_file(query_file: Path, query_type: str) -> Tuple[bool, List[str]]:
    """
    Validate a query file.
    
    Args:
        query_file: Path to query file
        query_type: Type of query ('splunk' or 'kql')
    
    Returns:
        (is_valid, list_of_errors)
    """
    try:
        with open(query_file, 'r', encoding='utf-8') as f:
            query = f.read()
        
        if query_type == 'splunk':
            return validate_splunk_query(query)
        elif query_type == 'kql':
            return validate_kql_query(query)
        else:
            return False, [f"Unknown query type: {query_type}"]
    
    except Exception as e:
        return False, [f"Error reading file: {str(e)}"]

def main():
    """Main validation function."""
    parser = argparse.ArgumentParser(description="Validate query syntax")
    parser.add_argument(
        "--type",
        choices=["splunk", "kql"],
        required=True,
        help="Type of queries to validate"
    )
    parser.add_argument(
        "--directory",
        type=str,
        required=True,
        help="Directory containing query files"
    )
    
    args = parser.parse_args()
    
    query_dir = Path(args.directory)
    
    if not query_dir.exists():
        print(f"Error: {query_dir} does not exist")
        sys.exit(1)
    
    # Find all query files (excluding metadata and error files)
    query_files = [
        f for f in query_dir.rglob(f"*.{args.type}")
        if not f.name.endswith('.meta') and not f.name.endswith('.error')
    ]
    
    if not query_files:
        print(f"No {args.type} query files found in {query_dir}")
        sys.exit(0)
    
    print(f"Validating {len(query_files)} {args.type} query file(s)...\n")
    
    all_valid = True
    for query_file in query_files:
        is_valid, errors = validate_query_file(query_file, args.type)
        relative_path = query_file.relative_to(query_dir)
        
        if is_valid:
            print(f"✓ {relative_path}")
        else:
            print(f"✗ {relative_path}")
            for error in errors:
                print(f"  ERROR: {error}")
            all_valid = False
    
    if not all_valid:
        print("\nValidation failed!")
        sys.exit(1)
    else:
        print(f"\nAll {args.type} queries validated successfully!")

if __name__ == "__main__":
    main()
