// Drag and drop for moving files/folders (simplified)
document.addEventListener('DOMContentLoaded', () => {
    const cards = document.querySelectorAll('.card');
    
    cards.forEach(card => {
        card.draggable = true;
        
        card.addEventListener('dragstart', (e) => {
            e.dataTransfer.setData('text/plain', card.dataset.id);
            card.classList.add('dragging');
        });
        
        card.addEventListener('dragend', () => {
            card.classList.remove('dragging');
        });
    });
    
    const folders = document.querySelectorAll('.folder-card');
    folders.forEach(folder => {
        folder.addEventListener('dragover', (e) => {
            e.preventDefault();
            folder.classList.add('drag-over');
        });
        
        folder.addEventListener('dragleave', () => {
            folder.classList.remove('drag-over');
        });
        
        folder.addEventListener('drop', (e) => {
            e.preventDefault();
            folder.classList.remove('drag-over');
            const draggedId = e.dataTransfer.getData('text/plain');
            const targetFolder = folder.dataset.id;
            
            if (draggedId !== targetFolder) {
                moveItem(draggedId, targetFolder);
            }
        });
    });
});

async function moveItem(itemId, targetFolder) {
    console.log(`Moving ${itemId} to ${targetFolder}`);
    showToast(`Moving item...`, 'info');
    
    const fileName = itemId.split('/').pop();
    const newPath = `${targetFolder}/${fileName}`;
    
    const formData = new FormData();
    formData.append('old_name', itemId);
    formData.append('new_name', newPath);
    
    try {
        const response = await fetch('/rename', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            showToast('Item moved successfully', 'success');
            setTimeout(() => location.reload(), 500);
        } else {
            showToast('Failed to move item', 'error');
        }
    } catch (error) {
        showToast('Error moving item', 'error');
    }
}

// Add some styles for drag and drop
const ddStyle = document.createElement('style');
ddStyle.textContent = `
    .card.dragging { opacity: 0.5; }
    .folder-card.drag-over { background-color: var(--selected-bg); border: 2px dashed var(--primary-color); }
`;
document.head.appendChild(ddStyle);
