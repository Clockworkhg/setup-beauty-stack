# setup-beauty-stack

美化技术栈一键安装 — 给 AI 编码助手装上完整的前端审美系统。

## 一句话

把"千篇一律紫色渐变 UI"升级成专业级界面。通过预设套餐批量安装 Tailwind CSS + shadcn/ui + Motion + Magic UI + React Bits + UI-UX-Pro-Max 设计规则 + roughViz。

## 安装

```bash
# 克隆到 Claude Code skills 目录
git clone https://github.com/Clockworkhg/setup-beauty-stack.git ~/.claude/skills/setup-beauty-stack
```

## 使用

```
/setup-beauty-stack <target-directory> --preset minimal|standard|deluxe|custom
```

## 四个套餐

| 套餐 | 内容 | 适用 |
|------|------|------|
| 🅰 极简 | Tailwind CSS + PostCSS + clsx | 已有组件库，只要原子化 CSS |
| 🅱 标准 | 极简 + shadcn/ui（26个 Radix 包）+ Motion | 大多数新项目的生产级起点 |
| 🅲 豪华 | 标准 + Magic UI + React Bits + UI-UX-Pro-Max + roughViz | 从零开始的豪华全餐 |
| 🅳 自定义 | 交互式逐项勾选 | 特定组合需求 |

## 设计原则

- **非破坏性** — 永不覆盖已有配置，`--force` 前自动备份
- **幂等** — 已安装的包自动跳过
- **先检测再行动** — 每次从 `--check` 开始
- **套餐优先** — 预设 4 个套餐覆盖 90% 场景

## 依赖

- Python 3.9+
- Node.js 项目（React / Vite / Next.js / Vue / Vanilla）

## 参考的 UI 库

| 库 | Stars | 用途 |
|----|-------|------|
| [UI-UX-Pro-Max](https://github.com/nextlevelbuilder/ui-ux-pro-max) | 93K | 设计规则文件，给 AI 装审美系统 |
| [React Bits](https://github.com/react-bits/react-bits) | 40K | 130+ 动画 React 组件 |
| [Magic UI](https://github.com/magicuidesign/magicui) | 21K | 150+ shadcn 动画组件 |
| [Motion](https://github.com/motiondivision/motion) | 30K | 框架无关声明式动画引擎 |
| [roughViz](https://github.com/jwilber/roughViz) | 7K | 手绘风格数据图表 |

## License

MIT
