// src/components/ui/scroll-area.tsx
import * as React from "react"

import { cn } from "../../lib/utils"

interface ScrollAreaProps extends React.HTMLAttributes<HTMLDivElement> {
  maxHeight?: string;
}

const ScrollArea = React.forwardRef<HTMLDivElement, ScrollAreaProps>(
  ({ className, maxHeight = "400px", children, ...props }, ref) => (
    <div
      ref={ref}
      className={cn("overflow-auto", className)}
      style={{ maxHeight }}
      {...props}
    >
      {children}
    </div>
  )
)
ScrollArea.displayName = "ScrollArea"

export { ScrollArea }