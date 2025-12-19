document.addEventListener('DOMContentLoaded', function(){

    const fileId = document.getElementById('result-container').getAttribute('data-file-id');

    let intervalId;

    async function monitorAnalysis() {
        const progressBar = document.getElementById('bar');
        const progressText = document.getElementById('progress-text');
        const statusText = document.getElementById('status');

        try{
            const response = await fetch(`/api/progress/${fileId}/`);
            const data = await response.json();

            progressBar.value = data.progress;
            progressText.textContent = data.progress + '%';
            statusText.textContent = data.status;

            if (data.status === 'done'){
                clearInterval(intervalId);

                document.getElementById('results-section').style.display = 'block';
                setupTabs();
                populateSummaries(data);
                populateDetails(data);
                // populateVMLogs(data);

                const uploadBtn = document.querySelector('.action-buttons a[href*="home"]');
                const downloadBtn = document.getElementById('download-report');

                if (uploadBtn) uploadBtn.style.display = 'inline-flex';
                if (downloadBtn) downloadBtn.style.display = 'inline-flex';
            }
        } catch(error){
            console.error('Error: ', error);
        }
    }
    intervalId = setInterval(monitorAnalysis, 1000);
    monitorAnalysis();

    // Tabs
    function setupTabs(){
        const tabButtons = document.querySelectorAll('.tab-btn');
        const tabPanes = document.querySelectorAll('.tab-pane');

        tabButtons.forEach(btn => {
            btn.addEventListener('click', ()=>{
                const tabName = btn.getAttribute('data-tab');

                // remove active class from all buttons
                tabButtons.forEach(b => b.classList.remove('active'));
                // add active class to clicked btn
                btn.classList.add('active');

                // remove active class from all panes
                tabPanes.forEach(pane => pane.classList.remove('active'));
                // add active class to clicked pane
                document.getElementById(`${tabName}-tab`).classList.add('active');

                if (tabName === 'logs') {
                    populateVMLogs();
                }
            });
        });
    }
    setupTabs();

    // Summary
    function populateSummaries(data){
        const summaryGrid = document.getElementById('summary-grid');
        summaryGrid.innerHTML = '';

        let html = '';

        // File Type
        const file_type = data.file_info?.file_type || 'Unknown';
        const file_interpreter = data.file_info?.interpreter || 'Unknown';

        html += `
            <div class="summary-card">
                <h5><i class="fas fa-file"></i> File Type</h5>
                <p><strong>${file_type}</strong></p>
                <p><strong>${file_interpreter}</strong></p>
            </div>
        `;

        // YARA
        const yaraMatches = data.yara_raw_matches?.length || 0;
        const yaraStatus = data.yara_error ? 'Error' : (yaraMatches > 0 ? 'Threats Detected' : 'Clean');
        const yaraClass = data.yara_error ? 'error' : (yaraMatches > 0 ? 'malicious' : 'safe');
        
        html += `
            <div class="summary-card">
                <h5><i class="fas fa-shield-alt"></i> Pattern Detection</h5>
                <p><strong class="${yaraClass}">${yaraStatus}</strong></p>
                <p>${data.yara_error ? sanitizeError(data.yara_error) : `${yaraMatches} matches`}</p>
            </div>
        `;

        // Bazaar
        let bazaarStatus = 'Not Scanned';
        let bazaarClass = 'safe';
        let bazaarDetails = 'Database check not performed';

        if (data.bazaar_error){
            bazaarStatus = 'Error';
            bazaarClass = 'error';
            bazaarDetails = sanitizeError(data.bazaar_error);
        } else if (data.bazaar_success){
            if (data.bazaar_is_malicious){
                bazaarStatus = 'Malicious';
                bazaarClass = 'malicious';
                bazaarDetails = 'Match malware in the database';
            } else{
                bazaarStatus = 'Clean';
                bazaarClass = 'safe';
                bazaarDetails = 'Not match in malware database';
            }
        }

        html += `
            <div class="summary-card">
                <h5><i class="fas fa-database"></i> Malware Database</h5>
                <p><strong class="${bazaarClass}">${bazaarStatus}</strong></p>
                <p>${bazaarDetails}</p>
            </div>
        `;

        // LSTM
        let lstmStatus = 'Not Scanned';
        let lstmClass = 'safe';
        let lstmDetails = 'Behavioral analysis not performed';

        if (data.lstm_error) {
            lstmStatus = 'Error';
            lstmClass = 'error';
            lstmDetails = sanitizeError(data.lstm_error);
        } else if (data.lstm_final_decision) {
            if (data.lstm_final_decision === 'anomalous') {
                lstmStatus = 'Anomalous';
                lstmClass = 'malicious';
                lstmDetails = `Anomaly detected`;
            } else if (data.lstm_final_decision === 'normal') {
                lstmStatus = 'Normal';
                lstmClass = 'safe';
                lstmDetails = 'No anomalies detected';
            } else {
                lstmStatus = data.lstm_final_decision;
                lstmClass = 'safe';
                lstmDetails = 'Analysis completed';
            }
        }

        html += `
            <div class="summary-card">
                <h5><i class="fas fa-brain"></i>Behavioral Analysis</h5>
                <p><strong class="${lstmClass}">${lstmStatus}</strong></p>
                <p>${lstmDetails}</p>
            </div>
        `;

        summaryGrid.innerHTML = html;
    }

    // Detail Tab
    function populateDetails(data) {
        const detailsContent = document.getElementById('details-content');

        const fileName = document.querySelector('.card header p').textContent.replace('File: ', '');

        let html = '';

        // File Properties Section
        html += `
            <div class="detail-section">
                <h6>File Properties</h6>
                <ul class="detail-list">
                    <li><span>File name</span><strong>${fileName}</strong></li>
                    <li><span>File type</span><strong>${data.file_info?.file_type || 'Unknown'}</strong></li>
                    <li><span>File size</span><strong>${formatFileSize(data.file_info?.file_size || 0)}</strong></li>
                </ul>
            </div>
        `;

        // File Hashes Section
        html += `
            <div class="detail-section">
                <h6>File Hashes</h6>
                <ul class="detail-list">
                    <li><span>MD5</span><strong class="hash-value">${data.file_info?.md5_hash || 'Not available'}</strong></li>
                    <li><span>SHA-1</span><strong class="hash-value">${data.file_info?.sha1_hash || 'Not available'}</strong></li>
                    <li><span>SHA-256</span><strong class="hash-value">${data.file_info?.sha256_hash || 'Not available'}</strong></li>
                </ul>
            </div>
        `;

        // LSTM section
        if (data.lstm_error){
            html += `
                <div class="detail-section">
                    <h6>Behavioral Analysis</h6>
                    <ul class="detail-list">
                        <li><span>Status</span><strong style="color: #f87171;">Error</strong></li>
                        <li><span>Error</span><strong>${sanitizeError(data.lstm_error)}</strong></li>
                    </ul>
                </div>
            `;
        } else if (!data.lstm_final_decision){
            html += `
            <div class="detail-section">
                <h6>Behavioral Analysis</h6>
                <ul class="detail-list">
                    <li><span>Status</span><strong>No log files found for analysis</strong></li>
                </ul>
            </div>
        `;
        } else {
            html += `
                <div class="detail-section">
                    <h6>Behavioral Analysis</h6>
                    <ul class="detail-list">
                        <li><span>Final Decision</span><strong>${data.lstm_final_decision}</strong></li>
                        <li><span>Max Anomaly Probability</span><strong>${(data.lstm_max_prob_anomaly * 100).toFixed(1)}%</strong></li>
                        <li><span>Mean Anomaly Probability</span><strong>${(data.lstm_mean_prob_anomaly * 100).toFixed(1)}%</strong></li>
                        <li><span>Number of Windows</span><strong>${data.lstm_num_windows || 'N/A'}</strong></li>
                    </ul>
                </div>
            `;
        }

        // Bazaar section
        if (data.bazaar_error){
            html += `
                <div class="detail-section">
                    <h6>Malware Database</h6>
                    <ul class="detail-list">
                        <li><span>Status</span><strong style="color: #f87171;">Error</strong></li>
                        <li><span>Error</span><strong>${sanitizeError(data.bazaar_error)}</strong></li>
                    </ul>
                </div>
            `;
        }else if (!data.bazaar_success){
            html += `
                <div class="detail-section">
                    <h6>Malware Database</h6>
                    <ul class="detail-list">
                        <li><span>Status</span><strong style="color: #f87171;">API Database failed</strong></li>
                    </ul>
                </div>
            `;
        } else if (data.bazaar_is_malicious && data.bazaar_malware_info){
            html += `
                <div class="detail-section">
                    <h6>Malware Database</h6>
                    <ul class="detail-list">
                        <li><span>Status</span><strong style="color: #dc3545;">Malicious</strong></li>
                        <li><span>Signature</span><strong>${data.bazaar_malware_info.signature || 'N/A'}</strong></li>
                        <li><span>File Name</span><strong>${data.bazaar_malware_info.file_name || 'N/A'}</strong></li>
                        <li><span>File Type</span><strong>${data.bazaar_malware_info.file_type || 'N/A'}</strong></li>
                        <li><span>First Seen</span><strong>${data.bazaar_malware_info.first_seen || 'N/A'}</strong></li>
                    </ul>
                </div>
            `;
        } else{
            html += `
                <div class="detail-section">
                    <h6>Malware Database</h6>
                    <ul class="detail-list">
                        <li><span>Status</span><strong style="color: #28a745;">Clean</strong></li>
                    </ul>
                </div>
            `;
        }

        // Yara section
        if (data.yara_error){
            html += `
                <div class="detail-section">
                    <h6>Patterns Detection</h6>
                    <ul class="detail-list">
                        <li><span>Status</span><strong style="color: #f87171;">Error</strong></li>
                        <li><span>Error</span><strong>${sanitizeError(data.yara_error)}</strong></li>
                    </ul>
                </div>
            `;
        } else if (!data.yara_raw_matches || data.yara_raw_matches.length === 0){
            html += `
                <div class="detail-section">
                    <h6>Patterns Detection</h6>
                    <ul class="detail-list">
                        <li><span>Status</span><strong style="color: #28a745;">Clean - No threats detected</strong></li>
                    </ul>
                </div>
            `;
        }else{
            // rules list
            let rulesHtml = '';
            data.yara_raw_matches.forEach((match, index) => {
                rulesHtml += `
                    <li class="rule-item">
                        <div class="rule-number">${index + 1}.</div>
                        <div class="rule-content">
                            <div class="rule-name">${match.rule}</div>
                            <div class="rule-description">${match.description || 'No description available'}</div>
                        </div>
                    </li>
                `;
            });
            
            html += `
                <div class="detail-section">
                    <h6>Patterns Detection</h6>
                    <ul class="detail-list">
                        <li><span>Status</span><strong style="color: #dc3545;">Threats Detected</strong></li>
                        <li><span>Total Matches</span><strong>${data.yara_raw_matches.length}</strong></li>
                    </ul>
                    <div class="matched-rules-section">
                        <span>Matched Rules:</span>
                        <ul class="rules-list">
                            ${rulesHtml}
                        </ul>
                    </div>
                </div>
            `;
        }

        detailsContent.innerHTML = html;
    }

    // VM logs tab
    async function populateVMLogs(){
        const logContent = document.getElementById('logs-content');
    
        logContent.innerHTML = '<div class="log-entry">Loading logs...</div>';
    
        try {
            const response = await fetch(`/api/vm-logs/${fileId}/`);
            
            if(!response.ok){
                const errorData = await response.json().catch(() => ({ error: 'Failed to fetch logs' }));
                throw new Error(errorData.error || 'Failed to fetch logs');
            }
    
            const data = await response.json();
    
            if(!data.logs || data.logs.length === 0){
                logContent.innerHTML = `<div class="log-entry">No logs</div>`;
                return;
            }
    
            // Get the first (and only) log file
            const logFile = data.logs[0];
    
            // Fetch the content of this log file
            const contentResponse = await fetch(`/api/vm-logs/${fileId}/${logFile.filename}/`);
            
            if(!contentResponse.ok){
                throw new Error('Failed to fetch log content');
            }
    
            const contentData = await contentResponse.json();
    
            // Split content by newlines
            const lines = contentData.content.split('\n');

            // Populate the file info header
            const fileInfo = document.getElementById('logs-file-info');
            const fileNameSpan = fileInfo.querySelector('.log-file-name');
            const fileLinesSpan = fileInfo.querySelector('.log-file-lines');

            fileNameSpan.textContent = logFile.filename;
            fileLinesSpan.textContent = `${lines.length} lines`;

            // Show the file info
            fileInfo.style.display = 'block';

            // Build HTML for log lines
            let html = '';
            lines.forEach((line, index) => {
                html += `
                    <div class="log-entry">
                        <span class="log-line-number">${index + 1}</span>
                        <span class="log-line-content">${line || ' '}</span>
                    </div>
                `;
            });

            logContent.innerHTML = html;
    
        } catch(error){
            logContent.innerHTML = `<div class="log-entry">Error: ${sanitizeError(error.message)}</div>`;
        }
    }

    ///////////////
    // Helpers
    //////////////

    // Helper function to sanitize error messages
    function sanitizeError(errorMessage) {
        if (!errorMessage) return 'Unknown error occurred';
        
        const error = String(errorMessage).toLowerCase();
        
        // File type/format errors
        if (error.includes('not supported') || error.includes('không phải định dạng') || 
            error.includes('file type') || error.includes('format')) {
            return 'File type not supported';
        }
        
        // File path/access errors
        if (error.includes('could not open') || error.includes('cannot open') || 
            error.includes('path') || error.includes('file not found') ||
            error.includes('permission denied') || error.includes('access denied')) {
            return 'Unable to access file. File may be corrupted or in an unsupported format.';
        }
        
        // Hash-related errors
        if (error.includes('no hash') || error.includes('hash')) {
            return 'Unable to calculate file hash';
        }
        
        // API/network errors
        if (error.includes('api') || error.includes('network') || 
            error.includes('connection') || error.includes('timeout')) {
            return 'External service unavailable. Please try again later.';
        }
        
        // VM/sandbox errors
        if (error.includes('vm') || error.includes('sandbox') || 
            error.includes('virtual machine')) {
            return 'Analysis environment error. Please try again.';
        }
        
        // LSTM/model errors
        if (error.includes('lstm') || error.includes('model') || 
            error.includes('neural') || error.includes('prediction')) {
            return 'Behavioral analysis failed. Insufficient data for analysis.';
        }
        
        // Database errors
        if (error.includes('database') || error.includes('db')) {
            return 'Database query failed';
        }
        
        // Generic fallback - don't show the actual error
        return 'An error occurred during analysis. Please try again or contact support if the issue persists.';
    }

    // Helper function to format file size
    function formatFileSize(bytes) {
        if (!bytes || bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    }

    // Refresh logs button handler
    const refreshLogsBtn = document.getElementById('refresh-logs');
    if (refreshLogsBtn) {
        refreshLogsBtn.addEventListener('click', function() {
            populateVMLogs();
        });
    }
    
    // Download logs button handler
    const downloadLogsBtn = document.getElementById('download-logs');
    if (downloadLogsBtn) {
        downloadLogsBtn.addEventListener('click', function() {
            console.log('Download logs clicked');

            try{
                const fileNameSpan = document.querySelector('.log-file-name');

                if(!fileNameSpan || !fileNameSpan.textContent){
                    alert('No log file abailable.')
                    return
                }

                const filename = fileNameSpan.textContent;

                const encodedFilename = encodeURIComponent(filename);
                const downloadUrl = `/api/download-log/${fileId}/${encodedFilename}/`;

                const link = document.createElement('a');
                link.href = downloadUrl;
                link.download = filename;
                link.style.display = 'none';
                document.body.appendChild(link);
                link.click();

                setTimeout(() => {
                    document.body.removeChild(link);
                }, 100);
        
            } catch (error){
                alert('Failed to download log file.')
            }
        });
    }

    const downloadReportBtn = document.getElementById('download-report');
    if (downloadReportBtn) {
        downloadReportBtn.addEventListener('click', function() {
            const downloadUrl = `/api/download-report/${fileId}/`;
            window.location.href = downloadUrl;
        });
    }
})