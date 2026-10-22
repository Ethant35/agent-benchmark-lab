# Full DeepSeek V4.1 Flash 1017 benchmark
Author: Ethan  
Date: 2026-10-22

**Raw result: 8/12 PASS (66.7%), 3 FAIL, 1 TIMEOUT. Observed key charge: $0.014957188, about 1.50 cents.** This excludes the earlier smoke tests.

Installed Agent Benchmark Lab v1.0.1; exact requested alias `deepseek/deepseek-v4.1-flash-1017`. Generation metadata names the served snapshot `deepseek/deepseek-v4.1-flash-20261017`. One provider-executed attempt per task, streaming, low reasoning, at most eight requests and 2,048 output tokens per request. The effective task deadline is 30 seconds: the runner takes the smaller of the task and configuration limits. No prompt, fixture, verifier, or implementation changes and no inference retries.

| Task | Outcome | Requests started | Completed-response cost USD |
|---|---|---:|---:|
| bugfix-interval-merge | PASS | 4 | 0.000425224 |
| bugfix-rounding | PASS | 5 | 0.000782350 |
| extraction-contacts | PASS | 5 | 0.000878362 |
| extraction-invoices | PASS | 4 | 0.000432504 |
| feature-order-filter | FAIL | 6 | 0.001737944 |
| feature-slugify | PASS | 7 | 0.002396870 |
| multistep-document-index | FAIL | 8 | 0.001835684 |
| multistep-ledger | TIMEOUT | 6 | 0.002174920 + incomplete request |
| navigation-config | FAIL | 4 | 0.000306338 |
| navigation-routes | PASS | 4 | 0.000852736 |
| refactor-csv-summary | PASS | 7 | 0.001668826 |
| refactor-text-stats | PASS | 5 | 0.001034570 |

## Failure analysis

- **feature-order-filter:** Outputs one JSON object per line; verifier requires one JSON array. The prompt does not explicitly specify an array.
- **multistep-document-index:** Reached the 8-request limit. Verifier also rejects docs key name instead of file, and manifest key files instead of sha256. Those exact keys are absent from the prompt; the fixture is only a TODO.
- **multistep-ledger:** Reached the 30-second task deadline during a provider response. The task deadline overrides the longer configured maximum; final request usage is unavailable.
- **navigation-config:** Correct facts and JSON types. Verifier rejects the explanation because it says cache enabled rather than the exact keyword caching. This is an evaluator false negative.

These are the unchanged verifier outcomes, not a clean estimate of model capability. In particular, the configuration-navigation failure is an evaluator defect, and two other failures involve unstated output-schema expectations. The corpus should clarify those contracts before model comparisons. The original failures are retained; none was relabeled as passing.

## Cost and execution evidence

65 requests started; 64 complete responses. Their costs total $0.014526328 and independently match all 64 OpenRouter generation records. The key-usage increase is $0.014957188, leaving $0.000430860 beyond the complete records. That difference is consistent with the interrupted request, whose generation ID was lost, but it cannot be independently attributed to that generation. Concurrent use of this same key, if any, would affect the key delta. Two final key readings agreed.

The timeout left an unknown request cost, so the runner blocked four later tasks before any provider calls. After checking actual key charges, those four untouched tasks ran once in a separate run. All four initial zero-request blocks remain in `summary.json`; they are not additional model attempts. The second run had a $0.10 local reserve, within the original $0.20 total ceiling given the verified prior charge. No account limits were changed.

Complete-response token totals are lower bounds because the interrupted response is missing: 121,618 input, 21,343 output, and 75,136 cached input tokens. Cached input is included in input tokens. Model-executed trials took 222.5 seconds in aggregate; all 16 infrastructure records, including the four zero-request blocks, took 231.0 seconds. These durations exclude orchestration and cost reconciliation.

[Trial summary](summary.json), [per-response usage](provider-usage.json), [generation records](generation-ledger.json), [cost reconciliation](cost-reconciliation.json), [initial configuration](config.json), and [remaining-task configuration](remaining-config.json) contain the detailed evidence. The two CLI transcripts preserve original statuses. Full raw traces, verifier files and opaque workspace archives remain locally under `.abl/full-deepseek-1017/`.

All trial cleanup-error lists are empty. Container and volume inventories were empty before VM shutdown. No GitHub Actions or workers were used. Credentials are absent from saved evidence.
