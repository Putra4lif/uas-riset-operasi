"""Uji optimalitas & iterasi perbaikan (Pertemuan 8).

Menggunakan metode MODI (Modified Distribution) untuk menghitung opportunity
cost tiap sel kosong secara matematis, dan lintasan tertutup (closed loop) ala
Stepping Stone untuk memindahkan alokasi pada tiap iterasi.

Ide kunci: sel-sel basis (m+n-1 buah) membentuk POHON RENTANG (spanning tree)
pada graf bipartit baris-kolom. Karena itu:
  - potensial u_i, v_j bisa dihitung dengan propagasi dari u_0 = 0;
  - menambahkan satu sel kosong menciptakan TEPAT SATU lintasan tertutup, yaitu
    lintasan unik di pohon antara simpul-baris dan simpul-kolomnya.
"""
from __future__ import annotations

from collections import deque
from typing import List, Optional, Set, Tuple

from .model import EPS, Allocation, Cell, Iteration, TransportationProblem


def repair_degeneracy(problem: TransportationProblem, allocation: Allocation) -> None:
    """Tambahkan sel basis beralokasi 0 hingga jumlahnya = m+n-1 (in place).

    Sel yang ditambahkan dipilih agar TIDAK membentuk siklus (memakai union-find),
    sehingga himpunan basis tetap berupa pohon rentang yang valid untuk MODI.
    Sel berbiaya terendah diprioritaskan.
    """
    m, n = problem.m, problem.n
    parent = list(range(m + n))  # simpul baris 0..m-1, simpul kolom m..m+n-1

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> bool:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
            return True
        return False

    for (i, j) in allocation.basic:
        union(i, m + j)

    need = m + n - 1
    if len(allocation.basic) >= need:
        return

    candidates = sorted(
        (problem.cost[i][j], i, j)
        for i in range(m)
        for j in range(n)
        if (i, j) not in allocation.basic
    )
    for _cost, i, j in candidates:
        if len(allocation.basic) >= need:
            break
        if union(i, m + j):  # hanya jika menghubungkan dua komponen (tak buat siklus)
            allocation.basic.add((i, j))  # alokasi tetap 0


def compute_potentials(
    problem: TransportationProblem, basic: Set[Cell]
) -> Tuple[List[Optional[float]], List[Optional[float]]]:
    """Hitung potensial u_i dan v_j dari syarat u_i + v_j = c_ij pada sel basis.

    Ditetapkan u_0 = 0, sisanya disebar via BFS pada pohon basis.
    """
    m, n = problem.m, problem.n
    u: List[Optional[float]] = [None] * m
    v: List[Optional[float]] = [None] * n

    row_cells = {i: [] for i in range(m)}
    col_cells = {j: [] for j in range(n)}
    for (i, j) in basic:
        row_cells[i].append(j)
        col_cells[j].append(i)

    u[0] = 0.0
    queue = deque([("R", 0)])
    while queue:
        kind, idx = queue.popleft()
        if kind == "R":
            i = idx
            for j in row_cells[i]:
                if v[j] is None:
                    v[j] = problem.cost[i][j] - u[i]
                    queue.append(("C", j))
        else:
            j = idx
            for i in col_cells[j]:
                if u[i] is None:
                    u[i] = problem.cost[i][j] - v[j]
                    queue.append(("R", i))
    return u, v


def find_loop(basic: Set[Cell], entering: Cell, m: int, n: int) -> Optional[List[Cell]]:
    """Cari lintasan tertutup untuk sel masuk `entering`.

    Mengembalikan daftar sel TERURUT dimulai dari `entering`, dengan tanda
    bergantian +, -, +, - ... (indeks genap = +, indeks ganjil = -).
    Caranya: telusuri lintasan unik di pohon basis antara simpul-baris r dan
    simpul-kolom c dari sel masuk (r, c); gabung dengan sel masuk -> siklus.
    """
    r, c = entering
    adj = {}  # simpul -> list (tetangga, sel)

    def add_edge(a, b, cell):
        adj.setdefault(a, []).append((b, cell))

    for (i, j) in basic:
        add_edge(("R", i), ("C", j), (i, j))
        add_edge(("C", j), ("R", i), (i, j))

    start, goal = ("R", r), ("C", c)
    prev = {start: (None, None)}  # simpul -> (induk, sel_penghubung)
    queue = deque([start])
    while queue:
        node = queue.popleft()
        if node == goal:
            break
        for nb, cell in adj.get(node, []):
            if nb not in prev:
                prev[nb] = (node, cell)
                queue.append(nb)

    if goal not in prev:
        return None  # tak ada lintasan (mestinya mustahil pada pohon rentang)

    path_cells = []
    node = goal
    while node != start:
        parent_node, cell = prev[node]
        path_cells.append(cell)
        node = parent_node

    return [entering] + path_cells


def optimize(
    problem: TransportationProblem,
    initial: Allocation,
    max_iter: int = 1000,
) -> Tuple[List[Iteration], Allocation, bool]:
    """Iterasikan dari solusi awal sampai optimal memakai MODI + Stepping Stone.

    Mengembalikan (daftar_iterasi, alokasi_optimal, tercapai_optimal).
    Setiap entri `daftar_iterasi` merekam keadaan SEBELUM perubahan agar
    langkah-langkahnya bisa ditampilkan ke pengguna.
    """
    alloc = initial.copy()
    repair_degeneracy(problem, alloc)
    m, n = problem.m, problem.n
    iterations: List[Iteration] = []

    for step in range(1, max_iter + 1):
        u, v = compute_potentials(problem, alloc.basic)

        reduced = {}
        for i in range(m):
            for j in range(n):
                if (i, j) in alloc.basic:
                    continue
                # Guard defensif: pada basis yang sudah ditambal (pohon rentang
                # penuh, m+n-1 sel), semua u/v pasti terdefinisi -> cabang ini
                # tak terjangkau di jalur normal, hanya jaga-jaga.
                if u[i] is None or v[j] is None:
                    continue
                reduced[(i, j)] = problem.cost[i][j] - u[i] - v[j]

        improving = [(val, cell) for cell, val in reduced.items() if val < -EPS]
        total = alloc.total_cost(problem)

        if not improving:
            iterations.append(Iteration(
                index=step, alloc=[list(row) for row in alloc.alloc],
                u=list(u), v=list(v), reduced=dict(reduced),
                entering=None, loop=None, theta=None, leaving=None,
                total_cost=total, optimal=True,
            ))
            return iterations, alloc, True

        # Sel masuk = opportunity cost paling negatif (tie-break: indeks terkecil).
        _, entering = min(improving)
        loop = find_loop(alloc.basic, entering, m, n)
        if loop is None:
            # Pengaman: tak seharusnya terjadi; hentikan sebagai belum-optimal.
            return iterations, alloc, False

        minus_cells = [loop[k] for k in range(1, len(loop), 2)]
        theta = min(alloc.alloc[i][j] for (i, j) in minus_cells)
        # Sel keluar = sel bertanda minus dengan alokasi terkecil (tie-break: indeks).
        leaving = min(
            (cell for cell in minus_cells if abs(alloc.alloc[cell[0]][cell[1]] - theta) < EPS)
        )

        iterations.append(Iteration(
            index=step, alloc=[list(row) for row in alloc.alloc],
            u=list(u), v=list(v), reduced=dict(reduced),
            entering=entering, loop=list(loop), theta=theta, leaving=leaving,
            total_cost=total, optimal=False,
        ))

        # Geser theta sepanjang lintasan: + pada genap, - pada ganjil.
        for k, (i, j) in enumerate(loop):
            if k % 2 == 0:
                alloc.alloc[i][j] += theta
            else:
                alloc.alloc[i][j] -= theta

        alloc.basic.add(entering)
        alloc.basic.discard(leaving)

    return iterations, alloc, False
