# Catalog proposal review gate

No clinical tests, aliases, units, panels or ranges are added by this release.
`docs/catalog/expansion-sources.md` is unchanged.

Run `python manage.py validate_catalog_proposals path/to/proposals.json` to perform
an offline structural check. This command does not connect to sources, install
anything or write to the database. Passing does not verify clinical truth or
approve import. No automatic installer is provided.

JSON root: `schema_version` (integer 1) and `proposals` (1–100 objects).
Each object requires exactly these string fields:

- `code`, `name`: proposed identity, never guessed from abbreviations.
- `specimen`, `method`: empty if the source does not specify them.
- `source_url`: HTTPS reference, without credentials.
- `source_title`, `source_excerpt`: traceable supporting evidence.
- `accessed_on`: ISO date YYYY-MM-DD, not in the future.
- `reviewed_by`, `reviewed_on`: explicit reviewer and non-future review date,
  not earlier than access.
- `decision`: exactly `accepted`.

Files are limited to 1 MiB. Duplicate JSON keys, duplicate proposed codes,
unknown fields and missing evidence are rejected. This is a local file checker,
not an authorization or source-authenticity system. Reviewer names and decisions
are assertions, not authenticated signatures. Existing catalog collisions and
identity ambiguity must be checked by the reviewer before a separate code change.

Human release checklist:
1. Open the original source and confirm the excerpt and precise identity.
2. Resolve free/total, direct/calculated, assay, specimen and method distinctions.
3. Do not invent units, reference intervals, specimen defaults or aliases.
4. Compare with existing tests and get explicit owner approval for additions.
5. Submit separately reviewed code, source documentation and dedicated tests.
6. Preview installation against a disposable database before approved deployment.

The automated test fixtures use example.org and synthetic identities only. They
are not clinical sources and must never become catalog entries.
