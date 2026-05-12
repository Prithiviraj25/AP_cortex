export interface InvoiceData {
  invoice_number: string
  vendor_name: string
  total_amount: number
  invoice_date: string
  po_reference?: string
}

export interface ValidationResult {
  checks_passed: string[]
  warnings: string[]
  issues: string[]
}

export interface Decision {
  status: 'APPROVED' | 'FLAGGED_FOR_REVIEW' | 'REJECTED'
  reasoning: string
  action: string
  confidence: number
}

export interface ProcessingResult {
  invoice: InvoiceData
  decision: Decision
  validation: ValidationResult
  timestamp: string
  raw_data?: Record<string, any>
}

export interface PurchaseOrder {
  'PO Number': string
  'Vendor Name': string
  'Approved Amount': number
  'Status': string
  'Created Date': string
  'Requestor': string
}

export interface PaymentRecord {
  'Invoice Number': string
  'Vendor Name': string
  'Invoice Amount': number
  'Payment Date': string
  'Payment Method': string
}

export interface ProcessingStep {
  id: number
  title: string
  status: 'pending' | 'active' | 'complete'
}
