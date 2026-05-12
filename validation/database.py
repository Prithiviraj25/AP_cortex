import pandas as pd
from typing import Optional, List, Dict

class InvoiceDatabase:
    """Handles PO and Payment History database operations"""
    
    def __init__(self, excel_path: str):
        """Load Excel database"""
        self.excel_path = excel_path
        
        # Load both sheets
        self.po_df = pd.read_excel(excel_path, sheet_name='Purchase Orders')
        self.payment_df = pd.read_excel(excel_path, sheet_name='Payment History')
        
        print(f"✅ Loaded {len(self.po_df)} Purchase Orders")
        print(f"✅ Loaded {len(self.payment_df)} Payment History records")
    
    def get_po_by_number(self, po_number: str) -> Optional[Dict]:
        """Get PO by exact PO number"""
        result = self.po_df[self.po_df['PO Number'] == po_number]
        
        if result.empty:
            return None
        
        return result.iloc[0].to_dict()
    
    def search_po_by_vendor_and_amount(self, vendor_name: str, amount: float, tolerance: float = 0.1) -> List[Dict]:
        """Fuzzy search PO by vendor name and amount (for missing PO reference)"""
        # Normalize vendor name for comparison
        vendor_lower = vendor_name.lower()
        
        # Filter by vendor (fuzzy match)
        vendor_matches = self.po_df[
            self.po_df['Vendor Name'].str.lower().str.contains(vendor_lower, na=False)
        ]
        
        # Filter by amount (within tolerance)
        matches = []
        for _, po in vendor_matches.iterrows():
            po_amount = po['Approved Amount']
            amount_diff = abs(po_amount - amount)
            amount_diff_percent = amount_diff / po_amount if po_amount > 0 else 1.0
            
            if amount_diff_percent <= tolerance:
                po_dict = po.to_dict()
                po_dict['match_confidence'] = 1.0 - amount_diff_percent
                matches.append(po_dict)
        
        # Sort by confidence
        matches.sort(key=lambda x: x['match_confidence'], reverse=True)
        
        return matches
    
    def check_duplicate_invoice(self, invoice_number: str, vendor_name: str) -> Optional[Dict]:
        """Check if invoice was already paid"""
        # Check by invoice number
        result = self.payment_df[
            (self.payment_df['Invoice Number'] == invoice_number) |
            (self.payment_df['Vendor Name'].str.lower() == vendor_name.lower())
        ]
        
        if not result.empty:
            # Check if same invoice number
            exact_match = result[result['Invoice Number'] == invoice_number]
            if not exact_match.empty:
                return exact_match.iloc[0].to_dict()
        
        return None
    
    def get_po_payment_history(self, po_number: str) -> List[Dict]:
        """Get all payments made against a PO"""
        result = self.payment_df[self.payment_df['PO Number'] == po_number]
        return result.to_dict('records')


# Test
if __name__ == "__main__":
    db = InvoiceDatabase("po_and_payment_database.xlsx")
    
    # Test exact PO lookup
    po = db.get_po_by_number("PO-2847")
    print(f"\nPO-2847: {po}")
    
    # Test fuzzy search
    matches = db.search_po_by_vendor_and_amount("Acme", 118.0, tolerance=0.15)
    print(f"\nFuzzy matches: {matches}")
    
    # Test duplicate check
    duplicate = db.check_duplicate_invoice("INV-8473", "ACME CORPORATION")
    print(f"\nDuplicate check: {duplicate}")