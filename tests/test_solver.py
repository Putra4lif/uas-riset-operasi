"""Uji kebenaran solver Metode Transportasi.

Menjalankan: dari folder UAS,  python -m pytest -v
atau tanpa pytest:               python tests/test_solver.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from solver import METHODS, load_case, solve, verify_with_scipy
from solver.balancing import balance
from solver.initial import least_cost
from solver.model import TransportationProblem

TOL = 1e-6

# Contoh persis dari materi Pertemuan 8 (3 sumber x 3 tujuan).
# Solusi Least Cost di materi: X1B=25, X1C=125, X2C=175, X3A=200, X3B=75, Z=4550.
MATERI = TransportationProblem(
    sources=["S1", "S2", "S3"],
    destinations=["A", "B", "C"],
    supply=[150, 175, 275],
    demand=[200, 100, 300],
    cost=[
        [6, 8, 10],
        [7, 11, 11],
        [4, 5, 12],
    ],
)


def _feasible(problem, alloc):
    """Cek alokasi memenuhi semua kendala supply & demand dan tak negatif."""
    m, n = problem.m, problem.n
    for i in range(m):
        assert abs(sum(alloc.alloc[i]) - problem.supply[i]) < TOL, f"supply baris {i}"
    for j in range(n):
        col = sum(alloc.alloc[i][j] for i in range(m))
        assert abs(col - problem.demand[j]) < TOL, f"demand kolom {j}"
    assert all(alloc.alloc[i][j] >= -TOL for i in range(m) for j in range(n))


def test_least_cost_materi_sama_dengan_4550():
    """Solusi awal Least Cost pada contoh materi harus tepat Z = 4550."""
    balanced, _ = balance(MATERI)
    a = least_cost(balanced)
    assert abs(a.total_cost(balanced) - 4550) < TOL


def test_materi_optimal_cocok_scipy():
    """Hasil optimal kita harus sama dengan solver LP scipy (dan <= solusi awal)."""
    sol = solve(MATERI, method="Least Cost")
    ref = verify_with_scipy(sol.problem)
    assert sol.optimal_reached
    assert sol.optimal_cost <= sol.initial_cost + TOL
    if ref["available"]:
        assert abs(sol.optimal_cost - ref["cost"]) < 1e-4


def test_semua_metode_awal_konvergen_ke_optimum_sama():
    """NWC, Least Cost, dan VAM harus mencapai biaya optimal yang sama."""
    hasil = {m: solve(MATERI, method=m).optimal_cost for m in METHODS}
    nilai = list(hasil.values())
    for v in nilai:
        assert abs(v - nilai[0]) < 1e-4, f"metode tak konvergen sama: {hasil}"


def test_basis_optimal_berukuran_m_plus_n_minus_1():
    """Basis optimal harus berukuran m+n-1 (tidak degenerate setelah ditambal)."""
    sol = solve(MATERI, method="NWC")
    assert len(sol.optimal.basic) == sol.problem.m + sol.problem.n - 1
    _feasible(sol.problem, sol.optimal)


def test_studi_kasus_semen_cocok_scipy():
    """Studi kasus utama (3x4) harus optimal dan cocok dengan scipy."""
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cases", "semen.json")
    prob = load_case(path)
    sol = solve(prob, method="VAM")
    ref = verify_with_scipy(sol.problem)
    assert sol.optimal_reached
    _feasible(sol.problem, sol.optimal)
    if ref["available"]:
        assert abs(sol.optimal_cost - ref["cost"]) < 1e-4


def test_unbalanced_ditambah_dummy_dan_benar():
    """Masalah timpang harus diseimbangkan otomatis lalu cocok dengan scipy."""
    prob = TransportationProblem(
        sources=["P1", "P2"],
        destinations=["K1", "K2"],
        supply=[100, 80],          # total 180
        demand=[90, 60],           # total 150  -> supply > demand, butuh tujuan dummy
        cost=[[4, 8], [6, 5]],
    )
    sol = solve(prob, method="Least Cost")
    assert sol.problem.n == 3  # ada kolom Dummy
    assert "Dummy" in sol.problem.destinations
    _feasible(sol.problem, sol.optimal)
    ref = verify_with_scipy(sol.problem)
    if ref["available"]:
        assert abs(sol.optimal_cost - ref["cost"]) < 1e-4


def test_demand_lebih_besar_tambah_sumber_dummy():
    """Bila demand > supply, harus ditambah SUMBER dummy."""
    prob = TransportationProblem(
        sources=["P1", "P2"],
        destinations=["K1", "K2"],
        supply=[60, 50],           # total 110
        demand=[90, 70],           # total 160 -> demand > supply, butuh sumber dummy
        cost=[[3, 7], [5, 4]],
    )
    sol = solve(prob, method="VAM")
    assert sol.problem.m == 3
    assert "Dummy" in sol.problem.sources
    _feasible(sol.problem, sol.optimal)
    ref = verify_with_scipy(sol.problem)
    if ref["available"]:
        assert abs(sol.optimal_cost - ref["cost"]) < 1e-4


def test_fuzz_acak_selalu_cocok_scipy():
    """Uji fuzz: ratusan masalah acak harus SELALU menghasilkan optimum = scipy.

    Mencakup ukuran beragam, kasus seimbang & timpang, dan kasus rawan degeneracy.
    """
    import random

    ref0 = verify_with_scipy(TransportationProblem(["a"], ["b"], [1], [1], [[1]]))
    if not ref0["available"]:
        return  # scipy tak ada -> lewati

    rng = random.Random(12345)
    n_kasus = 300
    for kasus in range(n_kasus):
        m = rng.randint(1, 5)
        n = rng.randint(1, 5)
        supply = [rng.randint(0, 30) for _ in range(m)]
        demand = [rng.randint(0, 30) for _ in range(n)]
        # sebagian kasus sengaja dibuat seimbang agar rawan degeneracy
        if rng.random() < 0.5 and sum(supply) > 0:
            # paksa seimbang: skala demand agar totalnya sama
            ds = sum(demand)
            if ds == 0:
                demand[rng.randrange(n)] = sum(supply)
            else:
                # set demand terakhir agar total cocok bila memungkinkan
                diff = sum(supply) - sum(demand)
                demand[-1] = max(0, demand[-1] + diff)
        cost = [[rng.randint(1, 20) for _ in range(n)] for _ in range(m)]
        if sum(supply) == 0 or sum(demand) == 0:
            continue

        prob = TransportationProblem(
            sources=[f"S{i}" for i in range(m)],
            destinations=[f"D{j}" for j in range(n)],
            supply=supply, demand=demand, cost=cost,
        )
        method = rng.choice(list(METHODS))
        sol = solve(prob, method=method)
        ref = verify_with_scipy(sol.problem)
        assert sol.optimal_reached, f"kasus {kasus}: tak konvergen ({method})"
        _feasible(sol.problem, sol.optimal)
        assert abs(sol.optimal_cost - ref["cost"]) < 1e-4, (
            f"kasus {kasus} ({method}): kita={sol.optimal_cost} scipy={ref['cost']} "
            f"supply={supply} demand={demand} cost={cost}"
        )


if __name__ == "__main__":
    # Mode tanpa pytest: jalankan semua fungsi test_* dan laporkan.
    funcs = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    gagal = 0
    for fn in funcs:
        try:
            fn()
            print(f"[ OK ] {fn.__name__}")
        except AssertionError as e:
            gagal += 1
            print(f"[GAGAL] {fn.__name__}: {e}")
        except Exception as e:  # noqa: BLE001
            gagal += 1
            print(f"[ERROR] {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(funcs) - gagal}/{len(funcs)} test lulus.")
    sys.exit(1 if gagal else 0)
