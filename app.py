"""Aplikasi web Metode Transportasi (Streamlit) — tampilan bergaya shadcn.

Menjalankan:
    pip install -r requirements.txt
    streamlit run app.py

Alur: input tabel interaktif (sumber, tujuan, biaya) -> solusi awal
(NWC / Least Cost / VAM) -> optimasi MODI/Stepping Stone -> langkah & solusi
optimal, diverifikasi otomatis dengan scipy. Seluruh ikon memakai Lucide (shadcn).
"""
from __future__ import annotations

import math
import os

import pandas as pd
import streamlit as st

import ui
from solver import load_case, solve, verify_with_scipy
from solver.model import TransportationProblem

HERE = os.path.dirname(os.path.abspath(__file__))
CONTOH = os.path.join(HERE, "cases", "semen.json")

st.set_page_config(page_title="Metode Transportasi", layout="wide")
ui.inject_css()


# --------------------------------------------------------------------------- #
# Util
# --------------------------------------------------------------------------- #
def fmt(x: float) -> str:
    """Format angka gaya Indonesia (titik ribuan). Kembalikan '—' bila kosong/NaN."""
    if not isinstance(x, (int, float)) or not math.isfinite(x):
        return "—"
    if abs(x - round(x)) < 1e-9:
        return f"{int(round(x)):,}".replace(",", ".")
    return f"{x:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


def to_num(x) -> float:
    """Konversi nilai sel tabel ke float. Sel kosong/teks -> NaN, ditolak oleh
    TransportationProblem.validate() dengan pesan ramah (bukan traceback)."""
    try:
        return float(x)
    except (TypeError, ValueError):
        return float("nan")


def muat_contoh() -> None:
    p = load_case(CONTOH)
    st.session_state.src_names = list(p.sources)
    st.session_state.src_supply = list(p.supply)
    st.session_state.dst_names = list(p.destinations)
    st.session_state.dst_demand = list(p.demand)
    st.session_state.cost = [list(r) for r in p.cost]


def init_state() -> None:
    if "src_names" not in st.session_state:
        muat_contoh()
        st.session_state.metode = "VAM"
        st.session_state.verifikasi = True


def unik(labels):
    seen, out = {}, []
    for x in labels:
        x = str(x) if x not in (None, "") else "?"
        if x in seen:
            seen[x] += 1
            out.append(f"{x} ({seen[x]})")
        else:
            seen[x] = 0
            out.append(x)
    return out


def _label_unik(base: str, dipakai) -> str:
    """Pilih label margin yang dijamin tak bentrok dengan nama sumber/tujuan pengguna.

    Mencegah bug: jika pengguna menamai tujuan "Kapasitas" atau sumber "Permintaan",
    label margin tidak boleh menimpa kolom/baris data tersebut.
    """
    label = base
    while label in dipakai:
        label += " "  # tambah spasi hingga unik
    return label


def resize_cost(m: int, n: int) -> None:
    cost = st.session_state.cost
    new = [[0.0] * n for _ in range(m)]
    for i in range(min(m, len(cost))):
        for j in range(min(n, len(cost[i]))):
            new[i][j] = cost[i][j]
    st.session_state.cost = new


# --------------------------------------------------------------------------- #
# Render tabel
# --------------------------------------------------------------------------- #
def tabel_alokasi(problem: TransportationProblem, alloc, judul: str):
    src = unik(problem.sources)
    dst = unik(problem.destinations)
    # Label margin dibuat unik agar tak menimpa kolom/baris data bila pengguna
    # kebetulan menamai tujuan "Kapasitas" atau sumber "Permintaan".
    cap = _label_unik("Kapasitas", set(dst))
    dem = _label_unik("Permintaan", set(src))

    data = pd.DataFrame(
        [[alloc.alloc[i][j] for j in range(problem.n)] for i in range(problem.m)],
        index=src, columns=dst,
    )
    data[cap] = list(problem.supply)  # cap dijamin kolom baru (tak bentrok)
    margin = pd.DataFrame(
        [list(problem.demand) + [problem.total_demand()]],
        index=[dem], columns=list(dst) + [cap],
    )
    df = pd.concat([data, margin])  # gabung berdasar posisi, bukan label

    def sorot(val):
        return (
            "background-color:#dcfce7;color:#166534;font-weight:600"
            if isinstance(val, (int, float)) and val > 1e-9 else ""
        )

    st.caption(judul)
    # subset sudah mengecualikan baris/kolom margin (yang terakhir), jadi cukup sorot semua.
    sty = df.style.apply(
        lambda col: [sorot(v) for v in col],
        axis=0, subset=(df.index[:-1], df.columns[:-1]),
    ).format("{:g}")
    st.dataframe(sty, width="stretch")


def tabel_biaya_rute(problem: TransportationProblem, alloc):
    baris = []
    for i in range(problem.m):
        for j in range(problem.n):
            q = alloc.alloc[i][j]
            if q > 1e-9:
                baris.append({
                    "Rute": f"{problem.sources[i]} → {problem.destinations[j]}",
                    "Jumlah": q,
                    "Biaya/unit": problem.cost[i][j],
                    "Subtotal": q * problem.cost[i][j],
                })
    df = pd.DataFrame(baris)
    st.dataframe(
        df.style.format({"Jumlah": "{:g}", "Biaya/unit": "{:g}", "Subtotal": "{:g}"}),
        width="stretch", hide_index=True,
    )


def tampilkan_iterasi(problem: TransportationProblem, it):
    src = unik(problem.sources)
    dst = unik(problem.destinations)
    grid = []
    for i in range(problem.m):
        row = []
        for j in range(problem.n):
            row.append(f"{it.reduced[(i, j)]:+g}" if (i, j) in it.reduced else "basis")
        grid.append(row)
    df = pd.DataFrame(grid, index=src, columns=dst)
    st.caption("Opportunity cost cᵢⱼ − (uᵢ + vⱼ) untuk sel kosong (negatif = bisa diperbaiki):")
    st.dataframe(df, width="stretch")

    u_str = ", ".join(f"u{i+1}={'-' if it.u[i] is None else f'{it.u[i]:g}'}" for i in range(problem.m))
    v_str = ", ".join(f"v{j+1}={'-' if it.v[j] is None else f'{it.v[j]:g}'}" for j in range(problem.n))
    st.caption(f"Potensial: {u_str}  |  {v_str}")

    if it.entering is not None:
        ei, ej = it.entering
        li, lj = it.leaving
        lintasan = " → ".join(
            f"({problem.sources[a]}, {problem.destinations[b]})" for a, b in it.loop
        )
        st.markdown(
            f"- **Sel masuk:** ({problem.sources[ei]}, {problem.destinations[ej]}) "
            f"— opportunity cost {it.reduced[it.entering]:+g}\n"
            f"- **Lintasan tertutup (+, −, +, − …):** {lintasan}\n"
            f"- **θ (unit digeser):** {it.theta:g} — **sel keluar:** "
            f"({problem.sources[li]}, {problem.destinations[lj]})"
        )


# --------------------------------------------------------------------------- #
# Halaman
# --------------------------------------------------------------------------- #
init_state()

ui.hero(
    "truck",
    "Metode Transportasi",
    "Optimasi biaya distribusi: solusi awal NWC / Least Cost / VAM, dioptimalkan "
    "dengan MODI + Stepping Stone, lalu diverifikasi dengan solver LP scipy.",
    eyebrow="Riset Operasi",
)

with st.sidebar:
    ui.section("settings", "Pengaturan")
    st.session_state.metode = st.selectbox(
        "Metode solusi awal", ["NWC", "Least Cost", "VAM"],
        index=["NWC", "Least Cost", "VAM"].index(st.session_state.get("metode", "VAM")),
    )
    st.session_state.verifikasi = st.checkbox(
        "Verifikasi dengan scipy", value=st.session_state.get("verifikasi", True)
    )
    if st.button("Muat contoh PT Sentosa Beton", width="stretch"):
        muat_contoh()
        st.rerun()
    st.caption(
        "Ubah / tambah baris pada tabel Sumber & Tujuan, isi biaya angkut, "
        "lalu tekan Hitung Solusi Optimal."
    )

ui.section("package", "Sumber (asal) & kapasitas", "Langkah 1 — daftar pabrik/gudang dan kapasitasnya")
src_df = st.data_editor(
    pd.DataFrame({"Sumber": st.session_state.src_names, "Kapasitas": st.session_state.src_supply}),
    num_rows="dynamic", width="stretch", key="ed_src",
)
src_df = src_df.dropna(how="all")
src_names = [str(x) for x in src_df["Sumber"].fillna("").tolist()]
src_supply = [to_num(x) for x in src_df["Kapasitas"].tolist()]

ui.section("map-pin", "Tujuan & permintaan", "Langkah 2 — daftar kota/wilayah dan permintaannya")
dst_df = st.data_editor(
    pd.DataFrame({"Tujuan": st.session_state.dst_names, "Permintaan": st.session_state.dst_demand}),
    num_rows="dynamic", width="stretch", key="ed_dst",
)
dst_df = dst_df.dropna(how="all")
dst_names = [str(x) for x in dst_df["Tujuan"].fillna("").tolist()]
dst_demand = [to_num(x) for x in dst_df["Permintaan"].tolist()]

st.session_state.src_names, st.session_state.src_supply = src_names, src_supply
st.session_state.dst_names, st.session_state.dst_demand = dst_names, dst_demand
m, n = len(src_names), len(dst_names)
resize_cost(m, n)

ui.section("grid", "Biaya angkut per unit", "Langkah 3 — biaya dari tiap sumber ke tiap tujuan")
cost_df = pd.DataFrame(st.session_state.cost, index=unik(src_names), columns=unik(dst_names))
cost_edit = st.data_editor(cost_df, width="stretch", key="ed_cost")
st.session_state.cost = [[to_num(c) for c in row] for row in cost_edit.values.tolist()]

total_s, total_d = sum(src_supply), sum(dst_demand)
ui.stat_cards([
    {"label": "Total kapasitas", "value": fmt(total_s), "icon": "layers", "sub": "Penawaran (supply)"},
    {"label": "Total permintaan", "value": fmt(total_d), "icon": "package", "sub": "Permintaan (demand)"},
])
if abs(total_s - total_d) > 1e-9:
    ui.alert("info", "info", "Tidak seimbang",
             "Program akan menambahkan baris/kolom dummy (biaya 0) secara otomatis.")

st.write("")
if st.button("Hitung Solusi Optimal", type="primary", width="stretch"):
    try:
        problem = TransportationProblem(
            sources=src_names, destinations=dst_names,
            supply=src_supply, demand=dst_demand,
            cost=[[float(c) for c in row] for row in st.session_state.cost],
        )
        problem.validate()
        sol = solve(problem, method=st.session_state.metode)
    except Exception as e:  # noqa: BLE001
        ui.alert("destructive", "triangle-alert", "Input belum valid", str(e))
        st.stop()

    st.divider()
    ui.alert("info", "info", "Penyeimbangan", sol.balance_note)

    n_iter = len([it for it in sol.iterations if not it.optimal])
    ui.stat_cards([
        {"label": "Biaya optimal", "value": fmt(sol.optimal_cost), "icon": "money", "sub": "Total minimum"},
        {"label": "Biaya solusi awal", "value": fmt(sol.initial_cost), "icon": "calculator",
         "sub": sol.initial_method},
        {"label": "Penghematan", "value": fmt(sol.savings), "icon": "trending-down",
         "accent": "green" if sol.savings > 1e-9 else "", "sub": "Awal → optimal"},
        {"label": "Jumlah iterasi", "value": str(n_iter), "icon": "repeat", "sub": "MODI"},
    ])

    if st.session_state.verifikasi:
        ref = verify_with_scipy(sol.problem)
        if not ref["available"]:
            ui.alert("warning", "triangle-alert", "Verifikasi dilewati", ref["message"])
        elif ref["success"] and abs(ref["cost"] - sol.optimal_cost) < 1e-4:
            ui.alert("success", "badge-check", "Terverifikasi",
                     f"Hasil cocok dengan solver LP scipy (biaya = {fmt(ref['cost'])}).")
        else:
            ui.alert("destructive", "triangle-alert", "Tidak cocok dengan scipy",
                     f"scipy = {ref['cost']}. Periksa kembali implementasi.")

    tab1, tab2, tab3 = st.tabs(
        [f"Solusi Awal ({sol.initial_method})", "Langkah Optimasi (MODI)", "Solusi Optimal"]
    )
    with tab1:
        tabel_alokasi(sol.problem, sol.initial, f"Alokasi awal — {sol.initial_method}")
        ui.metric("calculator", "Total biaya solusi awal", fmt(sol.initial_cost))
    with tab2:
        langkah = [it for it in sol.iterations if not it.optimal]
        if not langkah:
            ui.alert("success", "circle-check", "Solusi awal sudah optimal",
                     "Tidak diperlukan iterasi perbaikan.")
        for it in langkah:
            with st.expander(f"Iterasi {it.index} — biaya saat ini: {fmt(it.total_cost)}"):
                tampilkan_iterasi(sol.problem, it)
        if langkah and sol.optimal_reached:
            ui.alert("success", "circle-check", "Optimal tercapai",
                     "Semua opportunity cost ≥ 0.")
    with tab3:
        tabel_alokasi(sol.problem, sol.optimal, "Alokasi optimal")
        tabel_biaya_rute(sol.problem, sol.optimal)
        ui.metric("money", "Total biaya minimum", fmt(sol.optimal_cost), accent="green")
