"""Verifikasi kebenaran solusi memakai pemrograman linier (scipy).

Masalah transportasi adalah kasus khusus Linear Programming. Kita selesaikan
ulang dengan solver LP tepercaya (`scipy.optimize.linprog`, metode HiGHS) lalu
bandingkan biaya optimalnya dengan hasil algoritma manual kita. Jika cocok,
kita yakin implementasi MODI/Stepping Stone sudah benar.

scipy bersifat OPSIONAL: bila tidak terpasang, fungsi mengembalikan status
"tidak tersedia" tanpa membuat program gagal.
"""
from __future__ import annotations

from typing import Dict

from .model import TransportationProblem


def verify_with_scipy(problem: TransportationProblem) -> Dict:
    """Selesaikan masalah (yang sudah seimbang) sebagai LP dan kembalikan ringkasannya.

    Return dict berisi:
        available : bool  -> scipy terpasang atau tidak
        success   : bool  -> LP berhasil diselesaikan
        cost      : float -> biaya optimal menurut LP (None bila gagal)
        message   : str
    """
    try:
        from scipy.optimize import linprog
    except ImportError:
        return {
            "available": False,
            "success": False,
            "cost": None,
            "message": "scipy tidak terpasang (pip install scipy) — verifikasi dilewati.",
        }

    m, n = problem.m, problem.n
    c = [problem.cost[i][j] for i in range(m) for j in range(n)]

    A_eq, b_eq = [], []
    for i in range(m):  # tiap sumber: total keluar = supply
        row = [0.0] * (m * n)
        for j in range(n):
            row[i * n + j] = 1.0
        A_eq.append(row)
        b_eq.append(problem.supply[i])
    for j in range(n):  # tiap tujuan: total masuk = demand
        row = [0.0] * (m * n)
        for i in range(m):
            row[i * n + j] = 1.0
        A_eq.append(row)
        b_eq.append(problem.demand[j])

    res = linprog(c, A_eq=A_eq, b_eq=b_eq, bounds=(0, None), method="highs")
    return {
        "available": True,
        "success": bool(res.success),
        "cost": float(res.fun) if res.success else None,
        "message": res.message,
    }
