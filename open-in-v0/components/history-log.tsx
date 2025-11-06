"use client"

interface HistoryLogProps {
  history: string[]
}

export function HistoryLog({ history }: HistoryLogProps) {
  return (
    <div className="h-32 overflow-y-auto rounded-md border border-border bg-muted/30 p-3 font-mono text-xs">
      {history.length === 0 ? (
        <p className="text-muted-foreground">暂无操作历史</p>
      ) : (
        <div className="space-y-1">
          {history.map((entry, idx) => (
            <div key={idx} className="text-foreground">
              {entry}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
