// Global state
const state = {
    theme: localStorage.getItem('theme') || 'light',
    view: localStorage.getItem('view') || 'grid',
    selectedItem: null,
    currentPath: new URLSearchParams(window.location.search).get('path') || ''
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    applyTheme();
    applyView();
    initEventListeners();
});

function initEventListeners() {
    // Theme Toggle
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }

    // View Toggle
    const toggleView = document.getElementById('toggleView');
    if (toggleView) {
        toggleView.addEventListener('click', toggleGridView);
    }

    // Sort Button Dropdown
    const sortBtn = document.getElementById('sortBtn');
    if (sortBtn) {
        sortBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            sortBtn.parentElement.classList.toggle('active');
        });
    }

    // New Button Dropdown
    const newBtn = document.getElementById('newBtn');
    if (newBtn) {
        newBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            newBtn.parentElement.classList.toggle('active');
        });
    }

    // Profile Dropdown
    const profileBtn = document.getElementById('profileBtn');
    if (profileBtn) {
        profileBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            profileBtn.parentElement.classList.toggle('active');
        });
    }

    // Click outside to close dropdowns and context menu
    document.addEventListener('click', () => {
        const menu = document.getElementById('contextMenu');
        if (menu) menu.style.display = 'none';
        
        const activeDropdowns = document.querySelectorAll('.dropdown.active');
        activeDropdowns.forEach(dropdown => dropdown.classList.remove('active'));
    });

    // Close modals on Esc
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeUploadModal();
            closePreviewModal();
        }
    });
}

// Theme Logic
function toggleTheme() {
    state.theme = state.theme === 'light' ? 'dark' : 'light';
    localStorage.setItem('theme', state.theme);
    applyTheme();
}

function applyTheme() {
    document.documentElement.setAttribute('data-theme', state.theme);
    const themeIcon = document.querySelector('#themeToggle i');
    if (themeIcon) {
        themeIcon.className = state.theme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
    }
}

// View Logic
function applyView() {
    const driveView = document.querySelector('.drive-view');
    if (driveView) {
        if (state.view === 'list') {
            driveView.classList.add('list');
        } else {
            driveView.classList.remove('list');
        }
    }
    const viewIcon = document.querySelector('#toggleView i');
    if (viewIcon) {
        viewIcon.className = state.view === 'grid' ? 'fas fa-list' : 'fas fa-th-large';
    }
}

function toggleGridView() {
    state.view = state.view === 'grid' ? 'list' : 'grid';
    localStorage.setItem('view', state.view);
    applyView();
}

// Modal Logic
function openUploadModal() {
    document.getElementById('uploadModal').style.display = 'flex';
}

function closeUploadModal() {
    document.getElementById('uploadModal').style.display = 'none';
}

function openShareModal() {
    document.getElementById('shareModal').style.display = 'flex';
}

function closeShareModal() {
    document.getElementById('shareModal').style.display = 'none';
}

function openCreateFolderModal() {
    const folderName = prompt('Enter folder name:');
    if (folderName) {
        const formData = new FormData();
        formData.append('folder', folderName);
        formData.append('path', state.currentPath);
        
        fetch('/create-folder', {
            method: 'POST',
            body: formData
        }).then(() => location.reload());
    }
}

function openPreviewModal() {
    document.getElementById('previewModal').style.display = 'flex';
}

function closePreviewModal() {
    document.getElementById('previewModal').style.display = 'none';
    // Stop video if playing
    const video = document.getElementById('previewVideo');
    if (video) {
        video.pause();
        video.src = "";
    }
}

// Navigation
function navigateToFolder(path) {
    const currentParams = new URLSearchParams(window.location.search);
    currentParams.set('path', path);
    window.location.href = `${window.location.pathname}?${currentParams.toString()}`;
}

// Sorting
function handleSort(criteria) {
    const params = new URLSearchParams(window.location.search);
    params.set('sort', criteria);
    window.location.href = `${window.location.pathname}?${params.toString()}`;
}

// Deletion
function handleDeleteDirect(id, type) {
    if (confirm(`Are you sure you want to delete this ${type}?`)) {
        window.location.href = `/delete/${id}`;
    }
}

// Toast Notifications (Simple)
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerText = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('show');
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }, 100);
}

// Add simple toast styles
const style = document.createElement('style');
style.textContent = `
    .toast {
        position: fixed;
        bottom: 24px;
        left: 24px;
        background: #323232;
        color: white;
        padding: 12px 24px;
        border-radius: 4px;
        font-size: 14px;
        z-index: 2000;
        opacity: 0;
        transform: translateY(20px);
        transition: all 0.3s ease;
    }
    .toast.show {
        opacity: 1;
        transform: translateY(0);
    }
    .toast-error { background: #d93025; }
    .toast-success { background: #1e8e3e; }
`;
document.head.appendChild(style);
