#!/usr/bin/env bun

import { mkdir } from "fs/promises"
import { join } from "path"

const isWatch = process.argv.includes("--watch")
const isDev = process.env.MIX_ENV !== "prod"

// Get current directory (assets/)
// Bun provides import.meta.dir for the directory of the current file
const assetsDir = import.meta.dir
const outputDir = join(assetsDir, "..", "priv", "static", "assets")

// Ensure output directory exists
await mkdir(outputDir, { recursive: true })

// Build JavaScript bundle using Bun's native bundler
const jsResult = await Bun.build({
  entrypoints: [join(assetsDir, "js", "app.ts")],
  outdir: outputDir,
  target: "browser",
  format: "esm",
  splitting: true,
  minify: !isDev,
  sourcemap: isDev ? "inline" : false,
  external: ["/fonts/*", "/images/*"],
})

if (!jsResult.success) {
  console.error("JavaScript build failed:", jsResult.logs)
  process.exit(1)
}

// Build CSS using Tailwind CLI via Bun
const cssInput = join(assetsDir, "css", "app.css")
const cssOutput = join(outputDir, "app.css")
const cssCmd = isDev
  ? ["bunx", "tailwindcss", "-i", cssInput, "-o", cssOutput]
  : ["bunx", "tailwindcss", "-i", cssInput, "-o", cssOutput, "--minify"]

const cssProcess = Bun.spawn({
  cmd: cssCmd,
  cwd: assetsDir,
  stdout: "inherit",
  stderr: "inherit",
})

const cssExitCode = await cssProcess.exited

if (cssExitCode !== 0) {
  console.error("CSS build failed")
  process.exit(1)
}

console.log("Build complete!")

