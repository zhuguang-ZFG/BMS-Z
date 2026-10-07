# 本地一键复跑 CI 全部检查门（与 .github/workflows/tests.yml 对齐）。
# 用法：powershell -File scripts/local-gates.ps1
# 语义：FAIL 使退出码非零；工具缺失记 SKIP（附安装提示）但不算失败，
#       因为 CI 才是真门禁——本脚本只为提交前自查省时。
#       本地专属的门：「生成图对账」（CI 的 numpy 跟着 requirements 区间走，
#       浮点微差会让无关 PR 变红）、「社交卡对账」（要系统里的中文字体，runner 上没有）、
#       「发布记录对账」（要和 git 标签、gh 的 Release 比，CI 的 checkout 抓不到 tag）、
#       「分类真值对账」（要 gh 登录取 GitHub 上的讨论区分类，runner 上的 gh 没凭证）。
#       理由都见 tools/README.md 与 docs/维护说明.md。
# 注意：本文件必须保存为 UTF-8 with BOM，否则 Windows PowerShell 5.1
#       会按 ANSI 误读中文字节并报"字符串缺少终止符"。
# 解释器探测说明：py 启动器会读被调脚本的 shebang（check_docs.py 首行
#       #!/usr/bin/env python3 在本机解析不到），故候选用 'py -3' 显式
#       选版本、绕过 shebang；scoop 的 python313 若更新中损坏会被探测跳过。
[CmdletBinding()] param()

$root = Split-Path -Parent $PSScriptRoot
$results = [ordered]@{}

# 解释器探测：候选逐一实跑 -c 打印 sys.executable，拿到真实 exe 路径后再用——
# 绕开 shim 坑（本机 2026-10 实测）：WindowsApps 无 python 存根；git-bash/MSYS
# 无法执行 scoop 的 current 联接点路径（PowerShell 下正常）；uv 的 py shim 会
# 读被调脚本 shebang 且 -3 参数报 103。真实 exe 不吃 shebang，与 CI 行为一致。
$pyExe = $null
foreach ($c in @('python', "$env:USERPROFILE\scoop\apps\python313\current\python.exe", 'py')) {
    try {
        $resolved = & $c -c 'import sys; print(sys.executable)' 2>$null
        if ($LASTEXITCODE -eq 0 -and $resolved) {
            $pyExe = ($resolved | Select-Object -Last 1).Trim()
            break
        }
    } catch { }
}

function Invoke-Py {
    # 以探测成功的真实解释器运行，透传全部参数，退出码留在 $LASTEXITCODE
    & $pyExe @args
}

function Add-Result([string]$gate, [string]$status, [string]$note = '') {
    $results[$gate] = @{ status = $status; note = $note }
}

if (-not $pyExe) {
    Add-Result 'python 解释器' 'FAIL' 'python/scoop-python313/py 均不可用'
} else {
    # 1. 文档一致性（docs-consistency job）
    Invoke-Py (Join-Path $root '.github/scripts/check_docs.py')
    Add-Result 'check_docs' $(if ($LASTEXITCODE -eq 0) { 'PASS' } else { 'FAIL' })

    # 2. ruff（python-lint job；版本钉 0.15.21，见 tests.yml 注释）
    #    一律走模块形式：本机 PATH 上有个解析不动的 ruff 存根（Get-Command 说在、
    #    实际 spawn 失败），会把全绿的仓库报成 FAIL。
    $ruffProbe = Invoke-Py -m ruff --version 2>&1 | Out-String
    if ($ruffProbe -match 'No module named') {
        Add-Result 'ruff' 'SKIP' '未安装：pip install ruff==0.15.21'
    } else {
        Invoke-Py -m ruff check $root
        Add-Result 'ruff' $(if ($LASTEXITCODE -eq 0) { 'PASS' } else { 'FAIL' })
    }

    # 3/4/5. pytest 与冒烟（python job）
    $pytestProbe = Invoke-Py -m pytest --version 2>&1 | Out-String
    if ($pytestProbe -match 'No module named') {
        Add-Result 'pytest soc' 'SKIP' 'pytest 未安装：pip install -r code/requirements.txt'
        Add-Result 'pytest protocol' 'SKIP' '同上'
        Add-Result 'compare.py 冒烟' 'SKIP' '同上'
        Add-Result 'pytest 擂台基线' 'SKIP' '同上'
    } else {
        Push-Location (Join-Path $root 'code/soc')
        Invoke-Py -m pytest tests/ -q
        Add-Result 'pytest soc' $(if ($LASTEXITCODE -eq 0) { 'PASS' } else { 'FAIL' })
        Invoke-Py compare.py | Out-Null
        Add-Result 'compare.py 冒烟' $(if ($LASTEXITCODE -eq 0) { 'PASS' } else { 'FAIL' })
        Pop-Location
        Push-Location (Join-Path $root 'code/protocol')
        Invoke-Py -m pytest tests/ -q
        Add-Result 'pytest protocol' $(if ($LASTEXITCODE -eq 0) { 'PASS' } else { 'FAIL' })
        Pop-Location
        Push-Location $root
        Invoke-Py -m pytest challenges/01-soc/test_arena.py challenges/02-frames/test_rescue.py -q
        Add-Result 'pytest 擂台基线' $(if ($LASTEXITCODE -eq 0) { 'PASS' } else { 'FAIL' })
        Pop-Location
    }
}

# 6. 固件（c-firmware job）
if (Get-Command gcc -ErrorAction SilentlyContinue) {
    Push-Location (Join-Path $root 'code/firmware')
    $exe = Join-Path $PWD 'test_bms_local.exe'
    & gcc -std=c99 -Wall -Wextra -Werror -o $exe bms.c test_bms.c
    if ($LASTEXITCODE -eq 0) {
        & $exe
        Add-Result '固件 gcc+run' $(if ($LASTEXITCODE -eq 0) { 'PASS' } else { 'FAIL' })
        Remove-Item $exe -ErrorAction SilentlyContinue
    } else {
        Add-Result '固件 gcc+run' 'FAIL' '编译失败'
    }
    $hil = Join-Path $PWD 'hil_replay_local.exe'
    & gcc -std=c99 -Wall -Wextra -Werror -o $hil bms.c hil_replay.c
    if ($LASTEXITCODE -eq 0) {
        & $hil
        Add-Result 'hil_replay' $(if ($LASTEXITCODE -eq 0) { 'PASS' } else { 'FAIL' })
        Remove-Item $hil -ErrorAction SilentlyContinue
    } else {
        Add-Result 'hil_replay' 'FAIL' '编译失败'
    }
    Pop-Location
} else {
    Add-Result '固件 gcc+run' 'SKIP' 'gcc 不在 PATH'
    Add-Result 'hil_replay' 'SKIP' 'gcc 不在 PATH'
}

# 7. 生成图对账（本地专属，CI 不跑）。把生成器输出写到临时目录，与 assets 里
#    的入库版本逐字节比对。拦两类事故：手改生成产物、改了生成器没重新生成。
#    比对发生在临时目录，不改 assets、也不依赖 git 暂存状态。
$hasNumpy = $false
if ($pyExe) {
    Invoke-Py -c 'import numpy' 2>$null | Out-Null
    $hasNumpy = ($LASTEXITCODE -eq 0)
}
if ($pyExe -and $hasNumpy) {
    $tmpRegen = Join-Path ([IO.Path]::GetTempPath()) ("bmsz-regen-" + [IO.Path]::GetRandomFileName())
    Invoke-Py tools/gen_mechanism_svgs.py --out $tmpRegen 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0 -and (Test-Path $tmpRegen)) {
        $bad = $null
        foreach ($f in Get-ChildItem $tmpRegen -Filter *.svg) {
            $dst = Join-Path $root "docs/circuits/assets/$($f.Name)"
            if (-not (Test-Path $dst) -or ((Get-Content $f.FullName -Raw) -ne (Get-Content $dst -Raw))) {
                $bad = $f.Name
                break
            }
        }
        Add-Result '生成图对账' $(if ($bad) { 'FAIL' } else { 'PASS' }) $(if ($bad) { "$bad 与再生成结果不一致，看 tools/README.md 的对账说明" } else { '' })
    } else {
        Add-Result '生成图对账' 'FAIL' '生成器跑不动：python tools/gen_mechanism_svgs.py 的报错'
    }
    Remove-Item $tmpRegen -Recurse -Force -ErrorAction SilentlyContinue
} else {
    Add-Result '生成图对账' 'SKIP' 'numpy 不可用：pip install -r code/requirements.txt'
}

# 8. 社交卡对账（本地专属，CI 不跑）。这张位图原先没有源：147→148 那轮 README、
#    门户 HTML、路线图动画都跟着改了，只有它还写 147，而它是分享出去最先看到的一张。
#    现在由 tools/gen_social_card.py 画，图上的三个数从仓库现算，这里比对哈希
#    （位图不能按文本比）。CI 不跑：中文字体在系统字体目录，runner 上没有。
$hasPillow = $false
if ($pyExe) {
    Invoke-Py -c 'import PIL' 2>$null | Out-Null
    $hasPillow = ($LASTEXITCODE -eq 0)
}
if ($pyExe -and $hasPillow) {
    $tmpCard = Join-Path ([IO.Path]::GetTempPath()) ("bmsz-card-" + [IO.Path]::GetRandomFileName())
    Invoke-Py tools/gen_social_card.py --out $tmpCard 2>$null | Out-Null
    $gen = Join-Path $tmpCard 'bms-roadmap-social.png'
    $ship = Join-Path $root 'docs/circuits/assets/bms-roadmap-social.png'
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $gen)) {
        Add-Result '社交卡对账' 'FAIL' '生成器跑不动：多半是系统里没有 Noto Sans SC'
    } elseif ((Get-FileHash $gen).Hash -ne (Get-FileHash $ship).Hash) {
        Add-Result '社交卡对账' 'FAIL' '入库的社交卡与再生成结果不一致：跑 python tools/gen_social_card.py'
    } else {
        Add-Result '社交卡对账' 'PASS' ''
    }
    Remove-Item $tmpCard -Recurse -Force -ErrorAction SilentlyContinue
} else {
    Add-Result '社交卡对账' 'SKIP' 'Pillow 不可用：pip install pillow'
}

# 9. 发布记录对账（本地专属，CI 不跑）。docs/维护说明.md 的「发布记录」表抄了
#    标签 sha 和 Release 发布时间，抄错就是一条没人会点的假凭据。CI 的 checkout
#    不抓 tag、也没有 gh 登录，所以这里用 git / gh 的现值比。check_docs.py 里
#    同一张表的文本侧对账 CI 每次都跑，两边不重复。退出码 3 = 缺 git 或 gh，记 SKIP。
if ($pyExe) {
    Invoke-Py .github/scripts/check_docs.py --release-truth
    switch ($LASTEXITCODE) {
        0 { Add-Result '发布记录对账' 'PASS' '' }
        3 { Add-Result '发布记录对账' 'SKIP' '缺 git 或 gh（gh 要登录）：原因见上面的「注意」行；文本侧已对过' }
        default { Add-Result '发布记录对账' 'FAIL' '发布记录表与 git 标签 / gh Release 对不上' }
    }
} else {
    Add-Result '发布记录对账' 'SKIP' 'python 解释器不可用'
}

# 10. 分类真值对账（本地专属，CI 不跑）。维护说明那句「分类现有 N 个，slug 等于
#     中文名」记的是 GitHub 上的状态，CI 的 gh 没凭证取不到。分类真删了、改名了、
#     或 slug 不再等于中文名（发帖表就会套不上），本地这一跑会红。退出码 3 = 缺 gh。
if ($pyExe) {
    Invoke-Py .github/scripts/check_docs.py --categories-truth
    switch ($LASTEXITCODE) {
        0 { Add-Result '分类真值对账' 'PASS' '' }
        3 { Add-Result '分类真值对账' 'SKIP' '缺 gh（要登录）：原因见上面的「注意」行；文本侧已对过' }
        default { Add-Result '分类真值对账' 'FAIL' '分类清单与 GitHub 现存分类 / slug 对不上' }
    }
} else {
    Add-Result '分类真值对账' 'SKIP' 'python 解释器不可用'
}

Write-Host ''
Write-Host '==== 本地门结果 ====' -ForegroundColor Cyan
$fail = $false
foreach ($g in $results.GetEnumerator()) {
    $color = switch ($g.Value.status) { 'PASS' { 'Green' } 'FAIL' { 'Red' } default { 'Yellow' } }
    $line = '{0,-16} {1}' -f $g.Key, $g.Value.status
    if ($g.Value.note) { $line += "  ($($g.Value.note))" }
    Write-Host $line -ForegroundColor $color
    if ($g.Value.status -eq 'FAIL') { $fail = $true }
}
exit $(if ($fail) { 1 } else { 0 })
