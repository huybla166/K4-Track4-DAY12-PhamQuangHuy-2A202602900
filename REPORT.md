# REPORT — Lab Day 12

> Điền **bằng lời và số liệu của chính bạn** (lấy từ màn hình và từ `evidence/*.json`). Mỗi câu 4–8 dòng là đủ. Số không có trong bằng chứng của bạn sẽ bị trừ điểm. Báo cáo công khai trên GitHub; giảng viên đối chiếu với `evidence/` và với bài của các bạn khác.

| | |
|---|---|
| Họ và tên | Phạm Quang Huy |
| MSSV (đúng bằng `--student-id` bạn đã chạy) | 2A202602900 |
| GitHub | huybla166 |
| Seed chia dữ liệu / seed mô hình (xem `evidence/closedloop.json`, mục `student`) | split_seed 2737 / model_seed 8507 (5 seed huấn luyện: 8507–8511), cruise speed của lưới 12.0 m/s |
| Số seed huấn luyện bạn dùng (`--seeds`) | 5 (mặc định) |

Toàn bộ `evidence/` sinh từ **một lần chạy** `python run_all.py --student-id 2A202602900 --seeds 5` trên Kaggle (máy GPU T4, commit `4e575df`, 25/25 kiểm thử OK, 816 s; log ở `kaggle/logs/`). Mã của bài thuần numpy nên chạy trên CPU của máy đó, GPU không tham gia tính toán. Số liệu dưới đây lấy nguyên từ các file JSON (làm tròn).

## Kết quả cuối

Điền từ `evidence/closedloop.json`, `openloop.json`, `gate.json` (cho mỗi mô hình học, lấy **dải qua các seed**).

| Bộ điều khiển | L2 vòng hở (m) | Va chạm vòng kín trên log (%) | Quyết định cổng |
|---|---|---|---|
| constant-velocity | 1.265 | 19.5 (562/2883, tất định nên 1 lần chạy; CI95 [18.1, 21.0]) | BLOCK (rớt R2, R3, R4, R6) |
| IDM | 1.502 | 0.1 (3/2883; CI95 [0.04, 0.31]) | (baseline) |
| EgoMLP | 0.763 ± 0.005 (0.757–0.771 qua 5 seed) | 12.9 – 31.1 (TB 20.8) | BLOCK (rớt R2, R3, R4, R5, R6) |
| PercMLP | 0.625 ± 0.003 (0.621–0.627 qua 5 seed) | 0.38 – 1.32 (TB 0.68) | BLOCK (rớt R2, R3, R4, R6) |
| PercMLP+ (sau khi sửa) | 0.802 ± 0.016 | 0.10 – 0.17 (TB 0.12) | RELEASE (qua 7/7 quy tắc) |

## Câu 1 · Dữ liệu
Bước 0 bạn phát hiện những vấn đề gì ở dữ liệu? Vì sao không dùng cột `Acc_LV`, và bạn thay bằng gì? Bao nhiêu quỹ đạo bị loại vì trùng, và vì sao chia theo quỹ đạo?

Ba vấn đề trong `data_audit.json` (992,679 dòng, 9,993 quỹ đạo, mỗi quỹ đạo 70–109 bước ở 10 Hz):
- **`Acc_LV` không dùng được.** Tương quan của nó với đạo hàm `d(Speed_LV)/dt` chỉ **0.045**, trong khi cột tương ứng của xe theo sau (`Acc_FAV`) khớp tới **0.929**. Cột gia tốc xe dẫn gần như là nhiễu. Mình dùng `logs.a_lead`: lấy `Speed_LV` làm mượt bằng trung bình trượt 5 mẫu (0.5 s) rồi lấy sai phân trung tâm. Với gia tốc này p0.1 = −2.77 m/s², p1 = −1.95 m/s². Vì vậy `mine_braking` dùng ngưỡng −2 m/s² **kéo dài ≥ 5 bước liên tiếp**, để bắt cú phanh thật chứ không bắt một mẫu nhiễu.
- **383 quỹ đạo trùng hệt nhau** (cùng tốc độ xe dẫn, xe sau và khoảng cách) nằm ở các id cách xa nhau. Sau khi loại còn 9,610. Nếu giữ lại, một bản có thể rơi vào train và bản kia vào test: mô hình được chấm trên đúng bài đã học, điểm test đẹp giả.
- **Phải chia theo quỹ đạo, không chia theo khung.** Hai khung liền nhau chỉ cách 0.1 s nên gần như giống hệt nhau, và mỗi cửa sổ (2 s lịch sử + 3 s tương lai) chồng lên các cửa sổ kề bên. Chia theo khung sẽ làm rò thông tin sang test. Mình chia theo quỹ đạo với seed 2737, được 2,883 quỹ đạo test giữ lại hoàn toàn.

Ngoài ra `Spatial_Gap = Pos_LV − Pos_FAV − 4.5 m` đúng tới sai số 3.6e-11 m, nên cột khoảng cách đáng tin.

## Câu 2 · Phát lại
Bản refactor float32 khác bit ở bao nhiêu đoạn, vượt dung sai ở bao nhiêu? Thay đổi AEB làm lệch bao nhiêu đoạn, và vì sao lệch ở đúng những khung đó (mở một đoạn ra xem)? Phát theo thời gian thật làm lộ ra điều gì mà phát nhanh nhất che đi?

- **Refactor float32 (đổi thứ tự phép tính):** **600/600** đoạn không giống từng bit, nhưng **0/600** đoạn vượt dung sai. Lệch lớn nhất là 4.0e-4 m/s², nhỏ hơn atol = 1e-3 (cộng thêm rtol·|a|). Chạy lại đúng mã cũ thì 0 đoạn khác bit. Nguyên nhân: phép cộng số thực không có tính kết hợp, (0.1+0.2)+0.3 = 0.6000000000000001 còn 0.1+(0.2+0.3) = 0.6; cộng 50k số float32 theo chiều xuôi và chiều ngược lệch nhau tương đối 6.9e-6. Dung sai 1e-3 m/s² là hợp lý: nó nhỏ hơn nhiều mức nhiễu của bộ chấp hành (trong 0.1 s chỉ đổi tốc độ 1e-4 m/s), nhưng vẫn đủ nhạy để bắt một thay đổi hành vi thật (AEB làm lệch tới 2.01 m/s²).
- **Thêm AEB:** chỉ **7/600** đoạn lệch (52, 58, 156, 214, 324, 592, 593). Mở đoạn 52 (`evidence/peek_aeb.txt`): chỉ 3/78 khung lệch, là các khung 75–77 ngay trước lúc chạm. Ở đó TTC = 1.48 / 1.46 / 1.44 s, dưới ngưỡng 1.5 s, nên lệnh đổi từ −4.38 thành −6.00 m/s². Khung có TTC thấp nhất trong số khung không đổi là 1.51 s. Đoạn 156 có một khung TTC 1.27 s nhưng **không đổi**, vì IDM đã ra lệnh −7.22, mạnh hơn −6 rồi (AEB lấy `min(cmd, −6)`). Vậy AEB chỉ đổi những khung có TTC < 1.5 s **và** IDM đang phanh nhẹ hơn 6 m/s², tức là vài khung cuối của số ít đoạn sắp chạm.
- **Phát theo thời gian thật:** có **585 khung trễ + 581 khung rớt** trên 59,943 khung, làm **370/600** đoạn đổi lệnh (lệch tới 6.79 m/s²). Phát nhanh nhất thì có 0 khung trễ, 0 khung rớt, vì ở chế độ đó không có đồng hồ: thông điệp sau chỉ được gửi khi bộ điều khiển xử lý xong thông điệp trước, nên một khung tốn 140 ms (vượt hạn 100 ms) không hề lộ ra. Phát nhanh nhất chỉ kiểm tra được **logic**, không kiểm tra được **thời gian**.

## Câu 3 · Kịch bản
Lưới của bạn (tốc độ cruise, giới hạn khoảng cách, số ô): bao nhiêu % ô **không ai tránh được**? Độ trễ phản ứng 0 → 0,6 s làm vùng đâm của IDM tăng bao nhiêu? Log có phủ vùng khó không? (dẫn giới hạn phanh mạnh nhất của người lái trong log, và phần lưới đòi hỏi hơn thế)

- **Lưới:** cruise 12.0 m/s, khoảng cách 2.76–59.31 m (p2–p98 của log), tốc độ tiến gần 0–12 m/s, 60 × 45 = **2,700 ô**.
- **Vùng không ai tránh được:** **2.2 %** ô khi t_react = 0 và **7.4 %** khi t_react = 0.6 s. Mình kiểm chứng biên này bằng bộ phanh hết cỡ: nó đâm đúng 2.2 % và 7.4 % ô, **0 ô lệch** ngoài dải 5 % quanh biên ở cả hai độ trễ (xét 2,690 và 2,673 ô).
- **IDM:** vùng đâm tăng từ **2.2 % lên 7.4 %** khi độ trễ tăng từ 0 lên 0.6 s, và vùng đâm đó **trùng khít vùng bất khả kháng** (`attributable_area` = 0.0 % ở cả hai độ trễ; trên `scenarios_idm.png` đường đỏ nằm đúng trên đường cyan). Phần tăng thêm đến hoàn toàn từ vật lý của độ trễ, không phải lỗi của IDM. Ngược lại, const-vel đâm 77.6 % ô, trong đó **75.4 % / 70.2 %** là tránh được: đó mới là "bộ điều khiển thất bại".
- **Log không phủ vùng khó.** Người lái trong log phanh mạnh nhất (p99.9) **3.6 m/s²**, trong khi xe phanh được 9 m/s². **8.6 %** ô của lưới đòi phanh mạnh hơn mọi lần phanh có trong log. 614 sự kiện xe dẫn phanh khai thác được (6.4 % quỹ đạo; đỉnh phanh p50 −2.5, p99 −4.2 m/s²), nhưng các chấm trắng gần như đều nằm ở tốc độ tiến gần dưới ~6 m/s. Góc gap nhỏ, tiến gần nhanh hoàn toàn trống: mô hình học từ log chưa từng thấy vùng này.

## Câu 4 · Vòng hở và vòng kín
Dán bảng L2 và tỷ lệ va chạm của bốn bộ điều khiển (kèm hạng ở mỗi cách chấm). Cặp nào đổi thứ tự? Vì sao IDM có L2 như vậy mà vẫn lái tốt? Vì sao EgoMLP có L2 tốt hơn constant-velocity mà vẫn đâm?

| Bộ | L2 vòng hở (m) | hạng | L2 lát cắt phanh (m) | va chạm vòng kín TB (%) | hạng |
|---|---|---|---|---|---|
| const-vel | 1.265 | 3 | 1.846 | 19.5 | 3 |
| IDM | 1.502 | 4 | 1.555 | 0.1 | 1 |
| EgoMLP | 0.763 | 2 | 1.152 | 20.8 | 4 |
| PercMLP | 0.625 | 1 | 0.853 | 0.7 | 2 |

**4 cặp đổi thứ tự:** (const-vel, IDM), (const-vel, EgoMLP), (IDM, EgoMLP), (IDM, PercMLP). Xếp hạng theo L2 gần như ngược hẳn xếp hạng theo va chạm (`openloop_vs_closedloop.png`).
- **IDM có L2 tệ nhất (1.502 m, còn tệ hơn đứng yên ở tốc độ cũ 1.265 m) mà lái an toàn nhất (0.1 %, 3/2883).** L2 đo khoảng cách tới **quỹ đạo của người lái**, không đo độ an toàn. IDM có tham số riêng (T = 1.2 s, v0 = 15 m/s), còn người trong log giữ khoảng cách thời gian trung vị 1.81 s và tăng/giảm tốc theo kiểu của họ, nên dự báo 3 s của IDM lệch đều đặn khỏi người. Nhưng IDM là luật **phản hồi** theo khoảng cách và tốc độ tiến gần: khoảng cách mong muốn s* tăng khi tiến gần nhanh, còn lực phanh tăng theo (s*/gap)². Nhờ vậy ở mỗi bước nó tự sửa sai số của chính mình. Bằng chứng: L2 của IDM gần như không đổi khi xe dẫn phanh (1.502 → 1.555), trung vị phanh mạnh nhất 0.91 m/s².
- **EgoMLP có L2 tốt hơn constant-velocity (0.763 so với 1.265) vì** tốc độ của một xe tự tương quan rất mạnh, và **95.6 %** cửa sổ test không có xe dẫn phanh (lát cắt phanh chỉ chiếm 4.4 %). Ngoại suy quá khứ của chính mình vì thế khớp tốt **trung bình**. Nhưng nó **không có đầu vào gap hay tốc độ xe dẫn**, nên khi xe dẫn phanh nó không thể biết. L2 trên lát cắt phanh tăng lên 1.152; seed xấu nhất có trung vị phanh mạnh nhất chỉ 0.05 m/s² và đâm ở **61.2 %** quỹ đạo có xe dẫn phanh. Trong vòng kín, đầu vào của nó lại là chính các lệnh nó vừa ra, nên sai số tự khuếch đại: TB 20.8 %, còn tệ hơn const-vel 19.5 %.

## Câu 5 · Một lần chạy chưa đủ
EgoMLP dao động bao nhiêu giữa các seed? Khoảng tin cậy Wilson nói gì? Nếu bạn chỉ chạy đúng một seed thì có thể báo kết quả nào, và vì sao điều đó nguy hiểm?

- **EgoMLP qua 5 seed (8507–8511): 31.1 / 17.5 / 12.9 / 16.9 / 25.6 %**, chênh tới 2.4 lần giữa seed tốt nhất và xấu nhất. Khoảng tin cậy Wilson 95 % của seed xấu nhất (8507) là **[29.5, 32.9] %**, của seed tốt nhất (8509) là **[11.7, 14.1] %**: **hai khoảng không chồng nhau**. Wilson chỉ đo bất định do lấy mẫu 2,883 quỹ đạo với **một mô hình cố định**; nó không chứa độ ngẫu nhiên của huấn luyện. Khác biệt giữa các seed là thật, và lớn hơn hẳn sai số lấy mẫu (cổng ghi R5 rớt: 12.9..31.1 %).
- **Nếu chỉ chạy một seed** thì có thể báo "EgoMLP đâm 12.9 %" hoặc "31.1 %" tuỳ may rủi, kèm một khoảng tin cậy hẹp trông rất chắc chắn. Với PercMLP còn nguy hiểm hơn: 4 trong 5 seed (8507–8510) có cận trên 0.68 / 0.94 / 0.73 / 1.07 %, đều ≤ 0.1 + 1 = 1.1 %, nên **sẽ qua R2** nếu chỉ chạy một seed. Chỉ seed 8511 (1.32 %, CI [0.96, 1.80]) làm nó rớt. Một lần chạy cho cơ hội 4/5 để kết luận sai "PercMLP không kém IDM". Đó là lý do cổng lấy **seed xấu nhất** và có thêm quy tắc độ ổn định R5.

## Câu 6 · Tác nhân phản ứng
Dán bảng "xe sau phát lại" và "xe sau phản ứng". `T` bạn hiệu chỉnh là bao nhiêu, xe sau chân thực đến mức nào so với xe không phản ứng? Vì sao IDM bị tính "va chạm giả" khi xe sau chỉ phát lại, và điều này làm đổi kết luận về bộ điều khiển ra sao?

Lưới cắt vào, t_react = 0.6 s, % ô có va chạm bất kỳ (trước hoặc sau); cột cuối là riêng va chạm phía sau:

| Bộ | xe sau phát lại | xe sau phản ứng | va chạm phía sau: phát lại / phản ứng |
|---|---|---|---|
| const-vel | 77.6 % | 77.6 % | 0.0 % / 0.0 % |
| IDM | 77.4 % | **7.4 %** | **70.0 %** / 0.0 % |
| EgoMLP | 81.8 % | 81.8 % | 0.0 % / 0.0 % |
| PercMLP | 76.9 % | 29.4 % | 49.1 % / 0.0 % |
| PercMLP+ | 77.1 % | 7.7 % | 69.4 % / 0.0 % |

- **T = 1.2 s.** Khoảng cách Wasserstein-1 giữa phân bố khoảng cách thời gian của xe sau mô phỏng và của người trong log là 0.34, tốt nhất trong lưới (T = 1.4 cho 0.35, T = 2.4 cho 0.89; người có trung vị 1.81 s). Một xe không bao giờ phản ứng cho 0.87, tức là xe sau đã hiệu chỉnh gần người thật hơn khoảng 2.5 lần. Xe sau cách 16.4 m, trễ phản ứng 0.6 s.
- **Va chạm giả.** Xe sau "phát lại" giữ nguyên tốc độ trong log, nên nó không thể biết xe ta vừa phanh vì có xe cắt vào. Bộ điều khiển phanh **càng đúng** càng bị đâm từ phía sau: IDM bị tính va chạm phía sau ở 70.0 % lưới. Const-vel không bao giờ phanh nên 0 % bị đâm sau, nhưng tự đâm phía trước 77.6 %. Trong thế giới phát lại, IDM (77.4 %) trông **ngang const-vel (77.6 %) và còn tệ hơn PercMLP (76.9 %)**, một kết luận hoàn toàn sai.
- **Khi xe sau phản ứng,** va chạm phía sau về 0.0 % cho mọi bộ. IDM còn đúng **7.4 % = diện tích bất khả kháng 7.4 %**, nghĩa là mọi va chạm còn lại của nó là không ai tránh được, và thứ hạng trở về đúng (IDM 7.4 < PercMLP+ 7.7 < PercMLP 29.4 < const-vel 77.6 < EgoMLP 81.8). Ở t_react = 0 cũng vậy: IDM từ 77.1 % xuống 2.2 %.

## Câu 7 · Cổng phát hành và sửa
Quy tắc nào chặn PercMLP và nguyên nhân gốc là gì (dẫn số)? Bạn sửa bằng gì và vì sao nó chữa đúng nguyên nhân? Sau khi qua cổng, PercMLP+ có **tốt hơn** IDM không? Nó có nên được phát hành không, và bạn đề xuất làm gì trước khi quyết định?

**PercMLP bị chặn bởi 4 quy tắc** (qua R1, R5 với dải 0.4..1.3 %, và R7):
- R2: seed xấu nhất 1.3 %, cận trên 1.8 % > 0.1 % + 1 = 1.1 %.
- R3: 5.6 % trên 196 quỹ đạo có xe dẫn phanh, cận trên 9.8 % > 1.0 % + 5 = 6.0 %.
- R4: 22.0 % lưới đâm dù tránh được, so với IDM 0.0 % + 2.
- R6: 29.4 % so với 7.4 %.

Có hai nguyên nhân gốc:
1. **Kịch bản log không chứa (R4, R6).** Ở Câu 3, 8.6 % lưới đòi phanh mạnh hơn 3.6 m/s², mức phanh mạnh nhất của người trong log, mà PercMLP chỉ bắt chước người. Ở tốc độ 20 m/s, tốc độ chưa từng thấy khi huấn luyện, nó đâm 22.8–41.8 % lưới.
2. **Sai số tích luỹ khi tự lái (R2, R3).** L2 vòng hở của PercMLP tốt nhất (0.625) nhưng vòng kín vẫn đâm 0.4–1.3 %, so với IDM 0.1 %. Nó chỉ học ở các trạng thái **người** đã đi qua; một sai số nhỏ đẩy xe vào trạng thái gap nhỏ hơn, tiến gần nhanh hơn, ngoài phân bố huấn luyện, và ở đó dự báo của nó tệ.

**Cách sửa:**
1. Thêm 196,830 cửa sổ từ 20,000 ca cắt vào mô phỏng, nhãn lấy từ việc IDM làm ở đó. Cách này lấp đúng họ kịch bản còn thiếu: R4 từ 22.0 % xuống **0.3 %**, R6 từ 29.4 % xuống **7.7 %**.
2. DAgger 2 vòng (khoảng 894,700 cửa sổ): cho mô hình tự lái, ghi lại trạng thái **nó tự đi vào**, gắn nhãn bằng dự báo 3 s của IDM. Mô hình học cách tự sửa sai số của mình. Kết quả trên log còn 0.10–0.17 % (cận trên 0.4 %), lát cắt phanh 1.0 % (cận trên 3.6 %).

L2 lại **xấu đi**, từ 0.625 lên 0.802, vì nhãn giờ là của IDM chứ không phải của người. Điểm vòng hở đánh lừa theo cả hai chiều.

**PercMLP+ không tốt hơn IDM.** Ở mọi số đo nó bằng hoặc kém hơn một chút:

| Số đo | PercMLP+ | IDM |
|---|---|---|
| Va chạm trên log | 0.10–0.17 % | 0.10 % |
| Lát cắt phanh | 1.0 % | 1.0 % |
| Lưới cắt vào, phần tránh được | 0.3 % | 0.0 % |
| Thế giới phản ứng | 7.7 % | 7.4 % |
| Tốc độ 20 m/s | 0.5–1.7 % | 0.0 % |
| Có nhiễu cảm biến | 0.14–0.21 % | 0.07 % |

Cổng là phép thử **không-kém-hơn** với biên 1–5 điểm, nên "RELEASE" chỉ có nghĩa là không kém quá biên. Nó học từ chính IDM (thầy gán nhãn), nên giỏi lắm cũng bằng thầy trên tiêu chí của thầy.

**Đề xuất:** **chưa thay IDM**. Trước hết phải nói rõ PercMLP+ cần hơn IDM ở điểm gì (êm hơn, giống người hơn, đi nhanh hơn) và đo được điều đó. Sau đó chạy shadow mode song song với IDM, mở rộng tập test và các họ kịch bản giữ lại (tốc độ khác, xe dẫn phanh trong lúc cắt vào, nhiễu và trễ cảm biến), và giữ IDM/AEB làm lớp dự phòng.

## Câu 8 · Bài lab này không chứng minh được gì
Chọn **ít nhất ba** giới hạn quan trọng nhất đối với việc quyết định phát hành và giải thích vì sao mỗi cái làm kết luận của bạn kém chắc chắn. Điều gì cần làm tiếp để thu hẹp khoảng cách đến thế giới thật?

1. **Thế giới mô phỏng là giả định của chính chúng ta.** Chỉ có một chiều dọc, không đổi làn, bộ chấp hành lý tưởng (chỉ có độ trễ), phanh tối đa cố định 9 m/s² (mặt đường khô). Việc kiểm chứng "0 ô lệch" chỉ cho thấy bộ mô phỏng **nhất quán với công thức của mình**, không cho thấy nó **giống xe thật**. Trên mặt đường ướt, vùng bất khả kháng 7.4 % sẽ lớn hơn nhiều, và một mô hình "qua cổng" có thể rớt.
2. **Không có cảm biến.** Bộ điều khiển nhận gap và tốc độ xe dẫn gần như hoàn hảo; chỉ có một phép thử nhiễu Gauss (±1 m, ±0.5 m/s). Chỉ chừng đó nhiễu đã đẩy PercMLP lên tới 1.39 %. Mất dấu, phát hiện sai, trễ cảm biến thật chưa hề được thử, mà mô hình học thường nhạy với chúng hơn luật.
3. **Xe dẫn trong log không phản ứng với xe ta**, và chỉ có một tác nhân phản ứng (xe sau IDM, hiệu chỉnh bằng một con số W1 = 0.34). Câu 6 cho thấy thiếu phản ứng là đủ để đảo ngược kết luận; các tương tác khác (xe khác chen vào vì ta để gap rộng, xe dẫn phản ứng với ta) hoàn toàn vắng mặt.
4. **Độ phủ dữ liệu và thống kê quá nhỏ cho một quyết định an toàn.** Argoverse là đô thị: tốc độ p99 của xe dẫn chỉ 15.6 m/s, của xe theo sau 17.8 m/s. Ở 20 m/s, PercMLP+ đã kém IDM (0.5–1.7 % so với 0.0 %). Với 2,883 quỹ đạo khoảng 10 s (vài giờ lái), 0.1 % chỉ là 3 sự kiện, chênh nhiều bậc so với tần suất cần chứng minh (trên mỗi triệu km).
5. **Vòng luẩn quẩn quanh IDM.** IDM vừa là baseline, vừa là thầy gán nhãn cho cắt vào và DAgger, vừa là mô hình của xe sau. Cổng đang đo "giống IDM đến đâu trong một thế giới IDM".

**Làm tiếp:** mô phỏng vòng kín với tác nhân phản ứng học từ dữ liệu (cả xe dẫn); mô hình cảm biến và trễ, chạy HIL; thêm dữ liệu cao tốc, mưa, đêm và đo độ phủ ODD; shadow mode trên xe thật so quyết định với IDM; kế hoạch thống kê cho sự kiện hiếm (importance sampling, kiểm thử trên biên thay vì trung bình).

---

## Phụ lục · Bước 8 (bonus, không chấm): xem model của mình lái trong mô phỏng 3D

`python scripts/export_viz.py` xuất 15 model (3 loại × 5 seed) và 24 log test giữ lại (12 log có xe dẫn phanh mạnh nhất, tìm bằng `mine_braking` của mình) sang `viz/`. Mình xem trong trình duyệt (`python viz/serve.py`), rồi quét **toàn bộ** các cảnh trên cả 5 seed bằng `node bonus/viz_sweep.js`. Script này dùng lại đúng `viz/sim.js` và cách chấm của `viz/app.js`; kết quả ở `bonus/viz_sweep.json`. Mô phỏng 3D có vật lý riêng (xe đạp động học, 20 Hz, μ = 0.8), nên chỉ so **hình dạng** với `evidence/`, không so số.

| Quan sát (số seed đâm / 5) | IDM | const-vel | EgoMLP | PercMLP | PercMLP+ |
|---|---|---|---|---|---|
| Xe dẫn phanh 3 → 9 m/s² (đâm xe trước) | không | từ 4 m/s² | 1/5 → 4/5 | 0/5 | 0/5 |
| Cắt vào, xe ta 14 m/s, gap 10 m, tiến gần 10 m/s | không | có | 5/5 | 5/5 | 1/5 |
| Cắt vào, gap 20 m, tiến gần 13.5 m/s | không | có | 5/5 | 4/5 | 0/5 |
| Xe dẫn phanh 6 m/s², xe sau **phát lại** (xe sau đâm ta) | có | không | 3/5 | 5/5 | 5/5 |
| Như trên, xe sau **phản ứng** | không | không | 0/5 | 0/5 | 0/5 |
| 24 log thật: số lượt (log × seed) đâm xe trước | 0/24 | 11/24 | 65/120 | 1/120 | 0/120 |

Những gì mô phỏng 3D cho thấy, khớp với các câu ở trên:
- **EgoMLP mù** ([ảnh](bonus/viz_1_brake_egomlp.jpg)). Seed 1 đâm xe dẫn ở 8.6 s với mức phanh mạnh nhất 0.0 m/s²: nó không hề thấy xe dẫn phanh (Câu 4).
- **Va chạm giả** ([ảnh](bonus/viz_2_rear_replay_idm.jpg)). IDM giữ cách xe trước 6.5 m và phanh 7.8 m/s², nhưng xe sau phát lại vẫn đâm vào đuôi ở 10.3 s; const-vel không phanh nên "an toàn" phía sau (Câu 6).
- **Cắt vào** ([PercMLP](bonus/viz_3_cutin_percmlp.jpg), [PercMLP+](bonus/viz_4_cutin_percmlp_plus.jpg)). PercMLP chỉ phanh tới 6.9 m/s² rồi đâm ở 2.1 s; PercMLP+ phanh tới 7.8 m/s² và dừng cách 2.4 m (Câu 7). IDM chỉ đâm ở các ô mà ngay cả phanh μg ≈ 7.85 m/s² cũng không kịp (ví dụ gap 6 m, tiến gần ≥ 10 m/s), tức đúng biên bất khả kháng như Câu 3.
- **Chạy cả 24 log trong trang** ([ảnh](bonus/viz_5_all_logs.jpg)). Kết quả: IDM 0, const-vel 11, EgoMLP 11…17 log tuỳ seed, PercMLP 0…1, PercMLP+ 0. Cùng thứ tự với bảng vòng kín ở bước 4: EgoMLP và const-vel tệ nhất, PercMLP+ ngang IDM.
- **PercMLP+ không tốt đều hơn PercMLP ở mọi ô.** Ở gap 6 m, tiến gần 6 m/s và ở gap 10 m, tiến gần 8 m/s, PercMLP+ đâm 1/5 seed trong khi PercMLP 0/5. Đây thêm một lý do để không nói mô hình học "tốt hơn" khi chưa đo trên biên.
