# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LitBanana is an AI-powered image/text generator for creating Xiaohongshu (Little Red Book) style content. Users input a topic, the system generates an outline, then produces multiple images with consistent styling.

## Development Commands

### Backend (Python/Flask)
```bash
# Install dependencies
uv sync

# Run backend server (port 5500)
uv run python -m backend.app

# Run tests
uv run pytest

# Run specific test file
uv run pytest tests/test_filename.py

# Run single test
uv run pytest tests/test_filename.py::test_function_name -v
```

### Frontend (Vue 3/TypeScript)
```bash
cd frontend

# Install dependencies
pnpm install

# Run dev server (port 5173)
pnpm dev

# Build for production
pnpm build
```

### Docker
```bash
# Run with Docker
docker run -d -p 5500:5500 -v ./history:/app/history -v ./output:/app/output histonemax/LitBanana:latest

# Or with docker-compose
docker-compose up -d
```

## Architecture

### Backend Structure (`backend/`)
- **app.py**: Flask application factory, static file serving for production builds
- **config.py**: Configuration loading from YAML files (`text_providers.yaml`, `image_providers.yaml`)
- **routes/**: Modular API blueprints
  - `outline_routes.py`: POST `/api/outline` - Generate content outlines
  - `image_routes.py`: POST `/api/generate`, GET `/api/images/<filename>` - Image generation
  - `history_routes.py`: CRUD for generation history
  - `config_routes.py`: Provider configuration management
- **generators/**: Image generation provider implementations (factory pattern)
  - `factory.py`: Creates generators based on provider type
  - `google_genai.py`, `openai_compatible.py`, `image_api.py`, `jimeng.py`: Provider implementations
  - `base.py`: Abstract base class `ImageGeneratorBase`
- **services/**: Business logic (`outline.py`, `image.py`, `history.py`)
- **utils/**: Shared utilities (`text_client.py`, `genai_client.py`, `image_compressor.py`)

### Frontend Structure (`frontend/src/`)
- **stores/generator.ts**: Pinia store managing the generation workflow state machine (input → outline → generating → result)
- **views/**: Route components
  - `HomeView.vue`: Topic input
  - `OutlineView.vue`: Edit generated outline
  - `GenerateView.vue`: Image generation progress
  - `ResultView.vue`: View/download results
  - `HistoryView.vue`: Browse past generations
  - `SettingsView.vue`: Provider configuration
- **components/**: Reusable components organized by feature (`history/`, `home/`, `settings/`)
- **api/index.ts**: Backend API client

### Configuration Files
- `text_providers.yaml`: Text generation providers (OpenAI-compatible, Google Gemini)
- `image_providers.yaml`: Image generation providers (Google GenAI, OpenAI-compatible, JiMeng)
- Example templates: `*.yaml.example` files

## Key Patterns

### Provider Factory Pattern
Image generators use a factory pattern (`backend/generators/factory.py`). To add a new provider:
1. Create a class extending `ImageGeneratorBase`
2. Register in `ImageGeneratorFactory.GENERATORS` dict

### State Machine Flow
The frontend generator store tracks workflow stages: `input` → `outline` → `generating` → `result`. State persists to localStorage.

### API Endpoints
All API routes are prefixed with `/api`. Backend auto-serves frontend build from `frontend/dist/` when present (Docker/production mode).
