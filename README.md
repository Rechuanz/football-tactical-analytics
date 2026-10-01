# Football Tactical Analytics (StatsBomb + DuckDB + mplsoccer)

Pipeline: `statsbombpy` → pandas → DuckDB (in-memory) → SQL analítico → mplsoccer.

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt pyarrow
python main.py
```

Estrutura: `src/football_analytics/` (config, extract, transform, queries, viz), `sql/` (queries .sql),
`notebooks/`, `tests/`, `data/` e `outputs/` (ignorados no git).
