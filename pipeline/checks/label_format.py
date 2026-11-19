"""CHECK 2 — Dòng nhãn YOLO: sai định dạng, ID lớp lạ, box tràn ảnh, box rỗng, box lặp.   (Script 2 trong slide)   ★★

Test:  pytest tests/test_label_format.py -q

Mỗi dòng nhãn: `id cx cy w h` (5 số, toạ độ 0–1). Trả về list[Issue]; `Issue.line` = số dòng (đếm từ 1).

| code             | severity | khi nào                                                                  |
|------------------|----------|--------------------------------------------------------------------------|
| BAD_FORMAT       | ERROR    | không đúng 5 cột số (dùng `parse_yolo_line`, bắt `ValueError`)           |
| BAD_CLASS_ID     | ERROR    | id lớp ngoài 0..len(ds.classes)-1                                        |
| BOX_ZERO         | ERROR    | w <= 0 hoặc h <= 0                                                       |
| BOX_OUT_OF_IMAGE | ERROR    | mép box vượt [0,1] quá `cfg["label_format"]["overflow_tol"]`; extra={"overflow": mức tràn} |
| DUP_BOX          | ERROR    | cùng lớp với một dòng TRƯỚC ĐÓ và IoU > `dup_box_iou`; báo ở dòng SAU    |
| BOX_TINY         | WARN     | cạnh ngắn của box (px) < `min_box_px`  (cần `ds.image_size(stem)`)       |
| BOX_HUGE         | WARN     | w*h > `max_box_frac`                                                     |

Gợi ý
- Mép trái = x - w/2, mép phải = x + w/2 (xem câu hỏi "dòng YOLO nào lỗi?" trong slide).
- Một dòng hỏng (BAD_FORMAT, BAD_CLASS_ID, BOX_ZERO) thì `continue`, đừng kiểm tiếp hình học của dòng đó.
- Dòng thiếu cột làm script của slide dừng giữa chừng: đây là lý do phải `try/except`.
- `iou_xywh(a, b)` có sẵn trong common.py.
- Ngưỡng nằm trong `cfg["label_format"]` — đừng viết cứng số vào code.
"""
from ..common import ERROR, WARN, Issue, iou_xywh, parse_yolo_line  # noqa: F401


def run(ds, cfg):
    # Lấy toàn bộ ngưỡng kiểm tra từ cấu hình, không gắn cứng ngưỡng trong code.
    limits = cfg["label_format"]
    # Gom các lỗi và cảnh báo để trả về cho pipeline.
    issues = []
    # Duyệt từng file nhãn; Dataset đã sắp xếp file theo tên.
    for label_file in ds.label_files():
        # Stem là tên ảnh không có phần mở rộng, dùng để tra ảnh và ghi Issue.image.
        stem = label_file.stem
        # Lưu box hợp lệ trước đó theo class ID, riêng cho file ảnh hiện tại.
        previous = {}
        # Mỗi phần tử gồm số dòng gốc và nội dung; dòng trống đã bị bỏ nhưng số dòng không đổi.
        for line_no, text in ds.read_label_lines(stem) or []:
            # Thử chuyển dòng YOLO thành ID lớp, tâm box, chiều rộng và chiều cao.
            try:
                class_id, cx, cy, width, height = parse_yolo_line(text)
            # Dòng sai có thể gây ValueError; class ID vô cực cũng có thể gây OverflowError.
            except (ValueError, OverflowError) as exc:
                # Ghi lỗi định dạng cùng số dòng gốc và thông tin parser cung cấp.
                issues.append(Issue("label_format", ERROR, "BAD_FORMAT", stem, f"dòng nhãn sai định dạng: {exc}", line=line_no))
                # Không kiểm tra hình học khi không parse được dòng.
                continue
            # Class ID phải là chỉ số hợp lệ trong danh sách lớp của dataset.
            if not 0 <= class_id < len(ds.classes):
                # Ghi lỗi ID lớp, giữ nguyên số dòng nguồn.
                issues.append(Issue("label_format", ERROR, "BAD_CLASS_ID", stem, f"ID lớp {class_id} nằm ngoài danh sách lớp", line=line_no))
                # Không kiểm tra hình học khi ID lớp sai.
                continue
            # Box có chiều rộng hoặc chiều cao bằng 0 hay âm không có hình học hợp lệ.
            if width <= 0 or height <= 0:
                # Ghi lỗi box rỗng.
                issues.append(Issue("label_format", ERROR, "BOX_ZERO", stem, "Box rộng hoặc cao bằng 0", line=line_no))
                # Bỏ qua các kiểm tra tiếp theo cho box không hợp lệ.
                continue
            # Tính tọa độ mép trái và mép trên từ tâm và kích thước box.
            left, top = cx - width / 2, cy - height / 2
            # Tính tọa độ mép phải và mép dưới.
            right, bottom = cx + width / 2, cy + height / 2
            # Lấy phần tràn lớn nhất ở bốn cạnh; nếu không tràn thì giá trị là 0.
            overflow = max(0.0, -left, -top, right - 1.0, bottom - 1.0)
            # Chỉ báo lỗi khi mức tràn lớn hơn ngưỡng trong cấu hình.
            if overflow > limits["overflow_tol"]:
                # Lưu mức tràn lớn nhất vào extra để báo cáo có thể hiển thị chi tiết.
                issues.append(Issue("label_format", ERROR, "BOX_OUT_OF_IMAGE", stem, "Box tràn ra ngoài ảnh", line=line_no, extra={"overflow": overflow}))
            # Tạo box dạng (cx, cy, w, h), đúng định dạng mà hàm IoU nhận.
            box = (cx, cy, width, height)
            # Lấy danh sách box trước của cùng lớp; tạo danh sách rỗng nếu chưa có.
            prior_boxes = previous.setdefault(class_id, [])
            # Tìm xem box hiện tại có IoU vượt ngưỡng với box trước cùng lớp không.
            if any(iou_xywh(box, prior) > limits["dup_box_iou"] for prior in prior_boxes):
                # Báo trùng tại dòng hiện tại, tức dòng xuất hiện sau box đã có.
                issues.append(Issue("label_format", ERROR, "DUP_BOX", stem, "Box trùng với box trước đó cùng lớp", line=line_no))
            # Lưu box hiện tại để các dòng sau có thể kiểm tra trùng với nó.
            prior_boxes.append(box)
            # Lấy kích thước ảnh theo thứ tự (rộng, cao), nếu ảnh mở được.
            size = ds.image_size(stem)
            # Đổi hai cạnh box sang pixel, lấy cạnh ngắn nhất và so với ngưỡng cảnh báo.
            if size and min(width * size[0], height * size[1]) < limits["min_box_px"]:
                # Báo box nhỏ dưới dạng cảnh báo, không chặn pipeline.
                issues.append(Issue("label_format", WARN, "BOX_TINY", stem, "Cạnh ngắn của box nhỏ hơn ngưỡng pixel", line=line_no))
            # Diện tích chuẩn hóa của box là w*h; chỉ cảnh báo khi vượt ngưỡng cấu hình.
            if width * height > limits["max_box_frac"]:
                # Báo box chiếm diện tích quá lớn dưới dạng cảnh báo.
                issues.append(Issue("label_format", WARN, "BOX_HUGE", stem, "Box chiếm diện tích quá lớn", line=line_no))
    # Trả danh sách lỗi và cảnh báo cho caller.
    return issues
