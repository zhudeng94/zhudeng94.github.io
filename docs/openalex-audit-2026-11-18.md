# OpenAlex migration audit (2026-11-18)

## Identity and scope

The owner's published CV links ORCID `0000-0002-6409-9578` to Scholar ID `bzZYiBgAAAAJ`:
https://zhudeng.top/files/Zhu%20Deng_CV_2511.pdf

OpenAlex ORCID resolution returned `A5088725316`, Zhu Deng, University of Hong Kong. This is an identity anchor, not proof that every work in that profile is correct.

Live profile snapshot: 81 works, 8,551 citations. The complete works endpoint returned 80 records (meta.count=80), 80 unique DOIs, summed citations 8,550. This one-record discrepancy is an upstream inconsistency; never substitute one count for the other without naming its scope. Types include datasets, preprints, supplementary material, reviews and articles. Profile totals are not a sum over the curated homepage publication list and are not comparable to old Scholar totals.

## Current published catalogue coverage

The current rendered homepage list contains 52 unique DOIs. The private Google Sheet remains the live master catalogue; these audit counts describe the checked-in rendered list, not a fresh authenticated Sheet read.

- Exact DOI inside the primary author profile: 46/52 (88.5%).
- Additional DOI batch lookup: 5 additional exact DOI records, or 51/52 DOI-only matches.
- Requiring normalized title equality as well: **49/52 (94.2%) safe matches**. The three excluded rows must display unavailable, not zero or a previous Scholar number.
- No duplicate DOI in the catalogue or primary author result set. Different DOIs can represent related versions (preprint, journal article, dataset); do not merge them automatically or sum them as an alleged deduplicated author total.

## Three exclusions

1. `10.1038/s43017-026-00780-4`: catalogue title is *Global carbon emissions and decarbonization in 2025*. OpenAlex W4409363555 returns this DOI but the **2024** title and publication year 2025. Reject the title conflict.
2. `10.1038/s43017-025-00658-x`: catalogue title is *Global carbon emissions and decarbonization in 2024*. A direct DOI singleton lookup redirects/resolves to the same W4409363555, whose returned DOI is the **2026** DOI above. Reject the DOI mismatch and do not double-count the work.
3. `10.26599/CS.2025.9510006`: catalogue title uses singular *emission*; OpenAlex title is *Projection of global daily CO 2 emissions in 2025*. Punctuation/spacing normalization does not resolve the plural difference. Its author is also assigned ORCID `0000-0002-4003-8711`, not the owner's ORCID. Keep unavailable pending review rather than using fuzzy matching.

## Author disambiguation caveats

Three additional catalogue records (`10.1002/advs.77369`, `10.1016/j.adapen.2025.100260`, `10.1038/s43017-026-00791-1`) are assigned A5121455859 with the same owner ORCID. Another (`10.1016/j.ese.2026.100724`) is assigned A5138745030 without ORCID. These explain why primary-profile-only matching loses legitimate catalogue items. Work-specific DOI+title matching can be used without merging author profiles. Profile totals remain explicitly the primary profile's totals.

## API access

Official documentation checked: https://help.openalex.org/api/authentication/

Basic queries can currently run without a key. Basic paging supports this small dataset, per_page maximum100. Optional verified key increases independent budget; cursor paging beyond the first page requires a key. This audit made low-volume anonymous calls only. No account was created, no credential was requested or configured, and no paid plan was selected. Shared GitHub-runner anonymous quota may still be exhausted; fail safely and retain the prior output. Configure an optional secret only after owner authorization.

## Verification limits

This is a source-data audit, not production deployment verification. The migration is a draft PR only. No Scholar data files should be overwritten and the legacy files remain available for history. Actual fresh GSheet rendering and scheduled-run behaviour must be verified after separate merge authorization.
