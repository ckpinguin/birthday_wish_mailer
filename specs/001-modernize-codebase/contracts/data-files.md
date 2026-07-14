# Data File Contracts

Files the maintainer edits by hand. Formats are frozen (spec assumption: no
migration of recipient data).

## birthdays.csv / TEST_birthdays.csv

CSV with header row, columns exactly:

```csv
firstname,gender,email,year,month,day,active
Anna,f,anna@example.org,1975,7,14,1
```

- `gender`: `f` selects the feminine salutation; any other value the masculine.
- `year,month,day`: integers; incomplete or unparsable → row skipped (warning).
- `active`: `1` to include the row; anything else excludes it.
- Extra columns are ignored; column order is irrelevant (header-based access).
- File is untracked (contains personal data — Principle II).

## .secret.json

JSON object with the keys listed in data-model.md → AppConfig. Untracked.
Unknown keys are ignored (forward compatibility). `PROXY_HOST`/`PROXY_PORT` are
no longer read.

## letter_templates/letter_{1..3}.txt

UTF-8 plain text, German, containing the literal placeholders `[TITLE]`,
`[NAME]`, `[SENDER]`. Adding a template requires updating the template count in
one place in the code (content module constant).

## images/small_bday{1..3}.png

PNG files embedded inline. Same one-place constant applies.
