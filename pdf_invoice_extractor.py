#!/usr/bin/env python3
"""
PDF Invoice Data Extractor
Extracts items, seller info, dates, and detects GST invoices from PDF invoices.
"""

import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams


@dataclass
class Item:
    """Represents a line item in the invoice."""
    description: str = ""
    quantity: str = ""
    unit_price: str = ""
    amount: str = ""
    gst_rate: str = ""
    gst_amount: str = ""


@dataclass
class SellerInfo:
    """Represents seller/business information."""
    name: str = ""
    address: str = ""
    gstin: str = ""
    pan: str = ""
    email: str = ""
    phone: str = ""
    state: str = ""
    state_code: str = ""


@dataclass
class BuyerInfo:
    """Represents buyer/customer information."""
    name: str = ""
    address: str = ""
    gstin: str = ""
    state: str = ""


@dataclass
class InvoiceData:
    """Complete extracted invoice data."""
    is_gst_invoice: bool = False
    invoice_number: str = ""
    invoice_date: str = ""
    due_date: str = ""
    place_of_supply: str = ""
    seller: SellerInfo = field(default_factory=SellerInfo)
    buyer: BuyerInfo = field(default_factory=BuyerInfo)
    items: List[Item] = field(default_factory=list)
    totals: Dict[str, str] = field(default_factory=dict)
    raw_text: str = ""


class PDFInvoiceExtractor:
    """
    Extracts structured data from PDF invoices.
    Detects GST invoices and extracts relevant information.
    """
    
    # GST Invoice patterns
    GSTIN_PATTERN = r'\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}\d{1}[Z]{1}[A-Z\d]{1}\b'
    PAN_PATTERN = r'\b[A-Z]{5}\d{4}[A-Z]{1}\b'
    
    # Date patterns (common Indian formats)
    DATE_PATTERNS = [
        r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b',  # DD/MM/YYYY or DD-MM-YYYY
        r'\b(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{2,4})\b',  # DD Month YYYY
        r'\b([A-Za-z]{3,9}\s+\d{1,2},?\s+\d{2,4})\b',  # Month DD, YYYY
    ]
    
    # Invoice number patterns
    INVOICE_NUMBER_PATTERNS = [
        r'(?:Invoice\s*#?|Invoice\s+No\.?|Inv\s+No\.?)\s*[:\-]?\s*([A-Z0-9\-/]+)',
        r'(?:Tax\s+Invoice)\s*[:\-]?\s*([A-Z0-9\-/]+)',
        r'\b(Inv-\d+)\b',
    ]
    
    def __init__(self):
        self.laparams = LAParams(
            line_margin=0.5,
            word_margin=0.1,
            char_margin=2.0,
            boxes_flow=0.5
        )
    
    def extract_text(self, pdf_path: str) -> str:
        """Extract text from PDF file."""
        try:
            text = extract_text(pdf_path, laparams=self.laparams)
            return text.strip() if text else ""
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")
    
    def detect_gst_invoice(self, text: str) -> bool:
        """
        Detect if the invoice is a GST invoice.
        Looks for GSTIN, GST mentions, and tax invoice keywords.
        """
        text_upper = text.upper()
        
        # Check for GSTIN pattern
        if re.search(self.GSTIN_PATTERN, text_upper):
            return True
        
        # Check for GST-related keywords
        gst_keywords = [
            'GST INVOICE', 'TAX INVOICE', 'GSTIN', 'GST NO',
            'GOODS AND SERVICES TAX', 'CGST', 'SGST', 'IGST',
            'GST RATE', 'HSN', 'SAC'
        ]
        
        for keyword in gst_keywords:
            if keyword in text_upper:
                return True
        
        return False
    
    def extract_gstin(self, text: str) -> str:
        """Extract GST Identification Number."""
        match = re.search(self.GSTIN_PATTERN, text.upper())
        return match.group(0) if match else ""
    
    def extract_pan(self, text: str) -> str:
        """Extract Permanent Account Number."""
        match = re.search(self.PAN_PATTERN, text.upper())
        return match.group(0) if match else ""
    
    def extract_dates(self, text: str) -> Dict[str, str]:
        """Extract various dates from the invoice."""
        dates = {}
        
        for pattern in self.DATE_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Try to identify which date is which based on context
                for match in matches:
                    date_str = match if isinstance(match, str) else match[0]
                    
                    # Look for context around the date
                    pos = text.find(date_str)
                    context_start = max(0, pos - 50)
                    context_end = min(len(text), pos + 50)
                    context = text[context_start:context_end].upper()
                    
                    if 'INVOICE' in context and 'DATE' not in dates:
                        dates['invoice_date'] = date_str
                    elif 'DUE' in context or 'PAYMENT' in context:
                        dates['due_date'] = date_str
                    elif 'DATE' not in dates:
                        dates['invoice_date'] = date_str
        
        return dates
    
    def extract_invoice_number(self, text: str) -> str:
        """Extract invoice number."""
        for pattern in self.INVOICE_NUMBER_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Fallback: look for common invoice number formats
        match = re.search(r'\b(INV[A-Z0-9\-/]+)\b', text, re.IGNORECASE)
        return match.group(1) if match else ""
    
    def extract_seller_info(self, text: str) -> SellerInfo:
        """Extract seller/business information."""
        seller = SellerInfo()
        lines = text.split('\n')
        
        # Extract GSTIN
        seller.gstin = self.extract_gstin(text)
        
        # Extract PAN
        seller.pan = self.extract_pan(text)
        
        # Look for seller section
        in_seller_section = False
        for i, line in enumerate(lines):
            line_upper = line.upper()
            
            # Detect seller section headers
            if any(keyword in line_upper for keyword in [
                'SELLER', 'SUPPLIER', 'FROM', 'ISSUED BY', 'BUSINESS DETAILS'
            ]):
                in_seller_section = True
                continue
            
            # Exit seller section when we hit buyer section
            if any(keyword in line_upper for keyword in [
                'BUYER', 'CUSTOMER', 'BILL TO', 'SHIP TO'
            ]) and in_seller_section:
                break
            
            if in_seller_section:
                # Extract email
                email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', line)
                if email_match and not seller.email:
                    seller.email = email_match.group(0)
                
                # Extract phone
                phone_match = re.search(r'\b[\+]?[(]?[0-9]{1,4}[)]?[-\s\./0-9]*\b', line)
                if phone_match and not seller.phone and len(phone_match.group(0)) >= 10:
                    seller.phone = phone_match.group(0)
                
                # Extract name (usually first non-empty line in section)
                if not seller.name and line.strip() and len(line.strip()) > 3:
                    if not re.search(r'\d', line):  # Skip lines with numbers (addresses)
                        seller.name = line.strip()
                
                # Build address
                if re.search(r'\d', line) or any(word in line_upper for word in ['STREET', 'ROAD', 'AREA', 'CITY', 'STATE', 'PIN']):
                    seller.address += line.strip() + "\n"
        
        seller.address = seller.address.strip()
        
        # Extract state code from GSTIN (first 2 digits)
        if seller.gstin:
            seller.state_code = seller.gstin[:2]
            state_codes = {
                '01': 'Jammu and Kashmir', '02': 'Himachal Pradesh', '03': 'Punjab',
                '04': 'Chandigarh', '05': 'Uttarakhand', '06': 'Haryana',
                '07': 'Delhi', '08': 'Rajasthan', '09': 'Uttar Pradesh',
                '10': 'Bihar', '11': 'Sikkim', '12': 'Arunachal Pradesh',
                '13': 'Nagaland', '14': 'Manipur', '15': 'Mizoram',
                '16': 'Tripura', '17': 'Meghalaya', '18': 'Assam',
                '19': 'West Bengal', '20': 'Jharkhand', '21': 'Odisha',
                '22': 'Chhattisgarh', '23': 'Madhya Pradesh', '24': 'Gujarat',
                '25': 'Daman and Diu', '26': 'Dadra and Nagar Haveli',
                '27': 'Maharashtra', '28': 'Andhra Pradesh', '29': 'Karnataka',
                '30': 'Goa', '31': 'Lakshadweep', '32': 'Kerala',
                '33': 'Tamil Nadu', '34': 'Puducherry', '35': 'Telangana',
                '36': 'Andhra Pradesh', '37': 'Andhra Pradesh', '38': 'Telangana'
            }
            seller.state = state_codes.get(seller.state_code, '')
        
        return seller
    
    def extract_buyer_info(self, text: str) -> BuyerInfo:
        """Extract buyer/customer information."""
        buyer = BuyerInfo()
        lines = text.split('\n')
        
        in_buyer_section = False
        for i, line in enumerate(lines):
            line_upper = line.upper()
            
            # Detect buyer section headers
            if any(keyword in line_upper for keyword in [
                'BUYER', 'CUSTOMER', 'BILL TO', 'SHIP TO', 'CONSIGNED TO'
            ]):
                in_buyer_section = True
                continue
            
            # Exit buyer section
            if in_buyer_section and any(keyword in line_upper for keyword in [
                'ITEM', 'PRODUCT', 'DESCRIPTION', 'QTY', 'AMOUNT', 'TOTAL'
            ]):
                break
            
            if in_buyer_section:
                # Extract GSTIN
                if not buyer.gstin:
                    gstin_match = re.search(self.GSTIN_PATTERN, line.upper())
                    if gstin_match:
                        buyer.gstin = gstin_match.group(0)
                
                # Extract name
                if not buyer.name and line.strip() and len(line.strip()) > 3:
                    if not re.search(r'\d', line):
                        buyer.name = line.strip()
                
                # Build address
                if re.search(r'\d', line) or any(word in line_upper for word in ['STREET', 'ROAD', 'AREA', 'CITY', 'STATE', 'PIN']):
                    buyer.address += line.strip() + "\n"
        
        buyer.address = buyer.address.strip()
        
        # Extract state from GSTIN
        if buyer.gstin:
            state_codes = {
                '01': 'Jammu and Kashmir', '02': 'Himachal Pradesh', '03': 'Punjab',
                '07': 'Delhi', '24': 'Gujarat', '27': 'Maharashtra',
                '29': 'Karnataka', '32': 'Kerala', '33': 'Tamil Nadu',
                '36': 'Andhra Pradesh', '38': 'Telangana'
            }
            buyer.state = state_codes.get(buyer.gstin[:2], '')
        
        return buyer
    
    def extract_items(self, text: str) -> List[Item]:
        """Extract line items from the invoice."""
        items = []
        lines = text.split('\n')
        
        # Common column headers for item tables
        headers = ['SL', 'NO', 'DESCRIPTION', 'ITEM', 'PRODUCT', 'QTY', 'QUANTITY', 
                   'RATE', 'PRICE', 'AMOUNT', 'TOTAL', 'GST', 'TAX', 'HSN', 'SAC']
        
        in_items_section = False
        current_item = None
        
        for line in lines:
            line_upper = line.upper().strip()
            
            # Detect items section
            if any(header in line_upper for header in headers):
                in_items_section = True
                continue
            
            # Exit items section
            if in_items_section and any(keyword in line_upper for keyword in [
                'TOTAL AMOUNT', 'GRAND TOTAL', 'SUBTOTAL', 'TAXABLE VALUE',
                'INVOICE TOTAL', 'AMOUNT IN WORDS'
            ]):
                if current_item:
                    items.append(current_item)
                break
            
            if in_items_section and line.strip():
                # Try to parse item line
                # This is a simplified parser - may need adjustment for specific formats
                parts = re.split(r'\s{2,}|\t', line.strip())
                
                if len(parts) >= 2:
                    if current_item is None:
                        current_item = Item()
                    
                    # Heuristic: first part is usually description
                    if not current_item.description:
                        current_item.description = parts[0].strip()
                    
                    # Look for numbers in the line
                    numbers = re.findall(r'[\d,]+\.?\d*', line)
                    if numbers:
                        # Last number is usually amount
                        if not current_item.amount:
                            current_item.amount = numbers[-1]
                        
                        # Second last might be unit price
                        if len(numbers) > 1 and not current_item.unit_price:
                            current_item.unit_price = numbers[-2]
                        
                        # First number might be quantity
                        if len(numbers) > 2 and not current_item.quantity:
                            current_item.quantity = numbers[0]
                    
                    # Look for GST rate
                    gst_match = re.search(r'(\d+(?:\.\d+)?)\s*%\s*GST', line, re.IGNORECASE)
                    if gst_match:
                        current_item.gst_rate = gst_match.group(1)
                    
                    # If line has significant content, save current item and start new one
                    if current_item.description and current_item.amount:
                        items.append(current_item)
                        current_item = Item()
        
        return items
    
    def extract_totals(self, text: str) -> Dict[str, str]:
        """Extract total amounts from the invoice."""
        totals = {}
        
        # Common total labels
        total_patterns = [
            (r'(?:SUBTOTAL|SUB-TOTAL)\s*[:\-]?\s*([\d,]+\.?\d*)', 'subtotal'),
            (r'(?:TAXABLE\s+VALUE)\s*[:\-]?\s*([\d,]+\.?\d*)', 'taxable_value'),
            (r'(?:CGST)\s*[:\-]?\s*([\d,]+\.?\d*)', 'cgst'),
            (r'(?:SGST)\s*[:\-]?\s*([\d,]+\.?\d*)', 'sgst'),
            (r'(?:IGST)\s*[:\-]?\s*([\d,]+\.?\d*)', 'igst'),
            (r'(?:TOTAL\s+TAX)\s*[:\-]?\s*([\d,]+\.?\d*)', 'total_tax'),
            (r'(?:GRAND\s+TOTAL|TOTAL\s+AMOUNT|INVOICE\s+VALUE)\s*[:\-]?\s*([\d,]+\.?\d*)', 'grand_total'),
        ]
        
        for pattern, key in total_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                totals[key] = match.group(1)
        
        return totals
    
    def extract(self, pdf_path: str) -> InvoiceData:
        """
        Main method to extract all data from a PDF invoice.
        
        Args:
            pdf_path: Path to the PDF invoice file
            
        Returns:
            InvoiceData object with all extracted information
        """
        # Extract text
        text = self.extract_text(pdf_path)
        
        if not text:
            raise ValueError("No text could be extracted from the PDF")
        
        # Create invoice data object
        invoice = InvoiceData()
        invoice.raw_text = text
        
        # Detect if GST invoice
        invoice.is_gst_invoice = self.detect_gst_invoice(text)
        
        # Extract basic info
        invoice.invoice_number = self.extract_invoice_number(text)
        
        # Extract dates
        dates = self.extract_dates(text)
        invoice.invoice_date = dates.get('invoice_date', '')
        invoice.due_date = dates.get('due_date', '')
        
        # Extract parties
        invoice.seller = self.extract_seller_info(text)
        invoice.buyer = self.extract_buyer_info(text)
        
        # Extract items
        invoice.items = self.extract_items(text)
        
        # Extract totals
        invoice.totals = self.extract_totals(text)
        
        return invoice
    
    def to_dict(self, invoice: InvoiceData) -> Dict[str, Any]:
        """Convert InvoiceData to dictionary for JSON serialization."""
        return {
            'is_gst_invoice': invoice.is_gst_invoice,
            'invoice_number': invoice.invoice_number,
            'invoice_date': invoice.invoice_date,
            'due_date': invoice.due_date,
            'place_of_supply': invoice.place_of_supply,
            'seller': {
                'name': invoice.seller.name,
                'address': invoice.seller.address,
                'gstin': invoice.seller.gstin,
                'pan': invoice.seller.pan,
                'email': invoice.seller.email,
                'phone': invoice.seller.phone,
                'state': invoice.seller.state,
                'state_code': invoice.seller.state_code
            },
            'buyer': {
                'name': invoice.buyer.name,
                'address': invoice.buyer.address,
                'gstin': invoice.buyer.gstin,
                'state': invoice.buyer.state
            },
            'items': [
                {
                    'description': item.description,
                    'quantity': item.quantity,
                    'unit_price': item.unit_price,
                    'amount': item.amount,
                    'gst_rate': item.gst_rate,
                    'gst_amount': item.gst_amount
                }
                for item in invoice.items
            ],
            'totals': invoice.totals
        }


def main():
    """Example usage of the PDF Invoice Extractor."""
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("Usage: python pdf_invoice_extractor.py <path_to_pdf>")
        print("\nThis tool extracts data from PDF invoices including:")
        print("  - GST invoice detection")
        print("  - Seller and buyer information")
        print("  - Invoice dates and numbers")
        print("  - Line items")
        print("  - Totals and tax breakdown")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    try:
        extractor = PDFInvoiceExtractor()
        invoice = extractor.extract(pdf_path)
        
        # Print results
        print("=" * 60)
        print("PDF INVOICE EXTRACTION RESULTS")
        print("=" * 60)
        
        print(f"\nGST Invoice: {'YES' if invoice.is_gst_invoice else 'NO'}")
        print(f"Invoice Number: {invoice.invoice_number}")
        print(f"Invoice Date: {invoice.invoice_date}")
        print(f"Due Date: {invoice.due_date}")
        
        print("\n--- SELLER INFORMATION ---")
        print(f"Name: {invoice.seller.name}")
        print(f"GSTIN: {invoice.seller.gstin}")
        print(f"PAN: {invoice.seller.pan}")
        print(f"State: {invoice.seller.state} ({invoice.seller.state_code})")
        print(f"Email: {invoice.seller.email}")
        print(f"Phone: {invoice.seller.phone}")
        print(f"Address:\n{invoice.seller.address}")
        
        print("\n--- BUYER INFORMATION ---")
        print(f"Name: {invoice.buyer.name}")
        print(f"GSTIN: {invoice.buyer.gstin}")
        print(f"State: {invoice.buyer.state}")
        print(f"Address:\n{invoice.buyer.address}")
        
        print("\n--- ITEMS ---")
        if invoice.items:
            for i, item in enumerate(invoice.items, 1):
                print(f"{i}. {item.description}")
                print(f"   Qty: {item.quantity}, Rate: {item.unit_price}, Amount: {item.amount}")
                if item.gst_rate:
                    print(f"   GST: {item.gst_rate}%")
        else:
            print("No items extracted")
        
        print("\n--- TOTALS ---")
        for key, value in invoice.totals.items():
            print(f"{key.replace('_', ' ').title()}: {value}")
        
        # Save as JSON
        output_file = pdf_path.replace('.pdf', '_extracted.json')
        with open(output_file, 'w') as f:
            json.dump(extractor.to_dict(invoice), f, indent=2)
        print(f"\n✓ Data saved to: {output_file}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
