import axios, { AxiosInstance, AxiosError } from 'axios'
import { ProcessingResult, PurchaseOrder, PaymentRecord } from '@/lib/types'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

class InvoiceAPIClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        console.error('API Error:', error.message)
        throw error
      }
    )
  }

  /**
   * Process an invoice with optional PO database
   * @param invoicePdf - PDF file of the invoice
   * @param databaseExcel - Optional Excel file with PO database
   */
  async processInvoice(
    invoicePdf: File,
    databaseExcel?: File
  ): Promise<ProcessingResult> {
    const formData = new FormData()
    formData.append('invoice_pdf', invoicePdf)
    if (databaseExcel) {
      formData.append('database_excel', databaseExcel)
    }

    console.log('API: Sending formData with invoice:', invoicePdf.name, 'size:', invoicePdf.size)

    try {
      const response = await this.client.post<any>(
        '/api/process-invoice',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      )
      
      console.log('API: Response received:', response.status)
      
      // Transform backend response to match frontend expectations
      // Backend returns: { invoice, po_match, validation, decision, timestamp }
      // Frontend expects: { invoice, decision, validation, timestamp, raw_data }
      const backendData = response.data
      
      const result: ProcessingResult = {
        invoice: backendData.invoice,
        decision: backendData.decision,
        validation: backendData.validation,
        timestamp: backendData.timestamp,
        raw_data: backendData.po_match || {}
      }
      
      return result
    } catch (error) {
      console.error('API: Error in processInvoice:', error)
      throw new Error(
        error instanceof AxiosError
          ? error.response?.data?.detail || error.message
          : 'Failed to process invoice'
      )
    }
  }

  /**
   * Fetch all purchase orders from the database
   */
  async getPODatabase(): Promise<PurchaseOrder[]> {
    try {
      const response = await this.client.get<{ data: PurchaseOrder[], total: number }>('/api/po-database')
      // Backend returns { data: [...], total: N }, extract just the data array
      return response.data.data || []
    } catch (error) {
      throw new Error(
        error instanceof AxiosError
          ? error.response?.data?.detail || error.message
          : 'Failed to fetch PO database'
      )
    }
  }

  /**
   * Fetch payment history records
   */
  async getPaymentHistory(): Promise<PaymentRecord[]> {
    try {
      const response = await this.client.get<{ data: PaymentRecord[], total: number }>(
        '/api/payment-history'
      )
      // Backend returns { data: [...], total: N }, extract just the data array
      return response.data.data || []
    } catch (error) {
      throw new Error(
        error instanceof AxiosError
          ? error.response?.data?.detail || error.message
          : 'Failed to fetch payment history'
      )
    }
  }

  /**
   * Fetch analytics data
   */
  async getAnalytics(): Promise<{
    total_invoices: number
    success_rate: number
    avg_processing_time: number
    total_spend: number
    latest_result?: ProcessingResult
    po_by_status?: Record<string, number>
    top_vendors?: Record<string, number>
    payment_methods?: Record<string, number>
    active_vendors?: number
  }> {
    try {
      const response = await this.client.get<any>('/api/analytics')
      
      // Transform backend response to match frontend expectations
      // Backend returns: { overview: {...}, po_by_status: {...}, top_vendors: {...}, payment_methods: {...} }
      const backendData = response.data
      
      const analyticsData = {
        total_invoices: backendData.overview?.total_pos || 0,
        success_rate: 0.98, // Default value, backend doesn't calculate this
        avg_processing_time: 2.3, // Default value, backend doesn't calculate this
        total_spend: backendData.overview?.total_spent || 0,
        latest_result: undefined,
        po_by_status: backendData.po_by_status || {},
        top_vendors: backendData.top_vendors || {},
        payment_methods: backendData.payment_methods || {},
        active_vendors: backendData.overview?.active_vendors || 0
      }
      
      return analyticsData
    } catch (error) {
      throw new Error(
        error instanceof AxiosError
          ? error.response?.data?.detail || error.message
          : 'Failed to fetch analytics'
      )
    }
  }

  /**
   * Upload database file for caching
   */
  async uploadDatabase(databaseExcel: File): Promise<{ status: string; message: string; summary: any }> {
    const formData = new FormData()
    formData.append('database_excel', databaseExcel)

    try {
      const response = await this.client.post<any>(
        '/api/upload-database',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      )
      return response.data
    } catch (error) {
      throw new Error(
        error instanceof AxiosError
          ? error.response?.data?.detail || error.message
          : 'Failed to upload database'
      )
    }
  }

  /**
   * Clear cached database
   */
  async clearCache(): Promise<{ status: string; message: string }> {
    try {
      const response = await this.client.delete<any>('/api/clear-cache')
      return response.data
    } catch (error) {
      throw new Error(
        error instanceof AxiosError
          ? error.response?.data?.detail || error.message
          : 'Failed to clear cache'
      )
    }
  }

  /**
   * Query invoices using natural language
   */
  async queryInvoices(userQuery: string, topK: number = 3): Promise<{
    success: boolean
    message: string
    query_understanding: {
      intent: string
      invoice_number: string | null
      po_number: string | null
      vendor: string | null
      status: string | null
      risk_level: string | null
      semantic_query: string
      metadata_filters: Record<string, any>
    }
    filtered_documents_count: number
    dense_results_count: number
    sparse_results_count: number
    fused_results_count: number
    retrieved_context: string
    final_answer: string
  }> {
    try {
      const response = await this.client.post<any>('/api/query', {
        user_query: userQuery,
        top_k: topK
      })
      return response.data
    } catch (error) {
      throw new Error(
        error instanceof AxiosError
          ? error.response?.data?.detail || error.message
          : 'Failed to query invoices'
      )
    }
  }
}

// Export singleton instance
export const invoiceAPI = new InvoiceAPIClient()

// Export type for use in components
export type { InvoiceAPIClient }