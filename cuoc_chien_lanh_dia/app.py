# -*- coding: utf-8 -*-
"""
Cuộc Chiến Lãnh Địa - Flask backend
------------------------------------
Trò chơi tranh lãnh địa cho lớp học:
- 30 câu hỏi được xáo trộn ngẫu nhiên, admin chọn câu để mở.
- Sau khi mở câu hỏi, admin tự đọc to, bấm "Bắt đầu đếm giờ" (10s) khi muốn.
- Có tỉ lệ ngẫu nhiên xuất hiện Perk (buff) hoặc Debuff khi mở câu hỏi.
- Sau khi biết đội nào trả lời đúng, admin chuyển sang tab "Lãnh địa" và
  bấm vào 1 ô trên bàn cờ 5x6, chọn nhanh 1 trong 5 màu (Lam/Đỏ/Tím/Vàng/Lục)
  để gán ô đó cho đội tương ứng - không cần gõ chữ.

Chạy thử:
    pip install flask
    python app.py
Sau đó mở trình duyệt: http://127.0.0.1:5000
"""

import random
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

ROWS, COLS = 5, 12  # 30 ô, khớp với 30 câu hỏi

# ---------------------------------------------------------------------------
# Danh sách đội chơi (thay cho việc phải gõ tên đội bằng textbox)
# ---------------------------------------------------------------------------
TEAMS = {
    "do":   {"name": "Nhóm 1 (ĐL)",   "color": "#e74c3c"},
    "lam":  {"name": "Nhóm 2 (PCL)",  "color": "#3498db"},
    "tim":  {"name": "Nhóm 3 (Nguyễn 1)",  "color": "#9b59b6"},
    "vang": {"name": "Nhóm 5 (Liên họ)", "color": "#f1c40f"},
    "luc":  {"name": "Nhóm 6 (Nguyễn 2)",  "color": "#2ecc71"},
}
TEAM_ORDER = ["do", "lam", "tim", "vang", "luc"]

# ---------------------------------------------------------------------------
# Perk / Debuff - áp dụng THỦ CÔNG bởi admin ở tab Lãnh địa sau khi biết
# đội nào trả lời đúng/sai. Hệ thống chỉ có nhiệm vụ "quay số" ngẫu nhiên
# và hiển thị hướng dẫn, không tự động thao tác bàn cờ.
# ---------------------------------------------------------------------------
PERKS = [
    {
        "type": "buff",
        "key": "double",
        "title": "🎉 NHÂN ĐÔI LÃNH ĐỊA",
        "desc": "Nếu đội trả lời ĐÚNG: được chiếm thêm 1 ô bất kỳ ngoài ô hiện tại.",
    },
    {
        "type": "buff",
        "key": "spread",
        "title": "🌱 LAN TỎA",
        "desc": "Nếu đội trả lời ĐÚNG: được chiếm thêm 1 ô liền kề với ô vừa chiếm.",
    },
    {
        "type": "buff",
        "key": "shield",
        "title": "🛡️ KHIÊN CHẮN",
        "desc": "Nếu đội trả lời SAI: đội vẫn KHÔNG bị mất ô nào ở lượt này.",
    },
    {
        "type": "debuff",
        "key": "lose_tile",
        "title": "⚠️ MẤT ĐẤT",
        "desc": "Dù đúng hay sai: đội vẫn bị mất 1 ô đang sở hữu (admin chọn ô để thu hồi).",
    },
    {
        "type": "debuff",
        "key": "steal",
        "title": "😈 CƯỚP ĐẤT",
        "desc": "Nếu đội trả lời SAI: đội đang dẫn đầu bảng xếp hạng được chiếm thêm 1 ô của đội này.",
    },
]
# Trọng số random
PERK_WEIGHTS = {"none": 0.60, "buff": 0.25, "debuff": 0.15}


def roll_perk():
    """Random xem có ra Perk/Debuff không"""
    roll = random.random()
    if roll < PERK_WEIGHTS["none"]:
        return None
    pool_type = "buff" if roll < PERK_WEIGHTS["none"] + PERK_WEIGHTS["buff"] else "debuff"
    pool = [p for p in PERKS if p["type"] == pool_type]
    return random.choice(pool)

QUESTIONS = [
    # ============================= PHẦN I =============================
    {
        "id": 1, 
        "question": "Theo tư tưởng Hồ Chí Minh, sự ra đời của Đảng Cộng sản Việt Nam là sản phẩm của sự kết hợp giữa chủ nghĩa Mác - Lênin, phong trào công nhân và yếu tố nào sau đây?",
        "options": {
            "A": "Phong trào nông dân.",
            "B": "Phong trào yêu nước.",
            "C": "Phong trào trí thức.",
            "D": "Phong trào tư sản dân tộc.",
        },
        "answer": "B",
    },
    {
        "id": 2, 
        "question": "Trong Lễ kỷ niệm 30 năm Ngày thành lập Đảng (năm 1960), Chủ tịch Hồ Chí Minh đã khẳng định hai chiều kích cốt lõi của Đảng cầm quyền là gì?",
        "options": {
            "A": "Đảng là tiên phong và là lãnh đạo.",
            "B": "Đảng là đạo đức và là văn minh.",
            "C": "Đảng là kiên cường và là sáng tạo.",
            "D": "Đảng là của dân và vì dân.",
        },
        "answer": "B",
    },
    {
        "id": 3, 
        "question": "Chủ tịch Hồ Chí Minh ví tự phê bình và phê bình trong Đảng giống như cái gì để làm cho phần tốt nảy nở và phần xấu mất dần đi?",
        "options": {
            "A": "Chiếc gương soi hàng ngày.",
            "B": "Thang thuốc tốt.",
            "C": "Liều vắc-xin phòng bệnh.",
            "D": "Con dao sắc bén.",
        },
        "answer": "B",
    },
    {
        "id": 4, 
        "question": "Theo Chủ tịch Hồ Chí Minh, yếu tố nào được coi là \"gốc\", là nền tảng của người cách mạng?",
        "options": {
            "A": "Tài năng chuyên môn.",
            "B": "Đạo đức cách mạng.",
            "C": "Trình độ lý luận chính trị.",
            "D": "Kinh nghiệm thực tiễn.",
        },
        "answer": "B",
    },
    {
        "id": 5, 
        "question": "Vì sao Chủ tịch Hồ Chí Minh lại khẳng định Đảng Cộng sản Việt Nam không chỉ là đảng của giai cấp công nhân và nhân dân lao động mà còn đồng thời là đảng của dân tộc Việt Nam?",
        "options": {
            "A": "Vì giai cấp công nhân chiếm số lượng đông đảo nhất trong cơ cấu dân số của nước ta lúc bấy giờ.",
            "B": "Vì quyền lợi của giai cấp công nhân, nhân dân lao động và của toàn dân tộc là một, Đảng luôn đặt lợi ích của Tổ quốc lên trên hết.",
            "C": "Vì Đảng do toàn bộ các giai cấp trong xã hội đồng sáng lập và nuôi dưỡng.",
            "D": "Vì Đảng chỉ bảo vệ quyền lợi riêng cho tầng lớp trí thức và tư sản dân tộc.",
        },
        "answer": "A",
    },
    {
        "id": 6, 
        "question": "Việc Chủ tịch Hồ Chí Minh kiên quyết ký bác đơn ân xá và phê chuẩn bản án tử hình đối với Đại tá Trần Dụ Châu (năm 1950) thể hiện quan điểm nào sau đây trong xây dựng Đảng?",
        "options": {
            "A": "Kiên quyết phòng, chống tham ô, lãng phí, quan liêu (\"giặc nội xâm\") để giữ gìn sự trong sạch của tổ chức.",
            "B": "Phải chú trọng công tác phát triển đảng viên mới ở mọi tầng lớp trong xã hội.",
            "C": "Tập trung phát triển kinh tế quân đội gắn liền với củng cố quốc phòng an ninh.",
            "D": "Đề cao nguyên tắc tập trung dân chủ trong mọi hoạt động của lực lượng vũ trang.",
        },
        "answer": "B",
    },
    {
        "id": 7, 
        "question": "Ý nghĩa cốt lõi của nguyên tắc \"tập thể lãnh đạo, cá nhân phụ trách\" trong sinh hoạt Đảng theo tư tưởng Hồ Chí Minh là gì?",
        "options": {
            "A": "Đề cao quyền lực tuyệt đối của người đứng đầu cấp ủy để quyết nhanh công việc.",
            "B": "Tránh lạm quyền độc đoán, chuyên quyền, đồng thời khắc phục tư tưởng dựa dẫm, ỷ lại của cá nhân.",
            "C": "Giao toàn bộ trách nhiệm công việc cho tập thể để không ai phải chịu trách nhiệm cá nhân.",
            "D": "Giảm bớt số lượng cuộc họp và nâng cao tính hình thức trong sinh hoạt chi bộ.",
        },
        "answer": "B",
    },
    {
        "id": 8,
        "question": "Một cán bộ lãnh đạo cơ quan thường xuyên tự ý quyết định các dự án mua sắm tài sản công lớn mà không đưa ra tập thể bàn bạc, khi sai sót thì đùn đẩy trách nhiệm cho cấp dưới. Xét theo tư tưởng Hồ Chí Minh, vị cán bộ này đã vi phạm nghiêm trọng nguyên tắc nào trong xây dựng Đảng?",
        "options": {
            "A": "Kỷ luật nghiêm minh và tự giác.",
            "B": "Tập trung dân chủ (cụ thể là vi phạm \"tập thể lãnh đạo, cá nhân phụ trách\").",
            "C": "Đoàn kết, thống nhất trong Đảng.",
            "D": "Đảng phải thường xuyên tự chỉnh đốn.",
        },
        "answer": "B",
    },
    {
        "id": 9,
        "question": "Khi đánh giá và bố trí cán bộ trong một đơn vị sự nghiệp, nếu người đứng đầu áp dụng đúng đắn quan điểm \"Dụng nhân như dụng mộc\" và tư tưởng đánh giá cán bộ của Hồ Chí Minh, thì hành động nào sau đây là phù hợp nhất?",
        "options": {
            "A": "Bố trí người nhà, người thân cận giữ các vị trí chủ chốt để dễ bề quản lý và tin tưởng.",
            "B": "Xem xét năng lực, phẩm chất thông qua sản phẩm công việc thực tế và bố trí cán bộ vào đúng vị trí sở trường.",
            "C": "Chỉ dựa vào bằng cấp học thuật cao hay thâm niên công tác lâu năm để cất nhắc mà không cần thử thách qua thực tiễn.",
            "D": "Luân chuyển cán bộ liên tục giữa các phòng ban hoàn toàn ngẫu nhiên để rèn luyện ý chí.",
        },
        "answer": "B",
    },
    {
        "id": 10,
        "question": "Trong bối cảnh hiện nay, một số cán bộ, đảng viên có biểu hiện \"sợ sai, không dám làm, né tránh trách nhiệm\" khi thực hiện công vụ. Nhìn nhận từ tư tưởng Hồ Chí Minh về đạo đức và tác phong của người cán bộ, biểu hiện này phản ánh sự suy thoái về mặt nào?",
        "options": {
            "A": "Suy thoái về đạo đức, lối sống ích kỷ cá nhân.",
            "B": "Suy thoái về tư tưởng chính trị, phai nhạt ý chí chiến đấu và thiếu tinh thần phụng sự nhân dân.",
            "C": "Vi phạm nguyên tắc đoàn kết quốc tế.",
            "D": "Yếu kém hoàn toàn về chuyên môn nghiệp vụ kỹ thuật.",
        },
        "answer": "B",
    },
 
    # ============================= PHẦN II =============================
    {
        "id": 11, 
        "question": "Theo Chủ tịch Hồ Chí Minh, phẩm chất nào được coi là \"cái gốc của người cán bộ\"?",
        "options": {
            "A": "Năng lực chuyên môn.",
            "B": "Đạo đức cách mạng.",
            "C": "Trình độ lý luận chính trị.",
            "D": "Tinh thần đoàn kết nội bộ.",
        },
        "answer": "B",
    },
    {
        "id": 12, 
        "question": "Chủ tịch Hồ Chí Minh đã gọi tham ô, lãng phí và quan liêu là gì?",
        "options": {
            "A": "Những sai lầm khuyết điểm nhất thời.",
            "B": "Những vật cản trên con đường đi lên chủ nghĩa xã hội.",
            "C": "Kẻ thù của giai cấp công nhân.",
            "D": "Những thứ \"giặc ở trong lòng\".",
        },
        "answer": "D",
    },
    {
        "id": 13, 
        "question": "Theo nội dung nhóm trình bày, yếu tố nào dưới đây là nguyên nhân khách quan dẫn đến sự suy thoái của cán bộ, đảng viên?",
        "options": {
            "A": "Sự thiếu tu dưỡng, rèn luyện của bản thân cán bộ.",
            "B": "Ý thức tự phê bình và phê bình chưa cao.",
            "C": "Tác động của nền kinh tế thị trường, toàn cầu hóa và mạng xã hội.",
            "D": "Động cơ phấn đấu bị lệch lạc.",
        },
        "answer": "C",
    },
    {
        "id": 14, 
        "question": "Sự đứt gãy mối liên hệ mật thiết với nhân dân đi ngược lại với tôn chỉ hoạt động nào của Đảng?",
        "options": {
            "A": "Đảng lãnh đạo tuyệt đối, trực tiếp về mọi mặt.",
            "B": "Đảng từ nhân dân mà ra, vì nhân dân phục vụ.",
            "C": "Đảng là đội tiên phong của giai cấp công nhân.",
            "D": "Đảng hoạt động theo nguyên tắc tập trung dân chủ.",
        },
        "answer": "B",
    },
    {
        "id": 15, 
        "question": "Tại sao Chủ tịch Hồ Chí Minh coi bệnh quan liêu là một căn bệnh rất nguy hiểm đối với cán bộ?",
        "options": {
            "A": "Vì nó trực tiếp làm thất thoát tài sản nhà nước.",
            "B": "Vì nó khiến cán bộ không hiểu thực tế, không nắm được nguyện vọng của dân.",
            "C": "Vì nó là mầm mống của sự chia rẽ nội bộ Đảng.",
            "D": "Vì nó tạo điều kiện cho thế lực thù địch xuyên tạc.",
        },
        "answer": "B",
    },
    {
        "id": 16, 
        "question": "Theo đánh giá của Đảng ta, sự xuất hiện của các hành vi tham nhũng, lãng phí có nguyên nhân sâu xa nhất từ yếu tố nào thuộc về phương diện cá nhân của cán bộ, đảng viên?",
        "options": {
            "A": "Sự tác động của các luồng văn hóa ngoại lai thông qua quá trình toàn cầu hóa.",
            "B": "Sự bất cập trong các chính sách đãi ngộ, tiền lương của nhà nước.",
            "C": "Sự sa vào chủ nghĩa cá nhân và buông lỏng công tác tu dưỡng, rèn luyện đạo đức.",
            "D": "Sự chống phá tinh vi trên mặt trận tư tưởng của các thế lực thù địch.",
        },
        "answer": "C",
    },
    {
        "id": 17, 
        "question": "Trong tổ chức và sinh hoạt Đảng, sự suy giảm tính khách quan, minh bạch trong công tác cán bộ chủ yếu xuất phát từ việc vi phạm nguyên tắc cơ bản nào sau đây?",
        "options": {
            "A": "Nguyên tắc tự phê bình và phê bình.",
            "B": "Nguyên tắc tập trung dân chủ.",
            "C": "Nguyên tắc đoàn kết thống nhất.",
            "D": "Nguyên tắc kỷ luật nghiêm minh, tự giác.",
        },
        "answer": "B",
    },
    {
        "id": 18, 
        "question": "Biểu hiện đặc trưng nhất của sự suy thoái về tư tưởng chính trị trong môi trường hội nhập và bùng nổ thông tin hiện nay đối với một bộ phận cán bộ, đảng viên là gì?",
        "options": {
            "A": "Dao động lập trường, thiếu bản lĩnh nhận diện và đấu tranh bảo vệ nền tảng tư tưởng của Đảng.",
            "B": "Sử dụng quyền lực công để trục lợi cá nhân.",
            "C": "Quan liêu, thiếu trách nhiệm trong công tác quản lý nhà nước.",
            "D": "Bị chi phối bởi các quan hệ thân quen trong việc sắp xếp nhân sự.",
        },
        "answer": "A",
    },
    {
        "id": 19, 
        "question": "Thái độ hách dịch, vô cảm và gây khó khăn trong việc giải quyết thủ tục hành chính cho người dân không chỉ vi phạm đạo đức công vụ mà về mặt lý luận, mà còn phủ nhận trực tiếp bản chất nào của nhà nước theo tư tưởng Hồ Chí Minh? ",
        "options": {
            "A": "Tính giai cấp công nhân của bộ máy nhà nước.",
            "B": "Tính dân tộc và tính thời đại trong định hướng phát triển.",
            "C": "Nguyên tắc pháp quyền, quản lý xã hội bằng hiến pháp và pháp luật.",
            "D": "Bản chất nhà nước của nhân dân, do nhân dân, vì nhân dân.",
        },
        "answer": "D",
    },
    {
        "id": 20, 
        "question": "Khi phân tích về cơ chế phát sinh sự suy thoái, mối quan hệ biện chứng giữa yếu tố \"khoảng trống trong cơ chế kiểm tra, giám sát\" và \"sự suy thoái của cán bộ\" được giải thích như thế nào?",
        "options": {
            "A": "Cơ chế giám sát lỏng lẻo là nguyên nhân gốc rễ, quyết định hoàn toàn sự suy thoái đạo đức của cán bộ.",
            "B": "Sự lỏng lẻo của cơ chế quản lý tạo điều kiện môi trường thuận lợi để chủ nghĩa cá nhân phát sinh thành các hành vi vi phạm kéo dài.",
            "C": "Sự suy thoái của cán bộ là yếu tố khách quan, hoàn toàn không phụ thuộc vào mức độ hoàn thiện của cơ chế kiểm tra.",
            "D": "Cơ chế kiểm tra và đạo đức cán bộ là hai phạm trù độc lập, không có sự tác động qua lại lẫn nhau.",
        },
        "answer": "B",
    },
 
    # ============================= PHẦN III =============================
    {
        "id": 21,
        "question": "Bộ Chính trị khuyến khích học tập và làm theo tư tưởng, đạo đức, phong cách Hồ Chí Minh theo tinh thần của Chỉ thị nào?",
        "options": {
            "A": "Chỉ thị số 05-TW/CT và Chỉ thị số 06-TW/CT",
            "B": "Chỉ thị số 06-TW/CT và Chỉ thị số 07-TW/CT",
            "C": "Chỉ thị số 05-CT/TW và Chỉ thị số 06-CT/TW",
            "D": "Chỉ thị số 06-CT/TW và Chỉ thị số 07-CT/TW",
        },
        "answer": "C",
    },
    {
        "id": 22,
        "question": "Theo Hồ Chí Minh, đạo đức cách mạng \"không phải từ trên trời sa xuống\", mà giống như:",
        "options": {
            "A": "Như ngọc càng mài càng sáng, vàng càng luyện càng trong",
            "B": "Như ngọc càng mài càng sáng, bạc càng tôi càng cứng",
            "C": "Như ngọc càng mài càng sáng, sắt càng tôi càng cứng",
            "D": "Như ngọc càng mài càng sáng, đồng càng tôi càng cứng",
        },
        "answer": "A",
    },
    {
        "id": 23,
        "question": "Việc kiểm soát quyền lực, đặc biệt là quyền lực người đứng đầu, được ví bằng hình ảnh nào?",
        "options": {
            "A": "Xây tường lửa quyền lực",
            "B": "Nhốt quyền lực trong lồng cơ chế",
            "C": "Đóng khung trách nhiệm",
            "D": "Giám sát vòng ngoài",
        },
        "answer": "B",
    },
    {
        "id": 24,
        "question": "Câu nào thể hiện quan điểm của Hồ Chí Minh về mối quan hệ giữa đức và tài?",
        "options": {
            "A": "\"Đức và tài phải song hành\"",
            "B": "\"Có tài mà không có đức là người vô dụng. Có đức mà không có tài làm việc gì cũng khó\"",
            "C": "\"Đức là gốc, tài là ngọn\"",
            "D": "\"Tài quan trọng hơn đức\"",
        },
        "answer": "B",
    },
    {
        "id": 25, 
        "question": "Tự phê bình và phê bình được ví là \"vũ khí\", nhưng đồng thời nó cũng dễ bị lợi dụng theo hướng nào?",
        "options": {
            "A": "Dùng để đùn đẩy trách nhiệm tập thể",
            "B": "Dùng để hợp thức hóa sai phạm đã gây ra",
            "C": "Dùng để tự giải quyết những sai phạm",
            "D": "Dùng để công kích cá nhân",
        },
        "answer": "D",
    },
    {
        "id": 26, 
        "question": "Vì sao Hồ Chí Minh dùng liền 3 cách gọi khác nhau cho tham ô, lãng phí, quan liêu (\"kẻ thù của nhân dân\", \"giặc ở trong lòng\", \"giặc nội xâm\") thay vì chỉ dùng 1 cách gọi?",
        "options": {
            "A": "Để tránh lặp từ cho văn phong sinh động hơn",
            "B": "Để nhấn mạnh tính chất nguy hiểm ở nhiều khía cạnh",
            "C": "Việc lặp lại ý bằng nhiều cách diễn đạt là một thủ pháp tu từ nhằm tăng tính thuyết phục của văn bản chính luận, không nhằm phân biệt các khía cạnh nội dung cụ thể",
            "D": "Mỗi cách gọi tương ứng với một giai đoạn phát triển của tệ nạn: \"kẻ thù\" là giai đoạn mới hình thành, \"giặc trong lòng\" là giai đoạn lan rộng, \"giặc nội xâm\" là giai đoạn nguy hiểm nhất; thể hiện một tiến trình diễn biến theo thời gian",
        },
        "answer": "B",
    },
    {
        "id": 27, 
        "question": "Trong bốn cách diễn giải sau, cách nào thể hiện đầy đủ nhất ý nghĩa của yêu cầu \"mực thước cho người ta bắt chước\" trong câu nói của Hồ Chí Minh?",
        "options": {
            "A": "Người cán bộ cần đặt lợi ích của nhân dân lên trên lợi ích cá nhân, kể cả khi phải hy sinh quyền lợi của bản thân.",
            "B": "Người cán bộ cần gần gũi với nhân dân để tạo sự tin tưởng và thuận lợi cho việc tuyên truyền, vận động.",
            "C": "Người cán bộ cần biết lắng nghe nhân dân, từ đó điều chỉnh phương pháp lãnh đạo sao cho phù hợp với thực tế.",
            "D": "Người cán bộ phải thể hiện bằng chính hành vi, đạo đức và cách làm của mình để tạo thành cơ sở cho người khác noi theo.",
        },
        "answer": "D",
    },
    {
        "id": 28, 
        "question": "Mối quan hệ giữa nhận thức đúng và hành động của người trẻ được mô tả như thế nào?",
        "options": {
            "A": "Nhận thức đúng về tư tưởng Hồ Chí Minh là điều kiện duy nhất bảo đảm người trẻ có hành động đúng đắn",
            "B": "Nhận thức đúng về tư tưởng Hồ Chí Minh là điều kiện duy nhất bảo đảm người trẻ có hành động đúng đắn",
            "C": "Nhận thức sâu sắc có thể chuyển hóa thành niềm tin, từ đó định hướng thái độ, hành vi và trách nhiệm của người sinh viên",
            "D": "Hành động thực tiễn quan trọng hơn nhận thức, bởi nhận thức chỉ có tác dụng định hướng ban đầu",
        },
        "answer": "C",
    },
    {
        "id": 29, 
        "question": "Cụm từ \"công khai ở mức độ phù hợp\" thay vì \"công khai toàn bộ\" ngụ ý điều gì về cách tiếp cận trong bối cảnh chuyển đổi số mạnh mẽ, công nghệ và môi trường số?",
        "options": {
            "A": "Việc giới hạn phạm vi công khai cho thấy giải pháp đặt yêu cầu ổn định và bảo vệ lợi ích nội bộ lên trên yêu cầu minh bạch; về lâu dài, cách tiếp cận này có thể tạo ra khoảng trống để các trường hợp nhạy cảm được viện cớ ngoại lệ nhằm hạn chế công khai",
            "B": "Có sự cân nhắc giữa yêu cầu minh bạch để phòng chống tiêu cực và nhu cầu bảo mật thông tin cá nhân/an ninh tổ chức, không phải minh bạch tuyệt đối bằng mọi giá",
            "C": "Việc không yêu cầu công khai toàn bộ cho thấy quyền xác định phạm vi thông tin được công khai cần được trao ở mức nhất định cho chủ thể trực tiếp thực hiện, bởi họ là người có khả năng đánh giá tính nhạy cảm của thông tin trong thực tế",
            "D": "Cụm từ này chỉ mang tính hình thức, không ảnh hưởng đến cách triển khai thực tế, giúp thực tế không mang tính bắt buộc tuyệt đối, khuyến khích cán bộ linh hoạt trong việc triển khai",
        },
        "answer": "B",
    },
    {
        "id": 30, 
        "question": "Hành động nào thể hiện rõ nhất việc chuyển những yêu cầu về trách nhiệm xã hội thành một hình thức hoạt động phù hợp với đặc điểm tiếp nhận thông tin của thanh niên trong môi trường số?",
        "options": {
            "A": "Chủ động sử dụng các nền tảng mạng xã hội để chia sẻ những nội dung chính thống, giải thích các vấn đề xã hội bằng ngôn ngữ dễ tiếp cận; đồng thời kiểm chứng nguồn tin trước khi đăng tải hoặc chia sẻ",
            "B": "Thường xuyên đăng tải hình ảnh, video về hoạt động cá nhân và thành tích công tác lên mạng xã hội nhằm tạo hình ảnh tích cực, qua đó khuyến khích thanh niên noi theo",
            "C": "Hạn chế sử dụng mạng xã hội trong hoạt động công vụ vì những nền tảng này dễ phát sinh thông tin sai lệch, thay vào đó tập trung vào các hình thức tuyên truyền truyền thống để bảo đảm tính chính xác",
            "D": "Thực hiện các video short trên Facebook tuyên truyền phòng, chống các hành vi vi phạm pháp luật bằng hình thức ngắn gọn, sáng tạo, dễ tiếp cận với giới trẻ; đồng thời dẫn nguồn thông tin chính thống để người xem có thể kiểm chứng",
        },
        "answer": "D",
    },
]


TOTAL_QUESTIONS = len(QUESTIONS)


# ---------------------------------------------------------------------------
# Trạng thái ván chơi (lưu trong bộ nhớ - đủ dùng cho 1 buổi thuyết trình)
# ---------------------------------------------------------------------------
def new_game_state():
    """Khởi tạo một ván chơi mới"""
    order = list(range(TOTAL_QUESTIONS))
    random.shuffle(order)  # ngẫu nhiên thứ tự hiển thị 30 câu
    return {
        "grid": initial_grid(),
        "question_order": order,          # thứ tự index (vào QUESTIONS) để hiển thị
        "used_question_ids": [],          # id các câu đã mở
        "last_perk": None,                # perk vừa quay được (để hiển thị lại nếu cần)
    }

# app.py
def initial_grid():
    """Ghi bàn cờ ban đầu, mỗi đội có 1 màu"""
    grid = []
    for r in range(ROWS):
        team = TEAM_ORDER[r % len(TEAM_ORDER)]
        grid.append([team for _ in range(COLS)])   # cả hàng r = 1 màu
    return grid

GAME = new_game_state()


def public_question(q):
    """Trả về câu hỏi KHÔNG kèm đáp án (để không lộ khi chiếu màn hình)."""
    return {
        "id": q["id"],
        "text": q["question"],
        "options": q["options"]
    }


def ranking_payload():
    """đếm số ô mỗi đội có, xếp hạng, tìm đội dẫn đầu"""
    counts = {t: 0 for t in TEAM_ORDER}
    neutral = 0
    for row in GAME["grid"]:
        for cell in row:
            if cell in counts:
                counts[cell] += 1
            else:
                neutral += 1
    sorted_teams = sorted(TEAM_ORDER, key=lambda t: counts[t], reverse=True)
    ranking = [
        {"team": t, "name": TEAMS[t]["name"], "color": TEAMS[t]["color"], "count": counts[t]}
        for t in sorted_teams
    ]
    leader = ranking[0] if ranking and ranking[0]["count"] > 0 else None
    return {"ranking": ranking, "neutral": neutral, "leader": leader}


# ---------------------------------------------------------------------------
# Routes - giao diện
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    """Render trang chính"""
    return render_template(
        "index.html",
        rows=ROWS,
        cols=COLS,
        teams=TEAMS,
        team_order=TEAM_ORDER,
        total_questions=TOTAL_QUESTIONS,
    )


# ---------------------------------------------------------------------------
# API - trạng thái chung
# ---------------------------------------------------------------------------
@app.route("/api/state")
def api_state():
    """trả toàn bộ trạng thái (bảng, câu hỏi đã dùng, xếp hạng)"""
    ordered_questions = []
    for idx in GAME["question_order"]:
        q = QUESTIONS[idx]
        ordered_questions.append(
            {
                "id": q["id"],
                "used": q["id"] in GAME["used_question_ids"],
            }
        )
    return jsonify(
        {
            "grid": GAME["grid"],
            "teams": TEAMS,
            "questions": ordered_questions,
            **ranking_payload(),
        }
    )


# ---------------------------------------------------------------------------
# API - câu hỏi
# ---------------------------------------------------------------------------
@app.route("/api/question/<int:qid>/open", methods=["POST"])
def api_open_question(qid):
    """mở 1 câu, đánh dấu đã dùng, roll perk"""
    q = next((q for q in QUESTIONS if q["id"] == qid), None)
    if q is None:
        return jsonify({"error": "Không tìm thấy câu hỏi"}), 404

    if qid not in GAME["used_question_ids"]:
        GAME["used_question_ids"].append(qid)

    perk = roll_perk()
    GAME["last_perk"] = perk

    return jsonify({"question": public_question(q), "perk": perk})


@app.route("/api/question/<int:qid>/answer")
def api_reveal_answer(qid):
    """trả đáp án đúng khi admin bấm "hiện đáp án"""
    q = next((q for q in QUESTIONS if q["id"] == qid), None)
    if q is None:
        return jsonify({"error": "Không tìm thấy câu hỏi"}), 404
    return jsonify({"answer": q["answer"]})


# ---------------------------------------------------------------------------
# API - lãnh địa (bàn cờ)
# ---------------------------------------------------------------------------
@app.route("/api/claim", methods=["POST"])
def api_claim():
    """gán 1 ô cho 1 đội (hoặc bỏ trống)"""
    data = request.get_json(force=True) or {}
    r, c, team = data.get("row"), data.get("col"), data.get("team")

    if team is not None and team not in TEAMS:
        return jsonify({"error": "Đội không hợp lệ"}), 400
    if not (isinstance(r, int) and isinstance(c, int) and 0 <= r < ROWS and 0 <= c < COLS):
        return jsonify({"error": "Toạ độ không hợp lệ"}), 400

    GAME["grid"][r][c] = team  # team=None nghĩa là thu hồi ô về trung lập
    return jsonify({"grid": GAME["grid"], **ranking_payload()})


@app.route("/api/reset", methods=["POST"])
def api_reset():
    """làm mới toàn bộ ván chơi"""
    global GAME
    GAME = new_game_state()
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(debug=True)
