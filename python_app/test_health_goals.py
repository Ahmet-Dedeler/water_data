"""
Test script for the Health Goal Tracking feature.
"""
import asyncio
import sys
from pathlib import Path
from datetime import date, timedelta

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent))

from app.services.health_goal_service import health_goal_service
from app.services.user_service import user_service
from app.models.user import UserCreate
from app.models.health_goal import (
    HealthGoalCreate, HealthGoalUpdate, ProgressEntry, HealthGoalType, 
    HealthGoalStatus, HealthGoalPriority, HealthGoalFrequency
)


async def setup_test_data():
    """Set up a test user for health goal tests."""
    print("Setting up test user...")
    test_user_data = UserCreate(
        username="health_goal_tester",
        email="health@goal.com",
        password="testpass123",
        full_name="Health Goal Tester"
    )
    try:
        user = await user_service.create_user(test_user_data)
        print(f"Created test user: {user.username} (ID: {user.id})")
        return user
    except Exception as e:
        # It's possible the user already exists from a previous run
        users, _ = await user_service.get_users(limit=100)
        user = next((u for u in users if u.username == test_user_data.username), None)
        if user:
            print(f"Found existing test user: {user.username} (ID: {user.id})")
            return user
        else:
            print(f"Error setting up test user: {e}")
            return None


async def test_create_health_goal(user):
    """Test creating a new health goal."""
    print("\n=== Testing Health Goal Creation ===")
    try:
        goal_data = HealthGoalCreate(
            name="Daily Hydration Challenge",
            goal_type=HealthGoalType.DAILY_HYDRATION,
            target_value=2.5,
            unit="liters",
            target_date=date.today() + timedelta(days=30),
            priority=HealthGoalPriority.HIGH,
            motivation="Stay hydrated and feel more energetic!"
        )
        goal_response = await health_goal_service.create_health_goal(user.id, goal_data)
        goal = goal_response
        
        if goal:
            print(f"Successfully created goal: '{goal.name}' (ID: {goal.id})")
            print(f"  - Type: {goal.goal_type}")
            print(f"  - Target: {goal.target_value} {goal.unit}")
            print(f"  - Milestones created: {len(goal.milestones)}")
            return goal.id
        else:
            print("Failed to create health goal.")
            return None
    except Exception as e:
        print(f"Error in create health goal test: {e}")
        return None


async def test_get_health_goal(user_id, goal_id):
    """Test retrieving a health goal."""
    print("\n=== Testing Get Health Goal ===")
    if not goal_id:
        print("Skipping test: No goal_id provided.")
        return False
    try:
        goal = await health_goal_service.get_health_goal(goal_id, user_id)
        if goal:
            print(f"Successfully retrieved goal: '{goal.name}'")
            print(f"  - Status: {goal.status}")
            print(f"  - Progress: {goal.progress.completion_percentage:.2f}%")
            return True
        else:
            print("Failed to retrieve health goal.")
            return False
    except Exception as e:
        print(f"Error in get health goal test: {e}")
        return False


async def test_log_progress(user_id, goal_id):
    """Test logging progress for a health goal."""
    print("\n=== Testing Log Progress ===")
    if not goal_id:
        print("Skipping test: No goal_id provided.")
        return False
    try:
        progress_entries = [
            ProgressEntry(value=0.5, notes="Morning water", water_consumption=0.5),
            ProgressEntry(value=0.7, notes="Lunch hydration", water_consumption=0.7, mood_score=8),
            ProgressEntry(value=0.5, notes="Afternoon drink", water_consumption=0.5)
        ]
        
        new_achievements = []
        for entry in progress_entries:
            measurement, achievements = await health_goal_service.log_progress(goal_id, user_id, entry)
            if measurement:
                print(f"Logged progress: {measurement.value} {measurement.unit if measurement.unit else ''}")
                if achievements:
                    for ach in achievements:
                        print(f"  ** Achievement Unlocked! {ach.celebration_message} **")
                    new_achievements.extend(achievements)
            else:
                print(f"Failed to log progress for value {entry.value}")

        goal = await health_goal_service.get_health_goal(goal_id, user_id)
        print(f"Updated goal progress: {goal.progress.completion_percentage:.2f}%")
        print(f"  - Current streak: {goal.progress.streak_days} day(s)")
        print(f"  - Milestones achieved: {goal.progress.milestones_achieved}/{goal.progress.total_milestones}")
        
        return True
    except Exception as e:
        print(f"Error in log progress test: {e}")
        return False


async def test_update_health_goal(user_id, goal_id):
    """Test updating a health goal."""
    print("\n=== Testing Update Health Goal ===")
    if not goal_id:
        print("Skipping test: No goal_id provided.")
        return False
    try:
        update_data = HealthGoalUpdate(
            priority=HealthGoalPriority.CRITICAL,
            motivation="Really need to focus on this for my upcoming marathon!"
        )
        updated_goal = await health_goal_service.update_health_goal(goal_id, user_id, update_data)
        if updated_goal:
            print(f"Successfully updated goal '{updated_goal.name}'")
            print(f"  - New priority: {updated_goal.priority}")
            print(f"  - New motivation: {updated_goal.motivation}")
            return True
        else:
            print("Failed to update health goal.")
            return False
    except Exception as e:
        print(f"Error in update health goal test: {e}")
        return False


async def test_get_goal_stats(user_id):
    """Test getting user's goal statistics."""
    print("\n=== Testing Goal Statistics ===")
    try:
        stats = await health_goal_service.get_user_goal_stats(user_id)
        if stats:
            print("Successfully retrieved goal stats:")
            print(f"  - Total goals: {stats.total_goals}")
            print(f"  - Active goals: {stats.active_goals}")
            print(f"  - Completed goals: {stats.completed_goals}")
            print(f"  - Total achievements: {stats.total_achievements}")
            print(f"  - Longest streak: {stats.longest_streak} days")
            return True
        else:
            print("Failed to retrieve goal stats.")
            return False
    except Exception as e:
        print(f"Error in get goal stats test: {e}")
        return False


async def test_delete_health_goal(user_id, goal_id):
    """Test deleting a health goal."""
    print("\n=== Testing Delete Health Goal ===")
    if not goal_id:
        print("Skipping test: No goal_id provided.")
        return False
    try:
        success = await health_goal_service.delete_health_goal(goal_id, user_id)
        if success:
            print(f"Successfully deleted goal ID: {goal_id}")
            # Verify it's gone
            deleted_goal = await health_goal_service.get_health_goal(goal_id, user_id)
            if not deleted_goal:
                print("Verified that goal is no longer accessible.")
                return True
            else:
                print("Error: Goal still exists after deletion.")
                return False
        else:
            print("Failed to delete health goal.")
            return False
    except Exception as e:
        print(f"Error in delete health goal test: {e}")
        return False


async def main():
    """Run all health goal system tests."""
    print("Starting Health Goal Tracking System Tests...")
    print("=" * 50)

    user = await setup_test_data()
    if not user:
        print("Aborting tests: could not set up test user.")
        return

    results = []
    
    # Create a goal to be used by other tests
    goal_id = await test_create_health_goal(user)
    results.append(("Create Health Goal", bool(goal_id)))

    test_functions = [
        ("Get Health Goal", test_get_health_goal, [user.id, goal_id]),
        ("Log Progress", test_log_progress, [user.id, goal_id]),
        ("Update Health Goal", test_update_health_goal, [user.id, goal_id]),
        ("Get Goal Stats", test_get_goal_stats, [user.id]),
        ("Delete Health Goal", test_delete_health_goal, [user.id, goal_id])
    ]

    for test_name, test_func, args in test_functions:
        try:
            result = await test_func(*args)
            results.append((test_name, result))
        except Exception as e:
            print(f"Test '{test_name}' failed with an unhandled exception: {e}")
            results.append((test_name, False))

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
        print("🎉 All health goal tests passed!")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")


if __name__ == "__main__":
    asyncio.run(main()) 