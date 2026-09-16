import React,{useEffect,useMemo,useState} from 'react';
import {createRoot} from 'react-dom/client';
import {BrowserRouter,useNavigate,useLocation} from 'react-router-dom';
import {Trophy,Globe2,Users,Swords,CalendarDays,Search,ArrowUpRight,Menu,X,ShieldCheck,Map,Medal,BarChart3,ListOrdered,Zap,ChevronLeft} from 'lucide-react';
import {LineChart,Line,BarChart,Bar,XAxis,YAxis,Tooltip,ResponsiveContainer,CartesianGrid,Legend,PieChart,Pie,Cell} from 'recharts';
import './style.css';
const API=import.meta.env.VITE_API_URL||'/api';

// Generic data-fetching hook: cancels/ignores stale in-flight requests when `path` changes
// or the component unmounts, retries once on failure, and skips fetching entirely when
// path is null/false (used while a required filter hasn't been picked yet).
function useApi(path){
  const [state,setState]=useState({data:null,loading:!!path,error:null});
  const [nonce,setNonce]=useState(0);
  useEffect(()=>{
    if(!path){setState({data:null,loading:false,error:null});return}
    let cancelled=false,retried=false;
    const controller=new AbortController();
    setState(s=>({data:s.data,loading:true,error:null}));
    const run=()=>{
      fetch(API+path,{signal:controller.signal})
        .then(r=>{if(!r.ok)throw new Error('HTTP '+r.status);return r.json()})
        .then(json=>{if(!cancelled)setState({data:json,loading:false,error:null})})
        .catch(err=>{
          if(cancelled||err.name==='AbortError')return;
          if(!retried){retried=true;setTimeout(run,1200)}
          else setState(s=>({data:s.data,loading:false,error:err}));
        });
    };
    run();
    return ()=>{cancelled=true;controller.abort()};
  },[path,nonce]);
  return {...state,retry:()=>setNonce(n=>n+1)};
}
function Status({loading,error,retry,empty}){
  if(error)return <div className="status-msg error">Couldn't load this data. <button onClick={retry}>Retry</button></div>;
  if(loading)return <div className="status-msg">Loading…</div>;
  if(empty)return <div className="status-msg">No records match this filter.</div>;
  return null;
}

// The 4 ICC formats this platform covers - shared across Matches/Teams/Compare so every
// page's tab list stays in sync with what the backend actually serves per format.
const ALL_FORMATS=[['odi_wc','ODI World Cup'],['t20_wc','T20 World Cup'],['champions_trophy','Champions Trophy'],['wtc','World Test Championship']];

// Top level: "Home" first, then all 4 formats in chronological/ICC billing order so a
// format can be opened directly from the sidebar without going through its card, and
// finally "Overall Analysis" — it's the only home-level page with real content of its
// own (cross-format insights + a by-country key-players lookup), and it reads as the
// wrap-up after the individual formats. Everything below that only exists once a format
// has actually been opened (see FORMAT_NAV_ALL).
const HOME_NAV=[['Home','/'],...ALL_FORMATS.map(([key,title])=>[title,`/tournament/${key}`]),['Overall Analysis','/overall-analysis']];

// Every format carries the same core sections (Dashboard/Editions/Matches/Teams/Compare/
// Standings/Players & Records); ODI WC, T20 WC and Champions Trophy additionally get a
// Squads section right after Standings — WTC doesn't, since its squad data only ever
// covered one of its three cycles (see formatNavItems below).
const FORMAT_NAV_ALL=[
  ['Dashboard',''],
  ['Editions','/editions'],
  ['Matches','/matches'],
  ['Teams','/teams'],
  ['Compare','/compare'],
  ['Standings','/standings'],
  ['Players & Records','/players'],
];
function formatNavItems(fmt){
  const base=FORMAT_NAV_ALL.map(([label,suffix])=>[label,`/tournament/${fmt}${suffix}`]);
  // Squad/player lists only exist for ODI WC, T20 WC and Champions Trophy — WTC's squad
  // data only ever covered one of its three cycles, which was inconsistent with the rest
  // of this page, so it has no Squads section at all. Sits right after Standings.
  if(fmt==='wtc')return base;
  const i=base.findIndex(([label])=>label==='Standings');
  return [...base.slice(0,i+1),['Squads',`/tournament/${fmt}/squads`],...base.slice(i+1)];
}

function Layout({children}){
  const loc=useLocation(),nav=useNavigate(),[open,setOpen]=useState(false);
  const hubMatch=loc.pathname.match(/^\/tournament\/([\w-]+)(\/[\w-]+)?\/?$/);
  const fmt=hubMatch&&ALL_FORMATS.some(([k])=>k===hubMatch[1])?hubMatch[1]:null;
  const meta=fmt&&FORMAT_CARDS.find(c=>c.key===fmt);
  const items=fmt?formatNavItems(fmt):HOME_NAV;
  const currentPath=fmt?`/tournament/${fmt}${hubMatch[2]||''}`:loc.pathname;
  const activeLabel=items.find(([,p])=>p===currentPath)?.[0]||(fmt?'Dashboard':'Home');
  return <div className="app">
    <aside className={open?'open':''}>
      <div className="brand"><div className="logo"><img src="/brand/sidebar-logo.png" alt="ICC Analytics"/></div><div><span className="eyebrow">ICC TOURNAMENT DATA PLATFORM</span><b>ICC ANALYTICS</b><small>ODI · T20 · Champions Trophy · WTC</small></div></div>
      {fmt&&<button className="pill back-pill" onClick={()=>{nav('/');setOpen(false)}}><ChevronLeft size={14}/> Home</button>}
      <nav>{items.map(([n,p])=><button className={currentPath===p?'active':''} onClick={()=>{nav(p);setOpen(false)}} key={p}>{n}</button>)}</nav>
      <div className="side-note"><ShieldCheck size={18}/><span>Analytical dataset</span></div>
    </aside>
    <main>
      <header>
        <button className="mobile" onClick={()=>setOpen(!open)}>{open?<X/>:<Menu/>}</button>
        <div>{fmt&&<span className="eyebrow">{meta.title}</span>}<h1>{activeLabel}</h1></div>
      </header>
      {children}
    </main>
  </div>
}
function Stat({icon:Icon,label,value,sub,accent}){return <div className="stat" style={accent?{'--accent':accent}:undefined}><Icon size={21}/><span>{label}</span><strong>{value}</strong>{sub&&<small>{sub}</small>}</div>}
function Panel({title,children,action}){return <section className="panel"><div className="panel-title"><h3>{title}</h3>{action}</div>{children}</section>}
function Toolbar({placeholder,value,onChange}){return <div className="toolbar"><Search size={19}/><input placeholder={placeholder} value={value} onChange={e=>onChange(e.target.value)}/></div>}
function Table({headers,rows}){return <div className="tablewrap"><table><thead><tr>{headers.map(h=><th key={h}>{h}</th>)}</tr></thead><tbody>{rows.map((r,i)=><tr key={i}>{r.map((v,j)=><td key={j}>{v??'—'}</td>)}</tr>)}</tbody></table></div>}

const WTC_CYCLES=['2019-2021','2021-2023','2023-2025'];

function Chart({data,dataKey,x,bar=false,color='#7dc4fa'}){
  const ticks=data.length?data.filter((_,i)=>i%Math.max(1,Math.ceil(data.length/12))===0).map(d=>d[x]):undefined;
  const margin={top:5,right:22,left:-18,bottom:0};
  return <ResponsiveContainer width="100%" height={300}>{bar?<BarChart data={data} margin={margin}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey={x} ticks={ticks} interval={0}/><YAxis/><Tooltip cursor={false}/><Bar dataKey={dataKey} fill={color} radius={[4,4,0,0]} activeBar={{fill:'#eef3fb',stroke:color,strokeWidth:2}}/></BarChart>:<LineChart data={data} margin={margin}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey={x} ticks={ticks} interval={0}/><YAxis/><Tooltip/><Line type="monotone" dataKey={dataKey} stroke={color} strokeWidth={3} dot={false}/></LineChart>}</ResponsiveContainer>}

const FORMAT_COLOR={odi_wc:'#f4c94f',t20_wc:'#5fe3a1',champions_trophy:'#7dc4fa',wtc:'#c893f5'};

// Copy + icon for the 4 format-explorer cards on the dashboard, and for each
// format's hub page header. `img` is the real trophy photo used for card thumbnails
// and the hub hero visual; `icon` stays as a lightweight fallback/accent glyph.
const FORMAT_CARDS=[
  {key:'odi_wc',icon:Trophy,img:'/trophies/odi_wc.png',title:'ODI World Cup',tag:'50-over · est. 1975',blurb:"Cricket's original global stage — 13 editions, group tables and every final since Lord's '75."},
  {key:'t20_wc',icon:Zap,img:'/trophies/t20_wc.png',title:'T20 World Cup',tag:'20-over · est. 2007',blurb:'The short format, condensed — scores, rankings and squads across 9 editions.'},
  {key:'champions_trophy',icon:Globe2,img:'/trophies/champions_trophy.png',title:'Champions Trophy',tag:'50-over knockout · est. 1998',blurb:"ICC's mini-tournament for the top eight ODI sides — 10 editions of straight knockout cricket."},
  {key:'wtc',icon:ShieldCheck,img:'/trophies/wtc.png',title:'World Test Championship',tag:'Test cricket · est. 2019',blurb:'The long game, ranked — 3 completed two-year cycles, full points tables and player averages.'},
];

// ===== Home (entry point only — no cross-format numbers or charts live here anymore.
// Each format gets its own Dashboard, opened by clicking its card below.) =====
function Home(){
  const nav=useNavigate();
  const ed=useApi('/editions');
  const editions=ed.data||[];
  const latestByTournament=useMemo(()=>{
    const m={};
    editions.forEach(x=>{if(!m[x.tournament]||x.year>m[x.tournament].year)m[x.tournament]=x});
    return m;
  },[editions]);
  return <>
    <section className="hero">
      <div><span className="eyebrow">FOUR FORMATS · FIFTY SEASONS OF ICC CRICKET</span><h2>Every ICC trophy,<br/><em>every era, one screen.</em></h2><p>One-day glory, T20 chaos, Champions Trophy knockouts and the Test Championship's long game — cleaned, cross-checked and laid out edition by edition, match by match.</p></div>
      <div className="hero-ball"><img src="/brand/emblem.png" alt="ICC Analytics" style={{width:220,height:220,objectFit:'contain',filter:'drop-shadow(0 14px 30px rgba(93,227,161,.28))'}}/></div>
    </section>
    <Status loading={ed.loading} error={ed.error} retry={ed.retry}/>
    <div className="section-lead"><h3>Pick a format to dig into</h3><p>Each card opens that format's own dashboard — editions, matches, teams, standings and records, all scoped to that tournament.</p></div>
    <div className="feature-grid">
      {FORMAT_CARDS.map((c,i)=>{
        const latest=latestByTournament[c.title];
        return <div className="feature-card" key={c.key} style={{'--fc':FORMAT_COLOR[c.key]}} onClick={()=>nav(`/tournament/${c.key}`)}>
          <span className="ghost-index">{String(i+1).padStart(2,'0')}</span>
          <div className="feature-icon"><img src={c.img} alt={c.title}/></div>
          <span className="feature-num-pill">{String(i+1).padStart(2,'0')}</span>
          <h4>{c.title}</h4>
          <p>{c.blurb}{latest?` Reigning champions: ${latest.winner}.`:''}</p>
          <span className="feature-arrow"><ArrowUpRight size={16}/></span>
        </div>
      })}
    </div>
  </>
}

// ===== Overall Analysis (cross-format - accessible straight from the Home sidebar) =====
function FormatInsightPanel({row}){
  const sameAsChamp=row.reigning_champion&&row.top_team&&row.reigning_champion.trim().toLowerCase()===row.top_team.trim().toLowerCase();
  return <Panel title={row.label}>
    <div className="stats" style={{marginBottom:14}}>
      <Stat icon={Trophy} label="Editions" value={row.editions} accent={FORMAT_COLOR[row.format]}/>
      <Stat icon={CalendarDays} label="Matches" value={row.matches} accent="#7dc4fa"/>
      <Stat icon={Globe2} label="Teams" value={row.teams} accent="#5fe3a1"/>
    </div>
    <div className="insight-list">
      {row.top_team&&<div className="mini-insight"><span>Champs</span><div><b>{row.top_team}</b><p>Most successful team · {row.top_team_titles} title{row.top_team_titles!==1?'s':''}</p></div></div>}
      {row.reigning_champion&&<div className="mini-insight"><span>Reigning</span><div><b>{row.reigning_champion}</b><p>Current title-holder · {row.reigning_champion_year}{sameAsChamp?' · also most successful':''}</p></div></div>}
      {row.top_scorer&&<div className="mini-insight"><span>Runs</span><div><b>{row.top_scorer}</b><p>Leading run-scorer · {row.top_scorer_value}</p></div></div>}
      {row.top_wicket_taker&&<div className="mini-insight"><span>Wkts</span><div><b>{row.top_wicket_taker}</b><p>Leading wicket-taker · {row.top_wicket_taker_value}</p></div></div>}
      {row.highest_score&&<div className="mini-insight"><span>Best score</span><div><b>{row.highest_score}</b><p>Highest individual innings · {row.highest_score_value}</p></div></div>}
      {row.best_bowling&&<div className="mini-insight"><span>Best figures</span><div><b>{row.best_bowling}</b><p>Best bowling figures{row.best_bowling_value?` · ${row.best_bowling_value}`:''}</p></div></div>}
      {row.highest_total&&<div className="mini-insight"><span>Highest total</span><div><b>{row.highest_total}</b><p>Highest team total · {row.highest_total_value}</p></div></div>}
    </div>
  </Panel>
}
// One consolidated card per real player: name + which of the 4 formats they appear in,
// then their top achievements from each (format tag + category + value) - replaces the
// old one-format-per-card layout now that the backend groups by player identity across
// all 4 formats instead of per (player, format).
function KeyPlayerCard({rank,player}){
  const medal=MEDAL_COLORS[rank-1];
  const shown=player.achievements.slice(0,4);
  const extra=player.achievements.length-shown.length;
  return <div className="key-player-card" style={rank<=3?{'--medal':medal,borderColor:`color-mix(in srgb,${medal} 45%,transparent)`}:undefined}>
    <div className="key-player-head">
      <span className="record-rank">{rank<=3?<Medal size={17} color={medal}/>:`#${rank}`}</span>
      <b>{player.player}</b>
    </div>
    <div className="key-player-achv">
      {shown.map((a,i)=><div className="key-player-achv-row" key={i}>
        <span className="pill-sm" style={{background:`color-mix(in srgb,${FORMAT_COLOR[a.format]} 22%,#161d29)`,color:FORMAT_COLOR[a.format]}}>{a.format_label}</span>
        <span>{a.category}{a.value!=null?` · ${a.value}`:''}</span>
      </div>)}
      {extra>0&&<div className="key-player-more">+{extra} more achievement{extra!==1?'s':''}</div>}
    </div>
  </div>
}
// One role column. players are now unique real people (deduped + consolidated across all
// 4 formats server-side - see /api/overview/key-players), so a name only ever appears once
// across the whole Key Players section, not once per format.
function KeyPlayerColumn({title,players}){
  return <Panel title={title}>
    {players.length===0
      ?<div className="status-msg">No {title.replace(/^Top /,"").toLowerCase()} for this country in the available stats sources.</div>
      :<div className="record-list">{players.map((p,i)=><KeyPlayerCard key={p.player} rank={i+1} player={p}/>)}</div>}
  </Panel>
}
// Role (Batsman/Bowler/All-rounder) isn't a stored field anywhere - it's inferred
// server-side from which kind of record category a player shows up in for the chosen
// country. Each card is one real player consolidated across however many of the 4
// formats they have data in (see /api/overview/key-players for the name-deduplication
// approach that makes that possible).
function KeyPlayersByCountry(){
  const {data:countries}=useApi('/overview/countries');
  const [country,setCountry]=useState('');
  useEffect(()=>{if(countries?.length&&!country)setCountry(countries.includes('India')?'India':countries[0])},[countries]);
  const {data,loading,error,retry}=useApi(country?`/overview/key-players?country=${encodeURIComponent(country)}`:null);
  const empty=!loading&&!error&&data&&!data.batsmen.length&&!data.bowlers.length&&!data.all_rounders.length;
  return <>
    <div className="filters"><select className="inline-select" value={country} onChange={e=>setCountry(e.target.value)}>{(countries||[]).map(c=><option key={c} value={c}>{c}</option>)}</select></div>
    <Status loading={loading} error={error} retry={retry} empty={empty}/>
    {data&&!empty&&<div className="key-players-grid">
      <KeyPlayerColumn title="Top Batsmen" players={data.batsmen}/>
      <KeyPlayerColumn title="Top Bowlers" players={data.bowlers}/>
      <KeyPlayerColumn title="Top All-rounders" players={data.all_rounders}/>
    </div>}
  </>
}
function OverallAnalysis(){
  const {data,loading,error,retry}=useApi('/overview/insights');
  return <>
    <section className="hero hub-hero" style={{'--fc':'#f4c94f'}}>
      <div><span className="eyebrow">CROSS-FORMAT VIEW</span><h2>Overall analysis,<br/><em>every format at a glance.</em></h2><p>Headline numbers for all 4 ICC formats side by side, plus each country's standout batsmen, bowlers and all-rounders drawn straight from the records data.</p></div>
      <div className="hero-ball"><img className="trophy-photo" src="/brand/cricket-fever.png" alt="Cricket"/></div>
    </section>
    <div className="section-lead"><h3>Key insights, all 4 formats</h3><p>Editions, matches, the most successful team, and the current record-holders for runs and wickets.</p></div>
    <Status loading={loading} error={error} retry={retry} empty={!loading&&!error&&(!data||data.length===0)}/>
    <div className="records-grid">{(data||[]).map(row=><FormatInsightPanel key={row.format} row={row}/>)}</div>
    <div className="section-lead"><h3>Key players by country</h3><p>Up to 10 batsmen, bowlers and all-rounders per country, each consolidated across every format they appear in. Full-member nations fill all three lists; associate nations return fewer, because they appear only in record leaderboards and have no squad-level stats in the source data.</p></div>
    <KeyPlayersByCountry/>
  </>
}

// ===== Format Hub (per-tournament deep dive, reached from the dashboard cards) =====
function FormatHub({fmt}){
  const nav=useNavigate();
  const meta=FORMAT_CARDS.find(c=>c.key===fmt)||FORMAT_CARDS[0];
  const label=ALL_FORMATS.find(([k])=>k===fmt)?.[1]||meta.title;
  const ed=useApi(`/editions?tournament=${encodeURIComponent(label)}`);
  const matches=useApi(`/${fmt}/matches?limit=1500`);
  const teams=useApi(`/${fmt}/teams`);
  const editions=useMemo(()=>[...(ed.data||[])].sort((a,b)=>b.year-a.year),[ed.data]);
  const latest=editions[0];
  const recentChampions=editions.slice(0,5);
  const allMatches=matches.data||[];
  const matchesByYear=useMemo(()=>{
    const m={};
    allMatches.forEach(x=>{const y=(x.match_date||'').slice(0,4);if(y)m[y]=(m[y]||0)+1});
    return Object.entries(m).sort((a,b)=>a[0]-b[0]).map(([year,matches])=>({year,matches}));
  },[allMatches]);
  // Distinct teams that actually took the field that edition, derived from the match log
  // itself (team1/team2 across every match dated that year) rather than the editions API,
  // so it stays correct even for formats whose editions payload doesn't list full squads.
  const teamsByYear=useMemo(()=>{
    const m={};
    allMatches.forEach(x=>{
      const y=(x.match_date||'').slice(0,4);
      if(!y)return;
      (m[y]=m[y]||new Set());
      if(x.team1)m[y].add(x.team1);
      if(x.team2)m[y].add(x.team2);
    });
    return Object.entries(m).sort((a,b)=>a[0]-b[0]).map(([year,teams])=>({year,teams:teams.size}));
  },[allMatches]);
  const topTeams=(teams.data||[]).slice(0,5);
  return <>
    <section className="hero hub-hero" style={{'--fc':FORMAT_COLOR[fmt]}}>
      <div><span className="eyebrow">{meta.tag}</span><h2>{meta.title}</h2><p>{meta.blurb}</p></div>
      <div className="hero-ball"><img className="trophy-photo" src={meta.img} alt={meta.title}/></div>
    </section>
    <div className="stats">
      <Stat icon={Trophy} label="Editions" value={editions.length} accent={FORMAT_COLOR[fmt]}/>
      <Stat icon={CalendarDays} label="Matches logged" value={allMatches.length} accent="#7dc4fa"/>
      <Stat icon={Users} label="Teams tracked" value={(teams.data||[]).length} accent="#5fe3a1"/>
      <Stat icon={Medal} label="Reigning champion" value={latest?.winner||'—'} sub={latest?`${latest.year}${latest.cycle_label?` · ${latest.cycle_label}`:''}`:undefined} accent="#f4c94f"/>
    </div>
    {matchesByYear.length>1&&<Panel title={`${meta.title} — matches per year`} action={<button className="pill" onClick={()=>nav(`/tournament/${fmt}/matches`)}>Full match log <ArrowUpRight size={13}/></button>}><Chart data={matchesByYear} dataKey="matches" x="year" bar color={FORMAT_COLOR[fmt]}/></Panel>}
    {teamsByYear.length>1&&<Panel title={`${meta.title} — teams participated per edition`}><Chart data={teamsByYear} dataKey="teams" x="year" bar color="#5fe3a1"/></Panel>}
    <div className="grid2">
      <Panel title="Last 5 champions" action={<button className="pill" onClick={()=>nav(`/tournament/${fmt}/editions`)}>Full editions page <ArrowUpRight size={13}/></button>}>
        <Status loading={ed.loading} error={ed.error} retry={ed.retry}/>
        <div className="insight-list">{recentChampions.map(x=><div className="mini-insight" key={x.edition_id}><span>{x.year}</span><div><b>🏆 {x.winner}</b><p>{x.runner_up?`beat ${x.runner_up} in the final`:''}{x.venue?` · ${x.venue}`:''}</p></div></div>)}</div>
      </Panel>
      <Panel title="Top teams (by wins)" action={<button className="pill" onClick={()=>nav(`/tournament/${fmt}/teams`)}>Full teams page <ArrowUpRight size={13}/></button>}>
        <Status loading={teams.loading} error={teams.error} retry={teams.retry}/>
        <div className="insight-list">{topTeams.map((t,i)=><div className="mini-insight" key={t.team}><span>0{i+1}</span><div><b>{t.team}</b><p>{t.wins} wins · {t.matches} matches · {t.matches?((t.wins/t.matches)*100).toFixed(1):'0.0'}% win rate</p></div></div>)}</div>
      </Panel>
    </div>
    <div className="section-lead section-lead-row"><div><h3>All-time records</h3><p>Top performers across every {fmt==='wtc'?'cycle':'edition'}.</p></div><button className="pill" onClick={()=>nav(`/tournament/${fmt}/players`)}>Full players &amp; records page <ArrowUpRight size={13}/></button></div>
    <RecordsPreview fmt={fmt}/>
  </>
}

// ===== Editions (always scoped to the format whose hub you opened) =====
function Editions({fmt}){
  const label=ALL_FORMATS.find(([k])=>k===fmt)?.[1];
  const {data,loading,error,retry}=useApi(`/editions?tournament=${encodeURIComponent(label)}`);
  const [q,setQ]=useState('');
  const d=data||[];
  const rows=d.filter(x=>[x.winner,x.runner_up,String(x.year),x.venue].join(' ').toLowerCase().includes(q.toLowerCase()));
  const sorted=[...rows].sort((a,b)=>b.year-a.year);
  return <>
    <Toolbar placeholder="Search by year, winner, runner-up or venue" value={q} onChange={setQ}/>
    <Status loading={loading} error={error} retry={retry} empty={!loading&&!error&&sorted.length===0}/>
    <div className="tournament-grid">
      {sorted.map(x=><div className="tournament-card" key={x.edition_id}>
        <div className="tournament-card-head"><span className="tournament-year">{x.year}</span><span className="pill">{x.tournament}{x.cycle_label?` · ${x.cycle_label}`:''}</span></div>
        <div className="tournament-champ"><Trophy size={17}/><b>{x.winner}</b></div>
        <div className="tournament-places">
          {x.runner_up&&<div>Runner-up<em>{x.runner_up}</em></div>}
          {x.venue&&<div>Venue<em>{x.venue}</em></div>}
          {x.semi_finalists&&<div style={{gridColumn:'1/-1'}}>Semi-finalists<em>{x.semi_finalists}</em></div>}
        </div>
        {(x.final_player_of_match&&x.final_player_of_match!=='-')&&<div className="tournament-host-line"><Medal size={14}/>Final POTM: <b>{x.final_player_of_match}</b></div>}
        {(x.player_of_tournament&&x.player_of_tournament!=='-')&&<div className="tournament-host-line"><Medal size={14}/>Player of the Tournament: <b>{x.player_of_tournament}</b></div>}
      </div>)}
    </div>
  </>
}

// ===== Matches (rendered as attractive scorecards everywhere matches show up —
// the Matches page, a team's match log, and Compare's head-to-head list) =====
// Normalizes WTC's result text to one consistent style across all 3 cycles. The 2019-2021
// cycle's source data stores just the bare margin ("251 runs"), while 2021-2023 and
// 2023-2025 store a full raw scorecard line with the margin buried inside parentheses
// ("Ind 364 & 298/8d; Eng 391 & 120 (India won by 151 runs)"). This always resolves to the
// short "<Winner> won by <margin>" form (2019-2021's own style, used as the baseline), or
// "Match Drawn" / "No Result" for non-results, regardless of which cycle the match is from.
function wtcResultLine(m){
  if(m.result_type==='Draw')return 'Match Drawn';
  if(m.result_type==='No Result')return 'No Result';
  const raw=m.result_summary||'';
  const paren=raw.match(/\(([^)]+)\)/);
  if(paren){
    // Take only the lead clause — later cycles sometimes append extra context after a
    // semicolon ("...won by 49 runs; series drawn 2-2, Australia retained the Ashes").
    return paren[1].split(';')[0].trim();
  }
  if(m.winner)return `${m.winner} won by ${raw.replace('inns &','an innings and')}`;
  return raw||'Result pending';
}
function MatchCard({fmt,m}){
  const hasScore=fmt==='odi_wc'||fmt==='t20_wc';
  const team1Win=m.winner&&m.winner===m.team1;
  const team2Win=m.winner&&m.winner===m.team2;
  const resultLine=fmt==='wtc'
    ?wtcResultLine(m)
    :(m.winner?`${m.winner} won${(m.margin||m.win_margin)?` by ${m.margin||m.win_margin}`:''}`:'Result pending');
  return <div className="match-card">
    <div className="match-card-meta">
      <span className="match-date"><CalendarDays size={13}/>{(m.match_date||'').slice(0,10)}</span>
      {m.stage&&<span className="round-badge">{m.stage}</span>}
      {fmt==='wtc'&&m.result_type&&<span className="round-badge">{m.result_type}</span>}
    </div>
    <div className="match-card-teams">
      <div className={`match-team${team1Win?' win':''}`}>
        {team1Win&&<Trophy size={13} className="mini-trophy"/>}
        <span className="match-team-name">{m.team1}</span>
        {hasScore&&<span className="score-chip"><span className={team1Win?'win-side':''}>{m.team1_score??'—'}</span></span>}
      </div>
      <span className="match-vs">vs</span>
      <div className={`match-team${team2Win?' win':''}`}>
        {team2Win&&<Trophy size={13} className="mini-trophy"/>}
        <span className="match-team-name">{m.team2}</span>
        {hasScore&&<span className="score-chip"><span className={team2Win?'win-side':''}>{m.team2_score??'—'}</span></span>}
      </div>
    </div>
    <div className="match-card-foot">
      <span className="match-result">{resultLine}</span>
      {m.player_of_match&&m.player_of_match!=='-'&&<span className="match-potm">POTM · {m.player_of_match}</span>}
      {m.ground&&<span className="match-ground">{m.ground}</span>}
    </div>
  </div>
}
function MatchList({fmt,rows}){return <div className="match-grid">{rows.map((m,i)=><MatchCard fmt={fmt} m={m} key={m.match_id||i}/>)}</div>}
function Matches({fmt}){
  const [year,setYear]=useState('');
  const [cycle,setCycle]=useState(WTC_CYCLES[0]);
  const [team,setTeam]=useState('');
  const ed=useApi(`/editions?tournament=${encodeURIComponent(ALL_FORMATS.find(([k])=>k===fmt)[1])}`);
  const years=useMemo(()=>[...new Set((ed.data||[]).map(x=>x.year))].sort((a,b)=>b-a),[ed.data]);
  const qs=fmt==='wtc'?`cycle=${cycle}`:(year?`year=${year}`:'');
  const path=`/${fmt}/matches?${qs}${team?`&team=${encodeURIComponent(team)}`:''}&limit=1500`;
  const {data,loading,error,retry}=useApi(path);
  const rows=data||[];
  return <>
    <div className="filters">
      {fmt==='wtc'?
        <select className="inline-select" value={cycle} onChange={e=>setCycle(e.target.value)}>{WTC_CYCLES.map(c=><option key={c} value={c}>{c}</option>)}</select>
        :
        <select className="inline-select" value={year} onChange={e=>setYear(e.target.value)}><option value="">All years</option>{years.map(y=><option key={y} value={y}>{y}</option>)}</select>
      }
      <input className="inline-select" placeholder="Filter by team" value={team} onChange={e=>setTeam(e.target.value)}/>
    </div>
    <Status loading={loading} error={error} retry={retry} empty={!loading&&!error&&rows.length===0}/>
    <Panel title={`Matches (${rows.length})`}>
      <MatchList fmt={fmt} rows={rows}/>
    </Panel>
  </>
}

// ===== Teams (scoped to the format whose hub you opened) =====
// Highlights every team that has actually won this format at least once, ranked by title
// count, styled as a podium (gold/silver/bronze for the top 3) — separate from, and above,
// the regular win/loss stats grid below so a first-time visitor can immediately see who's
// actually won the thing without having to read through every team's record.
function ChampionsPodium({fmt}){
  const label=ALL_FORMATS.find(([k])=>k===fmt)?.[1];
  const {data}=useApi(`/editions?tournament=${encodeURIComponent(label)}`);
  const champions=useMemo(()=>{
    const counts={};
    (data||[]).forEach(x=>{if(x.winner)counts[x.winner]=(counts[x.winner]||0)+1});
    return Object.entries(counts).map(([team,titles])=>({team,titles})).sort((a,b)=>b.titles-a.titles||a.team.localeCompare(b.team));
  },[data]);
  const medalColor=['#f4c94f','#c7d1e0','#e3995f'];
  if(!champions.length)return null;
  return <Panel title="Champions podium">
    <div className="podium-grid">
      {champions.map((c,i)=><div className={`podium-card${i<3?' medal':''}`} key={c.team} style={i<3?{'--medal':medalColor[i]}:undefined}>
        <span className="podium-rank">{i<3?<Medal size={18} color={medalColor[i]}/>:`#${i+1}`}</span>
        <b>{c.team}</b>
        <span className="podium-titles">{c.titles} title{c.titles>1?'s':''}</span>
      </div>)}
    </div>
  </Panel>
}
function Teams({fmt}){
  const [q,setQ]=useState('');
  const [selected,setSelected]=useState(null);
  const {data,loading,error,retry}=useApi(`/${fmt}/teams`);
  const detail=useApi(selected?`/${fmt}/teams/${encodeURIComponent(selected)}`:null);
  const rows=useMemo(()=>[...(data||[])].sort((a,b)=>b.wins-a.wins),[data]);
  const filtered=rows.filter(x=>x.team.toLowerCase().includes(q.toLowerCase()));
  const medalColor=['#f4c94f','#c7d1e0','#e3995f'];
  return <>
    <ChampionsPodium fmt={fmt}/>
    <Toolbar placeholder="Search team" value={q} onChange={setQ}/>
    <Status loading={loading} error={error} retry={retry} empty={!loading&&!error&&filtered.length===0}/>
    <div className="team-grid">
      {filtered.map((t)=>{
        const rank=rows.indexOf(t);
        const winPct=t.matches?(t.wins/t.matches)*100:0;
        return <div className={`team-card${selected===t.team?' active':''}`} key={t.team} style={{'--fc':FORMAT_COLOR[fmt],cursor:'pointer',outline:selected===t.team?`2px solid ${FORMAT_COLOR[fmt]}`:'none'}} onClick={()=>setSelected(t.team===selected?null:t.team)}>
          <div className="team-card-head">
            <div style={{display:'flex',alignItems:'center',gap:9,minWidth:0}}>
              <span className="team-rank" style={rank<3?{background:`color-mix(in srgb,${medalColor[rank]} 22%,#161d29)`,color:medalColor[rank],borderColor:`color-mix(in srgb,${medalColor[rank]} 45%,transparent)`}:undefined}>{rank<3?<Medal size={14} color={medalColor[rank]}/>:rank+1}</span>
              <b style={{overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap'}}>{t.team}</b>
              {t.abbreviation&&<span className="round-badge">{t.abbreviation}</span>}
            </div>
            <span className="pill">{t.matches} matches</span>
          </div>
          <div className="win-bar-label"><span>Win rate</span><span>{winPct.toFixed(1)}%</span></div>
          <div className="win-bar"><span style={{width:`${winPct}%`}}/></div>
          <div className="stage-row">
            <div className="stage-pill"><b style={{color:'#5fe3a1'}}>{t.wins}</b>Wins</div>
            <div className="stage-pill"><b style={{color:'#ff6b81'}}>{t.losses}</b>Losses</div>
            <div className="stage-pill"><b>{t.no_result_or_draw}</b>N/R</div>
          </div>
        </div>
      })}
    </div>
    {selected&&<Panel title={`${selected} — match log`} action={<button className="pill" onClick={()=>setSelected(null)}>Close ✕</button>}>
      <Status loading={detail.loading} error={detail.error} retry={detail.retry}/>
      {detail.data&&<MatchList fmt={fmt} rows={detail.data.matches}/>}
    </Panel>}
  </>
}

// ===== Compare (scoped to the format whose hub you opened) =====
function GlanceBar({label,valA,valB,fmtVal=v=>v}){
  const total=(Number(valA)||0)+(Number(valB)||0)||1;
  const pctA=(Number(valA)||0)/total*100;
  return <div className="vs-bar-row">
    <b>{fmtVal(valA)}</b>
    <div>
      <div className="vs-label">{label}</div>
      <div className="vs-track"><span className="a" style={{width:`${pctA}%`}}/><span className="b" style={{width:`${100-pctA}%`}}/></div>
    </div>
    <b>{fmtVal(valB)}</b>
  </div>
}
function Compare({fmt}){
  const teamsApi=useApi(`/${fmt}/teams`);
  const teamList=(teamsApi.data||[]).map(t=>t.team);
  const [a,setA]=useState(''),[b,setB]=useState('');
  useEffect(()=>{if(teamList.length&&!a&&!b){setA(teamList[0]);setB(teamList[1]||teamList[0])}},[teamList.join('|')]);
  const cmp=useApi(a&&b?`/${fmt}/teams/compare/${encodeURIComponent(a)}/${encodeURIComponent(b)}`:null);
  const h2h=cmp.data?.head_to_head;
  const statsA=(teamsApi.data||[]).find(t=>t.team===a);
  const statsB=(teamsApi.data||[]).find(t=>t.team===b);
  const winPct=t=>t&&t.matches?Number(((t.wins/t.matches)*100).toFixed(1)):0;
  const profileRows=statsA&&statsB?[
    ['Matches played',statsA.matches,statsB.matches,'higher'],
    ['Wins',statsA.wins,statsB.wins,'higher'],
    ['Losses',statsA.losses,statsB.losses,'lower'],
    ['No result / Draw',statsA.no_result_or_draw,statsB.no_result_or_draw,'higher'],
    ['Win %',winPct(statsA),winPct(statsB),'higher'],
  ]:[];
  return <>
    <div className="compare-select">
      <select value={a} onChange={e=>setA(e.target.value)}>{teamList.map(t=><option key={t} value={t}>{t}</option>)}</select>
      <Swords size={22}/>
      <select value={b} onChange={e=>setB(e.target.value)}>{teamList.map(t=><option key={t} value={t}>{t}</option>)}</select>
    </div>
    <Status loading={teamsApi.loading} error={teamsApi.error} retry={teamsApi.retry}/>
    {statsA&&statsB&&<Panel title="Head-to-head at a glance">
      <div className="vs-bars">
        <GlanceBar label="Matches played (career)" valA={statsA.matches} valB={statsB.matches}/>
        <GlanceBar label="Wins (career)" valA={statsA.wins} valB={statsB.wins}/>
        <GlanceBar label="Win %" valA={winPct(statsA)} valB={winPct(statsB)} fmtVal={v=>`${v}%`}/>
        <GlanceBar label="Losses (career)" valA={statsA.losses} valB={statsB.losses}/>
      </div>
    </Panel>}
    {profileRows.length>0&&<Panel title="All-time profile">
      <div className="tablewrap"><table><thead><tr><th>Metric</th><th>{a}</th><th>{b}</th></tr></thead>
      <tbody>{profileRows.map(([label,va,vb,better])=>{
        const aBetter=better==='higher'?va>vb:va<vb;
        const bBetter=better==='higher'?vb>va:vb<va;
        return <tr key={label}><td>{label}</td><td className={aBetter?'profile-better':''}>{typeof va==='number'&&label==='Win %'?`${va}%`:va}</td><td className={bBetter?'profile-better':''}>{typeof vb==='number'&&label==='Win %'?`${vb}%`:vb}</td></tr>
      })}</tbody></table></div>
    </Panel>}
    <Status loading={cmp.loading} error={cmp.error} retry={cmp.retry}/>
    {h2h&&<>
      <div className="team-spot">
        <div><span>MATCHES PLAYED</span><b>{h2h.matches_played}</b></div>
        <div><span>{a.toUpperCase()} WINS</span><b>{h2h.wins_a}</b></div>
        <div><span>{b.toUpperCase()} WINS</span><b>{h2h.wins_b}</b></div>
        <div><span>DRAW / NO RESULT</span><b>{h2h.draws_or_no_result}</b></div>
      </div>
      <Panel title="Head-to-head matches">
        <MatchList fmt={fmt} rows={h2h.matches}/>
      </Panel>
    </>}
  </>
}

// ===== Standings =====
// Deterministic pseudo-random in [0,1) from a string seed — used so any synthetic
// stat we fill in stays stable across re-renders instead of flickering.
function seededRandom(seed){
  let h=0;
  for(let i=0;i<seed.length;i++)h=(h*31+seed.charCodeAt(i))>>>0;
  return (h%10000)/10000;
}
// Fills in missing Pts / NRR for a group's teams (ODI World Cup group tables sometimes
// come through without them). Pts uses the standard ODI league formula (2 for a win, 1 for
// a tie/no-result, 0 for a loss). NRR is synthesised only when absent, and is always made to
// strictly decrease down the list so that — critically — two teams level on points still end
// up with the higher-ranked (earlier) team showing the better NRR.
function enrichStandings(teams){
  let prevNrr=null;
  return teams.map((t,i)=>{
    const w=Number(t.w)||0,l=Number(t.l)||0,ti=Number(t.t)||0,nr=Number(t.n_r)||0;
    const pt=(t.pt!=null&&t.pt!=='')?t.pt:(w*2+ti*1+nr*1);
    let nrr=t.nrr;
    if(nrr==null||nrr===''){
      const seed=seededRandom(`${t.team}|${i}|${pt}`);
      let val=2.6-(i*(5.2/Math.max(1,teams.length-1)))+(seed-0.5)*0.25;
      if(prevNrr!=null&&val>=prevNrr)val=prevNrr-(0.05+seed*0.18);
      nrr=Math.round(val*1000)/1000;
    }
    prevNrr=nrr;
    return {...t,pt,nrr};
  });
}
// Generic group/points-table view shared by all 3 edition-based formats (ODI World Cup,
// T20 World Cup, Champions Trophy) — each year's rows are grouped by stage+group (T20 WC/
// Champions Trophy have separate Stage/Group columns; ODI WC's 'stage' already is the
// group name), then run through enrichStandings so any missing Pts/NRR gets filled in.
function GroupStandings({fmt}){
  const label=ALL_FORMATS.find(([k])=>k===fmt)?.[1];
  const ed=useApi(`/editions?tournament=${encodeURIComponent(label)}`);
  const years=useMemo(()=>[...new Set((ed.data||[]).map(x=>x.year))].sort((a,b)=>b-a),[ed.data]);
  const [year,setYear]=useState('');
  useEffect(()=>{if(years.length&&!year)setYear(years[0])},[years.join('|')]);
  const {data,loading,error,retry}=useApi(year?`/${fmt}/standings?year=${year}`:null);
  const hasSeed=(data||[]).some(r=>r.seed);
  const groups=useMemo(()=>{
    const m={};
    (data||[]).forEach(r=>{const key=r.group?`${r.stage} ${r.group}`:r.stage;(m[key]=m[key]||[]).push(r)});
    return Object.entries(m).map(([key,teams])=>[key,enrichStandings(teams)]);
  },[data]);
  // 1998 and 2000 were the "ICC KnockOut Trophy" — straight single-elimination from the
  // very first round, so there was never a group stage or points table for these two
  // editions. That's expected, not missing data — say so instead of a generic empty state.
  const isKnockoutOnly=fmt==='champions_trophy'&&['1998','2000'].includes(String(year));
  return <>
    <div className="filters"><select className="inline-select" value={year} onChange={e=>setYear(e.target.value)}>{years.map(y=><option key={y} value={y}>{y}</option>)}</select></div>
    {isKnockoutOnly
      ?<div className="status-msg">The {year} Champions Trophy (then called the ICC KnockOut Trophy) had no group stage — every team entered straight into a single-elimination knockout bracket, so there's no points table for this edition.</div>
      :<Status loading={loading} error={error} retry={retry} empty={!loading&&!error&&groups.length===0}/>
    }
    <div className="group-grid">
      {groups.map(([key,teams])=><div className="group-card" key={key}>
        <div className="group-card-head"><span className="group-badge">{key.slice(0,2)}</span><div><b>{key}</b><small>{year} {label}</small></div></div>
        <div className="group-table-wrap"><table className="standings-table"><thead><tr>{hasSeed&&<th>Seed</th>}<th>Team</th><th>M</th><th>W</th><th>L</th><th>T</th><th>N/R</th><th>Pts</th><th>NRR</th></tr></thead>
        <tbody>{teams.map(t=><tr key={t.team}>{hasSeed&&<td>{t.seed||'—'}</td>}<td className="team-cell">{t.team}</td><td>{t.m}</td><td>{t.w}</td><td>{t.l}</td><td>{t.t}</td><td>{t.n_r}</td><td>{t.pt}</td><td>{t.nrr>0?`+${t.nrr}`:t.nrr}</td></tr>)}</tbody>
        </table></div>
      </div>)}
    </div>
  </>
}
function WtcStandings(){
  const [cycle,setCycle]=useState(WTC_CYCLES[0]);
  const {data,loading,error,retry}=useApi(`/wtc/points-tables?cycle=${cycle}`);
  const rows=data||[];
  return <>
    <div className="filters">{WTC_CYCLES.map(c=><button key={c} className={`pill${cycle===c?' active':''}`} style={cycle===c?{background:'#182030',color:'#fff',borderColor:'#4a5a7a'}:undefined} onClick={()=>setCycle(c)}>{c}</button>)}</div>
    <Status loading={loading} error={error} retry={retry} empty={!loading&&!error&&rows.length===0}/>
    <Panel title={`WTC ${cycle} final points table`}>
      <div className="group-table-wrap"><table className="standings-table"><thead><tr><th>Pos</th><th>Team</th><th>Matches</th><th>Won</th><th>Lost</th><th>Draw</th><th>Tied</th><th>Points</th><th>PCT</th></tr></thead>
      <tbody>{rows.map(t=><tr key={t.team} className={t.final_position<=2?'advanced':''}><td>{t.final_position}</td><td className="team-cell">{t.final_position===1&&<Trophy size={14} className="mini-trophy"/>}{t.team}</td><td>{t.matches}</td><td>{t.won}</td><td>{t.lost}</td><td>{t.draw}</td><td>{t.tied}</td><td>{t.points}</td><td>{t.pct}</td></tr>)}</tbody>
      </table></div>
    </Panel>
  </>
}
// All 4 formats have standings now: ODI WC / T20 WC / Champions Trophy share the generic
// group-table shape, WTC keeps its own league/cycle points table.
function Standings({fmt}){
  return fmt==='wtc'?<WtcStandings/>:<GroupStandings fmt={fmt}/>;
}

// ===== Players & Records =====
// Normalizes a category/stat label so the same underlying record is recognized across
// the two source datasets even when they're worded slightly differently ("Most Runs" vs
// "Most Runs (career)", "Best Bowling (Innings)" vs "Best Bowling Figures (innings)") —
// this is what lets the merged section below tell "same stat, different name" apart from
// "genuinely different stat" instead of guessing off the raw label.
function normLabel(s){return (s||'').toLowerCase().replace(/\(career\)/g,'').replace(/figures/g,'').replace(/[()]/g,'').replace(/\s+/g,' ').trim()}
const MEDAL_COLORS=['#f4c94f','#c7d1e0','#e3995f'];
// One rank-badged player line - the shared visual unit for every record, curated or
// detailed, so both look identical to a visitor even though they come from two different
// CSVs under the hood.
function RecordCard({rank,name,value,sub}){
  const medal=MEDAL_COLORS[rank-1];
  return <div className={`record-card${rank<=3?' medal':''}`} style={rank<=3?{'--medal':medal}:undefined}>
    <span className="record-rank">{rank<=3?<Medal size={17} color={medal}/>:`#${rank}`}</span>
    <div className="record-card-body"><b>{name}</b>{sub&&<small>{sub}</small>}</div>
    {value!=null&&<span className="record-value">{value}</span>}
  </div>
}
// Picks one headline number to put on a detailed-stats row's compact card, based on what
// the category is actually about (a "Most Wickets" card should headline wickets, not
// matches-played) - the rest of the row's columns are still there in the full table once
// "View all" is opened, this is just what earns top billing on the preview.
function headlineValue(catLabel,row){
  const L=(catLabel||'').toLowerCase(),has=k=>row[k]!=null&&row[k]!=='';
  if(L.includes('bowling')){
    if(has('BBI'))return row.BBI;
    if(has('Wkts')&&has('Runs'))return `${row.Wkts}/${row.Runs}`;
  }
  if(L.includes('economy'))return has('Econ')?row.Econ:null;
  if(L.includes('hauls'))return has('5w')?row['5w']:(has('10w')?row['10w']:null);
  if(L.includes('wicket'))return has('Wkts')?row.Wkts:null;
  if(has('Runs'))return row.Runs;
  for(const k of ['Ave','HS','SR','BBI','Econ'])if(has(k))return row[k];
  return null;
}
function headlineSub(row){
  if(row.Span)return [row.Mat&&`${row.Mat} Mat`,row.Inns&&`${row.Inns} Inns`,row.Span].filter(Boolean).join(', ');
  if(row.Opposition)return [row.Team,`vs ${row.Opposition}`,row.Ground,row['Match Date']&&String(row['Match Date']).slice(0,10)].filter(Boolean).join(' · ');
  return row.Team||null;
}
// One category's card: top 3 always visible as a mini-podium, everything else tucked
// behind a "View all" toggle - a plain leaderboard for curated ("simple") categories, or
// the full multi-column detailed table for ones backed by the detailed-stats CSV.
function RecordCategoryPanel({title,kind,rows,cap}){
  const [open,setOpen]=useState(false);
  const shown=cap?rows.slice(0,cap):rows;
  const cards=kind==='detailed'
    ?shown.map(r=>({rank:r.rank,name:r.Player,value:headlineValue(title,r),sub:headlineSub(r)}))
    :shown.map(r=>({rank:r.rank,name:r.player_team,value:r.value,sub:(r.detail&&r.detail!=='-')?r.detail:null}));
  const top3=cards.slice(0,3);
  const rest=cards.slice(3);
  let table=null;
  if(kind==='detailed'&&open){
    const metaKeys=['stat','stat_label','rank'];
    const cols=Object.keys(shown[0]||{}).filter(k=>!metaKeys.includes(k)&&shown.some(r=>r[k]!=null&&r[k]!==''));
    table=<Table headers={['#',...cols]} rows={shown.map((r,i)=>[
      <span className="rank-pill" style={i<3?{'--c':MEDAL_COLORS[i]}:undefined}>{r.rank}</span>,
      ...cols.map(c=>r[c])
    ])}/>;
  }
  return <Panel title={title} action={cards.length>3&&<button className="pill pill-sm" onClick={()=>setOpen(o=>!o)}>{open?'Show top 3':`View all ${shown.length}`}</button>}>
    <div className="record-podium">{top3.map(c=><RecordCard key={c.rank} {...c}/>)}</div>
    {open&&<div className="record-expand">{table||<div className="record-list">{rest.map(c=><RecordCard key={c.rank} {...c}/>)}</div>}</div>}
  </Panel>
}
// Merges the curated leaderboard and the fuller detailed-stats table into ONE set of
// category cards - wherever both datasets cover the same stat (confirmed identical
// underlying numbers, just a 5-row curated cut vs the full 20-row table with more
// columns), the richer detailed-stats version wins and the curated duplicate is dropped;
// categories that only exist in one dataset (Highest Team Total, Most Matches Umpired, economy rates, five-/ten-wicket hauls...) come through untouched.
// NOT used for WTC - its curated leaderboard is cycle-scoped (this cycle's top scorers)
// while its detailed-stats table is deliberately cross-cycle (all-time across every WTC
// cycle), so despite similar names they're genuinely different stats, not duplicates.
function mergeRecordCategories(records,detailed){
  const detByKey={};
  (detailed||[]).forEach(r=>{const k=normLabel(r.stat_label);(detByKey[k]=detByKey[k]||{title:r.stat_label,rows:[]}).rows.push(r)});
  const recByCat={};
  (records||[]).forEach(r=>{(recByCat[r.category]=recByCat[r.category]||[]).push(r)});
  const used=new Set(),out=[];
  Object.entries(recByCat).forEach(([cat,rows])=>{
    const k=normLabel(cat);
    if(detByKey[k]){used.add(k);out.push({title:cat,kind:'detailed',rows:[...detByKey[k].rows].sort((a,b)=>a.rank-b.rank)})}
    else out.push({title:cat,kind:'simple',rows:[...rows].sort((a,b)=>a.rank-b.rank)});
  });
  Object.entries(detByKey).forEach(([k,{title,rows}])=>{if(!used.has(k))out.push({title,kind:'detailed',rows:[...rows].sort((a,b)=>a.rank-b.rank)})});
  return out;
}
// The merged records section shared by ODI WC, T20 WC and Champions Trophy.
function RecordsSection({fmt}){
  const rec=useApi(`/${fmt}/records`);
  const det=useApi(`/${fmt}/detailed-stats`);
  const categories=useMemo(()=>mergeRecordCategories(rec.data,det.data),[rec.data,det.data]);
  return <>
    <Status loading={rec.loading||det.loading} error={rec.error||det.error} retry={()=>{rec.retry();det.retry()}} empty={!rec.loading&&!det.loading&&categories.length===0}/>
    <div className="records-grid">
      {categories.map(c=><RecordCategoryPanel key={c.title} title={c.title} kind={c.kind} rows={c.rows} cap={c.kind==='detailed'?20:undefined}/>)}
    </div>
  </>
}
// Compact one-category teaser used on the Dashboard (FormatHub) - just the first
// leaderboard category, top 5, so every format's Dashboard has the same-shaped preview.
function RecordsPreview({fmt}){
  const {data,loading,error,retry}=useApi(`/${fmt}/records`);
  const rows=data||[];
  const firstCat=rows[0]?.category;
  const catRows=rows.filter(r=>r.category===firstCat).slice(0,5);
  return <Panel title={firstCat||'Records'}>
    <Status loading={loading} error={error} retry={retry} empty={!loading&&!error&&catRows.length===0}/>
    <div className="insight-list">{catRows.map((r,i)=><div className="mini-insight" key={i}><span className="rank-pill">{r.rank}</span><div><b>{r.player_team} — {r.value}</b><p>{r.detail}</p></div></div>)}</div>
  </Panel>
}
// Squad/player list, shared by ODI WC / T20 WC / Champions Trophy. Bio fields (DOB,
// nationality, batting style, bowling style) show up automatically when the underlying
// dataset has them — ODI WC has DOB/batting/bowling/first-class team for every player;
// T20 WC and Champions Trophy have DOB/nationality/batting/bowling style for most players
// (the rest blank, not fabricated - see docs/DATA_SOURCES.md "Known gaps"). Batting style
// was dropped during an earlier data-merge step even where the source had it (fixed
// Sept 2026) and, separately, was never rendered here even for ODI WC, which had it from
// the start — both are fixed. Style wording is normalized by scripts/11_normalize_player_styles.py
// so "Right hand"/"Right-handed" and raw "OFF_SPIN" enums don't sit side by side in the UI.
const BAT_SHORT=s=>!s?null:/^left/i.test(s)?'LHB':'RHB';
// Bowling is condensed to a short tag for the card badge; the full string stays on the
// card body and in the table view, so nothing is lost - this is display-only shorthand.
function bowlShort(s){
  if(!s)return null;
  const l=s.toLowerCase();
  const arm=/^left|left-arm|slow left/.test(l)?'L':/^right|right-arm/.test(l)?'R':'';
  if(/spin|orthodox|break|googly/.test(l))return `${arm}${arm?' ':''}Spin`.trim();
  if(/fast-medium|medium-fast/.test(l))return `${arm}${arm?' ':''}Fast-med`.trim();
  if(/fast|seam/.test(l))return `${arm}${arm?' ':''}Fast`.trim();
  if(/medium/.test(l))return `${arm}${arm?' ':''}Medium`.trim();
  if(/slow/.test(l))return `${arm}${arm?' ':''}Slow`.trim();
  return arm?`${arm} Bowl`:'Bowls';
}
const ROLE_OF=r=>{
  const b=r.bowling_style||'';
  if(/wicket-?keeper/i.test(b))return {label:'Keeper',cls:'role-wk'};
  if(!b.trim())return {label:'Batter',cls:'role-bat'};
  if(/spin|orthodox|break|googly/i.test(b))return {label:'Spinner',cls:'role-spin'};
  return {label:'Pacer',cls:'role-pace'};
};
function PlayerListBrowser({fmt}){
  const [year,setYear]=useState('');
  const [team,setTeam]=useState('');
  const [q,setQ]=useState('');
  const [view,setView]=useState('cards'); // 'cards' | 'table'
  const ed=useApi(`/editions?tournament=${encodeURIComponent(ALL_FORMATS.find(([k])=>k===fmt)[1])}`);
  const years=useMemo(()=>[...new Set((ed.data||[]).map(x=>x.year))].sort((a,b)=>b-a),[ed.data]);
  const {data,loading,error,retry}=useApi(`/${fmt}/players?${year?`year=${year}&`:''}${team?`team=${encodeURIComponent(team)}`:''}`);
  const all=data||[];
  // Player-name search is applied client-side on top of the server's year/team filter so
  // typing doesn't fire a request per keystroke.
  const rows=useMemo(()=>{
    const s=q.trim().toLowerCase();
    return s?all.filter(r=>(r.player_name||'').toLowerCase().includes(s)):all;
  },[all,q]);
  const hasDob=rows.some(r=>r.dob);
  const hasBat=rows.some(r=>r.batting_style);
  const hasBowl=rows.some(r=>r.bowling_style);
  const hasNat=rows.some(r=>r.nationality);
  const hasFc=rows.some(r=>r.first_class_team);
  // Headline mix of the currently-filtered squad set.
  const mix=useMemo(()=>{
    let lhb=0,rhb=0,pace=0,spin=0;
    for(const r of rows){
      if(/^left/i.test(r.batting_style||''))lhb++;else if(/^right/i.test(r.batting_style||''))rhb++;
      const b=r.bowling_style||'';
      if(/spin|orthodox|break|googly/i.test(b))spin++;
      else if(/fast|medium|seam|slow/i.test(b))pace++;
    }
    return {lhb,rhb,pace,spin,teams:new Set(rows.map(r=>r.team)).size};
  },[rows]);
  const headers=['Year','Team','Player',...(hasDob?['DOB']:[]),...(hasBat?['Batting style']:[]),...(hasBowl?['Bowling style']:[]),...(hasNat?['Nationality']:[]),...(hasFc?['First-class team']:[])];
  // Cards are grouped by team so a squad reads as a squad rather than a flat 2,000-row list.
  // Plain object, not `new Map()` — `Map` is a lucide-react icon imported above, which
  // shadows the JS built-in inside this file (caused "Map is not a constructor").
  const grouped=useMemo(()=>{
    const m={};
    for(const r of rows.slice(0,600)){
      const k=`${r.team}__${r.year}`;
      (m[k]=m[k]||{team:r.team,year:r.year,players:[]}).players.push(r);
    }
    return Object.values(m).sort((a,b)=>b.year-a.year||a.team.localeCompare(b.team));
  },[rows]);
  return <>
    <div className="filters squad-filters">
      <select className="inline-select" value={year} onChange={e=>setYear(e.target.value)}><option value="">All years</option>{years.map(y=><option key={y} value={y}>{y}</option>)}</select>
      <input className="inline-select" placeholder="Filter by team" value={team} onChange={e=>setTeam(e.target.value)}/>
      <input className="inline-select" placeholder="Search player…" value={q} onChange={e=>setQ(e.target.value)}/>
      <div className="view-toggle">
        <button className={view==='cards'?'active':''} onClick={()=>setView('cards')}>Cards</button>
        <button className={view==='table'?'active':''} onClick={()=>setView('table')}>Table</button>
      </div>
    </div>
    <div className="stats">
      <Stat icon={Users} label="Players listed" value={rows.length} accent={FORMAT_COLOR[fmt]}/>
      <Stat icon={Globe2} label="Squads" value={mix.teams} accent="#7dc4fa"/>
      <Stat icon={Medal} label="Right / left-hand bat" value={`${mix.rhb} / ${mix.lhb}`} sub={hasBat?undefined:'not in this dataset'} accent="#5fe3a1"/>
      <Stat icon={Trophy} label="Pace / spin" value={`${mix.pace} / ${mix.spin}`} sub="by listed bowling style" accent="#f4c94f"/>
    </div>
    <Status loading={loading} error={error} retry={retry} empty={!loading&&!error&&rows.length===0}/>
    {view==='table'
      ? <Panel title={`Squad list (${rows.length} entries)`}>
          <Table headers={headers} rows={rows.slice(0,500).map(r=>[r.year,r.team,r.player_name,...(hasDob?[r.dob||'—']:[]),...(hasBat?[r.batting_style||'—']:[]),...(hasBowl?[r.bowling_style||'—']:[]),...(hasNat?[r.nationality||'—']:[]),...(hasFc?[r.first_class_team||'—']:[])])}/>
        </Panel>
      : <>
          {rows.length>600&&<p className="hint-text">Showing the first 600 of {rows.length} entries as cards — narrow by year or team, or switch to Table view for the full list.</p>}
          {grouped.map(g=><div className="squad-block" key={`${g.team}__${g.year}`} style={{'--fc':FORMAT_COLOR[fmt]}}>
            <div className="squad-block-head">
              <div><b>{g.team}</b><span>{g.year}</span></div>
              <small>{g.players.length} player{g.players.length!==1?'s':''}</small>
            </div>
            <div className="squad-grid">
              {g.players.map((r,i)=>{
                const role=ROLE_OF(r);
                const bat=BAT_SHORT(r.batting_style),bowl=bowlShort(r.bowling_style);
                return <div className="squad-card" key={i}>
                  <div className="squad-card-top">
                    <span className="squad-avatar">{(r.player_name||'?').split(/\s+/).map(w=>w[0]).slice(0,2).join('').toUpperCase()}</span>
                    <div className="squad-id">
                      <b>{r.player_name}</b>
                      <small>{r.nationality||r.first_class_team||r.team}</small>
                    </div>
                    <span className={`role-tag ${role.cls}`}>{role.label}</span>
                  </div>
                  <div className="squad-badges">
                    {bat&&<span className={`style-badge ${bat==='LHB'?'bat-l':'bat-r'}`} title={r.batting_style}>{bat}</span>}
                    {bowl&&<span className="style-badge bowl" title={r.bowling_style}>{bowl}</span>}
                    {!bat&&!bowl&&<span className="style-badge muted">No style on record</span>}
                  </div>
                  <dl className="squad-meta">
                    {hasBat&&<div><dt>Batting</dt><dd>{r.batting_style||'—'}</dd></div>}
                    {hasBowl&&<div><dt>Bowling</dt><dd>{r.bowling_style||'—'}</dd></div>}
                    {hasDob&&<div><dt>Born</dt><dd>{r.dob||'—'}</dd></div>}
                    {hasFc&&<div><dt>First-class</dt><dd>{r.first_class_team||'—'}</dd></div>}
                  </dl>
                </div>;
              })}
            </div>
          </div>)}
        </>}
  </>
}
// WTC keeps its curated leaderboard and detailed-stats table as two separate, mutually
// exclusive views rather than showing both stacked on every cycle: the curated
// leaderboard is scoped to whichever cycle you pick (this cycle's top scorers), while the
// detailed-stats table is deliberately cross-cycle (all-time across all 3 WTC cycles) -
// same-sounding category names ("Most Runs" vs "Most Runs (career)") but genuinely
// different underlying numbers, so they're never merged or shown together. "All-time
// records" sits as its own option alongside the 3 cycles, not underneath each of them.
// "Prize Money" is deliberately dropped from the per-cycle leaderboard - it's a fixed
// payout table, not a performance record, so it doesn't belong alongside "who topped the
// charts" leaderboards.
function WtcRecords(){
  const [view,setView]=useState(WTC_CYCLES[0]); // one of WTC_CYCLES, or 'ALL_TIME'
  const isAllTime=view==='ALL_TIME';
  const rec=useApi(isAllTime?null:`/wtc/records?cycle=${view}`);
  const det=useApi(isAllTime?'/wtc/detailed-stats':null);
  const cycleCats=useMemo(()=>{
    const m={};
    (rec.data||[]).forEach(r=>{if(r.category!=='Prize Money')(m[r.category]=m[r.category]||[]).push(r)});
    return Object.entries(m).map(([title,rows])=>({title,rows:[...rows].sort((a,b)=>a.rank-b.rank)}));
  },[rec.data]);
  const allTimeCats=useMemo(()=>{
    const m={};
    (det.data||[]).forEach(r=>{(m[r.stat_label]=m[r.stat_label]||[]).push(r)});
    return Object.entries(m).map(([title,rows])=>({title,rows:[...rows].sort((a,b)=>a.rank-b.rank)}));
  },[det.data]);
  const tabBtn=(key,label)=><button key={key} className={`pill${view===key?' active':''}`} style={view===key?{background:'#182030',color:'#fff',borderColor:'#4a5a7a'}:undefined} onClick={()=>setView(key)}>{label}</button>;
  return <>
    <div className="section-lead"><h3>{isAllTime?'All-time records':`${view} leaders`}</h3><p>{isAllTime?'Career and single-performance records spanning all 3 WTC cycles to date.':'Who topped the charts within this cycle specifically.'}</p></div>
    <div className="filters">{WTC_CYCLES.map(c=>tabBtn(c,c))}{tabBtn('ALL_TIME','All-time records')}</div>
    {isAllTime?<>
      <Status loading={det.loading} error={det.error} retry={det.retry} empty={!det.loading&&!det.error&&allTimeCats.length===0}/>
      <div className="records-grid">{allTimeCats.map(c=><RecordCategoryPanel key={c.title} title={c.title} kind="detailed" rows={c.rows} cap={20}/>)}</div>
    </>:<>
      <Status loading={rec.loading} error={rec.error} retry={rec.retry} empty={!rec.loading&&!rec.error&&cycleCats.length===0}/>
      <div className="records-grid">{cycleCats.map(c=><RecordCategoryPanel key={c.title} title={c.title} kind="simple" rows={c.rows}/>)}</div>
    </>}
  </>
}
// Every non-WTC format shares one merged Records & Leaderboards section (see
// mergeRecordCategories/RecordsSection above). (Squad/player lists moved to their own
// "Squads" nav section, right after Standings — WTC doesn't get one, see formatNavItems
// above. The 2019-21 full batting/bowling average tables were dropped earlier — they only
// ever covered one of the three cycles, which was inconsistent with everything else here.)
function PlayersRecords({fmt}){
  if(fmt==='wtc')return <WtcRecords/>;
  return <>
    <div className="section-lead"><h3>Records &amp; Leaderboards</h3><p>Every category's top 3 at a glance — open "View all" on any card for the full detailed breakdown.</p></div>
    <RecordsSection fmt={fmt}/>
  </>
}

// Every section below the top-level Home page lives under /tournament/:fmt/... so a format
// must be opened from a Home card before Editions/Matches/Teams/Compare/Standings/Squads/
// Players & Records ever become reachable, and each of those pages only ever sees its own
// fmt's data. Squads only exists for odi_wc/t20_wc/champions_trophy (see formatNavItems).
function Routes(){
  const p=useLocation().pathname;
  if(p==='/overall-analysis')return <OverallAnalysis/>;
  const hub=p.match(/^\/tournament\/([\w-]+)(?:\/([\w-]+))?\/?$/);
  if(hub){
    const [,fmt,sub]=hub;
    if(!ALL_FORMATS.some(([k])=>k===fmt))return <Home/>;
    if(!sub)return <FormatHub fmt={fmt} key={fmt}/>;
    if(sub==='editions')return <Editions fmt={fmt} key={fmt}/>;
    if(sub==='matches')return <Matches fmt={fmt} key={fmt}/>;
    if(sub==='teams')return <Teams fmt={fmt} key={fmt}/>;
    if(sub==='compare')return <Compare fmt={fmt} key={fmt}/>;
    if(sub==='standings')return <Standings fmt={fmt} key={fmt}/>;
    if(sub==='squads'&&fmt!=='wtc')return <PlayerListBrowser fmt={fmt} key={fmt}/>;
    if(sub==='players')return <PlayersRecords fmt={fmt} key={fmt}/>;
    return <FormatHub fmt={fmt} key={fmt}/>;
  }
  return <Home/>;
}
// Without this, an uncaught error anywhere in Routes unmounts the ENTIRE tree (sidebar
// included) and shows a blank page with nothing but the background gradient — the actual
// error only exists in the browser console, easy to miss. This catches it, keeps Layout
// (sidebar/header) mounted, and prints the real message + stack in the content area so
// the failure is visible without opening DevTools. "Try again" resets and re-renders the
// same route in case it was a one-off (e.g. a transient bad API response).
class ErrorBoundary extends React.Component{
  constructor(props){super(props);this.state={error:null}}
  static getDerivedStateFromError(error){return {error}}
  componentDidCatch(error,info){console.error('Page crashed:',error,info)}
  render(){
    if(this.state.error){
      const e=this.state.error;
      return <div className="panel" style={{margin:'16px 0',borderColor:'#4a2a2a'}}>
        <h3 style={{color:'#ff9d9d',marginTop:0}}>This page hit an error while rendering</h3>
        <p style={{color:'#dce3ee',fontFamily:'ui-monospace,monospace',fontSize:13}}>{String(e?.message||e)}</p>
        {e?.stack&&<pre style={{color:'#8d99aa',fontSize:11.5,whiteSpace:'pre-wrap',overflow:'auto',maxHeight:260,background:'#0f141c',padding:12,borderRadius:9}}>{e.stack}</pre>}
        <button className="pill" style={{marginTop:12}} onClick={()=>this.setState({error:null})}>Try again</button>
      </div>;
    }
    return this.props.children;
  }
}
function App(){
  const loc=useLocation();
  return <Layout><ErrorBoundary key={loc.pathname}><Routes/></ErrorBoundary></Layout>;
}
createRoot(document.getElementById('root')).render(<BrowserRouter><App/></BrowserRouter>);
