"""BƯỚC 4 — Cửa chặn: quyết định Release / Hold / Rework.   ★

Test:  pytest tests/test_gate.py -q

Cây quyết định Day 07 (slide Day 09: "Lỗi bắt buộc chặn pipeline; lỗi cảnh báo chuyển người xem"):

  còn ≥ 1 lỗi bắt buộc (severity ERROR)                          -> "Rework"
  không còn lỗi bắt buộc, nhưng tỉ lệ ẢNH còn cảnh báo
      >= cfg["gate"]["warn_ratio_hold"]                          -> "Hold"
  còn lại                                                        -> "Release"

Tỉ lệ cảnh báo = (số ẢNH khác nhau có ≥ 1 cảnh báo) / (tổng số ảnh).  Chú ý:
- chỉ đếm issue có `image` nằm trong `image_stems` (bỏ "<dataset>", "data.yaml");
- bỏ qua ảnh nằm trong `reviewed` (người đã xem, cảnh báo của ảnh đó coi như đã xử lý) — nhưng LỖI BẮT BUỘC thì không bao giờ được bỏ qua;
- mẫu số là số ảnh, không phải số issue.

Trả về dict: decision, n_errors, n_warn_images, n_images, warn_ratio (làm tròn 4 chữ số), reasons (list[str], giải thích bằng tiếng Việt, có số liệu).
"""
from ..common import ERROR, WARN  # noqa: F401


def decide(issues, image_stems, cfg, reviewed=frozenset()):
    # Chuẩn hóa danh sách stem thành tập để so khớp và đếm mỗi ảnh đúng một lần.
    images = set(image_stems)
    # Ảnh đã review được loại khỏi phép đếm cảnh báo.
    reviewed_images = set(reviewed or ())
    # Đếm lỗi bắt buộc theo issue; lỗi không bị loại dù ảnh đã review.
    n_errors = 0
    # Lưu stem ảnh có cảnh báo để nhiều WARN trên cùng ảnh chỉ tính một lần.
    warn_images = set()
    # Xét từng issue một lần để hỗ trợ cả list lẫn iterable.
    for issue in issues:
        # ERROR luôn chặn phát hành, không phụ thuộc ảnh có trong dataset hay đã review.
        if issue.severity == ERROR:
            n_errors += 1
        # Chỉ đếm WARN trên ảnh thuộc dataset và chưa được review.
        elif issue.severity == WARN and issue.image in images and issue.image not in reviewed_images:
            warn_images.add(issue.image)
    # Số ảnh cảnh báo là số stem duy nhất; mẫu số là tổng số ảnh trong dataset.
    n_warn_images, n_images = len(warn_images), len(images)
    # Dataset rỗng có tỷ lệ 0 để tránh chia cho 0.
    raw_warn_ratio = n_warn_images / n_images if n_images else 0.0
    # Làm tròn tỷ lệ chỉ để trả về; quyết định vẫn dùng tỷ lệ chưa làm tròn.
    warn_ratio = round(raw_warn_ratio, 4)
    # Đọc ngưỡng Hold từ config.
    threshold = cfg["gate"]["warn_ratio_hold"]
    # Lỗi bắt buộc được xét trước cảnh báo nên luôn dẫn tới Rework.
    if n_errors:
        decision = "Rework"
        reasons = [f"Còn {n_errors} lỗi bắt buộc; ưu tiên Rework. Cảnh báo ở {n_warn_images}/{n_images} ảnh ({raw_warn_ratio:.2%}), ngưỡng Hold là {threshold:.2%}."]
    # Không có ERROR: tỷ lệ đạt hoặc vượt ngưỡng thì cần người xem thêm.
    elif raw_warn_ratio >= threshold:
        decision = "Hold"
        reasons = [f"Không còn lỗi bắt buộc; cảnh báo ở {n_warn_images}/{n_images} ảnh ({raw_warn_ratio:.2%}), đạt hoặc vượt ngưỡng Hold {threshold:.2%}."]
    # Nếu không rơi vào hai trường hợp trên, dữ liệu được Release.
    else:
        decision = "Release"
        reasons = [f"Không còn lỗi bắt buộc; cảnh báo ở {n_warn_images}/{n_images} ảnh ({raw_warn_ratio:.2%}), dưới ngưỡng Hold {threshold:.2%}."]
    # Trả quyết định và toàn bộ số liệu theo interface trong docstring.
    return {
        "decision": decision,
        "n_errors": n_errors,
        "n_warn_images": n_warn_images,
        "n_images": n_images,
        "warn_ratio": warn_ratio,
        "reasons": reasons,
    }
