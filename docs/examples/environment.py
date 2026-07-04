# environment.py — contrato de evidências Arbites
#
# Adicione este hook ao repo de automação (Behave + Selenium). Sem a
# variável ARBITES_EVIDENCE_DIR o hook não faz nada — o repo continua
# funcionando sozinho, fora do Arbites.
import os

EVIDENCE_DIR = os.environ.get("ARBITES_EVIDENCE_DIR")  # setado pelo Arbites no run


def after_step(context, step):
    if EVIDENCE_DIR and step.status == "failed" and hasattr(context, "driver"):
        ct = next((t for t in context.scenario.tags if t.startswith("CT-")), "unknown")
        path = os.path.join(EVIDENCE_DIR, ct, f"fail-{step.line}.png")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        context.driver.save_screenshot(path)
