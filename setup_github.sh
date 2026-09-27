#!/bin/bash

echo "=========================================="
echo "GitHub 公开项目设置脚本"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. 检查当前 Git 状态
echo -e "${YELLOW}[步骤 1] 检查当前 Git 状态${NC}"
echo "----------------------------------------"
git status --short
echo ""

# 2. 提示用户输入 GitHub 用户名
echo -e "${YELLOW}[步骤 2] 配置远程仓库${NC}"
echo "----------------------------------------"
read -p "请输入你的 GitHub 用户名: " GITHUB_USERNAME

if [ -z "$GITHUB_USERNAME" ]; then
    echo -e "${RED}错误：GitHub 用户名不能为空${NC}"
    exit 1
fi

# 验证 GitHub 用户名格式（防止命令注入）
if [[ ! "$GITHUB_USERNAME" =~ ^[a-zA-Z0-9_-]+$ ]]; then
    echo -e "${RED}错误：GitHub 用户名只能包含字母、数字、下划线和连字符${NC}"
    exit 1
fi

REPO_NAME="us-stock-trading-binance"
REMOTE_URL="https://github.com/${GITHUB_USERNAME}/${REPO_NAME}.git"

echo ""
echo "远程仓库地址: $REMOTE_URL"
echo ""

# 3. 检查是否已存在 origin
if git remote | grep -q "^origin$"; then
    echo -e "${YELLOW}检测到已存在 origin 远程仓库，将更新地址${NC}"
    git remote set-url origin "$REMOTE_URL"
else
    echo -e "${GREEN}添加新的 origin 远程仓库${NC}"
    git remote add origin "$REMOTE_URL"
fi

# 4. 验证远程仓库配置
echo ""
echo -e "${YELLOW}[步骤 3] 验证远程仓库配置${NC}"
echo "----------------------------------------"
git remote -v
echo ""

# 5. 提交所有更改
echo -e "${YELLOW}[步骤 4] 提交所有更改${NC}"
echo "----------------------------------------"

# 添加所有文件
git add .

# 提交
git commit -m "chore: 整理项目结构和修复安全问题

- 移动 47 个测试脚本到 tests/ 目录
- 修复测试脚本中的签名泄露问题（6 个文件）
- 整理根目录文件到合适位置
- 移动 SYSTEM_CHECK.md 到 docs/system/
- 添加 tests/README.md 说明文档
- 完成系统配置和功能验证"

echo -e "${GREEN}✅ 提交完成${NC}"
echo ""

# 6. 切换到 main 分支
echo -e "${YELLOW}[步骤 5] 切换到 main 分支${NC}"
echo "----------------------------------------"
CURRENT_BRANCH=$(git branch --show-current)
echo "当前分支: $CURRENT_BRANCH"

if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "重命名分支 $CURRENT_BRANCH -> main"
    git branch -M main
    echo -e "${GREEN}✅ 分支已切换到 main${NC}"
else
    echo -e "${GREEN}✅ 已在 main 分支${NC}"
fi
echo ""

# 7. 推送前的安全检查
echo -e "${YELLOW}[步骤 6] 安全检查${NC}"
echo "----------------------------------------"
echo "检查是否有敏感文件将被提交..."
echo ""

# 检查 secrets 目录
if git ls-files | grep -q "^secrets/"; then
    echo -e "${RED}⚠️  警告：检测到 secrets/ 目录中的文件将被提交！${NC}"
    git ls-files | grep "^secrets/"
    echo ""
    read -p "是否继续？(y/N) " CONTINUE
    if [ "$CONTINUE" != "y" ] && [ "$CONTINUE" != "Y" ]; then
        echo "已取消推送"
        exit 1
    fi
fi

# 检查数据库文件
if git ls-files | grep -q "\.db$"; then
    echo -e "${RED}⚠️  警告：检测到数据库文件将被提交！${NC}"
    git ls-files | grep "\.db$"
    echo ""
    read -p "是否继续？(y/N) " CONTINUE
    if [ "$CONTINUE" != "y" ] && [ "$CONTINUE" != "Y" ]; then
        echo "已取消推送"
        exit 1
    fi
fi

echo -e "${GREEN}✅ 安全检查通过${NC}"
echo ""

# 8. 推送到 GitHub
echo -e "${YELLOW}[步骤 7] 推送到 GitHub${NC}"
echo "----------------------------------------"
echo ""
echo -e "${YELLOW}重要提示：${NC}"
echo "1. GitHub 不再支持密码认证"
echo "2. 需要使用 Personal Access Token (PAT)"
echo "3. 如果你还没有 PAT，请按以下步骤创建："
echo ""
echo -e "${GREEN}创建 Personal Access Token：${NC}"
echo "   a. 访问：https://github.com/settings/tokens"
echo "   b. 点击 'Generate new token' -> 'Generate new token (classic)'"
echo "   c. Note: us-stock-trading-binance"
echo "   d. Expiration: 90 days 或 1 year"
echo "   e. 勾选: repo (完整仓库访问权限)"
echo "   f. 点击 'Generate token'"
echo "   g. 立即复制 token（只显示一次！）"
echo ""
echo "推送时："
echo "   Username: 你的 GitHub 用户名"
echo "   Password: 粘贴你的 Personal Access Token"
echo ""
read -p "准备好后按回车开始推送..."

# 推送
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}=========================================="
    echo "🎉 成功推送到 GitHub！"
    echo "==========================================${NC}"
    echo ""
    echo "仓库地址: https://github.com/${GITHUB_USERNAME}/${REPO_NAME}"
    echo ""
    echo "后续推送只需执行："
    echo "  git add ."
    echo "  git commit -m '更新说明'"
    echo "  git push"
else
    echo ""
    echo -e "${RED}=========================================="
    echo "❌ 推送失败"
    echo "==========================================${NC}"
    echo ""
    echo "常见问题："
    echo "1. 认证失败：检查 Personal Access Token 是否正确"
    echo "2. 仓库不存在：确认已在 GitHub 网站创建私有仓库"
    echo "3. 权限不足：检查 Token 是否有 'repo' 权限"
    echo ""
    echo "需要帮助？请查看 GitHub 文档："
    echo "https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token"
fi
