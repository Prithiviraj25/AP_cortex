'use client'

import { useState, useMemo, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { MetricCard } from '@/components/MetricCard'
import { Package, DollarSign, Building2, Clock, AlertCircle, Loader2 } from 'lucide-react'
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts'
import { invoiceAPI } from '@/lib/api'
import { PurchaseOrder } from '@/lib/types'
import { toast } from 'sonner'

// Mock data for charts (fallback)
const mockStatusDistribution = [
  { name: 'Open', value: 5, fill: '#3b82f6' },
  { name: 'Closed', value: 2, fill: '#10b981' },
  { name: 'Partial', value: 1, fill: '#f59e0b' },
]

const mockTopVendors = [
  { name: 'Tech Supplies Inc.', amount: 36500 },
  { name: 'Office Equipment Co.', amount: 14500 },
  { name: 'Software Solutions Ltd.', amount: 25000 },
  { name: 'Consulting Partners', amount: 35000 },
  { name: 'Marketing Services Inc.', amount: 18000 },
]

const mockSpendByDept = [
  { name: 'IT', amount: 40000 },
  { name: 'Operations', amount: 20500 },
  { name: 'Marketing', amount: 18000 },
  { name: 'HR', amount: 8000 },
  { name: 'Finance', amount: 12000 },
]

const mockPoTimeline = [
  { month: 'Jan', count: 2 },
  { month: 'Feb', count: 4 },
  { month: 'Mar', count: 2 },
]

export default function PODatabase() {
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [poData, setPoData] = useState<PurchaseOrder[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Fetch PO data on mount
  useEffect(() => {
    const fetchPOData = async () => {
      try {
        setLoading(true)
        setError(null)
        const data = await invoiceAPI.getPODatabase()
        setPoData(data)
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : 'Failed to load PO database'
        setError(errorMsg)
        toast.error(errorMsg)
        // Use mock data as fallback
        setPoData([])
      } finally {
        setLoading(false)
      }
    }

    fetchPOData()
  }, [])

  const filteredPOs = useMemo(() => {
    return poData.filter(po => {
      const matchesSearch = po['PO Number'].toLowerCase().includes(searchTerm.toLowerCase()) ||
                          po['Vendor Name'].toLowerCase().includes(searchTerm.toLowerCase())
      const matchesStatus = statusFilter === 'all' || po['Status'] === statusFilter
      return matchesSearch && matchesStatus
    })
  }, [searchTerm, statusFilter, poData])

  const totalSpend = poData.reduce((sum, po) => sum + po['Approved Amount'], 0)
  const openPOs = poData.filter(po => po['Status'] === 'Open').length
  const vendors = new Set(poData.map(po => po['Vendor Name'])).size

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center space-y-4">
          <Loader2 className="w-8 h-8 animate-spin text-primary-500 mx-auto" />
          <p className="text-slate-300">Loading PO database...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-primary-800 to-primary-300">PO Database</h1>
        <p className="text-slate-600 mt-2">Manage and track all purchase orders</p>
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
          label="Total POs"
          value={poData.length}
          icon={<Package className="w-5 h-5" />}
        />
        <MetricCard
          label="Total Spend"
          value={`$${(totalSpend / 1000).toFixed(1)}K`}
          icon={<DollarSign className="w-5 h-5" />}
        />
        <MetricCard
          label="Vendors"
          value={vendors}
          icon={<Building2 className="w-5 h-5" />}
        />
        <MetricCard
          label="Open POs"
          value={openPOs}
          icon={<Clock className="w-5 h-5" />}
        />
      </div>

      {/* Filters */}
      <div className="grid md:grid-cols-2 gap-4">
        <Input
          placeholder="Search by PO Number or Vendor..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="input-dark"
        />
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="input-dark">
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="Open">Open</SelectItem>
            <SelectItem value="Closed">Closed</SelectItem>
            <SelectItem value="Partial">Partial</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Data Table */}
      <Card className="bg-slate-800 border-slate-700">
        <CardHeader className="border-b border-slate-700">
          <CardTitle className="text-slate-100">Purchase Orders ({filteredPOs.length})</CardTitle>
        </CardHeader>
        <CardContent className="pt-6">
          {filteredPOs.length === 0 ? (
            <div className="text-center py-8 text-slate-400">
              <p>No purchase orders found</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table className="table-dark">
                <TableHeader>
                  <TableRow>
                    <TableHead>PO Number</TableHead>
                    <TableHead>Vendor</TableHead>
                    <TableHead>Amount</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Requestor</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredPOs.map((po, idx) => (
                    <TableRow key={idx}>
                      <TableCell className="font-medium text-primary-400">{po['PO Number']}</TableCell>
                      <TableCell>{po['Vendor Name']}</TableCell>
                      <TableCell>${po['Approved Amount'].toLocaleString()}</TableCell>
                      <TableCell>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          po['Status'] === 'Open' ? 'bg-primary-500/10 text-primary-400 border border-primary-500/30' :
                          po['Status'] === 'Closed' ? 'bg-success-500/10 text-success-400 border border-success-500/30' :
                          'bg-warning-500/10 text-warning-400 border border-warning-500/30'
                        }`}>
                          {po['Status']}
                        </span>
                      </TableCell>
                      <TableCell>{new Date(po['Created Date']).toLocaleDateString()}</TableCell>
                      <TableCell>{po['Requestor']}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Charts */}
      <div className="grid md:grid-cols-2 gap-4">
        {/* Status Distribution */}
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader className="border-b border-slate-700">
            <CardTitle className="text-base text-slate-100">PO Status Distribution</CardTitle>
          </CardHeader>
          <CardContent className="pt-6">
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={mockStatusDistribution}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value }) => `${name}: ${value}`}
                  outerRadius={90}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {mockStatusDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '0.5rem' }} />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Top Vendors */}
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader className="border-b border-slate-700">
            <CardTitle className="text-base text-slate-100">Top 5 Vendors</CardTitle>
          </CardHeader>
          <CardContent className="pt-6">
            <ResponsiveContainer width="100%" height={250}>
              <BarChart layout="vertical" data={mockTopVendors}>
                <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
                <XAxis type="number" stroke="#94a3b8" />
                <YAxis dataKey="name" type="category" width={180} stroke="#94a3b8" />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '0.5rem' }} />
                <Bar dataKey="amount" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Spend by Department */}
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader className="border-b border-slate-700">
            <CardTitle className="text-base text-slate-100">Spend by Department</CardTitle>
          </CardHeader>
          <CardContent className="pt-6">
            <ResponsiveContainer width="100%" height={250}>
              <BarChart layout="vertical" data={mockSpendByDept}>
                <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
                <XAxis type="number" stroke="#94a3b8" />
                <YAxis dataKey="name" type="category" width={100} stroke="#94a3b8" />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '0.5rem' }} />
                <Bar dataKey="amount" fill="#10b981" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* PO Timeline */}
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader className="border-b border-slate-700">
            <CardTitle className="text-base text-slate-100">PO Creation Timeline</CardTitle>
          </CardHeader>
          <CardContent className="pt-6">
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={mockPoTimeline}>
                <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
                <XAxis dataKey="month" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '0.5rem' }} />
                <Line type="monotone" dataKey="count" stroke="#f59e0b" strokeWidth={2} dot={{ fill: '#f59e0b' }} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
