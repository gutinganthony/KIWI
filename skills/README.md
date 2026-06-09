# KIWI Stock Analysis Skills

這個目錄放所有「股票分析模組」，每個模組都是一個 Claude Skill，
可以在任何一台機器上安裝後直接用 `/skill名稱` 呼叫。

---

## 現有模組

| Skill | 指令 | 用途 |
|-------|------|------|
| [Serenity 供應鏈選股](./serenity/SKILL.md) | `/serenity analyze $TICKER` | 從 AI 基礎建設 capex 反向追溯供應鏈瓶頸，找被低估的上游小市值股 |
| [WaveTrend 技術分析](./wavetrend/SKILL.md) | `/wavetrend $TICKER` | 用 WaveTrend Oscillator 判斷超買/超賣、進出場時機 |

---

## 在新機器上安裝所有 Skill（一次搞定）

```bash
# 在你的 Mac 上執行（Mac mini 或 MacBook 都一樣）
cd ~/path/to/KIWI   # 換成你實際的 KIWI 目錄路徑
bash skills/setup.sh
```

安裝完後重啟 Claude Code，所有 `/skill` 指令就可以用了。

---

## 新增一個 Skill（未來擴充用）

1. 在 `skills/` 下建一個新資料夾，例如 `skills/my-new-skill/`
2. 在裡面建一個 `SKILL.md` 檔案（照現有的格式寫）
3. 跟 Claude 說「幫我把 skills/my-new-skill 的 SKILL.md push 上去」
4. 在另一台機器 pull 下來後執行 `bash skills/setup.sh` 就安裝好了

> 💡 **Skill 的精髓就是一個 SKILL.md 文字檔。**
> 格式：說明這個 skill 做什麼、有哪些指令、分析步驟是什麼。
> Claude 讀這個檔案就知道怎麼執行。

---

## 技術說明（不想看可以跳過）

- `skills/` 裡的每個資料夾就是一個 skill
- `setup.sh` 會把它們複製到 `~/.claude/skills/` 讓 Claude Code 認得
- 因為 `skills/` 在 git repo 裡，所以 pull/push 就能同步兩台機器
- 不需要額外的伺服器或帳號，純本地運作

---

*最後更新：2026-06-09*
