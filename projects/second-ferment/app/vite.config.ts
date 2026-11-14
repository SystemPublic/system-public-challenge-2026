import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig, type Plugin } from 'vite'
import fs from 'node:fs'
import path from 'node:path'

// The evidence bundle lives in ../bundle (built by scripts/*.py). Serve it in dev and copy it on build,
// so there is one source of truth and no copy to drift.
const BUNDLE = path.resolve(__dirname, '../bundle/evidence.json')
function evidenceBundle(): Plugin {
  return {
    name: 'heatrx-evidence-bundle',
    configureServer(server) {
      server.middlewares.use('/data/evidence.json', (_req, res) => {
        res.setHeader('Content-Type', 'application/json')
        res.setHeader('Cache-Control', 'no-store')
        fs.createReadStream(BUNDLE).pipe(res)
      })
    },
    writeBundle(opts) {
      const out = path.join(opts.dir ?? 'dist', 'data')
      fs.mkdirSync(out, { recursive: true })
      fs.copyFileSync(BUNDLE, path.join(out, 'evidence.json'))
    },
  }
}

export default defineConfig({
  plugins: [react(), tailwindcss(), evidenceBundle()],
  server: { port: 5173, strictPort: true },
})
