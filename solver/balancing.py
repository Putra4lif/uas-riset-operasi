"""Penyeimbangan masalah transportasi (balancing).

Metode Transportasi mensyaratkan total penawaran = total permintaan.
Bila tidak seimbang, kita tambahkan SUMBER atau TUJUAN semu (dummy) dengan
biaya 0 untuk menyerap kelebihan. Unit yang "dikirim" ke/dari dummy artinya
tidak benar-benar dikirim (mis. permintaan tak terpenuhi / kapasitas menganggur).
"""
from __future__ import annotations

from typing import Tuple

from .model import EPS, TransportationProblem


def balance(problem: TransportationProblem) -> Tuple[TransportationProblem, str]:
    """Kembalikan (masalah_seimbang, keterangan).

    - supply > demand  -> tambah TUJUAN dummy menyerap kelebihan kapasitas.
    - demand > supply  -> tambah SUMBER dummy menutup kekurangan pasokan.
    - sudah seimbang   -> kembalikan salinan apa adanya.
    """
    problem.validate()
    total_s = problem.total_supply()
    total_d = problem.total_demand()
    p = problem.copy()

    if abs(total_s - total_d) < EPS:
        return p, "Masalah sudah seimbang (total supply = total demand)."

    if total_s > total_d:
        gap = total_s - total_d
        p.destinations.append("Dummy")
        p.demand.append(gap)
        for i in range(p.m):
            p.cost[i].append(0.0)
        note = (
            f"Tidak seimbang: supply ({total_s:g}) > demand ({total_d:g}). "
            f"Ditambahkan TUJUAN dummy berpermintaan {gap:g} dengan biaya 0."
        )
    else:
        gap = total_d - total_s
        p.sources.append("Dummy")
        p.supply.append(gap)
        p.cost.append([0.0] * p.n)
        note = (
            f"Tidak seimbang: demand ({total_d:g}) > supply ({total_s:g}). "
            f"Ditambahkan SUMBER dummy berkapasitas {gap:g} dengan biaya 0."
        )

    return p, note
