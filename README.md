# Novel Polisher

📚 Ứng dụng Windows để **làm mượt văn phong truyện tiếng Việt** từ file PDF bằng AI Gemini.

Đặc biệt tối ưu cho truyện cổ trang như "Tiêu Dao Tiểu Thư Sinh" (逍遥小书生) - giữ sắc thái nhẹ nhàng, hài đời thường.

> **Made By xDzungf** 🎮

---

## ⚡ Quick Start (Dành cho người dùng)

### Yêu cầu hệ thống
- Windows 10/11
- [.NET 8.0 Runtime](https://dotnet.microsoft.com/download/dotnet/8.0) (tải bản Desktop Runtime)

### Bước 1: Tải Release
Tải file ZIP từ [Releases](../../releases) và giải nén.

### Bước 2: Chuẩn bị API Key

Bạn cần một trong hai loại sau:

| Provider | Cách lấy |
|----------|----------|
| **Google AI Studio** (khuyên dùng) | Lấy API Key miễn phí tại [aistudio.google.com](https://aistudio.google.com/) |
| **Google Vertex AI** | Tạo Project trên Google Cloud + Service Account JSON |

### Bước 3: Chạy ứng dụng

1. Mở **NovelPolisher.exe**
2. Chọn file **PDF** cần xử lý (phải là PDF text-based, copy được chữ)
3. Chọn **Provider** và nhập thông tin xác thực:
   - AI Studio: Nhập API Key
   - Vertex AI: Nhập Project ID, Location, và chọn file JSON
4. Bấm **"Bắt Đầu"** và đợi xử lý
5. Lấy kết quả: File `polished.docx` trong thư mục output

### Resume sau khi tạm dừng

Nếu quá trình bị gián đoạn:
1. Mở lại app với cùng file PDF và output folder
2. Bấm **"Tiếp Tục"** (Resume) thay vì "Bắt Đầu"
3. App sẽ tiếp tục từ checkpoint đã lưu

---

## ✨ Tính Năng

- 📄 Trích xuất text từ PDF (text-based)
- 🔧 Tiền xử lý: nối dòng bị ngắt, loại header/footer lặp
- 📖 Tự động tách chương (Chương N: Title)
- 🤖 Làm mượt văn phong với Gemini AI
- 📝 Xuất DOCX (mặc định) + MD backup
- ⏸️ Checkpoint/Resume - có thể tạm dừng và tiếp tục
- 🔐 Lưu API key an toàn với DPAPI

---

## 📁 Cấu Trúc Output

```
out/
├── checkpoint.json      # Checkpoint để resume
├── chunks/              # Các chunk đã xử lý
│   ├── chap_0001_part_001.md
│   ├── chap_0001_part_002.md
│   └── ...
├── polished.docx        # ⭐ File output chính
└── polished.md          # Backup dạng Markdown
```

---

## 🛠️ Build từ Source (Dành cho Developer)

### Yêu cầu
- Python 3.10+
- .NET 8 SDK
- Visual Studio 2022 (hoặc VS Code với C# extension)

### Bước 1: Build Backend Python

```powershell
cd backend

# Cài đặt dependencies
pip install -r requirements.txt

# Build thành EXE
.\build_backend.ps1

# Output: backend/dist/backend.exe
```

### Bước 2: Build WPF App

```powershell
cd app

# Restore packages
dotnet restore

# Build Release
dotnet build -c Release

# Output: app/TranslatorApp/bin/Release/net8.0-windows/
```

### Bước 3: Copy backend.exe vào thư mục app

```powershell
copy ..\backend\dist\backend.exe .\TranslatorApp\bin\Release\net8.0-windows\
```

### Chạy tests

```powershell
cd backend
pytest tests/ -v
```

---

## 🎨 Tùy Chỉnh Style & Glossary

### style.yaml
Cấu hình tone, văn phong, cách xưng hô:

```yaml
tone: "co_trang_nhe_nhang"
avoid_modern_slang: true
pronouns:
  default_you: "ngươi"
  male_to_female: ["cô nương", "tiểu thư"]
```

### glossary.json
Danh sách thuật ngữ cần giữ nguyên:

```json
{
  "công tử": "công tử",
  "cô nương": "cô nương"
}
```

---

## 🔧 Troubleshooting

### "PDF appears to be scan-based"
- PDF của bạn là ảnh scan, không có text
- **Giải pháp**: Dùng OCR (như Adobe Acrobat, ABBYY) để convert sang PDF có text trước

### Lỗi API key / Quota
- Kiểm tra API key còn hiệu lực
- Kiểm tra quota trên Google Cloud Console
- Thử giảm tốc độ (tăng Sleep ms)

### Không tìm thấy chương
- Kiểm tra format tiêu đề chương trong PDF
- App hỗ trợ: "Chương N: Title", "CHƯƠNG N - Title", "Chương N：Title"

### Backend.exe không chạy
- Đảm bảo file backend.exe nằm cùng thư mục với NovelPolisher.exe
- Thử chạy `backend.exe --help` trong command prompt để kiểm tra

---

## 📁 Cấu trúc code

```
NovelPolisher/
├── backend/
│   ├── src/
│   │   ├── main.py           # CLI entry point
│   │   ├── pdf_extract.py    # PDF text extraction
│   │   ├── preprocess.py     # Text preprocessing
│   │   ├── chapter_split.py  # Chapter detection
│   │   ├── chunking.py       # Text chunking
│   │   ├── prompts.py        # AI prompts
│   │   ├── gemini_client.py  # Gemini API client
│   │   ├── checkpoint.py     # Save/resume
│   │   └── exporters.py      # DOCX/MD export
│   ├── tests/
│   ├── style.yaml
│   ├── glossary.json
│   └── requirements.txt
│
└── app/
    └── TranslatorApp/
        ├── ViewModels/
        │   └── MainViewModel.cs
        ├── Models/
        │   └── ProgressInfo.cs
        ├── Services/
        │   └── ConfigService.cs
        ├── MainWindow.xaml
        └── App.xaml
```

---

## 📜 License

MIT License

## 🙏 Credits

- Gemini AI by Google
- pypdf, python-docx, CommunityToolkit.Mvvm
