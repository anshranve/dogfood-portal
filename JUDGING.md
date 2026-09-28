# Judging design

## Assignment and isolation

Each judge is assigned to one or more tracks in the fixture data. The score endpoint treats the authenticated session as the source of truth for a judge identity. A `judge` query parameter can never switch that identity, so Judge B receives `403 Forbidden` when requesting Judge A's records.

## Weighted scoring

The portal preserves criterion-level scores from the fixture file. A production extension should allow organizers to define each criterion and its weight per event, then compute a project's raw score as the sum of `criterion_score × criterion_weight` divided by total weight.

## Normalization approach

The next implementation step is judge z-score normalization: calculate each judge's mean and standard deviation across completed reviews, transform that judge's raw score into a z-score, then convert it to a common display scale. A judge who scores every project unusually high or low therefore has less effect on rank. If a judge has no variation in scores, retain their raw weighted score and flag it for organizer review instead of dividing by zero.

## Auditability

The source fixture preserves the criterion values and comments that led to every displayed score. CSV exports let organizers independently inspect project data without a database client.
