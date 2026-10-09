# Heaven.gg — GitHub-first web release contract

## Product and provenance
Target repo: fengie/Heaven.gg (main). Web frontend in web/, built using node web/build.mjs with zero npm dependencies. Static output: dist/. No credentials required for local build, and no live scraping, payments, trackers or private character authentication.

- CH sources: data/reference/codex_published_build_catalog.json, data/catalog/priority_gear_lookup.json, data/reference/raid_boss_resistances_2026_10_08.json.
- AION app source: apps/aion2-value-atlas/index.html, copied byte-for-byte. Its canonical editable JSON and generator remain in its directory.
- Build identity: dist/version.json records the exact GITHUB_SHA during CI. Changes to any game dataset require a new GitHub commit, validation and publication.
- No runtime process updates itself: GitHub Pages serves a newly published artifact, with GitHub Actions release/job history for rollback. This is a web-native release/update strategy. Separate Toolbox worker auto-consumption still must be verified outside site CI.

## CI and deployment sequence
1. npm run test:web: isolated build, deterministic output, two accessible game tabs, JSON schema/coverage/provenance, copied AION app and browser JS parser.
2. npm run build: generate dist/ from GitHub source only.
3. .github/workflows/site.yml checks dist/version.json against GITHUB_SHA and uploads the tested directory.
4. Only on main, GitHub Pages deploys that exact artifact. The standard URL is https://fengie.github.io/Heaven.gg/, unless a custom domain is separately configured.
5. Verify the URL serves the portal, /Heaven.gg/version.json matches main SHA, AION loads in its second tab, and the CH catalog returns 327 records; log link to successful GitHub Pages run. If Pages is not enabled, activate GitHub Actions as its source in Settings → Pages and rerun a bounded dispatch. Never claim the app is live solely because source was merged.

## Recovery and security
On failed publication, the old Pages artifact remains authoritative, and workflow reports failure. Restore the previous verified GitHub commit through protected history (prefer revert PR) and redeploy; do not force-push. No untrusted upload or write APIs. User-supplied strings are escaped before display and outgoing Codex source URLs are restricted to HTTPS. No external payment links or automation.

## Coverage limitations
Celtic Heroes: user-authored build samples and historical game record extraction, not exact live meta. AION 2: snapshot October 9, 2026 and incomplete shop coverage, not refreshed automatically. The site never combines incompatible games' economies or labels predictions verified. Store source URLs and dates with observations before expanding.

No scheduled or recurring agent was created. Github-first is mandatory; the former AppDeploy AION preview is not part of this release pipeline.
