# Install the BoJack pet into Hermes Agent on Windows.
#   irm https://raw.githubusercontent.com/sounith1/AI-For-Beginners/claude/bold-ptolemy-25s8bp/etc/hermes-pets/bojack/install.ps1 | iex
$Branch = "claude/bold-ptolemy-25s8bp"

$ErrorActionPreference = "Stop"
# Hermes home: $env:HERMES_HOME, else %LOCALAPPDATA%\hermes (the Windows default)
$hermesHome = if ($env:HERMES_HOME) { $env:HERMES_HOME } else { Join-Path $env:LOCALAPPDATA "hermes" }
$dest = Join-Path $hermesHome "pets\bojack"
New-Item -ItemType Directory -Force -Path $dest | Out-Null

$base = "https://raw.githubusercontent.com/sounith1/AI-For-Beginners/$Branch/etc/hermes-pets/bojack"
foreach ($f in "pet.json", "spritesheet.webp") {
    $local = if ($PSScriptRoot) { Join-Path $PSScriptRoot $f } else { "" }
    if ($local -and (Test-Path $local)) { Copy-Item $local $dest -Force }
    else { Invoke-WebRequest -UseBasicParsing "$base/$f" -OutFile (Join-Path $dest $f) }
}
Write-Host "Installed BoJack to $dest"
hermes pets select bojack
