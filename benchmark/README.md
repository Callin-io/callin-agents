# Open voice-AI benchmark: Italian, Spanish, Portuguese

A reproducible test of AI phone-agent platforms on real phone calls in non-English languages.
Run by Callin.io; method, caller audio, scripts and raw data are public so anyone can re-run it.
If Callin.io loses a metric, the result is published anyway.

## Platforms
Callin.io, Retell AI, Vapi, Bland AI, ElevenLabs Agents (optional: Synthflow, Air).
Same conditions for all: the shared prompt in `agent_prompt.md` translated per language, the same LLM
where the platform allows it (Gemini 2.5 Flash or GPT-4o mini), the best native voice available per
language, a local phone number, vendor-recommended defaults otherwise.

## Languages and accents
it-IT (Milan, Naples) · es-ES (Madrid, Andalusia) · es-MX · pt-BR (São Paulo).
6 accents × 5 scenarios × 5 platforms = 150 calls, repeated 3 times = 450 calls.

## Scenarios (`scenarios/*.json`)
1. `booking` – restaurant table: date, time, party size, name
2. `reschedule` – move a clinic appointment, confirm identity data
3. `faq` – answer from a short document (opening hours, prices)
4. `interruption` – caller changes their mind mid-sentence
5. `handoff` – caller asks for a human: transfer

Each scenario has fixed caller lines, recorded once by native speakers (real voices, not TTS),
so every platform hears exactly the same audio.

## Metrics
| Metric | How | Unit |
|---|---|---|
| Response latency | end of caller turn → start of agent speech, from the stereo recording (`scripts/measure_latency.py`) | ms, median and p90 |
| Understanding | word error rate of the agent's transcript on fixed test phrases with names, numbers, addresses (`scripts/score_wer.py`) | % |
| Task success | scenario closed with the right data, checked by hand against `expected` | % of calls |
| Naturalness | blind listening by 5 native speakers per language | 1–5 |
| Interruption handling | agent stops and resumes correctly | % of calls |
| Cost | public all-inclusive price (telephony + LLM + voice) | $ / min |

## Procedure
1. Configure each platform with `agent_prompt.md` and the scenario's `knowledge` text.
2. The caller bot dials each agent and plays the caller lines in order, waiting for the agent to finish
   speaking (silence > 700 ms) before the next line. Record the call in stereo: left = caller, right = agent.
3. Save recordings as `recordings/<platform>/<lang>/<scenario>_<run>.wav`.
4. Run `python scripts/measure_latency.py recordings/ > results/latency.csv`.
5. Export each platform's transcript, run `python scripts/score_wer.py` against the scenario's
   `test_phrases`.
6. Blind rating: shuffle clips, hide platform names, collect 1–5 scores.
7. Before publishing, send each vendor its own results; 7 days to flag configuration errors.

## Publishing
Results at callin.io/benchmark (ES/IT versions), dated, with method version, example audio,
known limits and a link to this folder. Re-run every quarter.
