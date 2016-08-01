@echo off

rem Batch file for generating the mod_webkit Apache 2.2/2.4 DSO module.
rem You can either use the full Microsoft Visual Studio 2010
rem or the free Microsoft Visual C++ 2010 Express Edition
rem (download at http://www.microsoft.com/express/download/).
rem We also use the free Microsoft Windows 7 SDK to configure
rem the environment variables and for building the 64bit version
rem (at http://www.microsoft.com/download/details.aspx?id=8442).
rem You may also need the Microsoft Visual C++ 2010 SP1 compiler update
rem (at http://www.microsoft.com/download/details.aspx?&id=4422).

rem The path to your Apache 2.2/2.4 installation
rem (32bit version may be under %ProgramFiles(x86)% on 64bit systems)
set Apache=%ProgramFiles%\Apache Software Foundation\Apache2.2

rem The path to your Windows SDK installation
set SDK=%ProgramFiles%\Microsoft SDKs\Windows\v7.1

rem Setup the environment (use /x64 instead of /x86 to build a 64bit module)
call "%SDK%\bin\setenv" /Release /x86 /win7

set PATH=%Apache%\bin;%PATH%
set INCLUDE=%Apache%\include;%INCLUDE%
set LIB=%Apache%\lib;%LIB%

rem Compile and link mod_webkit
cl /W3 /O2 /EHsc /LD /MT ^
    /D WIN32 /D _WINDOWS /D _MBCS /D _USRDLL ^
    /D MOD_WEBKIT_EXPORTS /D NDEBUG ^
    mod_webkit.c marshal.c ^
    /link libhttpd.lib libapr-1.lib libaprutil-1.lib ws2_32.lib

rem Remove all intermediate results
del /Q *.exp *.ilk *.lib *.obj *.pdb

rem Install mod_webkit
copy mod_webkit.dll "%Apache%\modules\mod_webkit.so"

rem Wait for keypress before leaving
echo.
pause
