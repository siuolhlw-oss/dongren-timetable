# 東仁國中課表

雲林縣立東仁國民中學 115 學年度第一學期教師與班級課表查詢網站。

網站：https://siuolhlw-oss.github.io/dongren-timetable/

此獨立專案複製自 [崙背國中課表](https://github.com/siuolhlw-oss/lunbei-timetable)，保留教師／班級查詢、科目搜尋、手機單日與整週切換、班級返回，以及同班雙方無衝堂的調課候選與課表比較。

## 資料

- 教師課表 ver9.1：47 位教師、733 筆授課紀錄。
- 班級課表 ver8.27：23 張來源課表，733 筆授課紀錄與教師課表完全相符。
- 適用期間：2026-08-31 至 2027-01-20。
- 第 1 節 08:30 開始，第 8 節 16:50 結束；班級原表另列 08:00–08:20 導師時間。
- 17 個一般班級：101–106、201–206、301–305；3 個資源班：707、807、906。
- 使用者已確認 `106.`、`206.`、`305.` 是共同授課附表，15 個共同授課時段併入同號主班級，顯示所有教師。原始班級代碼保存在 `sourceClassIds`。
- 共同授課與資源班課程需確認協同教師及學生分組，暫不產生直接調課候選。一般班級的單一教師課程正常提供候選。
- 導師職務依教師 PDF 表頭，不由任教科目推定導師班級。

原始 PDF 保留在使用者端，不隨公開網站上傳。`timetable.json` 保存科目、節次、頁碼及來源雜湊；`data-validation.json` 保存交叉核對結果。

## 使用與維護

- [使用說明](user-manual.html)
- [資料核對紀錄](DATA-REVIEW.md)
- [資料更新與部署](operator-manual.md)
- [資料格式與調課規則](data-contract.md)

純 HTML、CSS、JavaScript，無需後端或登入；GitHub Pages 從 `main` 分支根目錄部署。

```sh
python import-pdfs.py teacher.pdf class.pdf
python build-data.py
node swap-engine.cjs
node candidate-preview.test.cjs
node mobile-today.test.cjs
python -m http.server 8767 --bind 127.0.0.1
```

匯入程式需要 `pypdf`。原始文字抽取保存在忽略的 `audit/` 資料夾，不會發布。
