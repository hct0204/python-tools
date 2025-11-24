#!/bin/bash

# 檢查Python程式端口使用情況的實用腳本

echo "🔍 檢查Python程式端口使用情況"
echo "================================="

# 方法1：最簡潔的一行命令
echo "📊 方法1：簡潔版本"
netstat -tlpn | grep python | awk '{split($7,a,"/"); printf "Port: %-20s PID: %-10s CMD: ", $4, a[1]; system("ps -p " a[1] " -o cmd --no-headers 2>/dev/null || echo \"N/A\"")}'

echo -e "\n📊 方法2：詳細版本"
netstat -tlpn | grep python | while IFS= read -r line; do
    port=$(echo "$line" | awk '{print $4}')
    pid=$(echo "$line" | awk '{split($7,a,"/"); print a[1]}')
    
    echo "┌─ Port: $port"
    echo "├─ PID: $pid"
    echo "└─ Command: $(ps -p $pid -o cmd --no-headers 2>/dev/null || echo 'Process not found')"
    echo
done

echo "📊 方法3：表格式輸出"
echo "Port                 | PID       | Command"
echo "---------------------|-----------|----------------------------------------"
netstat -tlpn | grep python | awk '{
    split($7,a,"/"); 
    pid=a[1]; 
    port=$4; 
    cmd_line="ps -p " pid " -o cmd --no-headers 2>/dev/null || echo \"N/A\"";
    cmd_line | getline cmd;
    close(cmd_line);
    printf "%-20s | %-9s | %s\n", port, pid, cmd
}'

echo -e "\n🎯 方法4：只顯示端口和服務名"
netstat -tlpn | grep python | awk '{
    split($7,a,"/"); 
    pid=a[1]; 
    port=$4; 
    cmd_line="ps -p " pid " -o cmd --no-headers 2>/dev/null";
    cmd_line | getline cmd;
    close(cmd_line);
    split(cmd, parts, " ");
    service_name=parts[2];
    gsub(/.*\//, "", service_name);
    printf "%s -> %s\n", port, service_name
}'