# AgentFlow AI

Enterprise research platform powered by LangGraph multi-agent orchestration.

## Quick Start

```bash
# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env   # fill in values
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
cp .env.example .env
npm run dev
```

See `docs/` for architecture and implementation guides.
