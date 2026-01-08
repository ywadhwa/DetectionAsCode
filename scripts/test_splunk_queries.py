#!/usr/bin/env python3
"""
Test Splunk queries against a Splunk instance.
"""
import os
import sys
import argparse
import requests
import time
from pathlib import Path
from typing import List, Tuple, Dict, Any
import urllib3

# Disable SSL warnings for self-signed certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def execute_splunk_query(
    query: str,
    host: str = "localhost",
    port: int = 8089,
    username: str = "admin",
    password: str = "ChangeMe123!",
    index: str = "test_data",
    timeout: int = 30
) -> Tuple[bool, Dict[str, Any]]:
    """
    Execute a Splunk query and return results.
    
    Returns:
        (success, result_dict)
    """
    try:
        # Create search job
        search_url = f"https://{host}:{port}/services/search/jobs"
        search_data = {
            "search": f"search index={index} {query}",
            "output_mode": "json"
        }
        
        response = requests.post(
            search_url,
            auth=(username, password),
            data=search_data,
            verify=False,
            timeout=timeout
        )
        response.raise_for_status()
        
        # Parse job ID
        import xml.etree.ElementTree as ET
        root = ET.fromstring(response.text)
        job_id = root.find(".//sid").text if root.find(".//sid") is not None else None
        
        if not job_id:
            return False, {"error": "Failed to create search job"}
        
        # Wait for job to complete
        max_wait = 60
        wait_time = 0
        while wait_time < max_wait:
            status_url = f"https://{host}:{port}/services/search/jobs/{job_id}"
            status_response = requests.get(
                status_url,
                auth=(username, password),
                verify=False,
                timeout=timeout
            )
            status_response.raise_for_status()
            
            status_root = ET.fromstring(status_response.text)
            dispatch_state = status_root.find(".//dispatchState")
            if dispatch_state is not None:
                state = dispatch_state.text
                if state == "DONE":
                    # Get results
                    results_url = f"https://{host}:{port}/services/search/jobs/{job_id}/results"
                    results_response = requests.get(
                        results_url,
                        auth=(username, password),
                        params={"output_mode": "json"},
                        verify=False,
                        timeout=timeout
                    )
                    results_response.raise_for_status()
                    results = results_response.json()
                    
                    return True, {
                        "job_id": job_id,
                        "results": results,
                        "result_count": len(results.get("results", []))
                    }
                elif state in ["FAILED", "FATAL"]:
                    return False, {"error": f"Search job failed with state: {state}"}
            
            time.sleep(2)
            wait_time += 2
        
        return False, {"error": "Search job timed out"}
    
    except requests.exceptions.RequestException as e:
        return False, {"error": f"Request failed: {str(e)}"}
    except Exception as e:
        return False, {"error": f"Unexpected error: {str(e)}"}

def test_query_file(
    query_file: Path,
    host: str = "localhost",
    port: int = 8089,
    username: str = "admin",
    password: str = "ChangeMe123!",
    index: str = "test_data"
) -> Tuple[bool, Dict[str, Any]]:
    """
    Test a single query file.
    
    Returns:
        (success, result_dict)
    """
    try:
        with open(query_file, 'r', encoding='utf-8') as f:
            query = f.read().strip()
        
        if not query:
            return False, {"error": "Query file is empty"}
        
        # Remove comments and clean up
        query_lines = []
        for line in query.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                query_lines.append(line)
        
        query = ' '.join(query_lines)
        
        return execute_splunk_query(query, host, port, username, password, index)
    
    except Exception as e:
        return False, {"error": f"Error reading query file: {str(e)}"}

def main():
    """Main testing function."""
    parser = argparse.ArgumentParser(description="Test Splunk queries")
    parser.add_argument(
        "--directory",
        type=str,
        default="output/splunk",
        help="Directory containing Splunk query files"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="Splunk host"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8089,
        help="Splunk management port"
    )
    parser.add_argument(
        "--username",
        type=str,
        default="admin",
        help="Splunk username"
    )
    parser.add_argument(
        "--password",
        type=str,
        default="ChangeMe123!",
        help="Splunk password"
    )
    parser.add_argument(
        "--index",
        type=str,
        default="test_data",
        help="Splunk index to query"
    )
    parser.add_argument(
        "--query",
        type=str,
        help="Test a specific query file"
    )
    
    args = parser.parse_args()
    
    query_dir = Path(__file__).parent.parent / args.directory
    
    if args.query:
        query_files = [Path(args.query)]
    else:
        if not query_dir.exists():
            print(f"Error: {query_dir} does not exist")
            sys.exit(1)
        
        query_files = [
            f for f in query_dir.rglob("*.splunk")
            if not f.name.endswith('.meta') and not f.name.endswith('.error')
        ]
    
    if not query_files:
        print("No Splunk query files found")
        sys.exit(0)
    
    print(f"Testing {len(query_files)} query file(s) against Splunk...\n")
    print(f"Host: {args.host}:{args.port}")
    print(f"Index: {args.index}\n")
    
    success_count = 0
    failed_queries = []
    
    for query_file in query_files:
        relative_path = query_file.relative_to(query_dir) if query_dir.exists() else query_file
        print(f"Testing: {relative_path}...", end=" ")
        
        success, result = test_query_file(
            query_file,
            args.host,
            args.port,
            args.username,
            args.password,
            args.index
        )
        
        if success:
            result_count = result.get("result_count", 0)
            print(f"✓ (Returned {result_count} results)")
            success_count += 1
        else:
            error = result.get("error", "Unknown error")
            print(f"✗ ({error})")
            failed_queries.append((relative_path, error))
    
    print(f"\n{'='*60}")
    print(f"Results: {success_count}/{len(query_files)} queries executed successfully")
    
    if failed_queries:
        print("\nFailed queries:")
        for query_path, error in failed_queries:
            print(f"  - {query_path}: {error}")
        sys.exit(1)
    else:
        print("\nAll queries executed successfully!")

if __name__ == "__main__":
    main()
