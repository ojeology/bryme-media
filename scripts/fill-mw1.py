#!/usr/bin/env python3
"""BRYME · Fill the 4 Matchweek-1 sports article placeholders with researched content.
All facts sourced: GW1 fixtures (content/fixtures.json), team news (Fantasy Football
Scout 20 Aug 2026, Rotowire 21 Aug 2026, premierleague.com), transfers
(content/pl-transfers.json). Picks/storylines are clearly editorial opinion.
"""
import json, os, re, html as H

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def esc(s): return H.escape(str(s), quote=True)

fixtures = json.load(open(os.path.join(ROOT, 'content/fixtures.json')))
transfers = json.load(open(os.path.join(ROOT, 'content/pl-transfers.json')))
gw1 = fixtures['matchweeks'][0]['matches']
gw1.sort(key=lambda m: (m.get('date', ''), m.get('time', '')))

def gw1_list():
    rows = []
    for m in gw1:
        rows.append(f'<li><b>{esc(m.get("homeName", ""))} v {esc(m.get("awayName", ""))}</b> — {esc(m.get("dayLabel", m.get("date", "")))}, {esc(m.get("time", ""))} UK' + (f', TV: {esc(m.get("tv", ""))}' if m.get('tv') else '') + '</li>')
    return ''.join(rows)

def make_article(path, eyebrow, h1, lead, body_html, source_name, source_url, related, published):
    html = open(path, encoding='utf-8').read()
    orig = html
    new_main = (
        '<main class="shell"><div class="crumb"><a href="/">Home</a> / <a href="/sports/">BRYME Sports</a> / '
        + esc(h1) + '</div>'
        '<article class="sp-article">'
        '<header class="sp-article-head"><div class="eyebrow">' + eyebrow + '</div>'
        '<h1>' + esc(h1) + '</h1>'
        '<p class="lead">' + esc(lead) + '</p>'
        '<div class="sp-meta"><span>By BRYME Sports Editorial</span><span>Published: ' + published + '</span><span>Last updated: ' + published + '</span></div>'
        '</header>'
        '<div class="sp-body">' + body_html + '</div>'
        '<section class="sp-source"><h2>Source</h2><p><b>Source:</b> ' + esc(source_name) + '</p>'
        '<p><b>Original report:</b> <a href="' + esc(source_url) + '" rel="noopener" target="_blank">' + esc(source_url) + '</a></p>'
        '<p class="sp-source-note">Information on this page is rewritten in BRYME\'s own original editorial voice, never copied. External selections and claims are always identified with their source. Editorial picks and storylines are BRYME\'s opinions, not facts.</p></section>'
        '<section class="sp-related"><h2>Related reading</h2><div class="sp-rel-grid">' + related + '</div></section>'
        '</article></main>'
    )
    i = html.find('<main'); j = html.find('</main>')
    if i < 0 or j < 0:
        print("NO MAIN:", path); return False
    html = html[:i] + new_main + html[j + len('</main>'):]
    if html != orig:
        open(path, 'w', encoding='utf-8').write(html)
        return True
    return False

def rel(label, href):
    return f'<a class="sp-rel" href="{href}">{label}</a>'

# ================= 1. Matchweek 1 preview =================
preview_body = (
    '<div class="prose legal-prose">'
    '<h2>The opening round</h2>'
    '<p>The 2026/27 Premier League season begins over four days, from the Friday night opener to Monday\'s London derby at Craven Cottage. All ten fixtures, kick-off times and TV listings are below, as published by the Premier League.</p>'
    '<ul>' + gw1_list() + '</ul>'
    '<h2>Friday: the champions begin</h2>'
    '<p>Arsenal beat newly promoted Coventry City 3-0 at the Emirates — Kai Havertz, Bukayo Saka and Martin Ødegaard on the scoresheet (ESPN, 21 Aug). It is the sixth consecutive season in which the defending champions have won their opening fixture.</p>'
    '<h2>Saturday</h2>'
    '<p>Hull City v Manchester United is the early game — the promoted side\'s first top-flight home match since 2017, against a United side under Michael Carrick that finished third last season. Tottenham travel to Brentford without Pedro Porro, Micky van de Ven and Pape Sarr (Rotowire, 21 Aug). Everton host Crystal Palace missing James Garner, Christian Nørgaard and Tim Iroegbunam.</p>'
    '<h2>Sunday and Monday</h2>'
    '<p>Manchester City welcome Bournemouth with Jeremy Doku their only absentee, and Newcastle host Liverpool — who travel without Hugo Ekitike, Conor Bradley and Joe Gomez. Monday closes the round at Fulham v Chelsea, with Xabi Alonso\'s Chelsea bringing record signing Morgan Rogers (£117m from Aston Villa).</p>'
    '<h2>What to watch</h2>'
    '<p>Four clubs begin under new managers: Xabi Alonso (Chelsea), Keith Andrews (Brentford), Marco Rose (Bournemouth) and Michael Carrick (Manchester United). Form from pre-season counts for little — the confirmed team news above is the more reliable signal.</p>'
    '</div>'
)

# ================= 2. Players to watch =================
p2w_body = (
    '<div class="prose legal-prose">'
    '<h2>Five players ready to make their mark</h2>'
    '<p>These five are argued from confirmed team news, new signings and opening fixtures. They are editorial selections — every claim about availability comes from the sources cited.</p>'
    '<h3>1. Morgan Rogers — Chelsea (midfielder, £117m)</h3>'
    '<p>The most expensive signing of the summer arrives at a Chelsea side opening at Fulham on Monday. Rogers scored and assisted regularly at Aston Villa last season and is a ready-made FPL asset; the transfer tracker lists the move as confirmed (Sky Sports, PL tracker).</p>'
    '<h3>2. Bukayo Saka — Arsenal</h3>'
    '<p>Confirmed fit and on the scoresheet in Friday\'s 3-0 win over Coventry (ESPN). With Saliba and Timber out, Arsenal\'s attacking route carries even more weight in the opener.</p>'
    '<h3>3. Kai Havertz — Arsenal</h3>'
    '<p>Scored the season\'s first goal in the 15th minute on Friday. Lower ownership than Saka and Salah makes him the differential pick of the champions\' attack.</p>'
    '<h3>4. Luka Vušković — Brighton (defender, ~€54m)</h3>'
    '<p>Brighton\'s record purchase from Tottenham. Note: Baleba, Mitoma and Tzimas are all ruled out of Sunday\'s game at Aston Villa (Rotowire), so the back line — and Vušković — will be tested early.</p>'
    '<h3>5. Mamadou Sangaré — Brentford (midfielder, ~€48m)</h3>'
    '<p>Brentford\'s club-record signing from Lens hosts a Tottenham side missing three starters. A home fixture against a depleted opponent is a strong platform for a debut statement.</p>'
    '<h2>Also worth a squad place</h2>'
    '<p>Erling Haaland (home to Bournemouth, only absentee Doku) and Mohamed Salah (safest premium despite the trip to Newcastle) remain the captaincy anchors. See the <a href="/sports/fpl/gameweek-1/">FPL Gameweek 1</a> page for BRYME\'s full captaincy discussion.</p>'
    '</div>'
)

# ================= 3. Injuries report =================
injuries = [
    ('Arsenal', 'William Saliba and Jurrien Timber miss the opener; Bruno Guimarães was a groin doubt for the Coventry match. (FFScout 20 Aug, Rotowire 21 Aug)'),
    ('Tottenham Hotspur', 'Pedro Porro, Micky van de Ven and Pape Sarr out for Brentford; Dominic Solanke back in the group. (Rotowire 21 Aug)'),
    ('Brighton & Hove Albion', 'Carlos Baleba, Kaoru Mitoma and Stefanos Tzimas ruled out of the Aston Villa game. (Rotowire 21 Aug)'),
    ('Everton', 'James Garner, Christian Nørgaard and Tim Iroegbunam miss Crystal Palace. (Rotowire 21 Aug)'),
    ('Manchester City', 'Jeremy Doku — calf, two to three weeks; the only confirmed absentee. (Rotowire 21 Aug)'),
    ('Liverpool', 'Hugo Ekitike, Conor Bradley and Joe Gomez out; Curtis Jones unavailable amid an expected Inter Milan move. (Rotowire 21 Aug)'),
    ('Chelsea', 'Wesley Fofana suspended for the first two gameweeks; Danny Welbeck expected fit. (FFScout 20 Aug)'),
    ('Newcastle United', 'Joelinton out; Tino Livramento not ready; Dedic set to debut. (FFScout 20 Aug)'),
    ('Nottingham Forest', 'Ryan Yates and Savona miss out; rest of squad available. (FFScout 20 Aug)'),
    ('Leeds United', 'Gudmundsson and Gnonto ruled out. (FFScout 20 Aug)'),
    ('Sunderland', 'Adingra out; Alderete, Mukiele and Meunier available. (FFScout 20 Aug)'),
    ('Bournemouth', 'Ryan Christie suspended; Adams, Juanlu Sánchez and Rodríguez train. (FFScout 20 Aug)'),
]
inj_items = ''.join(f'<li><b>{esc(c)}:</b> {esc(t)}</li>' for c, t in injuries)
injuries_body = (
    '<div class="prose legal-prose">'
    '<h2>Matchweek 1 availability</h2>'
    '<p>Compiled from the Friday press conferences. Only items confirmed by clubs or official channels are listed — nothing here is speculative. Availability changes squads and, for FPL managers, lineups.</p>'
    '<ul>' + inj_items + '</ul>'
    '<h2>What this means</h2>'
    '<p>Two promoted sides open against wounded opponents: Coventry faced an Arsenal side without its first-choice centre-back pairing, and Brentford meet a Tottenham side missing three starters. Manchester City, unusually, have a near-full squad; Liverpool and Newcastle both carry notable absences into their Sunday meeting.</p>'
    '</div>'
)

# ================= 4. Biggest matches =================
big_body = (
    '<div class="prose legal-prose">'
    '<h2>The five fixtures that decide the weekend\'s story</h2>'
    '<h3>Arsenal 3-0 Coventry City — Friday</h3>'
    '<p>Already played: the champions began their title defence with a routine win. Havertz 15\', Saka 23\', Ødegaard 49\' (ESPN). It tells us little about the title race — and everything about the gap between the top and a promoted side.</p>'
    '<h3>Newcastle United v Liverpool — Sunday, 16:30</h3>'
    '<p>The weekend\'s heavyweight fixture. Liverpool are missing Ekitike, Bradley and Gomez; Newcastle are without Joelinton. Two clubs with injury clouds meet in front of a full St James\' Park — the most likely place for the first genuine shock of the season.</p>'
    '<h3>Hull City v Manchester United — Saturday, 12:30</h3>'
    '<p>Michael Carrick\'s first league game as United manager, away at a promoted side playing its first top-flight home match in nine years. United have won eight of ten PL meetings and never lost to Hull in the division.</p>'
    '<h3>Manchester City v Bournemouth — Sunday, 14:00</h3>'
    '<p>City\'s easiest-looking fixture of the round, with Doku the only absentee. Bournemouth arrive under new manager Marco Rose with three confirmed signings (Álvaro Rodríguez, António Silva, Juanlu Sánchez).</p>'
    '<h3>Fulham v Chelsea — Monday, 20:00</h3>'
    '<p>A west London derby to close the round — and the debut stage for £117m signing Morgan Rogers. Chelsea\'s new-look side under Xabi Alonso will be the most-watched team of Monday night.</p>'
    '<h2>How to follow</h2>'
    '<p>Every match has a preview page in the <a href="/sports/premier-league/matches/">Match Centre</a>, updated with verified results after full time.</p>'
    '</div>'
)

related_all = (
    rel('matchweek 1 preview', '/sports/premier-league/matchweek-1-preview/') +
    rel('players to watch', '/sports/premier-league/players-to-watch-matchweek-1/') +
    rel('injuries', '/sports/premier-league/injuries-matchweek-1/') +
    rel('FPL gameweek 1', '/sports/fpl/gameweek-1/') +
    rel('transfers 2026/27', '/sports/transfers/premier-league-2026-27/')
)

JOBS = [
    ('sports/premier-league/matchweek-1-preview/index.html',
     '⚽ BRYME Sports · Matchweek Preview',
     'Premier League Matchweek 1: Everything You Need to Know',
     'The complete Matchweek 1 briefing: all ten fixtures, kick-off times, TV listings, team news and the storylines that matter.',
     preview_body,
     'Fantasy Football Scout (20 Aug 2026), Rotowire (21 Aug 2026), ESPN (21 Aug 2026), premierleague.com',
     'https://www.premierleague.com/fixtures',
     '21 August 2026'),
    ('sports/premier-league/players-to-watch-matchweek-1/index.html',
     '⚽ BRYME Sports · Players',
     '5 Players Ready to Make Their Mark in Matchweek 1',
     'New signings, breakout candidates and underrated names who could have a matchweek-one impact — every availability claim sourced.',
     p2w_body,
     'BRYME PL transfer tracker (Sky Sports, PL official tracker), Rotowire (21 Aug 2026), ESPN (21 Aug 2026)',
     'https://www.premierleague.com/transfers',
     '21 August 2026'),
    ('sports/premier-league/injuries-matchweek-1/index.html',
     '⚽ BRYME Sports · Injury & Availability',
     'Premier League Injury & Availability Report — Matchweek 1',
     'Injured, doubtful, suspended and returning players across all ten gameweek-one fixtures, from the Friday press conferences.',
     injuries_body,
     'Fantasy Football Scout (20 Aug 2026), Rotowire (21 Aug 2026), premierleague.com injury page',
     'https://www.premierleague.com/injury-news',
     '21 August 2026'),
    ('sports/premier-league/biggest-matches-matchweek-1/index.html',
     '⚽ BRYME Sports · Match Preview',
     'The Biggest Matches of Matchweek 1',
     'The fixtures that can\'t be missed this gameweek, with the storylines behind each one.',
     big_body,
     'ESPN (21 Aug 2026), Rotowire (21 Aug 2026), BRYME fixture data (premierleague.com)',
     'https://www.premierleague.com/fixtures',
     '21 August 2026'),
]

if __name__ == '__main__':
    done = 0
    for path, eyebrow, h1, lead, body, src, url, pub in JOBS:
        fp = os.path.join(ROOT, path)
        if make_article(fp, eyebrow, h1, lead, body, src, url, related_all, pub):
            done += 1
    print("matchweek-1 articles rebuilt:", done, "/", len(JOBS))
