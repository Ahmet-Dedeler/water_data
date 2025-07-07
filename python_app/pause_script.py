#!/usr/bin/env python3
"""
Pause script for feature implementation.
This script pauses for 30 seconds after each file modification.
"""

import time
import sys

def pause_after_modification(feature_name: str = "feature"):
    """
    Pause for 30 seconds after implementing a feature.
    
    Args:
        feature_name: Name of the feature that was just implemented
    """
    print(f"✅ Completed implementation of: {feature_name}")
    print("⏳ Pausing for 30 seconds before next feature...")
    
    # Countdown timer
    for i in range(30, 0, -1):
        print(f"⏰ {i} seconds remaining...", end="\r")
        time.sleep(1)
    
    print("\n🚀 Ready for next feature implementation!")
    print("-" * 50)

if __name__ == "__main__":
    feature_name = sys.argv[1] if len(sys.argv) > 1 else "Unknown Feature"
    pause_after_modification(feature_name) 