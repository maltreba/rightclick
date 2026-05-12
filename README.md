# rightclickwork

`rightclickwork` adalah integrasi **Windows right-click / context menu** yang mengubah file menjadi Markdown (`.md`) agar lebih mudah dipakai sebagai konteks untuk AI. Fokusnya adalah instalasi **tanpa privilege Administrator**: semua dependency Python dipasang di virtual environment lokal repo, dan menu klik kanan ditulis ke registry per-user (`HKCU`).

## Apa yang dilakukan tool ini?

- Menambahkan menu klik kanan **Convert to Markdown for AI** di Windows Explorer.
- Mengonversi file terpilih menjadi `.md` di folder `.ai-markdown` di sebelah file asal.
- Untuk file gambar seperti `.png`, `.jpg`, `.jpeg`, `.tif`, `.tiff`, `.bmp`, `.gif`, dan `.webp`, tool menjalankan OCR terlebih dahulu agar teks/angka/karakter di gambar ikut masuk ke Markdown.
- Untuk dokumen umum seperti PDF, Office, HTML, CSV, dan format lain, tool memakai converter Python `markitdown[all]` agar dependency Office seperti `.xlsx` ikut terpasang.
- Untuk PDF hasil scan/foto, jika MarkItDown tidak menemukan teks yang cukup, tool merender tiap halaman PDF menjadi gambar dengan PyMuPDF lalu menjalankan OCR per halaman.
- Untuk file teks/source code, tool membungkus isi file dalam Markdown code fence agar aman diberikan ke AI.
- Semua output diberi metadata sumber seperti path, ekstensi, MIME type, ukuran file, waktu konversi, dan converter yang dipakai.

## Instalasi cepat di Windows tanpa Administrator

> Jalankan PowerShell dari root repo ini.

```powershell
.\scripts\install-ai-markdown-context-menu.ps1
```

Script tersebut akan:

1. mencari Python 3 user-level (`py -3`, `python`, atau `python3`),
2. membuat virtual environment lokal di `.venv`,
3. memasang package repo ini dan converter lengkap `markitdown[all]` dari `requirements.txt`,
4. memasang dependency OCR dari `requirements-ocr.txt` secara default, termasuk `easyocr` dan `pymupdf`,
5. mendaftarkan context menu di `HKCU` sehingga tidak perlu Administrator.

Setelah selesai, klik kanan file di Windows Explorer lalu pilih **Convert to Markdown for AI**.

## Instalasi OCR Python tanpa Tesseract Windows

Installer normal sekarang memasang OCR dependencies secara default:

```powershell
.\scripts\install-ai-markdown-context-menu.ps1
```

Ini memasang `easyocr` dan `pymupdf` ke virtual environment lokal. `easyocr` lebih besar karena membawa dependency machine learning, tetapi tidak membutuhkan installer Administrator Windows. `pymupdf` dipakai untuk merender halaman PDF hasil scan/foto sebelum OCR.

Jika Anda hanya ingin converter dokumen tanpa OCR berat, gunakan opsi:

```powershell
.\scripts\install-ai-markdown-context-menu.ps1 -SkipOcr
```

Tool juga mendukung `pytesseract`/Tesseract jika sudah tersedia di `PATH`. Urutan OCR yang dicoba adalah:

1. `easyocr`,
2. `pytesseract` + executable Tesseract,
3. executable `tesseract` langsung dari `PATH`.

Jika tidak ada OCR engine, file Markdown tetap dibuat dengan warning agar Anda tahu OCR belum berjalan.

Untuk PDF hasil scan/foto yang sebelumnya menghasilkan warning `PyMuPDF is not installed`, jalankan ulang installer normal lalu ulangi konversi:

```powershell
.\scripts\install-ai-markdown-context-menu.ps1
```

## Cara pakai dari command line

Setelah instalasi, Anda bisa menjalankan converter dengan Python dari venv:

```powershell
.\.venv\Scripts\python.exe -m rightclick_ai_markdown "C:\Path\To\file.pdf"
```

Konversi folder non-recursive:

```powershell
.\.venv\Scripts\python.exe -m rightclick_ai_markdown "C:\Path\To\Folder"
```

Konversi folder recursive:

```powershell
.\.venv\Scripts\python.exe -m rightclick_ai_markdown --recursive "C:\Path\To\Folder"
```

Pilih folder output sendiri:

```powershell
.\.venv\Scripts\python.exe -m rightclick_ai_markdown --output-dir "C:\AI\Markdown" "C:\Path\To\file.docx"
```

## Lokasi output

Default output dibuat di folder `.ai-markdown` di sebelah file sumber:

```text
C:\Data\invoice.png
C:\Data\.ai-markdown\invoice.md
```

Jika file sumber sudah `.md`, output memakai suffix `_converted` supaya tidak menimpa file asli:

```text
notes.md -> .ai-markdown\notes_converted.md
```

Jika output sudah ada, tool membuat nama bernomor seperti `invoice-2.md`, kecuali Anda menjalankan dengan `--overwrite`.

## Uninstall context menu

```powershell
.\scripts\uninstall-context-menu.ps1 -MenuKey RightClickAiMarkdown
```

Jika Anda hanya ingin menghapus lokasi tertentu:

```powershell
.\scripts\uninstall-context-menu.ps1 -MenuKey RightClickAiMarkdown -Locations File,Directory
```

## Script yang tersedia

- `scripts/install-ai-markdown-context-menu.ps1` — installer utama untuk workflow Python + right-click converter.
- `scripts/install-context-menu.ps1` — helper generic untuk mendaftarkan command apa pun ke context menu per-user.
- `scripts/uninstall-context-menu.ps1` — menghapus registry key context menu per-user.
- `python -m rightclick_ai_markdown` — CLI converter file/folder ke Markdown.

## Registry yang dibuat

Installer utama default membuat key berikut:

- `HKCU\Software\Classes\*\shell\RightClickAiMarkdown`
- `HKCU\Software\Classes\Directory\shell\RightClickAiMarkdown`

Anda bisa memilih lokasi lain dengan parameter `-Locations`, misalnya:

```powershell
.\scripts\install-ai-markdown-context-menu.ps1 -Locations File,Directory,DirectoryBackground
```

## Troubleshooting

- Jika menu belum muncul, restart File Explorer lewat Task Manager atau sign out lalu sign in kembali.
- Jika Python tidak ditemukan, install Python untuk current user saja dari python.org atau Microsoft Store, lalu ulangi script install.
- Jika OCR gambar atau PDF hasil scan/foto belum berjalan, ulangi instalasi normal agar `easyocr` dan `pymupdf` terpasang; jangan gunakan `-SkipOcr` kecuali Anda memang tidak membutuhkan OCR. Anda juga bisa memakai executable `tesseract` di `PATH` sebagai fallback.
- Jika muncul warning MarkItDown seperti `MissingDependencyException` untuk `.xlsx`, jalankan ulang `scripts\install-ai-markdown-context-menu.ps1` atau jalankan `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` supaya `markitdown[all]` terpasang.
- Jika dependency gagal di-install karena jaringan/proxy kantor, jalankan `pip` dengan konfigurasi proxy perusahaan atau gunakan wheel offline ke virtual environment `.venv`.
