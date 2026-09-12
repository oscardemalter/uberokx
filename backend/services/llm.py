import logging, httpx
from backend.config import settings
logger = logging.getLogger(__name__)
SYS = ("Tu es JARVIS, orchestrateur de UberOKX. Philosophie MojoCode : discipline is the edge, "
       "setups A+, 1% risque, stop obligatoire. Reponds en {lang}, max 150 mots.")
async def ask_ollama(question, lang="fr", timeout=8.0):
    try:
        async with httpx.AsyncClient(timeout=timeout) as c:
            r = await c.post("http://127.0.0.1:11434/api/generate",
                             json={"model":"llama3.2","stream":False,
                                   "prompt":SYS.replace("{lang}","francais" if lang=="fr" else "english")+"\n"+question})
            if r.status_code == 200:
                return r.json().get("response")
    except Exception as e:
        logger.warning("ollama: %s", e)
    return None
async def ask_gpt(question, lang="fr", timeout=6.0):
    if not settings.OPENAI_API_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=timeout) as c:
            r = await c.post("https://api.openai.com/v1/chat/completions",
                             headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                             json={"model":settings.LLM_MODEL,"max_tokens":300,"messages":[
                                 {"role":"system","content":SYS.replace("{lang}","francais" if lang=="fr" else "english")},
                                 {"role":"user","content":question}]})
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logger.warning("llm: %s", e)
    return None
async def ask_deep(question, lang="fr"):
    return (await ask_ollama(question, lang)) or (await ask_gpt(question, lang))
