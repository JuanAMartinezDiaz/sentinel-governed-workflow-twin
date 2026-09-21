# Capability is not authority

Agentic systems collapse a distinction that traditional software often kept implicit.

A model may be technically capable of:

- generating a transaction request
- changing a record
- contacting an external system
- spawning another agent
- invoking a privileged tool

None of those capabilities establishes the organizational right to perform the action.

Sentinel models authority as a separate object with its own evidence.

## Decision questions

Before execution, the reference engine asks:

1. Is the agent registered?
2. Is this action class delegated?
3. Is the tool approved?
4. Is the risk within the agent's ceiling?
5. Is confidence sufficient for this action?
6. Is human approval required?
7. If execution cannot proceed, what safe bounded path applies?

The output is a disposition, not merely a recommendation score.
