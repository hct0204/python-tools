# IP Address Connectivity Checker with Round Robin Support

This repository contains two scripts for checking if IP addresses are alive by sending ping requests. Both scripts support round robin monitoring for continuous network monitoring.

## Scripts Included

1. **`check_ip_alive.py`** - Python version with advanced features
2. **`check_ip_alive.sh`** - Shell script version for lighter environments
3. **`sample_ips.txt`** - Sample IP addresses file for testing

## Features

- ✅ Check single or multiple IP addresses
- ✅ **IP Range Support** - CIDR notation (192.168.1.0/24) and range notation (192.168.1.1-192.168.1.50)
- ✅ Read IP addresses from a file
- ✅ **Round robin monitoring** for continuous monitoring
- ✅ Configurable timeout and ping count
- ✅ Parallel checking (Python version)
- ✅ Colored output for easy reading
- ✅ Statistics and uptime tracking
- ✅ Cross-platform support (Windows, Linux, macOS)

## Quick Start

### Python Version

```bash
# Make it executable (optional)
chmod +x check_ip_alive.py

# Check single IP
python3 check_ip_alive.py 8.8.8.8

# Check multiple IPs
python3 check_ip_alive.py 8.8.8.8 1.1.1.1 208.67.222.222

# Check IPs from file
python3 check_ip_alive.py --file sample_ips.txt

# Check IP range (192.168.122.2 to 192.168.122.253)
python3 check_ip_alive.py 192.168.122.2-192.168.122.253

# Check CIDR block
python3 check_ip_alive.py 192.168.1.0/24

# Round robin monitoring (checks every 10 seconds)
python3 check_ip_alive.py --round-robin --interval 10 8.8.8.8 1.1.1.1

# Round robin with IP range
python3 check_ip_alive.py --round-robin --interval 5 192.168.122.2-192.168.122.253

# Round robin with file input
python3 check_ip_alive.py --round-robin --file ip_ranges.txt --interval 5
```

### Shell Version

```bash
# Make it executable
chmod +x check_ip_alive.sh

# Check single IP
./check_ip_alive.sh 8.8.8.8

# Check multiple IPs
./check_ip_alive.sh 8.8.8.8 1.1.1.1 208.67.222.222

# Check IPs from file
./check_ip_alive.sh -f sample_ips.txt

# Round robin monitoring (checks every 15 seconds)
./check_ip_alive.sh -r -i 15 8.8.8.8 1.1.1.1

# Round robin with file input
./check_ip_alive.sh -r -f sample_ips.txt -i 5
```

## Round Robin Mode

Round robin mode continuously monitors the specified IP addresses at regular intervals. This is useful for:

- Network monitoring and alerting
- Testing network stability over time
- Tracking uptime statistics
- Identifying intermittent connectivity issues

### Round Robin Features

- **Continuous monitoring**: Runs indefinitely until stopped with Ctrl+C
- **Timestamped results**: Each check is timestamped
- **Uptime statistics**: Shows uptime percentages every 10 checks
- **Graceful exit**: Press Ctrl+C to stop and see final statistics
- **Real-time status**: Shows current status of all monitored IPs

### Example Round Robin Output

```
Starting round robin monitoring of 2 IP addresses
Check interval: 10 seconds
Ping timeout: 3 seconds, Count: 1
Press Ctrl+C to stop monitoring

[2024-01-15 14:30:15] Round Robin Check Results:
------------------------------------------------------------
  8.8.8.8            ✓ ALIVE    Alive
  1.1.1.1            ✓ ALIVE    Alive
  Status: 2/2 alive (100%)
  Next check in 10 seconds... (Check #1)

[2024-01-15 14:30:25] Round Robin Check Results:
------------------------------------------------------------
  8.8.8.8            ✓ ALIVE    Alive
  1.1.1.1            ✗ DEAD     Not reachable
  Status: 1/2 alive (50%)
  Next check in 10 seconds... (Check #2)
```

## Command Line Options

### Python Version (`check_ip_alive.py`)

| Option | Description | Default |
|--------|-------------|---------|
| `--file, -f` | File containing IP addresses (one per line) | - |
| `--timeout, -t` | Timeout in seconds for each ping | 3 |
| `--count, -c` | Number of ping packets to send | 1 |
| `--workers, -w` | Maximum concurrent ping operations | 10 |
| `--round-robin, -r` | Enable round robin monitoring mode | false |
| `--interval, -i` | Interval between round robin checks (seconds) | 10 |
| `--quiet, -q` | Only show summary, not individual results | false |
| `--no-summary` | Don't show summary statistics | false |

### Shell Version (`check_ip_alive.sh`)

| Option | Description | Default |
|--------|-------------|---------|
| `-f` | File containing IP addresses (one per line) | - |
| `-t` | Timeout in seconds for each ping | 3 |
| `-c` | Number of ping packets to send | 1 |
| `-r` | Enable round robin monitoring mode | false |
| `-i` | Interval between round robin checks (seconds) | 10 |
| `-h` | Show help message | - |

## IP Address File Format

Create a text file with one IP address per line. Comments start with `#`:

```
# DNS Servers
8.8.8.8
1.1.1.1
208.67.222.222

# Local Network
192.168.1.1
10.0.0.1

# Test unreachable IP
192.0.2.1
```

## Examples

### Basic Usage

```bash
# Test Google's DNS
python3 check_ip_alive.py 8.8.8.8

# Test multiple public DNS servers
python3 check_ip_alive.py 8.8.8.8 1.1.1.1 208.67.222.222

# Test with custom timeout
python3 check_ip_alive.py --timeout 5 --count 3 8.8.8.8
```

### Round Robin Monitoring

```bash
# Monitor critical servers every 30 seconds
python3 check_ip_alive.py --round-robin --interval 30 \
    192.168.1.1 192.168.1.100 192.168.1.200

# Monitor from file with fast checking (every 5 seconds)
python3 check_ip_alive.py --round-robin --file production_servers.txt --interval 5

# Shell version for lightweight monitoring
./check_ip_alive.sh -r -i 60 8.8.8.8 1.1.1.1
```

### Piping Input (Shell version only)

```bash
# From command output
echo "8.8.8.8 1.1.1.1" | ./check_ip_alive.sh

# From file using cat
cat sample_ips.txt | ./check_ip_alive.sh
```

## Exit Codes

- **0**: All hosts are alive
- **1**: Some hosts are alive (mixed results)
- **2**: No hosts are alive

## Requirements

### Python Version
- Python 3.6+
- No external dependencies (uses only standard library)

### Shell Version
- Bash 4.0+
- Standard `ping` command available
- Works on Linux, macOS, and Windows (Git Bash/WSL)

## Platform Compatibility

Both scripts automatically detect the operating system and use the appropriate ping command:

- **Linux/macOS**: `ping -c COUNT -W TIMEOUT IP`
- **Windows**: `ping -n COUNT -w TIMEOUT_MS IP`

## Tips

1. **For network monitoring**: Use round robin mode with appropriate intervals
2. **For quick checks**: Use the one-time mode with multiple IPs
3. **For automation**: Use the `--quiet` option and check exit codes
4. **For troubleshooting**: Increase timeout and ping count
5. **For CI/CD**: Use the Python version for better error handling

## Stopping Round Robin Mode

Press `Ctrl+C` to gracefully stop round robin monitoring. The script will show final statistics before exiting.