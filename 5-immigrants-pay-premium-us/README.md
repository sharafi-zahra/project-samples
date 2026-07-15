# Immigrant Pay Premium — Cross-Country Analysis

Analysis of whether immigrant graduates earn a pay premium or penalty relative to native
graduates with equivalent education, using cell-level average-pay data (school × degree ×
major × bachelor's country) across five countries (US, UK, Canada, Australia, Germany), with
a deep dive on the US.

## Approach

- **Unit of observation**: a cell-level average (mean pay for a given grad school × degree ×
  major × immigrant-status combination), not individual workers — explicitly noted throughout
  since it changes how results should be interpreted (group-average differences, not
  individual-level effects).
- **Raw gap**: unadjusted average pay by immigrant/native status per country.
- **Within-cell comparison**: pay gap restricted to cells that have both a native and an
  immigrant average for the same school/degree/major.
- **OLS regression**: `log(avg_pay) ~ immigrant + school FE + degree FE + major FE` per
  country (school fixed effects dropped for small samples, e.g. Germany); plus a pooled
  regression across all five countries with within-country standardized log pay and
  country/degree/major fixed effects.
- **US deep dive** (`us_schools.py`, `us_clean_analysis.py`, `us_subanalysis.py`): restricts to
  genuine graduate-level institutions (drops vocational/cosmetology/community-college entries),
  checks how many schools have both native and immigrant observations, and re-runs the
  regression on the cleaned sample plus subgroup/robustness cuts.

## Files

| File | Purpose |
|---|---|
| `analysis.py` | Main 5-country analysis: sample overview, raw gap, within-cell comparison, per-country and pooled OLS regressions, summary table. |
| `us_schools.py` | US-only school-level overview: counts of native/immigrant cells per school, identifies schools with only one group represented. |
| `us_clean_analysis.py` | Re-runs the US analysis after excluding non-graduate/vocational institutions. |
| `us_subanalysis.py` | Additional US subgroup/robustness regressions. |
| `build_notebook.py`, `build_notebook2.py` | Programmatically assemble the analysis into Jupyter notebooks (via `nbformat`) with narrative markdown alongside the code, for a readable walkthrough of the findings. |

## Notes

- Code only — the underlying cell-level pay CSVs are not included.
