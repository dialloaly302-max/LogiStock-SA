let S,U=null,V='dash',errMsg='',NEEDSETUP=false;
const $=id=>document.getElementById(id);
const F=n=>Math.round(n).toLocaleString('fr-FR')+' FCFA';
const D=t=>new Date(t).toLocaleString('fr-FR',{day:'2-digit',month:'2-digit',year:'2-digit',hour:'2-digit',minute:'2-digit'});
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const DAY=864e5;
const ROLES={'Administrateur':['dash','stock','cats','clients','ventes','histo','users'],'Commercial':['ventes','histo','clients','stock'],'Gestionnaire de stock':['stock','cats']};
let SC='';
function salesPanel(n){const L=S.sales.slice().sort((a,b)=>b.t-a.t).slice(0,n);
  return `<div class="card"><div class="ph"><h3>Historique des ventes</h3><button class="g s" onclick="go('histo')">Voir tout</button></div><div class="pb tw"><table><tr><th>Réf.</th><th>Client</th><th>Paiement</th><th class="num">Total</th><th>Statut</th></tr>${L.map(s=>`<tr><td class="nw">${esc(s.ref)}<br><small class="mut">${D(s.t)}</small></td><td>${esc(cn(cli(s.cid)))}</td><td><span class="tag ${s.mode==='credit'?'acc':''}">${esc(mo(s))}</span></td><td class="num nw">${F(s.total)}</td><td><span class="tag ${s.statut==='validée'?'grn':'red'}">${s.statut}</span></td></tr>`).join('')||'<tr><td colspan="5" class="mut">Aucune vente enregistrée.</td></tr>'}</table></div></div>`}
function cats(){$('v').innerHTML=`<div class="row" style="margin-bottom:12px"><h2 style="flex:1;margin:0">Catégories</h2>${canStock()?'<button onclick="fCat()">+ Catégorie</button>':''}</div>
  <div class="card tw"><table><tr><th>Catégorie</th><th class="num">Produits</th><th class="num">Quantité en stock</th>${canStock()?'<th></th>':''}</tr>${S.cats.map(c=>{const ps=S.products.filter(p=>p.cat===c.id);return `<tr><td>${esc(c.nom)}</td><td class="num">${ps.length}</td><td class="num">${ps.reduce((a,p)=>a+p.stock,0)}</td>${canStock()?`<td class="num"><button class="g s" onclick="fCat(${c.id})">Modifier</button> <button class="g s" onclick="delCat(${c.id})">Supprimer</button></td>`:''}</tr>`}).join('')||'<tr><td colspan="4" class="mut">Aucune catégorie.</td></tr>'}</table></div>`}
function fCat(id){const c=id?S.cats.find(x=>x.id===id):{nom:''};modal(`<h2>${id?'Modifier':'Nouvelle'} catégorie</h2><label>Nom *</label><input id="a1" value="${esc(c.nom)}"><p id="e" class="err"></p><div class="row"><button class="g" onclick="closeM()">Annuler</button><button onclick="sCat(${id||0})">Enregistrer</button></div>`)}
function sCat(id){const n=$('a1').value.trim();if(!n)return $('e').textContent='Le nom est obligatoire.';act('cat_save',{id,nom:n},'Catégorie enregistrée')}
function delCat(id){if(S.products.some(p=>p.cat===id))return toast('Impossible : des produits utilisent cette catégorie.');if(!confirm('Supprimer cette catégorie ?'))return;act('cat_delete',{id},'Catégorie supprimée')}
const GC=['#FFC83D','#C98F00','#FFE08A','#FF9F1C','#2ED47A','#B8AE96'];
const fK=n=>n>=1e6?(n/1e6).toFixed(1).replace('.0','')+' M':n>=1e3?Math.round(n/1e3)+' k':String(Math.round(n));
function chartsHtml(vs){
  const days=[...Array(7)].map((_,i)=>{const d=new Date();d.setHours(0,0,0,0);d.setDate(d.getDate()-6+i);return d});
  const val=days.map(d=>S.sales.filter(s=>s.statut==='validée'&&s.t>=d.getTime()&&s.t<d.getTime()+DAY).reduce((a,s)=>a+s.total,0));
  const mx=Math.max(...val,1),X=i=>40+i*60,Y=v=>170-v/mx*140;
  const line=val.map((v,i)=>(i?'L':'M')+X(i)+' '+Y(v).toFixed(1)).join(' '),area=line+' L400 170 L40 170 Z';
  const grid=[0,1,2,3,4].map(g=>{const y=170-g*35;return `<line x1="40" x2="400" y1="${y}" y2="${y}" style="stroke:var(--line)"/><text x="34" y="${y+3}" text-anchor="end" style="fill:var(--mut);font-size:9px">${fK(mx*g/4)}</text>`}).join('');
  const lab=days.map((d,i)=>`<text x="${X(i)}" y="190" text-anchor="middle" style="fill:var(--mut);font-size:9px">${d.toLocaleDateString('fr-FR',{weekday:'short',day:'numeric'})}</text><circle cx="${X(i)}" cy="${Y(val[i]).toFixed(1)}" r="3.5" style="fill:var(--cyan)"><title>${d.toLocaleDateString('fr-FR')} : ${F(val[i])}</title></circle>`).join('');
  const s1=`<svg viewBox="0 0 420 200" style="width:100%;height:auto;display:block"><defs><linearGradient id="ga" x1="0" y1="0" x2="0" y2="1"><stop offset="0" style="stop-color:#FFC83D;stop-opacity:.55"/><stop offset="1" style="stop-color:#FFC83D;stop-opacity:0"/></linearGradient></defs>${grid}<path d="${area}" fill="url(#ga)"/><path d="${line}" fill="none" style="stroke:var(--cyan);stroke-width:2.5;stroke-linejoin:round"/>${lab}</svg>`;
  const by={};vs.forEach(s=>by[mo(s)]=(by[mo(s)]||0)+s.total);
  const k=Object.keys(by),tot=k.reduce((a,x)=>a+by[x],0),C=2*Math.PI*54;let off=0;
  const s2=tot?`<div style="display:flex;gap:18px;align-items:center;flex-wrap:wrap"><svg viewBox="0 0 160 160" style="width:160px;height:160px;flex:0 0 auto">${k.map((x,i)=>{const len=by[x]/tot*C,e=`<circle cx="80" cy="80" r="54" fill="none" stroke="${GC[i%GC.length]}" stroke-width="22" stroke-dasharray="${len} ${C-len}" stroke-dashoffset="${-off}" transform="rotate(-90 80 80)"><title>${esc(x)} : ${F(by[x])}</title></circle>`;off+=len;return e}).join('')}<text x="80" y="76" text-anchor="middle" style="fill:var(--mut);font-size:10px">Total</text><text x="80" y="94" text-anchor="middle" style="fill:var(--txt);font-size:12px;font-weight:700">${fK(tot)}</text></svg><div style="flex:1;min-width:140px">${k.map((x,i)=>`<div class="lg"><i style="background:${GC[i%GC.length]}"></i><span style="flex:1">${esc(x)}</span><b>${Math.round(by[x]/tot*100)} %</b></div>`).join('')}</div></div>`:'<p class="mut">Aucune vente sur cette période.</p>';
  const cc={};vs.forEach(s=>(s.lignes||[]).forEach(l=>{const c=catn(prod(l.pid));if(c)cc[c]=(cc[c]||0)+l.q}));
  const ce=Object.entries(cc).sort((a,b)=>b[1]-a[1]),cm=ce.length?ce[0][1]:1;
  const s3=ce.length?ce.map(([n,q])=>`<div class="bar-l"><span>${esc(n.slice(0,22))}</span><div class="bar" style="width:${q/cm*100}%"></div><b>${q}</b></div>`).join(''):'<p class="mut">Aucune vente sur cette période.</p>';
  const ps=S.products.slice(0,10),sm=Math.max(...ps.map(p=>p.stock),1),bw=360/Math.max(ps.length,1);
  const s4=ps.length?`<svg viewBox="0 0 420 200" style="width:100%;height:auto;display:block"><defs><linearGradient id="gb" x1="0" y1="0" x2="0" y2="1"><stop offset="0" style="stop-color:#FFD76A"/><stop offset="1" style="stop-color:#C98F00"/></linearGradient></defs><line x1="40" x2="400" y1="170" y2="170" style="stroke:var(--line)"/>${ps.map((p,i)=>{const h=p.stock/sm*130,x=40+i*bw+bw*.15,w=bw*.7,low=p.stock<=p.seuil;return `<rect x="${x.toFixed(1)}" y="${(170-h).toFixed(1)}" width="${w.toFixed(1)}" height="${Math.max(h,1).toFixed(1)}" rx="4" ${low?'style="fill:var(--red)"':'fill="url(#gb)"'}><title>${esc(p.des)} : ${p.stock} (seuil ${p.seuil})</title></rect><text x="${(x+w/2).toFixed(1)}" y="${(165-h).toFixed(1)}" text-anchor="middle" style="fill:var(--txt);font-size:9px;font-weight:700">${p.stock}</text><text x="${(x+w/2).toFixed(1)}" y="186" text-anchor="middle" style="fill:var(--mut);font-size:9px">${esc(String(p.code).slice(0,7))}</text>`}).join('')}</svg>`:'<p class="mut">Aucun produit.</p>';
  const P=(t,b)=>`<div class="card"><div class="ph"><h3>${t}</h3></div><div class="pb">${b}</div></div>`;
  return `<div class="grid2">${P('Évolution du chiffre d’affaires (7 jours)',s1)}${P('Répartition par mode de paiement',s2)}</div>
  <div class="grid2">${P('Ventes par catégorie (quantités)',s3)}${P('Niveau de stock par produit',s4)}</div>`}
function catPanel(){const R=S.cats.map(c=>{const ps=S.products.filter(p=>p.cat===c.id);return `<tr><td>${esc(c.nom)}</td><td class="num">${ps.length}</td><td class="num">${ps.reduce((a,p)=>a+p.stock,0)}</td></tr>`}).join('');
  return `<div class="card"><div class="ph"><h3>Catégories</h3>${ROLES[U.role].includes('cats')?'<button class="g s" onclick="go(\'cats\')">Gérer</button>':''}</div><div class="pb tw"><table><tr><th>Catégorie</th><th class="num">Produits</th><th class="num">Quantité en stock</th></tr>${R||'<tr><td colspan="3" class="mut">Aucune catégorie.</td></tr>'}</table></div></div>`}
const catn=p=>(S.cats.find(c=>c.id===(p&&p.cat))||{}).nom||'';
function splash(){document.body.classList.add('auth');$('app').innerHTML=`<div id="splash"><div class="brand big"><i></i>LOGISTOCK</div><h1>Bienvenue dans LOGISTOCK</h1><p class="mut">${esc(un(U))} · ${esc(U.role)}</p><div class="sbar"><b></b></div></div>`;setTimeout(()=>{if(U)render()},5000)}
const cn=c=>c?((c.nom+' '+(c.prenom||'')).trim()):'';
const un=u=>u?(((u.prenom||'')+' '+u.nom).trim()):'';
const IC={dash:'📊',stock:'📦',cats:'🏷️',clients:'👥',ventes:'🧾',histo:'📜',users:'🔐'};
const LBL={dash:'Tableau de bord',stock:'Stock',cats:'Catégories',clients:'Clients',ventes:'Ventes',histo:'Historique des ventes',users:'Utilisateurs'};
const isAdm=()=>U.role==='Administrateur';
const canStock=()=>isAdm()||U.role==='Gestionnaire de stock';
const canSell=()=>isAdm()||U.role==='Commercial';
const canCli=()=>isAdm()||U.role==='Commercial';
function save(){}
function toast(t){const e=$('toast');e.textContent=t;e.style.display='block';setTimeout(()=>e.style.display='none',2600)}
S={cats:[],users:[],clients:[],products:[],moves:[],sales:[],pays:[]};
const API_BASE=window.LOGISTOCK_API||`${window.location.protocol}//${window.location.hostname}:8080/api`;
const ENDPOINTS={
  me:['GET','/auth/me'],
  setup:['POST','/auth/setup'],
  login:['POST','/auth/login'],
  logout:['POST','/auth/logout'],
  load:['GET','/bootstrap'],
  prod_save:['POST','/products'],
  entree:['POST','/stock/entries'],
  cli_save:['POST','/clients'],
  cli_archive:['POST','/clients/archive'],
  pay:['POST','/clients/payments'],
  sale_create:['POST','/sales'],
  sale_cancel:['POST','/sales/cancel'],
  cat_save:['POST','/categories'],
  cat_delete:['POST','/categories/delete'],
  user_save:['POST','/users'],
  pw_change:['POST','/users/password'],
  user_toggle:['POST','/users/toggle']
};
async function api(a,d){let j;const [m,p]=ENDPOINTS[a]||['POST','/'+a];try{const o={method:m,credentials:'include',headers:{}};if(m!=='GET'){o.headers['Content-Type']='application/json';o.body=JSON.stringify(d||{})}const r=await fetch(API_BASE+p,o);j=await r.json()}catch(e){throw new Error('Le serveur Java ne répond pas. Démarrez le backend Spring Boot (port 8080) et MySQL.')}
  if(j.error)throw new Error(j.error);return j}
async function refresh(){S=await api('load')}
async function act(a,d,ok){try{await api(a,d);await refresh();closeM();render();toast(ok)}catch(er){const e=$('e');e?e.textContent=er.message:toast(er.message)}}
async function boot(sp){try{const r=await api('me');NEEDSETUP=r.setup;U=r.user;if(U){await refresh();V=ROLES[U.role]?ROLES[U.role][0]:'dash'}}catch(e){errMsg=e.message}if(sp&&U)return splash();render()}
const prod=id=>S.products.find(p=>p.id==id),cli=id=>S.clients.find(c=>c.id==id),usr=id=>S.users.find(u=>u.id==id);
function solde(cid){return S.sales.filter(s=>s.cid==cid&&s.mode==='credit'&&s.statut==='validée').reduce((a,s)=>a+s.total,0)-S.pays.filter(p=>p.cid==cid).reduce((a,p)=>a+p.m,0)}
function retard(cid){if(solde(cid)<=0)return false;const o=S.sales.filter(s=>s.cid==cid&&s.mode==='credit'&&s.statut==='validée').sort((a,b)=>a.t-b.t)[0];return o&&Date.now()-o.t>30*DAY}
function notifs(){const a=S.moves.slice(0,30).map(m=>({t:m.t,m:`${m.type==='entrée'?'Entrée':'Sortie'} : ${m.q} × ${prod(m.pid)?.des} par ${un(usr(m.uid))} (reste ${m.rest})`}));
  S.products.filter(p=>p.stock<=p.seuil).forEach(p=>a.unshift({t:Date.now(),m:`⚠ Alerte stock : ${p.des} – ${p.stock} restant(s)`}));return a}
function modal(h){$('m').innerHTML='<div>'+h+'</div>';$('m').className='on'}
function closeM(){$('m').className=''}
$('m').onclick=e=>{if(e.target.id==='m')closeM()};
function setup0(){$('app').innerHTML=`<div class="laptop-scene">
  <div class="laptop-frame">
    <div class="laptop-screen">
      <div class="browser-chrome">
        <div class="browser-tabs">
          <div class="browser-tab active">
            <span class="tab-dot"></span>
            <span>LogiStock SA — Gestion commerciale</span>
          </div>
        </div>
        <div class="browser-addressbar">
          <span class="addr-lock">●</span>
          <span class="addr-url">localhost/logistock/</span>
        </div>
      </div>
      <div class="init-two-col">
        <section class="init-col-left">
          <div class="init-brand">
            <span class="init-brand-dot"></span>
            <span class="init-brand-name">LogiStock SA</span>
          </div>
          <h1>Première initialisation</h1>
          <p class="init-lead">L'application est vide. Choisissez votre nom, votre identifiant et votre mot de passe pour configurer l'accès principal.</p>
          <ul class="init-points">
            <li><span class="init-bullet"></span><span>Gestion commerciale &amp; suivi de stock</span></li>
            <li><span class="init-bullet"></span><span>Accès administrateur sécurisé</span></li>
            <li><span class="init-bullet"></span><span>Mot de passe : 6 caractères minimum</span></li>
          </ul>
        </section>
        <section class="init-col-right">
          <h2>Créer le compte administrateur</h2>
          <div class="init-field">
            <label for="s1">Nom complet</label>
            <input id="s1" autocomplete="name" placeholder="Nom complet">
          </div>
          <div class="init-field">
            <label for="s2">Identifiant</label>
            <input id="s2" autocomplete="username" placeholder="Identifiant">
          </div>
          <div class="init-field">
            <label for="s3">Mot de passe (6 caractères minimum)</label>
            <input id="s3" type="password" autocomplete="new-password" placeholder="Mot de passe (6 caractères minimum)">
          </div>
          <div class="init-field">
            <label for="s4">Confirmer le mot de passe</label>
            <input id="s4" type="password" autocomplete="new-password" placeholder="Confirmer le mot de passe" onkeydown="if(event.key==='Enter')setup()">
          </div>
          ${errMsg?`<p class="err">${esc(errMsg)}</p>`:''}
          <button type="button" class="init-submit-btn" onclick="setup()">Créer le compte et entrer</button>
        </section>
      </div>
    </div>
    <div class="laptop-base"></div>
  </div>
</div>`}
async function setup(){const n=$('s1').value.trim(),l=$('s2').value.trim(),p=$('s3').value;
  if(!n||!l)return fail('Le nom et l’identifiant sont obligatoires.');
  if(p.length<6)return fail('Le mot de passe doit contenir au moins 6 caractères.');
  if(p!==$('s4').value)return fail('Les deux mots de passe ne sont pas identiques.');
  try{await api('setup',{nom:n,login:l,pw:p});errMsg='';await boot(true)}catch(e){fail(e.message)}}
function fail(m){errMsg=m;setup0()}
/* ---------- Auth & shell ---------- */
async function login(){try{await api('login',{login:$('lg').value.trim(),pw:$('pw').value});errMsg='';await boot(true)}catch(e){errMsg=e.message;render()}}
async function logout(){try{await api('logout')}catch(e){}U=null;$('np').className='';render()}
function go(v){V=v;render()}
function render(){
  const a=$('app');document.body.classList.toggle('auth',!U);
  if(!U&&NEEDSETUP)return setup0();
  if(!U){a.innerHTML=`<div id="login">
  <section class="login-welcome"><div class="brand"><i></i>LOGISTOCK SA</div><div><div class="login-kicker">Gestion intelligente</div><h1>Bienvenue dans <span>LOGISTOCK</span></h1><p>Une solution simple et performante pour gérer vos stocks, vos ventes et vos clients en toute confiance.</p></div><div class="login-features"><span>◆ Gestion de stock</span><span>◆ Suivi des ventes</span><span>◆ Gestion clients</span></div></section>
  <section class="login-form"><h2>Connexion</h2><p class="mut">Accédez à votre espace de travail</p>
  <label for="lg">Identifiant</label><div class="login-field"><span class="field-icon">◉</span><input id="lg" autocomplete="username" placeholder="Votre identifiant"></div>
  <label for="pw">Mot de passe</label><div class="login-field"><span class="field-icon">◆</span><input id="pw" type="password" autocomplete="current-password" placeholder="Votre mot de passe" onkeydown="if(event.key==='Enter')login()"></div>
  ${errMsg?`<p class="err">${esc(errMsg)}</p>`:''}<button onclick="login()">Se connecter&nbsp; →</button><div class="login-foot">Accès sécurisé · Réservé aux utilisateurs autorisés</div></section>
  </div>`;return}
  const vs=ROLES[U.role];if(!vs.includes(V))V=vs[0];
  const nb=notifs().length;
  a.innerHTML=`<header><div class="brand"><i></i>LogiStock</div><span class="who">${esc(un(U))} · ${U.role}</span><button onclick="$('np').classList.toggle('on');showN()" aria-label="Notifications">🔔 ${nb}</button><button onclick="fPw()" title="Changer mon mot de passe" aria-label="Changer mon mot de passe">🔑</button><button onclick="logout()">Quitter</button></header>
  <nav>${vs.map(v=>`<button class="${v===V?'on':''}" onclick="go('${v}')"><span>${IC[v]}</span>${LBL[v]}</button>`).join('')}</nav><main id="v"></main>`;
  ({dash,stock,cats,clients,ventes,histo,users})[V]();
}
function showN(){const n=notifs();$('np').innerHTML='<h3>Notifications</h3>'+(n.length?n.map(x=>`<p><span class="mut">${D(x.t)}</span><br>${esc(x.m)}</p>`).join(''):'<p class="mut">Aucune notification.</p>')}
/* ---------- Dashboard ---------- */
let per='mois';
function dash(){
  const now=new Date(),st=per==='jour'?new Date(now.getFullYear(),now.getMonth(),now.getDate()).getTime():per==='mois'?new Date(now.getFullYear(),now.getMonth(),1).getTime():per==='30j'?Date.now()-30*DAY:0;
  const vs=S.sales.filter(s=>s.statut==='validée'&&s.t>=st);
  const ca=vs.reduce((a,s)=>a+s.total,0);
  const cnt={};vs.forEach(s=>s.lignes.forEach(l=>cnt[l.pid]=(cnt[l.pid]||0)+l.q));
  const top=Object.entries(cnt).sort((a,b)=>b[1]-a[1]).slice(0,6),mx=top.length?top[0][1]:1;
  const low=S.products.filter(p=>p.stock<=p.seuil);
  const cred=S.clients.reduce((a,c)=>a+Math.max(0,solde(c.id)),0);
  const val=S.products.reduce((a,p)=>a+p.stock*p.pa,0);
  $('v').innerHTML=`<div class="row" style="margin-bottom:12px"><h2 style="flex:1;margin:0">Tableau de bord</h2><div style="flex:0 0 180px"><select onchange="per=this.value;dash()" aria-label="Période">${[['jour','Aujourd’hui'],['mois','Ce mois'],['30j','30 derniers jours'],['tout','Depuis le début']].map(o=>`<option value="${o[0]}" ${per===o[0]?'selected':''}>${o[1]}</option>`).join('')}</select></div></div>
  <div class="kp"><div><span>Chiffre d’affaires</span><b>${F(ca)}</b></div><div><span>Ventes validées</span><b>${vs.length}</b></div><div class="${low.length?'w':''}"><span>Produits en stock critique</span><b>${low.length}</b></div><div class="a"><span>Crédits à recouvrer</span><b>${F(cred)}</b></div><div><span>Valeur du stock (prix d’achat)</span><b>${F(val)}</b></div></div>
  ${chartsHtml(vs)}
  <div class="grid2"><div class="card"><div class="ph"><h3>Produits les plus vendus</h3></div><div class="pb">${top.length?top.map(([id,q])=>`<div class="bar-l"><span>${esc(prod(id).des.slice(0,22))}</span><div class="bar" style="width:${q/mx*100}%"></div><b>${q}</b></div>`).join(''):'<p class="mut">Aucune vente sur cette période.</p>'}</div></div>
  <div class="card"><div class="ph"><h3>Stock critique</h3></div><div class="pb">${low.length?`<div class="tw"><table><tr><th>Produit</th><th>Restant</th><th>Seuil</th></tr>${low.map(p=>`<tr><td>${esc(p.des)}</td><td><span class="tag red">${p.stock}</span></td><td>${p.seuil}</td></tr>`).join('')}</table></div>`:'<p class="mut">Tous les stocks sont au-dessus du seuil.</p>'}</div></div></div>
  <div class="grid2">${salesPanel(8)}${catPanel()}</div>`}
/* ---------- Stock ---------- */
function stock(){
  $('v').innerHTML=`<div class="row" style="margin-bottom:12px"><h2 style="flex:1;margin:0">Stock en temps réel</h2><div style="flex:0 0 190px"><select aria-label="Catégorie" onchange="SC=this.value;stock()"><option value="">Toutes les catégories</option>${S.cats.map(c=>`<option value="${c.id}" ${SC==c.id?'selected':''}>${esc(c.nom)}</option>`).join('')}</select></div>${canStock()?'<button onclick="fProd()">+ Produit</button><button class="g" onclick="fEntree()">Entrée de stock</button>':''}</div>
  <div class="card tw"><table><tr><th>Code</th><th>Désignation</th><th>Catégorie</th><th>Unité</th>${canStock()?'<th>Prix achat</th>':''}<th>Prix vente</th><th>Stock</th>${canStock()?'<th></th>':''}</tr>
  ${S.products.filter(p=>!SC||p.cat==SC).map(p=>`<tr><td>${esc(p.code)}</td><td>${esc(p.des)}</td><td>${esc(S.cats.find(c=>c.id===p.cat)?.nom)}</td><td>${esc(p.unite)}</td>${canStock()?`<td>${F(p.pa)}</td>`:''}<td>${F(p.pv)}</td><td><span class="tag ${p.stock<=p.seuil?'red':'grn'}">${p.stock}</span></td>${canStock()?`<td><button class="g s" onclick="fProd(${p.id})">Modifier</button></td>`:''}</tr>`).join('')}</table></div>
  <div class="card"><div class="ph"><h3>Historique des mouvements</h3></div><div class="pb tw"><table><tr><th>Date</th><th>Type</th><th>Produit</th><th>Catégorie</th><th>Qté</th><th>Restant</th><th>Par</th></tr>
  ${S.moves.slice().sort((a,b)=>b.t-a.t).slice(0,40).map(m=>`<tr><td>${D(m.t)}</td><td><span class="tag ${m.type==='entrée'?'grn':'acc'}">${m.type}</span></td><td>${esc(prod(m.pid)?.des)}</td><td>${esc(catn(prod(m.pid)))}</td><td>${m.q}</td><td>${m.rest}</td><td>${esc(un(usr(m.uid)))}</td></tr>`).join('')}</table></div></div>`}
function fProd(id){const p=id?prod(id):{code:'',des:'',unite:'pièce',pa:0,pv:0,seuil:15,cat:1};
  modal(`<h2>${id?'Modifier':'Nouveau'} produit</h2><label>Code</label><input id="a1" value="${esc(p.code)}"><label>Désignation</label><input id="a2" value="${esc(p.des)}"><label>Unité</label><input id="a3" value="${esc(p.unite)}">
  <div class="row"><div><label>Prix d’achat (FCFA)</label><input id="a4" type="number" min="0" value="${p.pa}"></div><div><label>Prix de vente (FCFA)</label><input id="a5" type="number" min="0" value="${p.pv}" ${id&&!isAdm()?'disabled':''}></div></div>
  <label>Catégorie</label><select id="a7">${S.cats.map(c=>`<option value="${c.id}" ${c.id===p.cat?'selected':''}>${esc(c.nom)}</option>`).join('')}</select><label>Seuil d’alerte</label><input id="a6" type="number" min="0" value="${p.seuil}"><p id="e" class="err"></p><div class="row"><button class="g" onclick="closeM()">Annuler</button><button onclick="sProd(${id||0})">Enregistrer</button></div>`)}
function sProd(id){const c=$('a1').value.trim(),d=$('a2').value.trim();
  if(!c||!d)return $('e').textContent='Le code et la désignation sont obligatoires.';
  act('prod_save',{id,code:c,des:d,unite:$('a3').value,pa:+$('a4').value,pv:+$('a5').value,seuil:+$('a6').value,cat:+$('a7').value},'Produit enregistré')}
function fEntree(){modal(`<h2>Entrée de stock</h2><label>Produit</label><select id="a1">${S.products.map(p=>`<option value="${p.id}">${esc(p.des)}</option>`).join('')}</select>
  <div class="row"><div><label>Quantité</label><input id="a2" type="number" min="1" value="1"></div><div><label>Prix unitaire d’achat</label><input id="a3" type="number" min="0"></div></div><p id="e" class="err"></p><div class="row"><button class="g" onclick="closeM()">Annuler</button><button onclick="sEntree()">Valider l’entrée</button></div>`);
  $('a1').onchange=()=>$('a3').value=prod($('a1').value).pa;$('a1').onchange()}
function sEntree(){const q=+$('a2').value;if(!(q>0))return $('e').textContent='La quantité doit être supérieure à zéro.';
  act('entree',{pid:+$('a1').value,q,pu:+$('a3').value},'Entrée enregistrée')}
/* ---------- Clients ---------- */
function clients(){
  $('v').innerHTML=`<div class="row" style="margin-bottom:12px"><h2 style="flex:1;margin:0">Clients</h2><div><input id="q" placeholder="Rechercher un client" oninput="fq()" aria-label="Rechercher"></div>${canCli()?'<button onclick="fCli()">+ Client</button>':''}</div><div class="card tw" id="cl"></div>`;fq()}
function fq(){const q=($('q').value||'').toLowerCase();
  $('cl').innerHTML=`<table><tr><th>Nom</th><th>Téléphone</th><th>Adresse</th><th>Solde dû</th><th>Statut</th><th></th></tr>${S.clients.filter(c=>c.actif&&(c.nom+c.tel+c.adr).toLowerCase().includes(q)).map(c=>{const s=solde(c.id),r=retard(c.id);return`<tr><td>${esc(cn(c))}</td><td>${esc(c.tel)}</td><td>${esc(c.adr)}</td><td>${F(s)}</td><td><span class="tag ${r?'red':s>0?'acc':'grn'}">${r?'Débiteur (+30 j)':s>0?'En crédit':'Bon payeur'}</span></td><td><button class="g s" onclick="hCli(${c.id})">Historique</button> ${canCli()?`<button class="g s" onclick="fCli(${c.id})">Modifier</button>`:''}</td></tr>`}).join('')}</table>`}
function fCli(id){const c=id?cli(id):{nom:'',prenom:'',tel:'',adr:'',plafond:100000};
  modal(`<h2>${id?'Modifier':'Nouveau'} client</h2><label>Nom *</label><input id="a1" value="${esc(c.nom)}"><label>Prénom</label><input id="a5" value="${esc(c.prenom)}"><label>Téléphone *</label><input id="a2" value="${esc(c.tel)}"><label>Adresse</label><input id="a3" value="${esc(c.adr)}"><label>Plafond de crédit (FCFA)</label><input id="a4" type="number" min="0" value="${c.plafond}"><p id="e" class="err"></p>
  <div class="row"><button class="g" onclick="closeM()">Annuler</button>${id?`<button class="r" onclick="act('cli_archive',{id:${id}},'Client archivé')">Archiver</button>`:''}<button onclick="sCli(${id||0})">Enregistrer</button></div>`)}
function sCli(id){const n=$('a1').value.trim(),t=$('a2').value.trim();if(!n||!t)return $('e').textContent='Le nom et le téléphone sont obligatoires.';
  act('cli_save',{id,nom:n,prenom:$('a5').value.trim(),tel:t,adr:$('a3').value,plafond:+$('a4').value},'Client enregistré')}
function hCli(id){const c=cli(id);const ss=S.sales.filter(s=>s.cid==id).sort((a,b)=>b.t-a.t),ps=S.pays.filter(p=>p.cid==id);
  modal(`<h2>${esc(cn(c))}</h2><p>Solde dû : <b>${F(solde(id))}</b> · Plafond : ${F(c.plafond)}</p>${retard(id)?'<p class="err">Crédit en retard de plus de 30 jours : achats à crédit bloqués.</p>':''}
  <h3>Achats</h3><div class="tw"><table>${ss.map(s=>`<tr><td>${D(s.t)}</td><td>${s.ref}</td><td>${s.mode}</td><td>${F(s.total)}</td><td>${s.statut}</td></tr>`).join('')||'<tr><td class="mut">Aucun achat</td></tr>'}</table></div>
  <h3 style="margin-top:12px">Paiements</h3><div class="tw"><table>${ps.map(p=>`<tr><td>${D(p.t)}</td><td>${F(p.m)}</td></tr>`).join('')||'<tr><td class="mut">Aucun paiement</td></tr>'}</table></div>
  ${canSell()&&solde(id)>0?`<label>Encaisser un paiement (FCFA)</label><div class="row"><input id="a1" type="number" min="1"><button onclick="pay(${id})">Encaisser</button></div>`:''}<p><button class="g" onclick="closeM()">Fermer</button></p>`)}
async function pay(id){const m=+$('a1').value;if(!(m>0))return;try{await api('pay',{cid:id,m});await refresh();hCli(id);toast('Paiement enregistré')}catch(e){toast(e.message)}}
/* ---------- Ventes ---------- */
let cart=[];
const MOYL=()=>S.modes&&S.modes.length?S.modes.map(m=>m.nom):['Espèces','Orange Money','Moov Money','Virement bancaire','Chèque','Carte bancaire','Crédit'];
let HF={p:'tout',c:'',m:'',s:'',q:''};
function mo(s){return s.moyen||(s.mode==='credit'?'Crédit':'Espèces')}
function hvf(){const n=new Date(),st={jour:new Date(n.getFullYear(),n.getMonth(),n.getDate()).getTime(),'7j':Date.now()-7*DAY,mois:new Date(n.getFullYear(),n.getMonth(),1).getTime(),tout:0}[HF.p];
  return S.sales.filter(s=>s.t>=st&&(!HF.c||s.cid==HF.c)&&(!HF.m||mo(s)===HF.m)&&(!HF.s||s.statut===HF.s)&&(!HF.q||String(s.ref).toLowerCase().includes(HF.q.toLowerCase()))).sort((a,b)=>b.t-a.t)}
function ventes(){const L=S.sales.slice().sort((a,b)=>b.t-a.t);
  $('v').innerHTML=`<div class="row" style="margin-bottom:12px"><h2 style="flex:1;margin:0">Ventes</h2>${canSell()?'<button onclick="cart=[];fVente()">+ Nouvelle vente</button>':''}<button class="g" onclick="go('histo')">Historique des ventes</button></div>
  <div class="card tw"><table><tr><th>Réf.</th><th>Date</th><th>Client</th><th>Paiement</th><th class="num">Total</th><th>Statut</th><th></th></tr>${L.map(s=>`<tr><td>${esc(s.ref)}</td><td>${D(s.t)}</td><td>${esc(cn(cli(s.cid)))}</td><td><span class="tag ${s.mode==='credit'?'acc':''}">${esc(mo(s))}</span></td><td class="num">${F(s.total)}</td><td><span class="tag ${s.statut==='validée'?'grn':'red'}">${s.statut}</span></td><td class="num"><button class="g s" onclick="recu(${s.id})">Détails</button> <button class="s" onclick="facture(${s.id})">Facture</button> ${isAdm()&&s.statut==='validée'?`<button class="g s" onclick="fAnn(${s.id})">Annuler</button>`:''}</td></tr>`).join('')||'<tr><td colspan="7" class="mut">Aucune vente enregistrée.</td></tr>'}</table></div>`}
function histo(){
  const sel=(id,k,o)=>`<select id="${id}" onchange="HF.${k}=this.value;hv()">${o.map(x=>`<option value="${x[0]}" ${HF[k]==x[0]?'selected':''}>${esc(x[1])}</option>`).join('')}</select>`;
  $('v').innerHTML=`<div class="row" style="margin-bottom:12px"><h2 style="flex:1;margin:0">Historique des ventes</h2><button class="g" onclick="csv()">Exporter CSV</button></div>
  <div class="card"><div class="row"><div><label>Période</label>${sel('f1','p',[['jour','Aujourd’hui'],['7j','7 derniers jours'],['mois','Ce mois'],['tout','Tout']])}</div>
  <div><label>Client</label>${sel('f2','c',[['','Tous'],...S.clients.map(c=>[c.id,cn(c)])])}</div>
  <div><label>Paiement</label>${sel('f3','m',[['','Tous'],...MOYL().map(m=>[m,m])])}</div>
  <div><label>Statut</label>${sel('f4','s',[['','Tous'],['validée','Validées'],['annulée','Annulées']])}</div>
  <div><label>Référence</label><input id="f5" value="${esc(HF.q)}" placeholder="V-0001" oninput="HF.q=this.value;hv()"></div></div></div><div id="hv"></div>`;hv()}
function hv(){const L=hvf(),ok=L.filter(s=>s.statut==='validée'),ca=ok.reduce((a,s)=>a+s.total,0),by={};ok.forEach(s=>by[mo(s)]=(by[mo(s)]||0)+s.total);
  $('hv').innerHTML=`<div class="kp"><div><span>Ventes validées</span><b>${ok.length}</b></div><div><span>Chiffre d’affaires</span><b>${F(ca)}</b></div><div class="w"><span>Ventes annulées</span><b>${L.length-ok.length}</b></div></div>
  ${Object.keys(by).length?`<div class="card"><h3>Répartition par mode de paiement</h3>${Object.entries(by).map(([k,v])=>`<span class="tag" style="margin:0 6px 6px 0;display:inline-block">${esc(k)} : ${F(v)}</span>`).join('')}</div>`:''}
  <div class="card tw"><table><tr><th>Réf.</th><th>Date</th><th>Client</th><th>Vendeur</th><th>Paiement</th><th>Total</th><th>Statut</th><th></th></tr>${L.map(s=>`<tr><td>${esc(s.ref)}</td><td>${D(s.t)}</td><td>${esc(cn(cli(s.cid)))}</td><td>${esc(un(usr(s.uid)))}</td><td><span class="tag ${s.mode==='credit'?'acc':''}">${esc(mo(s))}</span></td><td>${F(s.total)}</td><td><span class="tag ${s.statut==='validée'?'grn':'red'}">${s.statut}</span></td><td><button class="g s" onclick="recu(${s.id})">Détails</button> <button class="s" onclick="facture(${s.id})">Facture</button> ${isAdm()&&s.statut==='validée'?`<button class="g s" onclick="fAnn(${s.id})">Annuler</button>`:''}</td></tr>`).join('')||'<tr><td colspan="8" class="mut">Aucune vente pour ces critères.</td></tr>'}</table></div>`}
function csv(){const r=[['Reference','Date','Client','Vendeur','Paiement','Total FCFA','Statut'],...hvf().map(s=>[s.ref,D(s.t),cn(cli(s.cid)),un(usr(s.uid)),mo(s),s.total,s.statut])];
  const b=new Blob(['\ufeff'+r.map(x=>x.map(v=>`"${String(v).replace(/"/g,'""')}"`).join(';')).join('\n')],{type:'text/csv'});const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='ventes.csv';a.click()}
function tot(){const sub=cart.reduce((a,l)=>a+l.q*prod(l.pid).pv,0),r=+($('rm')?.value||0);return{sub,t:Math.round(sub*(1-r/100))}}
function fVente(){const cs=S.clients.filter(c=>c.actif);
  modal(`<h2>Nouvelle vente</h2><div class="row"><div><label>Client</label><select id="vc">${cs.map(c=>`<option value="${c.id}">${esc(cn(c))}</option>`).join('')}</select></div><div><label>Mode de paiement</label><select id="vm">${MOYL().map(m=>`<option>${esc(m)}</option>`).join('')}</select></div></div>
  <div class="row"><div style="flex:2"><label>Produit</label><select id="vp">${S.products.map(p=>`<option value="${p.id}">${esc(p.des)} (${p.stock})</option>`).join('')}</select></div><div><label>Qté</label><input id="vq" type="number" min="1" value="1"></div><button onclick="addL()">Ajouter</button></div>
  <div class="tw" id="cr"></div><div class="row"><div><label>Remise (%) ${isAdm()?'':'– max 10'}</label><input id="rm" type="number" min="0" max="${isAdm()?100:10}" value="0" oninput="drawC()"></div></div><p id="e" class="err"></p>
  <div class="row"><button class="g" onclick="closeM()">Annuler</button><button onclick="valV()">Valider la vente</button></div>`);drawC()}
function addL(){const pid=+$('vp').value,q=+$('vq').value;if(!(q>0))return;const l=cart.find(x=>x.pid===pid);l?l.q+=q:cart.push({pid,q});drawC()}
function drawC(){const t=tot();$('cr').innerHTML=cart.length?`<table>${cart.map((l,i)=>`<tr><td>${esc(prod(l.pid).des)}</td><td>${l.q} × ${F(prod(l.pid).pv)}</td><td><button class="g s" onclick="cart.splice(${i},1);drawC()" aria-label="Retirer">✕</button></td></tr>`).join('')}<tr><th>Total</th><th colspan="2">${F(t.t)}</th></tr></table>`:'<p class="mut">Ajoutez au moins un produit.</p>'}
async function valV(){if(!cart.length)return $('e').textContent='Ajoutez au moins un produit.';
  try{const r=await api('sale_create',{cid:+$('vc').value,id_mode:((S.modes||[]).find(m=>m.nom===$('vm').value)||{}).id,remise:+$('rm').value,lignes:cart});await refresh();closeM();render();recu(r.id)}catch(er){$('e').textContent=er.message}}
function fAnn(id){modal(`<h2>Annuler la vente ${S.sales.find(s=>s.id===id).ref}</h2><label>Motif (obligatoire)</label><input id="a1"><p id="e" class="err"></p><div class="row"><button class="g" onclick="closeM()">Retour</button><button class="r" onclick="ann(${id})">Confirmer l’annulation</button></div>`)}
function ann(id){const mo=$('a1').value.trim();if(!mo)return $('e').textContent='Indiquez le motif de l’annulation.';act('sale_cancel',{id,motif:mo},'Vente annulée, stock rétabli')}
function facture(id){const h=window.lsFacture&&window.lsFacture(id);if(!h)return toast('Facture introuvable');modal(h+'<div class="row" style="margin-top:12px"><button class="g" onclick="closeM()">Fermer</button></div>');const m=$('m').firstElementChild;if(m)m.classList.add('ls-inv-modal')}
function recu(id){const s=S.sales.find(x=>x.id===id);
  modal(`<h2>Reçu ${s.ref}</h2><p class="mut">LogiStock SA · ${D(s.t)}<br>Client : ${esc(cn(cli(s.cid)))} · ${mo(s)} · Vendeur : ${esc(un(usr(s.uid)))}</p><div class="tw"><table>${s.lignes.map(l=>`<tr><td>${esc(prod(l.pid).des)}</td><td>${l.q} × ${F(l.pu)}</td><td>${F(l.q*l.pu)}</td></tr>`).join('')}</table></div>
  ${s.remise?`<p>Remise : ${s.remise} %</p>`:''}<h3>Total : ${F(s.total)}</h3>${s.statut==='annulée'?`<p class="err">Annulée – ${esc(s.motif)} (${esc(s.annPar)})</p>`:''}${(S.histo||[]).some(h=>h.sid===s.id)?'<h3>Historique de la vente</h3>'+S.histo.filter(h=>h.sid===s.id).map(h=>`<p class="mut" style="margin:4px 0">${D(h.t)} · ${esc(h.action)} · ${esc(un(usr(h.uid)))}${h.details?' – '+esc(h.details):''}</p>`).join(''):''}<div class="row"><button class="g" onclick="closeM()">Fermer</button><button onclick="print()">Imprimer</button></div>`)}
/* ---------- Utilisateurs ---------- */
function users(){
  $('v').innerHTML=`<div class="row" style="margin-bottom:12px"><h2 style="flex:1;margin:0">Utilisateurs et droits</h2><button onclick="fUsr()">+ Utilisateur</button><button class="g" onclick="bk()">Sauvegarder les données</button></div>
  <div class="card tw"><table><tr><th>Nom</th><th>Identifiant</th><th>Rôle</th><th>État</th><th></th></tr>${S.users.map(u=>`<tr><td>${esc(un(u))}</td><td>${esc(u.login)}</td><td>${u.role}</td><td><span class="tag ${u.actif?'grn':'red'}">${u.actif?'Actif':'Désactivé'}</span></td><td><button class="g s" onclick="fUsr(${u.id})">Modifier</button> ${u.id!==U.id?`<button class="g s" onclick="tg(${u.id})">${u.actif?'Désactiver':'Activer'}</button>`:''}</td></tr>`).join('')}</table></div>`}
async function tg(id){try{await api('user_toggle',{id});await refresh();render()}catch(e){toast(e.message)}}
function bk(){const b=new Blob([JSON.stringify(S)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='logistock-sauvegarde.json';a.click()}
function fUsr(id){const u=id?usr(id):{nom:'',login:'',pw:'',tel:'',role:'Commercial'};
  modal(`<h2>${id?'Modifier':'Nouvel'} utilisateur</h2><label>Nom complet</label><input id="a1" value="${esc(u.nom)}"><label>Identifiant</label><input id="a2" value="${esc(u.login)}"><label>Mot de passe</label><input id="a3" type="password" placeholder="${id?'Laisser vide pour ne pas changer':''}"><label>Rôle</label><select id="a4">${Object.keys(ROLES).map(r=>`<option ${r===u.role?'selected':''}>${r}</option>`).join('')}</select><p id="e" class="err"></p>
  <div class="row"><button class="g" onclick="closeM()">Annuler</button><button onclick="sUsr(${id||0})">Enregistrer</button></div>`)}
function sUsr(id){const n=$('a1').value.trim(),l=$('a2').value.trim(),p=$('a3').value;
  if(!n||!l||(!id&&!p))return $('e').textContent='Nom, identifiant et mot de passe sont obligatoires.';
  act('user_save',{id,nom:n,login:l,pw:p,role:$('a4').value},'Utilisateur enregistré')}
function fPw(){modal(`<h2>Changer mon mot de passe</h2><label>Ancien mot de passe</label><input id="a1" type="password"><label>Nouveau mot de passe (6 caractères minimum)</label><input id="a2" type="password"><label>Confirmer le nouveau mot de passe</label><input id="a3" type="password"><p id="e" class="err"></p><div class="row"><button class="g" onclick="closeM()">Annuler</button><button onclick="sPw()">Enregistrer</button></div>`)}
function sPw(){if($('a2').value!==$('a3').value)return $('e').textContent='Les deux mots de passe ne sont pas identiques.';act('pw_change',{old:$('a1').value,new:$('a2').value},'Mot de passe modifié')}
/* Désactive les suggestions / remplissage automatique du navigateur */
function noAuto(){document.querySelectorAll('input,select,textarea').forEach(e=>{if(e.dataset.na)return;e.dataset.na=1;e.setAttribute('autocomplete',e.type==='password'?'new-password':'off');e.setAttribute('autocorrect','off');e.setAttribute('autocapitalize','off');e.setAttribute('spellcheck','false');e.setAttribute('data-lpignore','true');e.name='f'+Math.random().toString(36).slice(2,9)})}
new MutationObserver(noAuto).observe(document.body,{childList:true,subtree:true});noAuto();
boot();




// === Vue Facture Moderne intégrée dans le détail de la vente ===
(function(){
  function esc(v){
    return String(v==null?'':v)
      .replace(/&/g,'&amp;')
      .replace(/</g,'&lt;')
      .replace(/>/g,'&gt;')
      .replace(/"/g,'&quot;');
  }

  function fmtNum(n){
    return Number(n||0).toLocaleString('fr-FR').replace(/\u202f|\u00a0/g,' ');
  }

  function fmtDate(ms){
    if(!ms) return '—';
    const d=new Date(Number(ms));
    if(isNaN(d.getTime())) return String(ms);
    return d.toLocaleString('fr-FR',{year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'});
  }

  function getStore(){
    // S = état principal de l'app (let global, absent de window)
    try{ if(typeof S!=='undefined' && S && Array.isArray(S.sales)) return S; }catch(e){}
    const cands=[window.DB,window.db,window.state,window.DATA,window.data,window.store];
    for(const obj of cands){
      if(obj && Array.isArray(obj.sales)) return obj;
    }
    return null;
  }

  function resolveSale(container){
    const st=getStore();
    if(!st || !Array.isArray(st.sales) || !st.sales.length) return null;

    if(container && container.dataset && container.dataset.saleId){
      const byAttr=st.sales.find(s=>String(s.id)===String(container.dataset.saleId));
      if(byAttr) return byAttr;
    }

    const txt=(container && container.textContent)||'';
    const refMatch=txt.match(/\bV-\d+\b/i);
    if(refMatch){
      const byRef=st.sales.find(s=>String(s.ref||'').toLowerCase()===refMatch[0].toLowerCase());
      if(byRef) return byRef;
    }

    if(window.currentSaleId!=null){
      const byWin=st.sales.find(s=>String(s.id)===String(window.currentSaleId));
      if(byWin) return byWin;
    }
    if(window.selectedSaleId!=null){
      const bySel=st.sales.find(s=>String(s.id)===String(window.selectedSaleId));
      if(bySel) return bySel;
    }

    return st.sales[st.sales.length-1];
  }

  function buildFactureHtml(sale, st){
    const clients=Array.isArray(st.clients)?st.clients:[];
    const products=Array.isArray(st.products)?st.products:[];
    const users=Array.isArray(st.users)?st.users:[];
    const histo=Array.isArray(st.histo)?st.histo.filter(h=>String(h.sid)===String(sale.id)):[];

    const client=clients.find(c=>String(c.id)===String(sale.cid))||{};
    const vendeur=users.find(u=>String(u.id)===String(sale.uid))||{};
    const lignes=Array.isArray(sale.lignes)?sale.lignes:[];

    let sousTotal=0;
    let totalArticles=0;
    const rowsHtml=lignes.map((l,idx)=>{
      const prod=products.find(p=>String(p.id)===String(l.pid))||{};
      const q=Number(l.q||0);
      totalArticles+=q;
      const pu=Number(l.pu!=null?l.pu:(prod.pv||0));
      const totalLigne=q*pu;
      sousTotal+=totalLigne;
      const nomProd=prod.des?`${prod.des}${prod.code?' ('+prod.code+')':''}`:`Produit #${l.pid}`;
      return `<tr><td>${esc(nomProd)}</td><td class="num">${fmtNum(pu)} F</td><td class="ctr">${esc(q)}${prod.unite?' '+esc(prod.unite):''}</td><td class="num"><b>${fmtNum(totalLigne)} F</b></td></tr>`;
    }).join('');

    const remisePct=Number(sale.remise||0);
    const montantRemise=Math.max(0,Math.round(sousTotal*(remisePct/100)));
    const netAPayer=sale.total!=null?Number(sale.total):Math.max(0,sousTotal-montantRemise);
    const isCancel=String(sale.statut||'').toLowerCase().includes('annul');
    const modeLabel=sale.moyen?(sale.mode==='credit'?`${sale.moyen} · Crédit`:`${sale.moyen} · Comptant`):(sale.mode||'—');
    const clientNom=`${client.prenom||''} ${client.nom||''}`.trim()||`Client #${sale.cid||''}`;
    const vendeurNom=`${vendeur.prenom||''} ${vendeur.nom||''}`.trim()||vendeur.login||`Utilisateur #${sale.uid||''}`;
    const refLabel=sale.ref||('V-'+sale.id);

    const remiseLine=`<div class="ls-df-srow"><span>Remise</span><span>${remisePct>0?'-'+fmtNum(montantRemise)+' FCFA ('+remisePct+' %)':'0 FCFA'}</span></div>`;
    const deco=`<svg class="ls-df-deco" viewBox="0 0 860 100" preserveAspectRatio="none" aria-hidden="true"><polygon fill="#F2B705" points="0,0 340,0 390,49 0,49"/><polygon fill="#F2B705" points="0,59 180,59 168,73 0,73"/><polygon fill="#F2B705" points="0,85 118,85 106,99 0,99"/><polygon fill="#0b0a06" points="360,0 860,0 860,100 460,100"/></svg>`;
    const logo=`<svg class="ls-df-logo" viewBox="0 0 100 88" aria-hidden="true"><polygon fill="#F2B705" points="25,0 75,0 100,44 75,88 25,88 0,44"/><polygon fill="#0b0a06" points="50,16 74,29 50,42 26,29"/><polygon fill="#fff" points="26,32 48,45 48,72 26,59"/><polygon fill="#fff" points="52,45 74,32 74,59 52,72"/></svg>`;

    return `
      <div class="ls-detail-facture-box" data-invoice-for="${esc(sale.id)}">
        <div class="ls-df-toolbar">
          <span class="ls-df-toolbar-title">Facture <b>${esc(refLabel)}</b></span>
          <button type="button" class="ls-df-btn" data-action="print-detail-invoice">🖨️ Imprimer / PDF</button>
        </div>

        <div class="ls-df-paper">
          ${deco}
          <div class="ls-df-body">
            <div class="ls-df-cols">
              <div class="ls-df-left">
                ${logo}
                <div class="ls-df-brand">LOGISTOCK SA</div>
                <div class="ls-df-h">Facturé à</div>
                <div class="ls-df-name">${esc(clientNom)}</div>
                ${client.tel?`<div class="ls-df-line"><span>Tél.</span>${esc(client.tel)}</div>`:''}
                ${client.email?`<div class="ls-df-line"><span>Email</span>${esc(client.email)}</div>`:''}
                ${client.adr?`<div class="ls-df-line"><span>Adresse</span>${esc(client.adr)}</div>`:''}
              </div>
              <div class="ls-df-right">
                <div class="ls-df-title">FACTURE</div>
                <div class="ls-df-line r"><span>N°</span><b>${esc(refLabel)}</b></div>
                <div class="ls-df-line r"><span>Date</span><b>${esc(fmtDate(sale.t))}</b></div>
                <div class="ls-df-line r"><span>Statut</span><b class="${isCancel?'bad':'good'}">${esc((sale.statut||'validée').toUpperCase())}</b></div>
                <div class="ls-df-h" style="margin-top:12px">Paiement</div>
                <div class="ls-df-line r"><span>Mode</span><b>${esc(modeLabel)}</b></div>
                <div class="ls-df-line r"><span>Vendeur</span><b>${esc(vendeurNom)}</b></div>
              </div>
            </div>

            <table class="ls-df-table">
              <thead><tr><th>Désignation</th><th class="num">Prix</th><th class="ctr">Qté</th><th class="num">Sous-total</th></tr></thead>
              <tbody>${rowsHtml||'<tr><td colspan="4" style="text-align:center;opacity:.6">Aucune ligne enregistrée</td></tr>'}</tbody>
            </table>

            <div class="ls-df-cols ls-df-bottom">
              <div class="ls-df-left">
                <div class="ls-df-h">Conditions</div>
                <p class="ls-df-terms">Paiement dû à la réception de la facture. Conservez ce document comme preuve d'achat.</p>
                <div class="ls-df-h" style="margin-top:10px">Merci pour votre confiance</div>
                ${isCancel&&sale.motif?`<p class="ls-df-cancel">Vente annulée : ${esc(sale.motif)}</p>`:''}
              </div>
              <div class="ls-df-right">
                <div class="ls-df-summary">
                  <div class="ls-df-srow"><span>Sous-total</span><span>${fmtNum(sousTotal)} FCFA</span></div>
                  ${remiseLine}
                  <div class="ls-df-srow total"><span>Total</span><span>${fmtNum(netAPayer)} FCFA</span></div>
                </div>
                <div class="ls-df-sign"><b>${esc(vendeurNom)}</b><small>Vendeur · LogiStock SA</small></div>
              </div>
            </div>
          </div>
          ${deco.replace('class="ls-df-deco"','class="ls-df-deco bottom"')}
        </div>
      </div>`;
  }

  window.lsFacture=function(id){
    const st=getStore();
    if(!st) return '';
    const sale=(st.sales||[]).find(x=>String(x.id)===String(id));
    return sale?buildFactureHtml(sale,st):'';
  };

  function findDetailContainers(){
    const found=new Set();
    const selectors=[
      '[id*="detail" i]',
      '[class*="detail" i]',
      '[id*="vente" i]',
      '[class*="vente" i]',
      '[id*="modal" i]',
      '[class*="modal" i]',
      '[role="dialog"]'
    ];
    const rm=document.getElementById('m');
    if(rm && rm.className==='on' && /Reçu\s+V-\d+/i.test(rm.textContent||'')) found.add(rm);
    document.querySelectorAll(selectors.join(',')).forEach(el=>{
      if(el.closest('.ls-detail-facture-box')) return;
      const txt=(el.textContent||'').toLowerCase();
      const hasSaleRef=/\bv-\d+\b/i.test(el.textContent||'');
      const looksLikeSaleDetail=(
        (txt.includes('détail') || txt.includes('detail') || txt.includes('vente')) &&
        (hasSaleRef || txt.includes('client') || txt.includes('remise') || txt.includes('paiement') || txt.includes('total'))
      );
      if(looksLikeSaleDetail && el.offsetHeight > 40){
        found.add(el);
      }
    });
    return Array.from(found);
  }

  function renderFactureInSaleDetails(){
    return; // la facture a maintenant sa propre fenêtre (bouton Facture)
    const st=getStore();
    if(!st) return;

    const containers=findDetailContainers();
    containers.forEach(box=>{
      const sale=resolveSale(box);
      if(!sale) return;
      const existing=box.querySelector('.ls-detail-facture-box');
      if(existing && existing.getAttribute('data-invoice-for')===String(sale.id)) return;
      if(existing) existing.remove();
      const wrapper=document.createElement('div');
      wrapper.innerHTML=buildFactureHtml(sale, st);
      (box.id==='m' && box.firstElementChild ? box.firstElementChild : box).appendChild(wrapper.firstElementChild);
    });
  }

  document.addEventListener('click',(ev)=>{
    const btn=ev.target.closest('[data-action="print-detail-invoice"]');
    if(!btn) return;
    ev.preventDefault();
    ev.stopPropagation();
    const box=btn.closest('.ls-detail-facture-box');
    if(!box) return;

    let printZone=document.getElementById('lsPrintZone');
    if(!printZone){
      printZone=document.createElement('div');
      printZone.id='lsPrintZone';
      document.body.appendChild(printZone);
    }
    printZone.innerHTML=box.outerHTML;
    document.body.classList.add('ls-printing-detail-invoice');
    window.print();
    setTimeout(()=>document.body.classList.remove('ls-printing-detail-invoice'),400);
  });

  document.addEventListener('click',(ev)=>{
    const trigger=ev.target.closest('tr, button, a, [data-sale-id]');
    if(trigger){
      const idAttr=trigger.getAttribute('data-sale-id');
      if(idAttr) window.currentSaleId=idAttr;
      const m=(trigger.textContent||'').match(/\bV-\d+\b/i);
      const st=getStore();
      if(m && st && Array.isArray(st.sales)){
        const found=st.sales.find(s=>String(s.ref||'').toLowerCase()===m[0].toLowerCase());
        if(found) window.currentSaleId=found.id;
      }
    }
    setTimeout(renderFactureInSaleDetails, 60);
  });

  const obs=new MutationObserver(()=>renderFactureInSaleDetails());
  window.addEventListener('DOMContentLoaded',()=>{
    renderFactureInSaleDetails();
    obs.observe(document.body,{childList:true,subtree:true});
  });
})();
