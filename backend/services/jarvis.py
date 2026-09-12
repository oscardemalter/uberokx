import re, time
from backend.services.quant import quant_core, NAME_MAP
CONCEPTS = {
    "scalping": ("Scalping = methode PRIORITAIRE MojoCode : 1m-5m, risque tres faible, squeeze+volume.",
                 "Scalping = MojoCode PRIORITY: 1m-5m, very low risk, squeeze+volume."),
    "futures": ("Futures : levier <= 5x, margin isolated, stop AVANT entree.",
                "Futures: leverage <= 5x, isolated margin, stop BEFORE entry."),
    "rsi": ("RSI <30 survendu, >70 surachete. Toujours en confluence.",
            "RSI <30 oversold, >70 overbought. Always in confluence."),
    "stop": ("Stop-loss sacre : place AVANT, jamais descendu.",
             "Sacred stop-loss: placed BEFORE, never moved down."),
    "risque": ("1% max/trade, 5% max/jour, 3 positions max.",
               "1% max/trade, 5% max/day, 3 positions max."),
    "discipline": ("Discipline is the edge. - ProTrader Mike", "Discipline is the edge."),
}
class JarvisBrain:
    def ask(self, question, lang="fr"):
        t0 = time.time(); q = (question or "").lower()
        for name, sym in NAME_MAP.items():
            if re.search(rf"\b{name}\b", q):
                a = quant_core.any_crypto(sym)
                if "error" not in a:
                    ms = int((time.time()-t0)*1000)
                    tr = "haussiere" if a["trend_up"] else "baissiere"
                    return {"reply": f"JARVIS ({ms}ms) - {a['symbol']} : {a['price']} USDT ({a['pct']}%). RSI {a['rsi']} - tendance {tr}. Scalping 1m-5m sur setup A+, risque 1%, stop obligatoire. HALO veille.",
                            "ms": ms, "fallback": False}
        for k, (fr, en) in CONCEPTS.items():
            if k in q:
                return {"reply": ("JARVIS : "+fr) if lang=="fr" else ("JARVIS: "+en),
                        "ms": int((time.time()-t0)*1000), "fallback": False}
        return {"reply": "JARVIS : je coordonne 9 agents 24/7. Questionne-moi sur un crypto (BTC, ETH...), scalping, futures, risque, quant...",
                "ms": int((time.time()-t0)*1000), "fallback": True}
jarvis_brain = JarvisBrain()
