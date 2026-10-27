# Come pubblicare "Callin.io for AI agents" (circa 30 minuti, per il team tecnico)

Prerequisito unico: creare l'agente "Task Caller" in app.callin.io con il testo di `task-caller-agent/prompt.md`, direzione in uscita, assegnargli un numero. Il suo id è `CALLIN_AGENT_ID`.

## 1. GitHub (organizzazione `callin-io`, nome libero al 25/10/2026)
1. github.com → New organization → piano Free → nome `callin-io`.
2. Nuovo archivio pubblico `callin-agents`, poi dalla cartella del pacchetto:
```bash
git init && git add -A && git commit -m "Callin.io for AI agents"
git branch -M main
git remote add origin https://github.com/callin-io/callin-agents.git
git push -u origin main
```

## 2. PyPI (`callin`, nome libero)
```bash
cd python && python -m pip install build twine
python -m build && python -m twine upload dist/*
```
(serve un account pypi.org e un token API; il nome `callin` va registrato al primo caricamento)

## 3. npm (`callin-sdk`)
Pubblicazione fidata, senza chiavi: GitHub → Actions → "Publish callin-sdk to npm" → Run workflow (ramo `main`).
Prerequisito una tantum su npmjs.com → pacchetto `callin-sdk` → Settings → Trusted Publisher → GitHub Actions:
organizzazione `Callin-io`, repository `callin-agents`, file `publish-npm.yml`, ambiente `npm`.
Ricordarsi di aumentare `version` in `js/package.json` e la versione nel `user-agent` di `js/src/index.js` prima di pubblicare.

## 4. ClawHub — abilità per OpenClaw
```bash
npm i -g clawhub
clawhub login            # accesso con GitHub
clawhub skill publish ./skills/callin-phone --slug callin-phone --name "Callin.io Phone Calls" --changelog "First release"
```

## 5. Claude
- Il plugin è già nell'archivio (`.claude-plugin/`): chiunque può installarlo con
  `/plugin marketplace add callin-io/callin-agents` e poi `/plugin install callin@callin`.
- Directory dei connettori: claude.ai/directory/manage (dopo aver aggiunto `title` e `readOnlyHint` agli strumenti del server MCP).

## 6. n8n
Il nodo `n8n-nodes-callin` esiste già (archivio vincpic-alt/n8n-nodes-callin): aggiungere l'operazione "Place call with objective" che usa lo stesso flusso della libreria (campagna con un contatto + variabili `objective`, `context`, `language`) e pubblicare la nuova versione su npm.

## 7. LangChain e CrewAI (dopo PyPI)
- LangChain: proporre su GitHub (langchain-ai/docs) una pagina "Callin.io" nella sezione strumenti, con l'esempio `examples/langchain_place_call.py`.
- CrewAI: aprire una proposta nella loro documentazione strumenti con `examples/crewai_place_call.py`.

## Prova dal vivo prima del lancio
```bash
export CALLIN_API_KEY=... CALLIN_AGENT_ID=...
python examples/python_quickstart.py   # sostituire il numero con il vostro cellulare
```

Dopo la prova: rigenerare la chiave API usata per i test.
