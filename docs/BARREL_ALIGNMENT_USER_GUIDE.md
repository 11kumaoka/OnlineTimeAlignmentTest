# Barrel telescope alignment — 最初に読む実行ガイド

このガイドは `feature/upstream-acts-geometry` の **32-track channel-based closure**
を保存・再現するための入口です。実装確定コミットは
`288e80e934b0acb09ef8eb7001398baea565dcf6`。
新機能、production への切り替え、push/merge はこの milestone に含みません。

まず本書で再現し、コードを読むときは [ソース・処理対応表](BARREL_ALIGNMENT_CODE_MAP.md)、
検証の細部は [closure 技術報告](BARREL_CHANNEL_ALIGNMENT_CLOSURE.md) を参照してください。
以前の段階の報告は履歴です。過去の「alignment は未検証」は当時の範囲を意味し、
今回の限定された closure の否定ではありません。

## 現在できること

Truth DD4hep の実センサー交差点を実 segmentation で量子化した immutable な
RawTrackerHit を、実際の JANA factory とインストール済み EICrecon/ACTS で再構成します。
native TrackStates から Mille を作り、公式 Pede の L1/L2 Global Y 補正を別 XML に適用し、
**新しい eicrecon プロセスで同じ入力チャネルを再構成**して closure を検証します。
Truth は入力生成と最後の評価だけに使用します。

## 前提と作業場所

- host の repository root から実行します。この検証機では
  `/Users/tkumaoka/eic/OnlineTimeAlignmentTest`。
- Docker の既存 `sweet_mahavira` が、この checkout を `/work` に read/write mount しています。
  別環境ではそのマウントを確認し、対応する container 名を設定してください。
- 固定 image の既定値は `environment/container.env.example` の
  `eicweb/eic_xl@sha256:67c914295a92396040c3051360d70786df9c1ee8458264ad0b83cd1a8ccf3d05`。
  `TESTBENCH_CONTAINER` を使う場合、wrapper は既存 container を使うため image pin を
  新規適用しません。実際の image ID は各実行環境で確認してください。
- EICrecon `195966d41899800eaeca6fbafd63cd53735e6543`、ACTS 45.3.0、DD4hep 1.36。
  この build では ROOT 6.38.00、podio 1.7、EDM4hep 1.0、
  EDM4eic `7d7705d9bbd4794b1b875c04258e7d986aea8a47`、JANA2 2026.02.00。
  Python ROOT/podio/numpy、CMake、C++20 compiler、algorithms が必要です。
  正確な package paths は各 build の `CMakeCache.txt` に記録されます。
- `external/install` に公式 Mille と Pede が必要です。
  `environment/dependencies.json` は Mille
  `cec2e880ecaab3d255e08e21c8f70f248c6098d8`、Millepede-II
  `7e3f4f57d993e0e0098d1a40da72823ac9c3207b` を固定します。
  最低限 `cmake/MilleConfig.cmake`、`lib/libMille2.so`、`bin/pede`、
  `bin/inspectMilleBinary` を確認してください。
- 外部依存がない新規 checkout では `environment/setup_dependencies.py` を使用します。
  これはネットワークまたは clean な pinned local sources、Fortran/LAPACK/OpenMP を必要とし、
  `external/` が存在すると拒否します。既存依存を上書きして実行しないでください。
  この milestone は既存の固定 installation を使用しています。
- closure 本体は古い RawHit/Truth サンプルを必要としません。ただし保全回帰には
  `validation/preserved_files.json`、`relocated_data_sha256.json`、`validated_sources.json`
  および `path_migration.json` が参照する既存ファイル・symlink が必要です。
  Git clone だけでは、無視されている歴史データは復元されません。

## 最小の実行手順

以下は host の同じ shell で順に実行します。**すべての名前は未使用であることが必要です。**
再実行時は build/result と regression build の名前を新しいものに変えてください。
既存の失敗ログや結果は削除しません。Docker login の `stty` 警告はこの非対話 wrapper
で出ることがありますが、成功判定は終了コードと stage の complete record です。

**CHECK-ONLY** — checkout、依存、既存 container の確認：

```bash
cd /Users/tkumaoka/eic/OnlineTimeAlignmentTest
git branch --show-current
git log -2 --format='%H %s'
git status --short --untracked-files=all
git diff --check
export TESTBENCH_CONTAINER=sweet_mahavira
docker inspect "$TESTBENCH_CONTAINER" --format '{{.Image}} {{json .Mounts}}'
ls external/install/cmake/MilleConfig.cmake external/install/lib/libMille2.so \
   external/install/bin/pede external/install/bin/inspectMilleBinary
```

`environment/run.sh` は host と container の橋渡しで、login shell 後 `/work` へ移動します。
以下の wrapper コマンドはすべて `result/.environment` も作成し得ます。

**WRITES OUTPUT** — opt-in plugin と validation binaries の新規 build：

```bash
bash environment/run.sh cmake -S /work/localDetEICrecon/experimental/barrel \
  -B /work/build/barrel_onboarding_20261023_01 \
  -DCMAKE_BUILD_TYPE=Release -DTELESCOPE_BUILD_MILLE_PROBE=ON
bash environment/run.sh cmake --build /work/build/barrel_onboarding_20261023_01 -j2
```

主成果物は `TelescopeTracking.so`、`TelescopeMille.so`、
`libTestbenchBarrelMetadata.so`、`BarrelChannels`、`BarrelMilleDerivatives` です。
CMake は Mille を `external/install/cmake` から読みます。
closure driver が build の plugin/library path を設定するため、手作業で production の
plugin installation を変更する必要はありません。

**WRITES OUTPUT** — 32-event closure、ゼロずれ control、JSON/ROOT 検証をまとめて実行：

```bash
bash environment/run.sh python3 validation/barrel_closure/closure.py \
  --build build/barrel_onboarding_20261023_01 \
  --result result/barrel_onboarding_20261023_01 \
  --events 32 --chi2-cut 1000 --step all
```

`--step all` は下表の geometry から check までで、regressions は含みません。
各外部 subprocess の `command.json`、`stdout.log`、`exit.json` と、完了した stage の
`complete.json`（成果物ハッシュ）を保持します。失敗時は同じ stage を再利用せず、
ログを保存して新しい run 名で再実行します。

**CHECK-ONLY** — report の要点と結果を読む：

```bash
python3 - <<'PY'
import json
from pathlib import Path
p = Path('result/barrel_onboarding_20261023_01')
r = json.loads((p/'validation/report.json').read_text())
for key in ('passed', 'events', 'recovered_global_y_mm', 'remaining_geometry_bias_mm',
            'post_correction_mm', 'control_correction_mm', 'input_channel_sha256'):
    print(key, r[key])
for name, row in r['summaries'].items():
    print(name, {k:v for k,v in row.items() if k != 'per_track_chi2' and k != 'residuals_mm'})
print('Pede diagnostics:', r['pede_diagnostics'])
PY
```

**CHECK-ONLY** — GUI 対応 ROOT 環境で diagnostics を開く：

```text
root -l result/barrel_onboarding_20261023_01/validation/closure.root
root [0] new TBrowser;
```

`L0_residuals`～`L4_residuals` は u/v と RecHit-minus-Truth Global Y、
`sensor_centers` は nominal/Truth/corrected の比較です。
`nominal_acts_chi2_stored_ndf` 等もあります。
GUI はグラフィカル環境が必要です。container batch の生成・read-back と GUI 操作は別です。

GUI のない環境では次で保存済み ROOT objects を確認できます。
**CHECK-ONLY**（wrapper の環境用ディレクトリ作成を除く）：

```bash
bash environment/run.sh python3 -c '
import ROOT
ROOT.gROOT.SetBatch(True)
f = ROOT.TFile.Open("/work/result/barrel_onboarding_20261023_01/validation/closure.root")
assert f and not f.IsZombie()
for name in ["sensor_centers", "L0_residuals", "L4_residuals", "nominal_acts_chi2_stored_ndf", "corrected_acts_chi2_stored_ndf"]:
    assert f.Get(name), name
print("ROOT diagnostic objects verified:", f.GetListOfKeys().GetEntries())
f.Close()
'
```


**CHECK-ONLY**（wrapper の環境用ディレクトリ作成を除く）— 公式 Mille binary decoder：

```bash
bash environment/run.sh bash -lc '
  export LD_LIBRARY_PATH=/work/external/install/lib:$LD_LIBRARY_PATH
  exec /work/external/install/bin/inspectMilleBinary \
    /work/result/barrel_onboarding_20261023_01/nominal/mille.dat'
```

**WRITES OUTPUT** — 独立 regression を新しい stage に出す：

```bash
bash environment/run.sh python3 validation/barrel_closure/closure.py \
  --build build/barrel_onboarding_20261023_01 \
  --result result/barrel_onboarding_20261023_01 \
  --events 32 --chi2-cut 1000 --step regressions --validation-name onboarding
```

これは `onboarding_regressions/` に18コマンドのログを保存し、別 build に geometry probe と
standalone one-track を再 build します。one-event JANA、PODIO read-back、native/legacy writer、
16-ray 数学 fixture、46 unit tests、安全拒否、保全を確認します。
46 tests は成功しても既存 SQLite ResourceWarning を出す場合があります。警告はログに残します。

**CHECK-ONLY** — 歴史ファイルと旧実装の保全（host Python 可）：

```bash
python3 validation/verify_preservation.py
git diff --check
git status --short
```

上記 commands に source の変更や commit/push はありません。
依存の初回 install は別途 **WRITES OUTPUT**、`git add`/`git commit` は
**MODIFIES SOURCE/REPOSITORY** です。

## stage を個別に実行する場合

共通引数を上記と同じにして `--step all` を次の名前に置き換えます。
別の再現 run を作るときは、新しい `--result` を全 stage で共通使用します。
既存 report への追加 check は `--validation-name fresh_identifier` が必要です。

| `--step` | 必要な入力・先行 stage | 出力・成功の意味 |
|---|---|---|
| geometry | maintained XML、barrel fixture builder | `geometry/fixtures/nominal.xml` と `geometry/truth.xml`、L1/L2 +0.150/+0.200 mm |
| data | geometry、BarrelChannels | `data/shifted.root` と `control.root`、別 Truth JSON、quantization/ID/hash 検証 |
| nominal | data、nominal XML、derivative executable | fresh JANA、`nominal/reco.root`・audit・mille.dat/json、32 accepted |
| solve | nominal の32 native Mille records | `solve/millepede.res`、rank 2、Schur/Pede 一致、status 0/1 |
| correct | solve、nominal XML | `correction/corrected.xml`、補正 provenance、実 Geometry/ID audit |
| corrected | data、correction、nominal の cut 記録 | 同じ shifted.root を新規 JANA で再構成、同一チャネル hash |
| postsolve | corrected records | 再構成後の残りの補正を Pede で診断 |
| control | data、nominal XML | 独立 nominal-channel 入力のゼロずれ control 再構成 |
| controlsolve | control records | control 補正がゼロと整合 |
| check | 上記すべて、評価用 offline Truth | `validation/report.json`・closure.root、whitelist/EDM/seed/closure gates |
| regressions | nominal、geometry/data、plugin build、歴史保全データ | `NAME_regressions/complete.json` の passed、18コマンド正常終了 |

`pilot` は geometry/data 後の独立4イベント試験です。default cut の失敗を調査する用途であり、
32-event complete closure の代替ではありません。`--events` は16～64のみ受理、検証済み cohort は32。

### `--chi2-cut 1000` の意味

deliberately misaligned fixture に upstream default 15 を使った4-event pilot は 0/4 accepted
でした。そこで本 closure では
`-PTelescopeTracking:TelescopeCKF:Chi2CutOff=1000` を全 nominal/corrected/control pass に
同じ値で指定します。driver は pass 間で異なる cut を拒否します。
各面1候補の捕捉範囲を広げる設定であり、誤差、Kalman weight、solver の調整ではありません。
一般の EICrecon に1000を推奨するものではなく、one-event regression は default 15 を維持します。

## 期待する結果と読み方

| 指標 | 参照値 |
|---|---:|
| nominal / corrected / control accepted | 各32/32 |
| 各 track | SiMAPS 5測定、outlier 0、未測定MPGD/AC-LGADのhole 2 |
| Mille | 各32 records、320 scalar equations |
| L1 / L2 Global Y 回収補正 | 約 +149.14 / +203.18 um |
| corrected minus Truth | 約 −0.86 / +3.18 um |
| nominal ACTS chi2 / stored NDF | 約37.167316 |
| corrected ACTS chi2 / stored NDF | 約0.690849 |
| control ACTS chi2 / stored NDF | 約0.641260 |
| Pede | rank 2、rejected local fits 0 |
| nominal/postsolve Pede | process exit 0、end status 1、chi2/NDF 約1.163519 |

Pede status 1 は warning であり、単独では solve 失敗ではありません。
ログの約1.08倍の誤差拡大提案は適用していません。warning を消すための誤差 rescaling はしません。
近似物理値の比較には declared tolerance（5 nominal errors、約10.963/10.255 um）を使い、
同じチャネル・EDM relations・固定 source hashes は別の厳密 regression として検証します。
Pede text の丸めは6e-6 mmの比較許容値です。ROOT ファイル全体の byte hash は、作成時刻等に
より再生成間で同じとは限りません。run 内で同じ入力が不変であることと、canonical channel
payload hash の一致を確認します。

chi2/NDF、derivative と Geometry 更新の詳しい意味は
[コード対応表](BARREL_ALIGNMENT_CODE_MAP.md#alignment-と-geometry-更新) を参照してください。

## 現在の制約と保守方針

zero field、ACTS assigned material/process noise なし、synthetic quantized-channel、
L1/L2 physical Global Y の2自由度だけを検証しています。Geant4/electronics、任意6-DOF、
磁場/物質を含む alignment、coverage、大規模統計、production Controller 統合は未検証です。
q/p は1 GeV electron の beam prior で、zero field で測定した運動量ではありません。

`provenance.json` と `upstream_diffs/` を保ち、各変更を座標/型/基準面ごとに置き換えます。
同じクラス名や collection 型だけを理由に交換しないでください。upstream が optional B0、
XZ covariance と seed reference/hypothesis を満たしたとき、既存の anisotropic covariance、
one-track、channel closure、保全回帰を通して局所コピーを一つずつ減らすのが最小の保守手順です。
旧 BeamTestReco/Controller は独立して保存し、この milestone では production へ自動昇格しません。
