# Code Assets

Code assets are one of the reusable layers inside AI Company OS.

They are not only implementation artifacts.

They are system assets that support reliability, routing, reporting, and repeatable execution across projects.

## Core Modules

| Name | Language | Purpose | Status |
|---|---|---|---|
| checkpoint_gen.py | Python | Checkpoint generation for resume | Active |
| gateway-wrapper.sh | Shell | Model gateway wrapper | Active |
| report-integration.py | Python | Daily / weekly report integration | Active |

## Supporting Scripts and Records

| Name | Language | Purpose |
|---|---|---|
| project-registry.yaml | YAML | Project registry configuration |
| execution-records.json | JSON | Central execution tracking |

## System Modules

| Name | Purpose |
|---|---|
| novel-v1/checkpoints/ | Checkpoint storage and resume logic |
| novel-v1/manuscripts/ | Output storage |
| control-center/modules/ | Control center modules |

## Why these assets matter

These code assets show that AI Company OS is not only generating outputs.

It is also building reusable implementation layers that make the system easier to run and improve over time.

They help the system:

- reduce repeated engineering work
- support recovery and continuity
- improve routing and execution reliability
- integrate reporting into daily and weekly operation
- make future projects easier to support with the same code base

This is part of how project execution turns into reusable company assets.
