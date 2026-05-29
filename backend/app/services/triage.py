"""
Triage Service - Inti dari Logika Medis & Pemicu HPA

Modul ini berisi dua fungsi utama:

1. cpu_intensive_triage_computation()
   ══════════════════════════════════
   Fungsi ini adalah PEMICU UTAMA untuk demonstrasi Kubernetes HPA.
   Ia menghitung bilangan prima hingga 300.000 secara sinkron (blocking)
   menggunakan algoritma trial division yang sengaja TIDAK dioptimasi.

   Kenapa ini penting untuk HPA?
   - Setiap request ke POST /api/patients akan mengeksekusi loop besar ini
   - Setiap eksekusi membutuhkan ~2-5 detik CPU penuh (bergantung hardware)
   - Saat load test dengan 50-100 request bersamaan, CPU pod akan memuncak
   - Kubernetes HPA akan mendeteksi lonjakan CPU dan menambah jumlah pod
   - Anda dapat menyaksikan pod "kloning" secara real-time di kubectl

2. determine_triage_status()
   ═════════════════════════
   Algoritma Triase Otomatis berdasarkan metodologi START Triage
   (Simple Triage and Rapid Treatment) yang digunakan di fasilitas
   kesehatan darurat. Menentukan prioritas penanganan berdasarkan
   skala nyeri dan kata kunci keluhan.
"""

import math


def cpu_intensive_triage_computation() -> int:
    """
    ⚠️  FUNGSI CPU-INTENSIVE - PEMICU KUBERNETES HPA ⚠️

    Menghitung semua bilangan prima dari 2 hingga 300.000
    menggunakan algoritma trial division yang TIDAK dioptimasi.

    Algoritma ini berjalan secara SINKRON (blocking), artinya
    thread yang menjalankannya akan terblokir total hingga selesai.
    Ini adalah perilaku yang DISENGAJA untuk keperluan simulasi HPA.

    Estimasi waktu eksekusi:
    - CPU modern (3+ GHz): ~1-3 detik
    - CPU container (throttled): ~3-8 detik

    Ketika 50+ request dikirim bersamaan (load test), Uvicorn akan
    mengalokasikan thread pool, semua thread akan sibuk menjalankan
    fungsi ini, dan CPU pod akan melonjak mendekati 100%.

    Returns:
        int: Jumlah bilangan prima yang ditemukan (hasilnya: 25.445 prima)
    """
    UPPER_LIMIT = 300_000
    prime_count = 0

    for candidate in range(2, UPPER_LIMIT + 1):
        is_prime = True
        # Trial division - sengaja menggunakan loop biasa (bukan Sieve of Eratosthenes)
        # agar komputasi semaksimal mungkin mengonsumsi CPU
        upper_bound = int(math.sqrt(candidate)) + 1
        for divisor in range(2, upper_bound):
            if candidate % divisor == 0:
                is_prime = False
                break
        if is_prime:
            prime_count += 1

    return prime_count


def determine_triage_status(chief_complaint: str, pain_level: int) -> str:
    """
    Algoritma Triase Otomatis - Metodologi START Triage.

    Sistem triase ini menentukan prioritas penanganan berdasarkan dua faktor:
    1. Tingkat nyeri (pain_level) pada skala 1-10
    2. Kata kunci medis dalam keluhan utama (chief_complaint)

    Kategori Triase:
    ─────────────────────────────────────────────────────────────
    🔴 KRITIS (Immediate):
       - Kondisi mengancam jiwa, membutuhkan penanganan dalam hitungan menit
       - Kriteria: pain_level >= 8 ATAU keluhan kardiovaskular/neurologis
       - Contoh: nyeri dada, sesak napas, tidak sadar, kejang, stroke

    🟡 SEDANG (Delayed):
       - Membutuhkan penanganan segera tapi tidak mengancam jiwa langsung
       - Kriteria: pain_level 5-7 ATAU gejala sistemik signifikan
       - Contoh: demam tinggi, mual parah, pusing berat, infeksi

    🟢 RINGAN (Minor):
       - Kondisi tidak kritis, dapat menunggu antrian normal
       - Kriteria: pain_level 1-4 DAN tidak ada gejala berat
       - Contoh: luka gores, batuk ringan, pilek
    ─────────────────────────────────────────────────────────────

    Args:
        chief_complaint: Deskripsi keluhan utama dari form pendaftaran
        pain_level: Skala nyeri 1-10 yang diinput oleh petugas

    Returns:
        str: "Kritis", "Sedang", atau "Ringan"
    """
    complaint_lower = chief_complaint.lower()

    # ────────────────────────────────────────────────────────────
    # KATA KUNCI KONDISI KRITIS (Merah)
    # Kondisi yang mengancam nyawa dan membutuhkan penanganan segera
    # ────────────────────────────────────────────────────────────
    critical_keywords = [
        # Kardiovaskular
        "nyeri dada", "dada", "jantung", "serangan jantung", "henti jantung",
        "aritmia", "cardiac",
        # Pernapasan
        "sesak napas", "sesak", "tidak bisa napas", "kesulitan bernapas",
        "napas", "shortness of breath", "cannot breathe",
        # Neurologis
        "pingsan", "tidak sadar", "kehilangan kesadaran", "pingsan mendadak",
        "kejang", "epilepsi", "stroke", "lumpuh", "kelumpuhan",
        "sakit kepala tiba-tiba", "kepala terbelah",
        # Trauma & Pendarahan
        "pendarahan", "darah banyak", "luka dalam", "luka tusuk", "luka bacok",
        "patah tulang", "trauma kepala", "benturan kepala", "kecelakaan parah",
        "luka tembak",
        # Bahasa Inggris
        "chest pain", "heart attack", "unconscious", "seizure", "hemorrhage",
        "severe bleeding", "fracture", "head trauma", "stroke",
    ]

    # ────────────────────────────────────────────────────────────
    # KATA KUNCI KONDISI SEDANG (Kuning)
    # Perlu perhatian segera tapi bukan darurat kritis
    # ────────────────────────────────────────────────────────────
    moderate_keywords = [
        # Sistemik
        "demam", "demam tinggi", "menggigil", "dehidrasi",
        "mual parah", "mual", "muntah", "diare berat", "diare",
        # Nyeri & Muskuloskeletal
        "pusing berat", "pusing", "migrain", "vertigo", "nyeri kepala",
        "nyeri perut", "sakit perut", "kram perut", "nyeri punggung",
        # Infeksi & Kondisi Lain
        "infeksi", "bengkak", "abses", "selulitis",
        "lemas parah", "lemas", "tidak kuat berdiri",
        # Bahasa Inggris
        "high fever", "fever", "nausea", "vomiting", "diarrhea",
        "dizziness", "migraine", "abdominal pain", "infection",
        "swelling", "weakness",
    ]

    # ── Evaluasi Kritis (Prioritas Tertinggi) ──
    if pain_level >= 8:
        return "Kritis"
    for keyword in critical_keywords:
        if keyword in complaint_lower:
            return "Kritis"

    # ── Evaluasi Sedang ──
    if pain_level >= 5:
        return "Sedang"
    for keyword in moderate_keywords:
        if keyword in complaint_lower:
            return "Sedang"

    # ── Default: Ringan ──
    return "Ringan"
