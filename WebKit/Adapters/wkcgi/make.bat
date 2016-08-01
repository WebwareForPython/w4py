@echo off

rem Batch file for generating the wkcgi.exe CGI executable
rem using the free Microsoft Visual C++ 2010 Express Edition
rem (download at http://www.microsoft.com/express/download/).

rem Path to Visual Studio (Visual C++) 10
rem (32bit version may be under %ProgramFiles(x86)% on 64bit systems)
set VC=%ProgramFiles(x86)%\Microsoft Visual Studio 10.0\VC

call "%VC%\vcvarsall"

rem Compile and link wkcgi
cl /W3 /O2 /EHsc /wd4996 ^
    /D WIN32 /D _CONSOLE /D _MBCS  ^
    wkcgi.c ^
    ..\common\wkcommon.c ..\common\marshal.c ^
    ..\common\environ.c ..\common\parsecfg.c ^
    /link wsock32.lib /subsystem:console


rem Remove all intermediate results
del /Q *.exp *.ilk *.lib *.obj *.pdb

rem Wait for keypress before leaving
echo.
pause
