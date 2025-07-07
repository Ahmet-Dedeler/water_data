from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, time
from enum import Enum


class DrinkCategory(str, Enum):
    """Main categories of drinks."""
    WATER = "water"
    TEA = "tea"
    COFFEE = "coffee"
    JUICE = "juice"
    SODA = "soda"
    ENERGY_DRINK = "energy_drink"
    SPORTS_DRINK = "sports_drink"
    ALCOHOL = "alcohol"
    SMOOTHIE = "smoothie"
    MILK = "milk"
    PLANT_MILK = "plant_milk"
    KOMBUCHA = "kombucha"
    OTHER = "other"


class CaffeineLevel(str, Enum):
    """Caffeine content levels."""
    NONE = "none"
    LOW = "low"          # 1-50mg
    MODERATE = "moderate" # 51-100mg
    HIGH = "high"        # 101-200mg
    VERY_HIGH = "very_high" # 200mg+


class HydrationEffect(str, Enum):
    """Effect on hydration."""
    HIGHLY_HYDRATING = "highly_hydrating"    # 1.2x multiplier
    HYDRATING = "hydrating"                  # 1.0x multiplier
    NEUTRAL = "neutral"                      # 0.8x multiplier
    MILDLY_DEHYDRATING = "mildly_dehydrating" # 0.6x multiplier
    DEHYDRATING = "dehydrating"              # 0.4x multiplier


class DrinkType(BaseModel):
    """Comprehensive drink type model."""
    id: Optional[int] = Field(None, description="Drink type ID")
    name: str = Field(..., max_length=100, description="Name of the drink type")
    category: DrinkCategory = Field(..., description="Main category of the drink")
    
    # Hydration properties
    hydration_multiplier: float = Field(1.0, ge=0, le=2.0, description="Hydration effectiveness multiplier")
    hydration_effect: HydrationEffect = Field(HydrationEffect.HYDRATING, description="Effect on hydration")
    
    # Nutritional information
    caffeine_mg_per_100ml: float = Field(0, ge=0, le=500, description="Caffeine content per 100ml")
    caffeine_level: CaffeineLevel = Field(CaffeineLevel.NONE, description="Caffeine level category")
    calories_per_100ml: float = Field(0, ge=0, le=1000, description="Calories per 100ml")
    sugar_g_per_100ml: float = Field(0, ge=0, le=50, description="Sugar content per 100ml")
    sodium_mg_per_100ml: float = Field(0, ge=0, le=1000, description="Sodium content per 100ml")
    
    # Additional nutrients
    antioxidants: bool = Field(False, description="Contains significant antioxidants")
    electrolytes: bool = Field(False, description="Contains electrolytes")
    vitamins: List[str] = Field(default_factory=list, description="Vitamins present")
    minerals: List[str] = Field(default_factory=list, description="Minerals present")
    
    # Health considerations
    health_benefits: List[str] = Field(default_factory=list, description="Potential health benefits")
    health_warnings: List[str] = Field(default_factory=list, description="Health warnings or considerations")
    recommended_daily_limit_ml: Optional[int] = Field(None, description="Recommended daily limit in ml")
    
    # Timing recommendations
    best_times_to_consume: List[str] = Field(default_factory=list, description="Best times to consume")
    avoid_times: List[str] = Field(default_factory=list, description="Times to avoid consumption")
    
    # Preparation and varieties
    common_varieties: List[str] = Field(default_factory=list, description="Common varieties or subtypes")
    preparation_methods: List[str] = Field(default_factory=list, description="Common preparation methods")
    
    # Metadata
    description: Optional[str] = Field(None, max_length=500, description="Description of the drink type")
    is_active: bool = Field(True, description="Whether this drink type is active")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    @validator('caffeine_level', always=True)
    def set_caffeine_level(cls, v, values):
        """Automatically set caffeine level based on caffeine content."""
        caffeine_mg = values.get('caffeine_mg_per_100ml', 0)
        if caffeine_mg == 0:
            return CaffeineLevel.NONE
        elif caffeine_mg <= 50:
            return CaffeineLevel.LOW
        elif caffeine_mg <= 100:
            return CaffeineLevel.MODERATE
        elif caffeine_mg <= 200:
            return CaffeineLevel.HIGH
        else:
            return CaffeineLevel.VERY_HIGH


class DrinkTypeCreate(BaseModel):
    """Model for creating a new drink type."""
    name: str = Field(..., max_length=100, description="Name of the drink type")
    category: DrinkCategory = Field(..., description="Main category of the drink")
    hydration_multiplier: float = Field(1.0, ge=0, le=2.0, description="Hydration effectiveness multiplier")
    caffeine_mg_per_100ml: float = Field(0, ge=0, le=500, description="Caffeine content per 100ml")
    calories_per_100ml: float = Field(0, ge=0, le=1000, description="Calories per 100ml")
    sugar_g_per_100ml: float = Field(0, ge=0, le=50, description="Sugar content per 100ml")
    sodium_mg_per_100ml: float = Field(0, ge=0, le=1000, description="Sodium content per 100ml")
    antioxidants: bool = Field(False, description="Contains significant antioxidants")
    electrolytes: bool = Field(False, description="Contains electrolytes")
    vitamins: List[str] = Field(default_factory=list, description="Vitamins present")
    minerals: List[str] = Field(default_factory=list, description="Minerals present")
    health_benefits: List[str] = Field(default_factory=list, description="Potential health benefits")
    health_warnings: List[str] = Field(default_factory=list, description="Health warnings")
    recommended_daily_limit_ml: Optional[int] = Field(None, description="Recommended daily limit in ml")
    best_times_to_consume: List[str] = Field(default_factory=list, description="Best times to consume")
    avoid_times: List[str] = Field(default_factory=list, description="Times to avoid consumption")
    common_varieties: List[str] = Field(default_factory=list, description="Common varieties")
    preparation_methods: List[str] = Field(default_factory=list, description="Preparation methods")
    description: Optional[str] = Field(None, max_length=500, description="Description")


class DrinkTypeUpdate(BaseModel):
    """Model for updating a drink type."""
    name: Optional[str] = Field(None, max_length=100, description="Name of the drink type")
    category: Optional[DrinkCategory] = Field(None, description="Main category of the drink")
    hydration_multiplier: Optional[float] = Field(None, ge=0, le=2.0, description="Hydration multiplier")
    caffeine_mg_per_100ml: Optional[float] = Field(None, ge=0, le=500, description="Caffeine content")
    calories_per_100ml: Optional[float] = Field(None, ge=0, le=1000, description="Calories per 100ml")
    sugar_g_per_100ml: Optional[float] = Field(None, ge=0, le=50, description="Sugar content")
    sodium_mg_per_100ml: Optional[float] = Field(None, ge=0, le=1000, description="Sodium content")
    antioxidants: Optional[bool] = Field(None, description="Contains antioxidants")
    electrolytes: Optional[bool] = Field(None, description="Contains electrolytes")
    vitamins: Optional[List[str]] = Field(None, description="Vitamins present")
    minerals: Optional[List[str]] = Field(None, description="Minerals present")
    health_benefits: Optional[List[str]] = Field(None, description="Health benefits")
    health_warnings: Optional[List[str]] = Field(None, description="Health warnings")
    recommended_daily_limit_ml: Optional[int] = Field(None, description="Daily limit")
    description: Optional[str] = Field(None, max_length=500, description="Description")
    is_active: Optional[bool] = Field(None, description="Whether active")


class DrinkLog(BaseModel):
    """Model for logging a drink consumption."""
    id: Optional[int] = Field(None, description="Log entry ID")
    user_id: int = Field(..., description="User ID")
    drink_type_id: int = Field(..., description="Drink type ID")
    volume_ml: float = Field(..., gt=0, le=5000, description="Volume consumed in ml")
    
    # Drink-specific details
    brand: Optional[str] = Field(None, max_length=100, description="Brand name")
    variety: Optional[str] = Field(None, max_length=100, description="Specific variety")
    preparation_method: Optional[str] = Field(None, description="How it was prepared")
    
    # Nutritional tracking
    actual_caffeine_mg: Optional[float] = Field(None, description="Actual caffeine content if different")
    actual_calories: Optional[float] = Field(None, description="Actual calories if different")
    added_sugar: bool = Field(False, description="Whether sugar was added")
    added_milk: bool = Field(False, description="Whether milk was added")
    
    # Context
    temperature: Optional[str] = Field(None, description="Temperature (hot, cold, room)")
    location: Optional[str] = Field(None, description="Where consumed")
    mood_before: Optional[int] = Field(None, ge=1, le=10, description="Mood before drinking (1-10)")
    mood_after: Optional[int] = Field(None, ge=1, le=10, description="Mood after drinking (1-10)")
    energy_before: Optional[int] = Field(None, ge=1, le=10, description="Energy before (1-10)")
    energy_after: Optional[int] = Field(None, ge=1, le=10, description="Energy after (1-10)")
    
    # Timing
    consumed_at: datetime = Field(default_factory=datetime.utcnow, description="When consumed")
    notes: Optional[str] = Field(None, max_length=300, description="Additional notes")
    
    # Calculated fields
    hydration_contribution: Optional[float] = Field(None, description="Calculated hydration contribution")
    caffeine_contribution: Optional[float] = Field(None, description="Calculated caffeine contribution")


class DrinkLogCreate(BaseModel):
    """Model for creating a drink log entry."""
    drink_type_id: int = Field(..., description="Drink type ID")
    volume_ml: float = Field(..., gt=0, le=5000, description="Volume consumed in ml")
    brand: Optional[str] = Field(None, max_length=100, description="Brand name")
    variety: Optional[str] = Field(None, max_length=100, description="Specific variety")
    preparation_method: Optional[str] = Field(None, description="How it was prepared")
    actual_caffeine_mg: Optional[float] = Field(None, description="Actual caffeine if different")
    actual_calories: Optional[float] = Field(None, description="Actual calories if different")
    added_sugar: bool = Field(False, description="Whether sugar was added")
    added_milk: bool = Field(False, description="Whether milk was added")
    temperature: Optional[str] = Field(None, description="Temperature")
    location: Optional[str] = Field(None, description="Where consumed")
    mood_before: Optional[int] = Field(None, ge=1, le=10, description="Mood before")
    mood_after: Optional[int] = Field(None, ge=1, le=10, description="Mood after")
    energy_before: Optional[int] = Field(None, ge=1, le=10, description="Energy before")
    energy_after: Optional[int] = Field(None, ge=1, le=10, description="Energy after")
    notes: Optional[str] = Field(None, max_length=300, description="Additional notes")


class DrinkLogUpdate(BaseModel):
    """Model for updating a drink log entry."""
    volume_ml: Optional[float] = Field(None, gt=0, le=5000, description="Volume consumed")
    brand: Optional[str] = Field(None, max_length=100, description="Brand name")
    variety: Optional[str] = Field(None, max_length=100, description="Specific variety")
    preparation_method: Optional[str] = Field(None, description="Preparation method")
    mood_after: Optional[int] = Field(None, ge=1, le=10, description="Mood after drinking")
    energy_after: Optional[int] = Field(None, ge=1, le=10, description="Energy after drinking")
    notes: Optional[str] = Field(None, max_length=300, description="Additional notes")


class DrinkSummary(BaseModel):
    """Summary of drink consumption for a user."""
    user_id: int = Field(..., description="User ID")
    date: datetime = Field(..., description="Date of summary")
    
    # Total consumption
    total_volume_ml: float = Field(..., description="Total volume consumed")
    total_hydration_contribution: float = Field(..., description="Total hydration contribution")
    total_caffeine_mg: float = Field(..., description="Total caffeine consumed")
    total_calories: float = Field(..., description="Total calories from drinks")
    
    # By category
    consumption_by_category: Dict[str, float] = Field(..., description="Volume by drink category")
    caffeine_by_category: Dict[str, float] = Field(..., description="Caffeine by category")
    
    # Recommendations
    hydration_goal_met: bool = Field(..., description="Whether hydration goal was met")
    caffeine_within_limits: bool = Field(..., description="Whether caffeine is within recommended limits")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations for improvement")


class DrinkRecommendation(BaseModel):
    """Personalized drink recommendation."""
    drink_type: DrinkType = Field(..., description="Recommended drink type")
    recommended_volume_ml: float = Field(..., description="Recommended volume")
    reason: str = Field(..., description="Reason for recommendation")
    best_time: Optional[str] = Field(None, description="Best time to consume")
    preparation_tips: List[str] = Field(default_factory=list, description="Preparation tips")
    health_notes: List[str] = Field(default_factory=list, description="Health considerations")


class DrinkStats(BaseModel):
    """Statistics about drink consumption."""
    total_drink_types: int = Field(..., description="Total number of drink types")
    most_popular_category: DrinkCategory = Field(..., description="Most popular drink category")
    average_daily_volume: float = Field(..., description="Average daily volume across all users")
    average_caffeine_intake: float = Field(..., description="Average daily caffeine intake")
    hydration_compliance_rate: float = Field(..., description="Percentage of users meeting hydration goals") 