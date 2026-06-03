@echo off
REM Prism 测试运行脚本 (Windows)
REM 使用方法: tests\run_tests.bat [选项]
REM
REM 选项:
REM   --unit      只运行单元测试
REM   --api       只运行 API 测试
REM   --integration  只运行集成测试
REM   --coverage  生成覆盖率报告
REM   --all       运行所有测试（默认）

setlocal enabledelayedexpansion

REM 项目根目录
cd /d "%~dp0.."

REM 打印标题
echo ============================================================
echo   Prism V2.0 测试套件
echo ============================================================
echo.

REM 解析参数
set RUN_UNIT=0
set RUN_API=0
set RUN_INTEGRATION=0
set RUN_COVERAGE=0

:parse_args
if "%~1"=="" goto :check_args
if "%~1"=="--unit" set RUN_UNIT=1
if "%~1"=="--api" set RUN_API=1
if "%~1"=="--integration" set RUN_INTEGRATION=1
if "%~1"=="--coverage" set RUN_COVERAGE=1
if "%~1"=="--all" (
    set RUN_UNIT=1
    set RUN_API=1
    set RUN_INTEGRATION=1
)
shift
goto :parse_args

:check_args
REM 如果没有指定任何选项，运行所有测试
if %RUN_UNIT%==0 if %RUN_API%==0 if %RUN_INTEGRATION%==0 (
    set RUN_UNIT=1
    set RUN_API=1
    set RUN_INTEGRATION=1
)

REM 检查 pytest 是否安装
python -c "import pytest" 2>nul
if errorlevel 1 (
    echo pytest 未安装，正在安装测试依赖...
    pip install pytest pytest-asyncio pytest-cov
)

REM 运行测试
set TOTAL_TESTS=0
set PASSED_TESTS=0
set FAILED_TESTS=0

REM 运行单元测试
if %RUN_UNIT%==1 (
    echo ------------------------------------------------------------
    echo   运行单元测试
    echo ------------------------------------------------------------
    echo.
    if %RUN_COVERAGE%==1 (
        pytest tests\test_*_unit.py -v --cov=src --cov-report=term-missing
    ) else (
        pytest tests\test_*_unit.py -v
    )
    if !errorlevel!==0 (
        echo [92m✅ 单元测试通过[0m
        set /a PASSED_TESTS+=1
    ) else (
        echo [91m❌ 单元测试失败[0m
        set /a FAILED_TESTS+=1
    )
    set /a TOTAL_TESTS+=1
    echo.
)

REM 运行 API 测试
if %RUN_API%==1 (
    echo ------------------------------------------------------------
    echo   运行 API 测试
    echo ------------------------------------------------------------
    echo.
    if %RUN_COVERAGE%==1 (
        pytest tests\test_*_api.py -v --cov=src --cov-report=term-missing
    ) else (
        pytest tests\test_*_api.py -v
    )
    if !errorlevel!==0 (
        echo [92m✅ API 测试通过[0m
        set /a PASSED_TESTS+=1
    ) else (
        echo [91m❌ API 测试失败[0m
        set /a FAILED_TESTS+=1
    )
    set /a TOTAL_TESTS+=1
    echo.
)

REM 运行集成测试
if %RUN_INTEGRATION%==1 (
    echo ------------------------------------------------------------
    echo   运行集成测试
    echo ------------------------------------------------------------
    echo.
    if %RUN_COVERAGE%==1 (
        pytest tests\test_integration.py -v --cov=src --cov-report=term-missing
    ) else (
        pytest tests\test_integration.py -v
    )
    if !errorlevel!==0 (
        echo [92m✅ 集成测试通过[0m
        set /a PASSED_TESTS+=1
    ) else (
        echo [91m❌ 集成测试失败[0m
        set /a FAILED_TESTS+=1
    )
    set /a TOTAL_TESTS+=1
    echo.
)

REM 打印总结
echo ============================================================
echo   测试总结
echo ============================================================
echo.
echo   总测试套件: %TOTAL_TESTS%
echo   通过: %PASSED_TESTS%
echo   失败: %FAILED_TESTS%
echo.

if %FAILED_TESTS%==0 (
    echo [92m✅ 所有测试通过！[0m
    exit /b 0
) else (
    echo [91m❌ 部分测试失败，请检查上面的错误信息。[0m
    exit /b 1
)