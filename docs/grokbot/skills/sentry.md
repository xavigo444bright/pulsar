# Skill: paper sentry

1. `pulsar overview` or `GET http://127.0.0.1:8000/v1/overview`
2. If `kill.tripped` is true, notify the owner with `reason`.
3. Never call `/v1/kill/reset` unless the owner typed a confirmation in the Bot chat.
