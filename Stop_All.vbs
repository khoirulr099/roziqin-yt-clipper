Set objWMIService = GetObject("winmgmts:\\.\root\cimv2")

On Error Resume Next
For Each Process in objWMIService.ExecQuery("Select * from Win32_Process Where Name = 'python3.exe'")
    cmdLine = Process.CommandLine
    If InStr(cmdLine, "bot.py") > 0 Or InStr(cmdLine, "streamlit") > 0 Then
        Process.Terminate()
    End If
Next
On Error GoTo 0

MsgBox "✅ Semua proses sudah dimatikan", vbInformation, "Stopped"