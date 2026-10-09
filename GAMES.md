# Heaven.gg — combined game intelligence hub

**Canonical repository:** https://github.com/fengie/Heaven.gg. Two games, one independently sourced and tested frontend, one GitHub repository.

| Game | Research source | Browser view |
| --- | --- | --- |
| **Celtic Heroes** | Original ch_tables/, data/, docs/, tests/ | Build explorer (327 public samples), equipment and historical boss intelligence |
| **AION 2** | apps/aion2-value-atlas/ and its own tests/data | Full Atreia Atlas shop/Mileage comparison dashboard |

## Run and ship

- npm run test:web verifies the unified site and its source identity.
- npm run build creates deterministic dist/ from tracked files, including a byte-identical copy of the AION browser app.
- The Heaven.gg Website workflow (.github/workflows/site.yml) validates PRs, then on verified main publishes an atomic GitHub Pages artifact. It does not deploy from a chat copy, separate AppDeploy instance, or unreviewed web edits.
- GitHub Pages URL after **successful** publication: https://fengie.github.io/Heaven.gg/. The URL is not evidence of live availability until a Pages deployment and browser check pass.
- GitHub Pages may require the repo Settings → Pages → Build and deployment → GitHub Actions selection; a 404 or deployment 404 must be recorded and repaired rather than claiming live service.

## Invariants

- Celtic Heroes CLI, datasets and unit tests remain in place. The browser reader exposes public saved-build calculator values, not calibrated or measured live DPS. Boss figures are historical and released gear claims require evidence.
- AION 2 shop data is a dated, limited October 9 Global snapshot. Do not infer extra Mileage on Quna spending or guaranteed future prices; user values skins, collecting and long-term play above meta.
- No proprietary game art bundled. No login, paid purchases or scheduled agents.
- .heaven/update-policy.json follows this renamed repository exactly. See web/DEPLOYMENT.md for release controls.
