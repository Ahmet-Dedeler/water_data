# Setup Guide

This guide provides detailed instructions for setting up the Water Bottles Health Leaderboard application for development and production.

## Prerequisites

### System Requirements
- **Operating System**: Windows 10/11, macOS 10.15+, or Linux
- **Node.js**: Version 18.0.0 or higher
- **npm**: Version 8.0.0 or higher (comes with Node.js)
- **Python**: Version 3.7 or higher
- **Git**: Latest version
- **Code Editor**: VS Code, WebStorm, or similar

### Recommended Tools
- **Terminal**: PowerShell (Windows), Terminal (macOS), or Bash (Linux)
- **Browser**: Chrome, Firefox, Safari, or Edge (latest versions)
- **Git Client**: Command line or GUI client like GitHub Desktop

## Installation

### 1. Clone the Repository

```bash
# Clone the repository
git clone https://github.com/your-username/water_bottles.git

# Navigate to project directory
cd water_bottles
```

### 2. Frontend Setup

#### Install Node.js Dependencies
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Verify installation
npm list --depth=0
```

#### Environment Configuration
Create a `.env.local` file in the `frontend` directory for environment variables:

```bash
# frontend/.env.local
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

#### Development Server
```bash
# Start development server with Turbopack (faster)
npm run dev

# Alternative: Start without Turbopack
npm run dev -- --no-turbo

# The application will be available at http://localhost:3000
```

### 3. Data Scraper Setup

#### Install Python Dependencies
```bash
# Navigate back to project root
cd ..

# Create virtual environment (recommended)
python -m venv water_env

# Activate virtual environment
# On Windows:
water_env\Scripts\activate
# On macOS/Linux:
source water_env/bin/activate

# Install requirements
pip install -r requirements.txt

# Verify installation
pip list
```

#### Environment Configuration for Scraper
Create a `.env` file in the project root if API keys are needed:

```bash
# .env (if required by API)
API_KEY=your_api_key_here
```

#### Run Data Scraper
```bash
# Fetch latest water data
python scraper.py

# Verify data was created
ls -la water_data.json
```

## Configuration

### Frontend Configuration

#### Next.js Configuration
The `next.config.ts` file contains Next.js specific settings:

```typescript
// next.config.ts
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
    images: {
        domains: ['external-image-domain.com'], // Add external image domains
    },
    // Additional configurations
};

export default nextConfig;
```

#### Tailwind CSS Configuration
Tailwind CSS 4 is configured via `postcss.config.mjs`:

```javascript
// postcss.config.mjs
import tailwindcss from '@tailwindcss/postcss';

export default {
    plugins: [tailwindcss],
};
```

#### TypeScript Configuration
TypeScript settings in `tsconfig.json`:

```json
{
    "compilerOptions": {
        "lib": ["dom", "dom.iterable", "es6"],
        "allowJs": true,
        "skipLibCheck": true,
        "strict": true,
        "noEmit": true,
        "esModuleInterop": true,
        "module": "esnext",
        "moduleResolution": "bundler",
        "resolveJsonModule": true,
        "isolatedModules": true,
        "jsx": "preserve",
        "incremental": true,
        "plugins": [
            {
                "name": "next"
            }
        ],
        "baseUrl": ".",
        "paths": {
            "@/*": ["./src/*"]
        }
    },
    "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
    "exclude": ["node_modules"]
}
```

### Data Configuration

#### Water Data Location
Ensure the data files are in the correct locations:
```
frontend/src/data/
├── water_data.json      # Main water data (scraped)
└── ingredients.json     # Ingredient information
```

#### Data File Structure
The scraper outputs data to the project root, so you may need to copy it:

```bash
# Copy scraped data to frontend data directory
cp water_data.json frontend/src/data/water_data.json
```

## Development Workflow

### Daily Development
1. **Start Frontend**: `cd frontend && npm run dev`
2. **Make Changes**: Edit components, pages, or styles
3. **Hot Reload**: Changes appear automatically in browser
4. **Test Features**: Verify functionality works as expected

### Data Updates
1. **Run Scraper**: `python scraper.py`
2. **Copy Data**: Update frontend data files if needed
3. **Restart Server**: Restart Next.js to load new data

### Code Quality
```bash
# Run linter
npm run lint

# Fix linting issues automatically
npm run lint -- --fix

# Type checking
npx tsc --noEmit
```

## Production Deployment

### Build Process
```bash
# Navigate to frontend
cd frontend

# Create production build
npm run build

# Test production build locally
npm start
```

### Performance Optimization
1. **Image Optimization**: Next.js automatically optimizes images
2. **Code Splitting**: Automatic with Next.js App Router
3. **Static Assets**: Served efficiently from `/public` directory
4. **Data Files**: Consider CDN for large JSON files

### Deployment Platforms

#### Vercel (Recommended)
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy from frontend directory
cd frontend
vercel

# Follow prompts for configuration
```

#### Other Platforms
- **Netlify**: Upload build folder from `frontend/.next`
- **AWS S3**: Static hosting with CloudFront
- **GitHub Pages**: For static builds only

## Troubleshooting

### Common Frontend Issues

#### Node.js Version Issues
```bash
# Check Node.js version
node --version

# Use Node Version Manager (if available)
nvm use 18
nvm install 18.0.0
```

#### Dependency Conflicts
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

#### Port Already in Use
```bash
# Kill process using port 3000
# Windows:
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# macOS/Linux:
lsof -ti:3000 | xargs kill -9

# Or use different port
npm run dev -- -p 3001
```

### Common Python Issues

#### Virtual Environment Issues
```bash
# Recreate virtual environment
rm -rf water_env
python -m venv water_env
source water_env/bin/activate  # or water_env\Scripts\activate on Windows
pip install -r requirements.txt
```

#### API Connection Issues
```bash
# Test API connectivity
curl https://app.oasis-health.com/api/items/bottled_water/

# Check network/firewall settings
# Verify API endpoints are accessible
```

#### Data File Issues
```bash
# Check if data file was created
ls -la water_data.json

# Validate JSON format
python -m json.tool water_data.json > /dev/null

# Check file permissions
chmod 644 water_data.json
```

### TypeScript Issues

#### Type Errors
```bash
# Check TypeScript compilation
npx tsc --noEmit

# Update type definitions
npm update @types/node @types/react @types/react-dom
```

#### Import Path Issues
```bash
# Verify tsconfig.json paths configuration
# Ensure files exist at specified paths
# Check case sensitivity on file names
```

### Performance Issues

#### Large Data Files
- Consider implementing pagination
- Use data streaming for large datasets
- Implement client-side caching

#### Slow Search
- Implement debouncing for search input
- Consider server-side search for large datasets
- Add search indexing

## IDE Setup

### VS Code Extensions
- **ES7+ React/Redux/React-Native snippets**
- **Tailwind CSS IntelliSense**
- **TypeScript Importer**
- **Prettier - Code formatter**
- **ESLint**
- **Auto Rename Tag**

### VS Code Settings
```json
{
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "typescript.preferences.includePackageJsonAutoImports": "on",
    "tailwindCSS.includeLanguages": {
        "typescript": "typescript",
        "typescriptreact": "typescriptreact"
    }
}
```

## Support

### Getting Help
1. **Check Documentation**: Review all documentation files
2. **Search Issues**: Look for similar problems in project issues
3. **Check Logs**: Review console output for error messages
4. **Community**: Reach out to the development community

### Reporting Issues
When reporting issues, include:
- Operating system and version
- Node.js and npm versions
- Python version
- Complete error messages
- Steps to reproduce the issue
- Expected vs actual behavior 