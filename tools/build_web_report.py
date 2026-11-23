"""Build the interactive web version of the commerce delivery review.

Reads deliverables/delivery-investigation/state-month.csv and controls.json and
writes report/index.html, a self-contained page for GitHub Pages.
Standard library only.

    python tools/build_web_report.py
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from web_report_shell import page

ROOT = Path(__file__).resolve().parents[1]
INVESTIGATION = ROOT / "deliverables" / "delivery-investigation"
OUT = ROOT / "report" / "index.html"


def load() -> dict:
    rows = []
    with open(INVESTIGATION / "state-month.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append([r["purchase_month"], r["state"], int(r["orders"]), int(r["eligible_deliveries"]),
                         int(r["late_deliveries"]), int(r["merchandise_cents"])])
    controls = json.loads((INVESTIGATION / "controls.json").read_text(encoding="utf-8"))
    src = controls["source_totals"]
    got = {"orders": sum(r[2] for r in rows), "eligible_deliveries": sum(r[3] for r in rows),
           "late_deliveries": sum(r[4] for r in rows), "merchandise_cents": sum(r[5] for r in rows)}
    for k, v in got.items():
        if v != src[k]:
            raise SystemExit(f"{k}: {v} does not reconcile to control total {src[k]}")
    return {"rows": rows, "min_eligible": controls["rate_ranking_min_eligible"], "totals": src}


BODY = r"""
<div class="controls" aria-label="Report filters">
  <div class="control"><label for="f-month"><span class="eyebrow">PURCHASE MONTH</span></label><select id="f-month"></select></div>
  <div class="control"><span>SHOW</span><div class="seg" id="f-top"></div></div>
</div>
<section class="overview" id="overview">
  <div class="headline">
    <div class="eyebrow"><span class="num">01</span>THE DELIVERY STORY</div>
    <h1>Two states.<br><span>Two different problems.</span></h1>
    <p class="standfirst">São Paulo and Rio de Janeiro account for about half of all late deliveries, but for different reasons: SP through sheer volume, RJ through a much higher late rate. Choose a month to see how the picture shifts.</p>
    <div class="big-label">ON-TIME RATE <span id="scope-label"></span></div>
    <div class="big" id="k-ontime">—</div>
    <div class="context"><span class="pill" id="k-late">—</span><span>late among <b id="k-elig">—</b> eligible deliveries</span></div>
    <div class="kpis">
      <div><span>ORDERS</span><strong id="k-orders">—</strong><small id="k-merch"></small></div>
      <div><span>SP + RJ SHARE OF LATE</span><strong id="k-share">—</strong><small id="k-share-n"></small></div>
      <div><span>MOST LATE DELIVERIES</span><strong id="k-work">—</strong><small id="k-work-n"></small></div>
      <div><span id="k-hi-label">HIGHEST LATE RATE</span><strong id="k-hi">—</strong><small id="k-hi-n"></small></div>
    </div>
  </div>
  <section class="card" aria-labelledby="trend-title">
    <div class="card-head"><div><div class="eyebrow">BY PURCHASE MONTH</div><h2 id="trend-title">Delivery volume and late rate</h2></div></div>
    <div class="legend"><span><i style="background:var(--blue)"></i>Eligible deliveries</span><span><i style="background:var(--orange)"></i>Late rate</span><span>Select a month to filter the report</span></div>
    <div id="trend" class="chart"></div>
    <div class="detail" aria-live="polite"><span>Month <b id="d-month">—</b></span><span>Eligible <b id="d-elig">—</b></span><span>Late <b id="d-late">—</b></span><span>Late rate <b id="d-rate">—</b></span></div>
    <p class="note">Months with fewer than 100 eligible deliveries at the edges of the source (Sep and Dec 2016, Sep–Oct 2018) are left off the chart but stay in the totals. Eligible means delivered with both a delivery date and an estimated date.</p>
  </section>
</section>
<section id="states">
  <div class="section-intro"><div><div class="eyebrow"><span class="num">02</span>COUNT VERSUS RATE</div><h2>Where to start an investigation</h2></div>
  <p id="threshold-note"></p></div>
  <div class="panels">
    <section class="panel"><div class="panel-title"><h3>Most late deliveries</h3><span>LATE DELIVERIES</span></div><div id="b-count"></div></section>
    <section class="panel"><div class="panel-title"><h3>Highest late rate</h3><span id="rate-unit">LATE RATE</span></div><div id="b-rate"></div></section>
  </div>
</section>
<section class="decision" id="decision"><div class="decision-index">03<span>THE NEXT CHECK</span></div>
  <div><h2>Review São Paulo's late orders in July 2018.</h2><p>That month SP had 100 late deliveries among 2,712 eligible orders. Alagoas had 4 among 22, a higher rate on a far smaller base. Start with the SP orders and request carrier, route and service-promise data before naming a cause.</p></div>
  <div class="decision-note">A workload to investigate.<br><b>The source doesn't establish a cause or describe current service.</b></div></section>
<nav class="links" aria-label="Project links"><a href="https://github.com/ZakJRademacher/commerce-delivery-review">Project repository</a><a href="https://github.com/ZakJRademacher/commerce-delivery-review/blob/main/docs/SQL_INVESTIGATION.md">SQL investigation</a><a href="https://github.com/ZakJRademacher/commerce-delivery-review/blob/main/docs/cleaning-rules.md">Definitions</a><a href="https://github.com/ZakJRademacher/commerce-delivery-review/raw/main/deliverables/Commerce%20Delivery%20Priorities.pbix">Power BI report (.pbix)</a></nav>
<footer><span id="foot-totals"></span><span>Independent, noncommercial portfolio analysis of historical public data</span>
<p>Source: Olist and André Sionek, <i>Brazilian E-Commerce Public Dataset by Olist</i> (Kaggle), purchases 2016–2018. The source and the data shown on this page are licensed <a href="https://creativecommons.org/licenses/by-nc-sa/4.0/">CC BY-NC-SA 4.0</a>; see <a href="https://github.com/ZakJRademacher/commerce-delivery-review/blob/main/docs/source-and-license.md">source and license</a>. Merchandise excludes freight and isn't profit or recognized revenue. The 100-eligible cutoff is a display rule, not a significance test. Figures are computed in the browser from the project's state-by-month table and reconcile to its control totals.</p></footer>
"""

SCRIPT = r"""
const rows=DATA.rows.map(([m,s,o,e,l,c])=>({m,s,o,e,l,c})),MIN=DATA.min_eligible;
const MN=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const mlabel=m=>MN[+m.slice(5)-1]+' '+m.slice(0,4);
const state={month:'all',top:'10'};
const sum=rs=>rs.reduce((a,r)=>(a.o+=r.o,a.e+=r.e,a.l+=r.l,a.c+=r.c,a),{o:0,e:0,l:0,c:0});
function group(rs,key){const g=new Map();for(const r of rs){const a=g.get(r[key])||{key:r[key],o:0,e:0,l:0,c:0};a.o+=r.o;a.e+=r.e;a.l+=r.l;a.c+=r.c;g.set(r[key],a);}return[...g.values()].map(a=>({...a,rate:a.e?a.l/a.e:null}));}
const scoped=()=>rows.filter(r=>state.month==='all'||r.m===state.month);
const months=group(rows,'m').sort((a,b)=>a.key.localeCompare(b.key));
const sel=$('f-month');sel.innerHTML='<option value="all">All months</option>'+months.filter(m=>m.o>0).map(m=>`<option value="${m.key}">${mlabel(m.key)}</option>`).join('');
sel.addEventListener('change',()=>{state.month=sel.value;render();});
const brl=c=>'R$ '+(c/100).toLocaleString('en-US',{maximumFractionDigits:0});
function kpis(){
  const t=sum(scoped()),st=group(scoped(),'s');
  $('scope-label').textContent=state.month==='all'?'All months':mlabel(state.month);
  $('k-ontime').textContent=pct(t.e?1-t.l/t.e:null);$('k-late').textContent=int(t.l);$('k-elig').textContent=int(t.e);
  $('k-orders').textContent=int(t.o);$('k-merch').textContent=brl(t.c)+' merchandise';
  const sprj=st.filter(s=>s.key==='SP'||s.key==='RJ').reduce((a,s)=>a+s.l,0);$('k-share').textContent=pct(t.l?sprj/t.l:null);$('k-share-n').textContent=`${int(sprj)} of ${int(t.l)} late deliveries`;
  const work=[...st].sort((a,b)=>b.l-a.l)[0],hi=st.filter(s=>s.e>=MIN).sort((a,b)=>b.rate-a.rate)[0];
  $('k-work').textContent=work?work.key:'—';$('k-work-n').textContent=work?`${int(work.l)} late · ${pct(work.rate)}`:'';
  $('k-hi-label').textContent=`HIGHEST LATE RATE (${MIN}+ ELIGIBLE)`;$('k-hi').textContent=hi?hi.key:'—';$('k-hi-n').textContent=hi?`${pct(hi.rate)} · ${int(hi.l)} of ${int(hi.e)}`:'No state reaches the cutoff';
}
function trend(){
  const ms=months.filter(m=>m.e>=MIN),W=720,H=290,L=52,R=46,T=16,B=36;
  const maxE=Math.max(...ms.map(m=>m.e)),top=Math.ceil(maxE/2000)*2000,maxR=.25;
  const step=(W-L-R)/ms.length,bw=Math.min(22,step*.66),x=i=>L+step*(i+.5),y=v=>T+(1-v/top)*(H-T-B),yr=v=>T+(1-Math.min(v,maxR)/maxR)*(H-T-B);
  let s=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Eligible deliveries and late rate by purchase month">`;
  for(let k=0;k<=4;k++){const v=top*k/4;s+=`<line class="grid-line" x1="${L}" x2="${W-R}" y1="${y(v)}" y2="${y(v)}"/><text class="axis" x="${L-10}" y="${y(v)+4}" text-anchor="end">${int(v)}</text><text class="axis" x="${W-R+10}" y="${y(v)+4}">${(maxR*k/4*100).toFixed(0)}%</text>`;}
  ms.forEach((m,i)=>{const on=state.month===m.key;
    s+=`<rect class="bar-mark${state.month!=='all'&&!on?' dim':''}" data-m="${m.key}" x="${x(i)-bw/2}" y="${y(m.e)}" width="${bw}" height="${H-B-y(m.e)}" rx="3" fill="var(--blue)" tabindex="0" role="button" aria-label="${mlabel(m.key)}: ${int(m.l)} late of ${int(m.e)} eligible, ${pct(m.rate)}"><title>${mlabel(m.key)} — ${int(m.l)} late of ${int(m.e)} (${pct(m.rate)})</title></rect>`;
    if(m.key.endsWith('-01')||m.key.endsWith('-07'))s+=`<text class="axis" x="${x(i)}" y="${H-14}" text-anchor="middle">${MN[+m.key.slice(5)-1]} ${m.key.slice(2,4)}</text>`;});
  s+=`<path d="${ms.map((m,i)=>(i?'L':'M')+x(i).toFixed(1)+','+yr(m.rate).toFixed(1)).join(' ')}" fill="none" stroke="var(--orange)" stroke-width="3" stroke-linejoin="round"/>`;
  ms.forEach((m,i)=>{if(state.month===m.key)s+=`<circle cx="${x(i)}" cy="${yr(m.rate)}" r="6" fill="var(--orange)" stroke="var(--card)" stroke-width="2"/>`;});
  $('trend').innerHTML=s+'</svg>';
  $('trend').querySelectorAll('.bar-mark').forEach(b=>{const pick=()=>{state.month=state.month===b.dataset.m?'all':b.dataset.m;sel.value=state.month;render();};b.addEventListener('click',pick);b.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();pick();}});});
  const d=state.month==='all'?sum(rows):months.find(m=>m.key===state.month);
  $('d-month').textContent=state.month==='all'?'All months':mlabel(state.month);$('d-elig').textContent=int(d.e);$('d-late').textContent=int(d.l);$('d-rate').textContent=pct(d.e?d.l/d.e:null);
}
function panels(){
  const st=group(scoped(),'s').filter(s=>s.e>0),n=state.top==='all'?Infinity:+state.top;
  const byCount=[...st].sort((a,b)=>b.l-a.l).slice(0,n);
  const ranked=st.filter(s=>s.e>=MIN).sort((a,b)=>b.rate-a.rate).slice(0,n),hidden=st.filter(s=>s.e<MIN).length;
  const meta=s=>`${int(s.l)} late of ${int(s.e)} eligible · ${pct(s.rate)} · ${int(s.o)} orders`;
  $('b-count').innerHTML=bars(byCount,{value:s=>s.l,label:s=>s.key,right:s=>int(s.l),meta});
  $('b-rate').innerHTML=ranked.length?bars(ranked,{value:s=>s.rate,max:Math.max(...ranked.map(s=>s.rate)),label:s=>s.key,right:s=>pct(s.rate),cls:()=>'alt',meta}):'<p class="note">No state has 100 or more eligible deliveries in this month.</p>';
  $('threshold-note').innerHTML=`The rate ranking includes states with at least ${MIN} eligible deliveries. <b>${hidden} state${hidden===1?'':'s'} below that cutoff stay in the count list and totals.</b>`;
}
function render(){kpis();trend();panels();}
seg('f-top',[['10','Top 10 states'],['all','All states']],state.top,v=>{state.top=v;panels();});
const T0=DATA.totals;$('foot-totals').textContent=`${int(T0.orders)} orders · ${int(T0.item_lines)} item lines · ${int(T0.eligible_deliveries)} eligible deliveries · ${int(T0.late_deliveries)} late`;
render();watchSections(['overview','states','decision']);
"""


def main() -> None:
    data = load()
    html_text = page(
        url="https://zakjrademacher.github.io/commerce-delivery-review/report/",
        image="https://zakjrademacher.github.io/commerce-delivery-review/deliverables/portfolio-cover-wide.png",
        title="Commerce Delivery Review",
        description="Interactive review of Olist delivery performance: late-delivery counts versus late rates by state and purchase month.",
        rail_name="Delivery<br>Priorities",
        nav=[("overview", "Overview"), ("states", "Count vs rate"), ("decision", "Next check")],
        window_label="SNAPSHOT",
        window_value="<strong>99,441 orders</strong>Purchases 2016–2018",
        credit="HISTORICAL REVIEW<br>Brazilian e-commerce<br>Zak Rademacher",
        identity="OPERATIONS / DELIVERY REVIEW",
        period="2016–2018 <span>/</span> HISTORICAL PUBLIC DATA",
        body=BODY,
        data=data,
        script=SCRIPT,
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html_text, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(html_text):,} bytes)")


if __name__ == "__main__":
    main()
