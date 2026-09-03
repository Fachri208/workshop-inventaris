"""
app.py
Halaman utama aplikasi Inventaris Workshop.

Aplikasi ini berjalan online di Streamlit Community Cloud, sehingga bisa
diakses dari HP mana pun lewat URL aplikasinya (misal https://workshop-inventaris.streamlit.app)
menggunakan jaringan internet/data seluler biasa — TIDAK perlu satu WiFi/hotspot
dengan laptop mana pun.
"""

import streamlit as st
import pandas as pd
from database import init_db, get_all_assets, find_asset_by_number, update_stock_taking, create_and_update_asset
from qr_scanner import decode_qr_from_bytes
from import_excel import import_dataframe

# ==========================================================
# SETUP AWAL
# ==========================================================
st.set_page_config(page_title="Inventaris Workshop", layout="wide")
init_db()  # pastikan tabel database sudah ada

# session_state dipakai supaya data hasil scan tidak hilang
# saat Streamlit me-refresh halaman (misal saat user mengetik di form)
if "asset_ditemukan" not in st.session_state:
    st.session_state.asset_ditemukan = None
if "asset_number_baru" not in st.session_state:
    st.session_state.asset_number_baru = None
if "pesan_error" not in st.session_state:
    st.session_state.pesan_error = None

st.title("📦 Inventaris Workshop")

# ==========================================================
# BAGIAN 0: UPLOAD DATA MASTER DARI EXCEL
# ==========================================================
with st.expander("📤 Upload Data Master dari Excel (klik untuk buka/tutup)"):
    st.caption(
        "Upload file Excel berisi data master barang (Period Name, Book Type, "
        "Asset Number, Asset Name, LOCATION, Internal/Vendor, System). "
        "Barang yang Asset Number-nya sudah ada di database tidak akan dobel."
    )
    file_excel = st.file_uploader("Pilih file Excel (.xlsx)", type=["xlsx", "xls"])

    if file_excel is not None:
        if st.button("Proses Upload"):
            df = pd.read_excel(file_excel, sheet_name=0)
            hasil = import_dataframe(df)

            if hasil["error"]:
                st.error("Kolom berikut tidak ditemukan di file Excel Anda:")
                for col in hasil["missing_columns"]:
                    st.write(f"- {col}")
                st.info("Kolom yang tersedia di file Anda:")
                for col in hasil["available_columns"]:
                    st.write(f"- {col}")
            else:
                st.success(
                    f"Import selesai! Total baris: {hasil['total']}, "
                    f"berhasil: {hasil['berhasil']}, dilewati (data kosong): {hasil['dilewati']}."
                )
                st.rerun()

st.markdown("---")

# ==========================================================
# BAGIAN 1: SCAN QR
# ==========================================================
st.header("1. Scan QR Barang")

foto = st.camera_input("Ambil foto QR pada barang")

if foto is not None:
    # Decode QR dari foto yang baru diambil
    image_bytes = foto.getvalue()
    asset_number = decode_qr_from_bytes(image_bytes)

    if asset_number is None:
        st.session_state.asset_ditemukan = None
        st.session_state.asset_number_baru = None
        st.session_state.pesan_error = "QR tidak terbaca. Coba foto ulang dengan pencahayaan lebih terang dan QR terlihat jelas di tengah frame."
    else:
        # Cari data barang di database berdasarkan Asset Number hasil scan
        data_barang = find_asset_by_number(asset_number)

        if data_barang is None:
            # Barang belum ada di database -> siapkan mode "barang baru",
            # semua kolom akan diisi manual oleh user
            st.session_state.asset_ditemukan = None
            st.session_state.asset_number_baru = asset_number
            st.session_state.pesan_error = None
        else:
            st.session_state.asset_ditemukan = dict(data_barang)
            st.session_state.asset_number_baru = None
            st.session_state.pesan_error = None

# Tampilkan pesan error kalau ada
if st.session_state.pesan_error:
    st.error(st.session_state.pesan_error)

# ==========================================================
# BAGIAN 2: FORM (auto-fill dari QR + isi manual)
# ==========================================================
if st.session_state.asset_ditemukan:
    data = st.session_state.asset_ditemukan

    st.header("2. Data Barang")
    st.success(f"Barang ditemukan: **{data['asset_name']}**")

    # --- Data auto-fill dari QR / database (read-only, tidak bisa diedit) ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.text_input("Asset Number", value=data["asset_number"], disabled=True)
        st.text_input("Period Name", value=data["period_name"], disabled=True)
    with col2:
        st.text_input("Asset Name", value=data["asset_name"], disabled=True)
        st.text_input("Book Type", value=data["book_type"], disabled=True)
    with col3:
        st.text_input("Location (tercatat)", value=data["location"], disabled=True)
        st.text_input("System", value=data["system"], disabled=True)

    st.markdown("---")
    st.subheader("Isi Hasil Pengecekan (manual)")

    # --- 4 kolom yang diisi manual oleh user ---
    with st.form("form_stock_taking"):
        asset_condition = st.selectbox(
            "Asset Condition",
            ["Baik", "Rusak Ringan", "Rusak Berat", "Hilang"]
        )
        updated_location = st.text_input(
            "Updated Location",
            placeholder="Isi lokasi barang saat ini"
        )
        transfer_to = st.text_input(
            "Transfer to (kosongkan jika tidak dipindah)",
            placeholder="Nama staff/lokasi tujuan"
        )
        request_reprint = st.radio(
            "Request Re-print Asset Tag",
            ["Tidak", "Ya"],
            horizontal=True
        )

        simpan = st.form_submit_button("💾 Simpan")

        if simpan:
            if not updated_location.strip():
                st.warning("Updated Location wajib diisi sebelum menyimpan.")
            else:
                update_stock_taking(
                    asset_number=data["asset_number"],
                    asset_condition=asset_condition,
                    updated_location=updated_location.strip(),
                    transfer_to=transfer_to.strip(),
                    request_reprint=request_reprint,
                )
                st.success(f"Data untuk '{data['asset_number']}' berhasil disimpan!")

                # Reset supaya siap scan barang berikutnya
                st.session_state.asset_ditemukan = None
                st.rerun()

# ==========================================================
# BAGIAN 2B: FORM BARANG BARU (Asset Number belum ada di database)
# ==========================================================
if st.session_state.asset_number_baru:
    asset_number_baru = st.session_state.asset_number_baru

    st.header("2. Daftarkan Barang Baru")
    st.info(
        f"Asset Number **{asset_number_baru}** belum terdaftar di database. "
        f"Isi datanya sekali di sini — untuk scan berikutnya pada barang yang sama, "
        f"data ini akan otomatis muncul."
    )

    with st.form("form_barang_baru"):
        st.text_input("Asset Number", value=asset_number_baru, disabled=True)

        col1, col2 = st.columns(2)
        with col1:
            period_name = st.text_input("Period Name", placeholder="misal: 2026-09")
            book_type = st.text_input("Book Type", placeholder="misal: IN_LGE_BOOK")
            asset_name = st.text_input("Asset Name", placeholder="Nama/jenis barang")
        with col2:
            location = st.text_input("Location", placeholder="Lokasi tercatat")
            internal_vendor = st.text_input("Internal/Vendor", placeholder="misal: INTERNAL")
            system = st.text_input("System", placeholder="misal: TAMS")

        st.markdown("---")
        st.subheader("Hasil Pengecekan (manual)")

        asset_condition_baru = st.selectbox(
            "Asset Condition",
            ["Baik", "Rusak Ringan", "Rusak Berat", "Hilang"],
            key="kondisi_baru"
        )
        updated_location_baru = st.text_input(
            "Updated Location",
            placeholder="Isi lokasi barang saat ini",
            key="lokasi_baru"
        )
        transfer_to_baru = st.text_input(
            "Transfer to (kosongkan jika tidak dipindah)",
            placeholder="Nama staff/lokasi tujuan",
            key="transfer_baru"
        )
        request_reprint_baru = st.radio(
            "Request Re-print Asset Tag",
            ["Tidak", "Ya"],
            horizontal=True,
            key="reprint_baru"
        )

        simpan_baru = st.form_submit_button("💾 Simpan Barang Baru")

        if simpan_baru:
            if not asset_name.strip() or not updated_location_baru.strip():
                st.warning("Asset Name dan Updated Location wajib diisi sebelum menyimpan.")
            else:
                create_and_update_asset(
                    asset_number=asset_number_baru,
                    period_name=period_name.strip(),
                    book_type=book_type.strip(),
                    asset_name=asset_name.strip(),
                    location=location.strip(),
                    internal_vendor=internal_vendor.strip(),
                    system=system.strip(),
                    asset_condition=asset_condition_baru,
                    updated_location=updated_location_baru.strip(),
                    transfer_to=transfer_to_baru.strip(),
                    request_reprint=request_reprint_baru,
                )
                st.success(f"Barang baru '{asset_number_baru}' berhasil didaftarkan & disimpan!")

                # Reset supaya siap scan barang berikutnya
                st.session_state.asset_number_baru = None
                st.rerun()

# ==========================================================
# BAGIAN 3: TABEL SEMUA BARANG
# ==========================================================
st.markdown("---")
st.header("3. Daftar Semua Barang")

data_semua = get_all_assets()

if not data_semua:
    st.info("Belum ada data barang. Silakan import data master dari Excel terlebih dahulu (lihat import_excel.py).")
else:
    # Konversi hasil query jadi list of dict supaya bisa ditampilkan st.dataframe
    tabel = [dict(row) for row in data_semua]

    # --- Kotak pencarian: mencari di SEMUA kolom sekaligus ---
    kata_kunci = st.text_input(
        "🔍 Cari barang",
        placeholder="Ketik Asset Number, Asset Name, Location, atau kata kunci lain..."
    )

    if kata_kunci.strip():
        kata_kunci_lower = kata_kunci.strip().lower()
        tabel_tampil = [
            baris for baris in tabel
            if any(kata_kunci_lower in str(nilai).lower() for nilai in baris.values() if nilai is not None)
        ]
    else:
        tabel_tampil = tabel

    st.dataframe(tabel_tampil, use_container_width=True)
    st.caption(f"Menampilkan {len(tabel_tampil)} dari {len(tabel)} total barang di database")