' Silent launcher for Job Application Tracker — runs Python without a console window.
Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

' Prefer uv if available (handles Python install), else fall back to python on PATH.
uvPath = sh.ExpandEnvironmentStrings("%USERPROFILE%\.local\bin\uv.exe")

If fso.FileExists(uvPath) Then
    cmd = """" & uvPath & """ run --python 3.12 python """ & scriptDir & "\tracker.py"""
Else
    cmd = "python """ & scriptDir & "\tracker.py"""
End If

' 0 = hidden window, False = don't wait
sh.Run cmd, 0, False
