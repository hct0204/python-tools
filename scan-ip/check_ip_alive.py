#!/usr/bin/env python3
"""
IP Address Connectivity Checker with Round Robin Support

This script checks if one or more IP addresses are reachable by sending ping requests.
Supports both individual IP addresses and reading from a file.
Includes round robin mode for continuous monitoring.

Usage:
    python check_ip_alive.py 8.8.8.8
    python check_ip_alive.py 8.8.8.8 1.1.1.1 192.168.1.1
    python check_ip_alive.py --file ip_list.txt
    python check_ip_alive.py --file ip_list.txt --timeout 5 --count 3
    python check_ip_alive.py --round-robin --interval 10 8.8.8.8 1.1.1.1
    python check_ip_alive.py --round-robin --file ip_list.txt --interval 5
"""

import subprocess
import sys
import argparse
import concurrent.futures
import time
from typing import List, Tuple
import platform
import signal
from datetime import datetime
import itertools
import ipaddress


def ping_ip(ip_address: str, timeout: int = 3, count: int = 1, show_progress: bool = False) -> Tuple[str, bool, str]:
    """
    Ping an IP address to check if it's alive.
    
    Args:
        ip_address: The IP address to ping
        timeout: Timeout in seconds for each ping
        count: Number of ping packets to send
        show_progress: Whether to show real-time ping progress
        
    Returns:
        Tuple of (ip_address, is_alive, message)
    """
    try:
        if show_progress:
            print(f"  🔍 Pinging {ip_address}...", end=" ", flush=True)
        
        # Determine ping command based on operating system
        if platform.system().lower() == "windows":
            # Windows ping command
            cmd = ["ping", "-n", str(count), "-w", str(timeout * 1000), ip_address]
        else:
            # Unix/Linux/macOS ping command
            cmd = ["ping", "-c", str(count), "-W", str(timeout), ip_address]
        
        # Execute ping command
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=timeout + 5  # Extra buffer for subprocess timeout
        )
        
        if result.returncode == 0:
            if show_progress:
                print("\033[92m✓\033[0m")  # Green checkmark
            return (ip_address, True, "Alive")
        else:
            if show_progress:
                print("\033[91m✗\033[0m")  # Red X
            return (ip_address, False, "Not reachable")
            
    except subprocess.TimeoutExpired:
        if show_progress:
            print("\033[93m⏱\033[0m")  # Yellow timeout symbol
        return (ip_address, False, "Timeout")
    except Exception as e:
        if show_progress:
            print("\033[91m❌\033[0m")  # Red error
        return (ip_address, False, f"Error: {str(e)}")


def expand_ip_range(ip_range: str) -> List[str]:
    """
    Expand IP range into list of individual IP addresses.
    
    Supports formats:
    - CIDR notation: 192.168.1.0/24
    - Range notation: 192.168.1.1-192.168.1.50
    - Single IP: 192.168.1.1
    
    Args:
        ip_range: IP range string
        
    Returns:
        List of IP addresses
    """
    try:
        # Handle CIDR notation (e.g., 192.168.1.0/24)
        if '/' in ip_range:
            network = ipaddress.IPv4Network(ip_range, strict=False)
            return [str(ip) for ip in network.hosts()]
        
        # Handle range notation (e.g., 192.168.1.1-192.168.1.50)
        elif '-' in ip_range:
            start_ip_str, end_ip_str = ip_range.split('-', 1)
            start_ip = ipaddress.IPv4Address(start_ip_str.strip())
            end_ip = ipaddress.IPv4Address(end_ip_str.strip())
            
            if start_ip > end_ip:
                raise ValueError(f"Start IP {start_ip} is greater than end IP {end_ip}")
            
            ips = []
            current = start_ip
            while current <= end_ip:
                ips.append(str(current))
                current += 1
            return ips
        
        # Handle single IP
        else:
            # Validate it's a valid IP
            ipaddress.IPv4Address(ip_range)
            return [ip_range]
            
    except Exception as e:
        print(f"Error parsing IP range '{ip_range}': {e}")
        return []


def read_ips_from_file(filename: str) -> List[str]:
    """
    Read IP addresses from a file.
    
    Args:
        filename: Path to file containing IP addresses (one per line)
        
    Returns:
        List of IP addresses
    """
    try:
        with open(filename, 'r') as f:
            ips = []
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):  # Skip empty lines and comments
                    # Check if line contains a range
                    if '/' in line or '-' in line:
                        expanded_ips = expand_ip_range(line)
                        ips.extend(expanded_ips)
                    else:
                        ips.append(line)
            return ips
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file '{filename}': {e}")
        sys.exit(1)


def check_ips_parallel(ip_addresses: List[str], timeout: int = 3, count: int = 1, max_workers: int = 10, show_progress: bool = False) -> List[Tuple[str, bool, str]]:
    """
    Check multiple IP addresses in parallel.
    
    Args:
        ip_addresses: List of IP addresses to check
        timeout: Timeout in seconds for each ping
        count: Number of ping packets to send
        max_workers: Maximum number of concurrent ping operations
        show_progress: Whether to show progress indicators
        
    Returns:
        List of tuples containing (ip_address, is_alive, message)
    """
    results = []
    completed = 0
    total = len(ip_addresses)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all ping tasks
        future_to_ip = {
            executor.submit(ping_ip, ip, timeout, count): ip 
            for ip in ip_addresses
        }
        
        if show_progress:
            print(f"Checking {total} IP addresses with {min(max_workers, total)} concurrent connections...")
        
        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_ip):
            result = future.result()
            results.append(result)
            completed += 1
            
            if show_progress:
                ip = future_to_ip[future]
                status = "✓" if result[1] else "✗"
                color = "\033[92m" if result[1] else "\033[91m"
                reset = "\033[0m"
                print(f"  [{completed:3d}/{total:3d}] {color}{status}{reset} {ip}")
    
    return results


def print_results(results: List[Tuple[str, bool, str]], show_summary: bool = True, round_robin: bool = False, timestamp: str = ""):
    """
    Print the ping results in a formatted table.
    
    Args:
        results: List of ping results
        show_summary: Whether to show summary statistics
        round_robin: Whether this is part of round robin monitoring
        timestamp: Timestamp for round robin mode
    """
    if not results:
        print("No results to display.")
        return
    
    # Sort results by IP address
    results.sort(key=lambda x: x[0])
    
    if round_robin:
        print(f"\n[{timestamp}] Round Robin Check Results:")
        print("-" * 60)
    else:
        # Print header
        print("\n" + "="*60)
        print(f"{'IP Address':<20} {'Status':<10} {'Details'}")
        print("="*60)
    
    # Print results
    alive_count = 0
    for ip, is_alive, message in results:
        status = "✓ ALIVE" if is_alive else "✗ DEAD"
        status_color = "\033[92m" if is_alive else "\033[91m"  # Green for alive, red for dead
        reset_color = "\033[0m"
        
        if round_robin:
            print(f"  {ip:<18} {status_color}{status:<10}{reset_color} {message}")
        else:
            print(f"{ip:<20} {status_color}{status:<10}{reset_color} {message}")
        
        if is_alive:
            alive_count += 1
    
    # Print summary
    if show_summary:
        total_count = len(results)
        dead_count = total_count - alive_count
        if round_robin:
            print(f"  Status: {alive_count}/{total_count} alive ({(alive_count/total_count)*100:.1f}%)")
        else:
            print("="*60)
            print(f"Summary: {alive_count}/{total_count} hosts alive, {dead_count}/{total_count} hosts unreachable")
            print(f"Success rate: {(alive_count/total_count)*100:.1f}%")


def round_robin_monitor(ip_addresses: List[str], interval: int = 10, timeout: int = 3, count: int = 1):
    """
    Continuously monitor IP addresses in round robin fashion.
    
    Args:
        ip_addresses: List of IP addresses to monitor
        interval: Interval in seconds between checks
        timeout: Timeout for each ping
        count: Number of ping packets per check
    """
    print(f"Starting round robin monitoring of {len(ip_addresses)} IP addresses")
    print(f"Check interval: {interval} seconds")
    print(f"Ping timeout: {timeout} seconds, Count: {count}")
    print("Press Ctrl+C to stop monitoring\n")
    
    # Setup signal handler for graceful exit
    def signal_handler(signum, frame):
        print("\n\nMonitoring stopped by user")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Track statistics
    check_count = 0
    history = {ip: [] for ip in ip_addresses}
    
    try:
        while True:
            check_count += 1
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Check all IPs with real-time progress
            results = []
            print(f"  Checking {len(ip_addresses)} IP addresses...")
            
            for i, ip in enumerate(ip_addresses, 1):
                print(f"  [{i:3d}/{len(ip_addresses):3d}]", end=" ")
                result = ping_ip(ip, timeout, count, show_progress=True)
                results.append(result)
                
                # Store in history (keep last 10 results per IP)
                history[ip].append(result[1])  # Store only alive/dead status
                if len(history[ip]) > 10:
                    history[ip].pop(0)
            
            # Print results
            print_results(results, show_summary=True, round_robin=True, timestamp=timestamp)
            
            # Show uptime statistics every 10 checks
            if check_count % 10 == 0:
                print(f"\n  Uptime Statistics (last {min(10, check_count)} checks):")
                for ip in ip_addresses:
                    if history[ip]:
                        uptime = (sum(history[ip]) / len(history[ip])) * 100
                        print(f"    {ip}: {uptime:.1f}% uptime")
                print()
            
            # Wait for next check
            print(f"  Next check in {interval} seconds... (Check #{check_count})")
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user")
        
        # Show final statistics
        print("\nFinal Statistics:")
        for ip in ip_addresses:
            if history[ip]:
                total_checks = len(history[ip])
                successful_checks = sum(history[ip])
                uptime = (successful_checks / total_checks) * 100
                print(f"  {ip}: {successful_checks}/{total_checks} successful ({uptime:.1f}% uptime)")


def main():
    parser = argparse.ArgumentParser(
        description="Check if IP addresses are alive by pinging them",
        epilog="""
Examples:
  %(prog)s 8.8.8.8                          # Check single IP
  %(prog)s 8.8.8.8 1.1.1.1 192.168.1.1      # Check multiple IPs
  %(prog)s 192.168.122.2-192.168.122.253    # Check IP range
  %(prog)s 192.168.1.0/24                   # Check CIDR block
  %(prog)s --file ip_list.txt                # Check IPs from file
  %(prog)s --file ips.txt --timeout 5 --count 3  # Custom timeout and ping count
  %(prog)s --round-robin --interval 10 8.8.8.8 1.1.1.1  # Round robin monitoring
  %(prog)s --round-robin --interval 2 192.168.122.2-192.168.122.253  # Round robin range
  %(prog)s --round-robin --file ips.txt --interval 5     # Round robin from file
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Input options
    parser.add_argument('ip_addresses', nargs='*', 
                       help='IP addresses, ranges, or CIDR blocks to check. ' +
                            'Supports: 8.8.8.8, 192.168.1.1-192.168.1.50, 192.168.1.0/24')
    parser.add_argument('--file', '-f', help='File containing IP addresses (one per line)')
    
    # Ping options
    parser.add_argument('--timeout', '-t', type=int, default=3, 
                       help='Timeout in seconds for each ping (default: 3)')
    parser.add_argument('--count', '-c', type=int, default=1,
                       help='Number of ping packets to send (default: 1)')
    parser.add_argument('--workers', '-w', type=int, default=10,
                       help='Maximum number of concurrent ping operations (default: 10)')
    
    # Round robin options
    parser.add_argument('--round-robin', '-r', action='store_true',
                       help='Enable round robin monitoring mode')
    parser.add_argument('--interval', '-i', type=int, default=10,
                       help='Interval in seconds between round robin checks (default: 10)')
    
    # Output options
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Only show summary, not individual results')
    parser.add_argument('--no-summary', action='store_true',
                       help='Don\'t show summary statistics')
    parser.add_argument('--show-progress', '-p', action='store_true',
                       help='Show real-time progress of which IPs are being pinged')
    
    args = parser.parse_args()
    
    # Get list of IP addresses
    ip_addresses = []
    
    if args.file:
        file_ips = read_ips_from_file(args.file)
        if file_ips:
            ip_addresses.extend(file_ips)
        else:
            print(f"No valid IP addresses found in file '{args.file}'")
            sys.exit(1)
    
    if args.ip_addresses:
        for ip_arg in args.ip_addresses:
            # Check if it's a range or CIDR
            if '/' in ip_arg or '-' in ip_arg:
                expanded_ips = expand_ip_range(ip_arg)
                if expanded_ips:
                    ip_addresses.extend(expanded_ips)
                else:
                    print(f"Warning: Could not parse IP range '{ip_arg}'")
            else:
                ip_addresses.append(ip_arg)
    
    if not ip_addresses:
        print("Error: No IP addresses provided. Use either command line arguments or --file option.")
        parser.print_help()
        sys.exit(1)
    
    # Validate timeout and count
    if args.timeout < 1:
        print("Error: Timeout must be at least 1 second")
        sys.exit(1)
    
    if args.count < 1:
        print("Error: Count must be at least 1")
        sys.exit(1)
        
    if args.interval < 1:
        print("Error: Interval must be at least 1 second")
        sys.exit(1)
    
    # Round robin mode
    if args.round_robin:
        round_robin_monitor(
            ip_addresses, 
            interval=args.interval,
            timeout=args.timeout, 
            count=args.count
        )
        return
    
    # One-time check mode
    if not args.show_progress:
        print(f"Checking {len(ip_addresses)} IP address(es)...")
        if len(ip_addresses) > 1:
            print(f"Using {min(args.workers, len(ip_addresses))} concurrent connections")
    
    start_time = time.time()
    
    # Check IP addresses
    results = check_ips_parallel(
        ip_addresses, 
        timeout=args.timeout, 
        count=args.count,
        max_workers=args.workers,
        show_progress=args.show_progress
    )
    
    end_time = time.time()
    
    # Print results
    if not args.quiet:
        print_results(results, show_summary=not args.no_summary)
    else:
        alive_count = sum(1 for _, is_alive, _ in results if is_alive)
        total_count = len(results)
        print(f"Results: {alive_count}/{total_count} hosts alive")
    
    print(f"\nCompleted in {end_time - start_time:.2f} seconds")


if __name__ == "__main__":
    main()