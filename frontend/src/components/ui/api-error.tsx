// src/components/ui/api-error.tsx

import React from 'react'
import { AlertOctagon } from 'lucide-react'

interface ApiErrorProps {
  error: Error
  onRetry?: () => void
  className?: string
}

export function ApiError({ error, onRetry, className = '' }: ApiErrorProps) {
  return (
    <div className={`flex flex-col items-center justify-center space-y-4 rounded-lg border border-red-200 bg-red-50 p-6 ${className}`}>
      <AlertOctagon className="h-8 w-8 text-red-500" />
      <div className="text-center">
        <h3 className="text-lg font-semibold text-red-700">
          Failed to load data
        </h3>
        <p className="mt-1 text-sm text-red-500">
          {error.message}
        </p>
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="rounded-md bg-red-100 px-4 py-2 text-sm font-medium text-red-700 hover:bg-red-200"
        >
          Try Again
        </button>
      )}
    </div>
  )
}

// 使用特定的錯誤顯示組件
export function NoDataError({ onRetry }: { onRetry?: () => void }) {
  return (
    <ApiError
      error={new Error('No data available for the selected period')}
      onRetry={onRetry}
    />
  )
}

export function NetworkError({ onRetry }: { onRetry?: () => void }) {
  return (
    <ApiError
      error={new Error('Network error, please check your connection')}
      onRetry={onRetry}
    />
  )
}