#!/usr/bin/env python3
"""BRYME · Add post-match analysis editorial to the 5 played match pages that lack it.
Only verified facts; predictions referenced from match-editorial.json.
"""
import os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

POST = {
    'sports/premier-league/matches/arsenal-vs-coventry/index.html': [
        ('What actually happened',
         "Kai Havertz put the champions ahead in the 15th minute, Bukayo Saka doubled the lead midway through the first half and Martin Ødegaard added a third four minutes after the interval (ESPN, 21 Aug). Coventry kept the score respectable, but Arsenal controlled the game throughout and opened the defence of their title with a routine win."),
        ('Against the pre-match prediction',
         "BRYME's published prediction was Arsenal 4-0. The winner and the clean sheet were called correctly; the exact scoreline was off by one goal. The prediction itself flagged the exact-scoreline call as the least reliable part of the forecast — this result is a reminder of exactly why."),
        ('BRYME post-match analysis',
         "The most useful read of this game is how little it tells us about the title race. Beating a newly promoted side at home is the minimum requirement for a defending champion, and Arsenal did it without needing to hit top gear. The notable detail is the timing of the goals — all three arrived in open play, spread across the match, with the game settled by the 49th minute. For FPL managers, Havertz and Saka both delivered on opening night; the 3-0 also keeps Arsenal's clean-sheet run alive for Gameweek 2."),
    ],
    'sports/la-liga/matches/atletico-madrid-vs-malaga/index.html': [
        ('What actually happened',
         "Atlético Madrid beat promoted Málaga 2-0 in their delayed season opener at the Metropolitano. The fixture had been pushed back from the opening round because of World Cup commitments, and Atlético started four days after everyone else (BBC Sport, 19 Aug). They controlled the game and took the points without drama."),
        ('Against the pre-match prediction',
         "BRYME's published prediction was Atlético 3-0. The winner and the clean sheet were called correctly; the exact scoreline was off by one goal."),
        ('BRYME post-match analysis',
         "The delayed start was the storyline, and Atlético handled it. The questions around a squad with four days' fewer preparation than the rest of the division were answered with a clean-sheet win. A 2-0 rather than a 3-0 is not a concern — the performance matters more than the margin in an opener, and Atlético's record of grinding out wins was intact from the first whistle."),
    ],
    'sports/la-liga/matches/rayo-vallecano-vs-alaves/index.html': [
        ('What actually happened',
         "Rayo Vallecano and Deportivo Alavés drew 1-1 (BBC Sport, 20 Aug). Both sides had already played once this season — Rayo lost 2-1 at Sevilla, Alavés beat Getafe 3-0 — and the draw leaves both unbeaten at home and away respectively across the opening exchanges."),
        ('Against the pre-match prediction',
         "BRYME's published prediction was exactly this result: Rayo Vallecano 1-1 Alavés. The scoreline was called correctly — the first exact hit of the season for BRYME's editorial predictions."),
        ('BRYME post-match analysis',
         "A 1-1 is the definition of a fair result between two mid-table sides finding their level. Alavés arrived with confidence after their 3-0 opening win and left with a point; Rayo will feel they should have turned home advantage into more. For the wider picture, both clubs look organised enough to avoid the relegation conversation that pre-season predicted for at least one of them."),
    ],
    'sports/la-liga/matches/real-betis-vs-real-sociedad/index.html': [
        ('What actually happened',
         "Rodrigo Riquelme's tidy left-foot finish in the 63rd minute, assisted by C. Hernández, settled a tight game at the Estadio de la Cartuja (BBC Sport, 21 Aug). Betis out-shot Real Sociedad 18-10 and put more on target 7-3, yet the visitors recorded the higher expected goals (1.58 to 1.06) — an inspired evening from Betis goalkeeper Álex Remiro kept it at one."),
        ('Against the pre-match prediction',
         "BRYME's published prediction was Real Betis 1-1 Real Sociedad. The draw never materialised: Betis took the single goal that the prediction gave them, but Real Sociedad could not find the reply. The winner call was the miss — Betis edged what was forecast as a stalemate."),
        ('BRYME post-match analysis',
         "This was the two sides' first competitive game of the season, both having been postponed in the opening round. Betis' win says more about their stability than their dominance — they were second-best on expected goals and won through one moment of quality plus a goalkeeping performance. Real Sociedad will take encouragement from creating more and the concern that they converted none of it."),
    ],
    'sports/ligue-1/matches/marseille-vs-strasbourg/index.html': [
        ('What actually happened',
         "Goalless at half time, Marseille blew Strasbourg away after the break: Amine Gouiri scored twice (46', 68' penalty), Keyliane Abdallah added a third in the 89th minute and Pierre-Emile Højbjerg a fourth in stoppage time. Strasbourg played the final half-hour a man down after S. El Mourabet's red card in the 59th minute (BBC Sport, 21 Aug)."),
        ('Against the pre-match prediction',
         "BRYME's published prediction was Marseille 2-1. The winner was called correctly; the scoreline was well off — the red card changed the shape of the game and the goals arrived once Strasbourg were down to ten."),
        ('BRYME post-match analysis',
         "The 4-0 flatters a game that was 0-0 at the break, and the red card is the hinge: three of the four goals came after the 59th minute against ten men. For Ligue 1 watchers the encouraging sign is the depth of Marseille's attacking options — Gouiri's brace, Abdallah's late finish and Højbjerg's long-range strike all came from different sources. For FPL-adjacent purposes, Marseille's opener is the clearest statement of any side on the opening weekend."),
    ],
}

def add_postmatch(path, blocks):
    s = open(path, encoding='utf-8').read()
    if '<section class="sp-postmatch">' in s:
        print(f"  already has post-match: {path}")
        return
    msecs = ''.join(
        f'<div class="sp-msec"><b>{esc(b)}</b><p>{esc(p)}</p></div>'
        for b, p in blocks
    )
    # "Against the pre-match prediction" block with honesty note
    sec = (
        '<section class="sp-postmatch">\n'
        '    <h3 class="sp-dir">Post-match analysis</h3>\n'
        '    <div class="sp-msec-grid">\n'
        + msecs +
        '    </div>\n'
        '  </section>\n'
    )
    # Insert right after the result block's closing </div>
    i = s.find('</div>\n        \n        <section class="sp-preview')
    if i < 0:
        # fallback: after the source-note of the result
        i = s.find('checked ')
        if i > 0:
            j = s.find('</p></div>', i)
            if j > 0:
                i = j + len('</p></div>')
    if i < 0:
        print(f"  [no insertion point] {path}")
        return
    s = s[:i] + '\n        \n        ' + sec + s[i:]
    open(path, 'w', encoding='utf-8').write(s)
    print(f"  added post-match: {path}")

def esc(s): return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

if __name__ == '__main__':
    for path, blocks in POST.items():
        add_postmatch(os.path.join(ROOT, path), blocks)
