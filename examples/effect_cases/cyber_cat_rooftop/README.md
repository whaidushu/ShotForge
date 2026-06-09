# Cyber Cat Rooftop Effect Case

This fixed case is the first ShotForge effect-demo target. It focuses on a
single five-second shot with concrete physical requirements: visible subject,
object, setting, weather, time of day, and action relationship.

The expected demo flow is:

```text
case target -> v1 raw-prompt generation -> v2 structured-prompt generation
-> frame observation -> physical evaluation -> targeted revision plan
-> v3 candidate generation -> candidate acceptance gate -> comparison report
```

The case is intentionally narrow so the project can prove measurable iteration,
preservation locks, and candidate rejection before expanding to multi-shot
continuity, style consistency, and atmosphere.
