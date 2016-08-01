@echo off

rem Batch file for generating the mod_webkit Apache 1.3 DSO module
rem using the free Microsoft Visual C++ Toolkit 2003
rem and Microsoft Windows Server 2003 R2 Platform SDK.
rem It seems that Microsoft Visual C++ 2005 or 2008 Express Edition
rem cannot be used to create modules for the Apache 1.3 binaries.

rem Set paths to Apache, SDK and Visual Studio
set Apache=%ProgramFiles%\Apache Group\Apache
set SDK=%ProgramFiles%\Microsoft Platform SDK for Windows Server 2003 R2

rem Setup the environment
call "%SDK%\setenv"

Set PATH=%Apache%\bin;%PATH%
Set INCLUDE=%Apache%\include;%INCLUDE%
Set LIB=%Apache%\libexec;%LIB%

rem Compile and link mod_webkit
cl /W3 /O2 /EHsc /LD /MT ^
    /D WIN32 /D _WINDOWS /D _MBCS /D _USRDLL ^
    /D _CRT_SECURE_NO_DEPRECATE ^
    /D MOD_WEBKIT_EXPORTS /D NDEBUG ^
    mod_webkit.c marshal.c ^
    /link ApacheCore.lib ws2_32.lib

rem Remove all intermediate results
del /Q *.exp *.ilk *.lib *.obj *.pdb

rem Install mod_webkit
copy mod_webkit.dll "%Apache%\modules\mod_webkit.so"

rem Wait for keypress before leaving
echo.
pause
