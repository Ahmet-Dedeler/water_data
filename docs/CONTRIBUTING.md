# Contributing Guide

Thank you for your interest in contributing to the Water Bottles Health Leaderboard project! This guide will help you get started with contributing to our codebase.

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Process](#development-process)
- [Coding Standards](#coding-standards)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)
- [Testing Guidelines](#testing-guidelines)

## Code of Conduct

### Our Pledge
We are committed to making participation in this project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, sex characteristics, gender identity and expression, level of experience, education, socio-economic status, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Expected Behavior
- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

## Getting Started

### Prerequisites
Before contributing, ensure you have completed the [Setup Guide](./SETUP.md) and have a working development environment.

### First-Time Contributors
1. **Fork the Repository**: Click the "Fork" button on GitHub
2. **Clone Your Fork**: 
   ```bash
   git clone https://github.com/your-username/water_bottles.git
   cd water_bottles
   ```
3. **Add Upstream Remote**:
   ```bash
   git remote add upstream https://github.com/original-owner/water_bottles.git
   ```
4. **Create Development Branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

### Finding Issues to Work On
- Look for issues labeled `good first issue` for beginners
- Check `help wanted` label for issues needing contributors
- Review the project roadmap in issues or project boards

## Development Process

### Branch Naming Convention
Use descriptive branch names that follow this pattern:
- `feature/description` - New features
- `bugfix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring
- `test/description` - Adding or updating tests

Examples:
- `feature/add-water-comparison`
- `bugfix/fix-search-dropdown`
- `docs/update-api-documentation`

### Development Workflow
1. **Sync with Upstream**:
   ```bash
   git fetch upstream
   git checkout main
   git merge upstream/main
   ```

2. **Create Feature Branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make Changes**: Implement your feature or fix
4. **Test Changes**: Ensure all tests pass and functionality works
5. **Commit Changes**: Follow commit message guidelines
6. **Push to Fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create Pull Request**: Submit PR for review

## Coding Standards

### TypeScript/JavaScript
- **Strict TypeScript**: Use strict typing, avoid `any` type
- **Functional Components**: Prefer functional components with hooks
- **Destructuring**: Use object/array destructuring where appropriate
- **Arrow Functions**: Use arrow functions for callbacks and short functions

```typescript
// Good
const handleSearch = (query: string): WaterData[] => {
    return waters.filter(water => 
        water.name.toLowerCase().includes(query.toLowerCase())
    );
};

// Avoid
function handleSearch(query) {
    return waters.filter(function(water) {
        return water.name.toLowerCase().includes(query.toLowerCase());
    });
}
```

### React Best Practices
- **Component Names**: Use PascalCase for component names
- **Props Interface**: Define TypeScript interfaces for all props
- **Hooks**: Follow React hooks rules and guidelines
- **Performance**: Use `useMemo` and `useCallback` for expensive operations

```typescript
// Good
interface WaterCardProps {
    water: WaterData;
    onSelect?: (id: number) => void;
}

const WaterCard: React.FC<WaterCardProps> = ({ water, onSelect }) => {
    const handleClick = useCallback(() => {
        onSelect?.(water.id);
    }, [water.id, onSelect]);

    return (
        <div onClick={handleClick}>
            {water.name}
        </div>
    );
};
```

### CSS/Styling
- **Tailwind CSS**: Use Tailwind utility classes consistently
- **Responsive Design**: Always consider mobile-first approach
- **Color Consistency**: Use project color scheme defined in documentation
- **Accessibility**: Ensure proper contrast ratios and focus states

```tsx
// Good
<button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:outline-none">
    Search
</button>

// Avoid inline styles
<button style={{padding: '8px 16px', backgroundColor: '#2563eb'}}>
    Search
</button>
```

### File Organization
- **Components**: One component per file
- **Imports**: Group imports (external libraries, internal modules, types)
- **Exports**: Use default exports for components, named exports for utilities

```typescript
// Good import order
import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import Image from 'next/image';

import { WaterData } from '@/types';
import Header from '@/components/Header';
import { formatScore } from '@/utils/helpers';
```

## Commit Guidelines

### Commit Message Format
Follow the conventional commit format:
```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Commit Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Formatting changes (no code logic changes)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples
```bash
git commit -m "feat(search): add real-time search functionality"
git commit -m "fix(header): resolve dropdown positioning issue"
git commit -m "docs(api): update water data schema documentation"
git commit -m "refactor(components): extract reusable card component"
```

### Commit Best Practices
- **Atomic Commits**: One logical change per commit
- **Clear Messages**: Describe what and why, not how
- **Present Tense**: Use present tense ("add" not "added")
- **Character Limit**: Keep subject line under 50 characters

## Pull Request Process

### Before Submitting
1. **Update Documentation**: Update relevant documentation for changes
2. **Test Changes**: Ensure all existing tests pass
3. **Lint Code**: Run linting and fix any issues
4. **Build Check**: Verify production build works

```bash
# Pre-submission checklist
npm run lint
npm run build
npm test # when tests are available
```

### PR Description Template
```markdown
## Description
Brief description of changes made.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] I have tested these changes locally
- [ ] All existing tests pass
- [ ] I have added tests for new functionality (if applicable)

## Screenshots (if applicable)
[Add screenshots for UI changes]

## Checklist
- [ ] My code follows the project's coding standards
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
```

### Review Process
1. **Automated Checks**: Ensure all CI/CD checks pass
2. **Peer Review**: Wait for at least one review from maintainers
3. **Address Feedback**: Make requested changes promptly
4. **Final Approval**: Merge only after approval from maintainers

## Issue Reporting

### Bug Reports
When reporting bugs, include:

```markdown
**Bug Description**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected Behavior**
A clear and concise description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Environment:**
- OS: [e.g. Windows 11, macOS 12.6]
- Browser: [e.g. Chrome 108, Safari 16]
- Node.js Version: [e.g. 18.12.0]

**Additional Context**
Add any other context about the problem here.
```

### Feature Requests
```markdown
**Feature Description**
A clear and concise description of what you want to happen.

**Problem it Solves**
Explain the problem this feature would solve.

**Proposed Solution**
Describe the solution you'd like.

**Alternatives Considered**
Describe any alternative solutions or features you've considered.

**Additional Context**
Add any other context, mockups, or examples about the feature request here.
```

## Testing Guidelines

### Testing Strategy
- **Unit Tests**: Test individual functions and components
- **Integration Tests**: Test component interactions
- **E2E Tests**: Test complete user workflows

### Writing Tests
When tests are implemented, follow these patterns:

```typescript
// Component test example
import { render, screen, fireEvent } from '@testing-library/react';
import SearchComponent from '@/components/SearchComponent';

describe('SearchComponent', () => {
    it('should filter results based on input', () => {
        const mockWaters = [
            { id: 1, name: 'Aquafina', brand: { name: 'PepsiCo' } },
            { id: 2, name: 'Dasani', brand: { name: 'Coca-Cola' } }
        ];

        render(<SearchComponent waters={mockWaters} />);
        
        const searchInput = screen.getByPlaceholderText('Search for a water brand...');
        fireEvent.change(searchInput, { target: { value: 'Aqua' } });
        
        expect(screen.getByText('Aquafina')).toBeInTheDocument();
        expect(screen.queryByText('Dasani')).not.toBeInTheDocument();
    });
});
```

### Test Coverage
- Aim for high test coverage on critical components
- Focus on edge cases and error scenarios
- Test accessibility features

## Release Process

### Version Numbering
We follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist
1. Update version numbers
2. Update CHANGELOG.md
3. Create release notes
4. Tag the release
5. Deploy to production

## Recognition

### Contributors
We recognize all types of contributions:
- Code contributions
- Documentation improvements
- Bug reports and feature requests
- Design contributions
- Community support

### Attribution
Contributors will be listed in:
- Repository contributors list
- CONTRIBUTORS.md file (if created)
- Release notes for significant contributions

## Questions?

### Getting Help
- **Documentation**: Check all documentation files first
- **Issues**: Search existing issues for similar questions
- **Discussions**: Use GitHub Discussions for general questions
- **Contact**: Reach out to maintainers for specific guidance

### Contact Information
- **Project Maintainer**: [Your GitHub Username]
- **Email**: [your-email@example.com] (if applicable)
- **Discord/Slack**: [Community links if available]

Thank you for contributing to making water health information more accessible to everyone! 🌊 