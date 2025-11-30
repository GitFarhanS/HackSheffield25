/**
 * StyleSwipe - Tinder-style clothing swiping interface
 */

const API_BASE = 'http://localhost:8000';

// State
let userFolder = null;
let products = [];
let currentProductIndex = 0;
let currentAngle = 'front'; // front, side, back
const angles = ['front', 'side', 'back'];

// DOM Elements
const loadingScreen = document.getElementById('loading-screen');
const swipeContainer = document.getElementById('swipe-container');
const resultsScreen = document.getElementById('results-screen');
const noProductsScreen = document.getElementById('no-products');
const cardsContainer = document.getElementById('cards-container');
const progressText = document.getElementById('progress-text');
const productTitle = document.getElementById('product-title');
const productPrice = document.getElementById('product-price');
const productSource = document.getElementById('product-source');
const likedItems = document.getElementById('liked-items');
const likedCount = document.getElementById('liked-count');
const progressBar = document.getElementById('progress-bar');
const loadingStatus = document.getElementById('loading-status');

// Buttons
const btnLike = document.getElementById('btn-like');
const btnDislike = document.getElementById('btn-dislike');
const btnRestart = document.getElementById('btn-restart');

// Touch handling
let startX = 0;
let startY = 0;
let currentX = 0;
let isDragging = false;

/**
 * Initialize the swipe interface
 */
async function init() {
    // Get user folder from URL or localStorage
    const urlParams = new URLSearchParams(window.location.search);
    userFolder = urlParams.get('user') || localStorage.getItem('userFolder');
    
    if (!userFolder) {
        // No user, redirect to upload page
        window.location.href = 'index.html';
        return;
    }
    
    // Check if we're coming from preferences (loading mode)
    const fromPreferences = urlParams.get('loading') === 'true';
    
    if (fromPreferences) {
        showLoadingScreen();
        await simulateLoading();
    }
    
    // Load products
    await loadProducts();
}

/**
 * Show loading screen with progress
 */
function showLoadingScreen() {
    loadingScreen.classList.remove('hidden');
    swipeContainer.classList.add('hidden');
    resultsScreen.classList.add('hidden');
    noProductsScreen.classList.add('hidden');
}

/**
 * Simulate loading steps
 */
async function simulateLoading() {
    const steps = ['search', 'download', 'generate', 'ready'];
    const stepElements = document.querySelectorAll('.step');
    
    for (let i = 0; i < steps.length; i++) {
        const step = steps[i];
        const progress = ((i + 1) / steps.length) * 100;
        
        // Update progress bar
        progressBar.style.width = `${progress}%`;
        
        // Update step states
        stepElements.forEach((el, index) => {
            if (index < i) {
                el.classList.remove('active');
                el.classList.add('completed');
            } else if (index === i) {
                el.classList.add('active');
                el.classList.remove('completed');
            } else {
                el.classList.remove('active', 'completed');
            }
        });
        
        // Update status text
        const statusTexts = {
            'search': 'Searching for products matching your style...',
            'download': 'Downloading product images...',
            'generate': 'Creating virtual try-on images...',
            'ready': 'All done! Get ready to swipe!'
        };
        loadingStatus.textContent = statusTexts[step];
        
        // Wait before next step
        if (step === 'generate') {
            // Longer wait for generation
            await new Promise(r => setTimeout(r, 3000));
        } else if (step === 'ready') {
            await new Promise(r => setTimeout(r, 1000));
        } else {
            await new Promise(r => setTimeout(r, 1500));
        }
    }
}

/**
 * Load products from API
 */
async function loadProducts() {
    try {
        const response = await fetch(`${API_BASE}/api/swipe/${userFolder}/products`);
        const data = await response.json();
        
        if (!data.products || data.products.length === 0) {
            showNoProducts();
            return;
        }
        
        products = data.products;
        
        // Check swipe status
        const statusResponse = await fetch(`${API_BASE}/api/swipe/${userFolder}/status`);
        const status = await statusResponse.json();
        
        if (status.completed) {
            // Already completed, show results
            showResults();
        } else {
            // Reset to current position
            currentProductIndex = status.swiped || 0;
            showSwipeInterface();
        }
    } catch (error) {
        console.error('Error loading products:', error);
        showNoProducts();
    }
}

/**
 * Show the main swipe interface
 */
function showSwipeInterface() {
    loadingScreen.classList.add('hidden');
    swipeContainer.classList.remove('hidden');
    resultsScreen.classList.add('hidden');
    noProductsScreen.classList.add('hidden');
    
    updateProgress();
    renderCards();
    setupEventListeners();
}

/**
 * Show no products message
 */
function showNoProducts() {
    loadingScreen.classList.add('hidden');
    swipeContainer.classList.add('hidden');
    resultsScreen.classList.add('hidden');
    noProductsScreen.classList.remove('hidden');
}

/**
 * Show results screen
 */
async function showResults() {
    loadingScreen.classList.add('hidden');
    swipeContainer.classList.add('hidden');
    resultsScreen.classList.remove('hidden');
    noProductsScreen.classList.add('hidden');
    
    await loadLikedProducts();
}

/**
 * Load liked products for results display
 */
async function loadLikedProducts() {
    try {
        const response = await fetch(`${API_BASE}/api/swipe/${userFolder}/liked`);
        const data = await response.json();
        
        likedCount.textContent = data.total || 0;
        
        if (data.liked_products && data.liked_products.length > 0) {
            renderLikedProducts(data.liked_products);
        } else {
            likedItems.innerHTML = `
                <div class="empty-state" style="grid-column: 1/-1;">
                    <span class="empty-icon">💔</span>
                    <h2>No Liked Items</h2>
                    <p>You didn't like any items. Try again with different preferences!</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading liked products:', error);
    }
}

/**
 * Render liked products in results
 * Shows all liked products even if some images are missing
 */
function renderLikedProducts(likedProducts) {
    likedItems.innerHTML = likedProducts.map(product => {
        // Build image URLs - use API path if available, fallback to thumbnail
        const getImageUrl = (angle) => {
            if (product.images?.[angle]) {
                return `${API_BASE}/api/image/${product.images[angle]}`;
            }
            return null;
        };
        
        const frontImg = getImageUrl('front');
        const sideImg = getImageUrl('side');
        const backImg = getImageUrl('back');
        
        // Use thumbnail as fallback if no images available
        const fallbackImg = product.thumbnail || '';
        const hasAnyImage = frontImg || sideImg || backImg || fallbackImg;
        
        const ratingHtml = product.rating ? 
            `<p class="rating">⭐ ${product.rating} (${product.reviews || 0} reviews)</p>` : '';
        
        // Create image elements - show placeholder for missing angles
        const createImgElement = (src, alt) => {
            if (src) {
                return `<img src="${src}" alt="${alt}" onerror="this.style.display='none'">`;
            }
            return `<div class="no-image-placeholder" title="Image not available"></div>`;
        };
        
        return `
            <div class="liked-item">
                <div class="liked-item-images">
                    ${frontImg ? createImgElement(frontImg, 'Front view') : 
                        (fallbackImg ? createImgElement(fallbackImg, 'Product') : createImgElement(null, 'Front'))}
                    ${createImgElement(sideImg, 'Side view')}
                    ${createImgElement(backImg, 'Back view')}
                </div>
                <div class="liked-item-info">
                    <h3>${product.title || 'Product'}</h3>
                    <p class="price">${product.price || 'N/A'}</p>
                    <p class="source">${product.source || ''}</p>
                    ${ratingHtml}
                    ${product.product_link ? 
                        `<a href="${product.product_link}" target="_blank" class="btn-purchase">View & Purchase →</a>` :
                        ''
                    }
                </div>
            </div>
        `;
    }).join('');
}

/**
 * Update progress display
 */
function updateProgress() {
    const total = products.length;
    const current = Math.min(currentProductIndex + 1, total);
    progressText.textContent = `${current} / ${total}`;
}

/**
 * Render cards for current product
 */
function renderCards() {
    if (currentProductIndex >= products.length) {
        showResults();
        return;
    }
    
    const currentProduct = products[currentProductIndex];
    currentAngle = 'front';
    
    // Update product info
    productTitle.textContent = currentProduct.title || 'Unknown Product';
    productPrice.textContent = currentProduct.price || 'N/A';
    productSource.textContent = currentProduct.source || '';
    
    // Update angle indicator
    updateAngleIndicator();
    
    // Create card
    const imagePath = currentProduct.images?.[currentAngle];
    const imageUrl = imagePath ? 
        `${API_BASE}/api/image/${userFolder.split('/').pop()}/${imagePath.split(userFolder.split('/').pop() + '/')[1]}` :
        currentProduct.thumbnail || '';
    
    cardsContainer.innerHTML = `
        <div class="swipe-card" id="current-card">
            <img src="${imageUrl}" alt="${currentProduct.title}" onerror="this.src='${currentProduct.thumbnail || ''}'">
            <div class="card-overlay">
                <div class="like-indicator">LIKE</div>
                <div class="nope-indicator">NOPE</div>
            </div>
        </div>
    `;
    
    // Setup drag listeners on the new card
    setupCardDrag();
}

/**
 * Update angle indicator dots
 */
function updateAngleIndicator() {
    document.querySelectorAll('.angle-dot').forEach(dot => {
        dot.classList.toggle('active', dot.dataset.angle === currentAngle);
    });
}

/**
 * Cycle to next angle on card tap
 */
function cycleAngle() {
    const currentIndex = angles.indexOf(currentAngle);
    currentAngle = angles[(currentIndex + 1) % angles.length];
    
    const currentProduct = products[currentProductIndex];
    const imagePath = currentProduct.images?.[currentAngle];
    const imageUrl = imagePath ? 
        `${API_BASE}/api/image/${userFolder.split('/').pop()}/${imagePath.split(userFolder.split('/').pop() + '/')[1]}` :
        currentProduct.thumbnail || '';
    
    const cardImg = document.querySelector('.swipe-card img');
    if (cardImg) {
        cardImg.src = imageUrl;
    }
    
    updateAngleIndicator();
}

/**
 * Setup card drag functionality
 */
function setupCardDrag() {
    const card = document.getElementById('current-card');
    if (!card) return;
    
    // Touch events
    card.addEventListener('touchstart', handleDragStart);
    card.addEventListener('touchmove', handleDragMove);
    card.addEventListener('touchend', handleDragEnd);
    
    // Mouse events
    card.addEventListener('mousedown', handleDragStart);
    document.addEventListener('mousemove', handleDragMove);
    document.addEventListener('mouseup', handleDragEnd);
    
    // Click for angle change
    card.addEventListener('click', (e) => {
        if (!isDragging && Math.abs(currentX - startX) < 10) {
            cycleAngle();
        }
    });
}

/**
 * Handle drag start
 */
function handleDragStart(e) {
    if (e.type === 'mousedown') {
        startX = e.clientX;
        startY = e.clientY;
    } else {
        startX = e.touches[0].clientX;
        startY = e.touches[0].clientY;
    }
    currentX = startX;
    isDragging = true;
    
    const card = document.getElementById('current-card');
    if (card) {
        card.classList.add('dragging');
    }
}

/**
 * Handle drag move
 */
function handleDragMove(e) {
    if (!isDragging) return;
    
    let clientX, clientY;
    if (e.type === 'mousemove') {
        clientX = e.clientX;
        clientY = e.clientY;
    } else {
        clientX = e.touches[0].clientX;
        clientY = e.touches[0].clientY;
    }
    
    currentX = clientX;
    const deltaX = clientX - startX;
    const deltaY = clientY - startY;
    const rotation = deltaX * 0.1;
    
    const card = document.getElementById('current-card');
    if (card) {
        card.style.transform = `translateX(${deltaX}px) translateY(${deltaY}px) rotate(${rotation}deg)`;
        
        // Show indicators
        if (deltaX > 50) {
            card.classList.add('swiping-right');
            card.classList.remove('swiping-left');
        } else if (deltaX < -50) {
            card.classList.add('swiping-left');
            card.classList.remove('swiping-right');
        } else {
            card.classList.remove('swiping-left', 'swiping-right');
        }
    }
}

/**
 * Handle drag end
 */
function handleDragEnd(e) {
    if (!isDragging) return;
    isDragging = false;
    
    const card = document.getElementById('current-card');
    if (!card) return;
    
    card.classList.remove('dragging');
    
    const deltaX = currentX - startX;
    const threshold = 100;
    
    if (deltaX > threshold) {
        // Swipe right - like
        swipeCard('right');
    } else if (deltaX < -threshold) {
        // Swipe left - dislike
        swipeCard('left');
    } else {
        // Return to center
        card.style.transform = '';
        card.classList.remove('swiping-left', 'swiping-right');
    }
}

/**
 * Swipe card in a direction
 */
async function swipeCard(direction) {
    const card = document.getElementById('current-card');
    if (!card) return;
    
    const liked = direction === 'right';
    const currentProduct = products[currentProductIndex];
    
    // Animate out
    card.classList.add(liked ? 'fly-right' : 'fly-left');
    
    // Record swipe
    try {
        await fetch(`${API_BASE}/api/swipe/${userFolder}/action`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                product_id: currentProduct.product_id,
                liked: liked
            })
        });
    } catch (error) {
        console.error('Error recording swipe:', error);
    }
    
    // Move to next
    setTimeout(() => {
        currentProductIndex++;
        updateProgress();
        renderCards();
    }, 400);
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    btnLike.addEventListener('click', () => swipeCard('right'));
    btnDislike.addEventListener('click', () => swipeCard('left'));
    btnRestart.addEventListener('click', resetAndRestart);
}

/**
 * Reset and restart swiping
 */
async function resetAndRestart() {
    try {
        await fetch(`${API_BASE}/api/swipe/${userFolder}/reset`, {
            method: 'POST'
        });
        
        currentProductIndex = 0;
        currentAngle = 'front';
        showSwipeInterface();
    } catch (error) {
        console.error('Error resetting:', error);
    }
}

// Initialize on load
document.addEventListener('DOMContentLoaded', init);

