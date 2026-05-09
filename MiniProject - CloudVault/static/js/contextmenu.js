function showContextMenu(e, id, type) {
    e.preventDefault();
    
    state.selectedItem = { id, type };
    
    const menu = document.getElementById('contextMenu');
    menu.style.display = 'block';
    
    // Position menu
    let x = e.clientX;
    let y = e.clientY;
    
    // Check boundaries
    const winWidth = window.innerWidth;
    const winHeight = window.innerHeight;
    const menuWidth = menu.offsetWidth;
    const menuHeight = menu.offsetHeight;
    
    if (x + menuWidth > winWidth) x = winWidth - menuWidth;
    if (y + menuHeight > winHeight) y = winHeight - menuHeight;
    
    menu.style.left = x + 'px';
    menu.style.top = y + 'px';
}

function handleDownload() {
    if (!state.selectedItem) return;
    const { id } = state.selectedItem;
    window.location.href = `/download/${id}`;
}

function handleRename() {
    if (!state.selectedItem) return;
    const { id } = state.selectedItem;
    const newName = prompt('Enter new name:', id.split('/').pop());
    
    if (newName && newName !== id.split('/').pop()) {
        const formData = new FormData();
        formData.append('old_name', id);
        formData.append('new_name', newName);
        
        // Use Fetch for rename
        fetch('/rename', {
            method: 'POST',
            body: formData
        }).then(() => location.reload());
    }
}

function handleDelete() {
    if (!state.selectedItem) return;
    const { id, type } = state.selectedItem;
    
    if (confirm(`Are you sure you want to delete this ${type}?`)) {
        window.location.href = `/delete/${id}`;
    }
}

function handleShare() {
    if (!state.selectedItem) return;
    const email = prompt('Enter email to share with:');
    if (email) {
        const formData = new FormData();
        formData.append('email', email);
        formData.append('permission', 'read');
        
        fetch('/share', {
            method: 'POST',
            body: formData
        }).then(() => showToast('Shared successfully!', 'success'));
    }
}
