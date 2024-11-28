// src/components/ui/loading-state.tsx

import React from 'react'
import { Loader2 } from 'lucide-react'

interface LoadingStateProps {
  message?: string
  variant?: 'default' | 'overlay' | 'inline'
  size?: 'sm' | 'md' | 'lg'
}

const sizeClasses = {
  sm: 'h-4 w-4',
  md: 'h-6 w-6',
  lg: 'h-8 w-8'
}

const variantClasses = {
  default: 'min-h-[200px] rounded-lg border bg-card p-4',
  overlay: 'fixed inset-0 z-50 flex bg-black/50',
  inline: 'inline-flex items-center'
}

export function LoadingState({ 
  message = 'Loading...', 
  variant = 'default',
  size = 'md'
}: LoadingStateProps) {
  const content = (
    <>
      <Loader2 className={`animate-spin ${sizeClasses[size]}`} />
      {message && 
        <span className={`ml-2 ${size === 'sm' ? 'text-sm' : 'text-base'}`}>
          {message}
        </span>
      }
    </>
  )

  if (variant === 'inline') {
    return (
      <div className={`${variantClasses[variant]}`}>
        {content}
      </div>
    )
  }

  return (
    <div className={`${variantClasses[variant]} flex items-center justify-center`}>
      <div className="flex flex-col items-center">
        {content}
      </div>
    </div>
  )
}