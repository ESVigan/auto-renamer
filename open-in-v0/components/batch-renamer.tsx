"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { ProjectCodesTable } from "@/components/project-codes-table"
import { DiffRulesTable } from "@/components/diff-rules-table"
import { FileListTable } from "@/components/file-list-table"
import { HistoryLog } from "@/components/history-log"
import { Save, FolderOpen, FileUp, FolderUp, RefreshCw, Trash2, Play, Undo2 } from "lucide-react"

export interface ProjectCode {
  id: string
  code: string
  fullName: string
}

export interface DiffRule {
  id: string
  diffNum: string
  fullName: string
  abbr: string
  lang: string
}

export interface FileItem {
  id: string
  originalPath: string
  originalName: string
  newName: string
  status: "ready" | "error" | "pending"
  errorMessage?: string
}

export function BatchRenamer() {
  const [date, setDate] = useState("251013")
  const [projectCodes, setProjectCodes] = useState<ProjectCode[]>([
    { id: "1", code: "洗衣店偷衣服", fullName: "Pre-shoot-洗衣店偷衣服-C02---华容道平铺02-tileflower" },
    { id: "2", code: "插队的补偿", fullName: "Pre-shoot-插队的补偿-C01-华容道平铺02tileflower" },
    { id: "3", code: "无语言偷看1", fullName: "pre-shoot-无语言偷看1" },
  ])
  const [diffRules, setDiffRules] = useState<DiffRule[]>([
    { id: "1", diffNum: "1", fullName: "核玩翻页", abbr: "HWFY", lang: "cn" },
    { id: "2", diffNum: "2", fullName: "动画quiz-批量化", abbr: "BVC", lang: "es" },
    { id: "3", diffNum: "4", fullName: "核玩新版", abbr: "SLT", lang: "en" },
  ])
  const [files, setFiles] = useState<FileItem[]>([])
  const [history, setHistory] = useState<string[]>([])
  const [lastRenames, setLastRenames] = useState<Array<{ oldPath: string; newPath: string }>>([])

  const addHistory = (message: string) => {
    setHistory((prev) => [...prev, `[${new Date().toLocaleTimeString()}] ${message}`])
  }

  const generateNewName = (
    originalName: string,
  ): { newName: string; status: "ready" | "error"; errorMessage?: string } => {
    const nameNoExt = originalName.replace(/\.[^/.]+$/, "")
    const ext = originalName.match(/\.[^/.]+$/)?.[0] || ""

    // Find matching project code
    let matchedCode: ProjectCode | undefined
    for (const project of projectCodes) {
      if (project.code && nameNoExt.startsWith(project.code)) {
        matchedCode = project
        break
      }
    }

    if (!matchedCode) {
      return { newName: "[无匹配项目]", status: "error", errorMessage: "未找到匹配的项目代号" }
    }

    // Extract diff number
    const remaining = nameNoExt.slice(matchedCode.code.length)
    const diffNum = remaining.startsWith("-") ? remaining.slice(1) : remaining

    if (!diffNum) {
      return { newName: "[缺少差分号]", status: "error", errorMessage: "文件名中缺少差分号" }
    }

    if (!/^\d+$/.test(diffNum)) {
      return { newName: `[差分号格式错误: ${diffNum}]`, status: "error", errorMessage: "差分号必须为纯数字" }
    }

    // Find matching diff rule
    const rule = diffRules.find((r) => r.diffNum === diffNum)
    if (!rule) {
      return { newName: `[差分号${diffNum}无规则]`, status: "error", errorMessage: `差分号 ${diffNum} 没有对应的规则` }
    }

    if (!rule.fullName || !rule.abbr || !rule.lang) {
      return { newName: `[差分号${diffNum}规则不完整]`, status: "error", errorMessage: "规则数据不完整" }
    }

    const finalName = `${date}_${matchedCode.fullName}+${rule.fullName}_${rule.lang}_${rule.abbr}_1080x1920${ext}`
    return { newName: finalName, status: "ready" }
  }

  const handleAddFiles = () => {
    // Simulate file selection
    const mockFiles = ["洗衣店偷衣服1.mp4", "插队的补偿2.mp4", "无语言偷看1-4.mp4"]

    const newFiles: FileItem[] = mockFiles.map((name, idx) => {
      const result = generateNewName(name)
      return {
        id: `file-${Date.now()}-${idx}`,
        originalPath: `/mock/path/${name}`,
        originalName: name,
        newName: result.newName,
        status: result.status,
        errorMessage: result.errorMessage,
      }
    })

    setFiles((prev) => [...prev, ...newFiles])
    addHistory(`添加了 ${mockFiles.length} 个文件`)
  }

  const handleRefresh = () => {
    const updatedFiles = files.map((file) => {
      const result = generateNewName(file.originalName)
      return {
        ...file,
        newName: result.newName,
        status: result.status,
        errorMessage: result.errorMessage,
      }
    })
    setFiles(updatedFiles)
    addHistory("已刷新文件识别")
  }

  const handleClearFiles = () => {
    setFiles([])
    addHistory("已清空文件列表")
  }

  const handleExecute = () => {
    const readyFiles = files.filter((f) => f.status === "ready")
    if (readyFiles.length === 0) {
      addHistory("❌ 没有可执行的文件")
      return
    }

    const renames = readyFiles.map((f) => ({
      oldPath: f.originalPath,
      newPath: f.originalPath.replace(f.originalName, f.newName),
    }))

    setLastRenames(renames)
    addHistory(`✅ 成功重命名 ${readyFiles.length} 个文件`)
    setFiles([])
  }

  const handleUndo = () => {
    if (lastRenames.length === 0) {
      addHistory("❌ 没有可撤销的操作")
      return
    }

    addHistory(`⏪ 已撤销 ${lastRenames.length} 个文件的重命名`)
    setLastRenames([])
  }

  return (
    <div className="flex min-h-screen flex-col">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="container mx-auto flex items-center justify-between px-6 py-4">
          <div className="flex items-center gap-4">
            <h1 className="text-2xl font-bold text-primary">🚀 智能批量重命名工具</h1>
            <Badge variant="secondary" className="text-xs">
              v0.1
            </Badge>
          </div>
          <div className="flex gap-2">
            <Button variant="default" size="sm">
              <Save className="mr-2 h-4 w-4" />
              保存配置
            </Button>
            <Button variant="outline" size="sm">
              <FolderOpen className="mr-2 h-4 w-4" />
              加载配置
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="container mx-auto flex flex-1 gap-6 p-6">
        {/* Left Panel */}
        <div className="flex w-[400px] flex-col gap-6">
          {/* Global Settings */}
          <Card className="p-6">
            <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold">🌐 全局设置</h2>
            <div className="flex items-center gap-3">
              <label className="w-32 text-sm text-muted-foreground">日期 (YYMMDD):</label>
              <Input
                value={date}
                onChange={(e) => setDate(e.target.value)}
                className="max-w-[150px]"
                placeholder="251013"
              />
            </div>
          </Card>

          {/* Project Codes */}
          <Card className="flex flex-col p-6">
            <h2 className="mb-2 flex items-center gap-2 text-sm font-semibold">📋 项目代号配置</h2>
            <p className="mb-4 text-xs text-muted-foreground">💡 直接在表格中编辑，支持多行配置</p>
            <ProjectCodesTable projectCodes={projectCodes} setProjectCodes={setProjectCodes} onUpdate={handleRefresh} />
          </Card>

          {/* Diff Rules */}
          <Card className="flex flex-col p-6">
            <h2 className="mb-2 flex items-center gap-2 text-sm font-semibold">⚙️ 差分规则配置</h2>
            <p className="mb-4 text-xs text-muted-foreground">💡 直接在表格中编辑，所有项目共用</p>
            <DiffRulesTable diffRules={diffRules} setDiffRules={setDiffRules} onUpdate={handleRefresh} />
          </Card>
        </div>

        {/* Right Panel */}
        <div className="flex flex-1 flex-col gap-6">
          {/* File List */}
          <Card className="flex flex-1 flex-col p-6">
            <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold">📁 文件列表与预览</h2>

            <div className="mb-4 flex flex-wrap gap-2">
              <Button variant="default" size="sm" onClick={handleAddFiles}>
                <FileUp className="mr-2 h-4 w-4" />
                添加文件
              </Button>
              <Button variant="default" size="sm">
                <FolderUp className="mr-2 h-4 w-4" />
                添加文件夹
              </Button>
              <Button variant="outline" size="sm" onClick={handleRefresh}>
                <RefreshCw className="mr-2 h-4 w-4" />
                刷新识别
              </Button>
              <Button variant="destructive" size="sm" onClick={handleClearFiles}>
                <Trash2 className="mr-2 h-4 w-4" />
                清空列表
              </Button>
            </div>

            <FileListTable files={files} setFiles={setFiles} onUpdate={handleRefresh} />

            <p className="mt-4 text-center text-xs text-muted-foreground">💡 支持拖拽文件到此处</p>
          </Card>

          {/* Execute Section */}
          <Card className="p-6">
            <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold">🚀 执行与历史</h2>

            <Button
              className="mb-4 w-full"
              size="lg"
              onClick={handleExecute}
              disabled={files.filter((f) => f.status === "ready").length === 0}
            >
              <Play className="mr-2 h-5 w-5" />
              开始执行重命名
            </Button>

            <Separator className="my-4" />

            <h3 className="mb-2 text-xs font-semibold text-muted-foreground">📜 操作历史:</h3>
            <HistoryLog history={history} />

            <Button
              className="mt-4 w-full"
              variant="destructive"
              size="sm"
              onClick={handleUndo}
              disabled={lastRenames.length === 0}
            >
              <Undo2 className="mr-2 h-4 w-4" />
              撤销上次操作
            </Button>
          </Card>
        </div>
      </div>

      {/* Status Bar */}
      <footer className="border-t border-border bg-card px-6 py-2">
        <div className="container mx-auto flex items-center justify-between text-xs text-muted-foreground">
          <span>就绪</span>
          <span>文件: {files.length}</span>
        </div>
      </footer>
    </div>
  )
}
