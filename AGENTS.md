# Repository Guidelines

## Structure at a Glance
- Core automation lives under `src/` (agents, workflows, utils, config, models) with `gst_workflow.py` stitching the LangGraph state machine.
- `backend_server.py` exposes REST + WebSocket; `run_full_system.py` boots backend and frontend together, while `run_frontend.py` leaves the API untouched.
- The React client resides in `frontend/` (components, hooks, lib, types).
- Retrieval artefacts (`data/`, `faiss_index/`, `RAG_Docs/`, `knowledge_graph.db`) stay read-only—never commit regenerated binaries.

```
.
├── backend_server.py
├── run_full_system.py
├── src/
│   ├── agents/
│   ├── workflows/
│   ├── utils/
│   ├── config/
│   └── models/
├── frontend/
│   └── src/{components,hooks,lib,types}
└── data/ · faiss_index/ · RAG_Docs/ · requirements.txt
```

## Build & Run
- Create a virtualenv (`python -m venv .agent_ticket && source .agent_ticket/bin/activate`) and install `pip install -r requirements.txt`.
- `python run_full_system.py` verifies dependencies, seeds `.env`, and launches FastAPI + Vite; stop with `Ctrl+C`.
- For API-only work run `python backend_server.py` and start the UI with `npm run dev`; other scripts (`type-check`, `lint`, `build`) live in the same directory.

## Real-time Processing Flow
- `resolver.process_query` runs via `asyncio.to_thread`, so progress callbacks stream while the workflow executes; backend logs mark `📡 Sent WebSocket message` for each payload.
- Agent 3 broadcasts sub-steps (`TwitterRetrievalAgent`, `LocalRetrievalAgent`, `WebRetrievalAgent`, `LLMReasoningAgent`); `[WS] …` console logs confirm which source is active.

## Coding Style & Naming
- Python: 3.12, 4-space indents, docstrings, type hints, snake_case functions, PascalCase classes, emoji logging (`logger.info("🔄 …")`).
- TypeScript: strict mode, shared types in `frontend/src/types`, PascalCase components, Tailwind utilities.
- Keep agent/workflow names aligned with their responsibilities (`PreprocessingAgent`, `gst_workflow`) and reuse `Config`.

## Testing & Verification
- No automated suite yet; place Python tests under `tests/` and run with `pytest`.
- For regressions run `python run_full_system.py`, submit a ticket, and match `📡` backend logs with `[WS]` console logs while ensuring history persists.
- Frontend changes must pass `npm run type-check` and `npm run lint`; attach visuals when tweaking agent progress or results UX.

## Commit & PR Discipline
- Use imperative commit titles (e.g., `feat: stream retrieval subagents`) with concise bodies.
- Document changes, linked issues, UI captures, and executed tests in every PR.
- Flag `.env` or secret handling explicitly and avoid committing regenerated indexes or other binary artefacts.

## Agent-Specific Tips
- Touch `src/agents/` and `src/workflows/gst_workflow.py` together so `AgentState` stays in sync.
- When adding retrieval sources, mirror the existing adapters in `src/agents/retrieval_agents.py` and extend the orchestrator rather than hard-coding paths or progress names.
