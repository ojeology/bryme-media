#!/usr/bin/env python3
"""Build the lean stylesheet used by Search-eligible legacy editorial pages."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
base = (ROOT / "assets/bryme-v2.css").read_text(encoding="utf-8")
compat = r'''

/* Lean editorial compatibility layer — replaces the 263 KB legacy platform sheet. */
.shell{width:min(calc(100% - 32px),var(--max));margin-inline:auto}
.top{position:sticky;z-index:50;top:0;border-bottom:1px solid var(--line);background:rgba(7,16,13,.9);backdrop-filter:blur(18px)}
.top .shell{min-height:72px;display:flex;align-items:center;justify-content:space-between;gap:24px}
.brand{font-size:18px;font-weight:950;letter-spacing:.08em}.brand b{color:var(--green)}
.topnav{display:flex;align-items:center;gap:5px}.topnav a{padding:9px 11px;border-radius:9px;color:var(--muted);font-size:13.5px;font-weight:750}.topnav a:hover,.topnav a.active{color:var(--ink);background:rgba(255,255,255,.06)}
.top-tools{display:flex;align-items:center}.header-search{padding:8px 13px;border:1px solid var(--line);border-radius:10px;color:var(--lime);font-size:13px;font-weight:850}
.crumb{padding:24px 0 0;color:var(--muted);font-size:13px}.crumb a{color:#c9d5cf}.crumb a:hover{color:var(--green)}
.article-hero{position:relative;isolation:isolate;overflow:hidden;min-height:360px;margin:20px 0 0;padding:110px clamp(20px,5vw,58px) 42px;display:flex;flex-direction:column;justify-content:flex-end;border:1px solid var(--line);border-radius:var(--radius);background:var(--panel)}
.article-hero-photo:before{content:"";position:absolute;inset:0;z-index:-2;background-image:var(--hero-img);background-size:cover;background-position:center}
.article-hero:after{content:"";position:absolute;inset:0;z-index:-1;background:linear-gradient(180deg,rgba(5,12,9,.16),rgba(5,12,9,.93) 83%)}
.article-hero .eyebrow{color:var(--lime);font-size:11px;font-weight:900;letter-spacing:.13em;text-transform:uppercase}
.article-hero h1{max-width:880px;margin:10px 0 12px;font-size:clamp(34px,6vw,64px);line-height:1.04;letter-spacing:-.045em;color:#fff}
.article-hero .lead{max-width:760px;margin:0;color:#d5ded9;font-size:17px;line-height:1.55}
.article-meta{display:flex;flex-wrap:wrap;gap:7px 14px;margin-top:18px;color:#bdc9c3;font-size:13px}.article-meta a{color:#fff;text-decoration:underline;text-underline-offset:3px}.article-meta span+span:before{content:"·";margin-right:14px;color:var(--dim)}
.article-byline{margin:12px 0 0;color:var(--muted);font-size:13px}
.article-body,.legal-prose{width:min(100%,780px);padding:42px 0 84px}
.prose h2{margin:42px 0 12px;font-size:clamp(25px,4vw,35px);line-height:1.18;letter-spacing:-.025em}.prose h3{margin:28px 0 8px;font-size:21px}.prose p,.prose li{color:#d5ded9;font-size:18px;line-height:1.82}.prose li+li{margin-top:8px}.prose ul,.prose ol{padding-left:24px}.prose a{color:var(--lime);text-decoration:underline;text-decoration-thickness:1px;text-underline-offset:3px}.prose blockquote{margin:28px 0;padding:8px 0 8px 22px;border-left:3px solid var(--green);color:var(--ink);font-size:22px;line-height:1.5}
.article-source{padding:12px 16px;border-left:3px solid var(--gold);background:rgba(240,199,106,.07);color:#f4dba2!important;font-size:14px!important}
.article-related,.sp-related{margin-top:54px;padding-top:28px;border-top:1px solid var(--line)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(175px,1fr));gap:16px}.tile{display:block;min-width:0}.poster{position:relative;aspect-ratio:16/9;overflow:hidden;border:1px solid var(--line);border-radius:12px;background:var(--panel)}.poster img{width:100%;height:100%;object-fit:cover;display:block}.tile h3{margin:9px 0 3px;font-size:14px;line-height:1.35}.tile-meta{display:flex;gap:6px;align-items:center;flex-wrap:wrap;color:var(--muted);font-size:11px}.type-badge{padding:2px 6px;border-radius:4px;background:var(--panel-2);color:var(--green);font-size:9px;font-weight:900;letter-spacing:.07em}.tile-play{display:none}
.list{display:grid;gap:10px}.row{display:block;padding:14px 0;border-bottom:1px solid var(--line)}.row b{display:block}.meta{color:var(--muted)!important}
.sp-source,.sp-faq{margin:30px 0;padding:20px;border:1px solid var(--line);border-radius:14px;background:var(--panel)}.sp-source h2,.sp-faq h2{margin-top:0}.sp-source p,.sp-source-note{font-size:14px!important;color:var(--muted)!important}
.sp-related h2{font-size:20px}.sp-rel-grid{display:flex;flex-wrap:wrap;gap:9px}.sp-rel{padding:7px 12px;border:1px solid var(--line);border-radius:999px;color:#d5ded9;font-size:13px}.sp-rel:hover{border-color:var(--green)}
.sp-table-wrap{max-width:100%;overflow-x:auto;margin:24px 0;border:1px solid var(--line);border-radius:12px}.sp-table{width:100%;min-width:620px;border-collapse:collapse;font-size:14px}.sp-table th,.sp-table td{padding:11px 13px;border-bottom:1px solid var(--line);text-align:left}.sp-table th{color:var(--muted);background:var(--panel);font-size:11px;text-transform:uppercase;letter-spacing:.07em}
.vcat-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}.vcat{display:flex;min-height:140px;flex-direction:column;justify-content:flex-end;padding:18px;border:1px solid var(--line);border-radius:14px;background:var(--panel)}.vcat b{font-size:16px}.vcat span{margin-top:5px;color:var(--muted);font-size:12px}.vcat-photo{position:relative;isolation:isolate;overflow:hidden;color:#fff}.vcat-photo:before{content:"";position:absolute;inset:0;z-index:-2;background-image:var(--card-img);background-size:cover;background-position:center}.vcat-photo:after{content:"";position:absolute;inset:0;z-index:-1;background:linear-gradient(180deg,rgba(5,12,9,.15),rgba(5,12,9,.92))}
.section{padding:56px 0}.section-head{display:flex;justify-content:space-between;gap:20px;align-items:end;margin-bottom:22px}.section-head h2{margin:0;font-size:30px}.section-head a{color:var(--green);font-weight:800}
.send-bar{display:flex;flex-wrap:wrap;align-items:center;gap:10px 14px;margin-top:18px;padding:12px 14px;border:1px solid var(--line);border-radius:12px;background:var(--panel)}.send-bar p{margin:0;color:var(--muted);font-size:13px}.send-wa{padding:8px 13px;border-radius:9px;background:#25d366;color:#06150e;font-size:13px;font-weight:900}
.quiet-link{border:0;background:transparent;color:var(--lime);font:inherit;font-weight:800;cursor:pointer}
.mobile-nav{display:none}.footer{border-top:1px solid var(--line);padding:54px 0 40px;background:#050b09}.footer-grid{display:grid;grid-template-columns:1.4fr repeat(3,1fr);gap:30px}.footer-brand p,.footer-note,.footer small{color:var(--muted);font-size:13px}.footer-col{display:flex;flex-direction:column;gap:8px}.footer-col h4{margin:0 0 6px;font-size:11px;text-transform:uppercase;letter-spacing:.1em}.footer-col a{color:var(--muted);font-size:13px}.footer-col a:hover{color:var(--green)}
.integrity-notice{position:relative;z-index:5;width:min(calc(100% - 32px),var(--max));margin:12px auto;padding:13px 18px;border:1px solid rgba(255,190,100,.38);border-radius:8px;background:#281b0d;color:#f3d7ad;font-size:13px}.integrity-notice b{color:#ffd08a}
@media(max-width:760px){
 .shell{width:min(calc(100% - 24px),var(--max))}.top .shell{min-height:58px}.topnav{display:none}.header-search{display:inline-flex}.article-hero{min-height:300px;margin-top:12px;padding:84px 18px 26px}.article-hero h1{font-size:clamp(30px,10vw,44px)}.article-hero .lead{font-size:15px}.article-body,.legal-prose{padding:28px 0 64px}.prose h2{margin-top:32px;font-size:25px}.prose p,.prose li{font-size:16px;line-height:1.72}.grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:11px}.section{padding:40px 0}.section-head h2{font-size:25px}.footer{padding-bottom:84px}.footer-grid{grid-template-columns:1fr 1fr}.footer-brand{grid-column:1/-1}.mobile-nav{position:fixed;z-index:60;left:0;right:0;bottom:0;display:grid;grid-template-columns:repeat(6,1fr);border-top:1px solid var(--line);background:rgba(5,11,9,.97);padding-bottom:env(safe-area-inset-bottom,0)}.mobile-nav a{min-width:0;padding:8px 1px;color:var(--muted);text-align:center;font-size:9px;font-weight:800}.mobile-nav .mn-ico{display:block;color:var(--green);font-size:14px}.integrity-notice{width:calc(100% - 24px)}
}
@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;transition:none!important}}
'''
out = (base.rstrip() + compat).rstrip() + "\n"
(ROOT / "assets/content-v2.css").write_text(out, encoding="utf-8")
print(f"wrote assets/content-v2.css ({len(out.encode('utf-8'))} bytes)")
