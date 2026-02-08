"""
Generate realistic PDF and image attachments for OneNote testing.
Creates proper binary files that can be opened and demonstrate attachment processing.
"""

import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import csv

def create_pdf_files():
    """Create realistic PDF files for testing."""
    
    # Create AI Framework Benchmark PDF
    create_ai_benchmark_pdf()
    
    # Create Vector DB Performance Analysis PDF  
    create_vector_db_analysis_pdf()
    
    # Create Security Guidelines PDF
    create_security_guidelines_pdf()
    
    # Create Performance Optimization Guide PDF
    create_performance_guide_pdf()
    
    # Create additional research PDFs
    create_test_results_summary_pdf()
    create_attention_paper_pdf()
    create_rag_optimization_strategies_pdf()
    create_multimodal_embeddings_pdf()
    create_document_ai_layout_pdf()
    create_hybrid_search_survey_pdf()
    
    print("✅ Created PDF files")

def create_ai_benchmark_pdf():
    """Create AI Framework Benchmark 2026 PDF."""
    doc = SimpleDocTemplate(
        "notebook_attachments/AI_Framework_Benchmark_2026.pdf",
        pagesize=letter,
        rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title = Paragraph("AI Framework Performance Benchmark - 2026 Results", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))
    
    # Executive Summary
    exec_summary = Paragraph("""
    <b>Executive Summary</b><br/><br/>
    Comprehensive evaluation of RAG (Retrieval-Augmented Generation) frameworks across multiple dimensions 
    including performance, cost, and accuracy. This benchmark study evaluates leading vector database 
    solutions and embedding frameworks for enterprise AI applications.
    """, styles['Normal'])
    story.append(exec_summary)
    story.append(Spacer(1, 12))
    
    # Performance Table
    data = [
        ['Framework', 'Response Time', 'Accuracy', 'Cost/Query', 'Throughput'],
        ['Azure AI Search', '1.2s', '87%', '$0.003', '50 qps'],
        ['Pinecone', '1.5s', '85%', '$0.005', '45 qps'], 
        ['ChromaDB', '2.1s', '82%', '$0.002', '35 qps'],
        ['Weaviate', '1.8s', '84%', '$0.004', '40 qps']
    ]
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(table)
    story.append(Spacer(1, 12))
    
    # Key Findings
    findings = Paragraph("""
    <b>Key Findings</b><br/><br/>
    • Azure AI Search demonstrates 23% faster hybrid search performance compared to alternatives<br/>
    • Multi-modal embeddings improve retrieval accuracy by 31% for document-heavy workloads<br/>
    • Custom chunking strategies reduce hallucination rates by 18%<br/>
    • Cost per query varies significantly, with ChromaDB offering the most economical solution<br/>
    • Throughput capacity directly correlates with infrastructure investment
    """, styles['Normal'])
    story.append(findings)
    
    doc.build(story)

def create_vector_db_analysis_pdf():
    """Create Vector Database Performance Analysis PDF."""
    doc = SimpleDocTemplate(
        "notebook_attachments/Vector_DB_Performance_Analysis.pdf",
        pagesize=A4
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    title = Paragraph("Vector Database Scalability Analysis", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))
    
    content = Paragraph("""
    <b>Test Configuration</b><br/><br/>
    • Document corpus: 1M+ technical documents<br/>
    • Query load: 100 concurrent users<br/>
    • Embedding model: text-embedding-3-large (1536 dimensions)<br/>
    • Test duration: 72 hours continuous operation<br/><br/>
    
    <b>Performance Results</b><br/><br/>
    Azure AI Search demonstrates superior performance for hybrid search scenarios, combining semantic 
    similarity with traditional keyword matching. The system maintains sub-2-second response times 
    even under heavy load conditions.<br/><br/>
    
    <b>Scalability Metrics</b><br/>
    • Index creation time: 45 minutes for 1M documents<br/>
    • Query latency P95: Under 2 seconds<br/>
    • Memory usage: 8GB for 1M vectors (1536-dim)<br/>
    • Concurrent query capacity: 200+ simultaneous requests<br/><br/>
    
    <b>Recommendations</b><br/>
    For production deployments processing large document collections, Azure AI Search provides 
    the optimal balance of performance, cost, and feature richness. The hybrid search capabilities 
    are particularly valuable for RAG applications requiring both semantic and exact match capabilities.
    """, styles['Normal'])
    
    story.append(content)
    doc.build(story)

def create_security_guidelines_pdf():
    """Create Security Guidelines PDF."""
    doc = SimpleDocTemplate(
        "notebook_attachments/LLM_Security_Guidelines.pdf", 
        pagesize=letter
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    title = Paragraph("LLM Security Guidelines - Enterprise AI Systems", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))
    
    content = Paragraph("""
    <b>Security Framework Overview</b><br/><br/>
    Enterprise AI applications require comprehensive security measures to protect sensitive data 
    and ensure compliance with regulatory requirements. This document outlines security best 
    practices for LLM-based systems.<br/><br/>
    
    <b>Data Protection</b><br/>
    • Encrypt all data in transit and at rest<br/>
    • Implement proper access controls and authentication<br/>
    • Use Azure Key Vault for credential management<br/>
    • Regular security audits and penetration testing<br/><br/>
    
    <b>Model Security</b><br/>
    • Input validation and sanitization<br/>
    • Prompt injection prevention<br/>
    • Output filtering and content moderation<br/>
    • Model version control and integrity verification<br/><br/>
    
    <b>Compliance Requirements</b><br/>
    • SOC 2 Type II certification<br/>
    • GDPR compliance for EU data<br/>
    • HIPAA compliance for healthcare data<br/>
    • Regular compliance assessments and reporting
    """, styles['Normal']) 
    
    story.append(content)
    doc.build(story)

def create_performance_guide_pdf():
    """Create Performance Optimization Guide PDF."""
    doc = SimpleDocTemplate(
        "notebook_attachments/Performance_Optimization_Guide.pdf",
        pagesize=letter
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    title = Paragraph("RAG Performance Optimization Guide", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))
    
    optimization_data = [
        ['Optimization Area', 'Technique', 'Expected Impact'],
        ['Chunking Strategy', 'Semantic boundaries', '15-20% accuracy gain'],
        ['Embedding Model', 'text-embedding-3-large', '10% better retrieval'],
        ['Index Configuration', 'Hybrid search enabled', '25% faster queries'],
        ['Caching Layer', 'Redis for embeddings', '60% latency reduction'],
        ['Load Balancing', 'Auto-scaling groups', '3x throughput capacity']
    ]
    
    table = Table(optimization_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(table)
    story.append(Spacer(1, 12))
    
    implementation = Paragraph("""
    <b>Implementation Guidelines</b><br/><br/>
    The optimization strategies outlined above have been tested in production environments 
    and demonstrate consistent performance improvements. Implementation should be done 
    incrementally, with careful monitoring of system metrics at each stage.<br/><br/>
    
    <b>Monitoring and Metrics</b><br/>
    Key performance indicators to track during optimization:<br/>
    • Query response time (target: <2 seconds)<br/>
    • Retrieval accuracy (target: >85%)<br/>
    • System throughput (target: >50 queries/second)<br/>
    • Resource utilization (CPU, memory, storage)<br/>
    • Cost per query and operational expenses
    """, styles['Normal'])
    
    story.append(implementation)
    doc.build(story)

def create_test_results_summary_pdf():
    """Create Test Results Summary PDF."""
    doc = SimpleDocTemplate(
        "notebook_attachments/test_results_summary.pdf",
        pagesize=letter
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    title = Paragraph("Attachment Processing Test Results - February 2026", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))
    
    # Test results table
    test_data = [
        ['Test Category', 'Files Tested', 'Success Rate', 'Avg Processing Time'],
        ['PDF Documents', '847', '95.2%', '3.4s'],
        ['PNG Images', '423', '92.8%', '2.1s'],
        ['JPEG Images', '356', '94.1%', '2.3s'],
        ['DOCX Files', '189', '97.3%', '4.2s'],
        ['XLSX Files', '134', '91.7%', '5.1s']
    ]
    
    table = Table(test_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(table)
    story.append(Spacer(1, 12))
    
    summary = Paragraph("""
    <b>Testing Summary</b><br/><br/>
    Comprehensive testing of attachment processing capabilities across multiple file formats. The system
    demonstrates high success rates for document processing, with particular strength in PDF and Office
    document handling. Image processing shows excellent OCR accuracy for technical diagrams and screenshots.<br/><br/>
    
    <b>Key Findings</b><br/>
    • Text extraction accuracy: 96.3% average across all formats<br/>
    • Table structure preservation: 94.7% for complex layouts<br/>
    • Handwriting recognition: 89.2% accuracy for legible text<br/>
    • Multi-language support: 92.1% accuracy for non-English content
    """, styles['Normal'])
    
    story.append(summary)
    doc.build(story)

def create_attention_paper_pdf():
    """Create Attention Is All You Need 2023 Update PDF."""
    doc = SimpleDocTemplate(
        "notebook_attachments/Attention_Is_All_You_Need_2023_Update.pdf",
        pagesize=letter
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    title = Paragraph("Attention Is All You Need: 2023 Architecture Updates", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))
    
    abstract = Paragraph("""
    <b>Abstract</b><br/><br/>
    This paper presents significant improvements to the Transformer architecture introduced in the original
    "Attention Is All You Need" work. Key enhancements include efficiency optimizations, reduced memory
    consumption, and improved performance on long sequences. These updates are particularly relevant for
    large-scale RAG systems processing extensive document collections.
    """, styles['Normal'])
    story.append(abstract)
    story.append(Spacer(1, 12))
    
    improvements = Paragraph("""
    <b>Key Improvements</b><br/><br/>
    • <b>Flash Attention</b>: 40% reduction in GPU memory usage<br/>
    • <b>Rotary Position Embedding</b>: Better handling of long sequences<br/>
    • <b>Layer Normalization Optimization</b>: 15% faster training<br/>
    • <b>Gradient Checkpointing</b>: Enables training of larger models<br/>
    • <b>Mixed Precision Training</b>: 2x speedup with minimal accuracy loss
    """, styles['Normal'])
    
    story.append(improvements)
    doc.build(story)

def create_rag_optimization_strategies_pdf():
    """Create RAG Performance Optimization Strategies PDF."""
    doc = SimpleDocTemplate(
        "notebook_attachments/RAG_Performance_Optimization_Strategies.pdf",
        pagesize=letter
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    title = Paragraph("RAG Performance Optimization Strategies", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))
    
    # Optimization techniques table
    opt_data = [
        ['Strategy', 'Implementation', 'Performance Gain'],
        ['Chunking Optimization', 'Semantic boundaries', '18% accuracy improvement'],
        ['Embedding Caching', 'Redis-based cache', '65% latency reduction'],
        ['Hybrid Search', 'Semantic + keyword', '23% better relevance'],
        ['Result Reranking', 'Cross-encoder model', '12% accuracy boost'],
        ['Context Compression', 'Selective inclusion', '30% token reduction']
    ]
    
    table = Table(opt_data, colWidths=[2*inch, 2*inch, 2*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(table)
    doc.build(story)

def create_multimodal_embeddings_pdf():
    """Create Multi-Modal Embeddings Comparative Study PDF."""
    doc = SimpleDocTemplate(
        "notebook_attachments/Multi_Modal_Embeddings_Comparative_Study.pdf",
        pagesize=letter
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    title = Paragraph("Multi-Modal Embeddings: Comparative Study 2026", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))
    
    content = Paragraph("""
    <b>Research Overview</b><br/><br/>
    Comprehensive evaluation of multi-modal embedding approaches for document understanding systems.
    This study compares text-only, vision-only, and combined embedding strategies for RAG applications
    processing documents with mixed content types.<br/><br/>
    
    <b>Key Findings</b><br/>
    • Combined text+vision embeddings improve retrieval by 31%<br/>
    • Vision-language models excel at diagram understanding<br/>
    • Text embeddings remain superior for pure textual content<br/>
    • Computational overhead is manageable for production use<br/><br/>
    
    <b>Recommended Architecture</b><br/>
    For OneNote RAG systems: Use text-embedding-3-large for text content and combine with
    vision embeddings for image-heavy documents. This hybrid approach maximizes both accuracy
    and efficiency while maintaining reasonable computational costs.
    """, styles['Normal'])
    
    story.append(content)
    doc.build(story)

def create_document_ai_layout_pdf():
    """Create Document AI Layout Understanding PDF.""" 
    doc = SimpleDocTemplate(
        "notebook_attachments/Document_AI_Layout_Understanding.pdf",
        pagesize=letter
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    title = Paragraph("Advanced Document AI: Layout Understanding Techniques", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))
    
    techniques = Paragraph("""
    <b>Layout Analysis Techniques</b><br/><br/>
    Modern document intelligence systems must preserve semantic meaning while extracting content.
    This paper outlines advanced techniques for understanding document structure and layout.<br/><br/>
    
    <b>Core Technologies</b><br/>
    • <b>LayoutLM</b>: Transformer model for document understanding<br/>
    • <b>Table Detection</b>: CNN-based table boundary identification<br/>
    • <b>Reading Order</b>: Graph-based sequence determination<br/>
    • <b>Visual Elements</b>: Image and chart content extraction<br/><br/>
    
    <b>Implementation for RAG</b><br/>
    For OneNote attachment processing, layout understanding enables better chunking
    strategies that preserve document structure. This leads to more accurate retrieval
    and better context preservation in generated responses.
    """, styles['Normal'])
    
    story.append(techniques)
    doc.build(story)

def create_hybrid_search_survey_pdf():
    """Create Hybrid Search Methods Survey PDF."""
    doc = SimpleDocTemplate(
        "notebook_attachments/Hybrid_Search_Methods_Survey.pdf",
        pagesize=letter
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    title = Paragraph("Hybrid Search Methods: A Comprehensive Survey", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))
    
    # Search methods comparison
    search_data = [
        ['Method', 'Precision', 'Recall', 'Latency', 'Use Case'],
        ['Dense (Semantic)', 'High', 'Medium', 'Fast', 'Conceptual queries'],
        ['Sparse (Keyword)', 'Medium', 'High', 'Very Fast', 'Exact matches'],
        ['Hybrid (Combined)', 'Very High', 'High', 'Fast', 'General purpose'],
        ['Reranked Hybrid', 'Highest', 'High', 'Medium', 'High precision needs']
    ]
    
    table = Table(search_data, colWidths=[1.5*inch, 1*inch, 1*inch, 1*inch, 1.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.navy),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(table)
    story.append(Spacer(1, 12))
    
    conclusion = Paragraph("""
    <b>Survey Conclusions</b><br/><br/>
    Hybrid search methods consistently outperform single-mode approaches across diverse query types.
    The combination of semantic understanding with exact keyword matching provides optimal results
    for enterprise RAG systems. Azure AI Search's implementation of hybrid search demonstrates
    superior performance characteristics for production deployments.
    """, styles['Normal'])
    
    story.append(conclusion)
    doc.build(story)

def create_image_files():
    """Create realistic architecture diagram images."""
    
    # RAG Architecture Overview
    create_rag_architecture_image()
    
    # Document Processing Flow  
    create_document_flow_image()
    
    # Query Execution Diagram
    create_query_execution_image()
    
    # Additional images for Page 2 and 3
    create_deployment_architecture_image()
    create_pdf_processing_example_image()
    create_image_ocr_demo_image()
    create_table_extraction_sample_image()
    create_testing_dashboard_screenshot_image()
    
    print("✅ Created image files")

def create_rag_architecture_image():
    """Create RAG architecture overview diagram.""" 
    img = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        font_title = ImageFont.truetype("arial.ttf", 24)
        font_normal = ImageFont.truetype("arial.ttf", 14)
        font_small = ImageFont.truetype("arial.ttf", 12)
    except:
        font_title = ImageFont.load_default()
        font_normal = ImageFont.load_default() 
        font_small = ImageFont.load_default()
    
    # Title
    draw.text((250, 20), "RAG Architecture Overview", fill='black', font=font_title)
    
    # Components
    components = [
        ("User Query", 50, 100, 150, 50),
        ("Query Processing", 250, 100, 150, 50),
        ("Vector Search", 450, 100, 150, 50),
        ("Document Retrieval", 650, 100, 120, 50),
        ("OneNote Graph API", 50, 200, 150, 50),
        ("Document Intelligence", 250, 200, 150, 50), 
        ("Embedding Service", 450, 200, 150, 50),
        ("Azure AI Search", 650, 200, 120, 50),
        ("Response Generation", 350, 300, 150, 50)
    ]
    
    # Draw components
    for name, x, y, w, h in components:
        draw.rectangle([x, y, x+w, y+h], outline='blue', width=2, fill='lightblue')
        draw.text((x+10, y+15), name, fill='darkblue', font=font_small)
    
    # Draw arrows
    arrows = [
        (200, 125, 250, 125),  # Query -> Processing
        (400, 125, 450, 125),  # Processing -> Vector Search
        (600, 125, 650, 125),  # Vector Search -> Retrieval
        (125, 150, 125, 200),  # Down to Graph API
        (325, 150, 325, 200),  # Down to Doc Intelligence
        (525, 150, 525, 200),  # Down to Embedding
        (710, 150, 710, 200),  # Down to AI Search
        (425, 250, 425, 300)   # Up to Response Gen
    ]
    
    for x1, y1, x2, y2 in arrows:
        draw.line([(x1, y1), (x2, y2)], fill='red', width=3)
        # Arrow head
        if x1 == x2:  # Vertical arrow
            if y2 > y1:  # Down arrow
                draw.polygon([(x2-5, y2-10), (x2, y2), (x2+5, y2-10)], fill='red')
            else:  # Up arrow
                draw.polygon([(x2-5, y2+10), (x2, y2), (x2+5, y2+10)], fill='red')
        else:  # Horizontal arrow
            draw.polygon([(x2-10, y2-5), (x2, y2), (x2-10, y2+5)], fill='red')
    
    # Data flow labels
    draw.text((60, 400), "Data Flow:", fill='black', font=font_normal)
    draw.text((60, 420), "1. OneNote notebooks → Graph API extraction", fill='black', font=font_small)
    draw.text((60, 440), "2. Attachments → Document Intelligence processing", fill='black', font=font_small)
    draw.text((60, 460), "3. Content → Embedding → Vector storage", fill='black', font=font_small)
    draw.text((60, 480), "4. Queries → Hybrid search → Relevant chunks", fill='black', font=font_small)
    
    img.save("notebook_attachments/rag_architecture_overview.png")

def create_document_flow_image():
    """Create document processing flow diagram."""
    img = Image.new('RGB', (900, 700), color='white')
    draw = ImageDraw.Draw(img) 
    
    try:
        font_title = ImageFont.truetype("arial.ttf", 20)
        font_normal = ImageFont.truetype("arial.ttf", 12)
    except:
        font_title = ImageFont.load_default()
        font_normal = ImageFont.load_default()
    
    # Title
    draw.text((300, 20), "Document Processing Pipeline", fill='black', font=font_title)
    
    # Process steps
    steps = [
        ("OneNote Notebook", 400, 80, 100, 40, 'lightgreen'),
        ("Extract Pages", 400, 160, 100, 40, 'lightblue'),
        ("Find Attachments", 400, 240, 100, 40, 'lightblue'),
        ("Download Content", 200, 320, 120, 40, 'lightyellow'),
        ("Document Intelligence", 600, 320, 140, 40, 'lightyellow'),
        ("Extract Text/Tables", 200, 400, 120, 40, 'lightcoral'),
        ("OCR Images", 600, 400, 120, 40, 'lightcoral'),
        ("Semantic Chunking", 400, 480, 120, 40, 'lightpink'),
        ("Generate Embeddings", 400, 560, 120, 40, 'lavender'),
        ("Store in AI Search", 400, 640, 120, 40, 'lightgreen')
    ]
    
    # Draw process steps
    for name, x, y, w, h, color in steps:
        draw.rectangle([x, y, x+w, y+h], outline='black', width=2, fill=color)
        # Handle text wrapping
        if len(name) > 12:
            words = name.split()
            if len(words) > 1:
                mid = len(words) // 2
                line1 = ' '.join(words[:mid])
                line2 = ' '.join(words[mid:])
                draw.text((x+5, y+8), line1, fill='black', font=font_normal)
                draw.text((x+5, y+22), line2, fill='black', font=font_normal)
            else:
                draw.text((x+5, y+15), name, fill='black', font=font_normal)
        else:
            draw.text((x+5, y+15), name, fill='black', font=font_normal)
    
    # Draw flow arrows
    flow_arrows = [
        (450, 120, 450, 160),  # Notebook -> Extract
        (450, 200, 450, 240),  # Extract -> Find 
        (400, 260, 320, 320),  # Find -> Download (left)
        (500, 260, 660, 320),  # Find -> Doc Intel (right)
        (260, 360, 260, 400),  # Download -> Extract Text
        (670, 360, 670, 400),  # Doc Intel -> OCR
        (260, 440, 420, 480),  # Extract Text -> Chunking
        (670, 440, 500, 480),  # OCR -> Chunking
        (450, 520, 450, 560),  # Chunking -> Embeddings
        (450, 600, 450, 640)   # Embeddings -> Store
    ]
    
    for x1, y1, x2, y2 in flow_arrows:
        draw.line([(x1, y1), (x2, y2)], fill='red', width=2)
        # Simple arrow head
        if abs(x2-x1) > abs(y2-y1):  # More horizontal
            if x2 > x1:  # Right arrow
                draw.polygon([(x2-8, y2-4), (x2, y2), (x2-8, y2+4)], fill='red')
            else:  # Left arrow  
                draw.polygon([(x2+8, y2-4), (x2, y2), (x2+8, y2+4)], fill='red')
        else:  # More vertical
            if y2 > y1:  # Down arrow
                draw.polygon([(x2-4, y2-8), (x2, y2), (x2+4, y2-8)], fill='red')
            else:  # Up arrow
                draw.polygon([(x2-4, y2+8), (x2, y2), (x2+4, y2+8)], fill='red')
    
    img.save("notebook_attachments/document_processing_flow.png")

def create_query_execution_image():
    """Create query execution diagram."""
    img = Image.new('RGB', (800, 500), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        font_title = ImageFont.truetype("arial.ttf", 18)
        font_normal = ImageFont.truetype("arial.ttf", 11)
    except:
        font_title = ImageFont.load_default()
        font_normal = ImageFont.load_default()
    
    # Title
    draw.text((250, 20), "Query Execution Flow", fill='black', font=font_title)
    
    # Components
    query_components = [
        ("User Query", 50, 70, 100, 35, 'lightblue'),
        ("Query Embedding", 200, 70, 120, 35, 'lightgreen'),
        ("Hybrid Search", 370, 70, 100, 35, 'lightyellow'),
        ("Result Ranking", 520, 70, 100, 35, 'lightcoral'),
        ("Context Assembly", 670, 70, 120, 35, 'lavender'),
        
        ("Vector Search", 150, 150, 100, 35, 'lightgray'),
        ("Keyword Search", 300, 150, 100, 35, 'lightgray'),
        
        ("Top-K Results", 200, 230, 100, 35, 'lightpink'),
        ("Re-ranking", 350, 230, 100, 35, 'lightpink'),
        
        ("Final Response", 400, 310, 120, 35, 'lightgreen')
    ]
    
    # Draw components
    for name, x, y, w, h, color in query_components:
        draw.rectangle([x, y, x+w, y+h], outline='black', width=1, fill=color)
        if len(name) > 10:
            words = name.split()
            if len(words) > 1:
                draw.text((x+5, y+8), words[0], fill='black', font=font_normal)
                draw.text((x+5, y+22), ' '.join(words[1:]), fill='black', font=font_normal)
            else:
                draw.text((x+5, y+15), name, fill='black', font=font_normal)
        else:
            draw.text((x+5, y+15), name, fill='black', font=font_normal)
    
    img.save("notebook_attachments/query_execution_diagram.png")

def create_deployment_architecture_image():
    """Create deployment architecture diagram."""
    img = Image.new('RGB', (900, 600), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        font_title = ImageFont.truetype("arial.ttf", 20)
        font_normal = ImageFont.truetype("arial.ttf", 12)
    except:
        font_title = ImageFont.load_default()
        font_normal = ImageFont.load_default()
    
    # Title
    draw.text((350, 20), "Production Deployment Architecture", fill='black', font=font_title)
    
    # Infrastructure layers
    layers = [
        ("Load Balancer", 400, 80, 100, 30, 'lightcoral'),
        ("API Gateway", 200, 140, 120, 40, 'lightblue'),
        ("Auth Service", 500, 140, 120, 40, 'lightblue'),
        ("Backend API", 100, 220, 100, 40, 'lightgreen'),
        ("Ingestion Worker", 250, 220, 120, 40, 'lightgreen'),
        ("RAG Orchestrator", 420, 220, 120, 40, 'lightgreen'),
        ("Graph Client", 600, 220, 100, 40, 'lightgreen'),
        ("Azure AI Search", 150, 320, 120, 40, 'lightyellow'),
        ("Document Intelligence", 350, 320, 140, 40, 'lightyellow'),
        ("OpenAI Service", 550, 320, 120, 40, 'lightyellow'),
        ("Redis Cache", 100, 420, 100, 40, 'lightpink'),
        ("Blob Storage", 300, 420, 120, 40, 'lightpink'),
        ("Key Vault", 500, 420, 100, 40, 'lightpink'),
        ("Monitoring", 650, 420, 100, 40, 'lightpink')
    ]
    
    # Draw components
    for name, x, y, w, h, color in layers:
        draw.rectangle([x, y, x+w, y+h], outline='black', width=1, fill=color)
        if len(name) > 12:
            words = name.split()
            if len(words) > 1:
                draw.text((x+5, y+8), words[0], fill='black', font=font_normal)
                draw.text((x+5, y+22), ' '.join(words[1:]), fill='black', font=font_normal)
            else:
                draw.text((x+5, y+15), name, fill='black', font=font_normal)
        else:
            draw.text((x+10, y+15), name, fill='black', font=font_normal)
    
    # Add scaling annotations
    draw.text((50, 520), "Scaling Features:", fill='black', font=font_normal)
    draw.text((50, 540), "• Auto-scaling groups for API services", fill='darkgreen', font=font_normal)
    draw.text((50, 560), "• Redis cluster for caching layer", fill='darkgreen', font=font_normal)
    draw.text((50, 580), "• Multi-region deployment support", fill='darkgreen', font=font_normal)
    
    img.save("notebook_attachments/deployment_architecture.png")

def create_pdf_processing_example_image():
    """Create PDF processing example screenshot."""
    img = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        font_title = ImageFont.truetype("arial.ttf", 16)
        font_normal = ImageFont.truetype("arial.ttf", 11)
        font_code = ImageFont.truetype("consolas.ttf", 10)
    except:
        font_title = ImageFont.load_default()
        font_normal = ImageFont.load_default()
        font_code = ImageFont.load_default()
    
    # Title
    draw.text((250, 20), "PDF Processing Example - Document Intelligence", fill='black', font=font_title)
    
    # Simulate a PDF processing interface
    draw.rectangle([50, 60, 750, 550], outline='black', width=2, fill='lightgray')
    
    # Input section
    draw.rectangle([70, 80, 370, 200], outline='darkblue', width=2, fill='white')
    draw.text((80, 90), "Input PDF: research_paper.pdf", fill='darkblue', font=font_normal)
    draw.text((80, 110), "Size: 2.3 MB | Pages: 15", fill='gray', font=font_normal)
    
    # Simulate PDF preview
    draw.rectangle([80, 130, 360, 190], outline='gray', width=1, fill='lightyellow')
    draw.text((90, 140), "AI Framework Benchmark Results", fill='black', font=font_normal)
    draw.text((90, 155), "Table 1: Performance Metrics", fill='black', font=font_normal)
    draw.text((90, 170), "| Framework | Time | Accuracy |", fill='darkblue', font=font_code)
    
    # Processing status
    draw.rectangle([390, 80, 730, 200], outline='darkgreen', width=2, fill='white')
    draw.text((400, 90), "Processing Status", fill='darkgreen', font=font_normal)
    draw.text((400, 110), "✓ Document uploaded", fill='green', font=font_normal)
    draw.text((400, 130), "✓ Text extraction complete", fill='green', font=font_normal)
    draw.text((400, 150), "✓ Table detection: 3 tables found", fill='green', font=font_normal)
    draw.text((400, 170), "✓ Content chunked into 12 segments", fill='green', font=font_normal)
    
    # Output section
    draw.rectangle([70, 220, 730, 530], outline='purple', width=2, fill='white')
    draw.text((80, 230), "Extracted Content & Metadata", fill='purple', font=font_normal)
    
    # Simulate extracted text
    extracted_text = [
        "Extracted Text (2,847 characters):",
        "# AI Framework Performance Benchmark - 2026 Results",
        "",
        "## Executive Summary", 
        "Comprehensive evaluation of RAG frameworks across multiple...",
        "",
        "## Performance Metrics",
        "| Framework | Response Time | Accuracy | Cost/Query |",
        "| Azure AI Search | 1.2s | 87% | $0.003 |",
        "| Pinecone | 1.5s | 85% | $0.005 |",
        "",
        "Tables Extracted: 3",
        "Languages Detected: English (99.2% confidence)",
        "Key-Value Pairs: 15 found",
        "Processing Model: prebuilt-layout"
    ]
    
    y_pos = 250
    for line in extracted_text:
        if y_pos > 510:
            break
        color = 'darkblue' if line.startswith('#') or line.startswith('|') else 'black'
        draw.text((80, y_pos), line, fill=color, font=font_code)
        y_pos += 15
    
    img.save("notebook_attachments/pdf_processing_example.png")

def create_image_ocr_demo_image():
    """Create OCR demo screenshot."""
    img = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        font_title = ImageFont.truetype("arial.ttf", 16)
        font_normal = ImageFont.truetype("arial.ttf", 11)
    except:
        font_title = ImageFont.load_default()
        font_normal = ImageFont.load_default()
    
    # Title
    draw.text((280, 20), "OCR Processing Demo - Technical Diagram", fill='black', font=font_title)
    
    # Simulate OCR interface
    draw.rectangle([50, 60, 750, 550], outline='black', width=2, fill='lightgray')
    
    # Original image preview
    draw.rectangle([70, 80, 370, 280], outline='darkred', width=2, fill='white')
    draw.text((80, 90), "Input Image: architecture_diagram.png", fill='darkred', font=font_normal)
    
    # Simulate a technical diagram
    draw.rectangle([80, 110, 360, 270], outline='blue', width=2, fill='lightblue')
    draw.text((100, 130), "USER QUERY", fill='black', font=font_normal)
    draw.rectangle([90, 120, 180, 150], outline='black', width=1)
    
    draw.text((220, 130), "→", fill='red', font=font_title)
    
    draw.text((250, 130), "EMBEDDINGS", fill='black', font=font_normal)
    draw.rectangle([240, 120, 350, 150], outline='black', width=1)
    
    draw.text((200, 170), "↓", fill='red', font=font_title)
    
    draw.text((180, 190), "VECTOR SEARCH", fill='black', font=font_normal) 
    draw.rectangle([170, 180, 290, 210], outline='black', width=1)
    
    draw.text((200, 230), "↓", fill='red', font=font_title)
    
    draw.text((190, 250), "RESPONSE", fill='black', font=font_normal)
    draw.rectangle([180, 240, 270, 270], outline='black', width=1)
    
    # OCR Results
    draw.rectangle([390, 80, 730, 530], outline='darkgreen', width=2, fill='white')
    draw.text((400, 90), "OCR Extraction Results", fill='darkgreen', font=font_normal)
    
    ocr_results = [
        "Detected Text Elements:",
        "",
        "USER QUERY (confidence: 98.3%)",
        "Position: (90, 120) - (180, 150)",
        "",
        "EMBEDDINGS (confidence: 97.1%)", 
        "Position: (240, 120) - (350, 150)",
        "",
        "VECTOR SEARCH (confidence: 99.2%)",
        "Position: (170, 180) - (290, 210)",
        "",
        "RESPONSE (confidence: 96.8%)",
        "Position: (180, 240) - (270, 270)",
        "",
        "Flow Arrows Detected: 3",
        "Layout Type: Flowchart/Process Diagram",
        "Reading Order: Top-to-bottom, left-to-right",
        "",
        "Extracted Workflow:",
        "1. User Query → Embeddings", 
        "2. Embeddings → Vector Search",
        "3. Vector Search → Response"
    ]
    
    y_pos = 110
    for line in ocr_results:
        if y_pos > 510:
            break
        color = 'darkgreen' if line.endswith('%') else 'black'
        draw.text((400, y_pos), line, fill=color, font=font_normal)
        y_pos += 15
    
    img.save("notebook_attachments/image_ocr_demo.png")

def create_table_extraction_sample_image():
    """Create table extraction sample screenshot."""
    img = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        font_title = ImageFont.truetype("arial.ttf", 16)
        font_normal = ImageFont.truetype("arial.ttf", 10)
    except:
        font_title = ImageFont.load_default()
        font_normal = ImageFont.load_default()
    
    # Title
    draw.text((250, 20), "Table Extraction & Markdown Conversion", fill='black', font=font_title)
    
    # Main container
    draw.rectangle([30, 60, 770, 570], outline='black', width=2, fill='lightgray')
    
    # Original table (simulated PDF/image)
    draw.rectangle([50, 80, 380, 280], outline='darkblue', width=2, fill='white')
    draw.text((60, 90), "Original Table in Document", fill='darkblue', font=font_normal)
    
    # Draw a sample table
    table_data = [
        ["Framework", "Response Time", "Accuracy"],
        ["Azure AI Search", "1.2s", "87%"],
        ["Pinecone", "1.5s", "85%"], 
        ["ChromaDB", "2.1s", "82%"]
    ]
    
    start_x, start_y = 60, 110
    cell_width, cell_height = 100, 25
    
    for row_idx, row in enumerate(table_data):
        for col_idx, cell in enumerate(row):
            x = start_x + col_idx * cell_width
            y = start_y + row_idx * cell_height
            
            # Header row background
            fill_color = 'lightblue' if row_idx == 0 else 'white'
            draw.rectangle([x, y, x + cell_width, y + cell_height], 
                         outline='black', width=1, fill=fill_color)
            draw.text((x + 5, y + 8), cell, fill='black', font=font_normal)
    
    # Arrow
    draw.text((390, 180), "→ EXTRACTION →", fill='red', font=font_title)
    
    # Extracted markdown
    draw.rectangle([420, 80, 750, 550], outline='darkgreen', width=2, fill='white')
    draw.text((430, 90), "Extracted Markdown Format", fill='darkgreen', font=font_normal)
    
    markdown_output = [
        "## Table 1",
        "Rows: 4, Columns: 3",
        "",
        "| Framework | Response Time | Accuracy |",
        "|-----------|---------------|----------|",
        "| Azure AI Search | 1.2s | 87% |",
        "| Pinecone | 1.5s | 85% |", 
        "| ChromaDB | 2.1s | 82% |",
        "",
        "Table Metadata:",
        "• Confidence Score: 97.3%",
        "• Cell Detection: 12/12 cells found",
        "• Header Row: Detected",
        "• Data Types: Text, Time, Percentage",
        "",
        "Structure Analysis:",
        "• Column 1: Framework names (text)",
        "• Column 2: Performance metrics (time)",
        "• Column 3: Accuracy percentages (numeric)",
        "",
        "Quality Indicators:",
        "• Border Detection: Excellent",
        "• Text Alignment: Consistent", 
        "• Character Recognition: 99.1%"
    ]
    
    y_pos = 110
    for line in markdown_output:
        if y_pos > 530:
            break
        color = 'darkblue' if line.startswith('|') or line.startswith('#') else 'black'
        draw.text((430, y_pos), line, fill=color, font=font_normal)
        y_pos += 15
    
    img.save("notebook_attachments/table_extraction_sample.png")

def create_testing_dashboard_screenshot_image():
    """Create testing dashboard screenshot."""
    img = Image.new('RGB', (1000, 700), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        font_title = ImageFont.truetype("arial.ttf", 18)
        font_normal = ImageFont.truetype("arial.ttf", 12)
        font_small = ImageFont.truetype("arial.ttf", 10)
    except:
        font_title = ImageFont.load_default()
        font_normal = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Title bar
    draw.rectangle([0, 0, 1000, 40], fill='darkblue')
    draw.text((20, 12), "OneNote RAG System - Performance Monitoring Dashboard", fill='white', font=font_title)
    
    # Navigation
    draw.rectangle([0, 40, 1000, 80], fill='lightblue')
    nav_items = ["Overview", "Ingestion", "Search Performance", "Attachments", "Errors"]
    x_pos = 20
    for item in nav_items:
        draw.text((x_pos, 55), item, fill='darkblue', font=font_normal)
        x_pos += len(item) * 10 + 20
    
    # Main dashboard area
    draw.rectangle([10, 90, 990, 690], outline='gray', width=1, fill='whitesmoke')
    
    # Metrics cards
    cards = [
        ("Total Notebooks", "1,247", 'lightgreen', 20, 110),
        ("Processed Pages", "18,392", 'lightblue', 220, 110),
        ("Attachments Processed", "4,573", 'lightyellow', 420, 110),
        ("Search Queries (24h)", "2,891", 'lightcoral', 620, 110),
        ("Avg Response Time", "1.34s", 'lightpink', 820, 110)
    ]
    
    for title, value, color, x, y in cards:
        draw.rectangle([x, y, x + 180, y + 80], outline='black', width=1, fill=color)
        draw.text((x + 10, y + 10), title, fill='black', font=font_normal)
        draw.text((x + 10, y + 35), value, fill='darkblue', font=font_title)
    
    # Processing stats chart area
    draw.rectangle([20, 210, 480, 450], outline='black', width=2, fill='white')
    draw.text((30, 220), "Attachment Processing by File Type", fill='black', font=font_normal)
    
    # Simulate bar chart
    chart_data = [("PDF", 180, 'red'), ("PNG", 120, 'blue'), ("DOCX", 90, 'green'), ("XLSX", 60, 'orange')]
    base_x, base_y = 50, 420
    
    for i, (label, height, color) in enumerate(chart_data):
        x = base_x + i * 80
        draw.rectangle([x, base_y - height, x + 50, base_y], fill=color, outline='black')
        draw.text((x + 5, base_y + 10), label, fill='black', font=font_small)
        draw.text((x + 15, base_y - height - 15), str(height), fill='black', font=font_small)
    
    # Performance timeline
    draw.rectangle([500, 210, 970, 450], outline='black', width=2, fill='white')
    draw.text((510, 220), "Response Time Trend (Last 7 Days)", fill='black', font=font_normal)
    
    # Simulate line chart
    import math
    points = []
    for i in range(50):
        x = 520 + i * 8
        y = 350 - int(30 * math.sin(i * 0.3) + 30 * math.cos(i * 0.2))
        points.append((x, y))
    
    for i in range(len(points) - 1):
        draw.line([points[i], points[i + 1]], fill='blue', width=2)
    
    # Recent activity log
    draw.rectangle([20, 470, 970, 680], outline='black', width=2, fill='white')
    draw.text((30, 480), "Recent Processing Activity", fill='black', font=font_normal)
    
    log_entries = [
        "2026-02-08 16:30:15 | INFO | Successfully processed notebook 'AI Research - Q1 2026'",
        "2026-02-08 16:29:43 | INFO | Attachment processing: research_paper.pdf (2.3MB) → 847 chunks",
        "2026-02-08 16:29:12 | INFO | OCR extraction: architecture_diagram.png → 'RAG ARCHITECTURE OVERVIEW'",
        "2026-02-08 16:28:55 | INFO | Table detected in performance_analysis.pdf → 3 tables, 97.2% confidence",
        "2026-02-08 16:28:31 | SUCCESS | Ingestion batch completed: 15 attachments in 2m 14s",
        "2026-02-08 16:27:18 | INFO | Document Intelligence analysis: security_guide.pdf → 2,847 characters",
        "2026-02-08 16:26:42 | INFO | Search query processed: 'vector database performance' → 5 results in 1.2s",
        "2026-02-08 16:26:01 | INFO | Hybrid search enabled for query: 'ai framework benchmarks'",
        "2026-02-08 16:25:33 | SUCCESS | Embeddings generated: 1,247 chunks in 45.3s",
        "2026-02-08 16:24:17 | INFO | Graph API sync: Retrieved 42 pages from 'Technical Documentation'"
    ]
    
    y_pos = 500
    for entry in log_entries[:8]:  # Show only first 8 entries
        color = 'green' if 'SUCCESS' in entry else ('orange' if 'INFO' in entry else 'black')
        draw.text((30, y_pos), entry[:95] + "..." if len(entry) > 95 else entry, fill=color, font=font_small)
        y_pos += 18
    
    img.save("notebook_attachments/testing_dashboard_screenshot.png")

def create_csv_file():
    """Create benchmark results CSV file.""" 
    data = [
        ['Framework', 'Query_Type', 'Response_Time_ms', 'Accuracy_Percent', 'Cost_Per_Query', 'Memory_Usage_MB'],
        ['Azure AI Search', 'Semantic', 1200, 87, 0.003, 450],
        ['Azure AI Search', 'Hybrid', 1100, 89, 0.0035, 480],
        ['Azure AI Search', 'Keyword', 800, 85, 0.002, 420],
        ['Pinecone', 'Semantic', 1500, 85, 0.005, 520],
        ['Pinecone', 'Hybrid', 1400, 87, 0.0055, 550],
        ['ChromaDB', 'Semantic', 2100, 82, 0.002, 380],
        ['ChromaDB', 'Hybrid', 2000, 84, 0.0025, 410],
        ['Weaviate', 'Semantic', 1800, 84, 0.004, 460],
        ['Weaviate', 'Hybrid', 1700, 86, 0.0045, 490],
    ]
    
    with open('notebook_attachments/benchmark_results.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerows(data)
    
    print("✅ Created CSV file")

def create_excel_file():
    """Create benchmark results Excel file with multiple sheets."""
    try:
        import pandas as pd
        
        # Main benchmark data
        benchmark_data = {
            'Framework': ['Azure AI Search', 'Azure AI Search', 'Azure AI Search', 'Pinecone', 'Pinecone', 'ChromaDB', 'ChromaDB', 'Weaviate', 'Weaviate'],
            'Query_Type': ['Semantic', 'Hybrid', 'Keyword', 'Semantic', 'Hybrid', 'Semantic', 'Hybrid', 'Semantic', 'Hybrid'],
            'Response_Time_ms': [1200, 1100, 800, 1500, 1400, 2100, 2000, 1800, 1700],
            'Accuracy_Percent': [87, 89, 85, 85, 87, 82, 84, 84, 86],
            'Cost_Per_Query': [0.003, 0.0035, 0.002, 0.005, 0.0055, 0.002, 0.0025, 0.004, 0.0045],
            'Memory_Usage_MB': [450, 480, 420, 520, 550, 380, 410, 460, 490]
        }
        
        # Processing statistics
        processing_stats = {
            'File_Type': ['PDF', 'PNG', 'JPEG', 'DOCX', 'XLSX', 'TXT'],
            'Files_Processed': [847, 423, 356, 189, 134, 89],
            'Success_Rate': [95.2, 92.8, 94.1, 97.3, 91.7, 98.1],
            'Avg_Processing_Time_sec': [3.4, 2.1, 2.3, 4.2, 5.1, 1.8],
            'Total_Size_MB': [2847.3, 891.2, 743.5, 456.7, 289.1, 12.3]
        }
        
        # Performance over time
        import datetime
        dates = [datetime.date(2026, 2, i) for i in range(1, 8)]
        performance_timeline = {
            'Date': dates,
            'Avg_Response_Time': [1.45, 1.38, 1.32, 1.41, 1.29, 1.34, 1.27],
            'Query_Count': [2341, 2456, 2678, 2234, 2891, 2567, 2123],
            'Error_Rate': [0.8, 0.6, 0.4, 0.9, 0.3, 0.5, 0.2],
            'Attachments_Processed': [156, 178, 203, 145, 234, 189, 167]
        }
        
        # Create Excel file with multiple sheets
        with pd.ExcelWriter('notebook_attachments/benchmark_results.xlsx', engine='openpyxl') as writer:
            pd.DataFrame(benchmark_data).to_excel(writer, sheet_name='Framework_Benchmarks', index=False)
            pd.DataFrame(processing_stats).to_excel(writer, sheet_name='Processing_Stats', index=False)
            pd.DataFrame(performance_timeline).to_excel(writer, sheet_name='Performance_Timeline', index=False)
        
        print("✅ Created Excel file")
        
    except ImportError:
        # Fallback: create a CSV if pandas is not available
        print("⚠️ pandas not available, creating CSV instead of Excel")
        create_csv_file()
    except Exception as e:
        print(f"⚠️ Error creating Excel file: {e}, creating CSV instead")
        create_csv_file()

def main():
    """Generate all attachment files."""
    print("🔧 Creating realistic attachment files for OneNote testing...")
    
    # Create directory if it doesn't exist
    os.makedirs('notebook_attachments', exist_ok=True)
    
    # Remove old invalid files
    old_files = [
        'notebook_attachments/AI_Framework_Benchmark_2026.pdf',
        'notebook_attachments/Vector_DB_Performance_Analysis.pdf', 
        'notebook_attachments/LLM_Security_Guidelines.pdf',
        'notebook_attachments/Performance_Optimization_Guide.pdf',
        'notebook_attachments/test_results_summary.pdf',
        'notebook_attachments/Attention_Is_All_You_Need_2023_Update.pdf',
        'notebook_attachments/RAG_Performance_Optimization_Strategies.pdf',
        'notebook_attachments/Multi_Modal_Embeddings_Comparative_Study.pdf',
        'notebook_attachments/Document_AI_Layout_Understanding.pdf',
        'notebook_attachments/Hybrid_Search_Methods_Survey.pdf',
        'notebook_attachments/rag_architecture_overview.png',
        'notebook_attachments/document_processing_flow.png',
        'notebook_attachments/query_execution_diagram.png',
        'notebook_attachments/deployment_architecture.png',
        'notebook_attachments/pdf_processing_example.png',
        'notebook_attachments/image_ocr_demo.png',
        'notebook_attachments/table_extraction_sample.png',
        'notebook_attachments/testing_dashboard_screenshot.png',
        'notebook_attachments/benchmark_results.csv',
        'notebook_attachments/benchmark_results.xlsx'
    ]
    
    for file_path in old_files:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"🗑️ Removed old file: {file_path}")
    
    # Generate new files
    create_pdf_files()
    create_image_files() 
    create_csv_file()
    create_excel_file()
    
    print("\n✅ Successfully created all attachment files!")
    print("\n📁 Created files:")
    for file_name in os.listdir('notebook_attachments'):
        file_path = os.path.join('notebook_attachments', file_name)
        size_kb = os.path.getsize(file_path) / 1024
        print(f"   📄 {file_name} ({size_kb:.1f} KB)")
    
    print(f"\n🚀 You can now manually attach these files to your OneNote pages!")
    print(f"   Location: {os.path.abspath('notebook_attachments')}")

if __name__ == "__main__":
    main()