LESSONS = {
    "beginner": {"id":"beginner","title_fr":"Debutant","title_en":"Beginner","color":"#39ff14","lessons":[
        {"id":"b1","title_fr":"Trading = probabilites, pas casino","title_en":"Trading = probabilities","content_fr":"90% perdent faute de plan. Execute un edge avec risque controle.","content_en":"90% lose without a plan. Execute an edge with controlled risk."},
        {"id":"b2","title_fr":"Long, Short, Levier, Liquidation","title_en":"Long, Short, Leverage","content_fr":"Le levier multiplie gains ET pertes. Commence <= 2x.","content_en":"Leverage multiplies both. Start <= 2x."},
        {"id":"b3","title_fr":"Regle des 1% et stop sacre","title_en":"1% rule","content_fr":"1% max/trade, stop AVANT l'entree, jamais descendu.","content_en":"1% max/trade, stop BEFORE entry."},
        {"id":"b4","title_fr":"Live merite","title_en":"Earned Live","content_fr":"PAPER par defaut ; LIVE se merite : switch + double confirmation + cles API. HALO veille : 1%, 5%/j, 3 positions.","content_en":"PAPER by default; LIVE is earned: switch + double confirmation + API keys. HALO watches: 1%, 5%/d, 3 positions."},
        {"id":"b5","title_fr":"Lire une bougie","title_en":"Read a candle","content_fr":"Corps = open->close, meches = rejets.","content_en":"Body = open->close, wicks = rejections."},
        {"id":"b6","title_fr":"Cles API sures","title_en":"Safe API keys","content_fr":"Lecture + Trade, JAMAIS retrait.","content_en":"Read + Trade, NEVER withdrawal."}]},
    "intermediate": {"id":"intermediate","title_fr":"Intermediaire","title_en":"Intermediate","color":"#00f0ff","lessons":[
        {"id":"i1","title_fr":"Tendances & zones","title_en":"Trends & zones","content_fr":"Trade DANS le sens de la tendance, sur support/resistance.","content_en":"Trade WITH the trend at S/R."},
        {"id":"i2","title_fr":"Confluence","title_en":"Confluence","content_fr":"RSI + volume + EMA + BB alignes, sinon rien.","content_en":"RSI + volume + EMA + BB aligned, else nothing."},
        {"id":"i3","title_fr":"Plan 5 points","title_en":"5-point plan","content_fr":"Setup, entree, stop, TP, taille. Sans les 5 = pas de trade.","content_en":"Setup, entry, stop, TP, size."},
        {"id":"i4","title_fr":"SCALPING priorite MojoCode","title_en":"SCALPING priority","content_fr":"1m-5m, squeeze+volume+direction, sorties rapides.","content_en":"1m-5m, squeeze+volume+direction."},
        {"id":"i5","title_fr":"Intraday vs Swing","title_en":"Intraday vs Swing","content_fr":"Intraday ferme le soir ; swing = tendance majeure.","content_en":"Intraday closed at night; swing = major trend."},
        {"id":"i6","title_fr":"Journal","title_en":"Journal","content_fr":"Note chaque trade, review hebdo.","content_en":"Log every trade, weekly review."}]},
    "pro": {"id":"pro","title_fr":"Professionnel","title_en":"Professional","color":"#ffd700","lessons":[
        {"id":"p1","title_fr":"Expectancy","title_en":"Expectancy","content_fr":"(winrate x gain)-(lossrate x perte) > 0 sur 100+ trades.","content_en":"Positive over 100+ trades."},
        {"id":"p2","title_fr":"Psychologie","title_en":"Psychology","content_fr":"FOMO, revenge = ennemis. Discipline = edge.","content_en":"FOMO, revenge = enemies."},
        {"id":"p3","title_fr":"Position sizing","title_en":"Sizing","content_fr":"Taille = (capital x 1%) / distance stop.","content_en":"Size = (capital x 1%) / stop distance."},
        {"id":"p4","title_fr":"Futures avance","title_en":"Adv. futures","content_fr":"Isolated margin, funding 8h, prix de liquidation.","content_en":"Isolated margin, 8h funding."},
        {"id":"p5","title_fr":"Bots","title_en":"Bots","content_fr":"Grid/DCA/snowball OK ; martingale = ruine (HALO bloque).","content_en":"Martingale = ruin (HALO blocks)."},
        {"id":"p6","title_fr":"Backtest->forward->live","title_en":"Order","content_fr":"Toujours cet ordre.","content_en":"Always this order."}]},
    "advanced": {"id":"advanced","title_fr":"Aguerri / Quant","title_en":"Advanced / Quant","color":"#bf00ff","lessons":[
        {"id":"a1","title_fr":"Quant trading","title_en":"Quant","content_fr":"Modeles statistiques + execution algo, radar TOP 20 temps reel.","content_en":"Stat models + algo execution."},
        {"id":"a2","title_fr":"Squeeze Bollinger","title_en":"BB Squeeze","content_fr":"Width 20e percentile + expansion + volume = A+.","content_en":"Width 20th pct + expansion + volume = A+."},
        {"id":"a3","title_fr":"Major reversals","title_en":"Reversals","content_fr":"RSI<28 + higher low ; RSI>72 + lower high.","content_en":"RSI<28 + higher low; RSI>72 + lower high."},
        {"id":"a4","title_fr":"Automatisation 24/7","title_en":"24/7 auto","content_fr":"HALO coupe a -5%/j. Automatise une regle prouvee.","content_en":"HALO cuts at -5%/d."},
        {"id":"a5","title_fr":"Drawdown","title_en":"Drawdown","content_fr":"-50% exige +100%. Protege d'abord.","content_en":"-50% needs +100%."},
        {"id":"a6","title_fr":"Patience = edge","title_en":"Patience","content_fr":"Setup A+ ou rien (Buffett : patients payes).","content_en":"A+ setup or nothing."}]},
}
def get_levels():
    return list(LESSONS.values())
