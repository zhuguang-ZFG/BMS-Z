import { fileURLToPath } from 'node:url'
import path from 'node:path'

export const VITEPRESS_DIR = path.dirname(fileURLToPath(import.meta.url))
export const SITE_OUT_DIR = path.join(VITEPRESS_DIR, 'site-dist')
