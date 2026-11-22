# app/journal — reviews

Structured review workflows (distinct from `trades`' free-form journal blocks).

## Models
- `TradeReview` — the 2-day post-trade review (followed-plan, emotion, what went
  well/wrong, lesson, rating). One per trade; completing it sets the trade's
  `review_completed` and flows through `partials/review_done.html`.
- `WeeklyReview` — weekend weekly review, keyed by `week_ending`. Drives the
  "weekly review due" notification (see analytics context processor).

## Rules
- A trade's review opens 2 days after exit (`review_due_at`); the form is
  HTMX-swappable (`review_form` → `review_done`).
- Owner-scope all lookups. Keep review forms in `app/trades/forms.py` style
  (ModelForm) consistent with the rest of the app.
