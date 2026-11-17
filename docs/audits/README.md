# Historical test-suite audits

The [November 13, 2026 report](test-suite-audit-2026-11-13.md) and its
[CSV inventory](test-suite-audit-2026-11-13.csv) record the investigation at
`d6802406feed90f6c4a7bdedde8cebfeafca4068` (PR #195 merge). They are preserved
byte for byte from the previously untracked owner-approved audit outputs.
Their test counts, failures, recommendations and descriptions of untracked files
refer to that revision and date, not the current checkout. Publishing them does
not approve their recommendations or authorize test execution or cleanup.

These reports are being added on `codex/track-preserved-project-metadata`, pending
PR review and merge. See [LOCAL_TESTING.md](../LOCAL_TESTING.md) and
[AGENTS.md](../../AGENTS.md) for current validation policy. Historical references
to these reports being untracked remain unchanged.

The empty [.gdignore](.gdignore) keeps this documentation directory out of Godot's
resource import scan. The pre-existing `test-suite-audit-2026-11-13.csv.import`
mistakenly configures the inventory as translation data. It remains unchanged on
disk and is excluded by one exact path in [.gitignore](../../.gitignore); the
existing generated translations remain ignored and preserved. No import-sidecar,
translation, cache or other owner file is deleted by this housekeeping change.

Exact-path rules in [.gitattributes](../../.gitattributes) preserve the two audit
files' original bytes, including the CSV's UTF-8 BOM and mixed record/field line
endings. The reports were checked for credentials and personal-profile paths
before publication; no redactions were required. No audit commands or Godot
processes were run as part of publishing these historical documents.
