# CLAUDE.local.md - not committed

- I run the dev server with `uv run app.py`on port 3000, not the default port - clashes with another project.
- My API key lives in a gitignored .env.
- Locally I set CLAUSECHECK_MODEL=gpt-5.6-sol to keep experiments cheap; the shared default is a larger model.
- Never make real API calls on your own. Tests are always mocked; I will try the live endpont myself, with a sample clause I wrote, never a real contract.
