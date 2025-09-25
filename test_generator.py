#!/usr/bin/env python3
"""
Simple test script to verify the website generator works correctly.
"""

import os
import sys
import json
from pathlib import Path
import tempfile
import shutil

def test_basic_functionality():
    """Test that the generator works with the provided example data."""
    script_dir = Path(__file__).parent
    
    # Check that required files exist
    generator_script = script_dir / "generate_website.py"
    data_dir = script_dir / "data"
    
    if not generator_script.exists():
        print("❌ ERROR: generate_website.py not found")
        return False
    
    if not data_dir.exists():
        print("❌ ERROR: data directory not found")
        return False
    
    # Run the generator
    print("🔧 Running website generator...")
    result = os.system(f"cd {script_dir} && python generate_website.py")
    
    if result != 0:
        print("❌ ERROR: Website generator failed")
        return False
    
    # Check output files exist
    docs_dir = script_dir / "docs"
    required_files = [
        docs_dir / "index.html",
        docs_dir / "styles.css",
        docs_dir / "equations" / "index.html",
        docs_dir / "mathematicians" / "index.html"
    ]
    
    for file_path in required_files:
        if not file_path.exists():
            print(f"❌ ERROR: Required file {file_path} not found")
            return False
    
    # Check that HTML files contain expected content
    main_index = docs_dir / "index.html"
    with open(main_index, 'r') as f:
        content = f.read()
        if "Mathematics Database" not in content:
            print("❌ ERROR: Main index missing title")
            return False
        if "Equations" not in content or "Mathematicians" not in content:
            print("❌ ERROR: Main index missing table links")
            return False
    
    print("✅ All tests passed!")
    return True

def test_data_validation():
    """Test that all data files are valid JSON."""
    script_dir = Path(__file__).parent
    data_dir = script_dir / "data"
    
    print("🔍 Validating JSON data files...")
    
    for table_dir in data_dir.iterdir():
        if not table_dir.is_dir():
            continue
            
        print(f"  Checking table: {table_dir.name}")
        
        # Check schema file
        schema_file = table_dir / "schema.json"
        if schema_file.exists():
            try:
                with open(schema_file, 'r') as f:
                    json.load(f)
                print(f"    ✅ schema.json is valid")
            except json.JSONDecodeError as e:
                print(f"    ❌ schema.json is invalid: {e}")
                return False
        
        # Check data files
        for json_file in table_dir.glob("*.json"):
            if json_file.name == "schema.json":
                continue
                
            try:
                with open(json_file, 'r') as f:
                    json.load(f)
                print(f"    ✅ {json_file.name} is valid")
            except json.JSONDecodeError as e:
                print(f"    ❌ {json_file.name} is invalid: {e}")
                return False
    
    return True

def main():
    """Run all tests."""
    print("🧪 Running Math Database Generator Tests\n")
    
    tests_passed = 0
    total_tests = 2
    
    # Test 1: Basic functionality
    print("Test 1: Basic Functionality")
    if test_basic_functionality():
        tests_passed += 1
    print()
    
    # Test 2: Data validation
    print("Test 2: Data Validation")
    if test_data_validation():
        tests_passed += 1
    print()
    
    # Summary
    print(f"📊 Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! The generator is working correctly.")
        return 0
    else:
        print("💥 Some tests failed. Please check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())