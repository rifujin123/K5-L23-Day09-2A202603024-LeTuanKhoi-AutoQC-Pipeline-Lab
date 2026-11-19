# Ghi chú tiến độ để tổng hợp `REPORT.md`

Cập nhật: 2026-11-19
Mục đích: lưu trạng thái đã làm và số liệu đã quan sát. Đây là ghi chú làm việc; chưa thay thế `submission/REPORT.md`.

## Tiến độ theo checkpoint

| Checkpoint | Trạng thái hiện tại | Ghi chú |
|---|---|---|
| CP1 — Chuẩn bị | Môi trường `.venv` Python 3.12 chạy được full suite | Đã đọc hướng dẫn dữ liệu; có thể tự đối chiếu các mục CP1 còn lại trong checklist. |
| CP2 — 4 module | Hoàn thành phần code và kiểm tra | Bốn test mục tiêu xanh; full suite **79 passed** bằng `.venv` Python 3.12. |
| CP3 — Calibration | Đã chọn ngưỡng | Người dùng quyết định giữ `phash_dist=10`, `conf=0.75` sau khi xem các cặp; cần ghi rõ đánh đổi bỏ sót. |
| CP4 — Chạy pipeline | Lần 10/0.75: Release | `clean_v1` hiện có 202 ảnh; cần đánh giá thêm các ảnh trùng bị bỏ sót. |
| CP5 — Báo cáo/nộp | Chưa làm | `submission/REPORT.md` vẫn là mẫu có TODO; train chưa chạy. |

## Những việc đã làm và kết quả test

| Module | Việc đã làm | Lệnh / kết quả | Thời gian test |
|---|---|---|---:|
| `label_format` | Kiểm tra định dạng, ID lớp, box, trùng lặp; giữ số dòng nguồn; ngưỡng lấy từ config. | `python -m pytest tests/test_label_format.py -q` — **14 passed** | 0.37 s |
| `gate` | Đếm ảnh có cảnh báo duy nhất; áp thứ tự `Rework` → `Hold` → `Release`; trả số liệu và lý do. | `python -m pytest tests/test_gate.py -q` — **10 passed** | 0.03 s |
| `autofix` | Xóa dòng/ảnh lỗi, cắt box, sửa names, chuyển ảnh thiếu nhãn cho người gán; không sửa WARN. | `python -m pytest tests/test_autofix.py -q` — **11 passed** | 0.38 s |
| `second_opinion` | So sánh dự đoán model với nhãn, tạo WARN cho thiếu nhãn/box lỏng/nhầm lớp/box thừa; giữ số dòng gốc. | `python -m pytest tests/test_second_opinion.py -q` — **15 passed** | 0.35 s |

**Bốn test module mục tiêu:** 50 ca qua; tổng thời gian pytest báo là **1.13 giây**. **Full suite:** 79 passed trong **39.69 giây** bằng `.venv` Python 3.12. Đây là thời gian thực thi test, không phải tổng thời gian làm bài. Không có mốc bắt đầu đáng tin cậy để tính thời lượng triển khai; không ghi ước lượng trong GUIDE thành thời gian thực tế.

Lần chạy đầu của `test_label_format` bị `PermissionError` khi pytest tạo thư mục tạm/cache, trước khi các assertion chạy. Chạy lại với quyền truy cập cần thiết cho kết quả **14 passed**. Đây là vấn đề môi trường chạy test, không phải test logic thất bại.

Lần đầu full suite dừng khi collection `tests/test_duplicates.py` vì `ModuleNotFoundError: imagehash`. Dependency đã có trong `requirements.txt`, nhưng chưa cài cho Python 3.14 mặc định; `docs/SETUP.md` hỗ trợ Python 3.9–3.13. Khắc phục bằng `.venv` Python 3.12 và cài `requirements.txt` vào đó; sau đó full suite đạt **79 passed**. Dùng `.\.venv\Scripts\python.exe` trực tiếp: venv hiện không có script `Activate.ps1` do bước `ensurepip` khi tạo môi trường bị lỗi.

## Trạng thái dữ liệu đã quan sát

- `data/raw/images`: **224 ảnh**.
- `data/raw/labels`: **218 file nhãn**; **6 ảnh chưa có file nhãn**, không có label stem mồ côi.
- Sáu ảnh chưa có nhãn: `img_0031`, `img_0053`, `img_0126`, `img_0135`, `img_0170`, `img_0219`.
- Pipeline chạy trên bản sao `work/run/ds`; `data/raw` là đầu vào. Các test module dùng fixture riêng.
- Đã có báo cáo trong `submission/reports/` và bản Release `submission/export/clean_v1/` của lần 10/0.75; calibration đã có kết quả sweep. Chưa có kết quả train.

## Kết quả chạy pipeline trên raw — lần cũ 16 / 0.6

- Chạy với `phash_dist=16`, `conf=0.6`; tổng thời gian pipeline báo **8.5 giây**.
- Intake nhận **193/224 ảnh**, loại **31 ảnh**. QC vòng 1 trên tập được nhận báo **36 lỗi bắt buộc và 149 cảnh báo**.
- Autofix ghi **35 bản ghi** vào `03_fixes.csv`; đây là số bản ghi hành động, bao gồm cả chuyển người gán, không đồng nghĩa 35 file được sửa.
- Vòng 2 còn **6 lỗi bắt buộc**, hàng đợi gồm **121 ảnh**. Người duyệt mô phỏng đã duyệt **80 ảnh** trong ngân sách 80.
- Gate vòng cuối: **0 lỗi bắt buộc**, **34/193 ảnh** còn cảnh báo chưa được tính là đã duyệt, tỷ lệ **17.62%** ≥ ngưỡng **10%** → **Hold**.
- Manifest của lần đó ghi **193 ảnh**; đây là **bản nháp** theo quyết định Hold. Các file báo cáo và export mặc định đã bị thay bằng lần chạy 16/0.75.
- Cần mở xem các cặp bị đánh dấu trùng trên raw, đọc báo cáo theo mã lỗi và xử lý các cảnh báo còn lại trước khi kết luận chất lượng dữ liệu. Kết quả train chưa có.
- Cấu hình lần này có SHA-1 `eb7d1f3f1756f5262960d5e1a294d5d4f930dd2f`. Note này lưu số liệu tổng hợp, không lưu toàn bộ các file chi tiết cũ.

## Kết quả chạy pipeline trên raw — lần trước 16 / 0.75

| Chỉ số | Lần 16 / 0.6 | Lần 16 / 0.75 |
|---|---:|---:|
| Ảnh được nhận / ảnh raw | 193 / 224 | 193 / 224 |
| Ảnh bị loại ở intake | 31 | 31 |
| QC vòng 1: lỗi bắt buộc / cảnh báo | 36 / 149 | 36 / 119 |
| Bản ghi autofix | 35 | 35 |
| Vòng 2: lỗi bắt buộc / ảnh trong hàng đợi | 6 / 121 | 6 / 104 |
| Ảnh được duyệt mô phỏng / ngân sách | 80 / 80 | 80 / 80 |
| Gate: lỗi bắt buộc / ảnh cảnh báo chưa duyệt | 0 / 34 | 0 / 14 |
| Tỷ lệ ảnh cảnh báo chưa duyệt | 34/193 = 17.62% | 14/193 = 7.25% |
| Quyết định | Hold | Release |
| Thời gian pipeline | 8.5 giây | 6.4 giây |

Lần 16/0.75 có SHA-1 config `db7d5651ca294c54b7a2b6b78eae11c526f8fae6`; báo cáo và manifest mặc định đã được thay bởi lần 10/0.75. Số cảnh báo và thứ tự hàng đợi có thể thay đổi theo ngưỡng; chưa xác định các cảnh báo nào thực sự được sửa hoặc bị lọc chỉ từ số tổng. Trên calib, `conf=0.75` bỏ sót 1/8 ca thiếu box và 4/5 ca box lỏng; Release theo gate không chứng minh mọi nhãn đều đúng.

## So sánh ngưỡng pHash — cùng conf 0.75

| Chỉ số | pHash 16 | pHash 10 |
|---|---:|---:|
| Ảnh nhận / ảnh raw | 193 / 224 | 202 / 224 |
| Ảnh bị loại | 31 | 22 |
| QC vòng 1: lỗi / cảnh báo | 36 / 119 | 36 / 123 |
| Bản ghi autofix | 35 | 35 |
| Vòng 2: lỗi / ảnh trong hàng đợi | 6 / 104 | 6 / 108 |
| Ảnh duyệt mô phỏng / ngân sách | 80 / 80 | 80 / 80 |
| Gate: lỗi / ảnh cảnh báo chưa duyệt | 0 / 14 | 0 / 18 |
| Tỷ lệ cảnh báo chưa duyệt | 7.25% | 8.91% |
| Quyết định | Release | Release |
| Thời gian pipeline | 6.4 giây | 7.6 giây |

Lần 10/0.75: `08_summary.json` và manifest xác nhận Release, **202 ảnh xuất**, 80 ảnh đã duyệt; SHA-1 config `0721bc01546f92f38a87b933d4e66bf0095a34ea`. Manifest lưu danh sách ảnh và nhãn, không sao chép ảnh. So với ngưỡng 16, intake giữ thêm 9 ảnh; số liệu này chưa xác nhận danh tính hay chất lượng từng ảnh. Trên calib, near duplicate ở 10 bắt 4/6, ở 16 bắt 5/6. Người dùng xác nhận `img_0084`–`img_0074` là cùng ảnh (pHash 16); đã kiểm manifest và **cả hai đều nằm trong export ngưỡng 10**. Chưa xử lý riêng cặp này; đây là điểm mù đã biết của bản Release hiện tại.

### Thống kê báo cáo vòng 1 hiện tại

`02_error_list_v1.csv` có **181 dòng issue**, gồm 22 issue intake và 159 issue QC (36 ERROR + 123 WARN). Đây là số dòng issue, không mặc định là số ảnh duy nhất.

| Mã | Số dòng issue | Mã | Số dòng issue |
|---|---:|---|---:|
| CORRUPT_IMAGE | 2 | BAD_SIZE | 3 |
| DUP_IMAGE_EXACT | 8 | DUP_IMAGE_NEAR | 4 |
| LEAK_TEST | 5 | MISSING_LABEL_FILE | 6 |
| EMPTY_LABEL | 12 | DUP_BOX | 7 |
| BAD_FORMAT | 3 | BAD_CLASS_ID | 6 |
| BOX_HUGE | 3 | BOX_TINY | 6 |
| BOX_OUT_OF_IMAGE | 8 | BOX_ZERO | 4 |
| BAD_CLASS_NAME | 2 | CLASS_RARE | 4 |
| POSSIBLE_MISSING | 39 | POSSIBLE_LOOSE_BOX | 14 |
| POSSIBLE_WRONG_CLASS | 16 | POSSIBLE_FALSE_POS | 29 |

`03_fixes.csv` có 35 bản ghi: **20 drop_line, 8 clip_box, 1 rename_classes, 6 needs_label**. Sáu `needs_label` là chuyển người gán, không phải máy tạo nhãn. Log ghi 80 ảnh được duyệt mô phỏng; chưa xác định số lỗi ngữ nghĩa thực sự được sửa từ log này.

## Giá trị cấu hình hiện tại

- `duplicates.phash_dist`: `10` (giá trị khởi đầu `2`; lần Release hiện có dùng `10`).
- `second_opinion.conf`: `0.75` (giá trị khởi đầu `0.25`; lần pipeline cũ dùng `0.6`).
- `gate.warn_ratio_hold`: `0.10` (ngưỡng Hold hiện tại).

## Kết quả calibration trên 39 ảnh

Đã chạy hai sweep; chi tiết và số đếm nằm tại `submission/calibration/calibration_report.md` và `submission/calibration/calibration.json`. Các ô dưới đây theo thứ tự **precision / recall / F1**.

| `phash_dist` | DUP_IMAGE_EXACT | DUP_IMAGE_NEAR |
|---:|---|---|
| 2 | 1.00 / 1.00 / 1.00 | 1.00 / 0.50 / 0.67 |
| 4, 6, 8, 10, 12, 14 | 1.00 / 1.00 / 1.00 | 1.00 / 0.67 / 0.80 |
| 16 | 1.00 / 1.00 / 1.00 | 1.00 / 0.83 / 0.91 |
| 20 | 1.00 / 0.33 / 0.50 | 1.00 / 0.50 / 0.67 |

| `second_opinion.conf` | WRONG_CLASS | MISSING | LOOSE_BOX | FALSE_POS |
|---:|---|---|---|---|
| 0.10 | 0.56 / 0.83 / 0.67 | 0.40 / 1.00 / 0.57 | 0.38 / 0.60 / 0.46 | 0.31 / 1.00 / 0.48 |
| 0.25 | 0.56 / 0.83 / 0.67 | 0.50 / 1.00 / 0.67 | 0.29 / 0.40 / 0.33 | 0.31 / 1.00 / 0.48 |
| 0.40 | 0.56 / 0.83 / 0.67 | 0.53 / 1.00 / 0.70 | 0.20 / 0.20 / 0.20 | 0.31 / 1.00 / 0.48 |
| 0.50 | 0.56 / 0.83 / 0.67 | 0.57 / 1.00 / 0.73 | 0.20 / 0.20 / 0.20 | 0.31 / 1.00 / 0.48 |
| 0.60 | 0.62 / 0.83 / 0.71 | 0.57 / 1.00 / 0.73 | 0.20 / 0.20 / 0.20 | 0.31 / 1.00 / 0.48 |
| 0.70 | 0.62 / 0.83 / 0.71 | 0.58 / 0.88 / 0.70 | 0.50 / 0.20 / 0.29 | 0.31 / 1.00 / 0.48 |
| 0.80 | 1.00 / 0.83 / 0.91 | 0.67 / 0.75 / 0.71 | 0.50 / 0.20 / 0.29 | 0.31 / 1.00 / 0.48 |

Ở cấu hình khởi đầu, `POSSIBLE_FALSE_POS` có TP=5, FP=11, FN=0; chỉ số không đổi trong sweep `conf` vì check này dùng `fp_conf` riêng. Sau sweep tinh tại `work/calibration_fine/`, người dùng giữ `phash_dist=16` và chọn thử `conf=0.75`; thời gian chạy calibration chưa được ghi nhận.

| Ngưỡng | Trước → chọn | Bằng chứng và lý do |
|---|---|---|
| `phash_dist` | 2 → 16 → 10 | Near duplicate trên calib: tại 2 P/R/F1 = 1.00/0.50/0.67; tại 16 = 1.00/0.83/0.91; tại 10 = 1.00/0.67/0.80. Người dùng giữ 10 sau khi xem cặp bị cờ; chấp nhận cần xử lý hoặc báo cáo cặp 0084–0074 bị bỏ sót. |
| `conf` | 0.25 → 0.6 → 0.75 | So với 0.6, tại 0.75: WRONG_CLASS P/R/F1 từ 0.62/0.83/0.71 lên 1.00/0.83/0.91; MISSING từ 0.57/1.00/0.73 thành 0.64/0.88/0.74 (7/8 thay vì 8/8 lỗi chèn); LOOSE_BOX recall vẫn 0.20. Các chỉ số là trên calib, cần kiểm trên raw. |

Sweep tinh cho near duplicate: ngưỡng 16–19 đều P/R/F1 = 1.00/0.83/0.91 trên calib; sau khi xem ảnh raw, người dùng chọn giữ ngưỡng 10. Tại `conf=0.75`, WRONG_CLASS = 1.00/0.83/0.91, MISSING = 0.64/0.88/0.74, LOOSE_BOX = 0.50/0.20/0.29, FALSE_POS = 0.31/1.00/0.48.

### Quan sát thủ công 7 cặp gần trùng trên raw

Người dùng mở và so sánh các cặp trong báo cáo intake; nhận xét dưới đây là quan sát của người dùng:

| Ảnh bị báo | Ảnh đối chiếu | pHash | Quan sát |
|---|---|---:|---|
| `img_0011` | `img_0008` | 16 | Khác nhau hoàn toàn — báo gần trùng nhầm. |
| `img_0084` | `img_0074` | 16 | Giống nhau; `img_0074` đã bị thu nhỏ so với `img_0084`. |
| `img_0177` | `img_0113` | 16 | Không giống nhau — báo gần trùng nhầm. `img_0113` cũng bị loại do `BAD_SIZE`. |
| `img_0186` | `img_0061` | 10 | Cùng ảnh, một ảnh bị thu nhỏ — người dùng đã xem lại và sửa nhận xét ban đầu. |
| `img_0223` | `img_0077` | 6 | Giống nhau; có thể đã chỉnh sáng. |
| `img_0076` | `img_0042` | 0 | Giống nhau; một ảnh bị thu nhỏ. |
| `img_0143` | `img_0037` | 0 | Giống nhau; một ảnh bị cắt nhỏ. |

Theo nhận xét cập nhật, trong 7 cặp được gắn `DUP_IMAGE_NEAR` có **5 cặp cùng ảnh và 2 cặp khác nhau**. Đây là kết quả xem thủ công các cặp đã bị gắn cờ, không phải precision tổng thể của toàn bộ check. Hai cặp khác nhau có khoảng cách 16, nhưng một cặp cùng ảnh cũng có khoảng cách 16; hạ ngưỡng có thể giảm báo nhầm đồng thời bỏ sót cặp trùng.

### Quan sát thủ công 11 cặp `LEAK_TEST`

Người dùng so sánh ảnh raw với ảnh test được ghi trong `01_intake`; kết quả sau là nhận xét của người dùng:

| Ảnh raw bị báo | Ảnh test | Quan sát |
|---|---|---|
| `img_0013` | `test_087.jpg` | Khác cảnh; pHash 16 |
| `img_0017` | `test_071.jpg` | Khác cảnh; pHash 16 |
| `img_0021` | `test_048.jpg` | Khác cảnh; pHash 16 |
| `img_0033` | `test_070.jpg` | Khác cảnh; pHash 16 |
| `img_0038` | `test_002.jpg` | Khác cảnh; pHash 16 |
| `img_0049` | `test_033.jpg` | Cùng ảnh, chỉnh sáng; pHash 0 |
| `img_0101` | `test_039.jpg` | Cùng ảnh, chỉnh sáng; pHash 6 |
| `img_0115` | `test_088.jpg` | Khác cảnh; pHash 16 |
| `img_0167` | `test_044.jpg` | Cùng ảnh, chỉnh sáng; pHash 2 (người dùng cập nhật đánh giá trước đó) |
| `img_0174` | `test_085.jpg` | Cùng ảnh; pHash 0 |
| `img_0221` | `test_009.jpg` | Cùng ảnh, chỉnh sáng; pHash 0 |

Theo bảng nhận xét mới nhất: **5/11 cặp cùng ảnh, 6/11 cặp khác cảnh**. Sáu cặp khác cảnh đều có pHash 16; năm cặp cùng ảnh có pHash 0, 2 hoặc 6. Cộng với 2/7 cặp `DUP_IMAGE_NEAR` được nhận xét là khác nhau có **8 ảnh raw nghi bị loại nhầm trong 18 cặp đã xem**. Đây là kết quả kiểm thủ công những cặp được gắn cờ, không đo được số cặp trùng bị bỏ sót. Hạ ngưỡng có thể thay đổi cặp đối chiếu do thứ tự và ưu tiên của check; không suy ra kết quả của lần chạy mới bằng cách lọc bảng này. Những quan sát test là dữ liệu đánh giá cuối, không nên tối ưu ngưỡng dựa riêng vào chúng.

Người dùng xác nhận các cặp hiển thị ở ngưỡng **8, 10 và 12** đều cùng ảnh khi xem cả bộ lọc **test/val** lẫn **gần trùng trong raw**. Cặp `img_0186`–`img_0061` được xem lại và nhận xét là cùng ảnh bị thu nhỏ, thay cho nhận xét ban đầu là khác ảnh. Dữ liệu trang cho toàn bộ loại cặp: ngưỡng 8 có 16 cặp (5 LEAK_TEST, 8 EXACT, 3 NEAR); ngưỡng 10 và 12 đều có 17 cặp (5 LEAK_TEST, 8 EXACT, 4 NEAR); ngưỡng 16 có 26 cặp (11 LEAK_TEST, 8 EXACT, 7 NEAR). Đây là số cờ của check trùng, không phải tổng số ảnh intake loại và không đo được các cặp trùng bị bỏ sót. Không chọn ngưỡng chỉ để tối ưu tập test/val.

## Việc cần làm tiếp

1. Quyết định cách xử lý hoặc ghi nhận cặp `0084`–`0074` vẫn cùng nằm trong export; đối chiếu thêm các ảnh được giữ lại nếu cần.
2. Đọc `02_error_list_v1`, `03_fixes.csv`, hàng đợi và log review của lần được chọn để thống kê lỗi và phân việc theo yêu cầu báo cáo.
3. Đã thử gate với `--budget 0`: **Rework**, 6 lỗi `MISSING_LABEL_FILE`, 92/202 ảnh cảnh báo (45,54%), 0 ảnh duyệt, không xuất dataset, 5,7 giây. `work/rep_nb/08_summary.json` ghi `exported: null`, `work/exp_nb/clean_v1` không tồn tại; người dùng xác nhận `$LASTEXITCODE` là **20**.
4. Cập nhật `submission/REPORT.md`, rồi chạy `check_submission.py --no-train`; chưa có kết quả kiểm bài nộp. Train là phần tùy chọn; nếu chưa train thì ghi “chưa chạy”.

## Gợi ý chuyển số liệu sang 6 mục trong `REPORT.md`

1. **Kết luận trước:** decision, số ảnh vào/ra lấy từ `08_summary.json` và `manifest.json`.
2. **Lỗi và phân việc:** nhóm lỗi từ `02_error_list_v1`; đối chiếu `03_fixes.csv` và hàng đợi review.
3. **Calibration:** dùng `submission/calibration/` và giá trị thực tế trong `configs/pipeline.yaml`.
4. **Gate và điểm mù:** lấy kết luận từ vòng QC cuối; ghi bằng chứng cho ít nhất hai điểm mù sau khi tự xem dữ liệu.
5. **Train:** chưa chạy thì ghi “chưa chạy”; nếu chạy, dùng `submission/results/comparison.md`.

## Mục 6 trong `REPORT.md` — kiểm code AI và nhật ký

Phần này cần gói thành **3 dòng** trong `REPORT.md` mục 6. Dùng đúng trải nghiệm thực tế; không ghi kiểm tra nào chưa làm như thể đã làm.

### Checklist kiểm code AI

1. **Đọc lướt code:** kiểm tra có xóa/ghi đè file không, có `except: pass` nuốt lỗi không, và có ngưỡng nào bị viết cứng thay vì đọc từ config không.
2. **Kiểm chứng:** chạy test; chạy pipeline trên **bản sao**, không dùng `data/raw` làm nơi sửa; thử các ca đã biết lỗi trong tập `calib`.
3. **Khi có lỗi:** gửi AI 5 dòng cuối traceback. Phân biệt lỗi môi trường/đường dẫn như `FileNotFoundError` với lỗi xử lý dữ liệu như `ValueError` hoặc `IndexError` do dòng nhãn thiếu cột.

### Nhật ký theo từng prompt

| Prompt | AI trả gì | Tôi kiểm bằng cách nào | Chỗ AI sai/thiếu và tôi sửa thế nào |
|---|---|---|---|
| Đọc docstring `label_format`, `common.py` và test; triển khai, giữ số dòng gốc, lấy ngưỡng từ config. | Cài đặt các kiểm tra định dạng, lớp, hình học, box trùng/nhỏ/lớn. | Test mục tiêu **14 passed**; đối chiếu diff và tự rà phép tính biên. Lần thử đầu lỗi quyền thư mục tạm trước khi test chạy, lần chạy lại đạt. | Lần đầu giải thích từng dòng ở ngoài file; sau khi được nhắc, bổ sung chú thích tiếng Việt ngay trong code. |
| Đọc docstring/test của `gate`; giải thích cách đếm ảnh cảnh báo và thứ tự quyết định. | Cài đặt đếm ERROR, đếm ảnh WARN duy nhất chưa review và trả `Rework`/`Hold`/`Release`. | Người dùng chạy `python -m pytest tests/test_gate.py -q`: **10 passed**. | Chưa ghi nhận lỗi logic qua test mục tiêu; chưa chạy gate trên dữ liệu raw thật nên chưa xác minh kết luận end-to-end. |
| Viết `autofix` theo docstring, gom issue theo ảnh/dòng và xử lý các ca biên. | Cài đặt drop/clip line, remove image, rename class và `needs_label`. | Test mục tiêu **11 passed**; cần bổ sung lần kiểm trên bản sao và các ca calib trước khi kết luận toàn pipeline. | Chưa ghi nhận lỗi qua test mục tiêu; kiểm trên bản sao/calib còn thiếu, chưa có sửa đổi dựa trên dữ liệu thật. |
| Viết `second_opinion` theo docstring; áp ngưỡng và đúng thứ tự issue. | Cài đặt cảnh báo missing/loose/wrong-class/false-positive, giữ thứ tự dự đoán và số dòng gốc. | Test mục tiêu **15 passed**; cần bổ sung lần kiểm trên bản sao và các ca calib trước khi kết luận toàn pipeline. | Chưa ghi nhận lỗi qua test mục tiêu; kiểm trên bản sao/calib còn thiếu, chưa có sửa đổi dựa trên dữ liệu thật. |
| Dán traceback `python -m pytest -q` báo thiếu `imagehash` khi collection `test_duplicates.py`. | AI xác định lỗi môi trường: dependency có trong `requirements.txt` nhưng thiếu trong Python 3.14 mặc định; repo hỗ trợ Python 3.9–3.13. | Đối chiếu traceback, requirements, setup doc và `pip show`; tạo `.venv` Python 3.12, cài requirements và chạy full suite: **79 passed**. | Không sửa code/test. `py -3.12` không chọn được runtime và ensurepip của runtime trực tiếp lỗi; dùng runtime 3.12 có sẵn cùng `uv pip install` vào `.venv` để khắc phục. |
| Nhờ AI giải thích checkpoint 3; sau khi chạy sweep, yêu cầu lưu kết quả và tạo file HTML trực quan để hiểu cách thử, chọn ngưỡng. | AI giải thích calib, precision/recall, tổng hợp hai bảng sweep vào note và tạo `submission/calibration/huong-dan-tuong-tac.html` với ô chọn ngưỡng và hướng dẫn. | AI đối chiếu số liệu với `calibration_report.md`; người dùng chọn `phash_dist=16`, `conf=0.6` và AI cập nhật config. Trang dùng số liệu của lần chạy đã ghi, không tự cập nhật sau sweep mới. | Chưa kiểm giao diện HTML trực tiếp trong trình duyệt và chưa xem các cặp ảnh raw. Cần bổ sung bằng chứng ở CP4. |
| Nhờ AI giải thích pHash, đọc intake và tạo trang so sánh ảnh theo từng ngưỡng; sau đó cung cấp nhận xét xem ảnh và yêu cầu cập nhật config. | AI tạo `submission/calibration/so-sanh-anh.html`, giải thích đánh đổi báo nhầm/bỏ sót, đối chiếu sweep và cập nhật `phash_dist=10` theo yêu cầu. | Người dùng tự xem ảnh trên trang và phân loại các cặp; AI đối chiếu 26 cặp ngưỡng 16 với báo cáo intake; đã chạy pipeline ngưỡng 10. | Người dùng xem lại cặp `0186`–`0061` và sửa nhận xét thành cùng ảnh bị thu nhỏ; AI đã cập nhật note. Cặp `0084`–`0074` đã xác nhận cùng nằm trong export; chưa đo hết số cặp bị bỏ sót. |

### Bản nháp 3 dòng có thể đưa vào `REPORT.md`

1. **Prompt:** dùng AI hỗ trợ viết bốn module, xử lý lỗi môi trường, giải thích calibration và tạo trang so sánh ảnh theo ngưỡng pHash.
2. **Tôi kiểm:** các test module và full suite đạt; đã chạy sweep calib, pipeline 16/0.75 và 10/0.75, tự xem các cặp bị cờ trên trang và xác nhận cặp trùng còn trong export.
3. **AI sai/thiếu:** ban đầu AI giải thích `label_format` ngoài code; sau góp ý đã thêm chú thích. Tôi xem lại và sửa nhận xét cặp `0186`–`0061` thành cùng ảnh; vẫn cần đánh giá các cặp bỏ sót và không chọn ngưỡng chỉ dựa trên test/val.
