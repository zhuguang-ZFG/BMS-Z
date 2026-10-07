#!/usr/bin/env node
/**
 * 构建后把仓库根上由站点托管的文件拷进 dist。
 *
 * 单独一步而不是塞进 vite 插件：VitePress 自己也在 closeBundle 里拷 public/，
 * 插件之间的钩子顺序没人保证，构建完再补文件是唯一稳的写法。
 *
 * 这个脚本直接由 Node 执行（不像 config.mts 会被 VitePress 打包），
 * 所以 import.meta.url 可信，路径不依赖 cwd。
 */
import { cpSync, existsSync, readFileSync } from 'node:fs'
import path from 'node:path'
import process from 'node:process'

const here = path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1'))
const docsDir = path.dirname(here)
const repoRoot = path.dirname(docsDir)
const outDir = path.join(here, 'dist')

const { assets } = JSON.parse(
  readFileSync(path.join(here, 'site-assets.json'), 'utf8')
)

if (!existsSync(outDir)) {
  console.error(`构建产物不存在：${outDir}——先跑 vitepress build docs`)
  process.exit(1)
}

for (const repoPath of Object.keys(assets)) {
  const from = path.join(repoRoot, repoPath)
  const to = path.join(outDir, path.basename(repoPath))
  if (!existsSync(from)) {
    console.error(`站点托管的文件找不到：${repoPath}`)
    process.exit(1)
  }
  cpSync(from, to)
  console.log(`copied: ${repoPath} -> dist/${path.basename(repoPath)}`)
}

// 动画与照片（docs/circuits/assets/**）是站点内容：正文里上百处 <a> 相对链接指向
// 它们，GitHub 和 Obsidian 靠同一相对路径打开。Vite 只接管 ![](...) 图片引用
// （拷成哈希文件名进 dist/assets/），<a> 链接的原始路径不会出现在 dist——
// 按原相对路径补拷一份，链接在 Pages 上才命中。.md 不拷：PHOTOS.md 由
// VitePress 自己构建成 PHOTOS.html，拷源文件只会覆盖出 markdown 原文。
const animFrom = path.join(docsDir, 'circuits', 'assets')
if (existsSync(animFrom)) {
  cpSync(animFrom, path.join(outDir, 'circuits', 'assets'), {
    recursive: true,
    filter: (src) => !src.endsWith('.md'),
  })
  console.log('copied: docs/circuits/assets -> dist/circuits/assets')
}
