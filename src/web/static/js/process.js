// Process status update functionality
document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const processingForm = document.querySelector('#processing-form');
    const processingInfo = document.querySelector('#processing-info');
    const processingStatus = document.querySelector('#processing-status');
    const progressBar = document.querySelector('#progress-bar');
    const stepColorEdit = document.querySelector('#step-color-edit');
    const stepTranscription = document.querySelector('#step-transcription');
    const stepChapters = document.querySelector('#step-chapters');
    
    // Get session ID from URL if available
    const urlParams = new URLSearchParams(window.location.search);
    const sessionId = urlParams.get('session_id');
    
    // If on processing page and form submitted, show progress and start polling
    if (processingForm && processingStatus) {
        processingForm.addEventListener('submit', function(e) {
            // Already handled by the backend, we just need to show the status UI
            processingInfo.classList.add('d-none');
            processingStatus.classList.remove('d-none');
            
            // Start checking status if we have a session ID
            if (sessionId) {
                pollProcessingStatus();
            }
        });
    }
    
    // Function to poll the processing status API
    function pollProcessingStatus() {
        if (!sessionId) return;
        
        fetch(`/api/status/${sessionId}`)
            .then(response => response.json())
            .then(status => {
                updateProgressUI(status);
                
                // If not all steps are complete, poll again in 5 seconds
                const isComplete = status.color_edit && status.transcription && status.chapters && status.titles_extracted;
                if (!isComplete) {
                    setTimeout(pollProcessingStatus, 5000);
                }
            })
            .catch(error => console.error('Error polling status:', error));
    }
    
    // Update the UI based on processing status
    function updateProgressUI(status) {
        // Calculate progress percentage
        let progress = 0;
        if (status.color_edit) progress += 33;
        if (status.transcription) progress += 33;
        if (status.chapters) progress += 34;
        
        // Update progress bar
        if (progressBar) {
            progressBar.style.width = `${progress}%`;
        }
        
        // Update step indicators
        if (stepColorEdit) {
            if (status.color_edit) {
                stepColorEdit.classList.remove('active');
                stepColorEdit.classList.add('done');
                stepColorEdit.querySelector('.status-icon').textContent = '✅';
            } else {
                stepColorEdit.classList.add('active');
                stepColorEdit.querySelector('.status-icon').textContent = '🔄';
            }
        }
        
        if (stepTranscription) {
            if (status.transcription) {
                stepTranscription.classList.remove('active');
                stepTranscription.classList.add('done');
                stepTranscription.querySelector('.status-icon').textContent = '✅';
            } else if (status.color_edit) {
                stepTranscription.classList.add('active');
                stepTranscription.querySelector('.status-icon').textContent = '🔄';
            }
        }
        
        if (stepChapters) {
            if (status.chapters) {
                stepChapters.classList.remove('active');
                stepChapters.classList.add('done');
                stepChapters.querySelector('.status-icon').textContent = '✅';
            } else if (status.transcription) {
                stepChapters.classList.add('active');
                stepChapters.querySelector('.status-icon').textContent = '🔄';
            }
        }
        
        // If all steps are complete, redirect to the next page
        if (status.titles_extracted) {
            window.location.href = '/select_title';
        }
    }
    
    // If we're on the processing page and have a session ID, start polling
    if (processingStatus && processingStatus.classList.contains('d-none') === false && sessionId) {
        pollProcessingStatus();
    }
});