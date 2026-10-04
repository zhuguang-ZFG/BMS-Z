# 本地一键复跑 CI 全部检查门（与 .github/workflows/tests.yml 对齐）。
# 用法：powershell -File scripts/local-gates.ps1
# 语义：FAIL 使退出码非零；工具缺失记 SKIP（附安装提示）但不算失败，
#       因为 CI 才是真门禁——本脚本只为提交前自查省时。
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
    if (Get-Command ruff -ErrorAction SilentlyContinue) {
        & ruff check $root
        Add-Result 'ruff' $(if ($LASTEXITCODE -eq 0) { 'PASS' } else { 'FAIL' })
    } else {
        $ruffOut = Invoke-Py -m ruff check $root 2>&1 | Out-String
        if ($ruffOut -match 'No module named') {
            Add-Result 'ruff' 'SKIP' '未安装：pip install ruff==0.15.21'
        } elseif ($LASTEXITCODE -eq 0) {
            Add-Result 'ruff' 'PASS'
        } else {
            Add-Result 'ruff' 'FAIL'
        }
    }

    # 3/4/5. pytest 与冒烟（python job）
    $pytestProbe = Invoke-Py -m pytest --version 2>&1 | Out-String
    if ($pytestProbe -match 'No module named') {
        Add-Result 'pytest soc' 'SKIP' 'pytest 未安装：pip install -r code/requirements.txt'
        Add-Result 'pytest protocol' 'SKIP' '同上'
        Add-Result 'compare.py 冒烟' 'SKIP' '同上'
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
    Pop-Location
} else {
    Add-Result '固件 gcc+run' 'SKIP' 'gcc 不在 PATH'
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
