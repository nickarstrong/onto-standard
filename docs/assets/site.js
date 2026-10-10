/* ONTO site: one small script. Orb, reveal on scroll, phone tab bar, demo switcher, copy address. No trackers, no cookies. */
(function(){
var reduce=false;try{reduce=matchMedia('(prefers-reduced-motion: reduce)').matches}catch(e){}
/* orb: student circle shrinks from the size of the base to its value, once */
var c=document.querySelector('.stu');
if(c&&!reduce){var R=+c.dataset.r0,Y=+c.dataset.y0,r1=+c.getAttribute('r'),y1=+c.getAttribute('cy'),t0=null;
 c.setAttribute('r',R);c.setAttribute('cy',Y);
 var f=function(t){if(!t0)t0=t;var k=Math.min(1,(t-t0)/1600);k=1-Math.pow(1-k,3);c.setAttribute('r',(R+(r1-R)*k).toFixed(2));c.setAttribute('cy',(Y+(y1-Y)*k).toFixed(2));if(k<1)requestAnimationFrame(f)};
 setTimeout(function(){requestAnimationFrame(f)},300);
 setTimeout(function(){c.setAttribute('r',r1);c.setAttribute('cy',y1)},2600);}
/* reveal blocks once */
var rv=document.querySelectorAll('.reveal');
if(rv.length){if(reduce||!('IntersectionObserver' in window)){rv.forEach(function(e){e.classList.add('in')})}
 else{var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target)}})},{rootMargin:'0px 0px -8% 0px'});rv.forEach(function(e){io.observe(e)})}}
/* phone tab bar hides on scroll down */
var tabs=document.querySelector('.tabs'),ly=window.scrollY;
if(tabs)window.addEventListener('scroll',function(){var y=window.scrollY;tabs.classList.toggle('hide',y>ly&&y>120);ly=y},{passive:true});
/* copy address */
document.querySelectorAll('[data-copy]').forEach(function(b){b.addEventListener('click',function(){var v=b.getAttribute('data-copy');
 (navigator.clipboard?navigator.clipboard.writeText(v):Promise.reject()).then(function(){var o=b.textContent;b.textContent='Copied';setTimeout(function(){b.textContent=o},1400)}).catch(function(){window.prompt('Address',v)})})});
/* home question box: examples only until the live mode opens */
var hf=document.getElementById('askform');
if(hf)hf.addEventListener('submit',function(e){e.preventDefault();location.href='/demo/'});
/* demo */
var D=document.getElementById('demo-data');if(!D)return;
var data=JSON.parse(D.textContent),byId={};data.examples.forEach(function(x){byId[x.id]=x});
var q=document.getElementById('dq'),ab=document.getElementById('a-base'),as=document.getElementById('a-student'),ln=document.getElementById('dline');
function esc(s){return s.replace(/[&<>"]/g,function(m){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]})}
function mark(t,ms){var h=esc(t);(ms||[]).forEach(function(m){var e=esc(m.text);h=h.split(e).join('<span class="made" title="'+esc(m.why)+'">'+e+'</span>')});return h}
function arm(a,x){var h='',n=a.turns.length;a.turns.forEach(function(t,i){
  if(i===1&&x.push)h+='<p class="push"><b>User:</b> '+esc(x.push)+'</p>';
  if(t.code)h+='<pre class="inset"><span class="k">Calculation</span>'+esc(t.code)+'</pre>';
  if(t.out)h+='<pre class="inset"><span class="k">Output</span>'+esc(t.out)+'</pre>';
  h+='<div class="txt">'+mark(t.text,a.marks)+'</div>'});
 h+='<div class="verdict"><span class="chip '+(a.clean?'ok':'no')+'">'+(a.clean?'✓ ':'✕ ')+esc(a.word)+'</span></div>';
 (a.marks||[]).forEach(function(m){h+='<p class="why">Wavy line: '+esc(m.why)+'.</p>'});return h}
function show(id,push){var x=byId[id];if(!x)return;
 var qh='';x.question.forEach(function(m,i){if(i===x.question.length-1)qh+='<p class="turn-user">'+esc(m.text)+'</p>';else qh+='<p class="turn-user prior"><b>'+(m.role==='user'?'User':'Model, earlier')+':</b> '+esc(m.text)+'</p>'});
 q.innerHTML=qh;ab.querySelector('.body').innerHTML=arm(x.arms.base,x);as.querySelector('.body').innerHTML=arm(x.arms.student,x);
 var b=x.arms.base.clean,s=x.arms.student.clean;
 ln.textContent=b&&s?'Both answers are clean on this question.':(!b&&s?'The regular model failed here; the student did not.':(b&&!s?'The student failed here; the regular model did not.':'Both failed on this question.'));
 document.querySelectorAll('.side button').forEach(function(bt){bt.setAttribute('aria-current',bt.dataset.id===id?'true':'false')});
 if(push)history.replaceState(null,'','#'+id)}
document.querySelectorAll('.side button').forEach(function(bt){bt.addEventListener('click',function(){show(bt.dataset.id,true);if(innerWidth<1024)document.getElementById('dq').scrollIntoView({behavior:reduce?'auto':'smooth',block:'start'})})});
var vs=document.querySelectorAll('.viewseg button'),ans=document.querySelector('.answers');
vs.forEach(function(b){b.addEventListener('click',function(){vs.forEach(function(o){o.setAttribute('aria-pressed',o===b?'true':'false')});ans.setAttribute('data-view',b.dataset.view)})});
var h=location.hash.slice(1);show(byId[h]?h:data.examples[0].id,false);
})();
