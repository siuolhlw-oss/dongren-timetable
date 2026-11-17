# 東仁國中課表資料更新與部署

1. 取得同一學期的教師與班級 PDF，先保留原檔。
2. 執行 `python import-pdfs.py teacher.pdf class.pdf`。程式依 PDF 文字位置抽取資料，逐位比對教師頁面節數合計，再逐筆比對兩份課表。
3. 匯入程式的頁面定位、47 位教師／23 張來源課表／733 筆核對值，專供這次 ver9.1 與 ver8.27。新版本若有異動，先核實來源再調整斷言與日期，不要略過錯誤。
4. 檢查 `audit/extracted.json`、來源 PDF 及 `data-validation.json`；不要把 `audit/raw-runs.json` 或原始 PDF 放入公開儲存庫。
5. 帶點的三張共同授課附表依使用者確認合併到主班級；合併時斷言主／附表的科目及時段相同，合併教師名單。資源班保留 `swapPolicy: "review"`。若要開放資源班調課，需先建立學生分組與原班級關係，不能只移除限制。
6. 執行 `python build-data.py` 更新兩個瀏覽器資料檔。
7. 執行 README 的三個 Node 檢查，並以手機／電腦檢查教師、班級、候選比較與返回。
8. 提交到 `siuolhlw-oss/dongren-timetable` 的 `main`。GitHub Pages 使用 `main` 的根目錄。

本專案的 `origin` 是東仁儲存庫；`upstream` 是原始崙背專案。更新東仁資料時推送 `origin`。
