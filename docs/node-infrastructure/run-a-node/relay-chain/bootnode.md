---
title: Set Up a Bootnode
description: Learn how to configure and run a Polkadot bootnode that accepts P2P, WS, and WebRTC connections, and how to manage its node key.
categories: Infrastructure
---

# Set Up a Bootnode

## Introduction

Bootnodes are essential for helping blockchain nodes discover peers and join the network. When a node starts, it needs to find other nodes, and bootnodes provide an initial point of contact. Once connected, a node can expand its peer connections and play its role in the network, like participating as a validator.

This guide walks you through setting up a Polkadot bootnode that accepts P2P, WebSocket (WS), and Web Real-Time Communication (WebRTC) connections. You also learn how to manage the node key and how to test that the bootnode is running correctly and is accessible to other nodes.

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
- **P2P/WebRTC**: A WebRTC connection over UDP, also configured via `--listen-addr`. In-browser light clients such as smoldot connect this way. WebRTC needs no domain name, TLS certificate, or reverse proxy.

WebRTC works only on the litep2p network backend, which is the default. The bootnode accepts up to 500 light client connections. You can change this limit with `--in-peers-light`.

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

This assigns P2P to TCP port 30310, P2P/WS to TCP port 30311, and P2P/WebRTC to UDP port 30310. To also accept WebRTC connections over IPv6, add `--listen-addr /ip6/::/udp/30310/webrtc-direct`.

!!! warning
    The addresses you pass with `--listen-addr` replace all default listen addresses, including the WebRTC ones. If you leave out the `webrtc-direct` address, the bootnode does not accept WebRTC connections.

### Configure WebRTC Networking

Open UDP port 30310 in your firewall. Existing rules for TCP port 30310 do not cover UDP.

If the bootnode is behind network address translation (NAT), or its public port differs from its listen port, forward the public UDP port to the listen port. Then pass the public address to the node:

```bash
--public-addr /ip4/INSERT_PUBLIC_IP/udp/INSERT_PUBLIC_PORT/webrtc-direct
```

The node advertises this address in the distributed hash table (DHT), where light clients discover it.

For an IPv6 address or a DNS name, use `ip6` or `dns` instead of `ip4`. Do not append `/certhash/...` or `/p2p/...` to WebRTC listen or public addresses. The node adds both parts itself and can refuse to start if they are present.

To stop the bootnode from serving WebRTC, remove the `webrtc-direct` listen address. Blocking the UDP port is not enough. The node still advertises its WebRTC address, and light clients that try this address fail to connect.

## Testing Bootnode Connection

If the preceding node is running with DNS name `dot-bootnode.stakeworld.io` and node-id `12D3KooWAb5MyC1UJiEQJk4Hg4B2Vi3AJdqSUhTGYUqSnEqCFMFg`, then the following P2P and P2P/WS commands should output `syncing 1 peers`.

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

A node cannot dial WebRTC addresses, so you cannot test this channel with a second node. Run the following checks instead:

1. Look for a `WebRTC certhash: uEi...` line in the bootnode's startup logs. This line confirms that the bootnode listens for WebRTC connections.
2. Query the bootnode's listen addresses through its RPC endpoint. Change the port if the bootnode does not use 9944:

    ```bash
    --8<-- 'code/node-infrastructure/webrtc/local-listen-addresses.sh'
    ```

    The response lists each WebRTC listen address with the certhash and peer ID appended, for example `/ip4/10.0.0.1/udp/30310/webrtc-direct/certhash/uEi.../p2p/12D3Koo...`.

3. From another machine, send a Session Traversal Utilities for NAT (STUN) binding request to the bootnode's public address and UDP port:

    ```bash
    --8<-- 'code/node-infrastructure/webrtc/check-webrtc-reachable.sh'
    ```

    The command prints `WebRTC reachable` if the bootnode answers the request. If the command prints nothing, the WebRTC port is not reachable from that machine.

## Add WebRTC Addresses to the Chain Specification

Light clients find bootnodes through the `bootNodes` field of the chain specification. For light clients to reach your bootnode over WebRTC, add its WebRTC address to this field, next to the existing TCP and WS addresses. The address has the following form:

```text
/dns/INSERT_DNS_NAME/udp/INSERT_PORT/webrtc-direct/certhash/INSERT_CERTHASH/p2p/INSERT_PEER_ID
```

Copy the certhash and peer ID from the `system_localListenAddresses` response or the startup logs. Both values are derived from the node key, so they only change if the node key changes.
