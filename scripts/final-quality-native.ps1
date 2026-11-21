# Run serially after profiling/soak: Tauri uses a single native instance.
$ErrorActionPreference = 'Stop'
$qualityRoot = Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $qualityRoot
$qualityOutput = Join-Path $qualityRoot '.artifacts/final-quality'
New-Item -ItemType Directory -Force -Path $qualityOutput | Out-Null
$qualityHash = (Get-FileHash -Algorithm SHA256 -LiteralPath 'src-tauri/target/release/nekoafk.exe').Hash.ToLowerInvariant()
$qualityStarted = (Get-Date).ToUniversalTime().ToString('o')
python tests/engineering_native.py *> "$qualityOutput/native-desktop-run.log"
if ($LASTEXITCODE -ne 0) { throw 'Native desktop acceptance failed; inspect native-desktop-run.log' }
Copy-Item -LiteralPath '.artifacts/engineering/desktop-native.json' -Destination "$qualityOutput/native-desktop.json"
python tests/native_smoke.py *> "$qualityOutput/native-smoke-run.log"
if ($LASTEXITCODE -ne 0) { throw 'Full native acceptance failed; inspect native-smoke-run.log' }
Copy-Item -LiteralPath '.artifacts/native-validation/report.json' -Destination "$qualityOutput/native-smoke-report.json"
python tests/character_native.py --soak 180 --continuous --art .artifacts/final-quality/character *> "$qualityOutput/character-run.log"
if ($LASTEXITCODE -ne 0) { throw 'Native character regression failed; inspect character-run.log' }
if ((Get-FileHash -Algorithm SHA256 -LiteralPath 'src-tauri/target/release/nekoafk.exe').Hash.ToLowerInvariant() -ne $qualityHash) { throw 'Executable changed during native acceptance' }
@{ exe_sha256 = $qualityHash; started_utc = $qualityStarted; finished_utc = (Get-Date).ToUniversalTime().ToString('o'); suites = @('engineering_native.py', 'native_smoke.py', 'character_native.py --soak 180 --continuous'); result = 'passed' } | ConvertTo-Json | Set-Content -LiteralPath "$qualityOutput/native-suite-build.json" -Encoding utf8
node scripts/final-quality-summary.mjs
if ($LASTEXITCODE -ne 0) { throw 'Evidence summary failed' }
