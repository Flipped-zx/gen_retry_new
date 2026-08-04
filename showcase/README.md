# Gen-Retry Trajectory Archive

Interactive showcase for four canonical Gen-Retry trajectories. The site compares
the first and submitted images, exposes the full attempt lineage, and contrasts the
initial execution instruction with the final retry instruction.

## Data Provenance

All displayed image attempts and metrics come from
`runs/phase7_flow_dppo200_fresh8_v1`. The site copies selected images into
`public/trajectories/` so the deployed build has no runtime dependency on the run
directories. Prompt text is copied from canonical actions, not raw teacher output.

## Commands

Requires Node.js `>=22.13.0`.

```bash
npm install
npm run dev
npm test
```

`npm test` builds the vinext/Cloudflare Worker output and checks the rendered page,
metadata, canonical content, and required trajectory assets.

