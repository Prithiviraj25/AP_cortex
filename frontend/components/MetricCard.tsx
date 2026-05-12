'use client'

import React from 'react'
import { Card, CardContent } from '@/components/ui/card'

interface MetricCardProps {
  label: string
  value: string | number
  icon?: React.ReactNode
  trend?: number
}

export function MetricCard({ label, value, icon, trend }: MetricCardProps) {
  return (
    <Card className="bg-slate-800 border-slate-700 hover:border-primary-500/50 hover:shadow-lg transition-all duration-200">
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-widest">
              {label}
            </p>
            <p className="text-3xl font-bold text-slate-100 mt-2">
              {value}
            </p>
            {trend !== undefined && (
              <p className={`text-xs mt-3 font-medium ${trend >= 0 ? 'text-success-400' : 'text-danger-400'}`}>
                {trend >= 0 ? '↑' : '↓'} {Math.abs(trend)}% from last month
              </p>
            )}
          </div>
          {icon && (
            <div className="ml-4 p-3 rounded-lg bg-primary-500/10">
              <div className="text-primary-400">
                {icon}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
