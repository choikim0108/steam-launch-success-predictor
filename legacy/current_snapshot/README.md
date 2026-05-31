# Current Snapshot Legacy Outputs

This directory preserves the earlier working model outputs based on current cumulative review count and current positive rate.

These files are not the final 90-day prediction workflow. They are kept only as reference evidence for the initial prototype.

Legacy criterion:

```text
success = total_reviews >= 500 AND positive_rate >= 0.80
```

Final target direction:

```text
X = store features + launch-day/7-day review signals
y = success_90d from 90-day review count and 90-day positive rate
```

