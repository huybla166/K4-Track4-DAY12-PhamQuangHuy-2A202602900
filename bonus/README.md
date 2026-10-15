# Bonus · Bước 8: model của mình lái trong mô phỏng 3D (không chấm)

Phụ lục của `REPORT.md`. Không chấm điểm; số ở đây lấy từ `bonus/viz_sweep.json`, không thuộc `evidence/`.

`python scripts/export_viz.py` xuất 15 model (3 loại × 5 seed) và 24 log test giữ lại (12 log có xe dẫn phanh mạnh nhất, tìm bằng `mine_braking` của mình) sang `viz/`. Mình xem trong trình duyệt (`python viz/serve.py`), rồi quét **toàn bộ** các cảnh trên cả 5 seed bằng `node bonus/viz_sweep.js`. Script này dùng lại đúng `viz/sim.js` và cách chấm của `viz/app.js`; kết quả ở `bonus/viz_sweep.json`. Mô phỏng 3D có vật lý riêng (xe đạp động học, 20 Hz, μ = 0.8), nên chỉ so **hình dạng** với `evidence/`, không so số.

| Quan sát (số seed đâm / 5) | IDM | const-vel | EgoMLP | PercMLP | PercMLP+ |
|---|---|---|---|---|---|
| Xe dẫn phanh 3 → 9 m/s² (đâm xe trước) | không | từ 4 m/s² | 1/5 → 4/5 | 0/5 | 0/5 |
| Cắt vào, xe ta 14 m/s, gap 10 m, tiến gần 10 m/s | không | có | 5/5 | 5/5 | 1/5 |
| Cắt vào, gap 20 m, tiến gần 13.5 m/s | không | có | 5/5 | 4/5 | 0/5 |
| Xe dẫn phanh 6 m/s², xe sau **phát lại** (xe sau đâm ta) | có | không | 3/5 | 5/5 | 5/5 |
| Như trên, xe sau **phản ứng** | không | không | 0/5 | 0/5 | 0/5 |
| 24 log thật: số lượt (log × seed) đâm xe trước | 0/24 | 11/24 | 65/120 | 1/120 | 0/120 |

Những gì mô phỏng 3D cho thấy, khớp với các câu trả lời trong `REPORT.md`:
- **EgoMLP mù** ([ảnh](viz_1_brake_egomlp.jpg)). Seed 1 đâm xe dẫn ở 8.6 s với mức phanh mạnh nhất 0.0 m/s²: nó không hề thấy xe dẫn phanh (REPORT.md, Câu 4).
- **Va chạm giả** ([ảnh](viz_2_rear_replay_idm.jpg)). IDM giữ cách xe trước 6.5 m và phanh 7.8 m/s², nhưng xe sau phát lại vẫn đâm vào đuôi ở 10.3 s; const-vel không phanh nên "an toàn" phía sau (REPORT.md, Câu 6).
- **Cắt vào** ([PercMLP](viz_3_cutin_percmlp.jpg), [PercMLP+](viz_4_cutin_percmlp_plus.jpg)). PercMLP chỉ phanh tới 6.9 m/s² rồi đâm ở 2.1 s; PercMLP+ phanh tới 7.8 m/s² và dừng cách 2.4 m (REPORT.md, Câu 7). IDM chỉ đâm ở các ô mà ngay cả phanh μg ≈ 7.85 m/s² cũng không kịp (ví dụ gap 6 m, tiến gần ≥ 10 m/s), tức đúng biên bất khả kháng như REPORT.md, Câu 3.
- **Chạy cả 24 log trong trang** ([ảnh](viz_5_all_logs.jpg)). Kết quả: IDM 0, const-vel 11, EgoMLP 11…17 log tuỳ seed, PercMLP 0…1, PercMLP+ 0. Cùng thứ tự với bảng vòng kín ở bước 4: EgoMLP và const-vel tệ nhất, PercMLP+ ngang IDM.
- **PercMLP+ không tốt đều hơn PercMLP ở mọi ô.** Ở gap 6 m, tiến gần 6 m/s và ở gap 10 m, tiến gần 8 m/s, PercMLP+ đâm 1/5 seed trong khi PercMLP 0/5. Đây thêm một lý do để không nói mô hình học "tốt hơn" khi chưa đo trên biên.

## Chạy lại

```bash
python3 scripts/export_viz.py      # viz/lab_models.js + viz/lab_data.js từ work/models và evidence/ (git-ignored)
python3 viz/serve.py               # xem tay ở http://localhost:8765
node bonus/viz_sweep.js            # quét mọi cảnh trên cả 5 seed -> bonus/viz_sweep.json
```

`viz_sweep.js` dùng lại nguyên `viz/sim.js` và đúng cách dựng cảnh / chấm của `viz/app.js` (`labParams`, `labExec`, `labOutcome`). Chỉ khác là nó chạy cả một lưới thay vì một vị trí thanh trượt, nên mỗi quan sát ở GUIDE bước 8 đi kèm số đếm.

| Ảnh | Cảnh |
|---|---|
| `viz_1_brake_egomlp.jpg` | Xe dẫn phanh 6 m/s²: EgoMLP (seed 1) đâm, phanh mạnh nhất 0.0 m/s² |
| `viz_2_rear_replay_idm.jpg` | Cùng cảnh, xe sau phát lại: IDM bị đâm từ phía sau (va chạm giả) |
| `viz_3_cutin_percmlp.jpg` | Cắt vào gap 10 m, tiến gần 10 m/s, xe ta 14 m/s: PercMLP đâm ở 2.1 s |
| `viz_4_cutin_percmlp_plus.jpg` | Cùng cảnh: PercMLP+ dừng cách 2.4 m |
| `viz_5_all_logs.jpg` | Nút "Chạy cả 24 log, cả năm bộ" trong trang |
