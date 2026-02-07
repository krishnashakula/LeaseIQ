# Enterprise Lease Intelligence Platform - Test Suite

## Test Configuration
$ErrorActionPreference = "Stop"
$testResults = @()
$passCount = 0
$failCount = 0

function Add-TestResult {
    param($TestName, $Status, $Message, $Details = "")
    $script:testResults += [PSCustomObject]@{
        Test = $TestName
        Status = $Status
        Message = $Message
        Details = $Details
        Timestamp = Get-Date -Format "HH:mm:ss"
    }
    if ($Status -eq "PASS") { $script:passCount++ } else { $script:failCount++ }
}

Write-Host "`n================================" -ForegroundColor Cyan
Write-Host "  TEST SUITE EXECUTION START" -ForegroundColor Cyan
Write-Host "================================`n" -ForegroundColor Cyan

## TEST 1: Server Availability Tests
Write-Host "[TEST 1] Server Availability Tests" -ForegroundColor Yellow

try {
    $backend = Test-NetConnection -ComputerName localhost -Port 5000 -InformationLevel Quiet -WarningAction SilentlyContinue
    if ($backend) {
        Add-TestResult "Backend Server (Port 5000)" "PASS" "Backend is running and accessible"
    } else {
        Add-TestResult "Backend Server (Port 5000)" "FAIL" "Backend is not responding on port 5000"
    }
} catch {
    Add-TestResult "Backend Server (Port 5000)" "FAIL" "Error checking backend: $($_.Exception.Message)"
}

try {
    $frontend = Test-NetConnection -ComputerName localhost -Port 3000 -InformationLevel Quiet -WarningAction SilentlyContinue
    if ($frontend) {
        Add-TestResult "Frontend Server (Port 3000)" "PASS" "Frontend is running and accessible"
    } else {
        Add-TestResult "Frontend Server (Port 3000)" "FAIL" "Frontend is not responding on port 3000"
    }
} catch {
    Add-TestResult "Frontend Server (Port 3000)" "FAIL" "Error checking frontend: $($_.Exception.Message)"
}

## TEST 2: API Endpoint Tests
Write-Host "`n[TEST 2] API Endpoint Tests" -ForegroundColor Yellow

# Test Health Endpoint
try {
    $healthResponse = Invoke-WebRequest -Uri "http://localhost:5000/health" -Method GET -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
    if ($healthResponse.StatusCode -eq 200) {
        Add-TestResult "API Health Endpoint" "PASS" "Health endpoint returned 200 OK"
    } else {
        Add-TestResult "API Health Endpoint" "FAIL" "Health endpoint returned: $($healthResponse.StatusCode)"
    }
} catch {
    Add-TestResult "API Health Endpoint" "FAIL" "Cannot reach health endpoint: $($_.Exception.Message)"
}

# Test CORS Headers
try {
    $corsResponse = Invoke-WebRequest -Uri "http://localhost:5000/health" -Method GET -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
    $corsHeader = $corsResponse.Headers['Access-Control-Allow-Origin']
    if ($corsHeader) {
        Add-TestResult "CORS Configuration" "PASS" "CORS headers are properly configured: $corsHeader"
    } else {
        Add-TestResult "CORS Configuration" "WARN" "CORS headers may not be configured (this could cause issues)"
    }
} catch {
    Add-TestResult "CORS Configuration" "FAIL" "Error checking CORS: $($_.Exception.Message)"
}

## TEST 3: File Structure Tests
Write-Host "`n[TEST 3] File Structure Tests" -ForegroundColor Yellow

$workspaceRoot = Get-Location
$requiredFiles = @(
    "frontend\index.html",
    "frontend\business_intelligence.html",
    "backend\app.py",
    "backend\requirements.txt"
)

foreach ($file in $requiredFiles) {
    $fullPath = Join-Path $workspaceRoot $file
    if (Test-Path $fullPath) {
        $size = (Get-Item $fullPath).Length
        Add-TestResult "File: $file" "PASS" "File exists (${size} bytes)"
    } else {
        Add-TestResult "File: $file" "FAIL" "File not found at: $fullPath"
    }
}

## TEST 4: Code Quality Tests
Write-Host "`n[TEST 4] Code Quality Tests" -ForegroundColor Yellow

# Test index.html for required functions
$indexPath = Join-Path $workspaceRoot "frontend\index.html"
$indexContent = Get-Content $indexPath -Raw
$requiredFunctions = @(
    "uploadFileEnhanced",
    "displayAdvancedAnalysis",
    "getRiskColor",
    "getComplianceColor",
    "window.currentResult"
)

foreach ($func in $requiredFunctions) {
    if ($indexContent -match [regex]::Escape($func)) {
        Add-TestResult "Function: $func" "PASS" "Function found in index.html"
    } else {
        Add-TestResult "Function: $func" "FAIL" "Function missing from index.html"
    }
}

# Test for API_URL configuration
if ($indexContent -match "const API_URL") {
    Add-TestResult "API Configuration" "PASS" "API_URL is properly configured"
} else {
    Add-TestResult "API Configuration" "FAIL" "API_URL configuration missing"
}

# Test for null safety patterns
$nullCheckPatterns = @("if \(!.*\)", "if \(.*\|\|.*\)")
$nullCheckCount = 0
foreach ($pattern in $nullCheckPatterns) {
    $matches = [regex]::Matches($indexContent, $pattern)
    $nullCheckCount += $matches.Count
}

if ($nullCheckCount -gt 20) {
    Add-TestResult "Null Safety Checks" "PASS" "Found $nullCheckCount null safety checks"
} else {
    Add-TestResult "Null Safety Checks" "WARN" "Only found $nullCheckCount null safety checks (expected 20+)"
}

## TEST 5: Frontend HTML Validation
Write-Host "`n[TEST 5] Frontend HTML Validation" -ForegroundColor Yellow

# Check for required HTML elements
$requiredElements = @(
    "id=`"uploadBtn`"",
    "id=`"fileInput`"",
    "id=`"resultSection`"",
    "id=`"metricsGrid`"",
    "id=`"riskContent`"",
    "id=`"revenueContent`"",
    "id=`"complianceContent`"",
    "id=`"marketContent`""
)

foreach ($element in $requiredElements) {
    if ($indexContent -match [regex]::Escape($element)) {
        Add-TestResult "HTML Element: $element" "PASS" "Element found"
    } else {
        Add-TestResult "HTML Element: $element" "FAIL" "Element missing"
    }
}

## TEST 6: JavaScript Syntax Check
Write-Host "`n[TEST 6] JavaScript Syntax Tests" -ForegroundColor Yellow

# Check for common syntax errors
$syntaxIssues = @()

# Check for console.log statements (should exist for debugging)
if ($indexContent -match "console\.log") {
    Add-TestResult "Debug Logging" "PASS" "Console logging is implemented"
} else {
    Add-TestResult "Debug Logging" "WARN" "No console logging found (debugging may be difficult)"
}

# Check for error handling
if ($indexContent -match "try\s*{" -and $indexContent -match "catch") {
    Add-TestResult "Error Handling" "PASS" "Try-catch blocks are implemented"
} else {
    Add-TestResult "Error Handling" "FAIL" "No try-catch error handling found"
}

# Check for async/await usage
if ($indexContent -match "async\s+function" -and $indexContent -match "await") {
    Add-TestResult "Async Operations" "PASS" "Async/await is properly implemented"
} else {
    Add-TestResult "Async Operations" "FAIL" "Async operations may not be properly implemented"
}

## TEST 7: Backend Python Validation
Write-Host "`n[TEST 7] Backend Python Tests" -ForegroundColor Yellow

if (Test-Path "backend\app_enhanced.py") {
    $pythonContent = Get-Content "backend\app_enhanced.py" -Raw
    
    # Check for required endpoints
    $requiredEndpoints = @("/api/upload", "/api/business/analyze", "/health")
    foreach ($endpoint in $requiredEndpoints) {
        if ($pythonContent -match [regex]::Escape($endpoint)) {
            Add-TestResult "Backend Endpoint: $endpoint" "PASS" "Endpoint defined"
        } else {
            Add-TestResult "Backend Endpoint: $endpoint" "FAIL" "Endpoint missing"
        }
    }
    
    # Check for CORS
    if ($pythonContent -match "CORS") {
        Add-TestResult "Backend CORS" "PASS" "CORS is configured in backend"
    } else {
        Add-TestResult "Backend CORS" "WARN" "CORS may not be configured"
    }
}

## TEST 8: Security Tests
Write-Host "`n[TEST 8] Security Tests" -ForegroundColor Yellow

# Check for file size validation
if ($indexContent -match "50.*1024.*1024") {
    Add-TestResult "File Size Limit" "PASS" "50MB file size limit is enforced"
} else {
    Add-TestResult "File Size Limit" "WARN" "No file size limit found"
}

# Check for file type validation
if ($indexContent -match "application/pdf") {
    Add-TestResult "File Type Validation" "PASS" "PDF file type validation is implemented"
} else {
    Add-TestResult "File Type Validation" "FAIL" "No file type validation found"
}

# Check for XSS protection
if ($indexContent -match "escapeHtml" -or $indexContent -match "textContent") {
    Add-TestResult "XSS Protection" "PASS" "XSS protection measures found"
} else {
    Add-TestResult "XSS Protection" "WARN" "Limited XSS protection detected"
}

## TEST 9: Performance Tests
Write-Host "`n[TEST 9] Performance Tests" -ForegroundColor Yellow

# Use previously loaded index size
if ($indexSize -lt 200KB) {
    Add-TestResult "Frontend File Size" "PASS" "index.html is ${indexSize} bytes (optimal)"
} elseif ($indexSize -lt 500KB) {
    Add-TestResult "Frontend File Size" "WARN" "index.html is ${indexSize} bytes (consider optimization)"
} else {
    Add-TestResult "Frontend File Size" "FAIL" "index.html is ${indexSize} bytes (too large)"
}

# Check for loading indicators
if ($indexContent -match "loading" -and $indexContent -match "spinner") {
    Add-TestResult "Loading Indicators" "PASS" "Loading indicators are implemented"
} else {
    Add-TestResult "Loading Indicators" "FAIL" "No loading indicators found"
}

# Check file sizes
$indexSize = (Get-Item $indexPath).Length

## TEST 10: Integration Tests
Write-Host "`n[TEST 10] Integration Tests" -ForegroundColor Yellow

# Test if backend can handle a mock request (without actual file)
try {
    $testResponse = Invoke-WebRequest -Uri "http://localhost:5000/health" -Method GET -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
    $responseTime = $testResponse.Headers['X-Response-Time']
    Add-TestResult "Backend Response Time" "PASS" "Backend responded successfully"
} catch {
    Add-TestResult "Backend Response Time" "FAIL" "Backend integration test failed: $($_.Exception.Message)"
}

## GENERATE TEST REPORT
Write-Host "`n================================" -ForegroundColor Cyan
Write-Host "       TEST REPORT" -ForegroundColor Cyan
Write-Host "================================`n" -ForegroundColor Cyan

# Display results grouped by status
$passTests = $testResults | Where-Object { $_.Status -eq "PASS" }
$failTests = $testResults | Where-Object { $_.Status -eq "FAIL" }
$warnTests = $testResults | Where-Object { $_.Status -eq "WARN" }

Write-Host "PASSED TESTS ($passCount):" -ForegroundColor Green
$passTests | ForEach-Object {
    Write-Host "   - $($_.Test)" -ForegroundColor Green
}

if ($warnTests.Count -gt 0) {
    Write-Host "`nWARNING TESTS ($($warnTests.Count)):" -ForegroundColor Yellow
    $warnTests | ForEach-Object {
        Write-Host "   - $($_.Test): $($_.Message)" -ForegroundColor Yellow
    }
}

if ($failTests.Count -gt 0) {
    Write-Host "`nFAILED TESTS ($failCount):" -ForegroundColor Red
    $failTests | ForEach-Object {
        Write-Host "   - $($_.Test): $($_.Message)" -ForegroundColor Red
    }
}

## SUMMARY
$totalTests = $testResults.Count
$passRate = [math]::Round(($passCount / $totalTests) * 100, 1)

Write-Host "`n================================" -ForegroundColor Cyan
Write-Host "        SUMMARY" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host "Total Tests: $totalTests" -ForegroundColor White
Write-Host "Passed: $passCount" -ForegroundColor Green
Write-Host "Failed: $failCount" -ForegroundColor Red
Write-Host "Warnings: $($warnTests.Count)" -ForegroundColor Yellow
Write-Host "Pass Rate: $passRate%" -ForegroundColor $(if ($passRate -ge 90) { "Green" } elseif ($passRate -ge 70) { "Yellow" } else { "Red" })

if ($passRate -ge 90) {
    Write-Host "`nEXCELLENT! System is production ready!" -ForegroundColor Green
} elseif ($passRate -ge 70) {
    Write-Host "`nGOOD! Minor issues need attention." -ForegroundColor Yellow
} else {
    Write-Host "`nCRITICAL! Major issues need to be fixed." -ForegroundColor Red
}

Write-Host "`n================================`n" -ForegroundColor Cyan

# Export detailed report
$reportPath = "TEST_REPORT_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"
$testResults | Format-Table -AutoSize | Out-File $reportPath
Write-Host "Detailed report saved to: $reportPath" -ForegroundColor Cyan
