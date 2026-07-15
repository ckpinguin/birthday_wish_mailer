# Feature Specification: Owner Review Routing

**Feature Branch**: `002-owner-review-routing`

**Created**: 2026-07-15

**Status**: Draft

**Input**: User description: "Generate the email, but always send it to OWNER_RECIPIENT (newly defined in the secrets). I want to add a little personal touch before sending it to the real receiver. I will need the receivers's address on that email too. You can decide if you want to send the Mail content as attachment or inline."

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Greetings Are Delivered to the Owner, Never Directly to the Birthday Person (Priority: P1)

On a day with one or more birthdays, the scheduled run generates each greeting exactly as today (personalized text, image, chart extras) but delivers every one of them to the owner's review address (`OWNER_RECIPIENT`, newly defined in the secrets file) instead of the birthday person's own address. The birthday person receives nothing from the system; the owner reviews each greeting, adds a personal touch, and forwards it manually.

**Why this priority**: This is the core behavioral change. Without the redirection, the personal-touch workflow is impossible and recipients would keep getting the unreviewed automated mail.

**Independent Test**: Configure `OWNER_RECIPIENT`, run the app on a date with a due birthday, and confirm the greeting arrives only in the owner's inbox and the birthday person's inbox stays empty.

**Acceptance Scenarios**:

1. **Given** a real (non-test) run and one person has their birthday today, **When** the run completes, **Then** exactly one greeting email is delivered to `OWNER_RECIPIENT` and none to the birthday person's address.
2. **Given** three people share today as birthday, **When** the run completes, **Then** the owner receives three separate emails, one per birthday person.
3. **Given** `OWNER_RECIPIENT` is missing or empty in the secrets file, **When** a real run starts, **Then** no email is sent at all and the run reports a clear configuration error.

---

### User Story 2 - The Owner Can See Who the Greeting Is For (Priority: P2)

Each email the owner receives clearly states the intended recipient's name and email address, so the owner knows where to forward it without looking anything up. When several birthday emails arrive on the same day, the owner can tell them apart before even opening them.

**Why this priority**: Redirection alone is useless if the owner has to open the CSV to figure out each greeting's destination. The address on the email is what makes the manual forward practical.

**Independent Test**: Trigger a run for a known birthday person and verify the received email shows that person's name and email address in a visible, copyable form, and that the subject line identifies the person.

**Acceptance Scenarios**:

1. **Given** a greeting for a birthday person, **When** the owner opens the email, **Then** the intended recipient's name and email address are displayed and can be copied as plain text.
2. **Given** two greetings arriving the same day, **When** the owner views their inbox list, **Then** each email's subject identifies which birthday person it belongs to.

---

### User Story 3 - The Greeting Is Forward-Ready (Priority: P3)

The greeting content appears inline in the email body — not as an attachment — rendered exactly as the birthday person would see it (image, formatting, chart extras included). The routing information (intended recipient's name and address) is visually separated from the greeting itself, so the owner can add a personal line and forward the message without the recipient seeing leftover routing details as part of the greeting.

**Why this priority**: This determines how smooth the owner's daily workflow is. The redirection (P1) and address display (P2) already deliver the essential value; this story removes friction.

**Independent Test**: Receive a review email, forward it to a test mailbox after adding a personal sentence, and confirm the greeting renders correctly in the forwarded copy with the routing block clearly distinguishable from the greeting.

**Acceptance Scenarios**:

1. **Given** a review email in the owner's inbox, **When** the owner opens it, **Then** the full greeting is visible inline without opening any attachment, and it renders identically to what the birthday person would have received.
2. **Given** a review email, **When** the owner inspects it, **Then** the routing information is set apart from the greeting content (e.g., clearly above or below it) rather than mixed into the greeting text.

---

### Edge Cases

- `OWNER_RECIPIENT` missing, empty, or malformed in the secrets file: the run must fail fast (with exit-2) with a clear error before any email is sent (a silent fallback to direct sending would defeat the feature's purpose).
- Multiple birthdays on the same day: one review email per person, each unambiguously labeled; no combining into a single digest.
- Enrichment failures (charts, song links, image issues): existing graceful-degradation behavior is unchanged — the plain greeting still goes to the owner.
- Test mode: continues to deliver to the test recipient, but with the same review format (routing block, subject labeling) so the new layout can be verified before real runs.
- A birthday person with a missing/invalid email in the CSV: existing filtering rules apply unchanged; nobody without a valid address produces a review email claiming otherwise.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: In real (non-test) runs, the system MUST deliver every generated birthday greeting to the owner review address (`OWNER_RECIPIENT`) instead of the birthday person's email address. The birthday person MUST NOT receive any email from the system.
- **FR-002**: The owner review address MUST be read from the secrets configuration under the key `OWNER_RECIPIENT`, alongside the existing credentials, and MUST never be hardcoded or committed (per constitution Principle II).
- **FR-003**: If `OWNER_RECIPIENT` is missing or empty, a real run MUST stop with a clear configuration error before sending any email.
- **FR-004**: Each review email MUST display the intended recipient's first name and email address in a visible, plain-text-copyable form within the message.
- **FR-005**: Each review email's subject MUST identify the intended birthday person, so multiple same-day emails are distinguishable in the inbox list.
- **FR-006**: The greeting content MUST be included inline in the email body (not as an attachment) and MUST be identical in content and rendering to what the birthday person would have received, including the embedded image and any chart extras.
- **FR-007**: The routing information (intended recipient details) MUST be visually separated from the greeting content so the owner can distinguish and exclude it when forwarding.
- **FR-008**: Test mode MUST keep delivering to the test recipient, using the same review format as real runs, so the new layout can be verified per constitution Principle III.
- **FR-009**: For every send, the run log MUST record both the actual delivery address (owner) and the intended birthday person, so an unattended run remains fully reconstructable from logs (per constitution Principle V).

### Key Entities

- **Owner review address (`OWNER_RECIPIENT`)**: A new entry in the secrets configuration; the sole delivery destination for all generated greetings in real runs.
- **Review email**: The message delivered to the owner; composed of the unmodified greeting (inline) plus a routing block (intended recipient's name and email address) and a subject that names the birthday person.
- **Intended recipient**: The birthday person from the CSV; their address is no longer a delivery target but becomes display data on the review email.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: Across any real run with N due birthdays, exactly N emails arrive at the owner review address and zero emails arrive at birthday persons' addresses.
- **SC-002**: For 100% of review emails, the owner can determine the intended recipient's name and email address from the email alone, without consulting the CSV or any other source.
- **SC-003**: The owner can review, personalize, and forward a greeting in under 2 minutes per email, with no reformatting needed for the greeting to render correctly for the final recipient.
- **SC-004**: A run with a missing owner review address sends zero emails and its logs state the exact configuration problem.

## Assumptions

- **Inline over attachment** (decision delegated by the user): the greeting goes inline in the email body. Rationale: the owner can verify rendering at a glance, and forwarding an inline HTML body preserves the greeting for the final recipient far better than expecting them to open an attachment.
- The manual forward is the owner's responsibility: the system does not track, remind about, or automate the second send to the real recipient. If the owner never forwards, the greeting is never delivered — accepted by design.
- `OWNER_RECIPIENT` is treated as a required configuration entry for real runs; test runs continue to rely on the existing test-recipient configuration for delivery.
- The existing BCC behavior, recipient CSV format, `active`-flag filtering, German templates, and enrichment pipeline are unchanged by this feature.
- Redirection to the owner applies permanently to all real runs (not an optional mode); direct-to-recipient sending is intentionally removed from the workflow.
