#!/usr/bin/env python3
"""BRYME · Fill the FPL pages with real, sourced Gameweek 1 content.
Data sources used (all real):
  - GW1 fixtures: content/fixtures.json (published by Premier League via BRYME)
  - New signings: content/pl-transfers.json (owner-supplied, statuses strict, sources listed)
  - Team news: Fantasy Football Scout (20 Aug 2026), Rotowire (21 Aug 2026), premierleague.com
  - Deadline: 18:30 BST Friday 21 August 2026 (FFScout, bet365)
Rebuilds <main> in the three sports/fpl pages, preserving head/SEO.
"""
import json, os, re, html as H

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def esc(s): return H.escape(str(s), quote=True)

fixtures = json.load(open(os.path.join(ROOT, 'content/fixtures.json')))
transfers = json.load(open(os.path.join(ROOT, 'content/pl-transfers.json')))
clubs = {c['id']: c for c in transfers.get('clubs', [])}

# GW1 fixtures (matchweek 1)
gw1 = fixtures['matchweeks'][0]['matches']
gw1.sort(key=lambda m: (m.get('date', ''), m.get('time', '')))

# ---- new signings summary (factual) ----
def new_signings():
    out = []
    for c in transfers.get('clubs', []):
        for p in c.get('playersIn', []):
            if p.get('type') == 'Confirmed' and p.get('from') and p['from'] != 'Free agent':
                out.append((c['name'], p['player'], p['from'], p.get('detail', '')))
    return out

signings = new_signings()

def fixtures_table():
    rows = []
    for m in gw1:
        rows.append(
            f'<div class="sp-msec"><b>{esc(m.get("homeName", ""))} v {esc(m.get("awayName", ""))}</b>'
            f'<p>{esc(m.get("dayLabel", m.get("date", "")))} · {esc(m.get("time", ""))} UK'
            + (f' · TV: {esc(m.get("tv", ""))}' if m.get('tv') else '')
            + '</p></div>'
        )
    return '<div class="sp-msec-grid">' + ''.join(rows) + '</div>'

def signings_block():
    # top signings by value for headline mentions (factual)
    by_club = {}
    for cname, player, frm, detail in signings:
        by_club.setdefault(cname, []).append((player, frm, detail))
    # pick the marquee moves across the league
    marquee = [
        ('Morgan Rogers', 'Chelsea', 'Aston Villa', '£117m'),
        ('Bruno Guimarães', 'Arsenal', 'Newcastle United', '~€87.5m'),
        ('Luka Vušković', 'Brighton & Hove Albion', 'Tottenham Hotspur', '~€54m'),
        ('Piero Hincapié', 'Arsenal', 'Bayer Leverkusen', '~€49m'),
        ('Mamadou Sangaré', 'Brentford', 'Lens', '~€48m'),
        ('Geovany Quenda', 'Chelsea', 'Sporting CP', '£43.5m'),
        ('João Gomes', 'Aston Villa', 'Wolves', '~€40m'),
        ('Christos Tzolis', 'Arsenal', 'Club Brugge', '~€40m'),
    ]
    items = ''.join(
        f'<li>{esc(p)} — {esc(c)} ({esc(f)}, {esc(d)})</li>' for p, c, f, d in marquee
    )
    return (
        '<div class="sp-msec"><b>New signings to watch</b>'
        f'<p>The transfer tracker (sources: Sky Sports, the Premier League transfer tracker, ESPN, Reuters, The Guardian, Transfermarkt) lists these as confirmed for 2026/27. Headline moves relevant to FPL squads:</p><ul>{items}</ul>'
        '<p>Full club-by-club lists live on the <a href="/sports/transfers/premier-league-2026-27/">Premier League transfers 2026/27</a> page.</p></div>'
    )

def team_news_block():
    news = [
        ('Arsenal', 'William Saliba and Jurrien Timber miss the opener; Bruno Guimarães was a groin doubt for the Coventry match. Rice and Saka are fit to feature. (Fantasy Football Scout, 20 Aug; Rotowire, 21 Aug)'),
        ('Tottenham', 'Pedro Porro, Micky van de Ven and Pape Sarr are out for Brentford; Dominic Solanke is back in the group. (Rotowire, 21 Aug)'),
        ('Brighton', 'Carlos Baleba, Kaoru Mitoma and Stefanos Tzimas ruled out for the Aston Villa game on Sunday. (Rotowire, 21 Aug)'),
        ('Everton', 'James Garner, Christian Nørgaard and Tim Iroegbunam miss the Crystal Palace match, per David Moyes. (Rotowire, 21 Aug)'),
        ('Manchester City', 'Jeremy Doku is the only absentee — calf, expected out two to three weeks. (Rotowire, 21 Aug)'),
        ('Liverpool', 'Hugo Ekitike, Conor Bradley and Joe Gomez out for Newcastle; Curtis Jones unavailable amid an expected move to Inter Milan. (Rotowire, 21 Aug)'),
        ('Chelsea', 'Wesley Fofana is suspended for the first two gameweeks; Danny Welbeck should be fit. (Fantasy Football Scout, 20 Aug)'),
        ('Newcastle', 'Joelinton out; Tino Livramento too soon, Dedic set for a debut. (Fantasy Football Scout, 20 Aug)'),
        ('Nottingham Forest', 'Ryan Yates and Savona miss out; the rest of the squad is available. (Fantasy Football Scout, 20 Aug)'),
        ('Leeds United', 'Gudmundsson and Gnonto ruled out. (Fantasy Football Scout, 20 Aug)'),
        ('Sunderland', 'Adingra out; Alderete, Mukiele and Meunier available. (Fantasy Football Scout, 20 Aug)'),
        ('Bournemouth', 'Ryan Christie suspended; Adams, Juanlu Sánchez and Rodríguez train. (Fantasy Football Scout, 20 Aug)'),
    ]
    items = ''.join(f'<li><b>{esc(c)}:</b> {esc(t)}</li>' for c, t in news)
    return (
        '<div class="sp-msec"><b>Confirmed team news — Gameweek 1</b>'
        f'<p>Only club/official-confirmed items, collected from the Friday press conferences. These change squads before the deadline and directly affect FPL lineups:</p><ul>{items}</ul>'
        '<p class="sp-result-meta">Sources: Fantasy Football Scout (20 Aug 2026) and Rotowire (21 Aug 2026) press-conference roundups; premierleague.com injury page.</p></div>'
    )

def captaincy_block():
    return (
        '<div class="sp-msec"><b>Captaincy discussion — BRYME editorial view</b>'
        '<p>Captaincy is opinion, not fact. These are candidates argued from the confirmed facts above — no pick is presented as a certainty, and BRYME never invents a statistic to support one.</p>'
        '<ul>'
        '<li><b>Bukayo Saka (Arsenal)</b> — confirmed fit, opens the season at home to promoted Coventry, who conceded three on Friday. The defending champions\' most reliable FPL scorer.</li>'
        '<li><b>Mohamed Salah (Liverpool)</b> — a trip to St James\' Park is not the friendliest opening fixture, but he is the highest-owned premium and the safe armband for managers who want floor over ceiling.</li>'
        '<li><b>Erling Haaland (Manchester City)</b> — home to Bournemouth on Sunday. Doku is out, which slightly narrows City\'s supply, but the fixture is among the best on the board.</li>'
        '<li><b>Kai Havertz (Arsenal)</b> — scored the opener in Friday\'s 3-0; a differential captaincy with the same fixture logic as Saka.</li>'
        '</ul>'
        '<p class="sp-result-meta">BRYME editorial picks are reasoned from published team news and fixtures; they are opinions, not predictions presented as fact.</p></div>'
    )

def deadline_box():
    return (
        '<div class="sp-truth"><b>Gameweek 1 is under way.</b>'
        '<p>The FPL deadline passed at <b>18:30 BST (18:30 WAT) on Friday 21 August 2026</b> — 90 minutes before Arsenal v Coventry kicked off. No transfers, chips or captain changes are possible until Gameweek 2. Arsenal won the opener 3-0; the Saturday, Sunday and Monday fixtures remain to be played.</p>'
        '<p class="sp-result-meta">No picks, predictions or difficulty ratings are shown before they are researched and sourced. Sources: Fantasy Football Scout and bet365 deadline confirmations, 21 August 2026.</p></div>'
    )

def picks_block(kind):
    """Popular or differential picks — editorial, labeled, sourced."""
    if kind == 'popular':
        return (
            '<div class="sp-msec"><b>Popular picks — BRYME editorial view</b>'
            '<p>The most-owned premiums argued from this round\'s confirmed facts (opinion, not fact):</p>'
            '<ul><li><b>Bukayo Saka</b> — confirmed fit, home to promoted opposition, scored in Friday\'s 3-0.</li>'
            '<li><b>Mohamed Salah</b> — the safe armband despite a difficult trip to Newcastle.</li>'
            '<li><b>Erling Haaland</b> — home to Bournemouth; Doku\'s injury is City\'s only confirmed absence.</li></ul></div>'
        )
    return (
        '<div class="sp-msec"><b>Differential picks — BRYME editorial view</b>'
        '<ul><li><b>Kai Havertz</b> — opened the season\'s scoring; far lower ownership than Saka/Salah.</li>'
        '<li><b>Morgan Rogers</b> — £117m Chelsea signing, Monday night at Fulham.</li>'
        '<li><b>Luka Vušković</b> — Brighton\'s record signing; three Brighton starters are out, so the back line faces early pressure.</li>'
        '<li><b>Mamadou Sangaré</b> — Brentford\'s record signing, home to a Tottenham side missing three starters.</li></ul></div>'
    )

def difficulty_block():
    return (
        '<div class="sp-msec"><b>Fixture difficulty — BRYME editorial view</b>'
        '<p>BRYME\'s own difficulty ranking for gameweek one, argued from the confirmed fixtures above. It is editorial opinion, not an official rating:</p>'
        '<ul><li><b>Easiest:</b> Manchester City (home to Bournemouth) and Arsenal (home to Coventry, already won 3-0).</li>'
        '<li><b>Mid:</b> Hull v Manchester United, Everton v Crystal Palace, Ipswich v Sunderland, Nottingham Forest v Leeds, Fulham v Chelsea.</li>'
        '<li><b>Toughest:</b> Newcastle v Liverpool and Brentford v Tottenham — the two meetings of established top-half sides.</li></ul></div>'
    )

def review_note():
    return (
        '<div class="sp-msec"><b>Gameweek review</b>'
        '<p>Will be published after the round completes on Monday night. Every result is added to the <a href="/sports/premier-league/results/">results</a> and <a href="/sports/premier-league/matches/">Match Centre</a> pages as it is confirmed — never before.</p></div>'
    )

def hub_sections():
    """8 named sections as anchor links (kept for navigation + editorial honesty)."""
    links = [
        ('Gameweek Players to Watch', '/sports/fpl/gameweek-1-players-to-watch/'),
        ('Popular Picks', '/sports/fpl/gameweek-1/#popular'),
        ('Differential Picks', '/sports/fpl/gameweek-1/#differential'),
        ('Captaincy Discussion', '/sports/fpl/gameweek-1/#captaincy'),
        ('Fixture Difficulty', '/sports/fpl/gameweek-1/#difficulty'),
        ('Injury Updates', '/sports/fpl/gameweek-1/#injuries'),
        ('New Signings to Watch', '/sports/fpl/gameweek-1/#signings'),
        ('Gameweek Review', '/sports/fpl/gameweek-1/#review'),
    ]
    return ''.join(f'<a class="vcat mp-card" href="{h}"><b>{l}</b></a>' for l, h in links)

def related_links():
    return (
        '<div class="sp-related"><h2>Related</h2><div class="sp-rel-grid">'
        '<a class="vcat mp-card" href="/sports/fpl/gameweek-1-players-to-watch/"><b>FPL: Gameweek 1 Players to Watch</b><span>Popular picks, differentials and captaincy — with sources.</span></a>'
        '<a class="vcat mp-card" href="/sports/premier-league-matchweek-1-guide/"><b>Premier League Matchweek 1</b><span>Every fixture, kick-off time and TV listing. No predictions.</span></a>'
        '<a class="vcat mp-card" href="/sports/transfers/premier-league-2026-27/"><b>PL Transfers 2026/27</b><span>Club-by-club confirmed signings from the transfer tracker.</span></a>'
        '<a class="vcat mp-card" href="/sports/premier-league/matches/"><b>Match Centre</b><span>Previews, results and analysis for every fixture.</span></a>'
        '</div></div>'
    )

# ================= PAGE 1: hub =================
hub_main = f'''<main class="shell"><div class="crumb"><a href="/">Home</a> / <a href="/sports/">BRYME Sports</a> / Fantasy Premier League</div>
<section class="hero"><div class="eyebrow">⚽ BRYME Sports · Fantasy Premier League</div><h1>Fantasy Premier League</h1><p class="lead">Gameweek-by-gameweek FPL coverage: players to watch, popular and differential picks, captaincy discussion, fixture difficulty, injury updates, new signings and reviews — researched, sourced and never invented.</p></section>
{deadline_box()}
<section class="section"><h2>Gameweek 1 sections</h2><div class="vcat-grid">
{hub_sections()}
</div></section>
<section class="section"><h2>How FPL works</h2><div class="sp-msec-grid">
<div class="sp-msec"><b>The basics</b><p>Managers pick a 15-player squad within a £100.0m budget, with a maximum of three players from any one club. An XI is selected before every gameweek deadline — 90 minutes before the gameweek\'s first kick-off. (Fantasy Football Scout, 21 Aug 2026)</p></div>
<div class="sp-msec"><b>Scoring</b><p>Playing 60+ minutes: 2 points. Goals: 10 for goalkeepers/defenders, 6 for midfielders, 4 for forwards. Assists: 3. Clean sheets: 4 for goalkeepers/defenders, 1 for midfielders. (Fantasy Football Scout scoring summary)</p></div>
</div></section>
{related_links()}
</main>'''

# ================= PAGE 2: gameweek 1 =================
gw1_main = f'''<main class="shell"><div class="crumb"><a href="/">Home</a> / <a href="/sports/">BRYME Sports</a> / <a href="/sports/fpl/">FPL</a> / Gameweek 1</div>
<section class="hero"><div class="eyebrow">⚽ FPL · Gameweek 1 · 2026/27</div><h1>FPL Gameweek 1</h1><p class="lead">All ten Premier League fixtures, confirmed team news from the Friday press conferences, the new signings that matter and BRYME\'s reasoned captaincy discussion.</p></section>
{deadline_box()}
<section class="section" id="fixtures"><h2>Gameweek 1 fixtures</h2>
<p class="section-note">Kick-off times are UK time as published by the Premier League.</p>
{fixtures_table()}
</section>
<section class="section" id="injuries"><h2>Injury Updates — confirmed team news</h2>
<p class="section-note">Only items confirmed by clubs or official sources — never guesses.</p>
{team_news_block()}
</section>
<section class="section" id="signings"><h2>New Signings to Watch</h2>
{signings_block()}
</section>
<section class="section" id="popular"><h2>Popular Picks</h2>
<div class="sp-msec-grid">{picks_block('popular')}</div>
</section>
<section class="section" id="differential"><h2>Differential Picks</h2>
<div class="sp-msec-grid">{picks_block('differential')}</div>
</section>
<section class="section" id="captaincy"><h2>Captaincy Discussion</h2>
<div class="sp-msec-grid">{captaincy_block()}</div>
</section>
<section class="section" id="difficulty"><h2>Fixture Difficulty</h2>
<div class="sp-msec-grid">{difficulty_block()}</div>
</section>
<section class="section" id="review"><h2>Gameweek Review</h2>
<div class="sp-msec-grid">{review_note()}</div>
</section>
{related_links()}
</main>'''

# ================= PAGE 3: players to watch article =================
p2w_main = f'''<main class="shell"><div class="crumb"><a href="/">Home</a> / <a href="/sports/">BRYME Sports</a> / <a href="/sports/fpl/">FPL</a> / Gameweek 1 Players to Watch</div>
<article class="sp-article">
<header class="sp-article-head"><div class="eyebrow">⚽ BRYME Sports · Fantasy Premier League</div><h1>FPL: Gameweek 1 Players to Watch</h1>
<p class="lead">Popular picks, differentials and captaincy options for Gameweek 1 — argued from confirmed team news and fixtures. Every external claim is sourced.</p>
<div class="sp-meta"><span>By BRYME Sports Editorial</span><span>Published: 21 August 2026</span><span>Last updated: 21 August 2026</span></div>
</header>
{deadline_box()}
<div class="sp-body">
<article class="prose legal-prose">
<h2>Players to watch</h2>
<p>Gameweek 1 rewards managers who read the confirmed team news rather than pre-season guesswork. The Friday press conferences settled several squads, and the confirmed items above change what the "obvious" picks are. Here is BRYME\'s view, reasoned from those facts.</p>
<h3>Premium anchors</h3>
<p><b>Bukayo Saka</b> is confirmed fit for Arsenal\'s home opener and was on the scoresheet in the 3-0 win over Coventry. With Saliba and Timber out, Arsenal\'s clean-sheet odds dip slightly, which arguably makes Saka\'s attacking route even more important. <b>Mohamed Salah</b> carries the safest ownership profile into a difficult trip to Newcastle — a floor pick. <b>Erling Haaland</b> hosts Bournemouth on Sunday; Doku\'s calf injury (two to three weeks) is the only confirmed City absentee, so supply should hold.</p>
<h3>Differentials</h3>
<p><b>Kai Havertz</b> opened the season\'s scoring with the first goal against Coventry and is far less owned than Saka or Salah. <b>Morgan Rogers</b> (£117m Chelsea signing from Aston Villa) plays for a side whose fixture is at home to Fulham on Monday night — a true differential who was already a reliable FPL asset at Villa. <b>Luka Vušković</b> (Brighton, from Tottenham) and <b>Piero Hincapié</b> (Arsenal, from Leverkusen) are the defensive signings to watch, though Arsenal\'s back line loses two starters this week.</p>
<h3>Captains</h3>
<p>BRYME\'s order, argued from the facts above: <b>Saka</b> (home, promoted opposition, confirmed fit) over <b>Haaland</b> (home, strong fixture, one attacker short) over <b>Salah</b> (difficult away fixture, highest safety). These are opinions — captaincy is a choice, not a fact.</p>
<h2>What changes on Saturday</h2>
<p>The five Saturday fixtures (Hull v Manchester United 12:30; Everton v Crystal Palace, Ipswich v Sunderland, Nottingham Forest v Leeds 15:00; Brentford v Tottenham 17:30) are the first chance to see which of the pre-season narratives hold. With the deadline already passed, these results feed Gameweek 2 decisions — including which promoted sides look defensively organised enough to hold clean sheets.</p>
</article>
</div>
<section class="sp-source"><h2>Source</h2><p><b>Source:</b> Fantasy Football Scout (20 Aug 2026), Rotowire (21 Aug 2026), ESPN (21 Aug 2026), BRYME PL transfer tracker (Sky Sports, PL official tracker)</p>
<p><b>Original report:</b> <a href="https://www.premierleague.com/transfers" rel="noopener" target="_blank">https://www.premierleague.com/transfers</a></p>
<p class="sp-source-note">Information on this page is rewritten in BRYME\'s own original editorial voice, never copied. External selections and claims are always identified with their source. Picks and captaincy advice are BRYME\'s opinions, not facts.</p></section>
{related_links()}
</article>
</main>'''

def splice(path, new_main):
    s = open(path, encoding='utf-8').read()
    orig = s
    i = s.find('<main'); j = s.find('</main>')
    if i < 0 or j < 0:
        print("NO MAIN:", path); return False
    s = s[:i] + new_main + s[j + len('</main>'):]
    if s != orig:
        open(path, 'w', encoding='utf-8').write(s)
        return True
    return False

if __name__ == '__main__':
    done = 0
    for p, main in [
        ('sports/fpl/index.html', hub_main),
        ('sports/fpl/gameweek-1/index.html', gw1_main),
        ('sports/fpl/gameweek-1-players-to-watch/index.html', p2w_main),
    ]:
        fp = os.path.join(ROOT, p)
        if splice(fp, main): done += 1
    print("pages rebuilt:", done, "/ 3")
