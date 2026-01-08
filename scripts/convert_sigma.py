#!/usr/bin/env python3
"""
Convert Sigma rules to Splunk or KQL queries.
"""
import os
import sys
import argparse
import subprocess
from pathlib import Path
from typing import List

def convert_sigma_rule(rule_path: Path, backend: str, output_dir: Path) -> bool:
    """
    Convert a single Sigma rule to the specified backend.
    
    Args:
        rule_path: Path to Sigma rule file
        backend: Backend to convert to ('splunk' or 'kql')
        output_dir: Directory to save converted queries
    
    Returns:
        True if conversion successful, False otherwise
    """
    try:
        # Create output directory structure mirroring input
        relative_path = rule_path.relative_to(Path(__file__).parent.parent / "sigma-rules")
        output_file = output_dir / relative_path.parent / f"{rule_path.stem}.{backend}"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Use sigma-cli to convert
        cmd = [
            "sigma",
            "convert",
            "-t", backend,
            "-f", str(rule_path)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            # Save the converted query
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result.stdout)
            
            # Also save metadata
            metadata_file = output_file.with_suffix(f".{backend}.meta")
            with open(metadata_file, 'w', encoding='utf-8') as f:
                f.write(f"Source: {rule_path}\n")
                f.write(f"Backend: {backend}\n")
                f.write(f"Status: Success\n")
            
            return True
        else:
            # Save error information
            error_file = output_file.with_suffix(f".{backend}.error")
            with open(error_file, 'w', encoding='utf-8') as f:
                f.write(f"Source: {rule_path}\n")
                f.write(f"Backend: {backend}\n")
                f.write(f"Status: Failed\n")
                f.write(f"Error: {result.stderr}\n")
            
            print(f"  ✗ Failed to convert {rule_path.name}: {result.stderr}")
            return False
    
    except Exception as e:
        print(f"  ✗ Error converting {rule_path.name}: {str(e)}")
        return False

def main():
    """Main conversion function."""
    parser = argparse.ArgumentParser(description="Convert Sigma rules to queries")
    parser.add_argument(
        "--backend",
        choices=["splunk", "kql", "splunkxml"],
        default="splunk",
        help="Backend to convert to"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="output",
        help="Output directory"
    )
    parser.add_argument(
        "--rule",
        type=str,
        help="Convert a specific rule file"
    )
    
    args = parser.parse_args()
    
    sigma_rules_dir = Path(__file__).parent.parent / "sigma-rules"
    output_dir = Path(__file__).parent.parent / args.output / args.backend
    
    if not sigma_rules_dir.exists():
        print(f"Error: {sigma_rules_dir} does not exist")
        sys.exit(1)
    
    # Find all Sigma rule files
    if args.rule:
        rule_files = [Path(args.rule)]
    else:
        rule_files = list(sigma_rules_dir.rglob("*.yml")) + list(sigma_rules_dir.rglob("*.yaml"))
    
    if not rule_files:
        print("No Sigma rule files found")
        sys.exit(0)
    
    print(f"Converting {len(rule_files)} rule(s) to {args.backend}...\n")
    
    success_count = 0
    for rule_file in rule_files:
        if convert_sigma_rule(rule_file, args.backend, output_dir):
            success_count += 1
            relative_path = rule_file.relative_to(sigma_rules_dir)
            print(f"  ✓ {relative_path}")
    
    print(f"\nConversion complete: {success_count}/{len(rule_files)} successful")
    
    if success_count < len(rule_files):
        sys.exit(1)

if __name__ == "__main__":
    main()
