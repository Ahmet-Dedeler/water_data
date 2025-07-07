from pydantic import BaseModel, Field
from typing import Optional, Dict


class IngredientInfo(BaseModel):
    """Model for ingredient information from the ingredients database."""
    name: str = Field(..., description="Ingredient name")
    benefits: Optional[str] = Field(default=None, description="Health benefits")
    risks: Optional[str] = Field(default=None, description="Health risks")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Calcium",
                "benefits": "Supports bone health, essential for muscle function",
                "risks": None
            }
        }


class IngredientsMap(BaseModel):
    """Model for the complete ingredients mapping."""
    ingredients: Dict[str, IngredientInfo] = Field(
        ..., 
        description="Mapping of ingredient ID to ingredient information"
    )
    
    def get_ingredient(self, ingredient_id: int) -> Optional[IngredientInfo]:
        """Get ingredient info by ID."""
        return self.ingredients.get(str(ingredient_id))
    
    def search_ingredients(self, query: str) -> Dict[str, IngredientInfo]:
        """Search ingredients by name."""
        query_lower = query.lower()
        return {
            id_: info for id_, info in self.ingredients.items()
            if query_lower in info.name.lower()
        }
    
    class Config:
        json_schema_extra = {
            "example": {
                "ingredients": {
                    "41": {
                        "name": "Calcium",
                        "benefits": "Supports bone health, essential for muscle function",
                        "risks": None
                    },
                    "20": {
                        "name": "Arsenic",
                        "benefits": None,
                        "risks": "Carcinogenic, neurotoxic"
                    }
                }
            }
        } 