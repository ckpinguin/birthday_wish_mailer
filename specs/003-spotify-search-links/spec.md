# Feature Specification: Spotify Search Links

**Feature Branch**: `003-spotify-search-links`

**Created**: 2026-07-15

**Status**: Draft

**Input**: User description: "Replace the Spotify Web API track lookup with credential-free Spotify search links. Spotify's February 2026 policy blocks Web API access for developers without Premium, so the app can no longer resolve direct track URLs. Instead, build Spotify search links (https://open.spotify.com/search/<song title and artist>) for the birthday chart songs — no API calls, no credentials. The SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET keys should no longer be required in the secrets file. The song P.S. block in the email keeps its current look; each song just links to the Spotify search results instead of the exact track page. Link building must never break the greeting send (graceful degradation stays)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Song Links Work Again, Without Any Spotify Credentials (Priority: P1)

Since Spotify's February 2026 policy change, the app's Spotify lookups are blocked for owners without a Premium subscription, so birthday emails currently list the chart songs without links. With this feature, every chart song in the birthday P.S. links to the Spotify search results for that song (title plus artist). Anyone clicking the link — the owner during review, or the birthday person after forwarding — lands on Spotify's search page with the song findable at a glance. No Spotify account, subscription, or registered application is involved in producing the links.

**Why this priority**: This restores the feature the policy change broke — clickable song links are the whole point of the enrichment. Everything else in this spec is cleanup that follows from how the links are made.

**Independent Test**: Run a test send for a birthday person born after 1958 and click each song link in the received email: each opens Spotify search results where the listed song is visible.

**Acceptance Scenarios**:

1. **Given** a birthday person with chart entries for their birth date, **When** the email is generated, **Then** every listed song carries a link to the Spotify search results for that song's title and artist.
2. **Given** a song whose title or artist contains spaces or special characters (e.g. `&`, apostrophes, accented letters), **When** the link is built, **Then** the link opens correctly and searches for the full title and artist.
3. **Given** any problem while building a link for one song, **When** the email is composed, **Then** the greeting still goes out, listing that song without a link (never aborting the send).

---

### User Story 2 - Setup Works Without a Spotify Developer Account (Priority: P2)

The owner sets up (or re-deploys) the mailer without creating any Spotify developer application: the two Spotify credential entries are no longer required in the secrets file, and a run with a secrets file that never mentions Spotify completes normally. Owners with old secrets files don't need to touch them — leftover Spotify entries are simply ignored.

**Why this priority**: Valuable simplification (two secrets fewer, no developer-dashboard dance), but only meaningful once the links themselves work credential-free (P1).

**Independent Test**: Remove `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` from the secrets file and run a test send: the run completes and the email contains linked songs as in User Story 1.

**Acceptance Scenarios**:

1. **Given** a secrets file without any Spotify entries, **When** the app starts, **Then** no configuration error is raised and the run proceeds normally.
2. **Given** a secrets file that still contains the old Spotify entries, **When** the app runs, **Then** the entries are ignored and behavior is identical to a file without them.
3. **Given** the project documentation, **When** a new owner follows the setup instructions, **Then** no Spotify credentials or developer account appear as requirements.

---

### Edge Cases

- Song title/artist with characters that are unsafe in links (`&`, `?`, `/`, `#`, umlauts, apostrophes): the link must encode them so the search query arrives intact.
- The chart lookup itself fails or the birth year predates the charts: existing behavior unchanged — the P.S. block is shortened or omitted; this feature adds no new failure mode there.
- Opening a search link without being logged in to Spotify: the results page is still viewable; playing a song may prompt for a (free) login — acceptable, since that is Spotify's floor for playback.
- Extremely long title + artist combinations: the link must remain a single working URL.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Each chart song in the birthday P.S. MUST link to the Spotify search results for that song, with the search query composed of the song's title and artist.
- **FR-002**: Link creation MUST NOT require any credentials, registered application, account, or network call — it is pure text construction from data the app already has.
- **FR-003**: The Spotify credential entries (`SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`) MUST no longer be required configuration; a secrets file without them MUST pass validation, and leftover entries MUST be ignored.
- **FR-004**: The P.S. block MUST keep its current appearance: same introductory text, same list format, same YouTube fallback hint; only the link targets change from track pages to search pages.
- **FR-005**: Titles and artists containing characters with special meaning in links MUST be encoded so the resulting link is valid and the search receives the full, unaltered query text.
- **FR-006**: A failure to build a link for a song MUST NOT prevent the greeting from being sent; the affected song falls back to appearing without a link (existing graceful-degradation principle).
- **FR-007**: Setup documentation MUST no longer list Spotify credentials as required and MUST reflect that song links point to search results.

### Key Entities

- **Chart song**: A top-chart entry for the birthday date — title, artist, and (new) a search link derived purely from those two fields; previously carried an exact track link resolved via the now-blocked lookup.
- **Secrets configuration**: The owner-maintained credentials file; loses its two Spotify entries from the required set, shrinking the mandatory keys to mail delivery + sender identity + owner review address.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of chart songs in generated emails carry a clickable link again (currently 0% for owners without Premium, since the lookup is blocked).
- **SC-002**: For a sample of at least 10 historical chart songs, the linked search page visibly contains the intended song in at least 9 cases.
- **SC-003**: A complete run succeeds with a secrets file containing zero Spotify-related entries; new-owner setup requires two fewer secret values and no third-party developer registration.
- **SC-004**: Zero send failures attributable to link building across any run.

## Assumptions

- A Spotify search-results link is an acceptable replacement for an exact track link: one extra click/glance for the reader, in exchange for working links without any subscription. The email's existing YouTube hint already covers readers without Spotify.
- Spotify's public search page remains reachable without login for viewing results; playback may require a free account — accepted as Spotify's own floor.
- The blocked exact-track lookup is removed rather than kept dormant behind a switch: the policy change is not expected to reverse for hobby-scale apps, and keeping dead code contradicts the project's simplicity principle. Direct-track resolution can return as a future feature if circumstances change.
- Owners are not required to clean old Spotify entries out of their secrets files; unknown entries continue to be ignored.
- Run logs stop reporting per-song lookup outcomes (there are no lookups anymore); chart-lookup logging is unchanged.
- The owner-review routing introduced by feature 002 is untouched; this feature only changes what the song list links to.
