"""Metode menentukan SOLUSI LAYAK AWAL (Pertemuan 6).

Tiga metode klasik, semuanya menghasilkan alokasi layak dengan total supply
terkirim = total demand terpenuhi (pada masalah yang sudah seimbang):

    - north_west_corner : mulai dari pojok kiri-atas (paling sederhana).
    - least_cost        : alokasi ke sel berbiaya terkecil lebih dulu.
    - vam               : Vogel's Approximation Method (berbasis penalti),
                          biasanya paling dekat ke optimal.

Catatan: sebagian metode bisa menghasilkan sel basis < m+n-1 (degenerate).
Penambalan degeneracy dilakukan terpisah di optimize.repair_degeneracy().
"""
from __future__ import annotations

from .model import EPS, Allocation, TransportationProblem


def _empty(problem: TransportationProblem):
    """Siapkan matriks alokasi nol + salinan supply/demand yang bisa dikurangi."""
    alloc = [[0.0] * problem.n for _ in range(problem.m)]
    return alloc, list(problem.supply), list(problem.demand)


def north_west_corner(problem: TransportationProblem) -> Allocation:
    """Metode Pojok Barat-Laut (North-West Corner Rule)."""
    alloc, supply, demand = _empty(problem)
    basic = set()
    i = j = 0
    while i < problem.m and j < problem.n:
        q = min(supply[i], demand[j])
        alloc[i][j] = q
        basic.add((i, j))
        supply[i] -= q
        demand[j] -= q

        s_done = supply[i] < EPS
        d_done = demand[j] < EPS
        if s_done and d_done:
            # Keduanya habis: maju satu arah; sel 0 berikutnya menjadi basis degenerate.
            if j < problem.n - 1:
                j += 1
            else:
                i += 1
        elif s_done:
            i += 1
        else:
            j += 1
    return Allocation(alloc, basic)


def _allocate(alloc, basic, supply, demand, i, j, active_rows, active_cols):
    """Alokasikan sebanyak mungkin ke sel (i, j) lalu nonaktifkan baris/kolom yang habis.

    Saat baris DAN kolom sama-sama habis, hanya satu yang dinonaktifkan supaya
    tidak kehilangan terlalu banyak sel basis (degeneracy ditambal kemudian).
    """
    q = min(supply[i], demand[j])
    alloc[i][j] = q
    basic.add((i, j))
    supply[i] -= q
    demand[j] -= q
    if supply[i] < EPS and demand[j] < EPS:
        if len(active_cols) > 1:
            active_cols.discard(j)
        else:
            active_rows.discard(i)
    elif supply[i] < EPS:
        active_rows.discard(i)
    else:
        active_cols.discard(j)


def least_cost(problem: TransportationProblem) -> Allocation:
    """Metode Biaya Sel Minimum (Least Cost / Minimum Cell Cost)."""
    alloc, supply, demand = _empty(problem)
    basic = set()
    active_rows = set(range(problem.m))
    active_cols = set(range(problem.n))

    while active_rows and active_cols:
        # Cari sel aktif berbiaya terkecil (tie-break: indeks terkecil agar deterministik).
        best = None
        best_cost = None
        for i in sorted(active_rows):
            for j in sorted(active_cols):
                c = problem.cost[i][j]
                if best_cost is None or c < best_cost - EPS:
                    best_cost = c
                    best = (i, j)
        i, j = best
        _allocate(alloc, basic, supply, demand, i, j, active_rows, active_cols)
    return Allocation(alloc, basic)


def vam(problem: TransportationProblem) -> Allocation:
    """Vogel's Approximation Method (metode penalti)."""
    alloc, supply, demand = _empty(problem)
    basic = set()
    active_rows = set(range(problem.m))
    active_cols = set(range(problem.n))

    while active_rows and active_cols:
        candidates = []  # (penalti, is_col, indeks)

        # Penalti = selisih dua biaya terkecil pada baris/kolom. Bila hanya tersisa
        # SATU sel aktif (len < 2), tidak ada selisih -> pakai biaya itu sendiri.
        for i in sorted(active_rows):
            costs = sorted(problem.cost[i][j] for j in active_cols)
            penalty = costs[1] - costs[0] if len(costs) >= 2 else costs[0]
            candidates.append((penalty, False, i))
        for j in sorted(active_cols):
            costs = sorted(problem.cost[i][j] for i in active_rows)
            penalty = costs[1] - costs[0] if len(costs) >= 2 else costs[0]
            candidates.append((penalty, True, j))

        # Penalti terbesar; tie-break: baris dulu, lalu indeks terkecil.
        penalty, is_col, idx = max(candidates, key=lambda t: (t[0], not t[1], -t[2]))

        if is_col:
            j = idx
            i = min(sorted(active_rows), key=lambda ii: problem.cost[ii][j])
        else:
            i = idx
            j = min(sorted(active_cols), key=lambda jj: problem.cost[i][jj])

        _allocate(alloc, basic, supply, demand, i, j, active_rows, active_cols)
    return Allocation(alloc, basic)


# Pemetaan nama -> fungsi, dipakai oleh UI dan solver.solve().
METHODS = {
    "NWC": north_west_corner,
    "Least Cost": least_cost,
    "VAM": vam,
}
