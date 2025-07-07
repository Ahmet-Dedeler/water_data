// API Base URL
const API_BASE = '/api/v1';

// Global state
let currentPage = 1;
let currentQuery = {};
let cachedStats = null;

// Utility functions
function formatScore(score) {
    return Math.round(score * 10) / 10;
}

function getScoreClass(score) {
    if (score >= 80) return 'score-excellent';
    if (score >= 70) return 'score-good';
    if (score >= 60) return 'score-fair';
    return 'score-poor';
}

function getHealthStatusBadge(status) {
    const badges = {
        'excellent': 'bg-green-100 text-green-800',
        'good': 'bg-blue-100 text-blue-800',
        'fair': 'bg-yellow-100 text-yellow-800',
        'poor': 'bg-red-100 text-red-800'
    };
    return badges[status] || 'bg-gray-100 text-gray-800';
}

// API functions
async function fetchAPI(endpoint, params = {}) {
    try {
        const url = new URL(`${window.location.origin}${API_BASE}${endpoint}`);
        Object.keys(params).forEach(key => {
            if (params[key] !== null && params[key] !== undefined && params[key] !== '') {
                url.searchParams.append(key, params[key]);
            }
        });
        
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// Load statistics
async function loadStats() {
    try {
        if (cachedStats) {
            updateStatsDisplay(cachedStats);
            return;
        }
        
        const data = await fetchAPI('/analytics/overview');
        cachedStats = data;
        updateStatsDisplay(data);
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

function updateStatsDisplay(stats) {
    document.getElementById('totalWaters').textContent = stats.total_waters || 0;
    document.getElementById('avgScore').textContent = formatScore(stats.average_score || 0);
    document.getElementById('totalBrands').textContent = stats.total_brands || 0;
    document.getElementById('labTestedCount').textContent = stats.lab_tested_count || 0;
}

// Load featured waters
async function loadFeaturedWaters() {
    try {
        const data = await fetchAPI('/waters/top', { limit: 6 });
        displayWaterCards(data.waters, 'featuredWaters');
    } catch (error) {
        console.error('Error loading featured waters:', error);
    }
}

// Search functionality
async function searchWaters() {
    const searchInput = document.getElementById('searchInput').value;
    const minScore = document.getElementById('minScore').value;
    const packaging = document.getElementById('packaging').value;
    const healthStatus = document.getElementById('healthStatus').value;
    const labTested = document.getElementById('labTested').value;
    const sortBy = document.getElementById('sortBy').value;
    
    const query = {
        q: searchInput,
        min_score: minScore,
        packaging_type: packaging,
        health_status: healthStatus,
        lab_tested: labTested === 'true' ? true : labTested === 'false' ? false : undefined,
        sort_by: sortBy,
        page: currentPage,
        limit: 12
    };
    
    // Remove empty values
    Object.keys(query).forEach(key => {
        if (query[key] === '' || query[key] === undefined) {
            delete query[key];
        }
    });
    
    currentQuery = query;
    
    try {
        showLoading(true);
        showResults(true);
        
        const data = await fetchAPI('/search', query);
        
        document.getElementById('resultCount').textContent = 
            `${data.total} result${data.total !== 1 ? 's' : ''} found`;
        
        displayWaterCards(data.waters, 'resultsGrid');
        updatePagination(data.total, data.page, data.limit);
        
    } catch (error) {
        console.error('Error searching waters:', error);
        showError('Failed to search waters. Please try again.');
    } finally {
        showLoading(false);
    }
}

// Display water cards
function displayWaterCards(waters, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    container.innerHTML = waters.map(water => createWaterCard(water)).join('');
}

function createWaterCard(water) {
    const scoreClass = getScoreClass(water.score || 0);
    const healthBadge = getHealthStatusBadge(water.health_status);
    
    return `
        <div class="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow">
            <div class="flex justify-between items-start mb-4">
                <div>
                    <h4 class="text-lg font-bold text-gray-800">${water.name || 'Unknown'}</h4>
                    <p class="text-sm text-gray-600">${water.brand?.name || 'Unknown Brand'}</p>
                </div>
                <div class="text-right">
                    <div class="text-2xl font-bold ${scoreClass}">
                        ${formatScore(water.score || 0)}
                    </div>
                    <div class="text-sm text-gray-500">Score</div>
                </div>
            </div>
            
            <div class="space-y-2 mb-4">
                <div class="flex justify-between">
                    <span class="text-sm text-gray-600">Packaging:</span>
                    <span class="text-sm font-medium">${water.packaging_type || 'Unknown'}</span>
                </div>
                
                ${water.source?.type ? `
                <div class="flex justify-between">
                    <span class="text-sm text-gray-600">Source:</span>
                    <span class="text-sm font-medium">${water.source.type}</span>
                </div>
                ` : ''}
                
                ${water.lab_tested !== undefined ? `
                <div class="flex justify-between">
                    <span class="text-sm text-gray-600">Lab Tested:</span>
                    <span class="text-sm font-medium ${water.lab_tested ? 'text-green-600' : 'text-gray-500'}">
                        ${water.lab_tested ? 'Yes' : 'No'}
                    </span>
                </div>
                ` : ''}
            </div>
            
            <div class="flex justify-between items-center">
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${healthBadge}">
                    ${(water.health_status || 'unknown').charAt(0).toUpperCase() + (water.health_status || 'unknown').slice(1)}
                </span>
                
                <button 
                    onclick="viewWaterDetails('${water.id}')"
                    class="text-blue-600 hover:text-blue-800 text-sm font-medium"
                >
                    View Details →
                </button>
            </div>
        </div>
    `;
}

// View water details (placeholder)
async function viewWaterDetails(waterId) {
    try {
        const water = await fetchAPI(`/waters/${waterId}`);
        
        // Create a modal or new page to show detailed information
        alert(`Water Details:\n\nName: ${water.name}\nBrand: ${water.brand?.name}\nScore: ${formatScore(water.score)}\n\nThis would open a detailed view in a real application.`);
        
    } catch (error) {
        console.error('Error loading water details:', error);
        showError('Failed to load water details.');
    }
}

// Pagination
function updatePagination(total, page, limit) {
    const totalPages = Math.ceil(total / limit);
    const pagination = document.getElementById('pagination');
    
    if (totalPages <= 1) {
        pagination.classList.add('hidden');
        return;
    }
    
    pagination.classList.remove('hidden');
    
    let buttons = [];
    
    // Previous button
    if (page > 1) {
        buttons.push(`
            <button onclick="changePage(${page - 1})" 
                    class="px-3 py-2 text-blue-600 hover:bg-blue-50 rounded">
                Previous
            </button>
        `);
    }
    
    // Page numbers
    const startPage = Math.max(1, page - 2);
    const endPage = Math.min(totalPages, page + 2);
    
    for (let i = startPage; i <= endPage; i++) {
        const isActive = i === page;
        buttons.push(`
            <button onclick="changePage(${i})" 
                    class="px-3 py-2 ${isActive ? 'bg-blue-600 text-white' : 'text-blue-600 hover:bg-blue-50'} rounded">
                ${i}
            </button>
        `);
    }
    
    // Next button
    if (page < totalPages) {
        buttons.push(`
            <button onclick="changePage(${page + 1})" 
                    class="px-3 py-2 text-blue-600 hover:bg-blue-50 rounded">
                Next
            </button>
        `);
    }
    
    pagination.innerHTML = buttons.join('');
}

function changePage(page) {
    currentPage = page;
    searchWaters();
}

// UI helper functions
function showLoading(show) {
    const spinner = document.getElementById('loadingSpinner');
    if (spinner) {
        spinner.classList.toggle('hidden', !show);
    }
}

function showResults(show) {
    const section = document.getElementById('resultsSection');
    if (section) {
        section.classList.toggle('hidden', !show);
    }
}

function showError(message) {
    // Simple error display - in a real app, you'd use a proper notification system
    alert(message);
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Search button
    document.getElementById('searchBtn')?.addEventListener('click', () => {
        currentPage = 1;
        searchWaters();
    });
    
    // Enter key in search input
    document.getElementById('searchInput')?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            currentPage = 1;
            searchWaters();
        }
    });
    
    // Auto-search when filters change
    const filterElements = ['minScore', 'packaging', 'healthStatus', 'labTested', 'sortBy'];
    filterElements.forEach(id => {
        document.getElementById(id)?.addEventListener('change', () => {
            currentPage = 1;
            searchWaters();
        });
    });
});

// Export functions for global access
window.searchWaters = searchWaters;
window.viewWaterDetails = viewWaterDetails;
window.changePage = changePage;
window.loadStats = loadStats;
window.loadFeaturedWaters = loadFeaturedWaters; 