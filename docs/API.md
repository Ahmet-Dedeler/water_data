# API Documentation

This document describes the data structures and schemas used in the Water Bottles Health Leaderboard application.

## Data Sources

The application uses data scraped from the **Oasis Health API** (`https://app.oasis-health.com/api/items/bottled_water/`) which provides comprehensive information about bottled water brands and their health characteristics.

## TypeScript Interfaces

### WaterData Interface

The main interface for water brand information:

```typescript
interface WaterData {
    id: number;                    // Unique identifier
    name: string;                  // Water brand name
    brand: Brand;                  // Brand information
    score: number;                 // Health score (0-100)
    description: string;           // Detailed description
    image: string;                 // Product image URL
    ingredients: Ingredient[];     // Array of ingredients/minerals
    sources: { url: string; label: string }[]; // Research sources
    packaging: string;             // Packaging type (e.g., "plastic", "glass")
    score_breakdown: { id: string; score: number }[]; // Score components
}
```

### Brand Interface

Brand information structure:

```typescript
interface Brand {
    name: string;                  // Brand name
}
```

### Ingredient Interface

Individual ingredient/mineral information:

```typescript
interface Ingredient {
    amount: number;                // Quantity present
    measure: string;               // Unit of measurement (mg/L, ppm, etc.)
    ingredient_id: number;         // Reference to ingredients.json
    is_beneficial: boolean | null; // Whether ingredient is beneficial
    is_contaminant: boolean | null; // Whether ingredient is a contaminant
    name?: string;                 // Ingredient name (populated from lookup)
    risks?: string | null;         // Health risks (populated from lookup)
    benefits?: string | null;      // Health benefits (populated from lookup)
}
```

### IngredientsMap Interface

Structure for ingredient lookup data:

```typescript
interface IngredientsMap {
    [key: string]: {
        name: string;              // Ingredient name
        benefits: string | null;   // Health benefits description
        risks: string | null;      // Health risks description
    };
}
```

## Data Files

### water_data.json

Large JSON file containing array of `WaterData` objects. Each entry represents a single water brand with complete analysis.

**Example Entry:**
```json
{
    "id": 123,
    "name": "Example Water Brand",
    "brand": {
        "name": "Example Brand Inc."
    },
    "score": 85,
    "description": "Premium spring water sourced from...",
    "image": "https://example.com/image.jpg",
    "ingredients": [
        {
            "amount": 25.5,
            "measure": "mg/L",
            "ingredient_id": 41,
            "is_beneficial": true,
            "is_contaminant": false
        }
    ],
    "sources": [
        {
            "url": "https://research-source.com",
            "label": "Scientific Study Title"
        }
    ],
    "packaging": "glass",
    "score_breakdown": [
        {
            "id": "untested_penalty",
            "score": 0
        }
    ]
}
```

### ingredients.json

Maps ingredient IDs to detailed information:

**Example Entries:**
```json
{
    "41": {
        "name": "Calcium",
        "benefits": "Supports bone health, essential for muscle function, vital for nerve transmission, important for cardiovascular health",
        "risks": null
    },
    "20": {
        "name": "Arsenic",
        "benefits": null,
        "risks": "Carcinogenic, neurotoxic, increased risk of cardiovascular disease, skin lesions, reproductive toxicity, increased risk of diabetes, developmental effects"
    }
}
```

## Scoring System

### Overall Score
- **Range**: 0-100
- **Higher is Better**: 100 represents the healthiest option
- **Factors**: Based on presence of contaminants, beneficial minerals, lab testing status

### Score Breakdown Components
- `untested_penalty`: Penalty for lack of third-party testing
- Additional scoring factors (implementation details in scoring algorithm)

### Lab Testing Indicator
- **Determined by**: `untested_penalty` score of 0 indicates lab tested
- **Display**: "Yes" if tested, "No" if not tested

### Microplastics Risk Assessment
- **Plastic packaging**: "High Risk"
- **Glass/other packaging**: "Minimal"

## API Endpoints (Internal)

The application uses static JSON data files rather than live API endpoints for the frontend. Data is updated via the Python scraper.

### Data Refresh Process
1. Run `python scraper.py`
2. Script fetches latest data from Oasis Health API
3. Updates `water_data.json` with new information
4. Frontend automatically uses updated data on next build/restart

## Error Handling

### Missing Data
- **Missing ingredients**: Displays "No ingredients listed"
- **Missing contaminants**: Displays "No contaminants listed"
- **Missing images**: Handled by Next.js Image component fallbacks
- **Invalid water ID**: Returns 404 page via Next.js `notFound()`

### Data Validation
- TypeScript provides compile-time type checking
- Runtime validation occurs during data processing
- Ingredient lookup failures gracefully degrade to basic ingredient info

## Performance Considerations

### Data Loading
- Static JSON files loaded at build time
- Large datasets (>2MB) may impact initial load
- Consider implementing pagination for large datasets

### Search Performance
- Client-side search implementation
- Limited to 6 results for performance
- Real-time filtering as user types

### Image Optimization
- Next.js Image component handles optimization
- Lazy loading and responsive sizing
- External image URLs from data source 