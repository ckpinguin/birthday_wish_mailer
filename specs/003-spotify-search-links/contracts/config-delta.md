# Contract: Configuration Delta

Delta against the frozen feature-001 contracts
([data-files.md](../../001-modernize-codebase/contracts/data-files.md)) and
feature 002's [cli-and-config.md](../../002-owner-review-routing/contracts/cli-and-config.md).
CLI flags, exit codes, CSV formats, templates, images: all unchanged.

## `.secret.json`

| Key | Before | After |
| ----------------------- | -------- | ---------------------------------------------- |
| `SPOTIFY_CLIENT_ID` | required | **not read** — leftover entries are ignored |
| `SPOTIFY_CLIENT_SECRET` | required | **not read** — leftover entries are ignored |
| `MAILHOST`, `PORT`, `LOGIN`, `PASSWORD`, `FROM_ADDR`, `SENDER` | required | required (unchanged) |
| `OWNER_RECIPIENT` | required for real runs (002) | unchanged |
| `BCC_ADDR`, `TEST_RECIPIENT` | optional | unchanged |

A `.secret.json` that never mentions Spotify is now fully valid (FR-003).
No migration needed: owners may delete the two entries or leave them —
behavior is identical either way (unknown keys were already ignored).

## Startup behavior

- No validation error may reference Spotify in any way after this feature.
- Everything else (missing-key errors, exit codes 0/1/2, feature 002's
  `OWNER_RECIPIENT` guard) is unchanged.

## Documentation

README's required-keys list drops the two Spotify entries and no longer
instructs owners to register a Spotify developer application; it notes that
song links open Spotify search results (FR-007).
