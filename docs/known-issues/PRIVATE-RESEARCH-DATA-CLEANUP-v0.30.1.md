# v0.30.1 — Private Instance Data Cleanup

**Date:** 2026-05-31
**Scope:** Removed `research/` from public repository history
**Method:** `git filter-repo --path research/ --invert-paths`
**Performed by:** Hermes Agent (Nous Research)

## Background

Instance-level research data (opportunity signals, market scan notes, watchlist configuration) was inadvertently committed to the public repository across 6 commits between 2026-05-26 and 2026-05-31, spanning tags v0.10 through v0.30.

No API keys, secrets, or credentials were exposed (verified via full history scan).

## Actions Taken

| # | Action | Status |
|:-:|:-------|:-------|
| 1 | Full local backup to `~/Desktop/backup-ai-company-os-pre-cleanup/` | ✅ |
| 2 | `.gitignore` updated to exclude `research/` | ✅ |
| 3 | `git filter-repo --path research/ --invert-paths` — rewrote 191 commits | ✅ |
| 4 | Remote backup tags (`backup/*`) deleted from remote and locally | ✅ |
| 5 | 26 old remote tags deleted (v0.10—v0.30, all affected) | ✅ |
| 6 | 25 old GitHub Releases deleted | ✅ |
| 7 | 26 tags force-pushed with clean history | ✅ |
| 8 | v0.30 source zip downloaded and verified: no `research/` files | ✅ |
| 9 | Release hygiene skill (`ai-company-os-release`) updated to v2.0 | ✅ |

## Scope

- **Files removed:** 12 files across `research/opportunity-pool/`, `research/source-notes/`, `research/weekly-briefs/`, and `research/watchlist.yaml`
- **Commits removed:** 6 commits (out of 191 total)
- **Tags rebuilt:** 26 (v0.10—v0.22.1, v0.26—v0.30)
- **GitHub Releases rebuilt:** 25 (all affected tags except v0.14.2 which had no release)

## Verification

```bash
# Local repository
git ls-files research/           → 0
git log --all -- research/       → 0 commits
git tag | while read t; do
  git ls-tree -r "$t" -- research/ → no output (clean)
done

# Remote release zip
gh release download v0.30 --archive=zip
# Unzip → grep research/ → 0 matches
```

## Impact

- All commit hashes changed — collaborators must re-clone
- 228 existing forks retain old history (cannot be recalled)
- Local working copy unaffected
- Old release zips may persist in GitHub's CDN cache but are unreachable from the release page

## Prevention

The Three-Layer Git Boundary is now enforced in the release workflow (skill v2.0):
- **Layer 1** (AI-Knowledge-OS) and **Layer 2** (research/) verified before every release
- Historical cross-check (`git log --all`) added to hygiene checks
- Neutral public narrative maintained in README and Release Notes
- Backup tags never pushed to remote
- Release zip verification after every tag rebuild
