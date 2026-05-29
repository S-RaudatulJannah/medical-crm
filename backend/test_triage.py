"""
Quick test script untuk memverifikasi semua kasus triase
"""
import urllib.request
import json
import time

BASE_URL = "http://localhost:8000"

test_cases = [
    {
        "name": "Tono Ringan",
        "age": 25,
        "chief_complaint": "Batuk ringan dan pilek biasa",
        "pain_level": 2,
        "expected": "Ringan"
    },
    {
        "name": "Maya Sedang",
        "age": 38,
        "chief_complaint": "Demam tinggi disertai mual dan muntah",
        "pain_level": 6,
        "expected": "Sedang"
    },
    {
        "name": "Rina Kritis",
        "age": 52,
        "chief_complaint": "Nyeri dada dan sesak napas mendadak",
        "pain_level": 9,
        "expected": "Kritis"
    },
]

print("=" * 55)
print("VERIFIKASI ALGORITMA TRIASE OTOMATIS")
print("=" * 55)

all_pass = True
for case in test_cases:
    t_start = time.time()
    payload = {k: v for k, v in case.items() if k != "expected"}
    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        f"{BASE_URL}/api/patients",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read())
    elapsed = time.time() - t_start

    status = result["triage_status"]
    passed = status == case["expected"]
    all_pass = all_pass and passed
    icon = "PASS" if passed else "FAIL"

    print(f"\n[{icon}] {case['name']}")
    print(f"      Keluhan  : {case['chief_complaint']}")
    print(f"      Pain     : {case['pain_level']}/10")
    print(f"      Triage   : {status} (expected: {case['expected']})")
    print(f"      CPU Time : {elapsed:.2f} detik")

print("\n" + "=" * 55)
print("HASIL:", "SEMUA TEST LULUS!" if all_pass else "ADA TEST GAGAL!")
print("=" * 55)

# Test GET endpoints
print("\n--- GET /api/patients ---")
resp = urllib.request.urlopen(f"{BASE_URL}/api/patients")
data = json.loads(resp.read())
print(f"Total pasien terdaftar: {data['total']}")

print("\n--- GET /api/hospitals/stats ---")
resp = urllib.request.urlopen(f"{BASE_URL}/api/hospitals/stats")
data = json.loads(resp.read())
print(f"Rumah Sakit: {data['hospital_name']}")
print(f"Kapasitas  : {data['bed_capacity']} tempat tidur")
print(f"Tersedia   : {data['beds_available']} tempat tidur")
print(f"Triase     : Kritis={data['triage_distribution']['critical']}, "
      f"Sedang={data['triage_distribution']['moderate']}, "
      f"Ringan={data['triage_distribution']['mild']}")
