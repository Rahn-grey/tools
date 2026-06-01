/**
 * PyPrint - Frontend JavaScript
 */

(function() {
    'use strict';

    // ============================================
    // Platform Detection
    // ============================================
    function initPlatformDetection() {
        const platformInfo = document.getElementById('platform-info');
        if (!platformInfo) return;

        const platform = getPlatformName();
        platformInfo.textContent = `Running on ${platform}`;
    }

    function getPlatformName() {
        const platform = navigator.platform || '';
        if (platform.includes('Win')) return 'Windows';
        if (platform.includes('Mac')) return 'macOS';
        if (platform.includes('Linux')) return 'Linux';
        return 'Unknown OS';
    }

    // ============================================
    // File Upload
    // ============================================
    function initFileUpload() {
        const dropZone = document.getElementById('drop-zone');
        const fileInput = document.getElementById('file-input');
        const filePreview = document.getElementById('file-preview');
        const removeFileBtn = document.getElementById('remove-file');
        const printBtn = document.getElementById('print-btn');

        if (!dropZone || !fileInput) return;

        // Prevent all default drag behaviors on document
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(function(eventName) {
            document.body.addEventListener(eventName, function(e) {
                e.preventDefault();
                e.stopPropagation();
            }, false);
        });

        // Also prevent on window
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(function(eventName) {
            window.addEventListener(eventName, function(e) {
                e.preventDefault();
            }, true);
        });

        // Click to open file dialog
        dropZone.addEventListener('click', function(e) {
            if (e.target.closest('.remove-file')) return;
            fileInput.click();
        });

        // File selected via dialog
        fileInput.addEventListener('change', function() {
            if (this.files && this.files.length > 0) {
                handleFileSelect(this.files[0]);
            }
        });

        // Drag and drop events on drop zone
        dropZone.addEventListener('dragover', function(e) {
            e.preventDefault();
            e.stopPropagation();
            e.dataTransfer.dropEffect = 'copy';
            this.classList.add('dragover');
        });

        dropZone.addEventListener('dragenter', function(e) {
            e.preventDefault();
            e.stopPropagation();
            this.classList.add('dragover');
        });

        dropZone.addEventListener('dragleave', function(e) {
            e.preventDefault();
            e.stopPropagation();
            if (!this.contains(e.relatedTarget)) {
                this.classList.remove('dragover');
            }
        });

        dropZone.addEventListener('drop', function(e) {
            e.preventDefault();
            e.stopPropagation();
            this.classList.remove('dragover');

            const files = e.dataTransfer.files;
            if (files && files.length > 0) {
                handleFileSelect(files[0]);

                // Use DataTransfer to set files on input
                const dataTransfer = new DataTransfer();
                for (let i = 0; i < files.length; i++) {
                    dataTransfer.items.add(files[i]);
                }
                fileInput.files = dataTransfer.files;
            }
        });

        // Remove file button
        if (removeFileBtn) {
            removeFileBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                resetFileInput();
            });
        }

        function handleFileSelect(file) {
            const ext = file.name.split('.').pop().toLowerCase();
            const validExts = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'txt'];

            if (!validExts.includes(ext)) {
                showFeedback(false, 'File type not supported. Please use PDF, Word, Excel, or image files.');
                return;
            }

            // Show preview
            showFilePreview(file);

            // Enable print button
            if (printBtn) {
                printBtn.disabled = false;
            }
        }

        function showFilePreview(file) {
            const dropZoneContent = document.querySelector('.drop-zone-content');
            const filePreviewEl = document.getElementById('file-preview');
            const fileName = filePreviewEl.querySelector('.file-name');
            const fileSize = filePreviewEl.querySelector('.file-size');

            if (dropZoneContent) dropZoneContent.hidden = true;
            if (filePreviewEl) {
                filePreviewEl.hidden = false;
                if (fileName) fileName.textContent = file.name;
                if (fileSize) fileSize.textContent = formatFileSize(file.size);
            }
        }

        window.resetFileInput = function() {
            fileInput.value = '';
            const dropZoneContent = document.querySelector('.drop-zone-content');
            const filePreviewEl = document.getElementById('file-preview');

            if (dropZoneContent) dropZoneContent.hidden = false;
            if (filePreviewEl) filePreviewEl.hidden = true;
            if (printBtn) printBtn.disabled = true;
        };
    }

    function formatFileSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    }

    // ============================================
    // Copies Control
    // ============================================
    function initCopiesControl() {
        const copiesInput = document.getElementById('copies-input');
        const minusBtn = document.getElementById('copies-minus');
        const plusBtn = document.getElementById('copies-plus');

        if (!copiesInput) return;

        if (minusBtn) {
            minusBtn.addEventListener('click', function() {
                const val = parseInt(copiesInput.value) || 1;
                if (val > 1) copiesInput.value = val - 1;
            });
        }

        if (plusBtn) {
            plusBtn.addEventListener('click', function() {
                const val = parseInt(copiesInput.value) || 1;
                if (val < 99) copiesInput.value = val + 1;
            });
        }
    }

    // ============================================
    // Print Form
    // ============================================
    function initPrintForm() {
        const form = document.getElementById('print-form');
        const printBtn = document.getElementById('print-btn');
        const feedbackEl = document.getElementById('print-feedback');
        const feedbackMessage = document.getElementById('feedback-message');
        const feedbackDismiss = document.getElementById('feedback-dismiss');
        const feedbackIcon = document.getElementById('feedback-icon');

        const previewModal = document.getElementById('print-preview-modal');
        const modalClose = document.getElementById('modal-close');
        const modalOverlay = document.getElementById('modal-overlay');
        const printCancel = document.getElementById('print-cancel');
        const printConfirm = document.getElementById('print-confirm');

        if (!form) return;

        // Load printers
        loadPrinters();

        // Print button - show preview modal
        printBtn.addEventListener('click', function() {
            const fileInput = document.getElementById('file-input');
            const printerSelect = document.getElementById('printer-select');
            const copiesInput = document.getElementById('copies-input');
            const pageRangeInput = document.getElementById('page-range');
            const printMethodSelect = document.getElementById('print-method');

            if (!fileInput.files || fileInput.files.length === 0) {
                showFeedback(false, 'Please select a file to print.');
                return;
            }

            if (!printerSelect.value) {
                showFeedback(false, 'Please select a printer.');
                return;
            }

            // Update preview values
            document.getElementById('preview-file').textContent = fileInput.files[0].name;
            document.getElementById('preview-printer').textContent = printerSelect.value;
            document.getElementById('preview-copies').textContent = copiesInput.value || 1;

            const pageRange = pageRangeInput.value.trim();
            document.getElementById('preview-page-range').textContent = pageRange || 'All';
            document.getElementById('preview-page-range-item').style.display = pageRange ? 'flex' : 'none';

            const methodText = printMethodSelect ? printMethodSelect.options[printMethodSelect.selectedIndex].text : 'Auto';
            document.getElementById('preview-method').textContent = methodText;

            const orientationInputs = document.querySelectorAll('input[name="orientation"]');
            let orientationText = 'Auto';
            orientationInputs.forEach(function(input) {
                if (input.checked) {
                    orientationText = input.nextElementSibling.textContent;
                }
            });
            document.getElementById('preview-orientation').textContent = orientationText;

            // Show modal
            if (previewModal) previewModal.hidden = false;
        });

        // Close modal handlers
        function closeModal() {
            if (previewModal) previewModal.hidden = true;
        }

        if (modalClose) modalClose.addEventListener('click', closeModal);
        if (modalOverlay) modalOverlay.addEventListener('click', closeModal);
        if (printCancel) printCancel.addEventListener('click', closeModal);

        // Confirm print - submit to server
        if (printConfirm) {
            printConfirm.addEventListener('click', async function() {
                closeModal();

                const fileInput = document.getElementById('file-input');
                const printerSelect = document.getElementById('printer-select');
                const copiesInput = document.getElementById('copies-input');
                const pageRangeInput = document.getElementById('page-range');
                const printMethodSelect = document.getElementById('print-method');

                // Disable button during submission
                printBtn.disabled = true;
                printBtn.querySelector('span').textContent = 'Sending...';

                const formData = new FormData();
                formData.append('file', fileInput.files[0]);
                formData.append('printer', printerSelect.value);
                formData.append('copies', copiesInput.value || 1);

                // Page range (optional)
                if (pageRangeInput && pageRangeInput.value.trim()) {
                    formData.append('page_range', pageRangeInput.value.trim());
                }

                // Print method
                if (printMethodSelect) {
                    formData.append('print_method', printMethodSelect.value);
                }

                // Orientation
                const orientationInputs = document.querySelectorAll('input[name="orientation"]');
                orientationInputs.forEach(function(input) {
                    if (input.checked) {
                        formData.append('orientation', input.value);
                    }
                });

                try {
                    const response = await fetch('/api/print', {
                        method: 'POST',
                        body: formData
                    });

                    const result = await response.json();

                    if (result.success) {
                        showFeedback(true, result.message || 'Print job sent successfully!');
                    } else {
                        showFeedback(false, result.error || 'Print failed. Please try again.');
                    }
                } catch (error) {
                    showFeedback(false, 'Network error. Please check your connection.');
                }

                printBtn.disabled = false;
                printBtn.querySelector('span').textContent = 'Print Now';
            });
        }

        // Dismiss feedback
        if (feedbackDismiss) {
            feedbackDismiss.addEventListener('click', function() {
                hideFeedback();
                resetFileInput();
            });
        }

        function showFeedback(success, message) {
            if (feedbackEl) feedbackEl.hidden = false;
            if (feedbackMessage) feedbackMessage.textContent = message;

            const iconSuccess = feedbackIcon ? feedbackIcon.querySelector('.icon-success') : null;
            const iconError = feedbackIcon ? feedbackIcon.querySelector('.icon-error') : null;

            if (success && iconSuccess) {
                iconSuccess.hidden = false;
                if (iconError) iconError.hidden = true;
            } else if (!success && iconError) {
                iconError.hidden = false;
                if (iconSuccess) iconSuccess.hidden = true;
            }
        }

        function hideFeedback() {
            if (feedbackEl) feedbackEl.hidden = true;
        }
    }

    async function loadPrinters() {
        const printerSelect = document.getElementById('printer-select');
        if (!printerSelect) return;

        try {
            const response = await fetch('/api/printers');
            const data = await response.json();

            // Clear existing options except placeholder
            const placeholder = printerSelect.querySelector('option[value=""]');
            printerSelect.innerHTML = '';
            if (placeholder) printerSelect.appendChild(placeholder);

            if (data.printers && data.printers.length > 0) {
                data.printers.forEach(function(printer) {
                    const option = document.createElement('option');
                    option.value = printer.name;
                    option.textContent = printer.name + (printer.is_default ? ' (Default)' : '');
                    if (printer.is_default) {
                        option.selected = true;
                    }
                    printerSelect.appendChild(option);
                });
            } else {
                const option = document.createElement('option');
                option.value = '';
                option.textContent = 'No printers found';
                option.disabled = true;
                printerSelect.appendChild(option);
            }
        } catch (error) {
            console.error('Failed to load printers:', error);
            const option = document.createElement('option');
            option.value = '';
            option.textContent = 'Failed to load printers';
            option.disabled = true;
            printerSelect.appendChild(option);
        }
    }

    // ============================================
    // Global exports for HTML onclick handlers
    // ============================================
    window.PyPrint = {
        resetFileInput: resetFileInput
    };

})();