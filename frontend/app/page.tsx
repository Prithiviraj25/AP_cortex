'use client'

import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { MetricCard } from '@/components/MetricCard'
import { StatusBadge } from '@/components/StatusBadge'
import { ProcessingPipeline } from '@/components/ProcessingPipeline'
import { ValidationResults } from '@/components/ValidationResults'
import { FileUp, Upload, Download, ChevronDown, AlertCircle, Loader2 } from 'lucide-react'
import { ProcessingResult, ProcessingStep } from '@/lib/types'
import { invoiceAPI } from '@/lib/api'
import { toast } from 'sonner'

export default function ProcessInvoice() {
  const [invoiceFile, setInvoiceFile] = useState<File | null>(null)
  const [databaseFile, setDatabaseFile] = useState<File | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [result, setResult] = useState<ProcessingResult | null>(null)
  const [steps, setSteps] = useState<ProcessingStep[]>([
    { id: 1, title: 'Extracting invoice data', status: 'pending' },
    { id: 2, title: 'Matching PO', status: 'pending' },
    { id: 3, title: 'Validating', status: 'pending' },
    { id: 4, title: 'Generating decision', status: 'pending' },
  ])
  const [backendError, setBackendError] = useState<string | null>(null)

  const onDropInvoice = useCallback((acceptedFiles: File[], rejectedFiles: any[]) => {
    if (rejectedFiles && rejectedFiles.length > 0) {
      toast.error('Please upload a PDF file only')
      return
    }
    if (acceptedFiles.length > 0) {
      setInvoiceFile(acceptedFiles[0])
      toast.success(`Invoice file uploaded: ${acceptedFiles[0].name}`)
    }
  }, [])

  const onDropDatabase = useCallback((acceptedFiles: File[], rejectedFiles: any[]) => {
    if (rejectedFiles && rejectedFiles.length > 0) {
      toast.error('Please upload an Excel file (.xlsx or .xls) only')
      return
    }
    if (acceptedFiles.length > 0) {
      setDatabaseFile(acceptedFiles[0])
      toast.success(`Database file uploaded: ${acceptedFiles[0].name}`)
    }
  }, [])

  const { getRootProps: getInvoiceRootProps, getInputProps: getInvoiceInputProps, isDragActive: isInvoiceDragActive } =
    useDropzone({ 
      onDrop: onDropInvoice, 
      noClick: false,
      multiple: false
    })

  const { getRootProps: getDatabaseRootProps, getInputProps: getDatabaseInputProps, isDragActive: isDatabaseDragActive } =
    useDropzone({ 
      onDrop: onDropDatabase, 
      noClick: false,
      multiple: false
    })

  const handleUploadDatabase = async () => {
    if (!databaseFile) {
      toast.error('Please select a database file first')
      return
    }

    console.log('Uploading database:', databaseFile.name)
    try {
      toast.loading('Uploading database...')
      await invoiceAPI.uploadDatabase(databaseFile)
      toast.dismiss()
      toast.success('Database uploaded and cached successfully!')
      setDatabaseFile(null)
    } catch (error) {
      toast.dismiss()
      const errorMsg = error instanceof Error ? error.message : 'Failed to upload database'
      console.error('Database upload error:', errorMsg)
      toast.error(errorMsg)
    }
  }

  const handleProcessInvoice = async () => {
    if (!invoiceFile) {
      toast.error('Please upload an invoice PDF')
      return
    }

    console.log('Processing invoice:', invoiceFile.name)

    setIsProcessing(true)
    setResult(null)
    setBackendError(null)
    setSteps(steps.map((s, idx) => ({
      ...s,
      status: idx === 0 ? 'active' : 'pending'
    })))

    try {
      console.log('Calling processInvoice API...')
      // Call the API - only pass databaseFile if it exists
      const processingResult = await invoiceAPI.processInvoice(invoiceFile, databaseFile || undefined)
      console.log('API response received:', processingResult)

      // Update steps to complete
      setSteps(prevSteps => prevSteps.map(s => ({ ...s, status: 'complete' })))

      setResult(processingResult)
      toast.success('Invoice processed successfully!')
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Error processing invoice'
      setBackendError(errorMessage)
      toast.error(errorMessage)
      setSteps(steps.map(s => ({ ...s, status: 'pending' })))
    } finally {
      setIsProcessing(false)
    }
  }

  const downloadJSON = () => {
    if (result) {
      const element = document.createElement('a')
      element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(JSON.stringify(result, null, 2)))
      element.setAttribute('download', `invoice-${result.invoice.invoice_number}.json`)
      element.style.display = 'none'
      document.body.appendChild(element)
      element.click()
      document.body.removeChild(element)
      toast.success('JSON downloaded successfully')
    }
  }

  const downloadCSV = () => {
    if (result) {
      let csv = 'Invoice Processing Result\n\n'
      csv += 'Invoice Information\n'
      csv += `Invoice Number,${result.invoice.invoice_number}\n`
      csv += `Vendor Name,${result.invoice.vendor_name}\n`
      csv += `Amount,${result.invoice.total_amount}\n`
      csv += `Date,${result.invoice.invoice_date}\n`
      csv += `PO Reference,${result.invoice.po_reference}\n\n`
      csv += 'Decision\n'
      csv += `Status,${result.decision.status}\n`
      csv += `Confidence,${result.decision.confidence}\n`
      
      const element = document.createElement('a')
      element.setAttribute('href', 'data:text/csv;charset=utf-8,' + encodeURIComponent(csv))
      element.setAttribute('download', `invoice-${result.invoice.invoice_number}.csv`)
      element.style.display = 'none'
      document.body.appendChild(element)
      element.click()
      document.body.removeChild(element)
      toast.success('CSV downloaded successfully')
    }
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-primary-800 to-primary-600">Process Invoice</h1>
        <p className="text-slate-600 mt-2">Upload and process your invoices with AI-powered matching and validation</p>
      </div>

      {/* Upload Section */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Invoice Upload */}
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader className="border-b border-slate-700">
            <CardTitle className="text-lg text-slate-100">Invoice Upload</CardTitle>
            <CardDescription className="text-slate-400">Upload a PDF invoice</CardDescription>
          </CardHeader>
          <CardContent className="pt-6">
            <div
              {...getInvoiceRootProps()}
              className={`
                border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all
                ${isInvoiceDragActive
                  ? 'border-primary-500 bg-primary-500/10'
                  : 'border-slate-600 bg-slate-700/50 hover:border-slate-500'
                }
              `}
            >
              <input 
                {...getInvoiceInputProps()} 
                accept=".pdf"
                onChange={(e) => {
                  if (e.target.files) {
                    onDropInvoice(Array.from(e.target.files), [])
                  }
                }}
              />
              <FileUp className="w-8 h-8 mx-auto text-slate-400 mb-2" />
              <p className="text-sm text-slate-300">Drag PDF here or click to select</p>
              <p className="text-xs text-slate-500 mt-1">PDF files only</p>
            </div>
            {invoiceFile && (
              <div className="mt-4 p-3 bg-success-500/10 border border-success-500/30 rounded-lg flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FileUp className="w-4 h-4 text-success-400" />
                  <span className="text-sm text-success-300">{invoiceFile.name}</span>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setInvoiceFile(null)}
                  className="text-slate-400 hover:text-slate-200"
                >
                  Remove
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Database Upload */}
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader className="border-b border-slate-700">
            <CardTitle className="text-lg text-slate-100">PO Database Upload</CardTitle>
            <CardDescription className="text-slate-400">Upload PO database (Excel)</CardDescription>
          </CardHeader>
          <CardContent className="pt-6">
            <div
              {...getDatabaseRootProps()}
              className={`
                border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all
                ${isDatabaseDragActive
                  ? 'border-primary-500 bg-primary-500/10'
                  : 'border-slate-600 bg-slate-700/50 hover:border-slate-500'
                }
              `}
            >
              <input 
                {...getDatabaseInputProps()} 
                accept=".xlsx,.xls"
                onChange={(e) => {
                  if (e.target.files) {
                    onDropDatabase(Array.from(e.target.files), [])
                  }
                }}
              />
              <Upload className="w-8 h-8 mx-auto text-slate-400 mb-2" />
              <p className="text-sm text-slate-300">Drag Excel here or click to select</p>
              <p className="text-xs text-slate-500 mt-1">XLSX or XLS files</p>
            </div>
            {databaseFile && (
              <div className="mt-4 p-3 bg-success-500/10 border border-success-500/30 rounded-lg flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Upload className="w-4 h-4 text-success-400" />
                  <span className="text-sm text-success-300">{databaseFile.name}</span>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setDatabaseFile(null)}
                  className="text-slate-400 hover:text-slate-200"
                >
                  Remove
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Database Upload Button */}
      {databaseFile && (
        <Button
          onClick={handleUploadDatabase}
          size="lg"
          className="w-full bg-success-500 hover:bg-success-600 text-white"
        >
          Upload Database
        </Button>
      )}

      {/* Information Note */}
      <Alert className="bg-primary-500/10 border-primary-500/30">
        <AlertCircle className="h-4 w-4 text-primary-400" />
        <AlertDescription className="text-slate-600">
          <strong>Optional:</strong> If you've already uploaded a PO database on this page, it will be cached and reused. You only need to upload a new database if you want to use different data.
        </AlertDescription>
      </Alert>

      {/* Process Button */}
      <Button
        onClick={handleProcessInvoice}
        disabled={!invoiceFile || isProcessing}
        size="lg"
        className="w-full btn-primary"
      >
        {isProcessing ? 'Processing...' : 'Process Invoice'}
      </Button>

      {/* Processing Status */}
      {isProcessing && (
        <Card className="bg-primary-500/10 border-primary-500/30">
          <CardContent className="p-6">
            <ProcessingPipeline steps={steps} />
          </CardContent>
        </Card>
      )}

      {/* Results Section */}
      {result && !isProcessing && (
        <div className="space-y-6">
          {/* Status */}
          <Card className="bg-gradient-to-br from-slate-800 to-slate-700 border-slate-700">
            <CardContent className="p-8 text-center space-y-4">
              <StatusBadge status={result.decision.status} />
              <p className="text-lg text-slate-300">{result.decision.reasoning}</p>
              <p className="text-4xl font-bold text-primary-400">
                {(result.decision.confidence * 100).toFixed(1)}%
              </p>
              <p className="text-sm text-slate-400">Confidence Score</p>
            </CardContent>
          </Card>

          {/* Metrics */}
          <div className="grid md:grid-cols-3 gap-4">
            <MetricCard
              label="Invoice Number"
              value={result.invoice.invoice_number}
            />
            <MetricCard
              label="Total Amount"
              value={`$${(result.invoice?.total_amount ?? 0).toLocaleString('en-US', {
                minimumFractionDigits: 2
              })}`}
            />
            <MetricCard
              label="Vendor"
              value={result.invoice.vendor_name}
            />
          </div>

          {/* Decision Info */}
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader className="border-b border-slate-700">
              <CardTitle className="text-base text-slate-100">Decision Details</CardTitle>
            </CardHeader>
            <CardContent className="pt-6 space-y-4">
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-slate-400 uppercase tracking-wide">Status</p>
                  <div className="mt-2">
                    <span className={`inline-block px-3 py-1 rounded-lg text-sm font-medium ${
                      result.decision.status === 'APPROVED' ? 'badge-success' :
                      result.decision.status === 'FLAGGED_FOR_REVIEW' ? 'badge-warning' :
                      'badge-danger'
                    }`}>
                      {result.decision.status}
                    </span>
                  </div>
                </div>
                <div>
                  <p className="text-xs text-slate-400 uppercase tracking-wide">Action</p>
                  <p className="mt-2 font-medium text-slate-100">{result.decision.action}</p>
                </div>
              </div>
              <Separator className="bg-slate-700" />
              <div>
                <p className="text-xs text-slate-400 uppercase tracking-wide">Reasoning</p>
                <p className="mt-2 text-slate-300">{result.decision.reasoning}</p>
              </div>
            </CardContent>
          </Card>

          {/* Validation Results */}
          <ValidationResults validation={result.validation} />

          {/* Raw Data */}
          {result.raw_data && (
            <Card className="bg-slate-800 border-slate-700">
              <Collapsible>
                <CollapsibleTrigger className="w-full">
                  <div className="flex items-center justify-between p-6 cursor-pointer hover:bg-slate-700/50 transition-colors">
                    <h3 className="font-semibold text-slate-100">Raw Processing Data</h3>
                    <ChevronDown className="w-5 h-5 text-slate-500" />
                  </div>
                </CollapsibleTrigger>
                <CollapsibleContent>
                  <Separator className="bg-slate-700" />
                  <div className="p-6">
                    <pre className="bg-slate-900/50 p-4 rounded-lg overflow-auto text-xs text-slate-300 border border-slate-700">
                      {JSON.stringify(result.raw_data, null, 2)}
                    </pre>
                  </div>
                </CollapsibleContent>
              </Collapsible>
            </Card>
          )}

          {/* Download Section */}
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader className="border-b border-slate-700">
              <CardTitle className="text-base text-slate-100">Export Results</CardTitle>
            </CardHeader>
            <CardContent className="flex gap-4 pt-6">
              <Button onClick={downloadJSON} variant="outline" className="flex-1 btn-secondary">
                <Download className="w-4 h-4 mr-2" />
                Download JSON
              </Button>
              <Button onClick={downloadCSV} variant="outline" className="flex-1 btn-secondary">
                <Download className="w-4 h-4 mr-2" />
                Download CSV
              </Button>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Info Alert */}
      {backendError && (
        <div className="rounded-lg bg-danger-500/10 border border-danger-500/30 p-4">
          <div className="flex gap-3">
            <AlertCircle className="w-5 h-5 text-danger-400 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-danger-300">Connection Error</h3>
              <p className="text-danger-200/80 text-sm mt-1">
                {backendError}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Info Alert */}
      <div className="rounded-lg bg-danger-500/10 border border-danger-500/30 p-4">
        <div className="flex gap-3">
          <AlertCircle className="w-5 h-5 text-danger-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold text-danger-600">Processing Information</h3>
            <p className="text-danger-400/80 text-sm mt-1">
              The invoice processing system uses AI to extract data, match with POs, validate information, and generate approval decisions. Database file upload is optional for enhanced matching.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
