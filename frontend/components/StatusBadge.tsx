'use client'

import { Check, AlertCircle, X } from 'lucide-react'

interface StatusBadgeProps {
  status: 'APPROVED' | 'FLAGGED_FOR_REVIEW' | 'REJECTED'
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const variants = {
    APPROVED: {
      bgColor: 'bg-success-500/10',
      borderColor: 'border-success-500/30',
      textColor: 'text-success-400',
      icon: <Check className="w-5 h-5" />,
      label: 'APPROVED'
    },
    FLAGGED_FOR_REVIEW: {
      bgColor: 'bg-warning-500/10',
      borderColor: 'border-warning-500/30',
      textColor: 'text-warning-400',
      icon: <AlertCircle className="w-5 h-5" />,
      label: 'FLAGGED FOR REVIEW'
    },
    REJECTED: {
      bgColor: 'bg-danger-500/10',
      borderColor: 'border-danger-500/30',
      textColor: 'text-danger-400',
      icon: <X className="w-5 h-5" />,
      label: 'REJECTED'
    }
  }

  const config = variants[status]

  return (
    <div className={`
      inline-flex items-center gap-2 px-4 py-3 rounded-lg border
      ${config.bgColor} ${config.borderColor} ${config.textColor}
      font-semibold text-base
    `}>
      {config.icon}
      {config.label}
    </div>
  )
}
