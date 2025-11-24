#!/bin/bash
# IP Address Connectivity Checker with Round Robin Support
# Usage: ./check_ip_alive.sh [IP1] [IP2] [IP3] ...
#        ./check_ip_alive.sh -f filename
#        ./check_ip_alive.sh -r -i 10 [IP1] [IP2]
#        echo "8.8.8.8 1.1.1.1" | ./check_ip_alive.sh

set -e

# Default values
TIMEOUT=3
COUNT=1
SHOW_HELP=false
ROUND_ROBIN=false
INTERVAL=10

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to show help
show_help() {
    cat << EOF
IP Address Connectivity Checker (Shell Version) with Round Robin Support

Usage:
    $0 [OPTIONS] [IP1] [IP2] [IP3] ...
    $0 -f filename
    echo "IP1 IP2 IP3" | $0

Options:
    -f FILE     Read IP addresses from file (one per line)
    -t TIMEOUT  Timeout in seconds (default: 3)
    -c COUNT    Number of ping packets (default: 1)
    -r          Enable round robin monitoring mode
    -i INTERVAL Interval in seconds between round robin checks (default: 10)
    -h          Show this help message

Examples:
    $0 8.8.8.8 1.1.1.1
    $0 -f sample_ips.txt
    $0 -t 5 -c 3 8.8.8.8
    $0 -r -i 15 8.8.8.8 1.1.1.1
    $0 -r -f sample_ips.txt -i 5
    echo "8.8.8.8 1.1.1.1" | $0

EOF
}

# Function to ping an IP address
ping_ip() {
    local ip=$1
    local timeout=$2
    local count=$3
    
    # Detect OS and use appropriate ping command
    if [[ "$OSTYPE" == "darwin"* ]] || [[ "$OSTYPE" == "linux"* ]]; then
        # macOS and Linux
        if ping -c "$count" -W "$timeout" "$ip" >/dev/null 2>&1; then
            echo -e "${GREEN}✓ $ip is alive${NC}"
            return 0
        else
            echo -e "${RED}✗ $ip is not reachable${NC}"
            return 1
        fi
    elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]]; then
        # Windows (Git Bash, Cygwin, etc.)
        if ping -n "$count" -w $((timeout * 1000)) "$ip" >/dev/null 2>&1; then
            echo -e "${GREEN}✓ $ip is alive${NC}"
            return 0
        else
            echo -e "${RED}✗ $ip is not reachable${NC}"
            return 1
        fi
    else
        # Fallback for other systems
        if ping -c "$count" "$ip" >/dev/null 2>&1; then
            echo -e "${GREEN}✓ $ip is alive${NC}"
            return 0
        else
            echo -e "${RED}✗ $ip is not reachable${NC}"
            return 1
        fi
    fi
}

# Function to validate IP address format
validate_ip() {
    local ip=$1
    if [[ $ip =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
        IFS='.' read -ra ADDR <<< "$ip"
        for i in "${ADDR[@]}"; do
            if (( i > 255 )); then
                return 1
            fi
        done
        return 0
    else
        return 1
    fi
}

# Parse command line arguments
while getopts "f:t:c:ri:h" opt; do
    case $opt in
        f)
            IP_FILE="$OPTARG"
            ;;
        t)
            TIMEOUT="$OPTARG"
            ;;
        c)
            COUNT="$OPTARG"
            ;;
        r)
            ROUND_ROBIN=true
            ;;
        i)
            INTERVAL="$OPTARG"
            ;;
        h)
            show_help
            exit 0
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            show_help
            exit 1
            ;;
    esac
done

shift $((OPTIND-1))

# Collect IP addresses
IPS=()

if [[ -n "$IP_FILE" ]]; then
    # Read from file
    if [[ ! -f "$IP_FILE" ]]; then
        echo -e "${RED}Error: File '$IP_FILE' not found${NC}" >&2
        exit 1
    fi
    
    while IFS= read -r line || [[ -n "$line" ]]; do
        # Skip empty lines and comments
        line=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
        if [[ -n "$line" && ! "$line" =~ ^# ]]; then
            IPS+=("$line")
        fi
    done < "$IP_FILE"
    
elif [[ $# -gt 0 ]]; then
    # Use command line arguments
    IPS=("$@")
    
elif [[ ! -t 0 ]]; then
    # Read from stdin
    while read -r line; do
        for ip in $line; do
            IPS+=("$ip")
        done
    done
    
else
    echo -e "${YELLOW}No IP addresses provided${NC}" >&2
    show_help
    exit 1
fi

# Validate that we have IPs to check
if [[ ${#IPS[@]} -eq 0 ]]; then
    echo -e "${YELLOW}No valid IP addresses to check${NC}" >&2
    exit 1
fi

# Validate timeout and count
if ! [[ "$TIMEOUT" =~ ^[0-9]+$ ]] || [[ "$TIMEOUT" -lt 1 ]]; then
    echo -e "${RED}Error: Timeout must be a positive integer${NC}" >&2
    exit 1
fi

if ! [[ "$COUNT" =~ ^[0-9]+$ ]] || [[ "$COUNT" -lt 1 ]]; then
    echo -e "${RED}Error: Count must be a positive integer${NC}" >&2
    exit 1
fi

if ! [[ "$INTERVAL" =~ ^[0-9]+$ ]] || [[ "$INTERVAL" -lt 1 ]]; then
    echo -e "${RED}Error: Interval must be a positive integer${NC}" >&2
    exit 1
fi

# Round robin monitoring function
round_robin_monitor() {
    local ips=("$@")
    local check_count=0
    
    echo "Starting round robin monitoring of ${#ips[@]} IP addresses"
    echo "Check interval: ${INTERVAL} seconds"
    echo "Ping timeout: ${TIMEOUT} seconds, Count: ${COUNT}"
    echo "Press Ctrl+C to stop monitoring"
    echo ""
    
    # Initialize history arrays
    declare -A history
    declare -A success_counts
    declare -A total_counts
    
    for ip in "${ips[@]}"; do
        history["$ip"]=""
        success_counts["$ip"]=0
        total_counts["$ip"]=0
    done
    
    # Signal handler for graceful exit
    trap 'echo -e "\n\nMonitoring stopped by user"; show_final_stats; exit 0' INT
    
    show_final_stats() {
        echo -e "\nFinal Statistics:"
        for ip in "${ips[@]}"; do
            if [[ ${total_counts["$ip"]} -gt 0 ]]; then
                local uptime=$(( (success_counts["$ip"] * 100) / total_counts["$ip"] ))
                echo -e "  $ip: ${success_counts["$ip"]}/${total_counts["$ip"]} successful (${uptime}% uptime)"
            fi
        done
    }
    
    while true; do
        check_count=$((check_count + 1))
        timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        
        echo -e "\n[$timestamp] Round Robin Check Results:"
        echo "------------------------------------------------------------"
        
        local alive_count=0
        for ip in "${ips[@]}"; do
            if ping_ip "$ip" "$TIMEOUT" "$COUNT"; then
                alive_count=$((alive_count + 1))
                success_counts["$ip"]=$((success_counts["$ip"] + 1))
            fi
            total_counts["$ip"]=$((total_counts["$ip"] + 1))
        done
        
        echo "  Status: $alive_count/${#ips[@]} alive ($(( (alive_count * 100) / ${#ips[@]} ))%)"
        
        # Show uptime statistics every 10 checks
        if [[ $((check_count % 10)) -eq 0 ]]; then
            echo -e "\n  Uptime Statistics (last $check_count checks):"
            for ip in "${ips[@]}"; do
                if [[ ${total_counts["$ip"]} -gt 0 ]]; then
                    local uptime=$(( (success_counts["$ip"] * 100) / total_counts["$ip"] ))
                    echo "    $ip: ${uptime}% uptime"
                fi
            done
        fi
        
        echo "  Next check in ${INTERVAL} seconds... (Check #$check_count)"
        sleep "$INTERVAL"
    done
}

# Check if round robin mode is enabled
if [[ "$ROUND_ROBIN" == true ]]; then
    round_robin_monitor "${IPS[@]}"
    exit 0
fi

# Start one-time checking
echo "Checking ${#IPS[@]} IP address(es) with ${COUNT} ping(s) and ${TIMEOUT}s timeout..."
echo "$(date)"
echo "================================================================"

alive_count=0
total_count=${#IPS[@]}

start_time=$(date +%s)

for ip in "${IPS[@]}"; do
    # Validate IP format
    if ! validate_ip "$ip"; then
        echo -e "${YELLOW}⚠ $ip - Invalid IP address format${NC}"
        continue
    fi
    
    # Ping the IP
    if ping_ip "$ip" "$TIMEOUT" "$COUNT"; then
        ((alive_count++))
    fi
done

end_time=$(date +%s)
duration=$((end_time - start_time))

# Show summary
echo "================================================================"
echo "Summary: $alive_count/$total_count hosts alive"
echo "Success rate: $(( (alive_count * 100) / total_count ))%"
echo "Completed in ${duration} seconds"

# Exit with appropriate code
if [[ $alive_count -eq $total_count ]]; then
    exit 0  # All hosts alive
elif [[ $alive_count -gt 0 ]]; then
    exit 1  # Some hosts alive
else
    exit 2  # No hosts alive
fi