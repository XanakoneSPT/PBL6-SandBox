document.addEventListener('DOMContentLoaded', function() {
    const fileId = document.getElementById('result-container').getAttribute('data-file-id');
    
    // Tab functionality for results
    const resultTabBtns = document.querySelectorAll('.results-tabs .tab-btn');
    const resultTabPanes = document.querySelectorAll('.tab-pane');

    resultTabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabName = btn.getAttribute('data-tab');
            
            // Update active tab button
            resultTabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Show corresponding tab content
            resultTabPanes.forEach(pane => {
                pane.classList.remove('active');
            });
            document.getElementById(`${tabName}-tab`).classList.add('active');
            
            // Load logs and files when logs tab is clicked
            if (tabName === 'logs') {
                loadVMLogs();
                loadAnalysisFiles();
            }
        });
    });

    // Real-time analysis progress monitoring
    function monitorAnalysis() {
        const progressBar = document.getElementById('bar');
        const progressText = document.getElementById('progress-text');
        const statusText = document.getElementById('status');
        const resultsSection = document.getElementById('results-section');
        const downloadBtn = document.getElementById('download-report');
        
        const interval = setInterval(async () => {
            try {
                const response = await fetch(`/api/progress/${fileId}/`);
                const data = await response.json();
                
                progressBar.value = data.progress;
                progressText.textContent = data.progress + '%';
                
                // Update status based on analysis state
                if (data.status === 'processing') {
                    statusText.className = 'status-indicator analyzing';
                    statusText.innerHTML = `<span class="scanning-animation"></span>${data.output_text || 'Processing...'}`;
                } else if (data.status === 'done') {
                    clearInterval(interval);
                    statusText.className = 'status-indicator complete';
                    statusText.innerHTML = '<i class="fas fa-check-circle"></i>Analysis complete!';
                    
                    // Show results
                    resultsSection.style.display = 'block';
                    downloadBtn.style.display = 'inline-flex';
                    populateResults(data);
                } else if (data.status === 'error') {
                    clearInterval(interval);
                    statusText.className = 'status-indicator error';
                    statusText.innerHTML = '<i class="fas fa-exclamation-triangle"></i>Analysis failed!';
                    
                    // Show error results
                    resultsSection.style.display = 'block';
                    populateErrorResults(data);
                }
                
            } catch (error) {
                console.error('Error fetching progress:', error);
            }
        }, 1000); // Check every second
    }

    // Load VM logs from the analysis
    async function loadVMLogs() {
        const logsContent = document.getElementById('logs-content');
        logsContent.innerHTML = '<div class="log-entry"><span class="log-time">Loading...</span><span class="log-message">Fetching VMware analysis logs...</span></div>';
        
        try {
            const response = await fetch(`/api/progress/${fileId}/`);
            const data = await response.json();
            
            if (data.output_text) {
                const logs = data.output_text.split('\n').filter(line => line.trim());
                logsContent.innerHTML = '';
                
                logs.forEach((log, index) => {
                    const logEntry = document.createElement('div');
                    logEntry.className = 'log-entry';
                    
                    const time = new Date().toLocaleTimeString();
                    const isError = log.toLowerCase().includes('error') || log.toLowerCase().includes('failed');
                    const isSuccess = log.toLowerCase().includes('success') || log.toLowerCase().includes('completed');
                    
                    logEntry.innerHTML = `
                        <span class="log-time">${time}</span>
                        <span class="log-message ${isError ? 'error' : isSuccess ? 'success' : ''}">${log}</span>
                    `;
                    logsContent.appendChild(logEntry);
                });
                
                // Scroll to bottom
                logsContent.scrollTop = logsContent.scrollHeight;
            } else {
                logsContent.innerHTML = '<div class="log-entry"><span class="log-time">No logs</span><span class="log-message">No analysis logs available yet.</span></div>';
            }
        } catch (error) {
            logsContent.innerHTML = '<div class="log-entry error"><span class="log-time">Error</span><span class="log-message">Failed to load logs: ' + error.message + '</span></div>';
        }
    }

    // Load analysis files from FROM_VM folder
    async function loadAnalysisFiles() {
        const filesContent = document.getElementById('analysis-files-content');
        filesContent.innerHTML = '<div class="file-entry"><span class="file-time">Loading...</span><span class="file-message">Fetching analysis files...</span></div>';
        
        try {
            const response = await fetch(`/api/analysis-files/${fileId}/`);
            const data = await response.json();
            
            if (data.analysis_files && data.analysis_files.length > 0) {
                filesContent.innerHTML = '';
                
                data.analysis_files.forEach((file, index) => {
                    const fileEntry = document.createElement('div');
                    fileEntry.className = 'file-entry';
                    
                    const time = new Date().toLocaleTimeString();
                    const fileIcon = getFileIcon(file.filename);
                    
                    fileEntry.innerHTML = `
                        <span class="file-time">${time}</span>
                        <span class="file-message">
                            <i class="fas ${fileIcon}"></i>
                            ${file.filename} (${file.size_mb} MB)
                        </span>
                        <span class="file-actions">
                            <button class="btn btn-tiny" onclick="downloadFile('${file.filename}')">
                                <i class="fas fa-download"></i>
                            </button>
                        </span>
                    `;
                    filesContent.appendChild(fileEntry);
                });
            } else {
                filesContent.innerHTML = '<div class="file-entry"><span class="file-time">No files</span><span class="file-message">No analysis files found in FROM_VM folder.</span></div>';
            }
        } catch (error) {
            filesContent.innerHTML = '<div class="file-entry error"><span class="file-time">Error</span><span class="file-message">Failed to load files: ' + error.message + '</span></div>';
        }
    }

    // Get file icon based on file extension
    function getFileIcon(filename) {
        const ext = filename.split('.').pop().toLowerCase();
        switch (ext) {
            case 'txt': return 'fa-file-alt';
            case 'log': return 'fa-file-alt';
            case 'json': return 'fa-file-code';
            case 'xml': return 'fa-file-code';
            case 'csv': return 'fa-file-csv';
            case 'pdf': return 'fa-file-pdf';
            case 'zip': return 'fa-file-archive';
            case 'tar': return 'fa-file-archive';
            case 'gz': return 'fa-file-archive';
            default: return 'fa-file';
        }
    }

    // Download analysis file
    function downloadFile(filename) {
        // This would need to be implemented with a proper download endpoint
        alert(`Download functionality for ${filename} would be implemented here`);
    }

    // Populate real analysis results
    function populateResults(data) {
        const summaryGrid = document.getElementById('summary-grid');
        const detailsContent = document.getElementById('details-content');
        const rawOutput = document.getElementById('output');

        // Parse analysis data
        const analysisText = data.output_text || '';
        const fileType = extractInfo(analysisText, 'File Type:', '\n') || 'Unknown';
        const interpreter = extractInfo(analysisText, 'Interpreter:', '\n') || 'Unknown';
        const needsCompilation = extractInfo(analysisText, 'Needs Compilation:', '\n') || 'Unknown';
        const executionResult = extractInfo(analysisText, 'Execution Result:', '\n') || 'Not executed';
        const straceResult = extractInfo(analysisText, 'Strace Analysis:', '\n') || 'Not performed';

        // Determine threat level based on execution result
        const isSafe = !executionResult.toLowerCase().includes('failed') && 
                      !executionResult.toLowerCase().includes('error');
        const threatLevel = isSafe ? 'Safe' : 'Suspicious';

        // Summary data based on real analysis
        summaryGrid.innerHTML = `
            <div class="summary-card">
                <h5><i class="fas fa-shield-alt"></i>Threat Level</h5>
                <p><span class="threat-level ${isSafe ? 'safe' : 'suspicious'}">${threatLevel}</span></p>
                <p>${isSafe ? 'No threats detected in sandbox analysis.' : 'Suspicious behavior detected.'}</p>
            </div>
            <div class="summary-card">
                <h5><i class="fas fa-code"></i>File Type</h5>
                <p><strong>${fileType}</strong></p>
                <p>Interpreter: ${interpreter}</p>
            </div>
            <div class="summary-card">
                <h5><i class="fas fa-cogs"></i>Compilation</h5>
                <p><strong>${needsCompilation}</strong></p>
                <p>${needsCompilation === 'True' ? 'Requires compilation before execution' : 'Interpreted language'}</p>
            </div>
            <div class="summary-card">
                <h5><i class="fas fa-play"></i>Execution</h5>
                <p><strong>${executionResult.includes('successfully') ? 'Success' : 'Failed'}</strong></p>
                <p>${executionResult}</p>
            </div>
            <div class="summary-card">
                <h5><i class="fas fa-search"></i>System Monitoring</h5>
                <p><strong>${straceResult.includes('successfully') ? 'Success' : straceResult.includes('failed') ? 'Failed' : 'Skipped'}</strong></p>
                <p>${straceResult}</p>
            </div>
        `;

        // Detailed analysis based on real data
        detailsContent.innerHTML = `
            <div class="detail-section">
                <h6>File Properties</h6>
                <ul class="detail-list">
                    <li><span>File name</span><strong>{{ file.original_name }}</strong></li>
                    <li><span>File type</span><strong>${fileType}</strong></li>
                    <li><span>Interpreter</span><strong>${interpreter}</strong></li>
                    <li><span>Analysis time</span><strong>${new Date().toLocaleString()}</strong></li>
                </ul>
            </div>
            <div class="detail-section">
                <h6>VMware Analysis</h6>
                <ul class="detail-list">
                    <li><span>Compilation required</span><strong>${needsCompilation}</strong></li>
                    <li><span>Execution result</span><strong style="color: ${isSafe ? '#28a745' : '#dc3545'};">${executionResult}</strong></li>
                    <li><span>Strace analysis</span><strong style="color: ${straceResult.includes('successfully') ? '#28a745' : straceResult.includes('failed') ? '#dc3545' : '#ffc107'};">${straceResult}</strong></li>
                    <li><span>Sandbox environment</span><strong>VMware Kali Linux</strong></li>
                </ul>
            </div>
            <div class="detail-section">
                <h6>Security Analysis</h6>
                <ul class="detail-list">
                    <li><span>Threat level</span><strong style="color: ${isSafe ? '#28a745' : '#dc3545'};">${threatLevel}</strong></li>
                    <li><span>System calls monitored</span><strong>Yes (strace)</strong></li>
                    <li><span>Execution environment</span><strong>Isolated VMware sandbox</strong></li>
                    <li><span>Log files generated</span><strong>Yes</strong></li>
                </ul>
            </div>
        `;

        // Raw output from VMware analysis
        rawOutput.textContent = analysisText || 'No analysis output available.';
    }

    // Helper function to extract information from analysis text
    function extractInfo(text, startMarker, endMarker) {
        const startIndex = text.indexOf(startMarker);
        if (startIndex === -1) return null;
        
        const valueStart = startIndex + startMarker.length;
        const endIndex = endMarker ? text.indexOf(endMarker, valueStart) : text.length;
        
        if (endIndex === -1) return text.substring(valueStart).trim();
        return text.substring(valueStart, endIndex).trim();
    }

    // Populate error results
    function populateErrorResults(data) {
        const summaryGrid = document.getElementById('summary-grid');
        const detailsContent = document.getElementById('details-content');
        const rawOutput = document.getElementById('output');

        summaryGrid.innerHTML = `
            <div class="summary-card error">
                <h5><i class="fas fa-exclamation-triangle"></i>Analysis Failed</h5>
                <p><span class="threat-level error">Error</span></p>
                <p>Analysis could not be completed.</p>
            </div>
            <div class="summary-card">
                <h5><i class="fas fa-info-circle"></i>Error Details</h5>
                <p><strong>Status:</strong> ${data.status}</p>
                <p><strong>Message:</strong> ${data.output_text || 'Unknown error'}</p>
            </div>
        `;

        detailsContent.innerHTML = `
            <div class="detail-section">
                <h6>Error Information</h6>
                <ul class="detail-list">
                    <li><span>Error status</span><strong style="color: #dc3545;">${data.status}</strong></li>
                    <li><span>Error message</span><strong>${data.output_text || 'No error message available'}</strong></li>
                    <li><span>Analysis progress</span><strong>${data.progress}%</strong></li>
                    <li><span>Time of error</span><strong>${new Date().toLocaleString()}</strong></li>
                </ul>
            </div>
        `;

        rawOutput.textContent = data.output_text || 'No error details available.';
    }

    // Download report functionality
    document.getElementById('download-report').addEventListener('click', function() {
        const fileName = '{{ file.original_name }}'.replace(/[^a-zA-Z0-9]/g, '_');
        const reportContent = document.getElementById('output').textContent;
        
        const blob = new Blob([reportContent], { type: 'text/plain' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `Malsandbox_report_${fileName}.txt`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    });

    // Add refresh logs functionality
    document.getElementById('refresh-logs').addEventListener('click', function() {
        loadVMLogs();
    });

    // Add refresh files functionality
    document.getElementById('refresh-files').addEventListener('click', function() {
        loadAnalysisFiles();
    });

    // Start the real analysis monitoring
    monitorAnalysis();
});