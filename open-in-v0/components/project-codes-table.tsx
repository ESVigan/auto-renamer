"use client"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Plus, Minus } from "lucide-react"
import type { ProjectCode } from "@/components/batch-renamer"

interface ProjectCodesTableProps {
  projectCodes: ProjectCode[]
  setProjectCodes: (codes: ProjectCode[]) => void
  onUpdate: () => void
}

export function ProjectCodesTable({ projectCodes, setProjectCodes, onUpdate }: ProjectCodesTableProps) {
  const handleAdd = () => {
    setProjectCodes([...projectCodes, { id: `project-${Date.now()}`, code: "", fullName: "" }])
  }

  const handleRemove = (id: string) => {
    setProjectCodes(projectCodes.filter((p) => p.id !== id))
    onUpdate()
  }

  const handleUpdate = (id: string, field: "code" | "fullName", value: string) => {
    setProjectCodes(projectCodes.map((p) => (p.id === id ? { ...p, [field]: value } : p)))
    onUpdate()
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="max-h-[200px] space-y-2 overflow-y-auto rounded-md border border-border p-2">
        {projectCodes.map((project) => (
          <div key={project.id} className="flex gap-2">
            <Input
              value={project.code}
              onChange={(e) => handleUpdate(project.id, "code", e.target.value)}
              placeholder="项目代号"
              className="h-8 w-32 text-xs"
            />
            <Input
              value={project.fullName}
              onChange={(e) => handleUpdate(project.id, "fullName", e.target.value)}
              placeholder="完整项目名"
              className="h-8 flex-1 text-xs"
            />
            <Button variant="ghost" size="sm" className="h-8 w-8 p-0" onClick={() => handleRemove(project.id)}>
              <Minus className="h-3 w-3" />
            </Button>
          </div>
        ))}
      </div>

      <div className="flex gap-2">
        <Button variant="outline" size="sm" onClick={handleAdd} className="flex-1 bg-transparent">
          <Plus className="mr-2 h-3 w-3" />
          添加行
        </Button>
      </div>
    </div>
  )
}
