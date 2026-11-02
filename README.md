# 🚩 RedFlag

**A scam-message checker for Indian-context SMS, with source-backed safety tips.**

**Live demo: https://meenakshi-n-24.github.io/RedFlag/**
API docs: https://redflag-api-iisy.onrender.com/docs

> The demo server runs on a free plan and sleeps when idle, so the first scan after a quiet period can take up to a minute.

Paste a suspicious SMS and RedFlag returns:

1. a verdict (**Red Flag**, **Warning** or **Likely safe**) with an estimated scam probability, and
2. safety tips from NPCI, RBI, Sanchar Saathi (Chakshu) and Kerala Police pages, each with its source link and word-for-word quotes.

RedFlag is a student project built for the Honeywell Future Skills Edge AI capstone. It is an **awareness aid, not an official tool**. Its verdicts are probabilities and can be wrong. Pasted messages are not saved.

## How it works

Message → clean text → TF-IDF + Logistic Regression → scam probability → verdict band → fixed set of source-backed tips

| Scam probability | Verdict |
|---|---|
| 0.65 or above | likely scam (Red Flag) |
| 0.35 to 0.65 | unsure (Warning) |
| below 0.35 | likely legitimate (Likely safe) |

The cut points were chosen by hand and not tuned. In the live demo, tips are selected by verdict band from four official pages copied by hand on 17 October 2026. The notebooks also explore retrieval and a Gemini explanation layer, described below.

## What the experiments showed

| Test | TF-IDF + Logistic Regression | DistilBERT |
|---|---|---|
| Locked SMS test set (776 messages), spam F1 | 0.959 | 0.959 |
| 100 hand-written Indian-style messages, trained on SMS data only, accuracy | 0.510 | 0.440 |

- Both models score about 0.96 F1 on the original SMS data but fall close to chance on Indian-style messages: the benchmark did not transfer.
- Adding Indian-style examples to training raised 5-fold cross-validated accuracy to 0.79–0.84 for the baseline and 0.81 for DistilBERT. These figures are optimistic, because the messages share templates.
- A simple TF-IDF model matched fine-tuned DistilBERT, so the simple model is the one deployed.
- A 20-message audit of the Gemini explanation layer found 29 of 36 advice items exact, 6 paraphrased, 1 stretched beyond its source and 0 unsupported (one rater).
- Retrieval worked for questions (right chunk in the top 3 for 15 of 16) but poorly with whole scam messages as queries.

Full details are in the project report.

## Limitations

- The Indian-style set has only 100 hand-written messages, so results on it are rough.
- The deployed model was trained on all 100 of them, so it has no clean held-out Indian-style score.
- The training data is an older, mostly UK-style SMS corpus whose "spam" label is broader than "scam".
- Hinglish and short messages are handled poorly. Ordinary bank alerts can land near the boundary.
- Tips are generic by verdict band, not tailored to each message.
- The knowledge base is a snapshot of four pages, one of them a state-police notice from August 2023. Helplines and portals can change, so confirm contact details on the official sites.

## Repository

| Folder | Contents |
|---|---|
| `docs/` | The web page (single HTML file, served by GitHub Pages) |
| `api/` | FastAPI backend and the trained model files (deployed on Render) |
| `notebooks/` | Baseline, DistilBERT, retrieval and explanation-layer notebooks |
| `knowledge_base/` | The four official source pages, copied by hand |

## Run it locally

```
cd api
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --reload
```

Then edit `API_BASE` in `docs/index.html` to `http://127.0.0.1:8000` and serve the `docs` folder (for example `python -m http.server 5500`). Hosted frontends must be listed in the `ALLOWED_ORIGINS` environment variable.

## Data and sources

- SMS Spam Collection (UCI Machine Learning Repository), not included in this repo: https://archive.ics.uci.edu/dataset/228/sms+spam+collection
- Advice text comes from pages of NPCI, RBI, Sanchar Saathi (Department of Telecommunications) and Kerala Police, retrieved 17 October 2026.
- All Indian-style test messages are invented; no real user messages were collected.

## Built with

Python, scikit-learn, FastAPI, Hugging Face Transformers (DistilBERT), sentence-transformers, Google Gemini API (notebooks only), Render and GitHub Pages.

## License

See `LICENSE`.
