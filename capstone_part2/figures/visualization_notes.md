# Traffic visualisation findings

Scope: all available years in the cleaned dataset. Records are averaged by timestamp before plotting, so each observed timestamp has equal weight. Missing hours are not filled with zero.

## 1. Average traffic by hour
The highest hourly mean occurs at 16:00 (5,708.61 vehicles), and the lowest at 03:00 (373.21 vehicles). These differences support time-specific mobility planning.

## 2. Weekday and weekend patterns
Average traffic is 3,557.44 vehicles on weekdays and 2,623.93 on weekends. The hourly curves allow comparison at similar times of day. Unequal coverage and holidays may influence these averages.

## 3. Temperature and traffic
The Pearson correlation for the cleaned, timestamp-averaged data is 0.139. The scatter shows whether similar temperatures coincide with different traffic volumes. This association does not establish causation because time of day and season may influence both variables. This calculation uses a different preparation method from the raw-record correlation in Part 1.
