
@python.exe %~dp0\setpkgcli set DOS %* > %TEMP%\temp.bat
set /p TOOLOUTPUT= < %TEMP%\temp.bat
%TEMP%\temp.bat
del %TEMP%\temp.bat

