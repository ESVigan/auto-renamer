"use client"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Plus, Minus } from "lucide-react"
import type { DiffRule } from "@/components/batch-renamer"

interface DiffRulesTableProps {
  diffRules: DiffRule[]
  setDiffRules: (rules: DiffRule[]) => void
  onUpdate: () => void
}

export function DiffRulesTable({ diffRules, setDiffRules, onUpdate }: DiffRulesTableProps) {
  const handleAdd = () => {
    setDiffRules([...diffRules, { id: `rule-${Date.now()}`, diffNum: "", fullName: "", abbr: "", lang: "" }])
  }

  const handleRemove = (id: string) => {
    setDiffRules(diffRules.filter((r) => r.id !== id))
    onUpdate()
  }

  const handleUpdate = (id: string, field: keyof Omit<DiffRule, "id">, value: string) => {
    setDiffRules(diffRules.map((r) => (r.id === id ? { ...r, [field]: value } : r)))
    onUpdate()
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="max-h-[250px] space-y-2 overflow-y-auto rounded-md border border-border p-2">
        {diffRules.map((rule) => (
          <div key={rule.id} className="flex gap-2">
            <Input
              value={rule.diffNum}
              onChange={(e) => handleUpdate(rule.id, "diffNum", e.target.value)}
              placeholder="差分号"
              className="h-8 w-16 text-xs"
            />
            <Input
              value={rule.fullName}
              onChange={(e) => handleUpdate(rule.id, "fullName", e.target.value)}
              placeholder="版本名全称"
              className="h-8 flex-1 text-xs"
            />
            <Input
              value={rule.abbr}
              onChange={(e) => handleUpdate(rule.id, "abbr", e.target.value)}
              placeholder="缩写"
              className="h-8 w-20 text-xs"
            />
            <Input
              value={rule.lang}
              onChange={(e) => handleUpdate(rule.id, "lang", e.target.value)}
              placeholder="语言"
              className="h-8 w-16 text-xs"
            />
            <Button variant="ghost" size="sm" className="h-8 w-8 p-0" onClick={() => handleRemove(rule.id)}>
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
