import * as React from 'react'

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'accent' | 'outline' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
}

export function Button({ className, variant = 'accent', size = 'md', ...props }: ButtonProps) {
  const base = 'inline-flex items-center justify-center rounded-xl transition-colors duration-150 focus-ring disabled:opacity-50 disabled:pointer-events-none'
  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base',
  }[size]
  const variants = {
    accent: 'accent',
    outline: 'border border-default bg-transparent text-primary',
    ghost: 'bg-transparent text-primary hover:bg-secondary',
  }[variant]
  const cls = [base, sizes, variants, className || ''].join(' ').trim()
  return <button className={cls} {...props} />
}
