from pydantic import BaseModel, Field, computed_field, field_validator
from typing import List, Optional, Dict, Any, Union
from .common import HealthStatus


class Brand(BaseModel):
    """Water brand information."""
    name: str = Field(..., description="Brand name")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Evian"
            }
        }


class Source(BaseModel):
    """Research source information."""
    url: str = Field(..., description="Source URL")
    label: str = Field(..., description="Source label/title")
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com/research",
                "label": "Water Quality Study 2023"
            }
        }


class ScoreBreakdown(BaseModel):
    """Score breakdown component."""
    id: str = Field(..., description="Score component ID")
    score: float = Field(..., description="Score value")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "untested_penalty",
                "score": 0
            }
        }


class Ingredient(BaseModel):
    """Water ingredient/mineral information."""
    amount: Optional[float] = Field(default=None, description="Amount of ingredient")
    measure: Optional[str] = Field(default=None, description="Unit of measurement")
    ingredient_id: int = Field(..., description="Ingredient ID for lookup")
    is_beneficial: Optional[bool] = Field(default=None, description="Whether ingredient is beneficial")
    is_contaminant: Optional[bool] = Field(default=None, description="Whether ingredient is a contaminant")
    name: Optional[str] = Field(default=None, description="Ingredient name (populated from lookup)")
    risks: Optional[str] = Field(default=None, description="Health risks")
    benefits: Optional[str] = Field(default=None, description="Health benefits")
    
    @field_validator('amount', mode='before')
    @classmethod
    def parse_amount(cls, v):
        """Parse amount field, handling special values."""
        if v == "$undefined" or v is None:
            return None
        if isinstance(v, str):
            try:
                return float(v)
            except ValueError:
                return None
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "amount": 25.5,
                "measure": "mg/L",
                "ingredient_id": 41,
                "is_beneficial": True,
                "is_contaminant": False,
                "name": "Calcium",
                "benefits": "Supports bone health",
                "risks": None
            }
        }


class WaterData(BaseModel):
    """Main water data model."""
    id: int = Field(..., description="Unique water ID")
    name: str = Field(..., description="Water product name")
    brand: Optional[Brand] = Field(default=None, description="Brand information")
    score: float = Field(..., ge=0, le=100, description="Health score (0-100)")
    description: Optional[str] = Field(default=None, description="Product description")
    image: str = Field(..., description="Product image URL")
    ingredients: List[Ingredient] = Field(default=[], description="List of ingredients/minerals")
    sources: Optional[List[Source]] = Field(default=[], description="Research sources")
    packaging: Optional[str] = Field(default=None, description="Packaging type")
    score_breakdown: Optional[List[ScoreBreakdown]] = Field(default=[], description="Score breakdown components")
    ph_level: Optional[float] = Field(default=None, description="pH level of the water")
    tds: Optional[float] = Field(default=None, description="Total Dissolved Solids in ppm")
    
    @computed_field
    @property
    def health_status(self) -> HealthStatus:
        """Compute health status based on score."""
        if self.score >= 90:
            return HealthStatus.EXCELLENT
        elif self.score >= 75:
            return HealthStatus.GOOD
        elif self.score >= 60:
            return HealthStatus.FAIR
        else:
            return HealthStatus.POOR
    
    @computed_field
    @property
    def contaminants(self) -> List[Ingredient]:
        """Get list of contaminants."""
        return [ing for ing in self.ingredients if ing.is_contaminant is True]
    
    @computed_field
    @property
    def nutrients(self) -> List[Ingredient]:
        """Get list of beneficial nutrients."""
        return [ing for ing in self.ingredients if ing.is_beneficial is True]
    
    @computed_field
    @property
    def lab_tested(self) -> bool:
        """Check if water is lab tested based on score breakdown."""
        if not self.score_breakdown:
            return False
        untested_penalty = next(
            (item for item in self.score_breakdown if item.id == "untested_penalty"),
            None
        )
        return untested_penalty.score == 0 if untested_penalty else False
    
    @computed_field
    @property
    def microplastics_risk(self) -> str:
        """Assess microplastics risk based on packaging."""
        if not self.packaging:
            return "Unknown"
        return "High Risk" if self.packaging.lower() == "plastic" else "Minimal"
    
    @computed_field
    @property
    def contaminants_count(self) -> int:
        """Count of contaminants."""
        return len(self.contaminants)
    
    @computed_field
    @property
    def nutrients_count(self) -> int:
        """Count of nutrients."""
        return len(self.nutrients)
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Evian Natural Spring Water",
                "brand": {"name": "Evian"},
                "score": 85.5,
                "description": "Natural spring water from the French Alps",
                "image": "https://example.com/evian.jpg",
                "packaging": "plastic",
                "ingredients": [
                    {
                        "amount": 80.0,
                        "measure": "mg/L",
                        "ingredient_id": 41,
                        "is_beneficial": True,
                        "is_contaminant": False,
                        "name": "Calcium"
                    }
                ],
                "sources": [
                    {
                        "url": "https://example.com/study",
                        "label": "Water Quality Analysis"
                    }
                ],
                "score_breakdown": [
                    {
                        "id": "untested_penalty",
                        "score": 0
                    }
                ]
            }
        }


class WaterCreate(BaseModel):
    """Model for creating new water entries."""
    name: str = Field(..., description="Water product name")
    brand_name: str = Field(..., description="Brand name")
    score: float = Field(..., ge=0, le=100, description="Health score")
    description: Optional[str] = Field(default=None, description="Product description")
    image: str = Field(..., description="Product image URL")
    packaging: Optional[str] = Field(default=None, description="Packaging type")
    ingredients: List[Ingredient] = Field(default=[], description="List of ingredients")
    sources: Optional[List[Source]] = Field(default=[], description="Research sources")
    score_breakdown: List[ScoreBreakdown] = Field(default=[], description="Score breakdown")
    ph_level: Optional[float] = Field(default=None, description="pH level of the water")
    tds: Optional[float] = Field(default=None, description="Total Dissolved Solids in ppm")


class WaterUpdate(BaseModel):
    """Model for updating water entries."""
    name: Optional[str] = Field(default=None, description="Water product name")
    brand_name: Optional[str] = Field(default=None, description="Brand name")
    score: Optional[float] = Field(default=None, ge=0, le=100, description="Health score")
    description: Optional[str] = Field(default=None, description="Product description")
    image: Optional[str] = Field(default=None, description="Product image URL")
    packaging: Optional[str] = Field(default=None, description="Packaging type")
    ingredients: Optional[List[Ingredient]] = Field(default=None, description="List of ingredients")
    sources: Optional[List[Source]] = Field(default=None, description="Research sources")
    score_breakdown: Optional[List[ScoreBreakdown]] = Field(default=None, description="Score breakdown")
    ph_level: Optional[float] = Field(default=None, description="pH level of the water")
    tds: Optional[float] = Field(default=None, description="Total Dissolved Solids in ppm")


class WaterDataResponse(BaseModel):
    """Response model for single water data."""
    success: bool = True
    message: str = "Water data retrieved successfully"
    data: WaterData


class WaterListResponse(BaseModel):
    """Response model for water data list."""
    success: bool = True
    message: str = "Water list retrieved successfully"
    data: List[WaterData]
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page")
    size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total number of pages")

    class Config:
        from_attributes = True


class WaterSummary(BaseModel):
    """Summary statistics for water data."""
    total_waters: int
    average_score: float
    excellent_count: int  # score >= 90
    good_count: int       # score 75-89
    fair_count: int       # score 60-74
    poor_count: int       # score < 60
    lab_tested_count: int
    plastic_packaging_count: int
    glass_packaging_count: int
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "total_waters": 150,
                "average_score": 73.2,
                "excellent_count": 12,
                "good_count": 45,
                "fair_count": 67,
                "poor_count": 26,
                "lab_tested_count": 89,
                "plastic_packaging_count": 120,
                "glass_packaging_count": 30
            }
        }


class WaterLogCreate(BaseModel):
    """Model for logging water intake."""
    water_id: int = Field(..., description="The ID of the water product consumed.")
    volume: float = Field(..., gt=0, description="The volume of water consumed, in liters.")
    drink_type_id: Optional[int] = Field(None, description="The ID of the drink type.")
    caffeine_mg: Optional[int] = Field(None, description="The amount of caffeine in mg.") 