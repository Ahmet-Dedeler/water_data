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
from app.services.water_service import WaterService


async def test_data_loading():
    """Test that data loads correctly"""
    print("Testing data loading...")
    
    data_service = DataService()
    await data_service.load_data()
    
    waters = await data_service.get_all_water_data()
    print(f"✅ Loaded {len(waters)} waters")
    
    ingredients_map = await data_service.get_ingredients_map()
    print(f"✅ Loaded {len(ingredients_map.ingredients)} ingredients")
    
    return data_service


async def test_search_functionality(data_service):
    """Test search functionality"""
    print("\nTesting search functionality...")
    
    # Test search suggestions
    suggestions = await SearchService.get_search_suggestions("water")
    print(f"✅ Search suggestions for 'water': {len(suggestions)} results")
    
    # Test advanced search
    results = await SearchService.advanced_search(query="water", limit=5)
    print(f"✅ Advanced search returned {len(results)} results")
    
    # Test ingredient search
    ingredient_results = await SearchService.search_by_ingredients("calcium")
    print(f"✅ Ingredient search returned {len(ingredient_results)} results")


async def test_water_service(data_service):
    """Test water service functionality"""
    print("\n💧 Testing water service...")
    
    water_service = WaterService(data_service)
    
    # Get top waters
    top_waters = await water_service.get_top_waters(limit=5)
    print(f"✅ Retrieved {len(top_waters)} top-rated waters")
    
    # Get analytics
    analytics = await water_service.get_analytics_overview()
    print(f"✅ Analytics: {analytics.total_waters} total waters, avg score: {analytics.average_score:.1f}")
    
    if top_waters:
        # Test individual water retrieval
        first_water = top_waters[0]
        water_detail = await water_service.get_water_by_id(first_water.id)
        print(f"✅ Retrieved water details: {water_detail.name}")


async def test_api_models():
    """Test that API models work correctly"""
    print("\n📋 Testing API models...")
    
    from app.models.water import WaterData, Brand, Source
    from app.models.common import HealthStatus, PackagingType
    
    # Create a test water instance
    test_water = WaterData(
        id="test-001",
        name="Test Water",
        brand=Brand(name="Test Brand", country="USA"),
        source=Source(type="Spring", location="Test Location"),
        packaging_type=PackagingType.PLASTIC_BOTTLE,
        score=85.5,
        lab_tested=True,
        ingredients=[]
    )
    
    print(f"✅ Created test water: {test_water.name}")
    print(f"✅ Health status: {test_water.health_status}")
    print(f"✅ Score breakdown: {test_water.score_breakdown}")


def check_file_structure():
    """Check that all required files exist"""
    print("\n📁 Checking file structure...")
    
    required_files = [
        "main.py",
        "requirements.txt",
        ".env.example",
        "app/__init__.py",
        "app/core/config.py",
        "app/models/water.py",
        "app/services/data_service.py",
        "app/api/endpoints/water.py",
        "data/water_data.json",
        "templates/base.html",
        "templates/index.html",
        "static/js/main.js",
        "static/css/style.css"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ All required files present")
        return True


async def main():
    """Run all tests"""
    print("Starting Water Health Application Tests\n")
    
    # Check file structure
    if not check_file_structure():
        print("\n❌ Test failed: Missing required files")
        return
    
    try:
        # Test data loading
        data_service = await test_data_loading()
        
        # Test search functionality
        await test_search_functionality(data_service)
        
        # Test water service
        await test_water_service(data_service)
        
        # Test API models
        await test_api_models()
        
        print("\n🎉 All tests passed! The Water Health application is ready to run.")
        print("\nTo start the application:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Copy .env.example to .env and configure if needed")
        print("3. Run the application: python main.py")
        print("4. Open your browser to http://localhost:8000")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 