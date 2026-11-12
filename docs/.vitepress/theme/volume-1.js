import './volume-1.css'
import { mountVolume1Calculators } from '../volume-1-generated/calc.js'
import { mountVolume1Gallery } from './volume-1-gallery.js'

export function mountVolumeOneTools(root = document) {
  mountVolume1Calculators(root)
  const cleanupGallery = mountVolume1Gallery(root)
  return () => { cleanupGallery?.() }
}
