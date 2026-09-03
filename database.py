"""
database.py
Modul untuk mengelola koneksi dan operasi CRUD ke database PostgreSQL (Supabase).
Semua fungsi di sini dipakai oleh app.py dan import_excel.py.

Kredensial koneksi database TIDAK ditulis langsung di sini (supaya aman),
melainkan diambil dari Streamlit Secrets (st.secrets["DB_CONNECTION_STRING"]).
Lihat panduan setup 'Secrets' di Streamlit Cloud untuk cara mengisinya.
"""

import psycopg2
import psycopg2.extras
from datetime import datetime
import streamlit as st


def get_connection():
    """Buka koneksi baru ke database PostgreSQL (Supabase)."""
    conn_string = st.secrets["DB_CONNECTION_STRING"]
    conn = psycopg2.connect(conn_string)
    return conn


def init_db():
    """
    Membuat tabel 'assets' jika belum ada.
    Dipanggil setiap kali app.py jalan (aman dipanggil berkali-kali).
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assets (
            id SERIAL PRIMARY KEY,
            period_name TEXT,
            book_type TEXT,
            asset_number TEXT UNIQUE NOT NULL,
            asset_name TEXT,
            location TEXT,
            internal_vendor TEXT,
            system TEXT,
            asset_condition TEXT,
            updated_location TEXT,
            transfer_to TEXT,
            request_reprint TEXT,
            last_scanned_at TEXT
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()


def get_all_assets():
    """Ambil semua data barang untuk ditampilkan di tabel utama."""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM assets ORDER BY id DESC")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def find_asset_by_number(asset_number):
    """
    Cari satu barang berdasarkan Asset Number (hasil decode QR).
    Return None kalau tidak ditemukan.
    """
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM assets WHERE asset_number = %s", (asset_number,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row


def insert_asset(data: dict):
    """
    Tambah 1 baris data master baru (dipakai saat import dari Excel).
    'data' adalah dict dengan key sesuai nama kolom di tabel.
    Kalau asset_number sudah ada, baris akan dilewati (ON CONFLICT DO NOTHING).
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO assets
        (period_name, book_type, asset_number, asset_name, location, internal_vendor, system)
        VALUES (%(period_name)s, %(book_type)s, %(asset_number)s, %(asset_name)s, %(location)s, %(internal_vendor)s, %(system)s)
        ON CONFLICT (asset_number) DO NOTHING
    """, data)
    conn.commit()
    cursor.close()
    conn.close()


def create_and_update_asset(asset_number, period_name, book_type, asset_name, location,
                             internal_vendor, system, asset_condition, updated_location,
                             transfer_to, request_reprint):
    """
    Dipakai saat Asset Number hasil scan BELUM ADA di database.
    Membuat baris baru sekaligus (data master + hasil pengecekan) dalam satu langkah,
    karena user mengisi semuanya secara manual lewat form.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO assets
        (asset_number, period_name, book_type, asset_name, location, internal_vendor, system,
         asset_condition, updated_location, transfer_to, request_reprint, last_scanned_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (asset_number) DO UPDATE SET
            period_name = EXCLUDED.period_name,
            book_type = EXCLUDED.book_type,
            asset_name = EXCLUDED.asset_name,
            location = EXCLUDED.location,
            internal_vendor = EXCLUDED.internal_vendor,
            system = EXCLUDED.system,
            asset_condition = EXCLUDED.asset_condition,
            updated_location = EXCLUDED.updated_location,
            transfer_to = EXCLUDED.transfer_to,
            request_reprint = EXCLUDED.request_reprint,
            last_scanned_at = EXCLUDED.last_scanned_at
    """, (
        asset_number, period_name, book_type, asset_name, location, internal_vendor, system,
        asset_condition, updated_location, transfer_to, request_reprint,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    cursor.close()
    conn.close()


def update_stock_taking(asset_number, asset_condition, updated_location, transfer_to, request_reprint):
    """
    Update kolom hasil stock taking (yang diisi manual setelah scan QR).
    Dipanggil saat user klik tombol 'Simpan' di form.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE assets
        SET asset_condition = %s,
            updated_location = %s,
            transfer_to = %s,
            request_reprint = %s,
            last_scanned_at = %s
        WHERE asset_number = %s
    """, (
        asset_condition,
        updated_location,
        transfer_to,
        request_reprint,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        asset_number
    ))
    conn.commit()
    cursor.close()
    conn.close()