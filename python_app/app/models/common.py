from pydantic import BaseModel, Field
from typing import Generic, TypeVar, List, Optional, Any
from enum import Enum

T = TypeVar('T')


class BaseResponse(BaseModel, Generic[T]):
    """Generic base response model."""
    success: bool = True
    message: str = "Request successful"
    data: Optional[T] = None
    errors: Optional[List[str]] = None


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints."""
    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=20, ge=1, le=100, description="Page size")
    
    @property
    def skip(self) -> int:
        return (self.page - 1) * self.size
    
    @property
    def limit(self) -> int:
        return self.size


class SearchParams(BaseModel):
    """Search parameters for filtering water data."""
    query: Optional[str] = Field(default=None, description="Search query for name or brand")
    min_score: Optional[int] = Field(default=None, ge=0, le=100, description="Minimum health score")
    max_score: Optional[int] = Field(default=None, ge=0, le=100, description="Maximum health score")
    packaging: Optional[str] = Field(default=None, description="Packaging type filter")
    has_contaminants: Optional[bool] = Field(default=None, description="Filter by presence of contaminants")
    lab_tested: Optional[bool] = Field(default=None, description="Filter by lab testing status")


class SortOrder(str, Enum):
    """Sort order enumeration."""
    ASC = "asc"
    DESC = "desc"


class SortField(str, Enum):
    """Available sort fields."""
    NAME = "name"
    SCORE = "score"
    BRAND = "brand"
    PACKAGING = "packaging"


class SortParams(BaseModel):
    """Sort parameters."""
    field: SortField = Field(default=SortField.SCORE, description="Field to sort by")
    order: SortOrder = Field(default=SortOrder.DESC, description="Sort order")


class HealthStatus(str, Enum):
    """Health status categories based on score."""
    EXCELLENT = "excellent"  # 90-100
    GOOD = "good"           # 75-89
    FAIR = "fair"           # 60-74
    POOR = "poor"           # 0-59


class PackagingType(str, Enum):
    """Packaging type enumeration."""
    PLASTIC_BOTTLE = "plastic"
    GLASS_BOTTLE = "glass"
    ALUMINUM_CAN = "aluminum"
    CARTON = "carton"


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = False
    message: str
    errors: List[str]
    error_code: Optional[str] = None 