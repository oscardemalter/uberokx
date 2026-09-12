const C='uberokx-v1';
self.addEventListener('install',e=>e.waitUntil(caches.open(C).then(c=>c.addAll(['/dashboard','/static/css/style.css','/static/js/app.js']))));
self.addEventListener('fetch',e=>{if(e.request.method!=='GET')return;e.respondWith(caches.match(e.request).then(m=>m||fetch(e.request).catch(()=>caches.match('/dashboard'))));});
