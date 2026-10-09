# Live publication receipt — 2026-10-09

- User-visible URL: https://atreia-atlas-4ko9ii.v2.appdeploy.ai/
- Host: AppDeploy; app ID: `atreia-atlas-4ko9ii`
- AppDeploy initial snapshot: `1791580873159`
- Readback: `ready`; no reported frontend or network errors. QA screenshot URLs present for desktop and mobile, but independent pixel review not completed.
- GitHub `fengie/aion2-value-atlas`: **NOT CREATED** by connected action (no GitHub repository-create action exposed).
- No source-to-GitHub deployment, GitHub Pages, CI gate or Heaven Toolbox repo autoupdate live verification. This preview is independent of repository hosting. No recurring/scheduled agents created.

## Publishing to GitHub after provisioning

1. Create a **new, empty** repository `fengie/aion2-value-atlas` with appropriate visibility and owner permissions. Do not initialize with README to avoid conflicting history.
2. Restore the supplied Git bundle with `git clone aion2-value-atlas.bundle aion2-value-atlas` (or use the ZIP and create history) and set remote to the exact verified URL.
3. Install the official Heaven Toolbox repo auto-update contract via its installer on a trusted machine and confirm signed/admitted CI; preserve protected branch gates.
4. Configure static hosting from the deterministic `index.html` artifact and verify deployed SHA and rollback behavior before declaring production auto-updates.
5. Record actual remote main revision, CI, owner and runtime acceptance evidence.