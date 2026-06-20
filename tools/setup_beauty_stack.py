#!/usr/bin/env python3
"""Setup Beauty Stack — batch-install UI beautification libraries into a target project.

Usage:
    python tools/setup_beauty_stack.py <target> --check       # preflight only
    python tools/setup_beauty_stack.py <target> --check --json  # machine-readable
    python tools/setup_beauty_stack.py <target> --preset standard  # install
    python tools/setup_beauty_stack.py <target> --preset deluxe --dry-run  # plan only
    python tools/setup_beauty_stack.py <target> --preset custom  # interactive
"""

import os, sys, subprocess, json, shutil, argparse
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional

# ── Path resolution ─────────────────────────────────────────────
_PKB_ROOT = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ── Constants ────────────────────────────────────────────────────
CHECKMARK = "✅"
WARNMARK = "⚠️"
ERRORMARK = "❌"
SKIPMARK = "⏭️"

# ── Data structures ──────────────────────────────────────────────

@dataclass
class ProjectInfo:
    """Detected project metadata."""
    project_type: str = "vanilla"         # react|nextjs|vue|vite|vanilla
    typescript: bool = False
    package_manager: str = "npm"          # npm|pnpm|yarn|bun
    package_manager_path: str = "npm"
    has_package_json: bool = False
    is_monorepo: bool = False
    existing_packages: dict = field(default_factory=dict)
    existing_configs: dict = field(default_factory=dict)
    css_frameworks: list = field(default_factory=list)
    next_router: str = ""                 # app|pages|""


@dataclass
class InstallResult:
    """Result of a single package install attempt."""
    name: str
    status: str = "pending"               # installed|skipped|failed
    version: str = ""
    reason: str = ""


@dataclass
class ConfigResult:
    """Result of a single config file operation."""
    path: str
    status: str = "pending"               # created|merged|skipped|failed
    reason: str = ""


@dataclass
class PresetReport:
    """Full report after preset execution."""
    status: str = "pending"               # success|partial|blocked
    preset: str = ""
    project: Optional[ProjectInfo] = None
    installed: list = field(default_factory=list)   # list[InstallResult]
    configs: list = field(default_factory=list)     # list[ConfigResult]
    warnings: list = field(default_factory=list)
    next_steps: list = field(default_factory=list)

# ── Preset definitions ───────────────────────────────────────────

PRESETS = {
    "minimal": {
        "name": "极简 (Minimal)",
        "description": "Tailwind CSS only — best for projects that already have a component library.",
        "packages": {
            "core": ["tailwindcss", "postcss", "autoprefixer"],
            "utilities": ["clsx", "tailwind-merge"],
        },
        "shadcn": False,
        "motion": False,
        "magic_ui": False,
        "react_bits": False,
        "roughviz": False,
        "design_rules": False,
    },
    "standard": {
        "name": "标准 (Standard)",
        "description": "Tailwind + shadcn/ui + Motion — the modern production stack.",
        "packages": {
            "core": ["tailwindcss", "postcss", "autoprefixer", "tailwindcss-animate"],
            "shadcn_deps": [
                "@radix-ui/react-accordion", "@radix-ui/react-aspect-ratio",
                "@radix-ui/react-avatar", "@radix-ui/react-checkbox",
                "@radix-ui/react-collapsible", "@radix-ui/react-context-menu",
                "@radix-ui/react-dialog", "@radix-ui/react-dropdown-menu",
                "@radix-ui/react-hover-card", "@radix-ui/react-label",
                "@radix-ui/react-menubar", "@radix-ui/react-navigation-menu",
                "@radix-ui/react-popover", "@radix-ui/react-progress",
                "@radix-ui/react-radio-group", "@radix-ui/react-scroll-area",
                "@radix-ui/react-select", "@radix-ui/react-separator",
                "@radix-ui/react-slider", "@radix-ui/react-slot",
                "@radix-ui/react-switch", "@radix-ui/react-tabs",
                "@radix-ui/react-toast", "@radix-ui/react-toggle",
                "@radix-ui/react-toggle-group", "@radix-ui/react-tooltip",
            ],
            "shadcn_utils": [
                "sonner", "cmdk", "vaul", "embla-carousel-react",
                "react-day-picker", "react-resizable-panels", "date-fns",
                "react-hook-form", "@hookform/resolvers", "zod",
            ],
            "utilities": [
                "class-variance-authority", "clsx", "tailwind-merge",
                "lucide-react", "next-themes",
            ],
        },
        "shadcn": True,
        "motion": True,
        "magic_ui": False,
        "react_bits": False,
        "roughviz": False,
        "design_rules": False,
    },
    "deluxe": {
        "name": "豪华 (Deluxe)",
        "description": "Full beauty stack — Tailwind + shadcn/ui + Motion + Magic UI + React Bits + UI-UX-Pro-Max rules + roughViz.",
        "packages": {
            "core": ["tailwindcss", "postcss", "autoprefixer", "tailwindcss-animate"],
            "shadcn_deps": [
                "@radix-ui/react-accordion", "@radix-ui/react-aspect-ratio",
                "@radix-ui/react-avatar", "@radix-ui/react-checkbox",
                "@radix-ui/react-collapsible", "@radix-ui/react-context-menu",
                "@radix-ui/react-dialog", "@radix-ui/react-dropdown-menu",
                "@radix-ui/react-hover-card", "@radix-ui/react-label",
                "@radix-ui/react-menubar", "@radix-ui/react-navigation-menu",
                "@radix-ui/react-popover", "@radix-ui/react-progress",
                "@radix-ui/react-radio-group", "@radix-ui/react-scroll-area",
                "@radix-ui/react-select", "@radix-ui/react-separator",
                "@radix-ui/react-slider", "@radix-ui/react-slot",
                "@radix-ui/react-switch", "@radix-ui/react-tabs",
                "@radix-ui/react-toast", "@radix-ui/react-toggle",
                "@radix-ui/react-toggle-group", "@radix-ui/react-tooltip",
            ],
            "shadcn_utils": [
                "sonner", "cmdk", "vaul", "embla-carousel-react",
                "react-day-picker", "react-resizable-panels", "date-fns",
                "react-hook-form", "@hookform/resolvers", "zod",
            ],
            "utilities": [
                "class-variance-authority", "clsx", "tailwind-merge",
                "lucide-react", "next-themes",
            ],
            "magic_ui": ["framer-motion"],
            "react_bits": ["framer-motion"],
            "charts": ["roughjs"],
        },
        "shadcn": True,
        "motion": True,
        "magic_ui": True,
        "react_bits": True,
        "roughviz": True,
        "design_rules": True,
    },
}

# ── Detection functions ──────────────────────────────────────────

def find_package_manager(target_dir: Path):
    """Detect the package manager from lock files and PATH.
    Returns (pm_name, pm_binary_path).
    """
    lock_map = {
        "pnpm-lock.yaml": ("pnpm", "pnpm"),
        "yarn.lock": ("yarn", "yarn"),
        "bun.lockb": ("bun", "bun"),
        "package-lock.json": ("npm", "npm"),
    }
    for lock_file, (pm_name, pm_cmd) in lock_map.items():
        if (target_dir / lock_file).exists():
            binary = shutil.which(pm_cmd) or shutil.which(f"{pm_cmd}.cmd")
            if binary:
                return (pm_name, binary)

    # No lock file — probe available runners
    for pm_cmd in ["pnpm", "yarn", "bun", "npm"]:
        binary = shutil.which(pm_cmd) or shutil.which(f"{pm_cmd}.cmd")
        if binary:
            return (pm_cmd, binary)
    return ("npm", "npm")


def detect_project_type(target_dir: Path) -> str:
    """Detect project type from package.json dependencies."""
    pkg = _read_package_json(target_dir)
    if pkg is None:
        return "vanilla"

    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
    dep_keys = set(deps.keys())

    if "next" in dep_keys:
        return "nextjs"
    if "vue" in dep_keys:
        return "vue"
    if "react" in dep_keys or "react-dom" in dep_keys:
        if "vite" in dep_keys:
            return "vite"
        return "react"
    if "vite" in dep_keys:
        return "vite"
    return "vanilla"


def detect_typescript(target_dir: Path) -> bool:
    """Check if project uses TypeScript."""
    return (target_dir / "tsconfig.json").exists()


def detect_existing_packages(target_dir: Path) -> dict:
    """Return {package_name: version} for all installed packages."""
    pkg = _read_package_json(target_dir)
    if pkg is None:
        return {}
    all_deps = {}
    for section in ["dependencies", "devDependencies", "peerDependencies"]:
        all_deps.update(pkg.get(section, {}))
    return all_deps


def detect_existing_configs(target_dir: Path) -> dict:
    """Check which config files already exist."""
    config_files = [
        "tailwind.config.js", "tailwind.config.ts", "tailwind.config.mjs",
        "postcss.config.js", "postcss.config.mjs", "postcss.config.ts",
        "components.json",
    ]
    result = {}
    for cf in config_files:
        result[cf] = (target_dir / cf).exists()
    return result


def detect_css_frameworks(target_dir: Path) -> list:
    """Detect existing CSS frameworks that might conflict."""
    pkg = _read_package_json(target_dir)
    if pkg is None:
        return []
    all_deps = {}
    for section in ["dependencies", "devDependencies"]:
        all_deps.update(pkg.get(section, {}))

    conflicts = []
    framework_map = {
        "bootstrap": "Bootstrap",
        "@mui/material": "Material UI (MUI)",
        "@mui/system": "Material UI (MUI)",
        "antd": "Ant Design",
        "@chakra-ui/react": "Chakra UI",
        "bulma": "Bulma",
        "foundation-sites": "Foundation",
        "semantic-ui-react": "Semantic UI",
        "@mantine/core": "Mantine",
        "daisyui": "DaisyUI",
        "windicss": "Windi CSS",
        "uno.css": "UnoCSS",
    }
    for pkg_name, label in framework_map.items():
        if pkg_name in all_deps:
            conflicts.append(label)
    return conflicts


def detect_monorepo(target_dir: Path) -> bool:
    """Check for monorepo indicators."""
    indicators = [
        "pnpm-workspace.yaml", "lerna.json", "nx.json", "turbo.json",
    ]
    for ind in indicators:
        if (target_dir / ind).exists():
            return True
    pkg = _read_package_json(target_dir)
    if pkg and "workspaces" in pkg:
        return True
    return False


def detect_next_router(target_dir: Path) -> str:
    """Detect Next.js router type (app/ vs pages/)."""
    if (target_dir / "app").exists() and (target_dir / "app" / "layout.tsx").exists():
        return "app"
    if (target_dir / "app").exists() and (target_dir / "app" / "layout.jsx").exists():
        return "app"
    if (target_dir / "pages").exists():
        return "pages"
    return "app"  # default for new Next.js


def _read_package_json(target_dir: Path) -> Optional[dict]:
    """Read package.json, return None if missing."""
    pkg_path = target_dir / "package.json"
    if not pkg_path.exists():
        return None
    try:
        return json.loads(pkg_path.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError):
        return None


def collect_project_info(target_dir: Path) -> ProjectInfo:
    """Gather all project detection results."""
    pm_name, pm_path = find_package_manager(target_dir)
    return ProjectInfo(
        project_type=detect_project_type(target_dir),
        typescript=detect_typescript(target_dir),
        package_manager=pm_name,
        package_manager_path=pm_path,
        has_package_json=(target_dir / "package.json").exists(),
        is_monorepo=detect_monorepo(target_dir),
        existing_packages=detect_existing_packages(target_dir),
        existing_configs=detect_existing_configs(target_dir),
        css_frameworks=detect_css_frameworks(target_dir),
        next_router=detect_next_router(target_dir),
    )

# ── Package installation ─────────────────────────────────────────

def _pm_install_args(pm_name: str, dev: bool = False) -> list:
    """Return the install command args for a given package manager."""
    base = {
        "npm": ["install"],
        "pnpm": ["add"],
        "yarn": ["add"],
        "bun": ["add"],
    }
    dev_flag = {
        "npm": ["--save-dev"],
        "pnpm": ["-D"],
        "yarn": ["-D"],
        "bun": ["-d"],
    }
    args = list(base.get(pm_name, ["install"]))
    if dev:
        args.extend(dev_flag.get(pm_name, ["--save-dev"]))
    return args


def run_pm_command(pm_name: str, pm_path: str, args: list, cwd: Path,
                   timeout: int = 300) -> subprocess.CompletedProcess:
    """Run a package manager command. Uses shell=True for Windows compat."""
    cmd_parts = [pm_path] + args
    # On Windows, shell=True with string; on Unix, list is fine
    if os.name == 'nt':
        cmd = ' '.join(f'"{p}"' if ' ' in p and not p.startswith('"') else p
                       for p in cmd_parts)
        return subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            shell=True, cwd=str(cwd), encoding='utf-8', errors='replace'
        )
    else:
        return subprocess.run(
            cmd_parts, capture_output=True, text=True, timeout=timeout,
            cwd=str(cwd), encoding='utf-8', errors='replace'
        )


def install_packages(package_list: list, pm_name: str, pm_path: str,
                     cwd: Path, existing: dict, dev: bool = False,
                     dry_run: bool = False) -> list:
    """Install a list of packages, skipping those already present.
    Returns list of InstallResult.
    """
    results = []
    to_install = []

    for pkg_spec in package_list:
        pkg_name = pkg_spec.split('@')[0] if '@' in pkg_spec else pkg_spec
        if pkg_name in existing:
            results.append(InstallResult(
                name=pkg_spec, status="skipped",
                version=existing[pkg_name],
                reason=f"Already installed ({existing[pkg_name]})"
            ))
        else:
            to_install.append(pkg_spec)

    if not to_install:
        return results

    if dry_run:
        for pkg in to_install:
            results.append(InstallResult(
                name=pkg, status="pending",
                reason="Would install (dry-run)"
            ))
        return results

    # Install in batches of 20 to avoid command-line length issues
    batch_size = 20
    for i in range(0, len(to_install), batch_size):
        batch = to_install[i:i + batch_size]
        install_args = _pm_install_args(pm_name, dev=dev) + batch
        proc = run_pm_command(pm_name, pm_path, install_args, cwd)

        for pkg in batch:
            if proc.returncode == 0:
                results.append(InstallResult(
                    name=pkg, status="installed",
                    reason="Installed successfully"
                ))
            else:
                results.append(InstallResult(
                    name=pkg, status="failed",
                    reason=f"Install failed: {proc.stderr[:200] if proc.stderr else 'unknown error'}"
                ))

    return results


# ── Config file generators ────────────────────────────────────────

def _write_if_changed(path: Path, content: str, dry_run: bool = False,
                      force: bool = False) -> ConfigResult:
    """Write a file, with merge/skip logic. Returns ConfigResult."""
    rel_path = str(path)

    if dry_run:
        action = "would overwrite" if path.exists() else "would create"
        return ConfigResult(path=rel_path, status="pending",
                            reason=f"{action} (dry-run)")

    if path.exists() and not force:
        # Backup existing
        bak_path = path.with_suffix(path.suffix + '.bak')
        try:
            shutil.copy2(path, bak_path)
        except OSError:
            pass
        path.write_text(content, encoding='utf-8')
        return ConfigResult(path=rel_path, status="merged",
                            reason=f"Overwritten (backup at {bak_path.name})")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')
    return ConfigResult(path=rel_path, status="created",
                        reason="Created new file")


TAILWIND_CONFIG_JS = '''/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
{content_paths}
  ],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
'''

TAILWIND_CONFIG_MINIMAL = '''/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
{content_paths}
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
'''

POSTCSS_CONFIG = '''export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
'''

COMPONENTS_JSON_REACT = '''{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "default",
  "rsc": false,
  "tsx": {tsx},
  "tailwind": {
    "config": "tailwind.config.js",
    "css": "{css_path}",
    "baseColor": "slate",
    "cssVariables": true,
    "prefix": ""
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils",
    "ui": "@/components/ui",
    "lib": "@/lib",
    "hooks": "@/hooks"
  }
}
'''

COMPONENTS_JSON_NEXT = '''{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "default",
  "rsc": true,
  "tsx": {tsx},
  "tailwind": {
    "config": "tailwind.config.js",
    "css": "{css_path}",
    "baseColor": "slate",
    "cssVariables": true,
    "prefix": ""
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils",
    "ui": "@/components/ui",
    "lib": "@/lib",
    "hooks": "@/hooks"
  }
}
'''

GLOBALS_CSS_SHADCN = '''@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 0 0% 3.9%;
    --card: 0 0% 100%;
    --card-foreground: 0 0% 3.9%;
    --popover: 0 0% 100%;
    --popover-foreground: 0 0% 3.9%;
    --primary: 0 0% 9%;
    --primary-foreground: 0 0% 98%;
    --secondary: 0 0% 96.1%;
    --secondary-foreground: 0 0% 9%;
    --muted: 0 0% 96.1%;
    --muted-foreground: 0 0% 45.1%;
    --accent: 0 0% 96.1%;
    --accent-foreground: 0 0% 9%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 0 0% 98%;
    --border: 0 0% 89.8%;
    --input: 0 0% 89.8%;
    --ring: 0 0% 3.9%;
    --radius: 0.5rem;
  }

  .dark {
    --background: 0 0% 3.9%;
    --foreground: 0 0% 98%;
    --card: 0 0% 3.9%;
    --card-foreground: 0 0% 98%;
    --popover: 0 0% 3.9%;
    --popover-foreground: 0 0% 98%;
    --primary: 0 0% 98%;
    --primary-foreground: 0 0% 9%;
    --secondary: 0 0% 14.9%;
    --secondary-foreground: 0 0% 98%;
    --muted: 0 0% 14.9%;
    --muted-foreground: 0 0% 63.9%;
    --accent: 0 0% 14.9%;
    --accent-foreground: 0 0% 98%;
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 0 0% 98%;
    --border: 0 0% 14.9%;
    --input: 0 0% 14.9%;
    --ring: 0 0% 83.1%;
  }
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
  }
}
'''

GLOBALS_CSS_MINIMAL = '''@tailwind base;
@tailwind components;
@tailwind utilities;
'''

VITE_CONFIG_TS = '''import path from "path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
});
'''

VITE_CONFIG_JS = '''import path from "path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
});
'''

UTILS_TS = '''import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
'''

UTILS_JS = '''import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs) {
  return twMerge(clsx(inputs));
}
'''


def _content_paths(project_type: str) -> str:
    """Generate Tailwind content paths based on project type."""
    paths = {
        "nextjs": '    "./app/**/*.{js,ts,jsx,tsx,mdx}",\n'
                  '    "./components/**/*.{js,ts,jsx,tsx,mdx}",\n'
                  '    "./src/**/*.{js,ts,jsx,tsx,mdx}",',
        "vue": '    "./src/**/*.{vue,js,ts,jsx,tsx}",\n'
               '    "./index.html",',
        "react": '    "./src/**/*.{js,ts,jsx,tsx}",\n'
                 '    "./index.html",',
        "vite": '    "./src/**/*.{js,ts,jsx,tsx}",\n'
                '    "./index.html",',
        "vanilla": '    "./src/**/*.{js,ts,jsx,tsx,html}",\n'
                   '    "./**/*.html",',
    }
    return paths.get(project_type, paths["vanilla"])


def _css_output_path(project_type: str) -> str:
    """Determine the CSS entry file path."""
    paths = {
        "nextjs": "app/globals.css",
        "vue": "src/assets/main.css",
        "react": "src/index.css",
        "vite": "src/index.css",
        "vanilla": "src/index.css",
    }
    return paths.get(project_type, "src/index.css")


def generate_tailwind_config(target_dir: Path, project_type: str,
                             has_shadcn: bool, ts: bool,
                             dry_run: bool = False,
                             force: bool = False) -> ConfigResult:
    """Generate tailwind.config with appropriate content paths."""
    ext = ".ts" if ts else ".js"
    config_path = target_dir / f"tailwind.config{ext}"

    if config_path.exists() and not force:
        return ConfigResult(path=str(config_path), status="skipped",
                            reason="Config already exists (use --force to overwrite)")

    content = TAILWIND_CONFIG_JS if has_shadcn else TAILWIND_CONFIG_MINIMAL
    content = content.replace("{content_paths}", _content_paths(project_type))

    return _write_if_changed(config_path, content, dry_run, force)


def generate_postcss_config(target_dir: Path, ts: bool,
                            dry_run: bool = False,
                            force: bool = False) -> ConfigResult:
    """Generate postcss.config with tailwindcss + autoprefixer."""
    if ts:
        config_path = target_dir / "postcss.config.ts"
        content = POSTCSS_CONFIG  # same content, TS can import JS-style exports
    else:
        config_path = target_dir / "postcss.config.js"
        content = POSTCSS_CONFIG

    if config_path.exists() and not force:
        return ConfigResult(path=str(config_path), status="skipped",
                            reason="Config already exists (use --force to overwrite)")

    return _write_if_changed(config_path, content, dry_run, force)


def generate_components_json(target_dir: Path, project_type: str,
                             ts: bool, css_path: str,
                             dry_run: bool = False,
                             force: bool = False) -> ConfigResult:
    """Generate shadcn components.json."""
    config_path = target_dir / "components.json"
    if config_path.exists() and not force:
        return ConfigResult(path=str(config_path), status="skipped",
                            reason="Config already exists (use --force to overwrite)")

    template = COMPONENTS_JSON_NEXT if project_type == "nextjs" else COMPONENTS_JSON_REACT
    content = template.replace("{tsx}", "true" if ts else "false")
    content = content.replace("{css_path}", css_path)

    return _write_if_changed(config_path, content, dry_run, force)


def generate_globals_css(target_dir: Path, project_type: str,
                         has_shadcn: bool,
                         dry_run: bool = False,
                         force: bool = False) -> ConfigResult:
    """Generate the CSS entry file with Tailwind directives and shadcn variables."""
    css_rel = _css_output_path(project_type)
    css_path = target_dir / css_rel

    if css_path.exists() and not force:
        return ConfigResult(path=str(css_path), status="skipped",
                            reason="CSS file already exists (use --force to overwrite)")

    content = GLOBALS_CSS_SHADCN if has_shadcn else GLOBALS_CSS_MINIMAL
    return _write_if_changed(css_path, content, dry_run, force)


def generate_vite_config(target_dir: Path, ts: bool,
                         dry_run: bool = False,
                         force: bool = False) -> ConfigResult:
    """Generate vite.config with path aliases."""
    ext = ".ts" if ts else ".js"
    config_path = target_dir / f"vite.config{ext}"

    if config_path.exists() and not force:
        return ConfigResult(path=str(config_path), status="skipped",
                            reason="vite.config already exists (use --force to overwrite)")

    content = VITE_CONFIG_TS if ts else VITE_CONFIG_JS
    return _write_if_changed(config_path, content, dry_run, force)


def generate_utils_lib(target_dir: Path, ts: bool,
                       dry_run: bool = False,
                       force: bool = False) -> ConfigResult:
    """Generate lib/utils with cn() helper."""
    ext = ".ts" if ts else ".js"
    utils_path = target_dir / "src" / "lib" / f"utils{ext}"

    if utils_path.exists() and not force:
        return ConfigResult(path=str(utils_path), status="skipped",
                            reason="utils already exists (use --force to overwrite)")

    content = UTILS_TS if ts else UTILS_JS
    return _write_if_changed(utils_path, content, dry_run, force)


# ── Design rules (UI-UX-Pro-Max) ──────────────────────────────────

def copy_design_rules(target_dir: Path, dry_run: bool = False) -> list:
    """Copy .mdc design rule files from PKB webpacks to target project.
    Searches raw/webpacks/ for ui-ux-pro-max rule files.
    Returns list of ConfigResult.
    """
    results = []
    # Search for UI-UX-Pro-Max webpack directories
    webpacks_dir = _PKB_ROOT / "raw" / "webpacks"
    if not webpacks_dir.exists():
        return [ConfigResult(path="design-rules/", status="failed",
                             reason="raw/webpacks/ not found in PKB")]

    # Look for ui-ux-pro-max webpack dirs
    rule_dirs = []
    for d in webpacks_dir.iterdir():
        if d.is_dir() and "ui-ux-pro-max" in d.name.lower():
            rule_dirs.append(d)

    if not rule_dirs:
        return [ConfigResult(path="design-rules/", status="skipped",
                             reason="No UI-UX-Pro-Max webpack found in PKB")]

    # Target rules directory
    rules_target = target_dir / ".cursor" / "rules"
    if dry_run:
        results.append(ConfigResult(path=str(rules_target), status="pending",
                                    reason="Would copy design rules (dry-run)"))
        return results

    rules_target.mkdir(parents=True, exist_ok=True)
    copied = 0
    for rule_dir in rule_dirs:
        for mdc_file in rule_dir.rglob("*.mdc"):
            dest = rules_target / mdc_file.name
            try:
                shutil.copy2(mdc_file, dest)
                copied += 1
            except OSError:
                pass

    if copied > 0:
        results.append(ConfigResult(path=str(rules_target), status="created",
                                    reason=f"Copied {copied} .mdc design rule files"))
    else:
        results.append(ConfigResult(path=str(rules_target), status="skipped",
                                    reason="No .mdc files found in webpack"))
    return results


# ── Preset execution ──────────────────────────────────────────────

def execute_preset(target_dir: Path, preset_name: str, pm_name: str,
                   pm_path: str, project_type: str, ts: bool,
                   existing_packages: dict, dry_run: bool = False,
                   force: bool = False,
                   skip_components: list = None,
                   include_components: list = None) -> PresetReport:
    """Execute a preset installation plan. Returns PresetReport."""
    skip_components = skip_components or []
    include_components = include_components or []
    preset = PRESETS.get(preset_name)
    if not preset:
        return PresetReport(status="blocked",
                            warnings=[f"Unknown preset: {preset_name}"])

    report = PresetReport(preset=preset_name)
    report.project = collect_project_info(target_dir)

    # ── Collect all packages to install ──
    all_packages = []
    all_dev_packages = []

    for category, pkgs in preset.get("packages", {}).items():
        if category in skip_components:
            continue
        if category == "core":
            all_dev_packages.extend(pkgs)
        elif category == "shadcn_deps":
            if "shadcn" not in skip_components:
                all_packages.extend(pkgs)
        elif category == "shadcn_utils":
            if "shadcn" not in skip_components:
                all_packages.extend(pkgs)
        elif category == "utilities":
            all_packages.extend(pkgs)
        elif category == "magic_ui":
            if "magic-ui" not in skip_components:
                all_packages.extend(pkgs)
        elif category == "react_bits":
            if "react-bits" not in skip_components:
                all_packages.extend(pkgs)
        elif category == "charts":
            if "roughviz" not in skip_components:
                all_packages.extend(pkgs)
        else:
            all_packages.extend(pkgs)

    # Motion is a runtime dep
    if preset.get("motion") and "motion" not in skip_components:
        if project_type == "vue":
            all_packages.append("motion-v")
        else:
            all_packages.append("motion")

    # Add --include packages
    for pkg in include_components:
        all_packages.append(pkg)

    # ── Install packages ──
    print(f"\n{'[DRY-RUN] ' if dry_run else ''}Installing packages for preset: {preset['name']}")
    print(f"  Project type: {project_type}")
    print(f"  Package manager: {pm_name}")
    print(f"  TypeScript: {ts}")
    print()

    if all_dev_packages:
        print(f"  Dev dependencies ({len(all_dev_packages)}): {', '.join(all_dev_packages[:8])}...")
        results = install_packages(all_dev_packages, pm_name, pm_path,
                                   target_dir, existing_packages,
                                   dev=True, dry_run=dry_run)
        report.installed.extend(results)

    if all_packages:
        print(f"  Dependencies ({len(all_packages)}): {', '.join(all_packages[:8])}...")
        results = install_packages(all_packages, pm_name, pm_path,
                                   target_dir, existing_packages,
                                   dev=False, dry_run=dry_run)
        report.installed.extend(results)

    # ── Generate config files ──
    has_shadcn = preset.get("shadcn", False) and "shadcn" not in skip_components
    css_path = _css_output_path(project_type)

    if not dry_run:
        print(f"\nGenerating configuration files...")

    # Tailwind config
    result = generate_tailwind_config(target_dir, project_type, has_shadcn, ts,
                                      dry_run, force)
    report.configs.append(result)

    # PostCSS config
    result = generate_postcss_config(target_dir, ts, dry_run, force)
    report.configs.append(result)

    # Globals CSS
    result = generate_globals_css(target_dir, project_type, has_shadcn,
                                  dry_run, force)
    report.configs.append(result)

    # Components.json (only for shadcn presets)
    if has_shadcn:
        result = generate_components_json(target_dir, project_type, ts, css_path,
                                          dry_run, force)
        report.configs.append(result)

    # Utils lib (only for shadcn presets)
    if has_shadcn:
        result = generate_utils_lib(target_dir, ts, dry_run, force)
        report.configs.append(result)

    # Vite config for vite/react projects
    if project_type in ("vite", "react"):
        result = generate_vite_config(target_dir, ts, dry_run, force)
        report.configs.append(result)

    # ── Design rules (deluxe only) ──
    if preset.get("design_rules") and "design-rules" not in skip_components:
        results = copy_design_rules(target_dir, dry_run)
        report.configs.extend(results)

    # ── Warnings ──
    css_conflicts = detect_css_frameworks(target_dir)
    if css_conflicts:
        report.warnings.append(
            f"Detected existing CSS frameworks: {', '.join(css_conflicts)}. "
            f"CSS class conflicts possible with Tailwind."
        )

    if detect_monorepo(target_dir):
        report.warnings.append(
            "Monorepo detected. Make sure you're targeting the correct sub-project."
        )

    # ── Next steps ──
    report.next_steps.append(f"Run `{pm_name} dev` to start the dev server")
    if has_shadcn:
        report.next_steps.append(
            "Import shadcn components: import { Button } from '@/components/ui/button'"
        )
        report.next_steps.append(
            "Add more components: npx shadcn@latest add <component-name>"
        )
    if preset.get("magic_ui"):
        report.next_steps.append(
            "Browse Magic UI components: https://magicui.design"
        )
    if preset.get("react_bits"):
        report.next_steps.append(
            "Browse React Bits: https://www.reactbits.dev"
        )
    report.next_steps.append(
        "Customize theme colors in your CSS file (--primary, --secondary, etc.)"
    )

    # Compute final status
    failed = [r for r in report.installed if r.status == "failed"]
    if failed:
        report.status = "partial"
    else:
        report.status = "success"

    return report


# ── Report formatting ─────────────────────────────────────────────

def format_report_json(report: PresetReport) -> str:
    """Serialize report as JSON for LLM consumption."""
    data = {
        "status": report.status,
        "preset": report.preset,
        "project": asdict(report.project) if report.project else None,
        "installed": {
            "packages": [
                {"name": r.name, "status": r.status, "version": r.version, "reason": r.reason}
                for r in report.installed
            ],
            "count": len([r for r in report.installed if r.status == "installed"]),
            "skipped": len([r for r in report.installed if r.status == "skipped"]),
            "failed": len([r for r in report.installed if r.status == "failed"]),
        },
        "configs": {
            "created": [r.path for r in report.configs if r.status == "created"],
            "merged": [r.path for r in report.configs if r.status == "merged"],
            "skipped": [r.path for r in report.configs if r.status == "skipped"],
            "failed": [r.path for r in report.configs if r.status == "failed"],
        },
        "warnings": report.warnings,
        "next_steps": report.next_steps,
    }
    return json.dumps(data, indent=2, ensure_ascii=False)


def format_report_terminal(report: PresetReport) -> str:
    """Format report for terminal display."""
    installed_count = len([r for r in report.installed if r.status == "installed"])
    pending_pkg = len([r for r in report.installed if r.status == "pending"])
    skipped_count = len([r for r in report.installed if r.status == "skipped"])
    failed_count = len([r for r in report.installed if r.status == "failed"])
    created_count = len([r for r in report.configs if r.status == "created"])
    pending_cfg = len([r for r in report.configs if r.status == "pending"])
    merged_count = len([r for r in report.configs if r.status == "merged"])
    skipped_cfg = len([r for r in report.configs if r.status == "skipped"])

    is_dry = (pending_pkg > 0 or pending_cfg > 0) and installed_count == 0

    lines = []
    sep = "=" * 60
    lines.append(sep)
    if is_dry:
        lines.append("  Beauty Stack — DRY RUN (no changes made)")
    else:
        lines.append("  Beauty Stack Setup Report")
    lines.append(sep)
    lines.append(f"  Preset:     {PRESETS.get(report.preset, {}).get('name', report.preset)}")
    if report.project:
        lines.append(f"  Project:    {report.project.project_type} "
                     f"{'+TS' if report.project.typescript else '+JS'}")
        lines.append(f"  Pkg Mgr:    {report.project.package_manager}")
    lines.append(sep)
    if is_dry:
        lines.append(f"  Packages:   {pending_pkg} would install, "
                     f"{skipped_count} would skip")
        lines.append(f"  Configs:    {pending_cfg} would create/modify, "
                     f"{skipped_cfg} would skip")
    else:
        lines.append(f"  Packages:   {installed_count} installed, "
                     f"{skipped_count} skipped, {failed_count} failed")
        lines.append(f"  Configs:    {created_count} created, "
                     f"{merged_count} merged, {skipped_cfg} skipped")
    lines.append(sep)

    failures = [r for r in report.installed if r.status == "failed"]
    if failures:
        lines.append(f"  {ERRORMARK} Failed packages:")
        for f in failures:
            lines.append(f"     - {f.name}: {f.reason}")
        lines.append(sep)

    if report.warnings:
        lines.append(f"  {WARNMARK} Warnings:")
        for w in report.warnings:
            lines.append(f"     - {w}")
        lines.append(sep)

    lines.append("  Next steps:")
    for step in report.next_steps:
        lines.append(f"     {step}")
    lines.append(sep)
    return '\n'.join(lines)


def format_check_terminal(info: ProjectInfo) -> str:
    """Format preflight check as terminal output."""
    lines = []
    sep = "=" * 60
    lines.append(sep)
    lines.append("  Beauty Stack — Preflight Check")
    lines.append(sep)
    lines.append(f"  Project type:      {info.project_type}")
    lines.append(f"  TypeScript:        {info.typescript}")
    lines.append(f"  Package manager:   {info.package_manager}")
    lines.append(f"  package.json:      {'Yes' if info.has_package_json else 'No ' + WARNMARK}")
    lines.append(f"  Monorepo:          {'Yes ' + WARNMARK if info.is_monorepo else 'No'}")
    lines.append(f"  Next.js router:    {info.next_router}" if info.project_type == "nextjs" else "")
    lines.append(sep)
    lines.append("  Existing configs:")
    for name, exists in info.existing_configs.items():
        mark = CHECKMARK if exists else "  -"
        lines.append(f"    {mark} {name}")
    lines.append(sep)
    if info.css_frameworks:
        lines.append(f"  {WARNMARK} Existing CSS frameworks: {', '.join(info.css_frameworks)}")
        lines.append("     May conflict with Tailwind. Consider prefix mode.")
        lines.append(sep)
    if info.is_monorepo:
        lines.append(f"  {WARNMARK} Monorepo detected. Target the correct sub-project.")
        lines.append(sep)
    lines.append(f"  Available presets: minimal | standard | deluxe | custom")
    lines.append(sep)
    return '\n'.join(lines)


def format_check_json(info: ProjectInfo) -> str:
    """Format preflight check as JSON."""
    data = {
        "project": {
            "type": info.project_type,
            "typescript": info.typescript,
            "package_manager": info.package_manager,
            "has_package_json": info.has_package_json,
            "is_monorepo": info.is_monorepo,
            "next_router": info.next_router,
        },
        "existing_packages": info.existing_packages,
        "existing_configs": info.existing_configs,
        "css_frameworks": info.css_frameworks,
        "available_presets": ["minimal", "standard", "deluxe", "custom"],
    }
    return json.dumps(data, indent=2, ensure_ascii=False)


# ── Custom preset interactive ─────────────────────────────────────

CUSTOM_OPTIONS = [
    ("tailwind", "Tailwind CSS (foundation, always recommended)", True),
    ("shadcn", "shadcn/ui (46 components, requires Tailwind)", False),
    ("motion", "Motion (framework-agnostic animation engine)", False),
    ("magic-ui", "Magic UI (150+ shadcn-compatible animated components)", False),
    ("react-bits", "React Bits (130+ animated React components)", False),
    ("roughviz", "roughViz (hand-drawn style charts)", False),
    ("design-rules", "UI-UX-Pro-Max design rules (.mdc files)", False),
]


def run_custom_interactive(target_dir: Path, pm_name: str, pm_path: str,
                           project_type: str, ts: bool,
                           existing_packages: dict, dry_run: bool = False,
                           force: bool = False) -> PresetReport:
    """Interactive custom preset selection. Returns PresetReport."""
    print("\n" + "=" * 60)
    print("  Custom Preset — Select components to install")
    print("=" * 60)
    print("  Enter 'y' to include, 'n' to skip, 'q' to confirm and proceed")
    print()

    selections = {}
    for key, desc, default in CUSTOM_OPTIONS:
        default_str = "Y/n" if default else "y/N"
        selections[key] = default

    print("  Selections (defaults shown, press Enter to accept):")
    for key, desc, default in CUSTOM_OPTIONS:
        mark = CHECKMARK if selections[key] else "  -"
        print(f"    {mark} [{key}] {desc}")
    print()

    # Build a simplified preset from selections
    custom_preset = {
        "name": "自定义 (Custom)",
        "description": "User-selected components.",
        "packages": {},
        "shadcn": selections.get("shadcn", False),
        "motion": selections.get("motion", False),
        "magic_ui": selections.get("magic-ui", False),
        "react_bits": selections.get("react-bits", False),
        "roughviz": selections.get("roughviz", False),
        "design_rules": selections.get("design-rules", False),
    }

    # Build package lists
    custom_preset["packages"]["core"] = ["tailwindcss", "postcss", "autoprefixer"]
    custom_preset["packages"]["utilities"] = ["clsx", "tailwind-merge"]

    if selections.get("shadcn"):
        custom_preset["packages"]["shadcn_deps"] = PRESETS["standard"]["packages"]["shadcn_deps"]
        custom_preset["packages"]["shadcn_utils"] = PRESETS["standard"]["packages"]["shadcn_utils"]
        custom_preset["packages"]["utilities"].extend([
            "class-variance-authority", "lucide-react", "next-themes",
        ])
        custom_preset["packages"]["core"].append("tailwindcss-animate")

    if selections.get("magic-ui"):
        custom_preset["packages"]["magic_ui"] = ["framer-motion"]

    if selections.get("react-bits"):
        custom_preset["packages"]["react_bits"] = ["framer-motion"]

    if selections.get("roughviz"):
        custom_preset["packages"]["charts"] = ["roughjs"]

    # Temporarily inject custom preset and execute
    PRESETS["_custom"] = custom_preset
    report = execute_preset(target_dir, "_custom", pm_name, pm_path,
                            project_type, ts, existing_packages,
                            dry_run, force)
    report.preset = "custom"
    del PRESETS["_custom"]
    return report


# ── CLI ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Setup Beauty Stack — batch-install UI beautification libraries",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/setup_beauty_stack.py ./my-app --check
  python tools/setup_beauty_stack.py ./my-app --check --json
  python tools/setup_beauty_stack.py ./my-app --preset standard
  python tools/setup_beauty_stack.py ./my-app --preset deluxe --dry-run
  python tools/setup_beauty_stack.py ./my-app --preset custom
  python tools/setup_beauty_stack.py . --preset standard --json
  python tools/setup_beauty_stack.py . --preset standard --skip shadcn motion

Presets:
  minimal   — Tailwind CSS only
  standard  — Tailwind + shadcn/ui + Motion
  deluxe    — Full stack: standard + Magic UI + React Bits + design rules + roughViz
  custom    — Interactive selection
        """
    )
    parser.add_argument("target", nargs="?", default=".",
                        help="Target project directory (default: current dir)")
    parser.add_argument("--preset", choices=["minimal", "standard", "deluxe", "custom"],
                        help="Preset to install")
    parser.add_argument("--check", action="store_true",
                        help="Run preflight check only (no changes)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show plan without executing")
    parser.add_argument("--json", action="store_true",
                        help="Output results as JSON (for LLM consumption)")
    parser.add_argument("--skip", nargs="*", default=[],
                        help="Components to skip (shadcn, motion, magic-ui, react-bits, roughviz, design-rules)")
    parser.add_argument("--include", nargs="*", default=[],
                        help="Extra packages to include")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite existing configs without prompting")
    parser.add_argument("--package-manager", choices=["npm", "pnpm", "yarn", "bun"],
                        help="Force a specific package manager")

    args = parser.parse_args()
    target_dir = Path(args.target).resolve()

    if not target_dir.exists():
        print(f"{ERRORMARK} Target directory does not exist: {target_dir}")
        return 1

    # ── Check mode ──
    if args.check:
        info = collect_project_info(target_dir)
        if args.json:
            print(format_check_json(info))
        else:
            print(format_check_terminal(info))
        return 0

    # ── Collect project info ──
    info = collect_project_info(target_dir)
    pm_name = args.package_manager or info.package_manager
    pm_path = args.package_manager or info.package_manager_path
    # Resolve binary path if a name was passed
    if pm_path in ("npm", "pnpm", "yarn", "bun"):
        pm_path = shutil.which(pm_path) or shutil.which(f"{pm_path}.cmd") or pm_path

    # ── Determine preset ──
    preset_name = args.preset
    if not preset_name:
        # Show available presets and exit
        print("No preset specified. Available presets:")
        for key, preset in PRESETS.items():
            print(f"  {key:12s} — {preset['name']}: {preset['description']}")
        print()
        print("Usage: python tools/setup_beauty_stack.py <target> --preset <name>")
        print("Or use --preset custom for interactive selection.")
        return 1

    if preset_name not in PRESETS:
        print(f"{ERRORMARK} Unknown preset: {preset_name}")
        print(f"Available: {', '.join(PRESETS.keys())}")
        return 1

    # ── Execute ──
    if preset_name == "custom":
        report = run_custom_interactive(
            target_dir, pm_name, pm_path, info.project_type,
            info.typescript, info.existing_packages,
            dry_run=args.dry_run, force=args.force,
        )
    else:
        report = execute_preset(
            target_dir, preset_name, pm_name, pm_path,
            info.project_type, info.typescript,
            info.existing_packages,
            dry_run=args.dry_run, force=args.force,
            skip_components=args.skip,
            include_components=args.include,
        )

    # ── Output ──
    if args.json:
        print(format_report_json(report))
    else:
        print(format_report_terminal(report))

    # ── Exit code ──
    if report.status == "blocked":
        return 1
    if report.status == "partial":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
