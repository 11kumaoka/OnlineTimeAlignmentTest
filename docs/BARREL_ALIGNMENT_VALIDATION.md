# Barrel alignment documentation milestone — 実行・保全記録

対象 repository は `11kumaoka/OnlineTimeAlignmentTest`、branch は
`feature/upstream-acts-geometry`。作業識別子は `barrel_onboarding_20261023_01`。
本記録の commands は [user guide](TELESCOPE_ALIGNMENT_USER_GUIDE.md) のものを実行しました。
source の物理/再構成/誤差/selection model は変更していません。

## 実装確定前のレビュー

開始時 HEAD は `f0d15a97aed49386021ea6b6d980b19bfcdfe970`。
tracked modifications は README 2件、CMake、FactoryAudit、TelescopeTracking、
TelescopeMille、provenance、BarrelMilleDerivatives、fixture prepare の9件でした。
untracked source/documentation は closure report、closure.py、BarrelChannels.cc、
CollectionCollector header とその空 upstream patch の5件。
closure report の Files and reuse と各変更を照合し、unrelated modifications はありませんでした。
`build/`、`result/`、`external/`、ROOT/Mille/log files は ignore されており stage していません。

- 旧 final closure の2 output hashes と final regressions の73 output hashes を照合：一致。
- `closure.py --step check --validation-name milestone_review_20261023` を既存 run の
  **新 stage** へ実行：成功。既存 report/root は上書きしていません。
- 46 unit tests、安全拒否チェック、221 baseline records / 2046 relocated files / 元 validated
  source・symlink・electron fitter diff の preservation：成功。
- pinned EICrecon の29 reviewed sources の SHA256 を実 Git objects と照合：一致。
- 9 copied file patches を再生成し、保存済み patches と byte 比較：一致。
  unchanged helper 2件は空 diff です。
- 別 upstream checkout の既存 `TimeframeSplitter.h` 編集と未追跡 ROOT はそのまま保持し、
  baseline は checkout working tree ではなく pinned commit の content を使用しました。

14ファイルだけを stage し、実装をローカル commit：

```text
288e80e934b0acb09ef8eb7001398baea565dcf6
Validate 32-track EICrecon-style barrel alignment closure
```

この直後の working tree は空でした。push、merge、production branch の操作はありません。

## 新規ディレクトリでの再現

使用 container: `sweet_mahavira`。mount: 本 repository → `/work`。
実 image ID は
`sha256:67c914295a92396040c3051360d70786df9c1ee8458264ad0b83cd1a8ccf3d05`。
EICrecon pin、ACTS 45.3.0、DD4hep 1.36 と他 package paths は
`build/barrel_onboarding_20261023_01/CMakeCache.txt` に記録されています。

| 実行 | 出力 | 結果 |
|---|---|---|
| guide の CMake configure/build | `build/barrel_onboarding_20261023_01/` | 全 targets build 成功 |
| guide の `--step all --events 32 --chi2-cut 1000` | `result/barrel_onboarding_20261023_01/` | geometry から check まで10 stages成功 |
| guide の `--step regressions --validation-name onboarding` | 同 run の `onboarding_regressions/` | 18 external commands、すべて exit 0 |
| guide の公式 `inspectMilleBinary` | nominal/mille.dat → decoder log | 32 records 読み取り成功 |
| guide の ROOT batch inspection | validation/closure.root | 非 zombie、42 keys、指定 canvas/histograms 取得成功 |
| guide の preservation command | baseline/source/path manifests | 元ファイル不変、成功 |

host-side build/closure/regression/decoder/ROOT read-back logs は
`result/barrel_onboarding_execution_20261023_01/` に保存しています。
各 closure/regression subprocess の正確な argv/cwd/exit/stdout は run 内の
`command.json`、`exit.json`、`stdout.log` に保存されています。
別 source diff audit は `result/barrel_onboarding_upstream_20261023_01/`。
GUI の TBrowser 操作は headless container では実施していません。batch 生成・read-back を確認しました。

全 regression は次の18 commandsです：geometry configure/build、benchmark configure/build、
geometry probe/check、standalone one-track、fixture input、one-event JANA、one-event read-back、
legacy writer、native/legacy comparison、mathematical fixture generation/Pede/check、
46 unit tests、safety、preservation。

## 実測値

| 指標 | nominal | corrected | zero-shift control |
|---|---:|---:|---:|
| processed / accepted / rejected | 32 / 32 / 0 | 32 / 32 / 0 | 32 / 32 / 0 |
| 各trackの測定 / outlier / hole | 5 / 0 / 2 | 5 / 0 / 2 | 5 / 0 / 2 |
| official Mille records | 32 | 32 | 32 |
| ACTS chi2 sum | 11893.541015625 | 221.07172513008118 | 205.2031548023224 |
| ACTS stored NDF sum | 320 | 320 | 320 |
| ACTS chi2 / stored NDF | 37.16731567382813 | 0.6908491410315036 | 0.6412598587572574 |

| 補正/比較 [um] | L1 | L2 |
|---|---:|---:|
| Truth に注入 | +150 | +200 |
| 公式 Pede 回収・実適用 | +149.14 | +203.18 |
| corrected minus Truth | −0.86 | +3.18 |
| corrected reconstruction からの残補正 | −0.00044872 | +0.0028774 |
| zero-shift control の補正 | −2.4148 | +0.7495 |

Pede の3 solves は rank 2、zero rejected local fits。
nominal/postsolve は process exit 0 / end status 1
`Ended with warnings (bad measurements)`、control は end status 0。
Pede chi2/statistical-NDF≈221.068691/190≈1.163519。
標準偏差の拡大提案は適用していません。

fresh canonical channel payload SHA256：

```text
d0c1be6ec40aa9bfa95e0e9c2bf42aaf1b05fa5b4147c3fddf272c2d5871c6b1
```

旧 `result/barrel_closure_20261024_03/final_closure/report.json` と新 report は、
`immutable_input_file_sha256` を除く全 top-level fields が一致しています。
全3 pass の per-track chi2 配列、residual arrays、補正、canonical channel payload は完全一致。
新旧 ROOT container 自体の byte hash は異なりますが、run 内では同じ shifted.root の
file SHA と payload SHA を nominal/corrected 前後で照合して不変性を確認しました。
物理の近似回収値・5sigma tolerance と、厳密な deterministic comparisons は分離しています。

新 run の全 `complete.json` の output hashes を最終確認：一致。
旧 final closure 2 hashes / final regressions 73 hashes も再確認：すべて不変。
validation manifests の221 baseline records、2046 relocated files、validated source と electron diff も不変。
歴史的 run 名に日付風文字列が含まれていても、この milestone で名称・内容を変更していません。

## 警告、失敗ログ、変更の範囲

今回の新規 build、closure、18 regression commands に失敗はありません。
Pede の上記 warning、Docker login の非対話 `stty` warning、既存 SQLite ResourceWarning は
それぞれのログに残っています。46 tests の終了は OK。
旧 `_01`/`_02` の writer API/default-cut/CLI qualification 等の失敗記録はそのまま保存しています。
今回、それらを消すための source 変更や physics assumptions の変更は行いませんでした。

実装コミット後の変更は、本 guide・source map・この record と README links、
過去 closure report の「未コミット」記述への最小の時点注記だけです。
新しい abstraction、fit、alignment parameter、Controller、誤差設定は追加していません。
文書の bash snippets の構文を確認し、relative links と source paths を確認しました。
最終 commit は `git log -2 --format='%H %s'` で確認できます。

検証範囲は synthetic quantized channels / zero field / no ACTS material /
L1-L2 physical Global Y only。production activation、field/material-aware alignment、一般6-DOF、
real electronics、statistical coverage は未検証のままです。
