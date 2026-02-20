const API_BASE_URL = 'http://localhost:5000/api';

// DOM Elements
const navBtns = document.querySelectorAll('.nav-btn');
const views = document.querySelectorAll('.view');
const messagesContainer = document.getElementById('messagesContainer');
const queryInput = document.getElementById('queryInput');
const sendBtn = document.getElementById('sendBtn');
const uploadBtn = document.getElementById('uploadBtn');
const fileInput = document.getElementById('fileInput');
const documentsList = document.getElementById('documentsList');
const uploadProgress = document.getElementById('uploadProgress');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const statusDot = document.getElementById('statusDot');
const statusText = document.getElementById('statusText');

// Sample question buttons
const sampleBtns = document.querySelectorAll('.sample-btn');

// State
let isProcessing = false;

// Navigation
navBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        const targetView = btn.getAttribute('data-view');
        
        navBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        views.forEach(v => v.classList.remove('active'));
        document.getElementById(`${targetView}View`).classList.add('active');
        
        if (targetView === 'documents') {
            loadDocuments();
        } else if (targetView === 'analytics') {
            loadAnalytics();
        }
    });
});

// Sample questions
sampleBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        queryInput.value = btn.textContent;
        sendQuery();
    });
});

// Check system health
async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();
        
        if (data.status === 'healthy') {
            statusDot.style.background = '#10b981';
            statusText.textContent = 'Connected';
        }
    } catch (error) {
        statusDot.style.background = '#ef4444';
        statusText.textContent = 'Disconnected';
        console.error('Health check failed:', error);
    }
}

// Initialize system
async function initializeSystem() {
    try {
        const response = await fetch(`${API_BASE_URL}/initialize`, {
            method: 'POST'
        });
        const data = await response.json();
        console.log('System initialized:', data);
    } catch (error) {
        console.error('Initialization failed:', error);
    }
}

// Query input handling
queryInput.addEventListener('input', () => {
    sendBtn.disabled = queryInput.value.trim() === '' || isProcessing;
    queryInput.style.height = 'auto';
    queryInput.style.height = queryInput.scrollHeight + 'px';
});

queryInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (!sendBtn.disabled) {
            sendQuery();
        }
    }
});

sendBtn.addEventListener('click', sendQuery);

// Send query
async function sendQuery() {
    const question = queryInput.value.trim();
    if (!question || isProcessing) return;
    
    isProcessing = true;
    sendBtn.disabled = true;
    
    // Remove welcome message
    const welcomeMsg = document.querySelector('.welcome-message');
    if (welcomeMsg) {
        welcomeMsg.remove();
    }
    
    // Add user message
    addMessage(question, 'user');
    
    // Clear input
    queryInput.value = '';
    queryInput.style.height = 'auto';
    
    // Add loading message
    const loadingId = addLoadingMessage();
    
    try {
        const response = await fetch(`${API_BASE_URL}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ question })
        });
        
        const data = await response.json();
        
        // Remove loading message
        removeLoadingMessage(loadingId);
        
        if (data.success) {
            addMessage(data.answer, 'assistant', data.sources);
        } else {
            addMessage(`Error: ${data.error}`, 'assistant');
        }
    } catch (error) {
        removeLoadingMessage(loadingId);
        addMessage(`Error: ${error.message}`, 'assistant');
    } finally {
        isProcessing = false;
        sendBtn.disabled = false;
    }
}

// Add message to chat
function addMessage(content, type, sources = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message message-${type}`;
    
    if (type === 'user') {
        messageDiv.innerHTML = `
            <div class="message-content">${escapeHtml(content)}</div>
        `;
    } else {
        let sourcesHtml = '';
        if (sources && sources.length > 0) {
            sourcesHtml = `
                <div class="message-sources">
                    <p>Sources:</p>
                    ${sources.map(s => `<span class="source-tag">${s.source}</span>`).join('')}
                </div>
            `;
        }
        
        messageDiv.innerHTML = `
            <div class="message-avatar">🤖</div>
            <div class="message-content">
                ${escapeHtml(content)}
                ${sourcesHtml}
            </div>
        `;
    }
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Add loading message
function addLoadingMessage() {
    const id = 'loading-' + Date.now();
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message message-loading';
    messageDiv.id = id;
    messageDiv.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="loading-dots">
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
        </div>
    `;
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    return id;
}

// Remove loading message
function removeLoadingMessage(id) {
    const loadingMsg = document.getElementById(id);
    if (loadingMsg) {
        loadingMsg.remove();
    }
}

// File upload
uploadBtn.addEventListener('click', () => {
    fileInput.click();
});

fileInput.addEventListener('change', async (e) => {
    const files = e.target.files;
    if (files.length === 0) return;
    
    for (let file of files) {
        await uploadFile(file);
    }
    
    fileInput.value = '';
    loadDocuments();
});

// Upload file
async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    uploadProgress.style.display = 'block';
    progressFill.style.width = '0%';
    progressText.textContent = `Uploading ${file.name}...`;
    
    try {
        // Simulate progress
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += 10;
            if (progress <= 90) {
                progressFill.style.width = progress + '%';
            }
        }, 200);
        
        const response = await fetch(`${API_BASE_URL}/upload`, {
            method: 'POST',
            body: formData
        });
        
        clearInterval(progressInterval);
        progressFill.style.width = '100%';
        
        const data = await response.json();
        
        if (data.success) {
            progressText.textContent = `✓ ${file.name} uploaded successfully!`;
            setTimeout(() => {
                uploadProgress.style.display = 'none';
            }, 2000);
        } else {
            progressText.textContent = `✗ Error: ${data.error}`;
        }
    } catch (error) {
        progressText.textContent = `✗ Error uploading ${file.name}`;
        console.error('Upload failed:', error);
    }
}

// Load documents
async function loadDocuments() {
    try {
        const response = await fetch(`${API_BASE_URL}/documents`);
        const data = await response.json();
        
        if (data.success && data.documents.length > 0) {
            documentsList.innerHTML = data.documents.map(doc => `
                <div class="doc-item">
                    <div class="doc-item-header">
                        <span class="doc-icon">📄</span>
                        <div>
                            <h4>${escapeHtml(doc.name)}</h4>
                            <p class="doc-meta">${doc.chunks} chunks</p>
                        </div>
                    </div>
                </div>
            `).join('');
        } else {
            documentsList.innerHTML = '<div class="loading-placeholder">No documents uploaded yet</div>';
        }
    } catch (error) {
        documentsList.innerHTML = '<div class="loading-placeholder">Error loading documents</div>';
        console.error('Failed to load documents:', error);
    }
}

// Load analytics
async function loadAnalytics() {
    try {
        const response = await fetch(`${API_BASE_URL}/analytics`);
        const data = await response.json();
        
        if (data.success) {
            const analytics = data.analytics;
            
            // Update stats
            document.getElementById('statDocs').textContent = analytics.stats.total_documents;
            document.getElementById('statChunks').textContent = analytics.stats.total_chunks;
            document.getElementById('statQueries').textContent = analytics.stats.total_queries;
            document.getElementById('statTime').textContent = analytics.stats.avg_response_time + 's';
            
            // Document distribution chart
            if (analytics.document_distribution.labels.length > 0) {
                createDocChart(analytics.document_distribution);
            }
            
            // Query timeline chart
            createQueryChart(analytics.query_timeline);
        }
    } catch (error) {
        console.error('Failed to load analytics:', error);
    }
}

// Create document chart
function createDocChart(data) {
    const ctx = document.getElementById('docChart');
    if (!ctx) return;
    
    // Destroy existing chart
    if (window.docChartInstance) {
        window.docChartInstance.destroy();
    }
    
    window.docChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.labels,
            datasets: [{
                data: data.values,
                backgroundColor: [
                    '#667eea',
                    '#764ba2',
                    '#f093fb',
                    '#4facfe',
                    '#43e97b'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    labels: {
                        color: '#a0aec0'
                    }
                }
            }
        }
    });
}

// Create query chart
function createQueryChart(data) {
    const ctx = document.getElementById('queryChart');
    if (!ctx) return;
    
    // Destroy existing chart
    if (window.queryChartInstance) {
        window.queryChartInstance.destroy();
    }
    
    window.queryChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.hours,
            datasets: [{
                label: 'Queries',
                data: data.queries,
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: '#a0aec0'
                    },
                    grid: {
                        color: '#2d3561'
                    }
                },
                x: {
                    ticks: {
                        color: '#a0aec0'
                    },
                    grid: {
                        color: '#2d3561'
                    }
                }
            },
            plugins: {
                legend: {
                    labels: {
                        color: '#a0aec0'
                    }
                }
            }
        }
    });
}

// Utility functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize app
checkHealth();
initializeSystem();
setInterval(checkHealth, 30000); // Check health every 30 seconds