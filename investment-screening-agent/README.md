# Investment Screening Agent

An LLM-driven agent (built on [pydantic-ai](https://ai.pydantic.dev/) + Claude) that screens
public companies for a growth-investing mandate: it pulls each company's financials, fetches
recent news, and synthesizes a structured recommendation for a portfolio manager, with a
Streamlit UI on top.

## How it works

- **`screening_agent.py`** — all business logic. The agent is equipped with two tools
  (`get_fundamentals_tool`, `get_news_tool`) and is instructed to call both before producing a
  structured `ScreeningOutput` (verdict, growth signal, positives/negatives from news, financial
  highlights, and risk flags). Deterministic synthesis (`temperature=0`, pinned model string)
  given the same tool outputs.
- **`app.py`** — pure Streamlit UI (company picker, run button, formatted results). No business
  logic — it only calls `screen()` from `screening_agent.py`.
- **Tool-call compliance & monitoring** — every run is checked post-hoc to confirm the model
  actually called both tools (rather than answering from parametric knowledge), and tracks
  LLM round-trips / token usage per run.
- **Auditability** — every run's exact tool payloads are designed to be persisted to a JSONL log
  so any screening result can be replayed or audited later (log itself not included here).

## Design notes (from the code's own docstrings)

- Two irreducible sources of run-to-run variability: live news search results (different
  articles each call) and model tool-calling order/decisions even at `temperature=0`.
- The verdict is a qualitative, model-weighed judgment (revenue growth, margin direction,
  balance-sheet strength, news tone) rather than a hard rule — the docstring spells out how to
  make it fully rule-based if an auditable threshold-based verdict is needed instead.

## Running it

Requires `ANTHROPIC_API_KEY` and `TAVILY_API_KEY` environment variables (see `load_dotenv()` in
`screening_agent.py`), plus `pandas`, `streamlit`, `pydantic`, `pydantic-ai`, and `python-dotenv`.
Also expects `CompanyList.csv`, `BalanceSheets.feather`, and `IncomeStatements.feather` in the
same directory (company fundamentals data — not included in this repo).

```bash
streamlit run app.py
```
