---
name: setup-beauty-stack
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion
description: Batch-install beautification/UI libraries (Tailwind, shadcn/ui, Motion, Magic UI, React Bits, UI-UX-Pro-Max rules, roughViz) into a target project with preset-based configuration. Non-destructive, detects existing configs, multi-framework support.
argument-hint: [target-directory] [--preset minimal|standard|deluxe|custom]
---

# /setup-beauty-stack — 美化技术栈一键安装

把 AI 编码助手生成的"千篇一律紫色渐变 UI"升级成专业级界面。通过预设套餐批量安装 Tailwind CSS + shadcn/ui + Motion + Magic UI + React Bits + UI-UX-Pro-Max 设计规则 + roughViz 图表库。

## 设计原则

1. **非破坏性** — 永不覆盖已有配置文件，默认跳过；`--force` 覆盖前自动备份为 `.bak`
2. **幂等** — 可重复运行，已安装的包跳过；版本冲突则警告并询问，不做静默升降级
3. **先检测再行动** — 每次执行前先 `--check`，让用户了解全貌再决定
4. **套餐优先** — 预设 4 个套餐覆盖 90% 场景，减少选择负担

## ⚡ Pre-Flight: 自动检测（每次执行前必跑）

```
Step 0: 运行预检
    └─ python tools/setup_beauty_stack.py <target_dir> --check [--json]
        ├─ 项目类型: react | vite | nextjs | vue | vanilla
        ├─ TypeScript: yes | no
        ├─ 包管理器: npm | pnpm | yarn | bun
        ├─ 已有配置: tailwind.config.js, postcss.config.js, components.json, ...
        └─ 冲突检测: Bootstrap, MUI, Ant Design, ... (WARN 如有)

Step 0b: 检测报告解读
    ├─ 无 package.json → 询问是否 npm init -y
    ├─ monorepo → WARN，建议指定子项目
    ├─ 已有 CSS 框架 → WARN，建议 Tailwind prefix 模式
    └─ 全部 clean → 继续
```

### 自动化工具

| 工具 | 用途 | 何时用 |
|------|------|--------|
| `python tools/setup_beauty_stack.py --check <target>` | 项目环境检测 | 每次执行前 |
| `python tools/setup_beauty_stack.py <target> --preset <name>` | 执行安装 | 用户选定套餐后 |
| `python tools/setup_beauty_stack.py <target> --preset <name> --dry-run` | 预览计划 | 不确定时 |
| `python tools/setup_beauty_stack.py <target> --preset <name> --json` | 机器可读输出 | LLM 消费 |

---

## 四个套餐

### 🅰 极简 (Minimal)
- **内容**: Tailwind CSS + PostCSS + Autoprefixer + clsx + tailwind-merge
- **生成**: `tailwind.config.js`, `postcss.config.js`, `src/index.css`（仅 @tailwind 指令）
- **不含**: shadcn、任何组件库、动画库
- **适用**: 已有组件库，只需要原子化 CSS；或用 Tailwind 纯手写风格

### 🅱 标准 (Standard)
- **内容**: 极简全部 + shadcn/ui 完整依赖（26 个 @radix-ui 包 + 10 个工具包）+ Motion 动画引擎
- **生成**: 极简全部 + `components.json` + shadcn CSS 变量 (light/dark) + `src/lib/utils.ts` + `vite.config.ts`（含 @ 路径别名）+ tsconfig 路径别名更新
- **适用**: 大多数 React/Vue 新项目的生产级起点

### 🅲 豪华 (Deluxe)
- **内容**: 标准全部 + Magic UI（150+ shadcn 动画组件）+ React Bits（130+ 动画组件）+ UI-UX-Pro-Max 设计规则（.mdc 文件）+ roughViz 手绘图表
- **生成**: 标准全部 + `.cursor/rules/` 目录（含 .mdc 设计规则）+ 增强的 tailwind.config（含 Magic UI/React Bits 动画 keyframes）+ `DESIGN.md`
- **适用**: 从零开始的"豪华全餐"项目，给 AI 装上完整的审美系统

### 🅳 自定义 (Custom)
- **内容**: 交互式菜单逐项勾选：Tailwind [必选] | shadcn/ui | Motion | Magic UI | React Bits | UI-UX-Pro-Max 规则 | roughViz
- **生成**: 根据勾选动态生成对应配置
- **适用**: 有特定组合需求的场合

---

## 工作流

> 📍 以下命令从项目根目录执行。`tools/setup_beauty_stack.py` 为 PKB 项目自带工具。若 skill 被复制到其他项目，需同步复制 `tools/setup_beauty_stack.py`。

### Step 1: Pre-Flight 检测

```bash
python tools/setup_beauty_stack.py <target_dir> --check
```

展示检测结果给用户：项目类型、包管理器、已有配置、冲突警告。

🔴 **CHECKPOINT** — 确认检测结果无误后继续。如有冲突框架或 monorepo，必须在此时解决。

> ⚡ **失败分支**: 若 `--check` 报错 → 检查 Python 3.9+ 是否安装 → 若仍失败，检查 `tools/setup_beauty_stack.py` 文件是否存在 → 兜底：手动读取 `package.json` 判断项目类型。

### Step 2: 选择套餐

用户口头选择或通过 `--preset` 标志指定：
```
/setup-beauty-stack ./my-app --preset standard
```

如果用户没有指定套餐，展示 4 个套餐并询问。

🔴 **CHECKPOINT** — 等待用户明确选择套餐（A/B/C/D），不替用户决定。

### Step 3: 预览（可选）

如果用户不确定，先 dry-run：
```bash
python tools/setup_beauty_stack.py <target_dir> --preset <name> --dry-run
```

展示将安装哪些包、生成哪些配置、跳过哪些。

🔴 **CHECKPOINT** — 预览结果需用户确认满意。

### Step 4: 执行安装

🛑 **STOP** — 最终确认后执行，这是不可逆步骤。

```bash
python tools/setup_beauty_stack.py <target_dir> --preset <name> [--force]
```

⚠️ `--force` 覆盖已有配置文件（先备份为 `.bak`）。使用 `--force` 前必须 🔴 **CHECKPOINT** 确认用户知晓覆盖风险。

> ⚡ **失败分支**: 若 `npm install` 失败 → 检查 `.npmrc` / 网络 → 切换镜像源 `--registry https://registry.npmmirror.com` → 仍失败则输出手动安装命令列表让用户自行排查。若配置生成冲突 → 跳过已有文件不覆盖 → 输出差异说明 → 兜底：生成 `.example` 参考文件让用户手动合并。

### Step 5: 输出报告

格式化报告展示：
- ✅ 已安装的包及版本
- 📝 创建/合并/跳过的配置文件
- ⚠️ 警告（冲突框架、monorepo 等）
- 🚀 后续操作建议

---

## 边缘情况与降级

### 边缘情况

| 场景 | 行为 | 检查点 |
|------|------|--------|
| 无 `package.json` | WARN — 询问是否 `npm init -y`（或对应 PM 的 init） | 🔴 等待用户确认 |
| 已有 Bootstrap/MUI/Ant Design | ⚠️ 警告 CSS class 冲突，建议 `--prefix tw-` 隔离 | 🔴 等待用户选择策略 |
| monorepo（pnpm-workspace.yaml 等） | ⚠️ 警告，建议指定子项目路径 | 🔴 等待用户指定子项目 |
| TypeScript vs JS | 自动检测 `tsconfig.json`，生成对应 `.ts` / `.js` 文件 | 自动，无需确认 |
| Next.js App Router | 检测 `app/` 目录，调整 CSS 路径为 `app/globals.css`，rsc=true | 自动，无需确认 |
| Vue 项目 | CSS → `src/assets/main.css`，Motion → `motion-v`，content 路径适配 `.vue` | 自动，无需确认 |

### 诚实降级

- ✅ **允许**: Tailwind 无 shadcn 也能正常安装
- ✅ **允许**: Motion 无 React 的情况（Vue/vanilla 项目）
- ❌ **禁止**: shadcn 在没有 Tailwind 的情况下安装（检测到后应先装 Tailwind）
- ❌ **禁止**: Magic UI 在无 shadcn 的情况下安装

## 反例黑名单 — 绝对不要做的事

以下反模式是本 skill 的禁区，违反任一条即为执行错误。

| # | 🚫 反模式 | 为什么危险 | ✅ 正确做法 |
|---|-----------|-----------|-----------|
| 1 | **跳过 `--check` 直接安装** | 不检测项目类型就装 → 装错框架配置、CSS冲突、包依赖级联失败 | 每次执行必须先 `--check`，展示检测报告后再安装 |
| 2 | **承诺"帮你设计UI"** | 本 skill 安装的是工具链和设计规则文件，不是视觉设计服务。越界承诺会让用户期望落空 | 澄清定位："我帮你装一套专业级 UI 基础设施，装完后 AI 编码助手就有了完整的审美系统来生成高质量界面" |
| 3 | **shadcn 无 Tailwind 就装** | shadcn/ui 强依赖 Tailwind CSS，缺前置安装后完全不可用 | 先确保 Tailwind 已装或同时安装（极简→标准→豪华递进） |
| 4 | **Magic UI 无 shadcn 就装** | Magic UI 是 shadcn 的动画层扩展，缺 shadcn 无法导入任何组件 | 检测 shadcn 是否到位，未安装则阻止并提示先装标准套餐 |
| 5 | **monorepo 根目录直接装** | 依赖散落到错误层级，workspace 协议冲突，其他子项目被污染 | 检测到 `pnpm-workspace.yaml` / `lerna.json` / `rush.json` 立即警告，要求指定子项目路径 |
| 6 | **检测到 Bootstrap/MUI/AntDesign 静默继续** | Tailwind 的 utility class 与这些框架的语义 class 全局冲突，页面样式崩坏 | 必须展示冲突警告，建议 `--prefix tw-` 隔离模式，等用户确认 |
| 7 | **`--force` 覆盖配置不备份** | 用户手写的 `tailwind.config.js` / `postcss.config.js` 永久丢失 | `--force` 覆盖前自动备份为 `.bak` 文件，报告中列出备份路径 |
| 8 | **直接修改项目已有 CSS/组件代码** | 本 skill 是配置安装工具，不应触碰业务代码 | 只生成新的配置文件（`tailwind.config.js`、`src/index.css` 等），不修改 `App.css`、已有组件等业务文件 |
| 9 | **不懂装懂 — 对未知框架硬跑** | 检测到非 React/Vue/Vanilla 项目（如 Angular/Svelte）还强行装可能导致构建链断裂 | 诚实告知"当前项目类型不支持"，只支持的项目类型明确列表：React/Vite/Next.js/Vue/Vanilla |

---

## 知识库引用

本 Skill 参考了 PKB 已收录的以下设计/UI 知识源：

| 库 | PKB Wiki 笔记 | Stars | 核心能力 |
|-----|--------------|-------|----------|
| UI-UX-Pro-Max | [[ui-ux-pro-max-repo]] | 93K | 设计规则文件，给 AI 装"审美系统" |
| React Bits | [[react-bits-repo]] | 40K | 130+ 动画 React 组件 |
| Magic UI | [[magic-ui-repo]] | 21K | 150+ shadcn 动画组件 |
| Motion | [[motion-division-repo]] | 30K | 框架无关声明式动画引擎 |
| roughViz | [[roughviz-repo]] | 7K | 手绘风格数据图表 |
| HeroUI | [[heroui-repo]] | — | NextUI 后继，Tailwind v4 组件库 |

**横评参考**: [[ai-programming-ui-tools-2026]] — 5 个工具的分层对比与选型组合。

---

## 相关 Skill

- **上游**: 无（这是一个项目初始化工具）
- **下游**: 目标项目的 AI 编码助手利用已安装的设计系统生成高质量 UI
- **参见**: 
  - `/make-skill` — 创建新 Skill（可用此 Skill 快速搭建 Skill 项目的 UI 基础设施）
  - `ui-ux-pro-max:ui-ux-pro-max` — UI-UX-Pro-Max 运行时设计规则引擎
  - `/ask-pkb` — 查询 PKB 中收录的设计/前端知识

---

## 故障排除

每条按「触发条件 → 一线修复 → 仍失败兜底」链式 fallback：

| 触发条件 | 一线修复 | 仍失败兜底 |
|----------|----------|-----------|
| `npm install` 报错（ETIMEDOUT / ECONNREFUSED） | 检查 `.npmrc`，切镜像 `--registry https://registry.npmmirror.com` | 输出 `package.json` + `npm install` 命令让用户手跑，逐一排查 |
| shadcn 组件 import 报红（Cannot find module） | 检查 `tsconfig.json` 的 `paths` 和 `vite.config.ts` 的 `resolve.alias` 是否正确 | 手动创建 `src/lib/utils.ts` + 重建 `components.json`，重跑 `npx shadcn@latest init` |
| Tailwind class 写了但页面无变化 | 检查 `tailwind.config.js` 的 `content` 数组是否包含 `./src/**/*.{ts,tsx}` 等路径 | 创建最小复现（一个 `<div className="bg-red-500">`），排查 PostCSS 管线 |
| Magic UI / Motion 动画不触发 | 确认 `framer-motion` 已装（`npm ls framer-motion`），确认组件被 `"use client"` 包裹（Next.js） | 降级到纯 CSS transition 替代，或从 Magic UI 文档粘贴最小示例逐个调试 |
| `components.json` 缺失 / shadcn CLI 报错 | 运行 `npx shadcn@latest init -d`（默认配置初始化） | 手动创建 `components.json`，按 shadcn 文档手工配置 aliases |
| pnpm workspace 依赖提升冲突 | 在 `.npmrc` 添加 `public-hoist-pattern[]=*tailwind*` 和 `shamefully-hoist=true` | 迁移到 `npm` 或 `yarn`，或将 beauty stack 限定到单个 workspace package |
