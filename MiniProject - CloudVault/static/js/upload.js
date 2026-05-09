let filesToUpload = [];

function initUpload() {
    const fileInput = document.getElementById('fileInput');
    const dropZone = document.getElementById('dropZone');

    if (fileInput) {
        fileInput.addEventListener('change', (e) => {
            handleFiles(e.target.files);
        });
    }

    const folderInput = document.getElementById('folderInput');
    if (folderInput) {
        folderInput.addEventListener('change', (e) => {
            handleFiles(e.target.files);
            openUploadModal(); // Open modal if triggered from sidebar
        });
    }

    if (dropZone) {
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('active');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('active');
        });

        dropZone.addEventListener('drop', async (e) => {
            e.preventDefault();
            dropZone.classList.remove('active');
            
            const items = e.dataTransfer.items;
            if (items) {
                const files = [];
                for (let i = 0; i < items.length; i++) {
                    const item = items[i].webkitGetAsEntry();
                    if (item) {
                        await scanFiles(item, '', files);
                    }
                }
                handleFiles(files);
            } else {
                handleFiles(e.dataTransfer.files);
            }
        });
    }
}

async function scanFiles(item, path, fileList) {
    if (item.isFile) {
        const file = await new Promise((resolve) => item.file(resolve));
        // Manually set relativePath because browser doesn't for drops
        Object.defineProperty(file, 'webkitRelativePath', {
            value: path ? path + file.name : file.name
        });
        fileList.push(file);
    } else if (item.isDirectory) {
        const dirReader = item.createReader();
        const entries = await new Promise((resolve) => dirReader.readEntries(resolve));
        for (let i = 0; i < entries.length; i++) {
            await scanFiles(entries[i], path + item.name + '/', fileList);
        }
    }
}

function handleFiles(files) {
    filesToUpload = [...files];
    const uploadList = document.getElementById('uploadList');
    uploadList.innerHTML = '';

    filesToUpload.forEach((file, index) => {
        const item = document.createElement('div');
        item.className = 'upload-item';
        item.style.display = 'flex';
        item.style.alignItems = 'center';
        item.style.gap = '12px';
        item.style.padding = '8px 0';
        item.style.borderBottom = '1px solid var(--border-color)';
        
        item.innerHTML = `
            <i class="fas fa-file"></i>
            <span style="flex: 1; font-size: 14px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${file.name}</span>
            <div class="progress-container" style="width: 100px; height: 4px; background: var(--border-color); border-radius: 2px; overflow: hidden;">
                <div id="progress-${index}" class="progress-bar" style="width: 0%; height: 100%; background: var(--primary-color); transition: width 0.3s;"></div>
            </div>
            <i class="fas fa-times" onclick="removeFile(${index})" style="cursor: pointer; color: var(--text-secondary);"></i>
        `;
        uploadList.appendChild(item);
    });
}

function removeFile(index) {
    filesToUpload.splice(index, 1);
    handleFiles(filesToUpload);
}

async function startUpload() {
    if (filesToUpload.length === 0) return;

    const startBtn = document.getElementById('startUploadBtn');
    startBtn.disabled = true;
    startBtn.innerText = 'Uploading...';

    const path = state.currentPath;

    for (let i = 0; i < filesToUpload.length; i++) {
        const file = filesToUpload[i];
        const formData = new FormData();
        formData.append('file', file);
        formData.append('path', path);
        
        // Add relative path for folder uploads
        if (file.webkitRelativePath) {
            formData.append('relative_path', file.webkitRelativePath);
        }

        try {
            await uploadFileWithProgress(formData, i);
        } catch (error) {
            console.error('Upload failed:', error);
            showToast(`Failed to upload ${file.name}`, 'error');
        }
    }

    showToast('Upload complete!', 'success');
    setTimeout(() => {
        location.reload();
    }, 1000);
}

function uploadFileWithProgress(formData, index) {
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/upload', true);

        xhr.upload.onprogress = (e) => {
            if (e.lengthComputable) {
                const percentComplete = (e.loaded / e.total) * 100;
                document.getElementById(`progress-${index}`).style.width = percentComplete + '%';
            }
        };

        xhr.onload = () => {
            if (xhr.status >= 200 && xhr.status < 300) {
                resolve(xhr.response);
            } else {
                reject(new Error(xhr.statusText));
            }
        };

        xhr.onerror = () => reject(new Error('Network Error'));
        xhr.send(formData);
    });
}

// Initialize on load
document.addEventListener('DOMContentLoaded', initUpload);
