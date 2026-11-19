"""CHECK 6 — Ý kiến thứ hai: so nhãn với một model LỚN HƠN (yolo26l).   ★★★ (khó nhất, đáng điểm nhất)

Test:  pytest tests/test_second_opinion.py -q

Máy kiểm quy tắc, người kiểm ý nghĩa (slide). Các lỗi như thiếu nhãn / gán nhầm lớp hợp lệ / box lỏng
KHÔNG bắt được bằng quy tắc cú pháp. Ta nhờ một model mạnh hơn "nhìn lại" và CHỈ CẢNH BÁO (model cũng có thể sai):
những ảnh bị cờ sẽ vào hàng đợi cho NGƯỜI duyệt.

`preds[stem]` = list `[id_lớp, conf, cx, cy, w, h]` của model (lấy qua `get_preds(ds, cfg, "checker")` nếu preds=None).
`L = ds.valid_boxes(stem)` = list `(id_lớp, cx, cy, w, h)` của nhãn (đã bỏ dòng hỏng).
Ngưỡng ở `cfg["second_opinion"]`: conf, min_area_px, fp_conf, iou_missing, iou_match, iou_loose.

Thuật toán gợi ý, với từng ảnh (bỏ qua ảnh không có trong preds hoặc không có file nhãn):
  P = dự đoán có conf >= conf  VÀ diện tích px (w*W * h*H) >= min_area_px
  Với mỗi dự đoán r trong P: lấy các nhãn có IoU(r, nhãn) >= iou_missing  (cands)
   - không có cands                            -> POSSIBLE_MISSING     (model thấy vật mà nhãn không có box)
   - có cands cùng lớp, tốt nhất IoU < iou_loose -> POSSIBLE_LOOSE_BOX  (đúng vật, box lỏng/lệch)
   - không có cands cùng lớp, nhưng cands tốt nhất IoU >= iou_match (khác lớp) -> POSSIBLE_WRONG_CLASS
  Với mỗi dòng nhãn hợp lệ: nếu IoU với MỌI dự đoán (conf >= fp_conf, không lọc diện tích) đều < iou_missing
                                             -> POSSIBLE_FALSE_POS  (box nhãn không khớp vật nào model thấy; Issue.line = số dòng)

Chi tiết các ca biên (test kiểm đúng các ca này)
- `cands` gồm nhãn MỌI lớp có IoU >= iou_missing; "tốt nhất cùng lớp" = cands cùng lớp có IoU lớn nhất; "tốt nhất khác lớp" tương tự với cands khác lớp.
- Thứ tự quyết định cho mỗi dự đoán: (1) cands rỗng -> MISSING. (2) có cands cùng lớp: IoU tốt nhất < iou_loose -> LOOSE_BOX, ngược lại KHÔNG cờ
  (nhãn đúng lớp đã phủ vật này, kể cả khi còn nhãn khác lớp chồng lên). (3) không có cands cùng lớp: nếu IoU tốt nhất khác lớp >= iou_match -> WRONG_CLASS;
  nếu chỉ có khác lớp với IoU trong [iou_missing, iou_match) -> không cờ gì (mơ hồ: để cho FALSE_POS / lần duyệt khác).
- Một dự đoán sinh tối đa MỘT issue (MISSING / LOOSE_BOX / WRONG_CLASS); một ảnh có thể có nhiều issue.
- Thứ tự issue: theo `ds.image_files()` rồi theo thứ tự dự đoán trong `preds[stem]`, cuối cùng là các FALSE_POS theo số dòng; `Issue.image` = stem, `Issue.line` chỉ đặt cho FALSE_POS.

Lưu ý số dòng: dùng `ds.read_label_lines(stem)` (giữ số dòng gốc, kể cả dòng hỏng/trống) để lấy `Issue.line`; `valid_boxes` KHÔNG giữ số dòng.

Tất cả severity WARN; `Issue.extra` nên có {"conf": ...} hoặc {"iou": ...} (hàng đợi duyệt dùng conf để xếp ưu tiên).

Gợi ý
- `iou_xywh` có sẵn. Dòng nhãn hỏng không được làm script chết (dùng `ds.valid_boxes` và `parse_yolo_line` trong try).
- Kết quả phụ thuộc mạnh vào ngưỡng: calibrate chúng ở Bước 3 thay vì đoán.
"""
from math import isfinite

from ..common import WARN, Issue, iou_xywh, parse_yolo_line  # noqa: F401
from ..model_cache import get_preds  # noqa: F401


def run(ds, cfg, preds=None):
    # Đọc ngưỡng một lần; các quyết định bên dưới đều dùng đúng giá trị trong config.
    limits = cfg["second_opinion"]
    # Khi caller không truyền dự đoán, lấy cache/model checker qua interface dùng chung.
    predictions = get_preds(ds, cfg, "checker") if preds is None else preds
    # Tập hợp cảnh báo theo đúng thứ tự ảnh, dự đoán, rồi dòng nhãn như docstring quy định.
    issues = []

    # Dataset.image_files() đã sắp xếp theo tên để thứ tự kết quả ổn định.
    for image_path in ds.image_files():
        stem = image_path.stem
        # Không thể đánh giá ảnh nếu model không có khóa dự đoán hoặc file nhãn không tồn tại.
        if stem not in predictions:
            continue
        label_lines = ds.read_label_lines(stem)
        if label_lines is None:
            continue

        # Parse nhãn thủ công để giữ số dòng gốc cho FALSE_POS; cách lọc khớp valid_boxes().
        labels = []
        for line_no, text in label_lines:
            try:
                class_id, cx, cy, width, height = parse_yolo_line(text)
            except (ValueError, OverflowError):
                # Dòng hỏng đã được check khác báo; không để nó làm check này dừng.
                continue
            if 0 <= class_id < len(ds.classes):
                labels.append((line_no, class_id, (cx, cy, width, height)))

        # Chuẩn hóa từng dự đoán thành (class_id, confidence, box), bỏ hàng hỏng hoặc phi hữu hạn.
        valid_predictions = []
        for row in predictions.get(stem) or []:
            try:
                if len(row) != 6:
                    continue
                values = [float(value) for value in row]
                if not all(isfinite(value) for value in values) or not values[0].is_integer():
                    continue
                class_id = int(values[0])
                confidence = values[1]
                box = tuple(values[2:6])
                if box[2] <= 0 or box[3] <= 0:
                    continue
            except (TypeError, ValueError, OverflowError):
                continue
            valid_predictions.append((class_id, confidence, box))

        # Chỉ nhóm dự đoán conf cao và đủ diện tích dùng để tìm thiếu nhãn/lệch box/nhầm lớp.
        image_size = ds.image_size(stem)
        large_predictions = []
        if image_size is not None:
            image_width, image_height = image_size
            for prediction in valid_predictions:
                _, confidence, (_, _, width, height) = prediction
                area_px = (width * image_width) * (height * image_height)
                if confidence >= limits["conf"] and area_px >= limits["min_area_px"]:
                    large_predictions.append(prediction)

        # So từng dự đoán đủ tin cậy với nhãn ở mọi lớp; mỗi dự đoán sinh tối đa một cảnh báo.
        for class_id, confidence, box in large_predictions:
            overlaps = [(label_class, iou_xywh(box, label_box)) for _, label_class, label_box in labels]
            candidates = [(label_class, overlap) for label_class, overlap in overlaps if overlap >= limits["iou_missing"]]

            # Không có nhãn nào phủ dự đoán đủ mức tối thiểu: có khả năng đang thiếu nhãn.
            if not candidates:
                issues.append(Issue(
                    "second_opinion", WARN, "POSSIBLE_MISSING", stem,
                    f"Model thấy vật lớp {class_id} nhưng không có box nhãn khớp (conf {confidence:.3f})",
                    extra={"conf": confidence, "iou": 0.0},
                ))
                continue

            # Tìm IoU cao nhất trong các nhãn cùng lớp; nhãn khác lớp được xét riêng sau.
            same_class = [overlap for label_class, overlap in candidates if label_class == class_id]
            if same_class:
                best_same_iou = max(same_class)
                # Đã tìm thấy đúng lớp nhưng box khớp yếu hơn ngưỡng loose: cảnh báo box lỏng.
                if best_same_iou < limits["iou_loose"]:
                    issues.append(Issue(
                        "second_opinion", WARN, "POSSIBLE_LOOSE_BOX", stem,
                        f"Box nhãn cùng lớp khớp lỏng với dự đoán (IoU {best_same_iou:.3f})",
                        extra={"conf": confidence, "iou": best_same_iou},
                    ))
                # Có nhãn cùng lớp đạt ngưỡng loose thì bỏ qua, kể cả lớp khác cũng chồng lấp.
                continue

            # Chỉ khi không có nhãn cùng lớp mới xét nhãn khác lớp để tránh báo nhầm lớp.
            other_classes = [overlap for label_class, overlap in candidates if label_class != class_id]
            if other_classes:
                best_other_iou = max(other_classes)
                # Nhãn khác lớp phải đạt iou_match; khoảng IoU mơ hồ thì cố ý không gắn cờ.
                if best_other_iou >= limits["iou_match"]:
                    issues.append(Issue(
                        "second_opinion", WARN, "POSSIBLE_WRONG_CLASS", stem,
                        f"Dự đoán lớp {class_id} khớp box nhãn lớp khác (IoU {best_other_iou:.3f})",
                        extra={"conf": confidence, "iou": best_other_iou},
                    ))

        # FALSE_POS dùng ngưỡng fp_conf riêng: không áp ngưỡng conf hay min_area_px ở trên.
        fp_predictions = [p for p in valid_predictions if p[1] >= limits["fp_conf"]]
        for line_no, label_class, label_box in labels:
            # Tìm dự đoán gần nhãn nhất trong toàn bộ predictions đạt fp_conf.
            overlaps = [(iou_xywh(label_box, box), confidence) for _, confidence, box in fp_predictions]
            best_iou = max((overlap for overlap, _ in overlaps), default=0.0)
            # Chỉ khi mọi IoU đều dưới iou_missing mới nghi ngờ dòng nhãn là box thừa.
            if best_iou < limits["iou_missing"]:
                extra = {"iou": best_iou}
                if overlaps:
                    # Lưu conf của dự đoán gần nhất để hàng đợi review có thêm tín hiệu ưu tiên.
                    _, best_conf = max(overlaps, key=lambda pair: pair[0])
                    extra["conf"] = best_conf
                issues.append(Issue(
                    "second_opinion", WARN, "POSSIBLE_FALSE_POS", stem,
                    f"Box nhãn lớp {label_class} không khớp dự đoán nào (IoU lớn nhất {best_iou:.3f})",
                    line=line_no, extra=extra,
                ))

    # Tất cả kết quả đều là WARN để chuyển sang hàng đợi người duyệt, không tự sửa nhãn.
    return issues
