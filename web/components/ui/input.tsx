import * as React from 'react'

type InputProps = React.InputHTMLAttributes<HTMLInputElement>

export const Input = React.forwardRef<HTMLInputElement, InputProps>(function Input(
  { className, ...props },
  ref
) {
  return (
    <input
      ref={ref}
      className={['w-full rounded-xl border border-default bg-secondary text-primary px-3 py-2 focus-ring transition-colors duration-150', className || ''].join(' ').trim()}
      {...props}
    />
  )
})
