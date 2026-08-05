
# 🚀 ProcureAI – Multi-Agent AI Procurement Intelligence Platform

ProcureAI is an enterprise-grade AI procurement platform that automates vendor quotation analysis using OCR, LLMs, deterministic AI agents, LangGraph orchestration, and Human-in-the-Loop approval.

## Live Demo

- Frontend: https://procure-ai-zeta.vercel.app/
- Backend: https://procureai-9vun.onrender.com

## Features

- JWT Authentication
- Workspace & Project Management
- Vendor & Quotation Management
- OCR using PaddleOCR
- LLM Extraction using Mistral AI
- LangGraph Workflow
- Comparison Agent
- Compliance Agent
- Recommendation Agent
- Human Review Loop
- Executive PDF Report
- Docker
- GitHub Actions CI
- Render + Vercel Deployment

## Architecture

```text
Next.js
   |
FastAPI
   |
PostgreSQL
   |
LangGraph
   |
Comparison -> Compliance -> Recommendation
                    |
              Human Review
                    |
              Executive Report
```

## Workflow

1. Upload quotation PDFs.
2. OCR for scanned documents.
3. Extract structured data using Mistral AI.
4. Store validated data in PostgreSQL.
5. Compare vendors.
6. Validate compliance.
7. Generate AI recommendation.
8. Human approval/review.
9. Generate executive report.

## Tech Stack

### Frontend
- Next.js 15
- React
- TypeScript
- Tailwind CSS
- shadcn/ui

### Backend
- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL
- JWT

### AI
- LangGraph
- Mistral AI
- PaddleOCR
- PyMuPDF

### DevOps
- Docker
- GitHub Actions
- Render
- Vercel

## Installation

### Backend

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

Backend:

```env
DATABASE_URL=
SECRET_KEY=
MISTRAL_API_KEY=
CORS_ORIGINS=
```

Frontend:

```env
NEXT_PUBLIC_API_URL=
```

## Author

Vraj Prajapati

GitHub: https://github.com/Vraj006

LinkedIn: https://www.linkedin.com/in/prajapati-vraj-094614288/

## License

MIT
