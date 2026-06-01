"""Paket solver Metode Transportasi.

API utama:
    solve(problem, method)      -> Solution   (alur lengkap awal -> optimal)
    load_case(path)             -> TransportationProblem
    METHODS                     -> dict nama metode solusi awal

Contoh:
    from solver import solve, load_case
    prob = load_case("cases/semen.json")
    sol = solve(prob, method="VAM")
    print(sol.optimal_cost)
"""
from __future__ import annotations

import json

from .balancing import balance
from .initial import METHODS
from .model import Allocation, Iteration, Solution, TransportationProblem
from .optimize import optimize
from .verify import verify_with_scipy

__all__ = [
    "solve",
    "load_case",
    "METHODS",
    "TransportationProblem",
    "Allocation",
    "Iteration",
    "Solution",
    "verify_with_scipy",
]


def solve(
    problem: TransportationProblem,
    method: str = "VAM",
    max_iter: int = 1000,
) -> Solution:
    """Selesaikan masalah transportasi secara lengkap.

    Langkah: seimbangkan -> solusi awal (sesuai `method`) -> MODI sampai optimal.
    `method` harus salah satu kunci di METHODS ("NWC", "Least Cost", "VAM").
    """
    if method not in METHODS:
        raise ValueError(f"Metode '{method}' tidak dikenal. Pilihan: {list(METHODS)}")

    balanced, note = balance(problem)
    initial = METHODS[method](balanced)
    iterations, optimal_alloc, reached = optimize(balanced, initial, max_iter)

    return Solution(
        problem=balanced,
        original=problem,
        balance_note=note,
        initial_method=method,
        initial=initial,
        iterations=iterations,
        optimal=optimal_alloc,
        optimal_reached=reached,
    )


def load_case(path: str) -> TransportationProblem:
    """Muat studi kasus dari berkas JSON.

    Format JSON:
        {
          "sources": ["Surabaya", ...],
          "destinations": ["Jakarta", ...],
          "supply": [300, ...],
          "demand": [250, ...],
          "cost": [[8, 6, 10, 9], ...]
        }
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    problem = TransportationProblem(
        sources=data["sources"],
        destinations=data["destinations"],
        supply=[float(x) for x in data["supply"]],
        demand=[float(x) for x in data["demand"]],
        cost=[[float(x) for x in row] for row in data["cost"]],
    )
    problem.validate()
    return problem
