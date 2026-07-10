# CareerKundi lifecycle domain (0050-PF7-S1)

## Owns

- `GoalRef` / `RecommendationRef` / `AttemptRef` / `OutcomeRef` / `FeedbackRef`
- Controlled kind/status enums
- Thin storage stubs for the lifecycle loop
- Create/get/list service helpers

## Does not own

- Workflow engines, schedulers, queues
- Recommendation ranking / job matching
- Application automation / agent planners
- Outcome scoring / ML feedback loops
- Public FastAPI lifecycle API
- Claim-to-lifecycle linking

## Semantics

| Concept | Meaning |
|---------|---------|
| Goal | What a subject aims for |
| Recommendation | A stored suggestion (not the recommender) |
| Attempt | Record that something was tried (not automation) |
| Outcome | What happened |
| Feedback | A response or learning signal |

**Thin records only.** No helper runs workflows, schedules tasks, or scores recommendations.
