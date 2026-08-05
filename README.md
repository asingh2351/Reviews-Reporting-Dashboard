# Executive Reviews Dashboard (Streamlit)

## Folder contents
```
spotstream/
├── app.py                 ← the dashboard code (paste this into your notepad/editor)
├── requirements.txt        ← Python packages needed
└── data/
    └── master_data.csv     ← pre-loaded with your 5 existing biweekly files (2,071 records)
```

## First-time setup
1. Copy this whole `spotstream` folder to your machine (keep `app.py` and the
   `data` folder together — the app looks for `data/master_data.csv` right
   next to itself).
2. Open a terminal in that folder and run:
   ```
   pip install -r requirements.txt
   streamlit run app.py
   ```
3. Your browser opens the dashboard, already showing all 2,071 records from
   May–July 2026.

## Every 2 weeks, when a new report comes in
1. Open the app (`streamlit run app.py` from that folder).
2. Drag the new `Reviews_Report_with_comments_for_SP_NYC_...csv` file into the
   uploader at the top.
3. It's merged into `data/master_data.csv` automatically and deduplicated —
   next time you open the app, that data is already there. You never need to
   re-upload old files.

## What each part of the dashboard does
- **KPI cards**: Total Garages (for the most recent month in your data/filters),
  % MoM Decline, % MoM Positive, overall Avg Rating.
- **Star Rating Distribution**: donut chart of 1★–5★ counts for the filtered data.
- **Ratings Month Over Month**: average rating trend, one bar per month.
- **Avg Rating gauge**: overall average for whatever is currently filtered.
- **Top 10 / Bottom 10 Garages**: biggest month-over-month rating improvements
  and declines (only for garages that have both a prior month and current
  month rating).
- **Customer Comments**: every comment in the filtered view, newest month first.
- **Lot Name Summary table**: Total Reviews / Prior Month Avg / Current Month
  Avg / Rolling MoM Improvement %, color-coded green (improved) / red (declined) —
  this mirrors your Power BI table exactly.

## Filters (left sidebar)
- **Lot Name** — pick specific garages, or leave blank for all.
- **Month** — pick specific months to include; leave blank to include everything
  (the "current month" used for MoM comparisons is always the most recent month
  in whatever is selected).
- **Comments (sentiment)** — Positive (4–5★), Neutral (3★), Negative (1–2★).
  *Note: your Power BI file has a "Comments" slicer — I couldn't tell from the
  raw data what field it filters on, so I built this sentiment filter as a
  practical stand-in. Let me know if you meant something else (e.g. filter by
  whether a comment exists at all) and I'll adjust it.*
- **Search comment text** — free-text keyword search across comments (bonus,
  not in the original Power BI report, but handy).

## Notes / assumptions
- "Current month" for MoM comparisons = the latest month present after filters
  are applied. As soon as you drop a new biweekly file with a later date, this
  shifts forward automatically — no manual setup needed each cycle.
- "Prior month" = the calendar month immediately before the current month. If
  no reviews exist for that lot in the prior month, the Prior/MoM cells are
  left blank, exactly like your Power BI table.
- Duplicate detection is based on `Rental ID` + `Review Created Date`. If a
  report ever gets re-sent with the same Rental ID and date, it won't double-count.
