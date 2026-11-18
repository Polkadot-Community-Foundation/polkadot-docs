---
title: Run a Metanode
description: Learn what a metanode runs in its first phase, the hardware it needs, and how to serve light clients over WebRTC from a Polkadot validator and its collators.
categories: Infrastructure
---

# Run a Metanode

!!! warning "Under Construction"
    This page is under construction and its content can change. It covers what a metanode runs in its first phase, the hardware it needs, and how to serve light clients over WebRTC. Full setup instructions will be added in a later update.

## Introduction

In the first phase, a metanode operator is a [validator](/node-infrastructure/run-a-validator/requirements/) operator who also provides the minimum services that [Polkadot Products](/apps/) need:

- Producing blocks for Asset Hub and People Chain as [collators](/node-infrastructure/run-a-collator/).
- Serving smoldot [light clients](/reference/tools/light-clients/) over Web Real-Time Communication (WebRTC) for the relay chain, Asset Hub, and People Chain. [Serve Light Clients over WebRTC](#serve-light-clients-over-webrtc) covers the node configuration this requires.
- Serving remote procedure call (RPC) requests for the relay chain, Asset Hub, and People Chain.

You can run the validator and the collators on separate machines or together on a single machine. [Hardware Requirements](#hardware-requirements) covers both options.

## Hardware Requirements

The following table lists the recommended minimum requirements for each service on its own machine and for a single machine that runs all three services:

| Resource | Validator                   | Asset Hub Collator                    | People Chain Collator                 | Single Machine                                            |
|:--------:|:---------------------------:|:-------------------------------------:|:-------------------------------------:|:---------------------------------------------------------:|
| CPU      | 8 physical cores at 3.4 GHz | 4+ cores (8+ for optimal performance) | 4+ cores (8+ for optimal performance) | 16 physical cores at 3.4 GHz (24 for optimal performance) |
| Memory   | 32 GB DDR4 ECC              | 32 GB (64 GB for optimal performance) | 32 GB (64 GB for optimal performance) | 64 GB DDR4 ECC (128 GB for optimal performance)           |
| Storage  | 2 TB+ NVMe SSD              | 200+ GB NVMe SSD, pruned              | 200+ GB NVMe SSD, pruned              | 2.4 TB+ NVMe SSD                                          |
| Network  | 500 Mbit/s symmetric        | 500+ Mbit/s, stable connection        | 500+ Mbit/s, stable connection        | 1 Gbit/s symmetric                                        |

Every machine needs a public IP address and must run Linux with kernel 5.16 or later. When you choose hardware, also consider the following details:

- **CPU**: The validator must meet the processor requirements in [Validator Requirements](/node-infrastructure/run-a-validator/requirements/#minimum-hardware-requirements), including disabled simultaneous multithreading. Prioritize single-threaded performance over core count.
- **Storage**: Prioritize latency over throughput. Fast disk I/O is critical for collator block production. Validator and single-machine storage requirements grow with the chains.
- **Network**: The collator figures are higher than the 100+ Mbit/s in [Run a Block-Producing Collator](/node-infrastructure/run-a-collator/#hardware-requirements) because metanode collators also serve RPC requests and light clients.
- **Relay chain data**: To use storage efficiently, point each collator at your validator's RPC endpoint with `--relay-chain-rpc-urls`, as described in [Run a Block-Producing Collator](/node-infrastructure/run-a-collator/#run-the-collator). The collator then reads relay chain data from the validator and runs a lightweight relay chain node instead of keeping a full relay chain database, which removes most of the collator's relay chain database storage.
- **Single machine**: CPU and storage are the sum of the per-service figures, including 24 cores for optimal performance. Memory and network are lower than the sum because the services do not all reach peak load at the same time: 64 GB of memory instead of 96 GB (128 GB instead of 160 GB for optimal performance), and 1 Gbit/s of network instead of 1.5 Gbit/s.

!!! warning "Validator Hardware Alone Is Not Enough"
    The hardware listed in [Validator Requirements](/node-infrastructure/run-a-validator/requirements/#minimum-hardware-requirements) is not enough to also run the collators. Running the validator and the Asset Hub collator on a machine that meets only the validator requirements leaves too few resources for validation.

## Serve Light Clients over WebRTC

In-browser light clients connect to full nodes over WebRTC. Unlike secure WebSocket connections, WebRTC needs no domain name, TLS certificate, or reverse proxy. It runs over UDP, so it needs its own firewall and port configuration.

WebRTC works only on the litep2p network backend, which is the default. Each node accepts up to 500 light client connections. You can change this limit with `--in-peers-light`.

### Enable WebRTC Listening

Which nodes listen for WebRTC connections by default depends on the release:

- **`polkadot-stable2612` and later**: Every node listens, including validators and collators. Your validator serves relay chain light clients, and your collators serve Asset Hub and People Chain light clients.
- **Earlier releases**: Validators and collators do not listen. Run a separate full node for each of the relay chain, Asset Hub, and People Chain to serve light clients.

If you pass `--listen-addr` to a node, your addresses replace all default listen addresses, including the WebRTC ones. In that case, add a WebRTC listen address yourself, for example `/ip4/0.0.0.0/udp/30333/webrtc-direct` or `/ip6/::/udp/30333/webrtc-direct`.

### Configure Ports and Public Addresses

A node listens for WebRTC on the UDP port with the same number as its P2P TCP port. The default is 30333, which you can change with `--port`. A collator uses two ports by default, 30333 for the parachain and 30334 for the relay chain. When you run several nodes on a single machine, give each node its own ports.

Open every WebRTC UDP port in your firewall. Existing rules for the TCP ports do not cover UDP.

If a node is behind network address translation (NAT), or its public port differs from its listen port, forward the public UDP port to the listen port. Then pass the public address to the node, so light clients can discover the node at that address:

```bash
--public-addr /ip4/INSERT_PUBLIC_IP/udp/INSERT_PUBLIC_PORT/webrtc-direct
```

For an IPv6 address or a DNS name, use `ip6` or `dns` instead of `ip4`. Do not append `/certhash/...` or `/p2p/...` to WebRTC listen or public addresses. The node adds both parts itself and can refuse to start if they are present.

To stop a node from serving WebRTC, pass `--listen-addr` with TCP and WS addresses only. Blocking the UDP port is not enough. The node still advertises its WebRTC address, and light clients that try this address fail to connect.

### Verify WebRTC Connectivity

Run the following checks on each node that serves light clients:

1. Look for a `WebRTC certhash: uEi...` line in the node's startup logs. This line confirms that the node listens for WebRTC connections.
2. Query the node's listen addresses through its RPC endpoint. Change the port if the node does not use 9944:

    ```bash
    --8<-- 'code/node-infrastructure/webrtc/local-listen-addresses.sh'
    ```

    The response lists each WebRTC listen address with the certhash and peer ID appended, for example `/ip4/10.0.0.1/udp/30333/webrtc-direct/certhash/uEi.../p2p/12D3Koo...`.

3. From another machine, send a Session Traversal Utilities for NAT (STUN) binding request to the node's public address and UDP port:

    ```bash
    --8<-- 'code/node-infrastructure/webrtc/check-webrtc-reachable.sh'
    ```

    The command prints `WebRTC reachable` if the node answers the request. If the command prints nothing, the WebRTC port is not reachable from that machine.
