---
title: 睡眠修復音頻實驗 — 科學依據 + 製作過程
date_added: 2026-04-21
last_updated: 2026-04-21
topic: health
tags: [sleep, pink-noise, brown-noise, audio, CBT-I, 4-7-8-breathing, body-scan, ElevenLabs, experiment]
version: 1.0
---

## 背景

為了驗證「睡眠修復音頻」是否能幫助解決入睡困難與半夜醒來後難以再次入睡的問題，今天進行了一輪從科學研究出發的音頻製作實驗。

---

## 科學依據整理

### 噪音類型與睡眠的關係

| 類型 | 特性 | 研究結論 |
|------|------|----------|
| 白噪音 (White Noise) | 所有頻率均等 | 高頻刺激感明顯，長期使用爭議較多 |
| 粉紅噪音 (Pink Noise) | -3 dB/倍頻程，中低頻較多 | Penn Medicine (2023)：50 dB 時減少 REM 睡眠約 19 分鐘 |
| 棕色噪音 (Brown Noise) | -6 dB/倍頻程，低頻主導 | 深沉、低頻，腦部較快停止追蹤，干擾更少 |
| Smoothed Brown Noise | 棕色噪音 + 多層平滑濾波 | YouTube 點閱最高類別，像穩定風扇或飛機艙聲 |

**關鍵研究數據：**
- WHO 建議：臥室夜間噪音 ≤ 30 dB
- 臨床甜蜜點：耳朵位置 30–40 dB（2022 雙盲試驗）
- 50 dB 粉紅噪音 → REM 減少，記憶力與情緒調節受損（Penn Medicine 2023）
- 最終選擇：Smoothed Brown Noise，RMS -28 dBFS，手機音量 30–45% 使用

### 音頻引導內容依據

| 技術 | 依據 | 效果 |
|------|------|------|
| 4-7-8 呼吸法 | RCT 驗證 | 活化副交感神經，降低心率與皮質醇 |
| 身體掃描 (Body Scan) | MBSR / CBT-I 核心技術 | 讓大腦從「思考模式」切換至「感知模式」 |
| 漸進式肌肉放鬆 (PMR) | CBT-I 標準療法 | 入睡時間縮短約 22 分鐘 |

---

## 製作過程與迭代記錄

### 版本演進

**V1 — macOS `say` 指令（Meijia 女聲）**
- 結果：聲音太機械，被使用者否定
- 教訓：TTS 語音品質是決定體驗的核心變數

**V2 — ElevenLabs v3（Anna Su 女聲 + Liam 男聲）**
- 腳本加入 `[breathes in slowly]`、`[exhales slowly]`、`[pause]`、`[long pause]` 等音頻標籤
- 備用版（v2 SSML）使用 `<break time="Xs"/>` 格式
- 旁白時長約 4 分鐘，語速約 60 字/分鐘

**粉紅噪音迭代（V1→V5）**

| 版本 | 問題 | 調整 |
|------|------|------|
| V1 | Peak 正規化 → 實際音量太大 | 改用 RMS 正規化 |
| V2 | RMS 7%（-23 dBFS），仍偏響 | 降至 RMS 4%（-28 dBFS）+ 高通 80 Hz |
| V3 | 高頻沙沙聲造成「急促感」 | 三層低通濾波（截止 ~250 Hz）|
| V4 | 粉紅噪音高頻本質問題 | 改用 Smoothed Brown Noise |
| **V5** | **最終版** | Smoothed Brown Noise（3 層平滑）+ Super Deep 版本 |

### 最終混音設定

```
旁白音量：85%
背景噪音（旁白期間）：180%（噪音本身 -28 dBFS，需拉高才可聽見）
背景噪音（旁白結束後）：240%，30 秒緩升
結構：旁白 4 分鐘 → 噪音繼續至第 10 分鐘
```

### 最終檔案（~/Desktop/sleep_final/）

| 檔案 | 聲音 | 噪音 |
|------|------|------|
| `anna_smoothed_brown.wav` | 女聲 Anna Su | Smoothed Brown |
| `anna_super_deep_brown.wav` | 女聲 Anna Su | Super Deep Brown |
| `liam_smoothed_brown.wav` | 男聲 Liam | Smoothed Brown |
| `liam_super_deep_brown.wav` | 男聲 Liam | Super Deep Brown |

---

## Next Steps — 音頻線（Line A）

- [ ] 連續使用 2–3 晚，記錄入睡時間與半夜醒來次數
- [ ] 選出偏好的聲音版本（Anna vs. Liam、Smoothed vs. Super Deep）
- [ ] 根據回饋微調噪音音量比例
- [ ] 評估是否需要更長版本（目前 10 分鐘）或循環播放方式
- [ ] 考慮 Siri 捷徑觸發（無需解鎖手機，半夜醒來直接播放）

---

## 技術筆記

- 所有音頻生成腳本存放於 `/tmp/make_noise_v5.py`、`/tmp/mix_audio.py`
- 使用 macOS `afconvert` 將 MP3 轉 WAV（不需 ffmpeg）
- Python 純 stdlib 混音（`wave`、`struct`、`math`）
- Voss-McCartney 16-row 演算法生成粉紅噪音
- 棕色噪音：積分白噪音（leak=0.998）+ 三層移動平均平滑
