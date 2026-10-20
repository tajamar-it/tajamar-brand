param([string]$In, [string]$Out)
# Convierte un .docx o .pptx a PDF con Word/PowerPoint (solo Windows con Office).
$ext = [IO.Path]::GetExtension($In).ToLower()
if ($ext -eq '.docx') {
  $w = New-Object -ComObject Word.Application
  $w.Visible = $false
  $w.DisplayAlerts = 0
  $w.AutomationSecurity = 3
  try {
    $d = $w.Documents.Open($In, $false, $true, $false, '', '', $true, '', '', 0, 0, $false, $true)
    $d.ExportAsFixedFormat($Out, 17)
    $d.Close(0)
  } finally { $w.Quit() }
} else {
  $p = New-Object -ComObject PowerPoint.Application
  $p.AutomationSecurity = 3
  try {
    $x = $p.Presentations.Open($In, $true, $false, $false)
    $x.SaveAs($Out, 32)
    $x.Close()
  } finally { $p.Quit() }
}
