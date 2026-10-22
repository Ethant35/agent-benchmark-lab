# Bundled benchmark corpus

Twelve independent task bundles use versioned YAML contracts, fresh fixture trees, deterministic reference actions and hidden verifiers. The reference runner performs real file and shell operations; it does not simulate provider responses. Agent-produced code runs only inside the task container. The root-owned verifier checks observable outputs through subprocesses running as an unprivileged user.

## Tasks

- bugfix-rounding (Bug fixing): Repair format_price in app.py: use exact decimal half-up rounding to 2 places. Preserve CLI: python app.py AMOUNT. Cover negative and tie cases.
- bugfix-interval-merge (Bug fixing): Fix merge_intervals in app.py. Read JSON pairs on stdin; merge overlapping or touching intervals, sort by start and print compact JSON. Keep the CLI.
- feature-order-filter (Feature implementation): Implement filter_orders.py: read orders.json; filter by required --status and numeric --minimum total (inclusive); emit matching full records as compact JSON in input order.
- feature-slugify (Feature implementation): Implement slugify(text) in slugify.py and stdin CLI. Normalize accents to ASCII, lowercase, collapse non-alphanumeric runs to hyphen, trim hyphens; punctuation-only input returns empty.
- navigation-config (Repository navigation): Inspect settings.py and write answer.json with its requested configuration facts, exact source path, and a concise explanation. Do not modify settings.py.
- navigation-routes (Repository navigation): Inspect routes.py and write route facts, exact source path, and a concise explanation, preserving method declaration order. Do not change source.
- refactor-csv-summary (Refactoring): Refactor summary.py into parse_rows(path) and summarize(rows) helpers while preserving behavior. CSV columns sku, quantity, unit_price; duplicate SKUs accumulate extended amounts rounded to cents; negative quantities remain valid. CLI prints sorted-key JSON.
- refactor-text-stats (Refactoring): Refactor text_stats.py into tokenize(text) and count_words(tokens). Preserve case-folded whitespace tokens including attached punctuation; output sorted JSON counts and total.
- extraction-invoices (Structured information extraction): Extract invoices.json into invoices_out.json. Each output has exactly invoice_id, vendor, date, amount_cents. Preserve order; convert decimal amount strings exactly.
- extraction-contacts (Structured information extraction): Extract contacts.txt to contacts.json with exact name, email, phone fields. Keep order and original phone text; lowercase emails; omit heading.
- multistep-ledger (Multistep tool use): Implement pipeline.py with dependent normalize, total, manifest steps. normalize reads CSV and writes transactions.json with lowercase account and cents. total reads it and writes totals.json preserving first-seen account order. manifest hashes both prior files with SHA-256 and records row_count. Execute each step in order.
- multistep-document-index (Multistep tool use): Implement indexer.py with three dependent commands: scan reads files.txt and writes docs.json with names and byte counts; index reads docs.json and writes index.json mapping lowercase punctuation-trimmed words to sorted filenames; manifest hashes docs.json and index.json and records document_count. Run scan, index, manifest in order.

Counts: bug fixing 2; feature implementation 2; repository navigation 2; refactoring 2; structured extraction 2; multistep tool use 2.
