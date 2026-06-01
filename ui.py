"""Lapisan tampilan bergaya shadcn untuk aplikasi Streamlit.

Berisi:
  - ICONS  : kumpulan ikon Lucide (set ikon resmi shadcn/ui) sebagai SVG inline.
  - icon() : render satu ikon.
  - CSS    : tema "new-york" shadcn (netral zinc, font Geist, border halus).
  - komponen: inject_css(), hero(), section(), stat_cards(), alert(), metric().

Tidak ada emoji — seluruh ikon memakai Lucide agar tampilan bersih & profesional.
"""
from __future__ import annotations

from typing import List

import streamlit as st

# --------------------------------------------------------------------------- #
# Ikon Lucide (https://lucide.dev) — set ikon bawaan shadcn/ui.
# Nilai = isi dalam <svg>; pembungkus <svg> ditambahkan oleh icon().
# --------------------------------------------------------------------------- #
ICONS = {
    "truck": '<path d="M14 18V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v11a1 1 0 0 0 1 1h2"/><path d="M15 18H9"/><path d="M19 18h2a1 1 0 0 0 1-1v-3.65a1 1 0 0 0-.22-.624l-3.48-4.35A1 1 0 0 0 17.52 8H14"/><circle cx="7" cy="18" r="2"/><circle cx="17" cy="18" r="2"/>',
    "package": '<path d="m7.5 4.27 9 5.15"/><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/>',
    "map-pin": '<path d="M20 10c0 4.993-5.539 10.193-7.399 11.799a1 1 0 0 1-1.202 0C9.539 20.193 4 14.993 4 10a8 8 0 0 1 16 0"/><circle cx="12" cy="10" r="3"/>',
    "grid": '<rect width="18" height="18" x="3" y="3" rx="2"/><path d="M3 9h18"/><path d="M3 15h18"/><path d="M9 3v18"/><path d="M15 3v18"/>',
    "calculator": '<rect width="16" height="20" x="4" y="2" rx="2"/><line x1="8" x2="16" y1="6" y2="6"/><line x1="16" x2="16" y1="14" y2="18"/><path d="M16 10h.01"/><path d="M12 10h.01"/><path d="M8 10h.01"/><path d="M12 14h.01"/><path d="M8 14h.01"/><path d="M12 18h.01"/><path d="M8 18h.01"/>',
    "badge-check": '<path d="M3.85 8.62a4 4 0 0 1 4.78-4.77 4 4 0 0 1 6.74 0 4 4 0 0 1 4.78 4.78 4 4 0 0 1 0 6.74 4 4 0 0 1-4.77 4.78 4 4 0 0 1-6.75 0 4 4 0 0 1-4.78-4.77 4 4 0 0 1 0-6.76Z"/><path d="m9 12 2 2 4-4"/>',
    "circle-check": '<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>',
    "list-ordered": '<path d="M10 12h11"/><path d="M10 18h11"/><path d="M10 6h11"/><path d="M4 10h2"/><path d="M4 6h1v4"/><path d="M6 18H4c0-1 2-2 2-3s-1-1.5-2-1"/>',
    "info": '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
    "triangle-alert": '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
    "settings": '<path d="M20 7h-9"/><path d="M14 17H5"/><circle cx="17" cy="17" r="3"/><circle cx="7" cy="7" r="3"/>',
    "money": '<rect width="20" height="12" x="2" y="6" rx="2"/><circle cx="12" cy="12" r="2"/><path d="M6 12h.01M18 12h.01"/>',
    "trending-down": '<polyline points="22 17 13.5 8.5 8.5 13.5 2 7"/><polyline points="16 17 22 17 22 11"/>',
    "layers": '<path d="M12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83Z"/><path d="m22 17.65-9.17 4.16a2 2 0 0 1-1.66 0L2 17.65"/><path d="m22 12.65-9.17 4.16a2 2 0 0 1-1.66 0L2 12.65"/>',
    "repeat": '<path d="m17 2 4 4-4 4"/><path d="M3 11v-1a4 4 0 0 1 4-4h14"/><path d="m7 22-4-4 4-4"/><path d="M21 13v1a4 4 0 0 1-4 4H3"/>',
    "route": '<circle cx="6" cy="19" r="3"/><path d="M9 19h8.5a3.5 3.5 0 0 0 0-7h-11a3.5 3.5 0 0 1 0-7H15"/><circle cx="18" cy="5" r="3"/>',
}


def icon(name: str, size: int = 18, stroke: float = 2) -> str:
    """Kembalikan markup SVG sebuah ikon Lucide (warna mengikuti currentColor)."""
    body = ICONS.get(name, "")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="{stroke}" '
        f'stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:middle">'
        f"{body}</svg>"
    )


# --------------------------------------------------------------------------- #
# Stylesheet — tema shadcn "new-york" (light, netral zinc).
# --------------------------------------------------------------------------- #
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600;700&family=Geist+Mono:wght@400;500;600&display=swap');

:root{
  --bg:#ffffff; --fg:#09090b; --card:#ffffff;
  --muted:#f4f4f5; --muted-fg:#71717a; --border:#e4e4e7;
  --primary:#18181b; --primary-fg:#fafafa; --radius:0.5rem;
  --green:#16a34a; --green-bg:#f0fdf4; --green-border:#bbf7d0;
  --amber:#b45309; --amber-bg:#fffbeb; --amber-border:#fde68a;
  --red:#dc2626; --red-bg:#fef2f2; --red-border:#fecaca;
}

.stApp, .stApp p, .stApp span, .stApp div, .stApp label, .stApp button,
[data-testid="stSidebar"] *{
  font-family:'Geist', ui-sans-serif, system-ui, -apple-system, sans-serif;
}
/* Jangan timpa font ikon Material Streamlit (mis. panah collapse sidebar),
   agar tetap dirender sebagai glyph, bukan teks ligatur 'keyboard_double_arrow_left'. */
[data-testid="stIconMaterial"]{ font-family:'Material Symbols Rounded' !important; }
.stApp{ background:var(--bg); color:var(--fg); }

/* Header & toolbar TETAP dirender agar tombol lipat/buka sidebar berfungsi.
   Hanya menu tiga-titik, tombol Deploy, dekorasi, dan footer yang disembunyikan. */
header[data-testid="stHeader"]{ background:transparent; }
[data-testid="stToolbarActions"], [data-testid="stMainMenu"], #MainMenu,
[data-testid="stAppDeployButton"], [data-testid="stStatusWidget"], footer,
[data-testid="stDecoration"]{ display:none; }
/* Tombol lipat sidebar selalu tampak (default Streamlit hanya saat hover, sehingga
   terkesan "sekilas muncul lalu hilang"). */
[data-testid="stSidebarCollapseButton"]{ visibility:visible !important; opacity:1 !important; }

.block-container{ padding-top:2.4rem; padding-bottom:5rem; max-width:1120px; }

h1,h2,h3,h4{ letter-spacing:-0.02em; color:var(--fg); font-weight:600; }

[data-testid="stMetricValue"], .mono{
  font-family:'Geist Mono', ui-monospace, monospace; font-variant-numeric:tabular-nums;
}

/* ---- buttons ---- */
.stButton > button{
  border-radius:.5rem; font-weight:500; padding:.45rem .9rem;
  border:1px solid var(--border); transition:background .15s ease, border-color .15s ease;
}
button[data-testid="stBaseButton-primary"]{
  background:var(--primary); color:var(--primary-fg); border:1px solid var(--primary);
}
button[data-testid="stBaseButton-primary"]:hover{ background:#27272a; border-color:#27272a; }
button[data-testid="stBaseButton-secondary"]{ background:var(--card); color:var(--fg); }
button[data-testid="stBaseButton-secondary"]:hover{ background:var(--muted); }

/* ---- tabs -> segmented control shadcn ---- */
.stTabs [data-baseweb="tab-list"]{
  background:var(--muted); padding:4px; border-radius:.6rem; gap:4px;
  border:1px solid var(--border);
}
.stTabs [data-baseweb="tab"]{
  height:auto; padding:6px 16px; border-radius:.45rem; color:var(--muted-fg);
  font-weight:500; background:transparent;
}
.stTabs [aria-selected="true"]{
  background:var(--card); color:var(--fg); box-shadow:0 1px 2px rgba(0,0,0,.07);
}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"]{ display:none; }

/* ---- data grids, expanders, inputs ---- */
[data-testid="stDataFrame"], [data-testid="stDataEditor"]{
  border:1px solid var(--border); border-radius:.5rem; overflow:hidden;
}
[data-testid="stExpander"]{ border:1px solid var(--border); border-radius:.5rem; box-shadow:none; }
[data-testid="stExpander"] summary{ font-weight:500; }
[data-testid="stExpander"] summary:hover{ color:var(--fg); }
.stSelectbox div[data-baseweb="select"] > div{ border-radius:.5rem; border-color:var(--border); }

/* ---- sidebar ---- */
[data-testid="stSidebar"]{ background:var(--muted); border-right:1px solid var(--border); }
[data-testid="stSidebar"] .block-container{ padding-top:1.5rem; }

/* ---- komponen kustom ---- */
.hero{ margin-bottom:1.2rem; }
.hero .eyebrow{
  display:inline-flex; align-items:center; gap:.4rem; font-size:.72rem; color:var(--muted-fg);
  border:1px solid var(--border); border-radius:999px; padding:.22rem .65rem; margin-bottom:.85rem;
  background:var(--card);
}
.hero .title{ display:flex; align-items:center; gap:.75rem; }
.hero .logo{
  width:44px; height:44px; border-radius:.7rem; background:var(--primary); color:var(--primary-fg);
  display:flex; align-items:center; justify-content:center; flex:0 0 auto;
}
.hero h1{ font-size:1.85rem; margin:0; font-weight:680; letter-spacing:-0.035em; }
.hero p{ color:var(--muted-fg); margin:.5rem 0 0; font-size:.95rem; max-width:60ch; }

.sec{ display:flex; align-items:center; gap:.65rem; margin:1.6rem 0 .55rem; }
.sec .ico{
  width:32px; height:32px; border:1px solid var(--border); border-radius:.5rem; background:var(--card);
  color:var(--fg); display:flex; align-items:center; justify-content:center; flex:0 0 auto;
}
.sec .t{ font-size:1.02rem; font-weight:600; letter-spacing:-0.01em; line-height:1.1; }
.sec .s{ font-size:.78rem; color:var(--muted-fg); margin-top:2px; }

.stat-grid{ display:grid; grid-template-columns:repeat(4,1fr); gap:.7rem; margin:.4rem 0 .2rem; }
.stat{ border:1px solid var(--border); border-radius:.65rem; padding:.85rem .95rem; background:var(--card); }
.stat .lab{
  display:flex; align-items:center; justify-content:space-between; color:var(--muted-fg);
  font-size:.72rem; text-transform:uppercase; letter-spacing:.045em; font-weight:500;
}
.stat .val{
  font-family:'Geist Mono', monospace; font-size:1.55rem; font-weight:600; margin-top:.4rem;
  letter-spacing:-0.02em; font-variant-numeric:tabular-nums; line-height:1.1;
}
.stat .val.green{ color:var(--green); } .stat .val.red{ color:var(--red); }
.stat .sub{ font-size:.73rem; color:var(--muted-fg); margin-top:.25rem; }

.alert{
  display:flex; gap:.7rem; align-items:flex-start; border:1px solid var(--border);
  border-radius:.65rem; padding:.8rem .95rem; margin:.5rem 0; background:var(--card); font-size:.9rem;
}
.alert .ico{ flex:0 0 auto; margin-top:1px; color:var(--muted-fg); }
.alert .ttl{ font-weight:600; }
.alert .desc{ color:var(--muted-fg); margin-top:2px; }
.alert.success{ background:var(--green-bg); border-color:var(--green-border); } .alert.success .ico{ color:var(--green); }
.alert.warning{ background:var(--amber-bg); border-color:var(--amber-border); } .alert.warning .ico{ color:var(--amber); }
.alert.destructive{ background:var(--red-bg); border-color:var(--red-border); } .alert.destructive .ico{ color:var(--red); }

@media (max-width:760px){ .stat-grid{ grid-template-columns:repeat(2,1fr); } }
"""


def inject_css() -> None:
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)


def hero(icon_name: str, title: str, subtitle: str, eyebrow: str = "") -> None:
    eb = (
        f'<div class="eyebrow">{icon("badge-check", 13)}<span>{eyebrow}</span></div>'
        if eyebrow else ""
    )
    st.markdown(
        f'<div class="hero">{eb}'
        f'<div class="title"><div class="logo">{icon(icon_name, 24)}</div>'
        f"<h1>{title}</h1></div><p>{subtitle}</p></div>",
        unsafe_allow_html=True,
    )


def section(icon_name: str, title: str, subtitle: str = "") -> None:
    sub = f'<div class="s">{subtitle}</div>' if subtitle else ""
    st.markdown(
        f'<div class="sec"><div class="ico">{icon(icon_name, 18)}</div>'
        f'<div><div class="t">{title}</div>{sub}</div></div>',
        unsafe_allow_html=True,
    )


def stat_cards(cards: List[dict]) -> None:
    """Render sebaris kartu statistik. Tiap kartu: {label, value, icon, sub?, accent?}."""
    items = ""
    for c in cards:
        accent = f' {c["accent"]}' if c.get("accent") else ""
        sub = f'<div class="sub">{c["sub"]}</div>' if c.get("sub") else ""
        items += (
            f'<div class="stat"><div class="lab"><span>{c["label"]}</span>'
            f'{icon(c["icon"], 16)}</div>'
            f'<div class="val{accent}">{c["value"]}</div>{sub}</div>'
        )
    st.markdown(f'<div class="stat-grid">{items}</div>', unsafe_allow_html=True)


def alert(kind: str, icon_name: str, title: str, desc: str = "") -> None:
    """kind: 'default' | 'success' | 'warning' | 'destructive' | 'info'."""
    cls = "" if kind in ("default", "info") else kind
    d = f'<div class="desc">{desc}</div>' if desc else ""
    st.markdown(
        f'<div class="alert {cls}"><div class="ico">{icon(icon_name, 18)}</div>'
        f'<div><div class="ttl">{title}</div>{d}</div></div>',
        unsafe_allow_html=True,
    )


def metric(icon_name: str, label: str, value: str, accent: str = "") -> None:
    """Satu kartu metrik (dipakai di dalam tab)."""
    a = f" {accent}" if accent else ""
    st.markdown(
        f'<div class="stat" style="display:inline-block;min-width:260px">'
        f'<div class="lab"><span>{label}</span>{icon(icon_name, 16)}</div>'
        f'<div class="val{a}">{value}</div></div>',
        unsafe_allow_html=True,
    )
