let selectedItems = new Set();

function toggleSelection(event, id) {
    // If clicking on an action button, don't toggle selection
    if (event.target.closest('.card-actions') || event.target.closest('.icon-btn-sm')) {
        return;
    }
    
    const card = document.querySelector(`.card[data-id="${id}"]`);
    
    if (selectedItems.has(id)) {
        selectedItems.delete(id);
        card.classList.remove('selected');
    } else {
        selectedItems.add(id);
        card.classList.add('selected');
    }
    
    updateBulkBar();
}

function updateBulkBar() {
    const bar = document.getElementById('bulkActionBar');
    const countSpan = document.getElementById('selectedCount');
    
    if (selectedItems.size > 0) {
        bar.classList.remove('hidden');
        countSpan.innerText = selectedItems.size;
    } else {
        bar.classList.add('hidden');
    }
}

function clearSelection() {
    selectedItems.clear();
    document.querySelectorAll('.card.selected').forEach(c => c.classList.remove('selected'));
    updateBulkBar();
}

async function bulkDelete() {
    if (!confirm(`Are you sure you want to delete ${selectedItems.size} items?`)) return;
    
    showToast('Deleting items...', 'info');
    
    const promises = Array.from(selectedItems).map(id => {
        const type = document.querySelector(`.card[data-id="${id}"]`).dataset.type;
        const formData = new FormData();
        formData.append('filename', id);
        formData.append('type', type);
        return fetch('/delete', { method: 'POST', body: formData });
    });
    
    await Promise.all(promises);
    showToast('Items deleted', 'success');
    setTimeout(() => location.reload(), 500);
}

function bulkDownload() {
    showToast('Preparing ZIP download...', 'info');
    
    const items = Array.from(selectedItems);
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/bulk-download';
    
    const input = document.createElement('input');
    input.type = 'hidden';
    input.name = 'items';
    input.value = JSON.stringify(items);
    
    form.appendChild(input);
    document.body.appendChild(form);
    form.submit();
    document.body.removeChild(form);
}
