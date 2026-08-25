# Push host code to the Pi and optionally run it.
#
#   .\scripts\deploy.ps1
#   .\scripts\deploy.ps1 -Run "python -m gui.main"
#   .\scripts\deploy.ps1 -Message "fix trigger offset" -Restart
#
# Commits anything dirty, pushes, pulls on the Pi. Keeps the git-only
# workflow to a single command so you are not typing ssh/pull/run by hand
# thirty times an afternoon.

param(
    [string]$Pi        = "tiger@scope.local",
    [string]$PiRepo    = "~/scope",
    [string]$Message   = "wip",
    [string]$Run       = "",
    [switch]$Restart,
    [switch]$NoCommit
)

$ErrorActionPreference = "Stop"

function Step($text) { Write-Host "`n==> $text" -ForegroundColor Cyan }

# --- commit anything outstanding -----------------------------------------
if (-not $NoCommit) {
    $dirty = git status --porcelain
    if ($dirty) {
        Step "committing local changes"
        git add -A
        git commit -m $Message
    } else {
        Write-Host "nothing to commit" -ForegroundColor DarkGray
    }
}

Step "pushing"
git push

# --- pull on the Pi -------------------------------------------------------
Step "pulling on $Pi"
ssh $Pi "cd $PiRepo && git pull --ff-only"
if ($LASTEXITCODE -ne 0) { throw "git pull failed on the Pi" }

# --- optional restart / run ----------------------------------------------
if ($Restart) {
    Step "restarting scope-gui"
    ssh $Pi "systemctl --user restart scope-gui && sleep 1 && systemctl --user is-active scope-gui"
}

if ($Run) {
    Step "running: $Run"
    ssh -t $Pi "cd $PiRepo/host && source ../.venv/bin/activate && $Run"
}

Write-Host "`ndone" -ForegroundColor Green
