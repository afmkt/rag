#!/usr/bin/env python3
"""
Test script for the RAG API endpoints
"""

import requests
import time
import subprocess
import os
import sys

def start_server():
    """Start the API server in a separate process."""
    os.chdir("/Users/michael/code/python/agno")
    return subprocess.Popen([sys.executable, "api.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def test_query_endpoints():
    """Test the query endpoints."""
    base_url = "http://localhost:8080"

    # Test data
    test_questions = {
        "pre": "What questions are asked in the questionnaire?",
        "middle": "What are the treatment guidelines for hypertension?",
        "post": "What medical records are available?"
    }

    results = {}

    for endpoint, question in test_questions.items():
        try:
            response = requests.post(f"{base_url}/query/{endpoint}", json={"question": question}, timeout=30)
            if response.status_code == 200:
                results[endpoint] = {"status": "success", "response": response.json()}
            else:
                results[endpoint] = {"status": "error", "status_code": response.status_code, "response": response.text}
        except Exception as e:
            results[endpoint] = {"status": "error", "error": str(e)}

    return results

def main():
    print("Starting API server...")
    server_process = start_server()

    # Wait for server to start
    time.sleep(10)

    try:
        print("Testing query endpoints...")
        results = test_query_endpoints()

        print("\nTest Results:")
        for endpoint, result in results.items():
            print(f"\n{endpoint.upper()} endpoint:")
            if result["status"] == "success":
                print("  Status: SUCCESS")
                print(f"  Response: {result['response']}")
            else:
                print(f"  Status: ERROR - {result}")

        print("\nNote: Upload endpoints require .docx files and cannot be tested automatically.")
        print("To test uploads, use curl or a tool like Postman:")
        print("curl -X POST -F 'file=@sample.docx' http://localhost:8080/upload/pre")

    finally:
        print("\nStopping server...")
        server_process.terminate()
        server_process.wait()

        # Print any server output
        stdout, stderr = server_process.communicate()
        if stdout:
            print("Server stdout:", stdout.decode())
        if stderr:
            print("Server stderr:", stderr.decode())

if __name__ == "__main__":
    main()