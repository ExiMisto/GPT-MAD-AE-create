param(
    [string]$RepositoryUrl = 'https://github.com/ExiMisto/GPT-MAD-AE-create.git',
    [string]$Python = 'python',
    [string]$CommitMessage = 'Add still-image MAD production research and reusable tools'
)
$ErrorActionPreference = 'Stop'
if ($RepositoryUrl -notmatch '^https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\.git)?$') {
    throw 'Expected an HTTPS GitHub repository URL'
}
Set-Location -LiteralPath $PSScriptRoot
& $Python 'tools/release_audit.py' '--root' '.'
if ($LASTEXITCODE -ne 0) { throw 'Publication audit failed; no Git changes made' }
if (-not (Test-Path -LiteralPath '.git')) {
    & git init -b main
    if ($LASTEXITCODE -ne 0) { throw 'git init failed' }
} else {
    throw 'This directory already contains a Git repository. Review and commit manually.'
}
& git add .
if ($LASTEXITCODE -ne 0) { throw 'git add failed' }
& git commit -m $CommitMessage
if ($LASTEXITCODE -ne 0) { throw 'git commit failed (configure your name/email if needed)' }
Write-Output 'Local commit created. Run the following commands yourself to publish:'
Write-Output ('git remote add origin ' + $RepositoryUrl)
Write-Output 'git push -u origin main'

