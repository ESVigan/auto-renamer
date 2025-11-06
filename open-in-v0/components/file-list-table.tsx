"use client"

import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { CheckCircle2, XCircle } from "lucide-react"
import type { FileItem } from "@/components/batch-renamer"

interface FileListTableProps {
  files: FileItem[]
  setFiles: (files: FileItem[]) => void
  onUpdate: () => void
}

export function FileListTable({ files, setFiles, onUpdate }: FileListTableProps) {
  const handleUpdateOriginalName = (id: string, newName: string) => {
    setFiles(files.map((f) => (f.id === id ? { ...f, originalName: newName } : f)))
    onUpdate()
  }

  if (files.length === 0) {
    return (
      <div className="flex flex-1 items-center justify-center rounded-md border border-dashed border-border py-12">
        <p className="text-sm text-muted-foreground">暂无文件，请添加文件</p>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-auto rounded-md border border-border">
      <table className="w-full text-xs">
        <thead className="sticky top-0 bg-muted">
          <tr className="border-b border-border">
            <th className="p-3 text-left font-semibold">原始文件名</th>
            <th className="p-3 text-left font-semibold">新文件名</th>
            <th className="w-20 p-3 text-center font-semibold">状态</th>
          </tr>
        </thead>
        <tbody>
          {files.map((file) => (
            <tr key={file.id} className="border-b border-border last:border-0 hover:bg-muted/50">
              <td className="p-3">
                <Input
                  value={file.originalName}
                  onChange={(e) => handleUpdateOriginalName(file.id, e.target.value)}
                  className="h-7 text-xs"
                />
              </td>
              <td className="p-3">
                <span className={file.status === "ready" ? "text-green-500" : "text-destructive"}>{file.newName}</span>
              </td>
              <td className="p-3 text-center">
                {file.status === "ready" ? (
                  <Badge variant="default" className="gap-1 bg-green-600">
                    <CheckCircle2 className="h-3 w-3" />
                    就绪
                  </Badge>
                ) : (
                  <Badge variant="destructive" className="gap-1">
                    <XCircle className="h-3 w-3" />
                    错误
                  </Badge>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
