import { execFileSync } from 'node:child_process'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..')

// 独立产品随站点发布；不复制工程正文进根索引，也不改变根搜索预算。
export function publishEngineering(siteConfig) {
  const destination = path.join(siteConfig.outDir, 'engineering')
  execFileSync('python', ['-X', 'utf8', 'tools/build_engineering.py', '--out', destination], {
    cwd: root,
    stdio: 'inherit',
  })
}
