#!/usr/bin/env python3
"""
Simple test script to verify the Water Health application is working correctly.
"""

import asyncio
import json
from pathlib import Path
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.data_service import DataService
from app.services.search_service import SearchService
from app.models.water import WaterData, Brand


async def test_basic_functionality():
    """Test basic functionality"""
    print("Testing data loading...")
    
    try:
        data_service = DataService()
        await data_service.load_data()
        
        waters = await data_service.get_all_water_data()
        print(f"SUCCESS: Loaded {len(waters)} waters")
        
        if waters:
            print(f"Sample water: {waters[0].name} by {waters[0].brand.name}")
            print(f"Score: {waters[0].score}")
            print(f"Health status: {waters[0].health_status}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False


async def test_search():
    """Test search functionality"""
    print("\nTesting search...")
    
    try:
        suggestions = await SearchService.get_search_suggestions("water")
        print(f"Search suggestions: {len(suggestions)} results")
        
        results = await SearchService.advanced_search(query="", limit=5)
        print(f"Advanced search: {len(results)} results")
        
        return True
        
    except Exception as e:
        print(f"ERROR in search: {e}")
        return False


async def main():
    """Run tests"""
    print("Starting Water Health Application Tests")
    print("=" * 50)
    
    # Test data loading
    success1 = await test_basic_functionality()
    
    # Test search
    success2 = await test_search()
    
    if success1 and success2:
        print("\n" + "=" * 50)
        print("ALL TESTS PASSED!")
        print("\nTo start the application:")
        print("1. Run: python main.py")
        print("2. Open: http://localhost:8000")
    else:
        print("\nSome tests failed!")


if __name__ == "__main__":
    asyncio.run(main()) 