"""
Test script for the Recommendation Engine feature.
Tests the recommendation service, models, and API endpoints.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent))

from app.services.recommendation_service import recommendation_service
from app.services.user_service import user_service
from app.services.review_service import review_service
from app.models.recommendation import (
    RecommendationRequest, RecommendationCriteria, RecommendationFeedback,
    RecommendationType
)
from app.models.user import UserCreate, UserProfile
from app.models.review import ReviewCreate


async def setup_test_data():
    """Set up test data for recommendations."""
    print("Setting up test data...")
    
    # Create a test user
    test_user = UserCreate(
        username="test_recommender",
        email="test@recommendation.com",
        password="testpass123",
        full_name="Test Recommender"
    )
    
    try:
        user = await user_service.create_user(test_user)
        print(f"Created test user: {user.username} (ID: {user.id})")
        
        # Update user profile with preferences
        profile_update = UserProfile(
            health_goals=["hydration", "mineral_balance"],
            dietary_restrictions=["low_sodium"],
            avoid_contaminants=["chlorine", "fluoride"],
            min_health_score=80,
            preferred_packaging=["glass", "aluminum"],
            max_budget=50.0
        )
        
        updated_profile = await user_service.update_user_profile(user.id, profile_update)
        print(f"Updated user profile with preferences")
        
        # Create some test reviews to learn preferences
        test_reviews = [
            ReviewCreate(
                water_id=1,
                rating=5,
                title="Excellent water",
                content="Great taste and health benefits",
                taste_rating=5,
                health_rating=5,
                value_rating=4,
                packaging_rating=5
            ),
            ReviewCreate(
                water_id=2,
                rating=3,
                title="Average water",
                content="Not bad but could be better",
                taste_rating=3,
                health_rating=3,
                value_rating=3,
                packaging_rating=3
            ),
            ReviewCreate(
                water_id=3,
                rating=4,
                title="Good mineral content",
                content="Nice mineral balance",
                taste_rating=4,
                health_rating=5,
                value_rating=4,
                packaging_rating=3
            )
        ]
        
        for review_data in test_reviews:
            review = await review_service.create_review(user.id, review_data)
            print(f"Created review for water {review_data.water_id}")
        
        return user
        
    except Exception as e:
        print(f"Error setting up test data: {e}")
        return None


async def test_basic_recommendations():
    """Test basic recommendation generation."""
    print("\n=== Testing Basic Recommendations ===")
    
    try:
        # Test anonymous recommendations
        print("Testing anonymous recommendations...")
        recommendations = await recommendation_service.generate_recommendations()
        
        print(f"Generated {len(recommendations.recommendations)} anonymous recommendations")
        print(f"Total analyzed: {recommendations.total_analyzed}")
        print(f"Average confidence: {recommendations.average_confidence:.2f}")
        print(f"Diversity score: {recommendations.diversity_score:.2f}")
        
        if recommendations.recommendations:
            top_rec = recommendations.recommendations[0]
            print(f"Top recommendation: {top_rec.water.brand.name if top_rec.water.brand else 'Unknown'} - {top_rec.water.name}")
            print(f"  Score: {top_rec.score.overall:.2f}")
            print(f"  Confidence: {top_rec.confidence:.2f}")
            print(f"  Type: {top_rec.recommendation_type}")
            print(f"  Primary reason: {top_rec.reason.primary_reason}")
        
        return True
        
    except Exception as e:
        print(f"Error in basic recommendations test: {e}")
        return False


async def test_personalized_recommendations(user):
    """Test personalized recommendations for a user."""
    print("\n=== Testing Personalized Recommendations ===")
    
    try:
        # Test personalized recommendations
        print(f"Testing personalized recommendations for user {user.id}...")
        recommendations = await recommendation_service.generate_recommendations(user_id=user.id)
        
        print(f"Generated {len(recommendations.recommendations)} personalized recommendations")
        print(f"Personalization score: {recommendations.personalization_score:.2f}")
        
        if recommendations.recommendations:
            for i, rec in enumerate(recommendations.recommendations[:3], 1):
                print(f"{i}. {rec.water.brand.name if rec.water.brand else 'Unknown'} - {rec.water.name}")
                print(f"   Overall Score: {rec.score.overall:.2f}")
                print(f"   Health Match: {rec.score.health_match:.2f}")
                print(f"   Preference Match: {rec.score.preference_match:.2f}")
                print(f"   Confidence: {rec.confidence:.2f}")
        
        return True
        
    except Exception as e:
        print(f"Error in personalized recommendations test: {e}")
        return False


async def test_custom_criteria_recommendations():
    """Test recommendations with custom criteria."""
    print("\n=== Testing Custom Criteria Recommendations ===")
    
    try:
        # Test health-focused recommendations
        criteria = RecommendationCriteria(
            health_goals=["detox", "hydration"],
            min_health_score=90,
            preferred_packaging=["glass"],
            max_budget=30.0
        )
        
        request = RecommendationRequest(
            limit=5,
            criteria=criteria,
            recommendation_type=RecommendationType.HEALTH_BASED
        )
        
        recommendations = await recommendation_service.generate_recommendations(request=request)
        
        print(f"Generated {len(recommendations.recommendations)} health-focused recommendations")
        
        if recommendations.recommendations:
            for rec in recommendations.recommendations:
                print(f"- {rec.water.brand.name if rec.water.brand else 'Unknown'} - {rec.water.name}")
                print(f"  Health Score: {rec.water.score}/100")
                print(f"  Match Score: {rec.score.health_match:.2f}")
        
        return True
        
    except Exception as e:
        print(f"Error in custom criteria test: {e}")
        return False


async def test_user_preference_profile(user):
    """Test user preference profile functionality."""
    print("\n=== Testing User Preference Profile ===")
    
    try:
        # Get user preference profile
        profile = await recommendation_service.get_user_preference_profile(user.id)
        
        if profile:
            print(f"User preference profile loaded successfully")
            print(f"Data points: {profile.data_points}")
            print(f"Preference confidence: {profile.preference_confidence:.2f}")
            print(f"Brand affinities: {len(profile.brand_affinity) if profile.brand_affinity else 0}")
            print(f"Packaging preferences: {len(profile.packaging_preferences) if profile.packaging_preferences else 0}")
            
            if profile.brand_affinity:
                print("Top brand preferences:")
                for brand, score in list(profile.brand_affinity.items())[:3]:
                    print(f"  {brand}: {score:.2f}")
        else:
            print("No preference profile found")
        
        return True
        
    except Exception as e:
        print(f"Error in preference profile test: {e}")
        return False


async def test_recommendation_feedback(user):
    """Test recommendation feedback functionality."""
    print("\n=== Testing Recommendation Feedback ===")
    
    try:
        # Create feedback
        feedback = RecommendationFeedback(
            action_taken="viewed",
            helpful=True,
            rating=4,
            notes="Good recommendation, will try it"
        )
        
        success = await recommendation_service.record_feedback(
            user_id=user.id,
            recommendation_id="test_rec_123",
            feedback=feedback
        )
        
        if success:
            print("Feedback recorded successfully")
        else:
            print("Failed to record feedback")
        
        return success
        
    except Exception as e:
        print(f"Error in feedback test: {e}")
        return False


async def test_trending_recommendations():
    """Test trending recommendations."""
    print("\n=== Testing Trending Recommendations ===")
    
    try:
        request = RecommendationRequest(
            limit=5,
            recommendation_type=RecommendationType.TRENDING
        )
        
        recommendations = await recommendation_service.generate_recommendations(request=request)
        
        print(f"Generated {len(recommendations.recommendations)} trending recommendations")
        
        if recommendations.recommendations:
            for rec in recommendations.recommendations:
                print(f"- {rec.water.brand.name if rec.water.brand else 'Unknown'} - {rec.water.name}")
                print(f"  Popularity Score: {rec.score.popularity:.2f}")
        
        return True
        
    except Exception as e:
        print(f"Error in trending recommendations test: {e}")
        return False


async def cleanup_test_data(user):
    """Clean up test data."""
    print("\n=== Cleaning Up Test Data ===")
    
    try:
        if user:
            # In a real implementation, you might want to delete the test user
            print(f"Test user {user.username} can be manually removed if needed")
        
        print("Cleanup completed")
        return True
        
    except Exception as e:
        print(f"Error in cleanup: {e}")
        return False


async def main():
    """Run all recommendation system tests."""
    print("Starting Recommendation Engine Tests...")
    print("=" * 50)
    
    # Track test results
    results = []
    
    # Setup test data
    user = await setup_test_data()
    if not user:
        print("Failed to set up test data. Aborting tests.")
        return
    
    # Run tests
    test_functions = [
        ("Basic Recommendations", test_basic_recommendations, []),
        ("Personalized Recommendations", test_personalized_recommendations, [user]),
        ("Custom Criteria", test_custom_criteria_recommendations, []),
        ("User Preference Profile", test_user_preference_profile, [user]),
        ("Recommendation Feedback", test_recommendation_feedback, [user]),
        ("Trending Recommendations", test_trending_recommendations, [])
    ]
    
    for test_name, test_func, args in test_functions:
        try:
            result = await test_func(*args)
            results.append((test_name, result))
        except Exception as e:
            print(f"Test {test_name} failed with error: {e}")
            results.append((test_name, False))
    
    # Cleanup
    await cleanup_test_data(user)
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All recommendation engine tests passed!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")


if __name__ == "__main__":
    asyncio.run(main()) 