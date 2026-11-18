---
title: Set Up a Bootnode
description: Learn how to configure and run a bootnode for Polkadot, including P2P, WS, and WebRTC connections and network key management.
categories: Infrastructure
---

# Set Up a Bootnode

## Introduction

Bootnodes are essential for helping blockchain nodes discover peers and join the network. When a node starts, it needs to find other nodes, and bootnodes provide an initial point of contact. Once connected, a node can expand its peer connections and play its role in the network, like participating as a validator.

This guide will walk you through setting up a Polkadot bootnode, configuring P2P, WebSocket (WS), and Web Real-Time Communication (WebRTC) connections, and managing network keys. You'll also learn how to test your bootnode to ensure it is running correctly and accessible to other nodes.

## Prerequisites

Before you start, you need to have the following prerequisites:

- Verify a working Polkadot (`polkadot`) binary is available on your machine.
- A VPS or other dedicated server setup.

## Accessing the Bootnode

Bootnodes accept connections from other nodes and light clients through the following channels:

- **P2P**: A direct peer-to-peer connection over TCP, configured with the following flag:

    ```bash

    --listen-addr /ip4/0.0.0.0/tcp/INSERT_PORT

    ```
    
    This is not enabled by default on non-validator nodes like archive RPC nodes.

- **P2P/WS**: A WebSocket (WS) connection, also configured via `--listen-addr`.
- **P2P/WebRTC**: A WebRTC connection over UDP, which in-browser light clients such as smoldot use. It needs no domain name, TLS certificate, or reverse proxy. WebRTC is only supported by the litep2p network backend, which is the default. Light client connections count toward the `--in-peers-light` limit, which defaults to 500.

## Node Key

A node key is the ED25519 key used by `libp2p` to assign your node an identity or peer ID. Generating a known node key for a bootnode is crucial, as it gives you a consistent key that can be placed in chain specifications as a known, reliable bootnode.

Starting a node creates its node key in the `chains/INSERT_CHAIN/network/secret_ed25519` file.

You can create a node key using:

 ``` bash
 polkadot key generate-node-key
 ``` 
 
This key can be used in the startup command line.

It is imperative that you backup the node key. If it is included in the `polkadot` binary, it is hardcoded into the binary, which must be recompiled to change the key.

## Running the Bootnode

A bootnode can be run as follows:

 ``` bash
 polkadot --chain polkadot \
 --name dot-bootnode \
 --listen-addr /ip4/0.0.0.0/tcp/30310 \
 --listen-addr /ip4/0.0.0.0/tcp/30311/ws \
 --listen-addr /ip4/0.0.0.0/udp/30310/webrtc-direct
 ```

This assigns p2p to TCP port 30310, p2p/ws to TCP port 30311, and p2p/webrtc to UDP port 30310.

!!! warning
    Passing `--listen-addr` replaces all default listen addresses, including the WebRTC ones that a full node otherwise listens on. If you omit the `webrtc-direct` address, the bootnode does not accept WebRTC connections. To also listen on IPv6, add `--listen-addr /ip6/::/udp/30310/webrtc-direct`.

### Configure WebRTC Networking

If the bootnode's public address or port differs from its local listen address or port, for example because it runs behind network address translation (NAT) or you redirect ports, add a matching public address. The node advertises this address in the distributed hash table (DHT), so light clients can discover it:

```bash
--public-addr /ip4/INSERT_PUBLIC_IP/udp/30310/webrtc-direct
```

Replace `ip4` with `ip6` or `dns` if needed. Do not append `/certhash/...` or `/p2p/...` to WebRTC listen or public addresses. The node adds both itself and can refuse to start if they are present.

Open the UDP port in your firewall. Existing rules for the TCP port do not cover UDP. If the bootnode is behind NAT, forward the public UDP port to the local listen port.

To stop a node from serving WebRTC, pass `--listen-addr` with TCP and WS addresses only. Blocking the UDP port is not enough, because the node still advertises its WebRTC address and light clients fail to connect.

## Testing Bootnode Connection

If the preceding node is running with DNS name `dot-bootnode.stakeworld.io` and node-id `12D3KooWAb5MyC1UJiEQJk4Hg4B2Vi3AJdqSUhTGYUqSnEqCFMFg` then the following P2P and P2P/WS commands should output `syncing 1 peers`.

!!!tip
    You can add `-lsub-libp2p=trace` on the end to get libp2p trace logging for debugging purposes.

### P2P

```bash
polkadot --chain polkadot \
--base-path /tmp/node \
--name "Bootnode testnode" \
--reserved-only \
--reserved-nodes "/dns/dot-bootnode.stakeworld.io/tcp/30310/p2p/12D3KooWAb5MyC1UJiEQJk4Hg4B2Vi3AJdqSUhTGYUqSnEqCFMFg" \
--no-hardware-benchmarks
```

### P2P/WS

```bash
polkadot --chain polkadot \
--base-path /tmp/node \
--name "Bootnode testnode" \
--reserved-only \
--reserved-nodes "/dns/dot-bootnode.stakeworld.io/tcp/30311/ws/p2p/12D3KooWAb5MyC1UJiEQJk4Hg4B2Vi3AJdqSUhTGYUqSnEqCFMFg" \
--no-hardware-benchmarks
```

### P2P/WebRTC

A node cannot dial WebRTC addresses, so test the WebRTC channel in the following ways instead:

1. Check the bootnode's startup logs for a `WebRTC certhash: uEi...` line, which shows that the node listens for WebRTC connections.
2. Query the bootnode's local listen addresses through its RPC endpoint:

    ```bash
    --8<-- 'code/node-infrastructure/webrtc/local-listen-addresses.sh'
    ```

    The response lists each WebRTC listen address with the certhash and peer ID appended, for example `/ip4/10.0.0.1/udp/30310/webrtc-direct/certhash/uEi.../p2p/12D3Koo...`.

3. From another machine, send a Session Traversal Utilities for NAT (STUN) binding request to the bootnode's public address and UDP port:

    ```bash
    --8<-- 'code/node-infrastructure/webrtc/check-webrtc-reachable.sh'
    ```

    The command prints `WebRTC reachable` only if the request reached the node and a STUN success response with the matching transaction ID came back. No output means the WebRTC endpoint is not reachable.

## Add WebRTC Addresses to the Chain Specification

For light clients to bootstrap over WebRTC, network operators need to add the bootnode's WebRTC address to the `bootNodes` field of the chain specification, alongside the existing TCP and WS addresses. The address has the following form:

```text
/dns/INSERT_DNS_NAME/udp/INSERT_PORT/webrtc-direct/certhash/INSERT_CERTHASH/p2p/INSERT_PEER_ID
```

Take the certhash and peer ID from the `system_localListenAddresses` response or the startup logs. Both are derived from the node key, so they only change if the node key changes.
