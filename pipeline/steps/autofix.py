"""BƯỚC 2/4 — Sửa tự động những lỗi bắt buộc mà máy sửa được AN TOÀN.   ★★

Test:  pytest tests/test_autofix.py -q

`fix(ds, issues, cfg) -> list[dict]`: duyệt `issues` (chỉ lỗi severity ERROR), sửa thẳng vào thư mục `ds`,
và trả về danh sách thay đổi; mỗi phần tử có khoá: image, line, action, before, after
(đây chính là file `03_fixes.csv` — bằng chứng pipeline đã làm gì, người có thể kiểm lại).

| code lỗi                                       | cách sửa                                    | action           |
|------------------------------------------------|---------------------------------------------|------------------|
| BAD_FORMAT, BAD_CLASS_ID, BOX_ZERO, DUP_BOX    | xoá dòng đó khỏi file nhãn                  | "drop_line"      |
| BOX_OUT_OF_IMAGE                               | cắt box về trong [0,1] (giữ nguyên lớp)     | "clip_box"       |
| MISSING_LABEL_FILE                             | KHÔNG sửa file (máy không thể bịa nhãn): ghi 1 dòng fix, before="(không có file)", after="chuyển người gán" | "needs_label" |
| BAD_CLASS_NAME                                 | ghi lại `names` trong data.yaml đúng `cfg["classes"]` | "rename_classes" |
| DUP_IMAGE_*, LEAK_TEST, CORRUPT_IMAGE, BAD_SIZE| xoá ảnh + nhãn khỏi `ds`                    | "remove_image"   |

Bẫy cần nghĩ tới (có test cho từng cái)
- Một file có NHIỀU dòng lỗi: số dòng trong `issues` là số dòng GỐC. Nếu xoá từng dòng một thì số dòng lệch.
  Gom theo file, rồi ghi lại MỘT lần.
- Sau khi cắt, box có thể không còn diện tích (nằm hẳn ngoài ảnh): lúc đó xoá dòng thay vì ghi box rỗng.
- Một dòng có 2 lỗi (vd. BOX_OUT_OF_IMAGE + DUP_BOX): xoá dòng thắng, chỉ ghi 1 fix `drop_line`, không ghi thêm `clip_box`. Dòng trống ở giữa file vẫn đếm vào số dòng gốc.
- Ảnh vừa bị xoá (DUP_IMAGE_*...) mà còn issue dòng của chính nó: bỏ qua êm, không được báo lỗi/chết.
- Không động tới lỗi WARN (cảnh báo là việc của người). Không sửa file ở `data/raw/` — chỉ sửa `ds`.
- Chạy lần 2 trên dữ liệu đã sửa phải không làm gì thêm (idempotent) — NGOẠI LỆ duy nhất: `needs_label` được ghi lại mỗi lần còn lỗi `MISSING_LABEL_FILE` (vì ảnh vẫn chưa có nhãn).

- `needs_label` KHÔNG tạo file nhãn rỗng (rỗng = "ảnh nền", khác với "chưa gán"). `review_queue` sẽ đẩy ảnh này lên đầu hàng đợi cho người.

Gợi ý: `yaml.safe_load / safe_dump`.
"""
from collections import defaultdict  # noqa: F401

import yaml  # noqa: F401

from ..common import ERROR, parse_yolo_line  # noqa: F401


def fix(ds, issues, cfg):
    # Chỉ lập kế hoạch sửa cho ERROR; WARN luôn để người xem.
    fixes = []
    line_codes = defaultdict(lambda: defaultdict(set))
    remove_images = set()
    needs_labels = set()
    rename_classes = False
    drop_codes = {"BAD_FORMAT", "BAD_CLASS_ID", "BOX_ZERO", "DUP_BOX"}
    remove_codes = {"LEAK_TEST", "CORRUPT_IMAGE", "BAD_SIZE"}

    # Gom lỗi trước khi đụng vào file để giữ nguyên số dòng gốc.
    for issue in issues:
        if issue.severity != ERROR:
            continue
        if issue.code.startswith("DUP_IMAGE_") or issue.code in remove_codes:
            remove_images.add(issue.image)
        elif issue.code == "MISSING_LABEL_FILE":
            needs_labels.add(issue.image)
        elif issue.code == "BAD_CLASS_NAME":
            rename_classes = True
        elif issue.code in drop_codes | {"BOX_OUT_OF_IMAGE"} and issue.line is not None:
            line_codes[issue.image][int(issue.line)].add(issue.code)

    # Xóa ảnh và nhãn trong ds; một ảnh chỉ tạo một bản ghi dù có nhiều lỗi loại ảnh.
    for stem in sorted(remove_images):
        image_paths = [p for p in ds.image_files() if p.stem == stem]
        label_path = ds.label_path(stem)
        targets = image_paths + ([label_path] if label_path.exists() else [])
        if not targets:
            continue
        before = ";".join(p.name for p in targets)
        for path in targets:
            path.unlink(missing_ok=True)
        fixes.append(dict(image=stem, line=None, action="remove_image", before=before, after="(đã xóa khỏi ds)"))

    # Chuyển ảnh chưa có nhãn cho người gán, tuyệt đối không tạo file .txt rỗng.
    for stem in sorted(needs_labels - remove_images):
        if ds.image_path(stem) is None or ds.label_path(stem).exists():
            continue
        fixes.append(dict(image=stem, line=None, action="needs_label", before="(không có file)", after="chuyển người gán"))

    # Sửa riêng names trong data.yaml và giữ lại các khóa cấu hình khác nếu có.
    if rename_classes:
        yaml_path = ds.yaml_path
        try:
            document = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError):
            document = {}
        if not isinstance(document, dict):
            document = {}
        classes = list(cfg["classes"])
        old_names = document.get("names", "(thiếu names)")
        if isinstance(old_names, list):
            normalized_names = dict(enumerate(old_names))
        elif isinstance(old_names, dict):
            try:
                normalized_names = {int(key): value for key, value in old_names.items()}
            except (TypeError, ValueError):
                normalized_names = {}
        else:
            normalized_names = {}
        if normalized_names != dict(enumerate(classes)):
            document["names"] = classes
            yaml_path.write_text(yaml.safe_dump(document, allow_unicode=True, sort_keys=False), encoding="utf-8")
            fixes.append(dict(image="data.yaml", line=None, action="rename_classes", before=str(old_names), after=str(classes)))

    # Sửa từng file nhãn đúng một lần, xử lý các line theo số dòng ban đầu.
    for stem in sorted(line_codes):
        if stem in remove_images:
            continue
        label_path = ds.label_path(stem)
        if not label_path.exists():
            continue
        raw_lines = label_path.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
        rewritten = []
        changed = False
        for line_no, raw_line in enumerate(raw_lines, 1):
            body = raw_line.rstrip("\r\n")
            ending = raw_line[len(body):]
            codes = line_codes[stem].get(line_no, set())
            if not codes:
                rewritten.append(raw_line)
                continue
            # Xóa dòng thắng mọi sửa khác trên cùng dòng, ví dụ DUP_BOX + BOX_OUT_OF_IMAGE.
            if codes & drop_codes:
                fixes.append(dict(image=stem, line=line_no, action="drop_line", before=body, after=""))
                changed = True
                continue
            if "BOX_OUT_OF_IMAGE" not in codes:
                rewritten.append(raw_line)
                continue
            # Parse lại dòng để tính tọa độ cắt; issue lỗi thời hoặc dòng hỏng được bỏ qua an toàn.
            parts = body.split()
            try:
                class_id, cx, cy, width, height = parse_yolo_line(body)
            except (ValueError, OverflowError):
                rewritten.append(raw_line)
                continue
            left, top = max(0.0, cx - width / 2), max(0.0, cy - height / 2)
            right, bottom = min(1.0, cx + width / 2), min(1.0, cy + height / 2)
            clipped_width, clipped_height = right - left, bottom - top
            # Box nằm hẳn ngoài ảnh sau khi cắt thì phải xóa, không ghi kích thước âm hoặc 0.
            if clipped_width <= 0 or clipped_height <= 0:
                fixes.append(dict(image=stem, line=line_no, action="drop_line", before=body, after=""))
                changed = True
                continue
            clipped = ((left + right) / 2, (top + bottom) / 2, clipped_width, clipped_height)
            if clipped == (cx, cy, width, height):
                rewritten.append(raw_line)
                continue
            # Giữ nguyên token class ID, còn bốn tọa độ được ghi với độ chính xác đủ để tái đọc.
            after = " ".join([parts[0], *(format(value, ".12g") for value in clipped)])
            fixes.append(dict(image=stem, line=line_no, action="clip_box", before=body, after=after))
            rewritten.append(after + ending)
            changed = True
        # Ghi file một lần sau khi mọi số dòng gốc đã được xử lý.
        if changed:
            label_path.write_text("".join(rewritten), encoding="utf-8")

    return fixes
