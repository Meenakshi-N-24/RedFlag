"""RedFlag core logic: text cleaning, model loading, verdict bands and source-backed advice.

No web framework in here, so it can be tested on its own:  python redflag_core.py "your message"
"""
import re
import sys
from pathlib import Path

import joblib

# ---- verdict bands (hand-chosen cut points, not tuned) ----
SCAM_AT = 0.65
UNSURE_AT = 0.35


def clean(t: str) -> str:
    """Must match the cleaning used when the model was trained."""
    t = t.lower()
    t = re.sub(r"https?://\S+|www\.\S+", " urltoken ", t)
    t = re.sub(r"\b\d{10,}\b", " phonetoken ", t)
    t = re.sub(r"[\u20b9$\u00a3]\s?\d[\d,\.]*|\brs\.?\s?\d[\d,\.]*", " moneytoken ", t)
    t = re.sub(r"\d+", " numtoken ", t)
    return re.sub(r"\s+", " ", t).strip()


def load_model(model_dir: Path):
    vec_path, clf_path = model_dir / "final_tfidf.joblib", model_dir / "final_lr.joblib"
    for p in (vec_path, clf_path):
        if not p.exists():
            raise RuntimeError(f"Model file not found: {p}. Export it from Colab (see the README).")
    return joblib.load(vec_path), joblib.load(clf_path)


def verdict_from_probability(p: float) -> str:
    if p >= SCAM_AT:
        return "likely scam"
    if p >= UNSURE_AT:
        return "unsure"
    return "likely legitimate"


# ---- official sources: text copied by hand on 17 October 2026 ----
RETRIEVED = "17 October 2026"
SOURCES = {
    "npci": {
        "short": "NPCI",
        "name": "NPCI (National Payments Corporation of India), Fraud Awareness",
        "url": "https://www.npci.org.in/fraud-awareness",
    },
    "chakshu": {
        "short": "Sanchar Saathi (Chakshu)",
        "name": "Sanchar Saathi, Department of Telecommunications (Chakshu)",
        "url": "https://sancharsaathi.gov.in/Home/index.jsp#faq-container",
    },
    "kerala": {
        "short": "Kerala Police (helpline 1930)",
        "name": "Kerala Police (Ernakulam Rural Cyber Police Station), National Cyber Crime Reporting Helpline No 1930",
        "url": "https://ps.keralapolice.gov.in/ernakulamruralcyber-ps/notifications/National-Cyber-Crime-Reporting-Helpline-No-1930-3338",
    },
    "rbi": {
        "short": "RBI",
        "name": "RBI (Reserve Bank of India), RBI Kehta Hai: Safe Digital Banking (SMS and IVRS messages)",
        "url": "https://www.rbi.org.in/commonman/English/scripts/smsdigitalbanking.aspx",
    },
}

# Each tip is our own short wording; "quotes" are copied word for word from the cited page.
TIPS = {
    "verify": {
        "source": "npci",
        "tip": ("Do not pay or share details because of this message. Check whether it really comes from the "
                "company and contact the company directly. Find your bank's contact details on its website, "
                "not from the message."),
        "quotes": [
            "Check to see if the message is coming from a legitimate business account or phone number and "
            "contact the company directly to confirm the authenticity of message before taking any action.",
            "Find contact details of bank from website only",
        ],
    },
    "pin": {
        "source": "npci",
        "tip": ("Never share your UPI PIN or debit card credentials with anyone. A UPI PIN is only for making "
                "payments, not for receiving money."),
        "quotes": [
            "Never share debit card credentials & UPI Pin with a third party",
            "UPI pin is to be entered only for payments and not for receipts",
        ],
    },
    "report_sms": {
        "source": "chakshu",
        "tip": "You can report suspected fraud calls, SMS and WhatsApp messages to Chakshu on the Sanchar Saathi portal.",
        "quotes": [
            "Chakshu facilitates citizens to report the suspected or unsolicited communications received through "
            "call, SMS or WhatsApp which are intended for cyber-crime, financial frauds, impersonation, fake "
            "customer services / lottery offer / loan offer / job offer / installation of mobile tower / "
            "disconnection of services or KYC update / loan etc. or any other misuse.",
        ],
    },
    "already_acted": {
        "source": "kerala",
        "tip": ("If you have already lost money, report it promptly on the National Cyber Crime Reporting Portal "
                "(cybercrime.gov.in) or call the 1930 helpline."),
        "quotes": [
            "The National Cybercrime Reporting Portal (https://cybercrime.gov.in) allows direct reporting of "
            "online crimes, including financial frauds.",
            "The helpline number 1930 is available 24 hours a day.",
            "Reporting online financial scams promptly is crucial.",
        ],
    },
    "bank_alert": {
        "source": "rbi",
        "tip": "If this is a transaction alert and you did not make that transaction, take it up with your bank immediately.",
        "quotes": [
            "If you get an alert about a transaction that you have not initiated or authorised, you can "
            "immediately take it up with your bank.",
        ],
    },
}

PLAN = {
    "likely scam": {
        "summary": "This message looks like a scam. Do not act on it until you have verified it.",
        "tips": ["verify", "pin", "report_sms", "already_acted"],
    },
    "unsure": {
        "summary": "RedFlag cannot tell. Treat this message with caution until you have verified it.",
        "tips": ["verify", "report_sms"],
    },
    "likely legitimate": {
        "summary": "This looks routine, but no tool can be sure.",
        "tips": ["bank_alert"],
    },
}

DISCLAIMER = ("RedFlag is a student-built awareness aid, not an official tool. Its verdicts are probabilities "
              "and can be wrong. Always confirm through your bank's or provider's official channels. "
              "The message you paste is not saved by this app.")


def build_advice(verdict: str) -> dict:
    items = []
    for key in PLAN[verdict]["tips"]:
        t, s = TIPS[key], SOURCES[TIPS[key]["source"]]
        items.append({"tip": t["tip"], "source": s["name"], "source_short": s["short"],
                      "url": s["url"], "retrieved": RETRIEVED, "quotes": t["quotes"]})
    text = "\n".join(f"- {i['tip']} (Source: {i['source_short']})" for i in items)
    return {"summary": PLAN[verdict]["summary"], "safety_advice": text, "advice_items": items}


def scan(message: str, vec, clf) -> dict:
    p = float(clf.predict_proba(vec.transform([clean(message)]))[0][1])
    verdict = verdict_from_probability(p)
    return {"verdict": verdict, "confidence_score": round(p, 3),   # = estimated probability of "scam"
            **build_advice(verdict), "disclaimer": DISCLAIMER}


if __name__ == "__main__":
    vec, clf = load_model(Path(__file__).parent / "model")
    result = scan(" ".join(sys.argv[1:]) or "Your KYC is pending. Update now at http://fake.example", vec, clf)
    print(result["verdict"], result["confidence_score"])
    print(result["safety_advice"])
