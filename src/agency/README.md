# Agency Multi-Agent System

This directory contains a multi-agent system based on [Agency Swarm](https://github.com/VRSEN/agency-swarm).

## Structure

```
agency/
├── agency.py                 # Main agency configuration
├── main.py                   # FastAPI deployment entry point
├── shared_instructions.md    # Shared instructions for all agents
├── example_agent/
│   ├── __init__.py
│   ├── example_agent.py     # Agent definition
│   ├── instructions.md      # Agent-specific instructions
│   ├── tools/               # Agent tools
│   │   └── ExampleTool.py
│   └── files/               # Agent local files
└── example_agent2/
    ├── __init__.py
    ├── example_agent2.py
    ├── instructions.md
    ├── tools/
    │   └── ExampleTool.py
    └── files/
```

## Usage

### Terminal Demo

Run the agency in terminal mode for testing:

```bash
python -m src.agency.agency
```

### FastAPI Deployment

Deploy the agency as a FastAPI service:

```bash
python -m src.agency.main
```

The API will be available at `http://localhost:8080`

## Creating New Agents

1. Create a new directory for your agent in `src/agency/`
2. Create the following files:
   - `__init__.py` - Export your agent
   - `agent_name.py` - Agent definition
   - `instructions.md` - Agent instructions
   - `tools/` - Directory for agent tools
   - `files/` - Directory for local files

3. Update `agency.py` to import and configure your new agent

## Environment Variables

Required environment variables (add to `.env`):
- `OPENAI_API_KEY` - Your OpenAI API key

## Learn More

- [Agency Swarm Documentation](https://agency-swarm.ai/)
- [Agency Swarm GitHub](https://github.com/VRSEN/agency-swarm)
