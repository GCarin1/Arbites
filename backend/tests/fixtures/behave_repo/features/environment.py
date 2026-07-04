# environment.py — contrato de evidências Arbites (versão de teste, sem Selenium)
import os

EVIDENCE_DIR = os.environ.get("ARBITES_EVIDENCE_DIR")  # setado pelo Arbites no run


def after_step(context, step):
    if EVIDENCE_DIR and step.status == "failed":
        ct = next((t for t in context.scenario.tags if t.startswith("CT-")), "unknown")
        path = os.path.join(EVIDENCE_DIR, ct, f"fail-{step.line}.png")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as handle:
            handle.write(b"fake-screenshot-bytes")
