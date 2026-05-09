function handlePreview(id, type) {
    const fileId = id || state.selectedItem.id;
    const fileName = fileId.split('/').pop();
    
    document.getElementById('previewFileName').innerText = fileName;
    openPreviewModal();
    
    const spinner = document.getElementById('previewSpinner');
    const img = document.getElementById('previewImage');
    const video = document.getElementById('previewVideo');
    const pdf = document.getElementById('previewPdf');
    const code = document.getElementById('previewCode');
    const codeContent = document.getElementById('codeContent');
    const fallback = document.getElementById('previewFallback');
    
    // Reset
    [img, video, pdf, code, fallback].forEach(el => el.classList.add('hidden'));
    spinner.classList.remove('hidden');
    
    const ext = fileName.split('.').pop().toLowerCase();
    const previewUrl = ownerId ? `/shared/preview/${ownerId}/${fileId}` : `/preview/${fileId}`;
    
    document.getElementById('downloadPreview').onclick = () => {
        window.location.href = ownerId ? `/shared/download/${ownerId}/${fileId}` : `/download/${fileId}`;
    };

    const codeExtensions = {
        'py': 'python',
        'js': 'javascript',
        'css': 'css',
        'html': 'html',
        'json': 'json',
        'md': 'markdown',
        'txt': 'clike'
    };

    if (['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext)) {
        img.src = previewUrl;
        img.onload = () => {
            spinner.classList.add('hidden');
            img.classList.remove('hidden');
        };
    } else if (['mp4', 'webm', 'ogg'].includes(ext)) {
        video.src = previewUrl;
        video.onloadeddata = () => {
            spinner.classList.add('hidden');
            video.classList.remove('hidden');
        };
    } else if (ext === 'pdf') {
        pdf.src = previewUrl;
        pdf.onload = () => {
            spinner.classList.add('hidden');
            pdf.classList.remove('hidden');
        };
    } else if (codeExtensions[ext]) {
        fetch(previewUrl)
            .then(res => res.text())
            .then(text => {
                codeContent.innerText = text;
                codeContent.className = `language-${codeExtensions[ext]}`;
                spinner.classList.add('hidden');
                code.classList.remove('hidden');
                Prism.highlightElement(codeContent);
            })
            .catch(() => {
                spinner.classList.add('hidden');
                fallback.classList.remove('hidden');
            });
    } else {
        spinner.classList.add('hidden');
        fallback.classList.remove('hidden');
    }
}

// Add event listeners to file cards
document.addEventListener('DOMContentLoaded', () => {
    // We use delegation for dynamically added or shared cards
    document.addEventListener('click', (e) => {
        const card = e.target.closest('.card');
        if (!card) return;

        if (e.detail === 2) { // Double click
            if (card.dataset.type === 'file') {
                handlePreview(card.dataset.id, 'file', card.dataset.ownerId);
            } else if (card.dataset.type === 'folder') {
                if (card.dataset.ownerId) {
                    navigateToSharedFolder(card.dataset.ownerId, card.dataset.id);
                } else {
                    navigateToFolder(card.dataset.id);
                }
            }
        } else {
            selectItem(card);
        }
    });
});

function selectItem(element) {
    document.querySelectorAll('.card').forEach(c => c.classList.remove('selected'));
    element.classList.add('selected');
    state.selectedItem = {
        id: element.dataset.id,
        type: element.dataset.type
    };
}
