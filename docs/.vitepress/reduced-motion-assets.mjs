import { mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import path from 'node:path'

export const REDUCED_MOTION_ASSETS = [
  'cc-cv.svg',
  'precharge.svg',
  'passive-balancing.svg',
  'active-balancing.svg',
]

const reducedMotionNames = new Set(REDUCED_MOTION_ASSETS)

function reducedMotionFilename(name) {
  return name.replace(/\.svg$/, '.reduce.svg')
}

const SMIL_ELEMENT = /<(animate|animateMotion|animateTransform|set|discard)\b[^>]*?(?:\/\s*>|>[\s\S]*?<\/\1\s*>)/g

export function withoutSvgMotion(svg) {
  return svg.replace(SMIL_ELEMENT, '')
}

function hidePlaybackGroup(svg) {
  return svg.replace(/<g\b([^>]*)>/g, (opening, attributes) => {
    const className = attributes.match(/\bclass=(["'])(.*?)\1/)?.[2]
    if (!className?.split(/\s+/).includes('playback')) return opening

    if (/\bopacity\s*=/.test(attributes)) {
      return `<g${attributes.replace(/\bopacity\s*=\s*(["'])[^"']*\1/, 'opacity="0"')}>`
    }
    return `<g${attributes} opacity="0">`
  })
}

export function writeReducedMotionAssets(sourceDir, publicDir) {
  const outputDir = path.join(publicDir, 'circuits', 'reduced-motion')
  mkdirSync(outputDir, { recursive: true })

  return REDUCED_MOTION_ASSETS.map((name) => {
    const source = readFileSync(path.join(sourceDir, name), 'utf8')
    const still = hidePlaybackGroup(withoutSvgMotion(source))
    if (/<(?:animate|animateMotion|animateTransform|set|discard)\b/.test(still)) {
      throw new Error(`reduced-motion: 无法清除 ${name} 中的 SMIL`)
    }
    const output = path.join(outputDir, reducedMotionFilename(name))
    writeFileSync(output, still, 'utf8')
    return output
  })
}

export function reducedMotionAssetsPlugin(docsDir) {
  const sourceDir = path.join(docsDir, 'circuits', 'assets')
  const publicDir = path.join(docsDir, 'public')
  const refresh = () => writeReducedMotionAssets(sourceDir, publicDir)
  return {
    name: 'bms-reduced-motion-assets',
    buildStart() {
      refresh()
    },
    configureServer(server) {
      const sources = REDUCED_MOTION_ASSETS.map((name) => path.join(sourceDir, name))
      server.watcher.add(sources)
      server.watcher.on('change', (changed) => {
        if (sources.includes(changed)) refresh()
      })
    },
  }
}

function escapedAttribute(value) {
  return value
    .replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

export function reducedMotionImageRenderer(md, base) {
  const imageRule = md.renderer.rules.image
  const basePrefix = base.split('/').filter(Boolean).join('/')
  const normalizedBase = basePrefix ? `/${basePrefix}/` : '/'

  md.renderer.rules.image = (tokens, index, options, env, self) => {
    const token = tokens[index]
    const source = token.attrGet('src') ?? ''
    const localSource = source.split(/[?#]/, 1)[0]
    const name = localSource.slice(localSource.lastIndexOf('/') + 1)
    const renderedImage = imageRule(tokens, index, options, env, self)

    if (!reducedMotionNames.has(name) || /^(?:[a-z][a-z\d+.-]*:)?\/\//i.test(localSource) || localSource.startsWith('/')) {
      return renderedImage
    }

    const still = escapedAttribute(`${normalizedBase}circuits/reduced-motion/${reducedMotionFilename(name)}`)
    const label = escapedAttribute(`${token.content || name.slice(0, -4)}，窄屏可横向滚动查看`)
    const width = Number(token.attrGet('width')) || 800
    return `<picture class="bms-motion-diagram" role="region" tabindex="0" aria-label="${label}" style="--bms-motion-width: ${width}px"><source :srcset="'${still}'" media="(prefers-reduced-motion: reduce)">${renderedImage}</picture>`
  }
}
