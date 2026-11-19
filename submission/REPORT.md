# Báo cáo Day 09 — Lê Tuấn Khôi, 2A202603024

## 1. Kết luận trước

Từ 224 ảnh ban đầu, pipeline giữ lại 202 ảnh và loại 22 ảnh ở bước tiếp nhận. Sau khi sửa tự động và duyệt mô phỏng, không còn lỗi bắt buộc; 18/202 ảnh (8,91%) vẫn có cảnh báo chưa được duyệt. Tỷ lệ này dưới ngưỡng 10%, nên gate kết luận **Release** và xuất danh sách 202 ảnh cùng nhãn.

Tuy vậy, kết luận Release chưa có nghĩa là mọi lỗi đều đã được tìm thấy. Khi xem thủ công, tôi xác nhận `img_0074` và `img_0084` là cùng ảnh, nhưng cả hai vẫn nằm trong manifest. Tôi quyết định giữ cả hai và ghi nhận đây là một điểm mù của bộ dữ liệu hiện tại.

## 2. Lỗi và phân việc

Trước khi sửa, báo cáo `02_error_list_v1.csv` ghi 181 dòng lỗi và cảnh báo: 22 dòng ở bước tiếp nhận và 159 dòng QC, trong đó QC có 36 lỗi bắt buộc và 123 cảnh báo. Tôi đếm theo dòng báo cáo vì một ảnh có thể xuất hiện nhiều lần.

| Mã lỗi | Số dòng | Ai xử lý | Vì sao |
|---|---:|---|---|
| CORRUPT_IMAGE 2; BAD_SIZE 3 | 5 | Máy | Intake loại ảnh hỏng hoặc quá nhỏ. |
| DUP_IMAGE_EXACT 8; DUP_IMAGE_NEAR 4; LEAK_TEST 5 | 17 | Máy; người xem lại | Intake loại ảnh bị báo trùng; pHash có thể báo nhầm. |
| MISSING_LABEL_FILE | 6 | Duyệt mô phỏng | Máy ghi `needs_label`, không tự tạo nhãn. |
| DUP_BOX 7; BAD_FORMAT 3; BAD_CLASS_ID 6; BOX_ZERO 4 | 20 | Máy | Autofix xóa dòng nhãn lỗi. |
| BOX_OUT_OF_IMAGE 8; BAD_CLASS_NAME 2 | 10 | Máy | Cắt box hoặc xóa dòng không còn diện tích; sửa tên lớp. |
| EMPTY_LABEL 12; BOX_HUGE 3; BOX_TINY 6 | 21 | Hàng đợi duyệt | Cảnh báo gắn với ảnh cần xem xét. |
| POSSIBLE_MISSING 39; POSSIBLE_LOOSE_BOX 14; POSSIBLE_WRONG_CLASS 16; POSSIBLE_FALSE_POS 29 | 98 | Hàng đợi duyệt | Model nghi thiếu, lệch, nhầm lớp hoặc thừa box. |
| CLASS_RARE | 4 | Người đọc thống kê | Cảnh báo cấp dataset, không phải ảnh trong hàng đợi. |

`03_fixes.csv` ghi 35 hành động: 20 `drop_line`, 8 `clip_box`, 1 `rename_classes` và 6 `needs_label`. Hàng đợi có 108 ảnh, xếp theo trọng số cảnh báo, độ tin cậy và sửa đổi tự động; `img_0020` đứng đầu với 11,524 điểm, sáu ảnh thiếu nhãn tiếp theo có 10 điểm mỗi ảnh.

Script **duyệt mô phỏng** 80/108 ảnh bằng cách thay nhãn bằng nhãn tham chiếu; tôi không trực tiếp sửa 80 ảnh này. “Hàng đợi duyệt” trong bảng là hướng xử lý, không có nghĩa mọi cảnh báo đã được duyệt. Tôi chưa xác minh được bao nhiêu cảnh báo là lỗi ngữ nghĩa thật và đã được sửa.

## 3. Calibration (2 ngưỡng)

Tôi thử các ngưỡng trên 39 ảnh calib có lỗi được chèn sẵn, sau đó chọn hai giá trị dưới đây. Các chỉ số chỉ mô tả kết quả trên tập calib; tôi ghi riêng từng loại cảnh báo của `second_opinion` để dễ thấy sự đánh đổi.

| Tham số | Khởi đầu | Đã chọn | Precision / Recall (trước → sau) | Lý do và đánh đổi |
|---|---:|---:|---|---|
| `duplicates.phash_dist` | 2 | 10 | Near duplicate: 1,00 / 0,50 → 1,00 / 0,67 (3/6 → 4/6 lỗi chèn) | 10 hạn chế gắn cờ các cặp có khoảng cách 16 mà người xem thấy khác nhau; đổi lại bỏ sót một số cặp trùng. |
| `second_opinion.conf` | 0,25 | 0,75 | WRONG_CLASS: 0,56 / 0,83 → 1,00 / 0,83; MISSING: 0,50 / 1,00 → 0,64 / 0,88; LOOSE_BOX: 0,29 / 0,40 → 0,50 / 0,20 | Chọn 0,75 để tăng precision ở các nhóm này trên calib, chấp nhận bỏ sót thêm lỗi thiếu box và box lỏng. FALSE_POS dùng `fp_conf` riêng, giữ 0,31 / 1,00 trong sweep. |

Kết quả calib cần được đọc thận trọng vì tập này nhỏ và các lỗi chèn không bao phủ hết lỗi tự nhiên. Ở ngưỡng 10, check không báo sai cặp gần trùng nào trên calib, nhưng cũng chỉ bắt được 4/6 ca đã chèn. Trên raw, tôi thấy `img_0074` và `img_0084` là cùng ảnh, có pHash 16 và đều lọt vào export. Ngược lại, ở ngưỡng 16, một số cặp bị báo lại là hai ảnh khác nhau. Tôi cũng đã xem một số cặp test/val để kiểm tra rò rỉ; điều này cần được tính đến khi diễn giải kết quả đánh giá cuối.

## 4. Cửa chặn và điều pipeline không bắt được

Tôi chạy pipeline với `--budget 0` và các thư mục work, báo cáo, export riêng. Không có ảnh nào được duyệt; sau QC vẫn còn 6 lỗi `MISSING_LABEL_FILE`, nên gate kết luận **Rework** dù còn 92/202 ảnh có cảnh báo. Terminal trả mã thoát **20**; `work/rep_nb/08_summary.json` ghi `exported: null`, và thư mục `work/exp_nb/clean_v1` không tồn tại. Lần chạy mất 5,7 giây.

Hai điểm mù có bằng chứng:

1. **Ảnh gần trùng bị bỏ sót:** `img_0074` và `img_0084` cùng nằm trong manifest tại ngưỡng 10; người xem xác nhận cùng ảnh nhưng khoảng cách pHash là 16.
2. **Box lỏng:** tại `conf=0.75`, calibration bắt **1/5** ca `LOOSE_BOX` đã chèn (recall 0,20), bỏ sót 4/5. Đây là bằng chứng trên calib, không phải ước tính recall của raw.

## 5. Train: raw vs clean (tùy chọn, chấm riêng)

Tôi chưa chạy train vì chưa có thời gian, nên chưa có kết quả raw và clean theo từng seed để so sánh mAP. Vì vậy, hiện tại tôi chưa thể kết luận dữ liệu sau QC giúp model tốt hơn hay không.

## 6. Quyết định và ghi chú AI

Gate cho phép Release bản 202 ảnh theo cấu hình hiện tại. Tôi giữ nguyên cả hai ảnh `0074–0084` và ghi nhận cặp trùng này là một điểm mù đã biết: ngưỡng pHash 10 không phát hiện được cặp có khoảng cách 16. Việc giữ cả hai có thể làm tăng ảnh trùng trong tập huấn luyện.

1. **Prompt:** Tôi nhờ AI hỗ trợ viết bốn module, giải thích calibration, tạo trang so sánh ảnh và định dạng báo cáo; tôi đưa yêu cầu và quyết định ngưỡng.
2. **Kiểm:** Full suite đạt 79 test; tôi chạy pipeline, tự xem ảnh và đối chiếu số liệu với `submission/reports/`, manifest, báo cáo calibration và `work/rep_nb/`. AI cũng hỗ trợ chạy test và đọc file; các số chưa xác minh được ghi rõ.
3. **AI sai/thiếu:** Ban đầu AI giải thích `label_format` ngoài file; sau góp ý, AI thêm chú thích vào code. Tôi cũng xem lại và sửa nhận xét ban đầu về cặp `0186–0061` thành cùng ảnh bị thu nhỏ.

Khi chạy `check_submission.py --no-train` trên Windows, 79 test đạt nhưng công cụ vẫn báo 2 lỗi vì thấy `MANIFEST` và `data/calib` trong `pipeline/calibrate.py`. Tôi đối chiếu thấy file này có SHA-1 khớp danh sách file đề được bảo vệ. Nguyên nhân kiểm tra là đường dẫn Windows `pipeline\calibrate.py` không khớp chuỗi `pipeline/calibrate.py` trong danh sách, khiến công cụ quét nhầm file calibration của đề. Do đó lệnh hiện chưa đạt trạng thái hết lỗi trên Windows; tôi không sửa công cụ hay file đề và báo rõ giới hạn này khi nộp.
