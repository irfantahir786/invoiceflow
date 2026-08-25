#!/usr/bin/env python3
"""
Test script to demonstrate the Invoice Table Extractor API.
Creates a sample PDF and tests the extraction endpoint.
"""

import requests
import tempfile
import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors


def create_sample_invoice_pdf(output_path: str):
    """Create a sample invoice PDF with tables for testing."""
    
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    
    # Title
    title = Paragraph("TAX INVOICE", styles['Heading1'])
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    # Seller Info
    seller_info = [
        ["Seller Name:", "ABC Enterprises Pvt Ltd"],
        ["GSTIN:", "27AABCU9603R1ZM"],
        ["Address:", "123 Business Street, Mumbai, Maharashtra - 400001"],
        ["Email:", "contact@abcenterprises.com"],
        ["Phone:", "+91-9876543210"]
    ]
    seller_table = Table(seller_info, colWidths=[100, 300])
    seller_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    elements.append(seller_table)
    elements.append(Spacer(1, 20))
    
    # Buyer Info
    buyer_info = [
        ["Buyer Name:", "XYZ Corporation"],
        ["GSTIN:", "29AADCS1234F1Z5"],
        ["Address:", "456 Tech Park, Bangalore, Karnataka - 560001"]
    ]
    buyer_table = Table(buyer_info, colWidths=[100, 300])
    buyer_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    elements.append(buyer_table)
    elements.append(Spacer(1, 20))
    
    # Invoice Details
    invoice_details = [
        ["Invoice Number:", "INV-2024-001"],
        ["Invoice Date:", "15/01/2024"],
        ["Place of Supply:", "Karnataka"]
    ]
    details_table = Table(invoice_details, colWidths=[100, 300])
    details_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    elements.append(details_table)
    elements.append(Spacer(1, 20))
    
    # Item Table
    item_data = [
        ["Item No", "Description", "HSN Code", "Qty", "Rate", "Amount"],
        ["1", "Laptop Computer", "8471", "2", "45000.00", "90000.00"],
        ["2", "Wireless Mouse", "8471", "5", "500.00", "2500.00"],
        ["3", "USB Cable", "8544", "10", "150.00", "1500.00"],
        ["4", "Monitor 24 inch", "8528", "2", "12000.00", "24000.00"],
        ["", "", "", "", "Subtotal:", "118000.00"]
    ]
    
    item_table = Table(item_data, colWidths=[50, 200, 80, 60, 100, 100])
    item_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))
    elements.append(item_table)
    elements.append(Spacer(1, 20))
    
    # Tax Summary Table
    tax_data = [
        ["Tax Type", "Taxable Value", "Rate", "Tax Amount"],
        ["CGST", "59000.00", "9%", "5310.00"],
        ["SGST", "59000.00", "9%", "5310.00"],
        ["", "", "Total Tax:", "10620.00"],
        ["", "", "Grand Total:", "128620.00"]
    ]
    
    tax_table = Table(tax_data, colWidths=[150, 120, 100, 120])
    tax_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))
    elements.append(tax_table)
    
    # Build PDF
    doc.build(elements)
    print(f"Sample invoice PDF created: {output_path}")


def test_api():
    """Test the FastAPI extraction endpoint."""
    
    # Create temporary PDF
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        pdf_path = tmp.name
    
    try:
        # Generate sample invoice
        create_sample_invoice_pdf(pdf_path)
        
        # Test API endpoint
        api_url = "http://localhost:8000/extract"
        
        print("\n" + "="*60)
        print("Testing Invoice Extraction API")
        print("="*60)
        
        with open(pdf_path, 'rb') as f:
            files = {'file': ('sample_invoice.pdf', f, 'application/pdf')}
            response = requests.post(api_url, files=files)
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"\n✓ API Response Status: {response.status_code}")
            print(f"\n📄 Filename: {result.get('filename')}")
            print(f"🏷️  Is GST Invoice: {result.get('is_gst_invoice')}")
            print(f"\n📊 Metadata:")
            print(f"   - Total Pages: {result['metadata']['total_pages']}")
            print(f"   - Total Tables: {result['metadata']['total_tables']}")
            print(f"   - Total Rows: {result['metadata']['total_rows']}")
            
            print(f"\n📋 Extracted Tables:")
            for table in result.get('tables', []):
                print(f"\n   Table {table['table_index'] + 1} (Page {table['page_number']}):")
                print(f"   - Headers: {table['headers']}")
                print(f"   - Rows: {table['row_count']}")
                print(f"   - Columns: {table['column_count']}")
                
                # Show first 2 rows as sample
                if table['rows']:
                    print("   Sample data:")
                    for i, row in enumerate(table['rows'][:2]):
                        print(f"     Row {i+1}: {row}")
            
            print("\n" + "="*60)
            print("✅ Test completed successfully!")
            print("="*60)
            
            # Save full JSON response
            import json
            with open('extraction_result.json', 'w') as f:
                json.dump(result, f, indent=2)
            print("\n💾 Full JSON response saved to: extraction_result.json")
            
        else:
            print(f"\n✗ API Error: {response.status_code}")
            print(f"Response: {response.text}")
    
    finally:
        # Cleanup
        if os.path.exists(pdf_path):
            os.unlink(pdf_path)


if __name__ == "__main__":
    test_api()
