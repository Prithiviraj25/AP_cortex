'use client'

import { useState, useMemo, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { MetricCard } from '@/components/MetricCard'
import { CreditCard, DollarSign, TrendingUp, Calendar, AlertCircle, Loader2 } from 'lucide-react'
import {
  BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts'
import { invoiceAPI } from '@/lib/api'
import { PaymentRecord } from '@/lib/types'
import { toast } from 'sonner'

// Mock data for charts (fallback)
const mockPaymentMethods = [
  { name: 'Bank Transfer', value: 61500, fill: '#3b82f6' },
  { name: 'Credit Card', value: 26500, fill: '#10b981' },
  { name: 'Wire Transfer', value: 12000, fill: '#f59e0b' },
]

const mockVendorDistribution = [
  { name: 'Tech Supplies Inc.', amount: 24500, fill: '#06b6d4' },
  { name: 'Office Equipment Co.', amount: 8500, fill: '#8b5cf6' },
  { name: 'Software Solutions Ltd.', amount: 25000, fill: '#ec4899' },
  { name: 'Consulting Partners', amount: 12000, fill: '#f97316' },
  { name: 'Marketing Services Inc.', amount: 18000, fill: '#14b8a6' },
]

export default function PaymentHistory() {
  const [searchTerm, setSearchTerm] = useState('')
  const [paymentData, setPaymentData] = useState<PaymentRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Fetch payment history on mount
  useEffect(() => {
    const fetchPayments = async () => {
      try {
        setLoading(true)
        setError(null)
        const data = await invoiceAPI.getPaymentHistory()
        setPaymentData(data)
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : 'Failed to load payment history'
        setError(errorMsg)
        toast.error(errorMsg)
        setPaymentData([])
      } finally {
        setLoading(false)
      }
    }

    fetchPayments()
  }, [])

  const filteredPayments = useMemo(() => {
    return paymentData.filter(payment => {
      return payment['Invoice Number'].toLowerCase().includes(searchTerm.toLowerCase()) ||
             payment['Vendor Name'].toLowerCase().includes(searchTerm.toLowerCase())
    })
  }, [searchTerm, paymentData])

  const totalPaid = paymentData.reduce((sum, p) => sum + p['Invoice Amount'], 0)
  const avgPayment = paymentData.length > 0 ? (totalPaid / paymentData.length).toFixed(2) : '0'
  const methodsCount = new Set(paymentData.map(p => p['Payment Method'])).size

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center space-y-4">
          <Loader2 className="w-8 h-8 animate-spin text-primary-500 mx-auto" />
          <p className="text-slate-300">Loading payment history...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-primary-800 to-primary-300">Payment History</h1>
        <p className="text-slate-600 mt-2">Track all invoice payments and payment methods</p>
      </div>

      {/* Error Alert */}
      {error && (
        <Card className="bg-warning-500/10 border-warning-500/30">
          <CardContent className="p-6">
            <div className="flex gap-4">
              <AlertCircle className="w-6 h-6 text-warning-400 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-semibold text-warning-300">Database Not Uploaded</h3>
                <p className="text-warning-200/80 text-sm mt-2">
                  {error.includes('404') || error.includes('not uploaded') 
                    ? 'No database has been uploaded yet. Please go to the Process Invoice page and upload a PO database file first.'
                    : error}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Metrics */}
      <div className="grid md:grid-cols-4 gap-4">
        <MetricCard
          label="Total Paid"
          value={`$${(totalPaid / 1000).toFixed(1)}K`}
          icon={<DollarSign className="w-5 h-5" />}
        />
        <MetricCard
          label="Average Payment"
          value={`$${parseFloat(avgPayment).toLocaleString()}`}
          icon={<TrendingUp className="w-5 h-5" />}
        />
        <MetricCard
          label="Payment Methods"
          value={methodsCount}
          icon={<CreditCard className="w-5 h-5" />}
        />
        <MetricCard
          label="Payments Made"
          value={paymentData.length}
          icon={<Calendar className="w-5 h-5" />}
        />
      </div>

      {/* Search */}
      <Input
        placeholder="Search by Invoice Number or Vendor..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        className="input-dark"
      />

      {/* Payment Records Table */}
      <Card className="bg-slate-800 border-slate-700">
        <CardHeader className="border-b border-slate-700">
          <CardTitle className="text-slate-100">Payment Records ({filteredPayments.length})</CardTitle>
        </CardHeader>
        <CardContent className="pt-6">
          {filteredPayments.length === 0 ? (
            <div className="text-center py-8 text-slate-400">
              <p>No payment records found</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table className="table-dark">
                <TableHeader>
                  <TableRow>
                    <TableHead>Invoice Number</TableHead>
                    <TableHead>Vendor Name</TableHead>
                    <TableHead>Amount</TableHead>
                    <TableHead>Payment Date</TableHead>
                    <TableHead>Payment Method</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredPayments.map((payment, idx) => (
                    <TableRow key={idx}>
                      <TableCell className="font-medium text-primary-400">{payment['Invoice Number']}</TableCell>
                      <TableCell>{payment['Vendor Name']}</TableCell>
                      <TableCell>${payment['Invoice Amount'].toLocaleString()}</TableCell>
                      <TableCell>{new Date(payment['Payment Date']).toLocaleDateString()}</TableCell>
                      <TableCell>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          payment['Payment Method'] === 'Bank Transfer' ? 'bg-primary-500/10 text-primary-400 border border-primary-500/30' :
                          payment['Payment Method'] === 'Credit Card' ? 'bg-success-500/10 text-success-400 border border-success-500/30' :
                          'bg-warning-500/10 text-warning-400 border border-warning-500/30'
                        }`}>
                          {payment['Payment Method']}
                        </span>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Charts */}
      <div className="grid md:grid-cols-1 gap-6">
        {/* Payment Methods */}
        {/* <Card className="bg-slate-800 border-slate-700">
          <CardHeader className="border-b border-slate-700">
            <CardTitle className="text-base text-slate-100">Payment Methods Distribution</CardTitle>
          </CardHeader>
          <CardContent className="pt-6">
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={mockPaymentMethods}>
                <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
                <XAxis dataKey="name" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '0.5rem' }} />
                <Bar dataKey="value" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card> */}

        {/* Vendor Distribution */}
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader className="border-b border-slate-700">
            <CardTitle className="text-base text-slate-100">Vendor Payment Distribution</CardTitle>
          </CardHeader>
          <CardContent className="pt-6">
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={mockVendorDistribution}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, amount }: any) => `${name}: $${(amount / 1000).toFixed(0)}K`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="amount"
                >
                  {mockVendorDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '0.5rem' }} />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
