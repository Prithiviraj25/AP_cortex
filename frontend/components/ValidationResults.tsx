'use client'

import { Check, AlertCircle, X } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ValidationResult } from '@/lib/types'

interface ValidationResultsProps {
  validation: ValidationResult
}

export function ValidationResults({ validation }: ValidationResultsProps) {
  return (
    <Card className="bg-slate-800 border-slate-700">
      <CardHeader className="border-b border-slate-700">
        <CardTitle className="text-base text-slate-100">Validation Results</CardTitle>
      </CardHeader>
      <CardContent className="pt-6">
        <div className="grid md:grid-cols-3 gap-6">
          {/* Passed Checks */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Check className="w-5 h-5 text-success-400" />
              <h4 className="font-semibold text-sm text-success-400">Passed ({validation.checks_passed.length})</h4>
            </div>
            <div className="space-y-2">
              {validation.checks_passed.length > 0 ? (
                validation.checks_passed.map((check, idx) => (
                  <div key={idx} className="badge-success">
                    ✓ {check}
                  </div>
                ))
              ) : (
                <p className="text-xs text-slate-500">No passed checks</p>
              )}
            </div>
          </div>

          {/* Warnings */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-warning-400" />
              <h4 className="font-semibold text-sm text-warning-400">Warnings ({validation.warnings.length})</h4>
            </div>
            <div className="space-y-2">
              {validation.warnings.length > 0 ? (
                validation.warnings.map((warning, idx) => (
                  <div key={idx} className="badge-warning">
                    ⚠ {warning}
                  </div>
                ))
              ) : (
                <p className="text-xs text-slate-500">No warnings</p>
              )}
            </div>
          </div>

          {/* Issues */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <X className="w-5 h-5 text-danger-400" />
              <h4 className="font-semibold text-sm text-danger-400">Issues ({validation.issues.length})</h4>
            </div>
            <div className="space-y-2">
              {validation.issues.length > 0 ? (
                validation.issues.map((issue, idx) => (
                  <div key={idx} className="badge-danger">
                    ✗ {issue}
                  </div>
                ))
              ) : (
                <p className="text-xs text-slate-500">No issues</p>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
