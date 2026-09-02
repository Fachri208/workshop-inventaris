"""
import_excel.py
Script untuk mengimpor data master barang dari file Excel ke database SQLite.
Cara pakai (lewat terminal):
    python import_excel.py "nama_file.xlsx"

Atau kalau nama file mengandung spasi:
    python import_excel.py "data barang.xlsx"
"""

import sys
import pandas as pd
from database import init_db, insert_asset

# ==========================================================
# MAPPING KOLOM
# Sesuaikan bagian ini kalau nama header di Excel Anda berbeda.
# Format: "nama_kolom_di_database": "nama_header_persis_di_excel"
# ==========================================================
COLUMN_MAPPING = {
    "period_name": "Period Name",
    "book_type": "Book Type",
    "asset_number": "Asset Number",
    "asset_name": "Asset Name",
    "location": "LOCATION",
    "internal_vendor": "Internal/Vendor",
    "system": "System",
}


def import_dataframe(df):
    """
    Fungsi inti: menerima DataFrame pandas (dari file Excel manapun sumbernya,
    baik dibuka lewat path file atau hasil upload di Streamlit) dan
    memasukkan datanya ke database.

    Return: dict berisi ringkasan hasil import, atau dict berisi 'error'
    kalau ada kolom yang tidak ditemukan.
    """
    # Bersihkan nama kolom dari spasi berlebih
    df.columns = [str(c).strip() for c in df.columns]

    # Cek apakah semua kolom yang dibutuhkan ada di file Excel
    missing_columns = [
        excel_col for excel_col in COLUMN_MAPPING.values()
        if excel_col not in df.columns
    ]
    if missing_columns:
        return {
            "error": True,
            "missing_columns": missing_columns,
            "available_columns": list(df.columns),
        }

    init_db()

    total = len(df)
    berhasil = 0
    dilewati = 0

    for _, row in df.iterrows():
        asset_number = row.get(COLUMN_MAPPING["asset_number"])

        # Lewati baris yang Asset Number-nya kosong
        if pd.isna(asset_number) or str(asset_number).strip() == "":
            dilewati += 1
            continue

        data = {
            "period_name": _clean(row.get(COLUMN_MAPPING["period_name"])),
            "book_type": _clean(row.get(COLUMN_MAPPING["book_type"])),
            "asset_number": str(asset_number).strip(),
            "asset_name": _clean(row.get(COLUMN_MAPPING["asset_name"])),
            "location": _clean(row.get(COLUMN_MAPPING["location"])),
            "internal_vendor": _clean(row.get(COLUMN_MAPPING["internal_vendor"])),
            "system": _clean(row.get(COLUMN_MAPPING["system"])),
        }

        insert_asset(data)
        berhasil += 1

    return {
        "error": False,
        "total": total,
        "berhasil": berhasil,
        "dilewati": dilewati,
    }


def import_from_excel(file_path):
    """
    Dipakai untuk menjalankan import lewat command line:
        python import_excel.py "nama_file.xlsx"
    """
    print(f"Membaca file: {file_path} ...")
    df = pd.read_excel(file_path, sheet_name=0)
    hasil = import_dataframe(df)

    if hasil["error"]:
        print("PERINGATAN: kolom berikut tidak ditemukan di file Excel:")
        for col in hasil["missing_columns"]:
            print(f"   - {col}")
        print("Kolom yang tersedia di file:")
        for col in hasil["available_columns"]:
            print(f"   - {col}")
        print("\nSilakan sesuaikan COLUMN_MAPPING di bagian atas file ini, lalu jalankan ulang.")
        return

    print("\nSelesai import.")
    print(f"   Total baris di Excel : {hasil['total']}")
    print(f"   Berhasil diproses    : {hasil['berhasil']}")
    print(f"   Dilewati (data kosong): {hasil['dilewati']}")
    print("\nCatatan: barang dengan Asset Number yang SAMA dengan yang sudah ada di database akan otomatis dilewati (tidak dobel).")


def _clean(value):
    """Ubah nilai kosong/NaN dari Excel jadi string kosong, selain itu jadi string biasa."""
    if pd.isna(value):
        return ""
    return str(value).strip()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Cara pakai: python import_excel.py \"nama_file.xlsx\"")
        sys.exit(1)

    file_path = sys.argv[1]
    import_from_excel(file_path)