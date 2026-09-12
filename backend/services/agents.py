from typing import Dict, List
AGENTS = [
    {"id":"jarvis","name":"JARVIS","role_fr":"Orchestrateur Central","color":"#00f0ff"},
    {"id":"dawn","name":"DAWN","role_fr":"Assistant Personnel","color":"#39ff14"},
    {"id":"halo","name":"HALO","role_fr":"Gardien du Risque","color":"#00ff9f"},
    {"id":"ledger","name":"LEDGER","role_fr":"Analyste Marche","color":"#ffd700"},
    {"id":"quill","name":"QUILL","role_fr":"Redacteur","color":"#00bfff"},
    {"id":"penny","name":"PENNY","role_fr":"Email & Suivi","color":"#ff69b4"},
    {"id":"vox","name":"VOX","role_fr":"Social Media","color":"#bf00ff"},
    {"id":"sentry","name":"SENTRY","role_fr":"Surveillance 24/7","color":"#00ffff"},
    {"id":"groove","name":"GROOVE","role_fr":"Focus & Motivation","color":"#ff8c00"},
]
def get_all_agents() -> List[Dict]:
    return AGENTS
def agent_response(agent_id, question, lang="fr"):
    a = next((x for x in AGENTS if x["id"] == agent_id), AGENTS[0])
    return f"{a['name']} : {question} - Discipline is the edge."
