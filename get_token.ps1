# 1. Leer variables del .env
Get-Content .env | ForEach-Object {
    if ($_ -match "^API_KEY=(.*)") { $ApiKey = $matches[1].Trim() }
    if ($_ -match "^SECRET=(.*)") { $Secret = $matches[1].Trim() }
}

# 2. Codificar credenciales en Base64
$Bytes = [System.Text.Encoding]::UTF8.GetBytes("${ApiKey}:${Secret}")
$Encoded = [Convert]::ToBase64String($Bytes)

# 3. Hacer la petición 
$Headers = @{
    "Authorization" = "Basic $Encoded"
    "Content-Type"  = "application/x-www-form-urlencoded"
}

$Body = @{ 
    grant_type = "client_credentials" 
    scope = "read" 
}

$Response = Invoke-RestMethod -Method Post -Uri "https://api.idealista.com/oauth/token" -Headers $Headers -Body $Body

# 4. Imprimir solo el token
Write-Host $Response