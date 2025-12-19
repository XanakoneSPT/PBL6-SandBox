document.addEventListener('DOMContentLoaded', function(){
    const fileInput = document.getElementById('file');
    const chooseBtn = document.getElementById('choose-file-btn');
    const uploadForm = document.getElementById('upload-form');
    const uploadContainer = document.getElementById('upload-container');
    const uploadIcon = document.getElementById('upload-icon');

    // 
    chooseBtn.addEventListener('click', function(e){
        e.preventDefault();
        fileInput.click();
    });

    fileInput.addEventListener('change', function(e){
        const file = e.target.files[0];

        if(!file){
            return;
        }

        // Update button to show uploading
        chooseBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Uploading...';
        chooseBtn.disabled = true;
                
        // Update icon
        uploadIcon.innerHTML = '<i class="fas fa-check-circle"></i>';
        uploadContainer.classList.add('file-selected');
                
        // Submit form automatically
        uploadForm.submit();
    });

    uploadContainer.addEventListener('dragover', function(e){
        e.preventDefault();
        uploadContainer.classList.add('dragover');
    });
    uploadContainer.addEventListener('dragleave', function(e){
        e.preventDefault();
        uploadContainer.classList.remove('dragover');
    });
    uploadContainer.addEventListener('drop', function(e){
        e.preventDefault();
        uploadContainer.classList.remove('dragover');

        const files = e.dataTransfer.files;
        if(files.length > 0){
            //set dropped file to input
            fileInput.files = files;
            //trigger change event
            fileInput.dispatchEvent(new Event('change'));
        }
    });
});