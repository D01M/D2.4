# GitHub Release Creator Script
# Usage: ./create_release.ps1 -Token YOUR_GITHUB_TOKEN

param(
    [Parameter(Mandatory=$false)]
    [string]$Token = $env:GITHUB_TOKEN
)

if (-not $Token) {
    Write-Host "Error: GITHUB_TOKEN environment variable not set or -Token not provided"
    Write-Host "Get a token from: https://github.com/settings/tokens"
    exit 1
}

$owner = "DarkSidePast"
$repo = "darkTM2.3"
$tag = "v1.0.0"
$zipPath = "dist\OpenSeismo-Lite-v1.0.0.zip"

$headers = @{
    "Authorization" = "token $Token"
    "Accept" = "application/vnd.github.v3+json"
}

$body = @{
    tag_name = $tag
    name = "v1.0.0 - Tsunami Warning System Release"
    body = "Initial release with tsunami warning system, CartoDB neutral map tiles, and infinite tab spawning bug fix. Ready for production use.`n`nFeatures:`n- JMA-inspired tsunami warning system`n- Geopolitically neutral map visualization`n- Multi-source earthquake data`n- Seismic station network support`n- Fixed infinite tab spawning bug"
    draft = $false
    prerelease = $false
} | ConvertTo-Json

$releaseUrl = "https://api.github.com/repos/$owner/$repo/releases"

Write-Host "Creating release..."
$release = Invoke-RestMethod -Uri $releaseUrl -Method POST -Headers $headers -Body $body

Write-Host "Release created: $($release.html_url)"
Write-Host "Uploading asset..."

$uploadUrl = $release.upload_url -replace '\{\?name,label\}', "?name=OpenSeismo-Lite-v1.0.0.zip"

$fileBytes = [System.IO.File]::ReadAllBytes((Resolve-Path $zipPath))

$uploadHeaders = @{
    "Authorization" = "token $Token"
    "Content-Type" = "application/zip"
}

$asset = Invoke-RestMethod -Uri $uploadUrl -Method POST -Headers $uploadHeaders -Body $fileBytes

Write-Host "Asset uploaded successfully!"
Write-Host "Release available at: $($release.html_url)"
