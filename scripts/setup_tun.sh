#!/bin/bash
# Creates and configures the VPN TUN interface.
# Run as root before starting the server.
set -e

TUN_NAME=${1:-vpn0}
SERVER_IP=${2:-10.8.0.1}
CIDR=${3:-24}

echo "[+] Creating TUN interface: $TUN_NAME"
ip tuntap add dev $TUN_NAME mode tun
ip addr add $SERVER_IP/$CIDR dev $TUN_NAME
ip link set $TUN_NAME up
ip link set $TUN_NAME mtu 1420

echo "[+] TUN interface $TUN_NAME is up at $SERVER_IP/$CIDR"
ip addr show $TUN_NAME
