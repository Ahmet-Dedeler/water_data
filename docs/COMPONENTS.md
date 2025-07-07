# Component Documentation

This document provides detailed information about the React components used in the Water Bottles Health Leaderboard application.

## Component Architecture

The application follows a modular component structure with reusable UI components and page-specific components.

```
src/
├── app/                    # Next.js App Router pages
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Home page
│   └── water/[id]/        # Dynamic water detail pages
└── components/            # Reusable components
    ├── Header.tsx         # Main navigation header
    └── ScoreCircle.tsx    # Circular score visualization
```

## Core Components

### Header Component

**File**: `src/components/Header.tsx`

The main navigation header with integrated search functionality.

#### Props
```typescript
interface HeaderProps {
    waters: WaterData[];  // Array of all water data for search
}
```

#### Features
- **Real-time Search**: Filters water brands as user types
- **Autocomplete Dropdown**: Shows up to 6 matching results
- **Click Outside Detection**: Closes search results when clicking elsewhere
- **Responsive Design**: Adapts to different screen sizes
- **Brand Logo Display**: Shows water brand images in search results

#### Usage
```tsx
import Header from '@/components/Header';
import waterData from '@/data/water_data.json';

<Header waters={waterData} />
```

#### State Management
- `query`: Current search input value
- `results`: Filtered search results
- `isFocused`: Controls search dropdown visibility

#### Search Algorithm
- Searches in both water name and brand name
- Case-insensitive matching
- Minimum 2 characters to trigger search
- Limited to 6 results for performance

#### Styling
- Tailwind CSS classes for styling
- Gray color scheme with hover effects
- Responsive layout with mobile optimizations

---

### ScoreCircle Component

**File**: `src/components/ScoreCircle.tsx`

A circular progress indicator for displaying health scores visually.

#### Props
```typescript
interface ScoreCircleProps {
    score: number;  // Score value (0-100)
}
```

#### Features
- **SVG-based Visualization**: Smooth circular progress animation
- **Dynamic Colors**: Green progress indicator
- **Responsive Size**: Scales appropriately for different contexts
- **Score Display**: Shows numeric score with "/100" suffix

#### Usage
```tsx
import ScoreCircle from '@/components/ScoreCircle';

<ScoreCircle score={85} />
```

#### Technical Implementation
- Uses SVG `circle` elements with `stroke-dasharray` for progress effect
- Calculates circle circumference: `2π × radius`
- Progress offset: `circumference - (score/100) × circumference`
- Rotated -90 degrees to start from top

#### Styling
- 24×24 size (w-24 h-24)
- Gray background circle
- Green progress circle
- Bold score text display

---

## Page Components

### Root Layout

**File**: `src/app/layout.tsx`

The root layout component that wraps all pages.

#### Features
- **SEO Metadata**: Title, description, and Open Graph tags
- **Font Loading**: Inter font from Google Fonts
- **Global Styling**: Background color and base styles
- **HTML Structure**: Proper HTML5 structure

#### Metadata Configuration
```typescript
export const metadata: Metadata = {
    title: {
        default: "Water Brands Leaderboard",
        template: `%s | Water Brands Leaderboard`
    },
    description: "The healthiest bottled waters based on the latest science.",
    openGraph: { /* OpenGraph config */ }
};
```

---

### Water Detail Page

**File**: `src/app/water/[id]/page.tsx`

Dynamic page component for individual water brand details.

#### Features
- **Dynamic Routing**: Uses Next.js dynamic routes with `[id]` parameter
- **Data Fetching**: Loads water data from JSON files
- **SEO Optimization**: Dynamic metadata generation
- **404 Handling**: Returns `notFound()` for invalid IDs
- **Ingredient Processing**: Merges ingredient data with detailed information

#### Key Sections
1. **Hero Section**: Water image, name, and score
2. **Quick Stats**: Lab testing, contaminants, nutrients, microplastics
3. **Description**: Detailed water description
4. **Contaminants**: List of harmful ingredients with risks
5. **Ingredients**: Beneficial minerals with health benefits
6. **Sources**: Research sources (conditionally displayed)

#### Data Processing
```typescript
const getFullIngredient = (ing: Ingredient): Ingredient => {
    const details = allIngredients[ing.ingredient_id];
    return details ? { ...ing, ...details } : ing;
};
```

#### Styling Patterns
- **Red Theme**: Contaminants section (red-50 background, red-500 border)
- **Green Theme**: Nutrients section (green-50 background, green-500 border)
- **Responsive Grid**: 1 column on mobile, 3 columns on desktop
- **Card Layout**: White background with subtle shadows

---

## Styling Conventions

### Color Scheme
- **Primary**: Blue-600 for scores and links
- **Success**: Green-500/50 for beneficial content
- **Warning**: Red-500/50 for harmful content
- **Neutral**: Gray scales for text and backgrounds

### Typography
- **Headings**: Font weights from semibold (600) to extrabold (800)
- **Body Text**: Regular (400) and medium (500) weights
- **Code/Numbers**: Monospace font family for precise display

### Layout Patterns
- **Container**: `max-w-4xl mx-auto px-4` for consistent page width
- **Cards**: White background with border and shadow
- **Responsive**: Mobile-first approach with sm/md/lg breakpoints

### Interactive Elements
- **Hover Effects**: Subtle color changes and underlines
- **Focus States**: Ring-2 focus rings for accessibility
- **Transitions**: Smooth transitions for color changes

## Component Guidelines

### Best Practices
1. **TypeScript**: All components use proper TypeScript interfaces
2. **Accessibility**: Semantic HTML and proper ARIA attributes
3. **Performance**: Image optimization with Next.js Image component
4. **Responsive**: Mobile-first responsive design
5. **Reusability**: Components accept props for different contexts

### File Naming
- **PascalCase**: Component files use PascalCase (e.g., `Header.tsx`)
- **Descriptive**: Names clearly indicate component purpose
- **Extensions**: Use `.tsx` for components with JSX

### Import Patterns
```typescript
// External libraries first
import Link from 'next/link';
import Image from 'next/image';

// Internal imports
import { WaterData } from '@/types';
import Header from '@/components/Header';
```

### State Management
- **useState**: For local component state
- **useEffect**: For side effects and lifecycle events
- **useRef**: For DOM references and imperative operations

## Future Enhancements

### Potential Component Additions
- **Loading Spinner**: For data loading states
- **Error Boundary**: For error handling
- **Pagination**: For large datasets
- **Filter Component**: Advanced filtering options
- **Sort Component**: Multiple sorting options
- **Modal Component**: For detailed ingredient information

### Performance Optimizations
- **React.memo**: For expensive components
- **useMemo**: For expensive calculations
- **Lazy Loading**: For large component trees
- **Virtualization**: For very large lists 