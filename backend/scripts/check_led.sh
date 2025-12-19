#!/bin/bash
# RK3568 LED 检查脚本
# 用于查看板载 LED 信息和测试 LED 控制

echo "========================================="
echo "RK3568 LED 检查工具"
echo "========================================="

# 1. 查看所有可用的 LED
echo -e "\n[1] 可用的 LED 列表："
ls -l /sys/class/leds/
echo ""

# 2. 显示每个 LED 的详细信息
echo "[2] LED 详细信息："
for led in /sys/class/leds/*/; do
    led_name=$(basename "$led")
    echo ""
    echo "--- $led_name ---"

    # 当前亮度
    if [ -f "$led/brightness" ]; then
        brightness=$(cat "$led/brightness")
        echo "  当前亮度: $brightness"
    fi

    # 最大亮度
    if [ -f "$led/max_brightness" ]; then
        max_brightness=$(cat "$led/max_brightness")
        echo "  最大亮度: $max_brightness"
    fi

    # 触发模式
    if [ -f "$led/trigger" ]; then
        trigger=$(cat "$led/trigger")
        echo "  触发模式: $trigger"
    fi

    # 完整路径
    echo "  路径: $led"
done

# 3. 推荐使用的 LED
echo ""
echo "[3] 推荐配置："
echo ""

# 优先级：sys_led > user > work
if [ -d "/sys/class/leds/sys_led" ]; then
    echo "✓ 推荐使用: sys_led"
    echo "  配置路径: /sys/class/leds/sys_led/brightness"
elif [ -d "/sys/class/leds/user" ]; then
    echo "✓ 推荐使用: user"
    echo "  配置路径: /sys/class/leds/user/brightness"
elif [ -d "/sys/class/leds/work" ]; then
    echo "✓ 推荐使用: work"
    echo "  配置路径: /sys/class/leds/work/brightness"
else
    echo "⚠ 未找到常用的 LED，请从上面列表中选择"
fi

# 4. LED 测试（可选）
echo ""
echo "[4] 是否测试 LED 控制？(y/n)"
read -r test_led

if [ "$test_led" = "y" ] || [ "$test_led" = "Y" ]; then
    echo ""
    echo "请输入要测试的 LED 名称（如 sys_led）："
    read -r led_name

    led_path="/sys/class/leds/$led_name/brightness"

    if [ ! -f "$led_path" ]; then
        echo "✗ LED 不存在: $led_path"
        exit 1
    fi

    echo "开始测试 $led_name ..."

    # 保存原始状态
    original=$(cat "$led_path")
    echo "  原始亮度: $original"

    # 测试：关闭
    echo "  [1/3] 关闭 LED..."
    echo 0 > "$led_path"
    sleep 1

    # 测试：打开
    echo "  [2/3] 打开 LED..."
    echo 1 > "$led_path"
    sleep 1

    # 测试：闪烁
    echo "  [3/3] 闪烁测试（5次）..."
    for i in {1..5}; do
        echo 1 > "$led_path"
        sleep 0.3
        echo 0 > "$led_path"
        sleep 0.3
    done

    # 恢复原始状态
    echo "$original" > "$led_path"
    echo "  恢复原始状态: $original"

    echo ""
    echo "✓ 测试完成！"
fi

echo ""
echo "========================================="
echo "检查完成"
echo "========================================="
