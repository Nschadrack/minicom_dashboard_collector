// static/js/upload.js
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('uploadForm');
    const fileInput = document.getElementById('csvFile');
    const errorDiv = document.querySelector('.error-message');
    const MAX_SIZE_MB = 50;


    fileInput.addEventListener('change', () => {
        validateFile(fileInput.files[0]);
    });

    function validateFile(file) {
        errorDiv.style.display = 'none';
        
        if (!file) {
            showError('Please select a file');
            return false;
        }

        if (!file.name.endsWith('.csv')) {
            showError('Only CSV files are allowed');
            return false;
        }

        if (file.size > MAX_SIZE_MB * 1024 * 1024) {
            showError(`File size exceeds ${MAX_SIZE_MB}MB`);
            return false;
        }

        return true;
    }

    function showError(message) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
    }
});