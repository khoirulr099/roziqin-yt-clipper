Set WshShell = CreateObject("Wscript.Shell")

WshShell.Run "cmd /c cd /d C:\Users\khoir\Downloads\youtube-auto-clip && python3 bot.py", 0, False
WScript.Sleep 2000
WshShell.Run "cmd /c cd /d C:\Users\khoir\Downloads\youtube-auto-clip && python3 -m streamlit run app.py", 0, False

MsgBox "✅ Telegram Bot + Web Streamlit sudah berjalan", vbInformation, "Done"