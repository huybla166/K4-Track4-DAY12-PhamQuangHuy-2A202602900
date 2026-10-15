# Bonus · Bước 8: model của mình lái trong mô phỏng 3D (không chấm)

```bash
python3 scripts/export_viz.py      # viz/lab_models.js + viz/lab_data.js từ work/models và evidence/ (git-ignored)
python3 viz/serve.py               # xem tay ở http://localhost:8765
node bonus/viz_sweep.js            # quét mọi cảnh trên cả 5 seed -> bonus/viz_sweep.json
```

`viz_sweep.js` dùng lại nguyên `viz/sim.js` và đúng cách dựng cảnh / chấm của `viz/app.js` (`labParams`, `labExec`, `labOutcome`). Chỉ khác là nó chạy cả một lưới thay vì một vị trí thanh trượt, nên mỗi quan sát ở GUIDE bước 8 đi kèm số đếm. Kết quả và cách đọc nằm ở phụ lục cuối `REPORT.md`.

| Ảnh | Cảnh |
|---|---|
| `viz_1_brake_egomlp.jpg` | Xe dẫn phanh 6 m/s²: EgoMLP (seed 1) đâm, phanh mạnh nhất 0.0 m/s² |
| `viz_2_rear_replay_idm.jpg` | Cùng cảnh, xe sau phát lại: IDM bị đâm từ phía sau (va chạm giả) |
| `viz_3_cutin_percmlp.jpg` | Cắt vào gap 10 m, tiến gần 10 m/s, xe ta 14 m/s: PercMLP đâm ở 2.1 s |
| `viz_4_cutin_percmlp_plus.jpg` | Cùng cảnh: PercMLP+ dừng cách 2.4 m |
| `viz_5_all_logs.jpg` | Nút "Chạy cả 24 log, cả năm bộ" trong trang |
