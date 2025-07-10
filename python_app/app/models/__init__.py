# STAGE 1: Cleaned __init__.py with known correct models

from .water import (
    Brand,
    Source,
    ScoreBreakdown,
    Ingredient,
    WaterData,
    WaterCreate,
    WaterUpdate,
    WaterDataResponse,
    WaterListResponse,
    WaterSummary,
    WaterLogSearchCriteria,
    WaterLogCreate,
)
from .ingredient import (
    IngredientInfo,
    IngredientsMap,
)
from .common import (
    BaseResponse,
    PaginationParams,
    SearchParams,
    SortOrder,
    SortField,
    SortParams,
    HealthStatus,
    PackagingType,
    ErrorResponse,
)
from .user import (
    UserRole,
    UserProfile,
    User,
    UserCreate,
    UserUpdate,
    UserProfileUpdate,
    Token,
    UserLogin,
    PasswordChange,
    PasswordReset,
    PasswordResetConfirm,
    UserPreferencesUpdate,
    DailyStreakBase,
    DailyStreakCreate,
    DailyStreakUpdate,
    DailyStreak,
    StreakSummary,
)
from .achievement import (
    Achievement,
    UserAchievement,
    UserAchievementDetail,
)

# The rest of the imports are commented out for now.
# I will re-introduce them after verifying the contents of each file. 