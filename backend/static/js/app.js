const $ = id => document.getElementById(id);
let currentLang='fr', selectedAgent='jarvis', audioCtx=null, ecoMode=localStorage.getItem('ub_eco')==='1';
function appendTerminal(m){ const t=$('terminal'); if(!t)return; const p=document.createElement('p'); p.textContent=m;
 const pr=t.querySelector('.prompt'); if(pr)t.insertBefore(p,pr); else t.appendChild(p); t.scrollTop=t.scrollHeight; }
function playTone(f,d){ try{ if(!audioCtx)audioCtx=new (window.AudioContext||window.webkitAudioContext)();
 const o=audioCtx.createOscillator(),g=audioCtx.createGain(); o.frequency.value=f; g.gain.value=.06;
 o.connect(g); g.connect(audioCtx.destination); o.start(); g.gain.exponentialRampToValueAtTime(.001,audioCtx.currentTime+d); o.stop(audioCtx.currentTime+d);}catch(_){} }
function playSound(n){ playTone(n==='signal'?880:660,.08); }
function toggleSound(){ playSound('click'); }
function toggleEco(){ ecoMode=!ecoMode; localStorage.setItem('ub_eco',ecoMode?'1':'0'); document.body.classList.toggle('eco',ecoMode); }
function setLang(l){ currentLang=l; $('lang-fr').classList.toggle('active',l==='fr'); $('lang-en').classList.toggle('active',l==='en'); }
function updateClock(){ const e=$('clock-time'); if(e)e.textContent=new Date().toISOString().substr(11,8); }
setInterval(updateClock,1000); updateClock();
function openSettings(){$('settings-modal').classList.remove('hidden'); refreshStatus();}
function openAcademy(){$('academy-modal').classList.remove('hidden');}
function openChat(){$('chat-modal').classList.remove('hidden');}
function closeModal(id){$(id).classList.add('hidden');}
function show(id){$(id).classList.toggle('hidden');}
function selectAgent(id){ selectedAgent=id; document.querySelectorAll('.agent-card').forEach(c=>c.classList.remove('selected'));
 const c=document.querySelector('.agent-card[data-agent="'+id+'"]'); if(c)c.classList.add('selected'); }
async function sendChat(){ const i=$('chat-input'); const q=i.value.trim(); if(!q)return; i.value='';
 const h=$('chat-history'); h.innerHTML+='<div class="chat-msg user">Toi : '+q+'</div>';
 const r=await (await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},
 body:JSON.stringify({agent_id:selectedAgent,question:q,lang:currentLang,deep:$('chat-deep').checked})})).json();
 h.innerHTML+='<div class="chat-msg agent">'+r.reply+'</div>'; h.scrollTop=h.scrollHeight; }
async function showLevel(id){ const c=$('lessons-container'); c.classList.remove('hidden');
 const lv=(await (await fetch('/api/academy')).json()).find(x=>x.id===id); if(!lv)return;
 c.innerHTML='<h3>'+lv.title_fr+'</h3>'+lv.lessons.map(l=>'<div class="lesson-item" onclick="this.querySelector(\'.lesson-content\').classList.toggle(\'hidden\')"><h4>'+l.title_fr+'</h4><div class="lesson-content hidden">'+l.content_fr+'</div></div>').join(''); }
async function saveRisk(){ await fetch('/api/settings/risk',{method:'POST',headers:{'Content-Type':'application/json'},
 body:JSON.stringify({risk_pct:parseFloat($('set-risk').value),max_positions:parseInt($('set-positions').value)})});
 appendTerminal('> 🛡️ HALO mis à jour'); }
async function refreshRadar(){ const b=$('radar-list'); if(!b)return;
 const r=await (await fetch('/api/radar')).json();
 b.innerHTML=(r.watchlist||[]).map(w=>'<div class="card"><span>'+w.symbol.replace('/USDT:USDT','').replace('/USDT','')+'</span><strong class="'+(w.pct>=0?'ok':'mode-live')+'">'+w.pct+'%</strong></div>').join('')||'<p class="muted">Scan...</p>'; }
async function refreshStatus(){ const s=await (await fetch('/api/status')).json();
 const m=$('current-mode'); if(m){ m.textContent=(s.trading_mode||'paper').toUpperCase(); m.className=s.trading_mode==='live'?'mode-live':'mode-paper'; }
 const sw=$('mode-live-switch'); if(sw)sw.checked=s.trading_mode==='live';
 const ml=$('mode-label'); if(ml)ml.textContent=s.trading_mode==='live'?'LIVE (réel)':'PAPER (simulé)';
 const vb=$('verification-badge'); if(vb&&s.verification)vb.textContent='Vérification : '+(s.verification.verified?'VÉRIFIÉE':'non vérifiée');
 const ft=$('ft-status'); if(ft)ft.textContent='Bridge : '+(s.bridge&&s.bridge.running?'ON':'OFF'); }
async function toggleMode(wantLive){
 if(wantLive){ if(!confirm('Trading RÉEL : fonds réels. Continuer ?')){refreshStatus();return;}
  if(prompt('Tapez exactement : LIVE')!=='LIVE'){refreshStatus();return;} }
 else if(!confirm('Repasser en PAPER (simulé) ?')){refreshStatus();return;}
 const d=await (await fetch('/api/settings/mode',{method:'POST',headers:{'Content-Type':'application/json'},
  body:JSON.stringify({mode:wantLive?'live':'paper',confirm_live:wantLive})})).json();
 appendTerminal(d.success?'> 🔀 Mode='+d.mode.toUpperCase():'> ⛔ '+(d.reason||'Refus')); refreshStatus(); }
async function saveOkxKeys(){ const r=await (await fetch('/api/okx/keys',{method:'POST',headers:{'Content-Type':'application/json'},
 body:JSON.stringify({api_key:$('okx-key').value,api_secret:$('okx-secret').value,passphrase:$('okx-pass').value})})).json();
 appendTerminal(r.success?'> ✅ Clés vérifiées':'> ❌ '+(r.msg||r.reason)); refreshStatus(); }
async function fastConnect(){ const r=await (await fetch('/api/okx/fast_connect',{method:'POST',headers:{'Content-Type':'application/json'},
 body:JSON.stringify({api_key:$('okx-key').value,api_secret:$('okx-secret').value,passphrase:$('okx-pass').value,demo:$('okx-demo').checked})})).json();
 appendTerminal(r.success?'> ⚡ Fast Connect OK':'> ❌ '+(r.msg||r.reason)); refreshStatus(); }
function oauthStart(){ location.href='/api/okx/oauth/start'; }
async function saveSignalBot(){ const r=await (await fetch('/api/okx/signalbot',{method:'POST',headers:{'Content-Type':'application/json'},
 body:JSON.stringify({url:$('sb-url').value,secret:$('sb-secret').value})})).json();
 appendTerminal(r.success?'> 📡 Signal Bot lié':'> ❌ '+r.reason); }
async function saveWallet(){ const r=await (await fetch('/api/okx/wallet',{method:'POST',headers:{'Content-Type':'application/json'},
 body:JSON.stringify({address:$('w-addr').value,chain:$('w-chain').value})})).json();
 appendTerminal(r.success?'> 👛 Wallet lié':'> ❌ '+r.reason); }
async function startFtBridge(){ const s=await (await fetch('/api/status')).json(); let cl=false;
 if(s.trading_mode==='live'){ if(!confirm('FreqTrade RÉEL ?'))return; if(prompt('Tapez : LIVE')!=='LIVE')return; cl=true; }
 else if(!confirm('FreqTrade PAPER ?'))return;
 const r=await (await fetch('/api/freqtrade/start',{method:'POST',headers:{'Content-Type':'application/json'},
  body:JSON.stringify({confirm_live:cl})})).json();
 appendTerminal(r.success?'>  Bridge démarré':'> ❌ '+r.reason); refreshStatus(); }
async function stopFtBridge(){ await fetch('/api/freqtrade/stop',{method:'POST'}); appendTerminal('> 🤖 Bridge arrêté'); refreshStatus(); }
async function runFtBacktest(){ const r=await (await fetch('/api/freqtrade/backtest',{method:'POST',headers:{'Content-Type':'application/json'},
 body:JSON.stringify({days:30})})).json(); appendTerminal(r.success?'> 📊 Backtest terminé':'> ❌ '+r.reason); }
document.addEventListener('DOMContentLoaded',()=>{ refreshStatus(); refreshRadar(); setInterval(refreshRadar, ecoMode?60000:20000);
 appendTerminal('> Mode serveur : PAPER par défaut'); });
