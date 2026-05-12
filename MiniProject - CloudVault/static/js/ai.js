function openAIModal(filename) {
    const modal = document.getElementById('aiModal');
    const loading = document.getElementById('aiLoading');
    const content = document.getElementById('aiContent');
    const filenameEl = document.getElementById('aiFilename');
    
    filenameEl.textContent = filename.split('/').pop();
    modal.classList.add('active');
    loading.classList.remove('hidden');
    content.classList.add('hidden');
    
    fetch(`/ai/summarize/${filename}`)
        .then(response => response.json())
        .then(data => {
            loading.classList.add('hidden');
            if (data.error) {
                alert(data.error);
                closeAIModal();
                return;
            }
            
            document.getElementById('aiSummaryText').textContent = data.summary;
            const tagsContainer = document.getElementById('aiTagsContainer');
            tagsContainer.innerHTML = '';
            
            data.tags.forEach(tag => {
                const span = document.createElement('span');
                span.className = 'ai-tag';
                span.textContent = tag;
                tagsContainer.appendChild(span);
            });
            
            content.classList.remove('hidden');
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Failed to analyze file.');
            closeAIModal();
        });
}

function closeAIModal() {
    document.getElementById('aiModal').classList.remove('active');
}

// Add to context menu handle
function handleAISummarize() {
    if (state.selectedItem && state.selectedItem.type === 'file') {
        openAIModal(state.selectedItem.id);
    }
}
