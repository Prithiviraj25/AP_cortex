'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { MetricCard } from '@/components/MetricCard'
import { StatusBadge } from '@/components/StatusBadge'
import { TrendingUp, CheckCircle, AlertCircle, Clock, Loader2 } from 'lucide-react'
import {
  LineChart, Line, BarChart, Bar, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts'
import { invoiceAPI } from '@/lib/api'
import { toast } from 'sonner'

// Mock data for charts (fallback)
const mockSpendByStatus = [
  { name: 'Approved', value: 2200000, fill: '#10b981' },
  { name: 'Flagged', value: 250000, fill: '#f59e0b' },
  { name: 'Rejected', value: 50000, fill: '#ef4444' },
]

const mockPaymentMethods = [
  { name: 'Bank Transfer', value: 61500, fill: '#3b82f6' },
  { name: 'Credit Card', value: 26500, fill: '#10b981' },
  { name: 'Wire Transfer', value: 12000, fill: '#f59e0b' },
]

const mockPaymentTrend = [
  { month: 'Jan', amount: 245000 },
  { month: 'Feb', amount: 320000 },
  { month: 'Mar', amount: 280000 },
  { month: 'Apr', amount: 390000 },
  { month: 'May', amount: 350000 },
  { month: 'Jun', amount: 420000 },
]

const mockTopVendorsAnalytics = [
  { name: 'Tech Supplies Inc.', amount: 420000, fill: '#3b82f6' },
  { name: 'Software Solutions Ltd.', amount: 385000, fill: '#10b981' },
  { name: 'Consulting Partners', amount: 365000, fill: '#f59e0b' },
  { name: 'Office Equipment Co.', amount: 280000, fill: '#ef4444' },
  { name: 'Marketing Services Inc.', amount: 250000, fill: '#8b5cf6' },
  { name: 'Finance Partners', amount: 220000, fill: '#06b6d4' },
  { name: 'HR Solutions', amount: 180000, fill: '#ec4899' },
  { name: 'IT Consultants', amount: 160000, fill: '#f97316' },
  { name: 'Legal Services', amount: 145000, fill: '#14b8a6' },
  { name: 'Facilities Management', amount: 115000, fill: '#6366f1' },
  { name: 'Travel Services', amount: 95000, fill: '#a855f7' },
  { name: 'Logistics Partners', amount: 85000, fill: '#22d3ee' },
  { name: 'Insurance Providers', amount: 75000, fill: '#f43f5e' },
  { name: 'Training Services', amount: 65000, fill: '#d946ef' },
  { name: 'Maintenance Services', amount: 55000, fill: '#06b6d4' },
]

export default function Analytics() {
  const [analyticsData, setAnalyticsData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        setLoading(true)
        setError(null)
        const data = await invoiceAPI.getAnalytics()
        setAnalyticsData(data)
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : 'Failed to load analytics'
        setError(errorMsg)
        toast.error(errorMsg)
      } finally {
        setLoading(false)
      }
    }

    fetchAnalytics()
  }, [])

  // Transform backend data for charts
  const spendByStatusData = analyticsData?.po_by_status 
    ? Object.entries(analyticsData.po_by_status).map(([name, count]: [string, any]) => ({
        name,
        value: count,
        fill: name === 'Open' ? '#3b82f6' : name === 'Closed' ? '#10b981' : '#f59e0b'
      }))
    : mockSpendByStatus

  const topVendorsData = analyticsData?.top_vendors
    ? Object.entries(analyticsData.top_vendors)
        .map(([name, amount]: [string, any]) => ({ name, amount: amount as number }))
        .sort((a, b) => b.amount - a.amount)
        .slice(0, 15)
    : mockTopVendorsAnalytics

  const paymentMethodsData = analyticsData?.payment_methods
    ? Object.entries(analyticsData.payment_methods).map(([name, count]: [string, any], index: number) => ({
        name,
        value: count,
        fill: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'][index % 5]
      }))
    : mockPaymentMethods

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center space-y-4">
          <Loader2 className="w-8 h-8 animate-spin text-primary-500 mx-auto" />
          <p className="text-slate-300">Loading analytics...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-primary-700 to-primary-300">Analytics Dashboard</h1>
        <p className="text-slate-600 mt-2">System overview and processing metrics</p>
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

      {/* System Metrics */}
      <div className="grid md:grid-cols-4 gap-4">
        <MetricCard
          label="Invoices Processed"
          value={analyticsData?.total_invoices || 0}
          icon={<CheckCircle className="w-5 h-5" />}
        />
        <MetricCard
          label="Success Rate"
          value={`${((analyticsData?.success_rate || 0) * 100).toFixed(1)}%`}
          icon={<TrendingUp className="w-5 h-5" />}
        />
        <MetricCard
          label="Avg Processing Time"
          value={`${(analyticsData?.avg_processing_time || 0).toFixed(1)}s`}
          icon={<Clock className="w-5 h-5" />}
        />
        <MetricCard
          label="Total Amount Processed"
          value={`$${((analyticsData?.total_spend || 0) / 1000000).toFixed(1)}M`}
          icon={<CheckCircle className="w-5 h-5" />}
        />
      </div>

      {/* Latest Processing Result */}
      {analyticsData?.latest_result && (
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader className="border-b border-slate-700">
            <CardTitle className="text-base text-slate-100">Latest Processing Result</CardTitle>
          </CardHeader>
          <CardContent className="pt-6 space-y-4">
            <div className="grid md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Invoice Number</p>
                <p className="text-lg font-semibold text-primary-400">{analyticsData.latest_result.invoice.invoice_number}</p>
              </div>
              <div className="space-y-2">
                <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Vendor</p>
                <p className="text-lg font-semibold text-slate-100">{analyticsData.latest_result.invoice.vendor_name}</p>
              </div>
              <div className="space-y-2">
                <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Amount</p>
                <p className="text-lg font-semibold text-success-400">${analyticsData.latest_result.invoice.total_amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}</p>
              </div>
              <div className="space-y-2">
                <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Status</p>
                <div>
                  <StatusBadge status={analyticsData.latest_result.decision.status} />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Charts */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Spend by Status */}
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader className="border-b border-slate-700">
            <CardTitle className="text-base text-slate-100">Spend by Decision Status</CardTitle>
          </CardHeader>
          <CardContent className="pt-6">
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={spendByStatusData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
                <XAxis dataKey="name" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '0.5rem' }} />
                <Bar dataKey="value" fill="#3b82f6">
                  {spendByStatusData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Payment Trend */}
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader className="border-b border-slate-700">
            <CardTitle className="text-base text-slate-100">Payment Methods Distribution</CardTitle>
          </CardHeader>
          <CardContent className="pt-6">
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={paymentMethodsData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
                <XAxis dataKey="name" stroke="#94a3b8" angle={-45} textAnchor="end" height={80} />
                <YAxis stroke="#94a3b8" />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '0.5rem' }} />
                <Bar dataKey="value" fill="#3b82f6">
                  {paymentMethodsData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Top 15 Vendors */}
      <Card className="bg-slate-800 border-slate-700">
        <CardHeader className="border-b border-slate-700">
          <CardTitle className="text-base text-slate-100">Top 15 Vendors by Spending</CardTitle>
          <CardDescription className="text-slate-400">Total spending across all vendors</CardDescription>
        </CardHeader>
        <CardContent className="pt-6">
          <ResponsiveContainer width="100%" height={400}>
            <BarChart
              layout="vertical"
              data={topVendorsData}
              margin={{ top: 5, right: 30, left: 200, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
              <XAxis type="number" stroke="#94a3b8" />
              <YAxis dataKey="name" type="category" width={195} fontSize={12} stroke="#94a3b8" />
              <Tooltip formatter={(value: any) => `$${value.toLocaleString()}`} contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '0.5rem' }} />
              <Bar dataKey="amount" fill="#3b82f6" radius={[0, 8, 8, 0]}>
                {topVendorsData.map((_entry: any, index: number) => {
                  const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899', '#f97316', '#14b8a6', '#6366f1', '#a855f7', '#22d3ee', '#f43f5e', '#d946ef', '#06b6d4']
                  return <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                })}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  )
}