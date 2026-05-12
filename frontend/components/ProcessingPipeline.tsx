'use client'

import { Check, Loader2 } from 'lucide-react'
import { Progress } from '@/components/ui/progress'
import { ProcessingStep } from '@/lib/types'

interface ProcessingPipelineProps {
  steps: ProcessingStep[]
}

export function ProcessingPipeline({ steps }: ProcessingPipelineProps) {
  const completedSteps = steps.filter(s => s.status === 'complete').length
  const progressPercent = (completedSteps / steps.length) * 100

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-slate-600">Processing Steps</h3>
        <span className="text-sm text-slate-600">{completedSteps} of {steps.length}</span>
      </div>

      <Progress value={progressPercent} className="h-2" />

      <div className="space-y-3 mt-6">
        {steps.map((step) => (
          <div key={step.id} className="flex items-start gap-4">
            <div className="flex-shrink-0 mt-1">
              {step.status === 'complete' && (
                <div className="w-6 h-6 rounded-full bg-success-500 flex items-center justify-center shadow-md">
                  <Check className="w-4 h-4 text-white" />
                </div>
              )}
              {step.status === 'active' && (
                <div className="w-6 h-6 rounded-full bg-primary-500 flex items-center justify-center shadow-md">
                  <Loader2 className="w-4 h-4 text-white animate-spin" />
                </div>
              )}
              {step.status === 'pending' && (
                <div className="w-6 h-6 rounded-full border-2 border-slate-600 bg-slate-700" />
              )}
            </div>
            <div className="flex-1 pt-0.5">
              <p className={`text-sm font-medium ${
                step.status === 'complete' ? 'text-success-400' :
                step.status === 'active' ? 'text-primary-400' :
                'text-slate-600'
              }`}>
                {step.title}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
