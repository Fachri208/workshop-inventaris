import sqlite3
from datetime import datetime

DB_NAME = "workshop.db"


def get_connection():
    """Buka koneksi baru ke database SQLite."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # supaya hasil query bisa diakses seperti dict
    return conn


def init_db():
    """
    Membuat tabel 'assets' jika belum ada.
    Dipanggil sekali di awal (misal saat app.py pertama kali jalan).
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    conn.close()


def get_all_assets():
    """Ambil semua data barang untuk ditampilkan di tabel utama."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM assets ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows


def find_asset_by_number(asset_number):
    """
    Cari satu barang berdasarkan Asset Number (hasil decode QR).
    Return None kalau tidak ditemukan.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM assets WHERE asset_number = ?", (asset_number,))
    row = cursor.fetchone()
    conn.close()
    return row


def insert_asset(data: dict):
    """
    Tambah 1 baris data master baru (dipakai saat import dari Excel).
    'data' adalah dict dengan key sesuai nama kolom di tabel.
    Kalau asset_number sudah ada, baris akan dilewati (INSERT OR IGNORE).
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO assets
        (period_name, book_type, asset_number, asset_name, location, internal_vendor, system)
        VALUES (:period_name, :book_type, :asset_number, :asset_name, :location, :internal_vendor, :system)
    """, data)
    conn.commit()
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
        SET asset_condition = ?,
            updated_location = ?,
            transfer_to = ?,
            request_reprint = ?,
            last_scanned_at = ?
        WHERE asset_number = ?
    """, (
        asset_condition,
        updated_location,
        transfer_to,
        request_reprint,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        asset_number
    ))
    conn.commit()
    conn.close()