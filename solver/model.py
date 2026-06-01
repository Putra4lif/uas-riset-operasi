"""Struktur data inti untuk masalah Metode Transportasi.

Modul ini HANYA berisi representasi data + util kecil, tanpa logika algoritma.
Dipakai bersama oleh balancing.py, initial.py, optimize.py, verify.py, dan app.py.

Konvensi indeks:
    i = indeks sumber (asal / pabrik)      0..m-1
    j = indeks tujuan (kota / gudang)      0..n-1
    cost[i][j] = biaya angkut per unit dari sumber i ke tujuan j
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

# Toleransi pembanding bilangan pecahan (menghindari galat floating point).
EPS = 1e-9

Cell = Tuple[int, int]  # (i, j)


@dataclass
class TransportationProblem:
    """Definisi sebuah masalah transportasi.

    Attributes:
        sources:      nama tiap sumber, mis. ["Surabaya", "Semarang", "Bandung"]
        destinations: nama tiap tujuan, mis. ["Jakarta", "Yogyakarta", ...]
        supply:       kapasitas tiap sumber (panjang = jumlah sumber)
        demand:       permintaan tiap tujuan (panjang = jumlah tujuan)
        cost:         matriks biaya cost[i][j] (m baris x n kolom)
    """

    sources: List[str]
    destinations: List[str]
    supply: List[float]
    demand: List[float]
    cost: List[List[float]]

    # -- ukuran -------------------------------------------------------------
    @property
    def m(self) -> int:
        """Jumlah sumber."""
        return len(self.sources)

    @property
    def n(self) -> int:
        """Jumlah tujuan."""
        return len(self.destinations)

    # -- keseimbangan -------------------------------------------------------
    def total_supply(self) -> float:
        return sum(self.supply)

    def total_demand(self) -> float:
        return sum(self.demand)

    def is_balanced(self) -> bool:
        """True jika total penawaran == total permintaan."""
        return abs(self.total_supply() - self.total_demand()) < EPS

    # -- validasi -----------------------------------------------------------
    def validate(self) -> None:
        """Pastikan dimensi konsisten & nilai masuk akal. Lempar ValueError bila salah."""
        if self.m == 0 or self.n == 0:
            raise ValueError("Minimal harus ada 1 sumber dan 1 tujuan.")
        if len(self.supply) != self.m:
            raise ValueError(
                f"Jumlah nilai supply ({len(self.supply)}) != jumlah sumber ({self.m})."
            )
        if len(self.demand) != self.n:
            raise ValueError(
                f"Jumlah nilai demand ({len(self.demand)}) != jumlah tujuan ({self.n})."
            )
        if len(self.cost) != self.m or any(len(row) != self.n for row in self.cost):
            raise ValueError(
                f"Matriks biaya harus berukuran {self.m} x {self.n}."
            )
        # Tolak nilai kosong/NaN/tak hingga LEBIH DULU: catatan penting -> nan < 0
        # bernilai False, jadi tanpa cek ini NaN akan lolos pengecekan negatif di bawah
        # dan menghasilkan biaya optimal "nan" atau crash di solver LP.
        if any(not math.isfinite(s) for s in self.supply) or any(not math.isfinite(d) for d in self.demand):
            raise ValueError("Supply dan demand harus berupa angka (tidak boleh kosong/NaN).")
        if any(not math.isfinite(c) for row in self.cost for c in row):
            raise ValueError("Biaya harus berupa angka (tidak boleh kosong/NaN).")
        if any(s < 0 for s in self.supply) or any(d < 0 for d in self.demand):
            raise ValueError("Supply dan demand tidak boleh negatif.")
        if any(c < 0 for row in self.cost for c in row):
            raise ValueError("Biaya tidak boleh negatif.")

    def copy(self) -> "TransportationProblem":
        return TransportationProblem(
            sources=list(self.sources),
            destinations=list(self.destinations),
            supply=list(self.supply),
            demand=list(self.demand),
            cost=[list(row) for row in self.cost],
        )


@dataclass
class Allocation:
    """Sebuah solusi (layak awal maupun optimal) beserta sel basisnya.

    alloc[i][j] = jumlah unit yang dikirim dari sumber i ke tujuan j.
    basic       = himpunan sel basis (i, j); pada solusi non-degenerate
                  jumlahnya tepat m + n - 1.
    """

    alloc: List[List[float]]
    basic: Set[Cell] = field(default_factory=set)

    def total_cost(self, problem: "TransportationProblem") -> float:
        """Hitung total biaya = sum(alloc[i][j] * cost[i][j])."""
        return sum(
            self.alloc[i][j] * problem.cost[i][j]
            for i in range(problem.m)
            for j in range(problem.n)
        )

    def copy(self) -> "Allocation":
        return Allocation(
            alloc=[list(row) for row in self.alloc],
            basic=set(self.basic),
        )


@dataclass
class Iteration:
    """Rekaman satu iterasi uji optimalitas (MODI / Stepping Stone).

    Dipakai untuk MENAMPILKAN langkah ke pengguna, bukan sekadar hasil akhir.
    """

    index: int                              # iterasi ke-berapa (1-based)
    alloc: List[List[float]]                # alokasi pada awal iterasi ini (disimpan
                                            # untuk debug/ekstensi; belum dirender di UI)
    u: List[Optional[float]]                # potensial baris u_i
    v: List[Optional[float]]                # potensial kolom v_j
    reduced: Dict[Cell, float]              # opportunity cost sel non-basis
    entering: Optional[Cell]                # sel masuk (paling negatif)
    loop: Optional[List[Cell]]             # lintasan tertutup (urut +,-,+,-,..)
    theta: Optional[float]                  # jumlah unit yang digeser
    leaving: Optional[Cell]                 # sel keluar dari basis
    total_cost: float                       # total biaya pada awal iterasi
    optimal: bool                           # True jika sudah optimal (semua reduced >= 0)


@dataclass
class Solution:
    """Hasil lengkap penyelesaian: solusi awal, langkah iterasi, dan solusi optimal."""

    problem: TransportationProblem          # masalah SETELAH diseimbangkan
    original: TransportationProblem         # masalah asli (sebelum dummy)
    balance_note: str                       # keterangan penyeimbangan
    initial_method: str                     # "NWC" | "Least Cost" | "VAM"
    initial: Allocation
    iterations: List[Iteration]
    optimal: Allocation
    optimal_reached: bool                   # False bila berhenti karena batas iterasi

    @property
    def initial_cost(self) -> float:
        return self.initial.total_cost(self.problem)

    @property
    def optimal_cost(self) -> float:
        return self.optimal.total_cost(self.problem)

    @property
    def savings(self) -> float:
        """Penghematan biaya dari solusi awal ke optimal."""
        return self.initial_cost - self.optimal_cost
