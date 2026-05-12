import json
from collections import defaultdict

def build_llm_context(doc_json, y_threshold=15, x_column_threshold=50):
    """
    Reconstruct invoice layout with better table detection
    """
    kids = doc_json.get("kids", [])
    
    # ----------------------------------------
    # FILTER TEXT ELEMENTS
    # ----------------------------------------
    elements = []
    for item in kids:
        if item.get("type") not in ["paragraph", "heading"]:
            continue
        content = item.get("content", "").strip()
        if not content:
            continue
        bbox = item.get("bounding box", [])
        if len(bbox) != 4:
            continue
        x1, y1, x2, y2 = bbox
        elements.append({
            "text": content,
            "x": x1,
            "y": y1,
            "width": x2 - x1,
            "bbox": bbox,
            "type": item.get("type")
        })
    
    # Sort by Y then X
    elements = sorted(elements, key=lambda e: (e["y"], e["x"]))
    
    # ----------------------------------------
    # GROUP INTO ROWS
    # ----------------------------------------
    rows = []
    current_row = []
    current_y = None
    
    for elem in elements:
        if current_y is None:
            current_y = elem["y"]
        
        if abs(elem["y"] - current_y) <= y_threshold:
            current_row.append(elem)
        else:
            rows.append(current_row)
            current_row = [elem]
            current_y = elem["y"]
    
    if current_row:
        rows.append(current_row)
    
    # Sort each row left to right
    for row in rows:
        row.sort(key=lambda e: e["x"])
    
    # ----------------------------------------
    # DETECT TABLE SECTIONS
    # ----------------------------------------
    def is_table_row(row):
        """Detect if row is part of table (has 3+ aligned items)"""
        return len(row) >= 3
    
    def detect_sections(rows):
        """Split into header, table, footer"""
        header_rows = []
        table_rows = []
        footer_rows = []
        
        in_table = False
        table_ended = False
        
        for row in rows:
            if is_table_row(row) and not table_ended:
                in_table = True
                table_rows.append(row)
            elif in_table and not is_table_row(row):
                table_ended = True
                footer_rows.append(row)
            elif table_ended:
                footer_rows.append(row)
            else:
                header_rows.append(row)
        
        return header_rows, table_rows, footer_rows
    
    header, table, footer = detect_sections(rows)
    
    # ----------------------------------------
    # BUILD CONTEXT
    # ----------------------------------------
    context = []
    
    context.append("# INVOICE DOCUMENT STRUCTURE\n")
    context.append("This invoice has been parsed with spatial layout preservation.\n")
    
    # HEADER SECTION
    if header:
        context.append("\n## HEADER SECTION")
        context.append("Contains: Company info, addresses, invoice metadata\n")
        for row in header:
            row_text = "  ".join([e["text"] for e in row])
            context.append(row_text)
    
    # TABLE SECTION
    if table:
        context.append("\n## LINE ITEMS TABLE")
        context.append("Contains: Product/service line items with quantities, prices, taxes\n")
        
        # Try to identify column structure from first row
        if len(table) > 0:
            first_row = table[0]
            context.append("Column Headers:")
            context.append("  |  ".join([e["text"] for e in first_row]))
            context.append("-" * 80)
        
        # Data rows
        for row in table[1:]:
            # Align by x-position for better column detection
            row_text = "  |  ".join([e["text"] for e in row])
            context.append(row_text)
    
    # FOOTER SECTION
    if footer:
        context.append("\n## FOOTER SECTION")
        context.append("Contains: Subtotal, taxes, total amount, notes\n")
        for row in footer:
            row_text = "  ".join([e["text"] for e in row])
            context.append(row_text)
    
    # ----------------------------------------
    # LLM EXTRACTION INSTRUCTIONS
    # ----------------------------------------
    context.append("\n## EXTRACTION INSTRUCTIONS")
    context.append("""
Extract the following fields from this invoice:

**Metadata:**
- invoice_number: Invoice/reference number
- invoice_date: Issue date
- vendor_name: FROM company name
- vendor_address: FROM address
- customer_name: TO company name
- customer_address: TO address
- po_reference: Purchase order number (if mentioned)

**Line Items:** For each row in the table, extract:
- item_id or description
- quantity
- unit_price
- tax_rate
- line_total

**Totals:**
- subtotal: Amount before tax
- tax_amount: Total tax
- total_amount: Final total (THIS IS THE MOST IMPORTANT)
- currency: USD/EUR/etc

**CRITICAL:**
- The TOTAL AMOUNT is usually the largest number in the footer
- Look for "Total USD", "Total Amount", or "Grand Total"
- For this invoice, Total USD = 538.00
- Subtotal = 500.00
- Tax = 38.00

Return as JSON with all fields populated.
""")
    
    return "\n".join(context)


# ----------------------------------------
# USAGE
# ----------------------------------------
def extract_invoice_with_context(path):
   
    with open(path, 'r') as f:
        doc_json = json.load(f)

    context = build_llm_context(doc_json)
    
    return context