from typing import Dict, List
from .database import InvoiceDatabase

def validate_invoice(invoice_data: Dict, matched_po: Dict, db: InvoiceDatabase) -> Dict:
    """
    Validate invoice against PO and business rules
    
    Returns:
        {
            'is_valid': bool,
            'issues': List[str],
            'warnings': List[str],
            'checks_passed': List[str]
        }
    """
    
    issues = []
    warnings = []
    checks_passed = []
    
    # CHECK 1: PO Match
    if not matched_po or not matched_po.get('po_data'):
        issues.append("No matching PO found")
        return {
            'is_valid': False,
            'issues': issues,
            'warnings': warnings,
            'checks_passed': checks_passed
        }
    
    po = matched_po['po_data']
    checks_passed.append("✅ PO match found")
    
    # CHECK 2: PO Status
    if po['Status'] == 'Closed':
        issues.append(f"PO {po['PO Number']} is closed")
    elif po['Status'] == 'Pending Approval':
        warnings.append(f"PO {po['PO Number']} is pending approval")
    else:
        checks_passed.append(f"✅ PO status: {po['Status']}")
    
    # CHECK 3: Vendor Match
    invoice_vendor = invoice_data['vendor_name'].lower()
    po_vendor = po['Vendor Name'].lower()
    
    if invoice_vendor not in po_vendor and po_vendor not in invoice_vendor:
        issues.append(f"Vendor mismatch: Invoice '{invoice_data['vendor_name']}' vs PO '{po['Vendor Name']}'")
    else:
        checks_passed.append("✅ Vendor match")
    
    # CHECK 4: Amount Validation
    invoice_amount = invoice_data['total_amount']
    po_amount = po['Approved Amount']
    
    amount_diff = invoice_amount - po_amount
    amount_diff_percent = abs(amount_diff) / po_amount if po_amount > 0 else 1.0
    
    TOLERANCE = 0.05  # 5% tolerance
    
    if amount_diff_percent <= TOLERANCE:
        checks_passed.append(f"✅ Amount match: ${invoice_amount:.2f} vs ${po_amount:.2f} (within {TOLERANCE:.0%} tolerance)")
    elif amount_diff > 0:
        # Invoice is higher than PO
        if amount_diff_percent <= 0.10:  # Up to 10% can be flagged, not rejected
            warnings.append(f"Amount exceeds PO by ${amount_diff:.2f} ({amount_diff_percent:.1%}). PO: ${po_amount:.2f}, Invoice: ${invoice_amount:.2f}")
        else:
            issues.append(f"Amount exceeds PO by ${amount_diff:.2f} ({amount_diff_percent:.1%}). PO: ${po_amount:.2f}, Invoice: ${invoice_amount:.2f}")
    else:
        # Invoice is lower than PO (partial invoice?)
        warnings.append(f"Invoice amount ${invoice_amount:.2f} is less than PO ${po_amount:.2f}. Possible partial delivery.")
    
    # CHECK 5: Duplicate Detection
    duplicate = db.check_duplicate_invoice(
        invoice_data['invoice_number'],
        invoice_data['vendor_name']
    )
    
    if duplicate:
        issues.append(f"⚠️ DUPLICATE: Invoice {invoice_data['invoice_number']} was already paid on {duplicate.get('Payment Date')}")
    else:
        checks_passed.append("✅ No duplicate found")
    
    # CHECK 6: Required Fields
    required_fields = ['invoice_number', 'vendor_name', 'total_amount', 'invoice_date']
    missing_fields = [f for f in required_fields if not invoice_data.get(f)]
    
    if missing_fields:
        issues.append(f"Missing required fields: {', '.join(missing_fields)}")
    else:
        checks_passed.append("✅ All required fields present")
    
    # CHECK 7: PO Cumulative Amount (for split invoices)
    payment_history = db.get_po_payment_history(po['PO Number'])
    total_paid = sum(p['Invoice Amount'] for p in payment_history)
    remaining = po_amount - total_paid
    
    if invoice_amount > remaining:
        issues.append(f"Invoice ${invoice_amount:.2f} exceeds remaining PO balance ${remaining:.2f} (${total_paid:.2f} already paid)")
    elif total_paid > 0:
        warnings.append(f"Partial PO: ${total_paid:.2f} already paid. Remaining: ${remaining:.2f}")
    
    # Final validation
    is_valid = len(issues) == 0
    
    return {
        'is_valid': is_valid,
        'issues': issues,
        'warnings': warnings,
        'checks_passed': checks_passed,
        'po_details': {
            'po_number': po['PO Number'],
            'approved_amount': po_amount,
            'invoice_amount': invoice_amount,
            'amount_difference': amount_diff,
            'amount_difference_percent': amount_diff_percent
        }
    }


# Test
if __name__ == "__main__":
    from database import InvoiceDatabase
    from matcher import find_matching_po
    
    db = InvoiceDatabase("data/po_and_payment_database.xlsx")
    
    # Test invoice
    invoice = {
        'vendor_name': 'ACME CORPORATION',
        'invoice_number': 'INV-8473',
        'po_reference': 'PO-2847',
        'total_amount': 118.0,
        'invoice_date': '2026-03-15'
    }
    
    # Find PO
    matched_po = find_matching_po(invoice, db)
    
    # Validate
    validation = validate_invoice(invoice, matched_po, db)
    
    print(f"\n{'='*60}")
    print(f"VALIDATION RESULT: {'✅ VALID' if validation['is_valid'] else '❌ INVALID'}")
    print(f"{'='*60}")
    
    if validation['checks_passed']:
        print("\n✅ Checks Passed:")
        for check in validation['checks_passed']:
            print(f"   {check}")
    
    if validation['warnings']:
        print("\n⚠️  Warnings:")
        for warning in validation['warnings']:
            print(f"   {warning}")
    
    if validation['issues']:
        print("\n❌ Issues:")
        for issue in validation['issues']:
            print(f"   {issue}")