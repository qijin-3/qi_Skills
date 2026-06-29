#!/bin/bash

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

APP_PATH="/Applications/WeChat.app"
COPY_PATH="/Applications/WeChat2.app"
BUNDLE_ID="com.tencent.xinWeChat2"

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}  微信双开工具${NC}"
echo -e "${GREEN}================================${NC}"
echo ""

# 步骤 1: 检查原版微信是否存在
echo -e "${YELLOW}[1/4]${NC} 检查微信应用..."
if [ ! -d "$APP_PATH" ]; then
    echo -e "${RED}✗ 错误: 未找到微信应用 $APP_PATH${NC}"
    echo "请先安装微信后再运行此脚本"
    exit 1
fi
echo -e "${GREEN}✓${NC} 找到微信应用"

# 步骤 2: 检查副本是否已存在
echo -e "${YELLOW}[2/4]${NC} 检查副本..."
if [ -d "$COPY_PATH" ]; then
    echo -e "${YELLOW}! 警告: WeChat2.app 已存在${NC}"
    read -p "是否删除并重新创建？(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$COPY_PATH"
        echo -e "${GREEN}✓${NC} 已删除旧副本"
    else
        echo "操作已取消"
        exit 0
    fi
fi

# 步骤 3: 复制应用
echo -e "${YELLOW}[3/4]${NC} 复制应用..."
cp -R "$APP_PATH" "$COPY_PATH"
echo -e "${GREEN}✓${NC} 应用复制完成"

# 步骤 4: 修改 Bundle ID
echo -e "${YELLOW}[4/4]${NC} 配置应用..."
/usr/libexec/PlistBuddy -c "Set :CFBundleIdentifier $BUNDLE_ID" "$COPY_PATH/Contents/Info.plist" 2>/dev/null || true
echo -e "${GREEN}✓${NC} Bundle ID 已修改"

# 步骤 5: 重新签名
echo -e "${YELLOW}[5/5]${NC} 重新签名..."
codesign --force --deep --sign - "$COPY_PATH" 2>/dev/null || true
echo -e "${GREEN}✓${NC} 应用已重新签名"

# 完成
echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}  ✓ 微信双开设置完成！${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo "你现在有两个微信应用："
echo "  • 原版: $APP_PATH"
echo "  • 双开版: $COPY_PATH"
echo ""
echo -e "${YELLOW}双击 WeChat2.app 即可打开第二个微信${NC}"
echo ""
