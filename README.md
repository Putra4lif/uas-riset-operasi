# Implementasi Metode Transportasi — Optimasi Biaya Distribusi

**Mata Kuliah:** Riset Operasi · **Kelas:** VIC · **Kelompok 3** (5 anggota)

> Aplikasi web (Streamlit + Python) yang menyelesaikan masalah **Metode Transportasi**:
> menentukan **solusi layak awal** (NWC / Least Cost / VAM), lalu **mengoptimalkan**
> dengan **MODI + Stepping Stone** hingga total biaya distribusi minimum.
> Hasil **diverifikasi otomatis** dengan solver Linear Programming `scipy`.

---

## 1. Tentang Metode Transportasi

**Metode Transportasi** adalah kasus khusus *Linear Programming* (LP) untuk
mengalokasikan pasokan dari beberapa **sumber** (pabrik/gudang) ke beberapa
**tujuan** (kota/wilayah) dengan **total biaya distribusi seminimum mungkin**.

**Formulasi matematis:**

```
minimum  Z = Σᵢ Σⱼ  cᵢⱼ · xᵢⱼ
batasan  Σⱼ xᵢⱼ = Sᵢ      (seluruh pasokan sumber i terkirim)
         Σᵢ xᵢⱼ = Dⱼ      (seluruh permintaan tujuan j terpenuhi)
         xᵢⱼ ≥ 0
```

dengan `cᵢⱼ` = biaya angkut per unit dari sumber *i* ke tujuan *j*,
`xᵢⱼ` = jumlah unit yang dikirim, `Sᵢ` = kapasitas/supply, `Dⱼ` = permintaan/demand.

Penyelesaian dilakukan **dua tahap**: (1) cari **solusi layak awal**, lalu
(2) **uji & perbaiki** sampai optimal.

| Metode | Tahap | Cara kerja singkat | Karakteristik |
|---|---|---|---|
| **North-West Corner (NWC)** | Solusi awal | Mulai dari sel pojok kiri-atas, alokasi maksimum, lalu geser ke kanan/bawah | Paling sederhana; mengabaikan biaya → solusi awal biasanya jauh dari optimal |
| **Least Cost** | Solusi awal | Alokasi ke sel berbiaya terkecil lebih dulu | Mempertimbangkan biaya → umumnya lebih baik dari NWC |
| **VAM (Vogel)** | Solusi awal | Hitung *penalti* (selisih dua biaya terkecil tiap baris/kolom), alokasi pada penalti terbesar | Biasanya paling dekat dengan optimal (sering langsung optimal) |
| **Stepping Stone** | Optimasi | Telusuri lintasan tertutup tiap sel kosong, hitung perubahan biaya, geser alokasi | Intuitif & visual |
| **MODI** | Optimasi | Hitung potensial `uᵢ, vⱼ`, lalu *opportunity cost* `cᵢⱼ−(uᵢ+vⱼ)` secara matematis | Lebih efisien dari Stepping Stone (tak perlu telusuri semua lintasan) |

**Konsep penting:**

- **Seimbang vs tidak seimbang** — syaratnya `Σ supply = Σ demand`. Bila tidak,
  ditambahkan **sumber/tujuan *dummy*** berbiaya 0 untuk menyerap selisih.
- **Degeneracy** — solusi layak butuh tepat **`m + n − 1`** sel basis; bila kurang,
  disisipkan sel beralokasi 0 agar uji optimalitas tetap valid.
- **Optimalitas** — tercapai bila **semua opportunity cost sel kosong ≥ 0**.

---

## 2. Studi Kasus — PT Sentosa Beton

Sebuah perusahaan semen punya **3 pabrik** dan harus memasok **4 kota** dengan biaya
angkut minimum.

**Kapasitas pabrik (supply, ton):** Surabaya 300 · Semarang 400 · Bandung 500
**Permintaan kota (demand, ton):** Jakarta 250 · Yogyakarta 350 · Denpasar 400 · Medan 200

**Biaya angkut (ribu Rp/ton):**

| | Jakarta | Yogyakarta | Denpasar | Medan |
|---|---|---|---|---|
| **Surabaya** | 8 | 6 | 10 | 9 |
| **Semarang** | 9 | 12 | 13 | 7 |
| **Bandung** | 14 | 9 | 16 | 5 |

Total supply = total demand = **1.200 ton** (seimbang). Program tetap dapat menangani
kasus **tidak seimbang** (otomatis menambah baris/kolom *dummy*).

### Hasil

| Metode awal | Biaya solusi awal | Biaya optimal | Iterasi |
|---|---|---|---|
| NWC | 13.000 | **10.700** | 3 |
| Least Cost | 11.450 | **10.700** | 1 |
| VAM | **10.700** | **10.700** | 0 |

Ketiganya konvergen ke **biaya minimum = 10.700 (ribu Rp)**, cocok dengan `scipy`.
VAM bahkan langsung optimal — menunjukkan kualitas metode penalti Vogel.

**Alokasi optimal:** Surabaya→{Yogyakarta 50, Denpasar 250}, Semarang→{Jakarta 250, Denpasar 150},
Bandung→{Yogyakarta 300, Medan 200}.

---

## 3. Cara Menjalankan

```bash
# 1. Pasang dependency
pip install -r requirements.txt

# 2. Jalankan aplikasi web
streamlit run app.py
```

Ubah tabel **Sumber / Tujuan / Biaya**, lalu klik **Hitung Solusi Optimal**.

Menjalankan **uji otomatis**:

```bash
python -m pytest -v          # jika pytest terpasang
python tests/test_solver.py  # tanpa pytest
```

---

## 4. Struktur Proyek

```
UAS/
├── app.py                 # Antarmuka web Streamlit (input & output)
├── ui.py                  # Lapisan tampilan: ikon Lucide (shadcn) + komponen + tema CSS
├── .streamlit/
│   └── config.toml        # Tema warna global (palet netral shadcn)
├── solver/                # "Otak" — logika algoritma murni (tanpa tampilan)
│   ├── __init__.py        #   solve(): merangkai seluruh alur + load_case()
│   ├── model.py           #   struktur data: TransportationProblem, Allocation, ...
│   ├── balancing.py       #   penyeimbangan otomatis (dummy)
│   ├── initial.py         #   solusi awal: NWC, Least Cost, VAM
│   ├── optimize.py        #   MODI + lintasan tertutup (Stepping Stone) + degeneracy
│   └── verify.py          #   verifikasi via scipy.optimize.linprog
├── tests/test_solver.py   # uji kebenaran (contoh materi = 4550, cocok scipy, dll.)
├── cases/semen.json       # data studi kasus
├── requirements.txt
└── README.md
```

Logika algoritma **terpisah penuh** dari tampilan — mudah diuji & dipresentasikan.
Tampilan memakai gaya **shadcn/ui** (palet netral, font Geist, ikon **Lucide**).

---

## 5. Alur Penyelesaian di Aplikasi (sesuai materi Pertemuan 6 & 8)

1. **Penyeimbangan** — jika Σsupply ≠ Σdemand, tambah sumber/tujuan **dummy** biaya 0.
2. **Solusi layak awal** — pilih salah satu: **NWC**, **Least Cost**, atau **VAM**.
3. **Cek degeneracy** — jumlah sel basis harus = `m + n − 1`; bila kurang, sisipkan
   sel beralokasi 0 (memakai *union-find* agar tetap berupa pohon rentang).
4. **Uji optimalitas (MODI)** — hitung potensial `uᵢ, vⱼ` dari `uᵢ + vⱼ = cᵢⱼ` pada
   sel basis, lalu *opportunity cost* tiap sel kosong = `cᵢⱼ − (uᵢ + vⱼ)`.
   Semua ≥ 0 → **optimal**.
5. **Iterasi (Stepping Stone)** — pilih sel paling negatif, bentuk **lintasan tertutup**,
   geser θ unit (θ = alokasi minimum pada sel bertanda −), ulangi sampai optimal.

> **Catatan teknis:** sel basis membentuk *pohon rentang* pada graf bipartit
> baris–kolom. Karena itu lintasan tertutup untuk sebuah sel kosong = lintasan unik
> di pohon antara simpul-baris dan simpul-kolomnya — dihitung efisien dengan BFS.

---

## 6. Verifikasi & Pengujian

- Setiap hasil dicek ulang dengan **`scipy.optimize.linprog`** (HiGHS). Badge hijau
  "Terverifikasi" muncul bila biaya optimal manual **persis sama** dengan solver LP.
- **8 unit test** memastikan: contoh materi → Z=4550, ketiga metode konvergen,
  basis = m+n−1, kasus timpang (dua arah), kecocokan dengan scipy, dan **uji fuzz
  300 kasus acak** yang seluruhnya dicek-silang dengan scipy.

---

## 7. Pembagian Tugas (5 orang)

| Anggota | Tanggung jawab | Berkas |
|---|---|---|
| 1 | Struktur data inti & penyeimbangan | `model.py`, `balancing.py` |
| 2 | Metode solusi awal (NWC / Least Cost / VAM) | `initial.py` |
| 3 | Optimasi MODI + Stepping Stone | `optimize.py` |
| 4 | Antarmuka web & visualisasi | `app.py`, `ui.py` |
| 5 | Pengujian, verifikasi, studi kasus, dokumentasi | `tests/`, `verify.py`, `README.md` |
