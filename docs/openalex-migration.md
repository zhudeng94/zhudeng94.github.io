# OpenAlex citation updates

This migration changes the citation source, not the curated paper catalogue or Altmetric provider. Google Scholar numbers must never be presented as OpenAlex counts. The old Scholar crawler is retained only for historical reference; the renamed scheduled workflow no longer invokes it.

## Identity and scope

The author's published CV identifies ORCID `0000-0002-6409-9578`; OpenAlex resolves it to `A5088725316`, Zhu Deng (University of Hong Kong). Each update verifies both identifiers. A changed resolution stops the update for manual review, rather than silently switching author clusters.

The homepage's total citations, h-index and indexed-work count are **OpenAlex author-profile metrics**. They are not sums over the curated publication list. OpenAlex's author aggregate and work search can lag one another; the snapshot records `works_count` and `retrieved_works_count` separately. Work search is complete only when every result reported by its own `meta.count` has been received with unique IDs and the expected author attribution.

Per-paper citations use the existing Google Sheet's curated DOI and title. OpenAlex DOI lookups are batched, independent of author clustering. A match requires the returned DOI to match exactly after URL/case normalization and the title to match after Unicode/case/punctuation normalization. Aliases, missing works, duplicate DOI results and title mismatches show **OpenAlex citations: N/A**, never zero, guessed matches or old Scholar values. Genuine zero counts remain zero. Empty catalogues, repeated response IDs, zero exact-DOI coverage or zero title-confirmed coverage abort rather than replacing the entire list with N/A. No automatic author-profile merging is performed.

## Operation and credential policy

`Get OpenAlex Citation Data` (historical filename `google_scholar_crawler.yaml`) runs daily at 08:00 UTC or manually. It stores only `openalex_data.json` in the existing `google-scholar-stats` branch. All `gs_data*.json` files remain untouched as historical data. The existing branch name avoids bootstrap races or a new branch-creation permission. A successful run triggers `Generate publications`; the independent 09:00 UTC publication schedule remains.

OpenAlex currently allows basic keyless requests and page-based pagination up to 10,000 results. This author's workload is small. `OPENALEX_API_KEY` is optional; if later needed the owner can configure a GitHub Actions secret, but this change does not create an account, obtain or store a key. The code sends an existing key only in the Authorization header and never logs it. Errors stop the job without retry loops, response-body logging or a fallback to Scholar. No proxy or CAPTCHA handling is used. See https://help.openalex.org/api/authentication/ for current limits and pricing.

The complete snapshot is validated before an atomic local replace. No publishing step runs if retrieval fails. Publication generation completes all API lookups and rendering before writing outputs; failures retain both previous generated files. A non-fast-forward git push fails rather than forcing away concurrent work.

## Review and rollout

This is a draft migration, not authorization to merge/deploy. After approval and merge, run `Get OpenAlex Citation Data` on `main` once, then verify the new snapshot, generated DOI/title match coverage and Pages deployment. The homepage displays N/A until its first validated OpenAlex snapshot exists; it does not fall back to cached Scholar counts. See the dated audit for unresolved metadata and profile clustering issues. These require explicit reviewed data corrections, not fuzzy matching.

Tests: `python -m unittest discover -s tests -v`; `python -m compileall -q publication_generator openalex_crawler tests`.
