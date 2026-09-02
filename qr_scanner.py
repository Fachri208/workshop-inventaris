"""
qr_scanner.py
Modul untuk membaca (decode) QR code dari sebuah gambar.
Dipakai oleh app.py setelah user mengambil foto lewat kamera HP (st.camera_input).

Dependensi:
    pip install pyzbar Pillow

Catatan instalasi (khusus pyzbar):
    - Windows: biasanya langsung jalan setelah `pip install pyzbar`
    - Linux/Debian/Ubuntu: perlu install library sistem tambahan dulu:
        sudo apt-get install libzbar0
    - Mac: brew install zbar
"""

from pyzbar.pyzbar import decode
from PIL import Image
import io


def decode_qr_from_bytes(image_bytes):
    """
    Membaca QR code dari data gambar (bytes), misal langsung dari
    hasil st.camera_input() di Streamlit.

    Parameter:
        image_bytes: bytes gambar (jpg/png)

    Return:
        - string hasil decode QR pertama yang ditemukan, ATAU
        - None kalau tidak ada QR yang terbaca di gambar
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
    except Exception as e:
        print(f"Gagal membuka gambar: {e}")
        return None

    hasil = decode(image)

    if not hasil:
        return None

    # Ambil QR pertama yang terdeteksi (kalau di foto ada beberapa QR sekaligus)
    qr_pertama = hasil[0]
    teks = qr_pertama.data.decode("utf-8").strip()
    return teks


def decode_qr_from_file(file_path):
    """
    Versi alternatif: membaca QR langsung dari path file gambar di disk.
    Berguna untuk testing tanpa harus lewat Streamlit.
    """
    image = Image.open(file_path)
    hasil = decode(image)

    if not hasil:
        return None

    return hasil[0].data.decode("utf-8").strip()