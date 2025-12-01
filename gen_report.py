from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle

def sanitize_error(error_message):
    if not error_message:
        return 'Unknown error occurred'
    
    error = str(error_message).lower()
    
    # File type/format errors
    if any(keyword in error for keyword in ['not supported', 'không phải định dạng', 
                                             'file type', 'format', 'định dạng']):
        return 'File type not supported'
    
    # File path/access errors
    if any(keyword in error for keyword in ['could not open', 'cannot open', 
                                            'path', 'file not found',
                                            'permission denied', 'access denied',
                                            'lỗi khi quét']):
        return 'Unable to access file. File may be corrupted or in an unsupported format.'
    
    # Hash-related errors
    if any(keyword in error for keyword in ['no hash', 'hash']):
        return 'Unable to calculate file hash'
    
    # API/network errors
    if any(keyword in error for keyword in ['api', 'network', 
                                            'connection', 'timeout']):
        return 'External service unavailable. Please try again later.'
    
    # VM/sandbox errors
    if any(keyword in error for keyword in ['vm', 'sandbox', 
                                            'virtual machine']):
        return 'Analysis environment error. Please try again.'
    
    # LSTM/model errors
    if any(keyword in error for keyword in ['lstm', 'model', 
                                            'neural', 'prediction']):
        return 'Behavioral analysis failed. Insufficient data for analysis.'
    
    # Database errors
    if any(keyword in error for keyword in ['database', 'db']):
        return 'Database query failed'
    
    # Generic fallback - don't show the actual error
    return 'An error occurred during analysis. Please try again or contact support if the issue persists.'

def generate_pdf(file_info, progress_data):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    content = []

    # Define simple table style
    def apply_table_style(table):
        """Apply simple, clean styling to tables"""
        table.setStyle(TableStyle([
            # Header row (if exists)
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f5f5f5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#333333')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            
            # All cells
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#000000')),
            
            # First column (labels) - slightly bold
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            
            # Alignment
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            
            # Padding
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            
            # Borders
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ]))
        return table

    # Custom styles
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=12,
        alignment=1,  # Center
        fontName='Helvetica-Bold'
    )
    
    heading2_style = ParagraphStyle(
        'Heading2Style',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#34495e'),
        spaceBefore=12,
        spaceAfter=8,
        fontName='Helvetica-Bold'
    )
    
    heading3_style = ParagraphStyle(
        'Heading3Style',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.HexColor('#34495e'),
        spaceBefore=10,
        spaceAfter=6,
        fontName='Helvetica-Bold'
    )
    
    # Style for hash values - smaller font, monospace, wraps properly
    hash_style = ParagraphStyle(
        'HashStyle',
        parent=styles['Normal'],
        fontSize=8,
        fontName='Courier',  # Monospace for better readability
        textColor=colors.HexColor('#000000'),
        leading=10,
        wordWrap='CJK'  # Enable word wrapping
    )

    # Title
    content.append(Paragraph("MalSandbox Report", title_style))
    content.append(Spacer(1, 0.2*inch))
    
    # File name
    file_name = file_info.get('original_name', 'Unknown')
    content.append(Paragraph(f"File: {file_name}", styles['Normal']))
    content.append(Spacer(1, 0.3*inch))

    # ========== SUMMARY SECTION ==========
    content.append(Paragraph("Summary", heading2_style))
    content.append(Spacer(1, 0.1*inch))
    
    ################
    # Interpreter
    ################
    interpreter = progress_data.get('interpreter', 'Unknown')
    content.append(Paragraph(f"<b>Interpreter:</b> {interpreter}", styles['Normal']))
    
    ######################
    # Pattern detection
    #####################
    content.append(Paragraph("Pattern Detection", heading3_style))

    # Get YARA data - use filtered matches for summary (more accurate, excludes false positives)
    yara_filtered_matches = progress_data.get('yara_filtered_matches', []) or []
    yara_raw_matches = progress_data.get('yara_raw_matches', []) or []
    yara_error = progress_data.get('yara_error') or progress_data.get('yara_scan_error')
    yara_count = len(yara_filtered_matches)
    
    # Infer completion: if matches exist or error exists, scan was completed
    yara_complete = progress_data.get('yara_scan_complete', 
                                      bool(yara_filtered_matches or yara_raw_matches or yara_error))

    # Determine status
    if not yara_complete:
        status = "Not Scanned"
    elif yara_error:
        status = f"Error: {sanitize_error(yara_error)}"
    elif yara_count == 0:
        status = "Clean - No threats"
    else:
        status = f"Threats Detected ({yara_count} matches)"

    # Display
    content.append(Paragraph(f"<b>Status:</b> {status}", styles['Normal']))
    
    ####################
    # Malware Database
    ###################
    content.append(Paragraph("Malware Database", heading3_style))

    # Get Bazaar data
    bazaar_success = progress_data.get('bazaar_success', False)
    bazaar_error = progress_data.get('bazaar_error')
    is_malicious = progress_data.get('bazaar_is_malicious', False)
    
    # Infer completion: if success flag exists in data or error exists, scan was completed
    bazaar_complete = progress_data.get('bazaar_scan_complete',
                                        'bazaar_success' in progress_data or bool(bazaar_error))

    # Determine status
    if not bazaar_complete:
        status = "Not Scanned"
    elif bazaar_error:
        status = f"API Error: {sanitize_error(bazaar_error)}"
    elif not bazaar_success:
        status = "API Error"
    elif is_malicious:
        status = "Malware Detected"
    else:
        status = "Clean - Not in database"

    # Display
    content.append(Paragraph(f"<b>Status:</b> {status}", styles['Normal']))
    
    ###################################
    # Behavioral Analysis
    ##################################
    content.append(Paragraph("Behavioral Analysis", heading3_style))
    # TODO: Add LSTM status
    # Get LSTM data
    lstm_decision = progress_data.get('lstm_final_decision')

    # Determine status
    if lstm_decision == 'anomalous':
        status = "Anomalous"
    elif lstm_decision == 'normal':
        status = "Normal"
    else:
        status = "Not Analyzed"

    # Display
    content.append(Paragraph(f"<b>Status:</b> {status}", styles['Normal']))
    
    # ========== DETAILS SECTION ==========
    # content.append(PageBreak())  # New page
    content.append(Spacer(1, 0.1*inch))
    content.append(Paragraph("Details", heading2_style))
    content.append(Spacer(1, 0.1*inch))
    
    # File Properties - use table
    content.append(Paragraph("File Properties", heading3_style))
    file_props = [
        ['File Name', file_name],
        ['File Size', f"{file_info.get('file_size', 0) / 1024:.2f} KB" if file_info.get('file_size') else 'Unknown'],
        ['File Type', file_info.get('file_type', 'Unknown')],
    ]
    table = Table(file_props, colWidths=[2*inch, 4*inch])
    apply_table_style(table)
    content.append(table)
    content.append(Spacer(1, 0.2*inch))
    
    # File Hashes - use table with wrapping for long hashes
    content.append(Paragraph("File Hashes", heading3_style))
    
    # Create hash data with Paragraph objects for proper wrapping
    md5_hash = file_info.get('md5_hash', 'Not available')
    sha1_hash = file_info.get('sha1_hash', 'Not available')
    sha256_hash = file_info.get('sha256_hash', 'Not available')
    
    hash_data = [
        ['MD5', Paragraph(md5_hash, hash_style) if md5_hash != 'Not available' else 'Not available'],
        ['SHA-1', Paragraph(sha1_hash, hash_style) if sha1_hash != 'Not available' else 'Not available'],
        ['SHA-256', Paragraph(sha256_hash, hash_style) if sha256_hash != 'Not available' else 'Not available'],
    ]
    hash_table = Table(hash_data, colWidths=[2*inch, 4*inch])
    apply_table_style(hash_table)
    content.append(hash_table)
    content.append(Spacer(1, 0.2*inch))
    
    ########################
    # Behavioral Analysis
    #######################
    content.append(Paragraph("Behavioral Analysis", heading3_style))

    # Get LSTM data
    lstm_decision = progress_data.get('lstm_final_decision')
    lstm_max_prob = progress_data.get('lstm_max_prob_anomaly')
    lstm_mean_prob = progress_data.get('lstm_mean_prob_anomaly')
    lstm_windows = progress_data.get('lstm_num_windows')
    lstm_error = progress_data.get('lstm_error')

    # Create table
    lstm_data = []

    if lstm_decision:
        decision_text = "Anomalous" if lstm_decision == 'anomalous' else "Normal"
        lstm_data.append(['Status', decision_text])
        
        if lstm_max_prob is not None:
            lstm_data.append(['Max Anomaly Probability', f"{lstm_max_prob * 100:.2f}%"])
        if lstm_mean_prob is not None:
            lstm_data.append(['Mean Anomaly Probability', f"{lstm_mean_prob * 100:.2f}%"])
        if lstm_windows is not None:
            lstm_data.append(['Windows Analyzed', str(lstm_windows)])
        if lstm_error:
            lstm_data.append(['Error', sanitize_error(lstm_error)])
    else:
        lstm_data.append(['Status', 'Not Analyzed'])

    if lstm_data:
        lstm_table = Table(lstm_data, colWidths=[2*inch, 4*inch])
        apply_table_style(lstm_table)
        content.append(lstm_table)
    else:
        content.append(Paragraph("No LSTM analysis data available", styles['Normal']))

    content.append(Spacer(1, 0.2*inch))
    
    # Malware Database
    content.append(Paragraph("Malware Database", heading3_style))

    # Get Bazaar data
    bazaar_success = progress_data.get('bazaar_success', False)
    bazaar_error = progress_data.get('bazaar_error') or progress_data.get('bazaar_scan_error')
    is_malicious = progress_data.get('bazaar_is_malicious', False)
    malware_info = progress_data.get('bazaar_malware_info', {})
    
    # Infer completion: if success flag exists in data or error exists, scan was completed
    bazaar_complete = progress_data.get('bazaar_scan_complete',
                                        'bazaar_success' in progress_data or bool(bazaar_error))

    # Create table
    bazaar_data = []

    if not bazaar_complete:
        bazaar_data.append(['Status', 'Not Scanned'])
    elif bazaar_error:
        bazaar_data.append(['Status', 'API Error'])
        bazaar_data.append(['Error', sanitize_error(bazaar_error)])
    elif not bazaar_success:
        bazaar_data.append(['Status', 'API Error'])
    elif is_malicious:
        bazaar_data.append(['Status', 'Malware Detected'])
        bazaar_data.append(['Database', 'Malware Bazaar (abuse.ch)'])
        bazaar_data.append(['Hash Checked', 'SHA-256'])
        
        # Add malware info if available
        if malware_info.get('signature'):
            bazaar_data.append(['Signature', malware_info['signature']])
        if malware_info.get('file_name'):
            bazaar_data.append(['Original Filename', malware_info['file_name']])
        if malware_info.get('file_type'):
            bazaar_data.append(['File Type', malware_info['file_type']])
        if malware_info.get('first_seen'):
            bazaar_data.append(['First Seen', malware_info['first_seen']])
        if malware_info.get('tags'):
            tags = malware_info['tags']
            tags_str = ', '.join(tags) if isinstance(tags, list) else str(tags)
            bazaar_data.append(['Tags', tags_str])
    else:
        bazaar_data.append(['Status', 'Clean - Not in database'])
        bazaar_data.append(['Database', 'Malware Bazaar (abuse.ch)'])
        bazaar_data.append(['Hash Checked', 'SHA-256'])

    bazaar_table = Table(bazaar_data, colWidths=[2*inch, 4*inch])
    apply_table_style(bazaar_table)
    content.append(bazaar_table)
    content.append(Spacer(1, 0.2*inch))
    
    # Pattern Detection
    content.append(Paragraph("Pattern Detection", heading3_style))

    # Get YARA data - use raw matches for details (shows all matches including filtered ones)
    yara_raw_matches = progress_data.get('yara_raw_matches', []) or []
    yara_filtered_matches = progress_data.get('yara_filtered_matches', []) or []
    yara_count = len(yara_filtered_matches)  # Count filtered matches (real threats)
    yara_error = progress_data.get('yara_error') or progress_data.get('yara_scan_error')
    
    # Infer completion: if matches exist or error exists, scan was completed
    yara_complete = progress_data.get('yara_scan_complete',
                                      bool(yara_filtered_matches or yara_raw_matches or yara_error))

    # Create status table
    yara_status_data = []

    if not yara_complete:
        yara_status_data.append(['Status', 'Not Scanned'])
    elif yara_error:
        yara_status_data.append(['Status', 'Error'])
        yara_status_data.append(['Error', sanitize_error(yara_error)])
    elif yara_count == 0:
        yara_status_data.append(['Status', 'Clean - No threats detected'])
        yara_status_data.append(['Total Matches', '0'])
    else:
        yara_status_data.append(['Status', f'Threats detected ({yara_count} matches)'])
        yara_status_data.append(['Total Matches', str(yara_count)])
        if len(yara_raw_matches) > yara_count:
            yara_status_data.append(['Raw Matches (before filtering)', str(len(yara_raw_matches))])

    yara_status_table = Table(yara_status_data, colWidths=[2*inch, 4*inch])
    apply_table_style(yara_status_table)
    content.append(yara_status_table)

    # Show filtered matches in details (these are the real threats)
    if yara_count > 0:
        content.append(Spacer(1, 0.15*inch))
        content.append(Paragraph("<b>Matched Rules:</b>", styles['Normal']))
        content.append(Spacer(1, 0.1*inch))
        
        # Show all filtered matches with better styling
        rule_style = ParagraphStyle(
            'RuleStyle',
            parent=styles['Normal'],
            fontSize=10,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=4,
            leftIndent=0
        )
        
        desc_style = ParagraphStyle(
            'DescStyle',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#555555'),
            leftIndent=20,
            spaceAfter=8,
            leading=12
        )
        
        for idx, match in enumerate(yara_filtered_matches, 1):
            rule_name = match.get('rule', 'Unknown')
            description = match.get('description', 'No description available')
            
            rule_text = f"{idx}. {rule_name}"
            content.append(Paragraph(rule_text, rule_style))
            
            if description and description != 'No description available':
                content.append(Paragraph(description, desc_style))

    content.append(Spacer(1, 0.2*inch))

    # Build PDF
    doc.build(content)
    buffer.seek(0)
    return buffer