(function() {
    'use strict';
    
    // Wait for DOM to be ready
    function ready(fn) {
        if (document.readyState !== 'loading') {
            fn();
        } else {
            document.addEventListener('DOMContentLoaded', fn);
        }
    }
    
    function initializeUpload() {
        console.log('Initializing upload functionality...');
        
        // Check if we're on the upload page
        const uploadForm = document.getElementById('upload-form');
        if (!uploadForm) {
            console.log('Not on upload page, skipping upload.js initialization');
            return;
        }

        const fileInput = document.getElementById('file');
        const chooseFileBtn = document.getElementById('choose-file-btn');
        const uploadContainer = document.getElementById('upload-container');
        const uploadIcon = document.getElementById('upload-icon');

        // Debug: Check if elements exist
        console.log('Upload form:', uploadForm);
        console.log('File input:', fileInput);
        console.log('Choose file btn:', chooseFileBtn);
        console.log('Upload container:', uploadContainer);

        // Check if all required elements exist
        if (!fileInput || !chooseFileBtn || !uploadContainer || !uploadIcon) {
            console.error('Required DOM elements not found:', {
                fileInput: !!fileInput,
                chooseFileBtn: !!chooseFileBtn,
                uploadContainer: !!uploadContainer,
                uploadIcon: !!uploadIcon
            });
            return;
        }

        // Ensure file input is accessible
        fileInput.style.position = 'absolute';
        fileInput.style.left = '-9999px';
        fileInput.style.opacity = '0';
        fileInput.style.pointerEvents = 'none';

        // File upload functionality
        chooseFileBtn.addEventListener('click', (e) => {
            console.log('Choose file button clicked');
            e.preventDefault();
            e.stopPropagation();
            
            // Try multiple methods to trigger file input
            try {
                console.log('About to trigger file input click');
                fileInput.click();
                console.log('File input click triggered');
            } catch (error) {
                console.error('Error triggering file input:', error);
                // Fallback: create a new file input
                const newInput = document.createElement('input');
                newInput.type = 'file';
                newInput.name = 'file';
                newInput.style.display = 'none';
                document.body.appendChild(newInput);
                newInput.click();
                newInput.addEventListener('change', (event) => {
                    if (event.target.files.length > 0) {
                        fileInput.files = event.target.files;
                        fileInput.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                    document.body.removeChild(newInput);
                });
            }
        });

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                const file = e.target.files[0];
                const fileName = file.name;
                const fileSize = (file.size / 1024 / 1024).toFixed(2);
                
                // Check file size (limit to 100MB)
                if (file.size > 100 * 1024 * 1024) {
                    alert('File size too large. Please select a file smaller than 100MB.');
                    return;
                }
                
                chooseFileBtn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Uploading...`;
                uploadContainer.classList.add('file-selected');
                uploadIcon.innerHTML = '<i class="fas fa-file-check"></i>';
                
                // Auto-submit the form
                setTimeout(() => {
                    uploadForm.submit();
                }, 500);
            }
        });

        // Drag and drop functionality
        uploadContainer.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadContainer.classList.add('dragover');
        });

        uploadContainer.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadContainer.classList.remove('dragover');
        });

        uploadContainer.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadContainer.classList.remove('dragover');
            
            if (e.dataTransfer.files.length > 0) {
                const file = e.dataTransfer.files[0];
                const fileName = file.name;
                const fileSize = (file.size / 1024 / 1024).toFixed(2);
                
                // Create a new FileList with the dropped file
                const dataTransfer = new DataTransfer();
                dataTransfer.items.add(file);
                fileInput.files = dataTransfer.files;
                
                // Check file size (limit to 100MB)
                if (file.size > 100 * 1024 * 1024) {
                    alert('File size too large. Please select a file smaller than 100MB.');
                    return;
                }
                
                chooseFileBtn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Uploading...`;
                uploadContainer.classList.add('file-selected');
                uploadIcon.innerHTML = '<i class="fas fa-file-check"></i>';
                
                // Auto-submit the form
                setTimeout(() => {
                    uploadForm.submit();
                }, 500);
            }
        });

        // Click on container to choose file
        uploadContainer.addEventListener('click', (e) => {
            // Only trigger if clicking on the container itself, not on the button
            if (e.target === uploadContainer && !uploadContainer.classList.contains('file-selected')) {
                fileInput.click();
            }
        });

        console.log('Upload functionality initialized successfully');
    }
    
    // Initialize when DOM is ready
    ready(function() {
        // Add a small delay to ensure all other scripts are loaded
        setTimeout(initializeUpload, 100);
    });
    
})();