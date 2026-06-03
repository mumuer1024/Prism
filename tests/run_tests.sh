#!/bin/bash
# Prism 测试运行脚本
# 使用方法: bash tests/run_tests.sh [选项]
#
# 选项:
#   --unit      只运行单元测试
#   --api       只运行 API 测试
#   --integration  只运行集成测试
#   --coverage  生成覆盖率报告
#   --all       运行所有测试（默认）

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# 打印标题
print_title() {
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  Prism V2.0 测试套件${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo ""
}

# 打印测试结果
print_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2 通过${NC}"
    else
        echo -e "${RED}❌ $2 失败${NC}"
    fi
}

# 解析参数
RUN_UNIT=false
RUN_API=false
RUN_INTEGRATION=false
RUN_COVERAGE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --unit)
            RUN_UNIT=true
            shift
            ;;
        --api)
            RUN_API=true
            shift
            ;;
        --integration)
            RUN_INTEGRATION=true
            shift
            ;;
        --coverage)
            RUN_COVERAGE=true
            shift
            ;;
        --all)
            RUN_UNIT=true
            RUN_API=true
            RUN_INTEGRATION=true
            shift
            ;;
        *)
            echo "未知参数: $1"
            echo "使用方法: bash tests/run_tests.sh [--unit|--api|--integration|--coverage|--all]"
            exit 1
            ;;
    esac
done

# 如果没有指定任何选项，运行所有测试
if [ "$RUN_UNIT" = false ] && [ "$RUN_API" = false ] && [ "$RUN_INTEGRATION" = false ]; then
    RUN_UNIT=true
    RUN_API=true
    RUN_INTEGRATION=true
fi

print_title

# 检查 pytest 是否安装
if ! command -v pytest &> /dev/null; then
    echo -e "${YELLOW}pytest 未安装，正在安装测试依赖...${NC}"
    pip install pytest pytest-asyncio pytest-cov
fi

# 运行测试
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

run_tests() {
    local test_type=$1
    local test_files=$2
    
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}  运行 $test_type 测试${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    if [ "$RUN_COVERAGE" = true ]; then
        pytest $test_files -v --cov=src --cov-report=term-missing
    else
        pytest $test_files -v
    fi
    
    local exit_code=$?
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    if [ $exit_code -eq 0 ]; then
        PASSED_TESTS=$((PASSED_TESTS + 1))
        print_result 0 "$test_type 测试"
    else
        FAILED_TESTS=$((FAILED_TESTS + 1))
        print_result 1 "$test_type 测试"
    fi
    
    echo ""
}

# 运行各类测试
if [ "$RUN_UNIT" = true ]; then
    run_tests "单元" "tests/test_*_unit.py"
fi

if [ "$RUN_API" = true ]; then
    run_tests "API" "tests/test_*_api.py"
fi

if [ "$RUN_INTEGRATION" = true ]; then
    run_tests "集成" "tests/test_integration.py"
fi

# 打印总结
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  测试总结${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  总测试套件: $TOTAL_TESTS"
echo -e "  ${GREEN}通过: $PASSED_TESTS${NC}"
echo -e "  ${RED}失败: $FAILED_TESTS${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✅ 所有测试通过！${NC}"
    exit 0
else
    echo -e "${RED}❌ 部分测试失败，请检查上面的错误信息。${NC}"
    exit 1
fi