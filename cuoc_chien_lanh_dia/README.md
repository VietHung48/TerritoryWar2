# Cuộc Chiến Lãnh Địa (Flask)

Trò chơi tranh lãnh địa cho lớp học, chạy bằng Python + Flask.

## Cài đặt và chạy

```bash
pip install flask
python app.py
```

Mở trình duyệt tại: http://127.0.0.1:5000

Nếu muốn nhiều máy trong cùng mạng LAN cùng xem (ví dụ máy chiếu + laptop admin),
chạy: `app.run(host="0.0.0.0", debug=True)` trong `app.py`, sau đó các máy khác
truy cập bằng địa chỉ IP LAN của máy chạy server.

## Cách chơi

1. **Tab "Câu hỏi"**: có 30 ô số tương ứng 30 câu hỏi đã được xáo trộn ngẫu
   nhiên. Bấm vào 1 ô bất kỳ để mở câu hỏi đó (ô đã dùng sẽ mờ đi, không bấm
   lại được).
2. Khi câu hỏi hiện lên, có thể xuất hiện **Perk (buff)** màu xanh hoặc
   **Debuff** màu đỏ ở đầu popup — đọc to lên cho cả lớp biết luật áp dụng
   cho câu này.
3. Admin đọc to câu hỏi, sau đó tự bấm nút **"Bắt đầu đếm giờ (10s)"** khi
   muốn cho các đội bắt đầu suy nghĩ / trả lời.
4. Nghe câu trả lời của các đội, admin có thể bấm **"Hiện đáp án"** để đối
   chiếu (đáp án được giấu cho tới khi bấm, tránh lộ khi đang chiếu màn hình).
5. Bấm **"Chuyển sang Lãnh địa"** để sang bàn cờ 5x6.
6. Ở tab **"Lãnh địa"**, bấm vào 1 ô trên bàn cờ → chọn nhanh 1 trong 5 màu
   (Đỏ / Lam / Tím / Vàng / Lục) để gán ô đó cho đội tương ứng, hoặc chọn
   "Bỏ trống" để thu hồi về trung lập. Không cần gõ chữ.
   - Nếu perk là **"Nhân đôi"** hoặc **"Lan tỏa"** và đội trả lời đúng: admin
     chủ động bấm thêm 1 ô nữa cho đội đó.
   - Nếu debuff là **"Mất đất"** hoặc **"Cướp đất"**: admin bấm vào ô của đội
     bị ảnh hưởng và chọn "Bỏ trống" (mất đất) hoặc đổi màu sang đội hưởng lợi
     (cướp đất).
7. Bảng xếp hạng bên phải tự cập nhật theo số ô mỗi đội đang chiếm.
8. Bấm **"↺ Chơi lại"** ở góc trên để làm mới toàn bộ ván chơi (xáo lại thứ
   tự câu hỏi, xoá lãnh địa).

## Cập nhật câu hỏi thật

File `app.py` có sẵn 12 câu hỏi thật (lấy từ nội dung gốc) và 18 câu hỏi
MẪU (placeholder) được đánh dấu rõ `[CÂU HỎI MẪU #...]`. Hãy mở `app.py`,
tìm biến `QUESTIONS`, và thay nội dung/đáp án của 18 câu mẫu này bằng câu
hỏi thật của nhóm trước khi dùng chính thức, để tránh dùng nhầm dữ liệu
chưa được kiểm chứng.

Có thể thêm ảnh minh họa cho câu hỏi bằng cách:
1. Copy file ảnh vào thư mục `static/img/`.
2. Thêm đường dẫn vào trường `images` của câu hỏi tương ứng, ví dụ:
   `"images": ["/static/img/ten-anh.jpg"]`

## Tùy chỉnh khác

- Đổi tỉ lệ ra Perk/Debuff: sửa `PERK_WEIGHTS` trong `app.py`.
- Thêm/sửa nội dung Perk: sửa danh sách `PERKS` trong `app.py`.
- Đổi màu/tên đội: sửa `TEAMS` và `TEAM_ORDER` trong `app.py`.
- Đổi kích thước bàn cờ: sửa `ROWS`, `COLS` trong `app.py` (lưu ý nên giữ
  ROWS x COLS = số câu hỏi để mỗi câu tương ứng khả năng chiếm 1 ô).
