# Gateway App

This surface owns messaging ingress and delivery processes.

## Own Here

- adapter lifecycle
- runtime process wiring
- inbound event normalization
- outbound delivery handling

## Do Not Own Here

- memory rules
- elephant-State ownership policy
- Personal Model semantics
- deleted product-facing reset-era system-layer terms or legacy planning
  semantics

Gateway behavior should flow through `packages/gateway_core/` and the kernel.
