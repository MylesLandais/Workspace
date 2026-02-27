// Subreddit statistics schema
// Run this migration to enable storing post count statistics on Subreddit nodes

// Note: Statistics are stored as properties on Subreddit nodes:
// - stats: Map containing monthly_counts, yearly_counts, all_time_estimate, etc.
// - stats_updated_at: DateTime when statistics were last updated
// - post_velocity: Float (average posts per day, calculated from recent months)

// Create index for statistics queries
CREATE INDEX subreddit_stats_updated_at_index IF NOT EXISTS
FOR (s:Subreddit) ON (s.stats_updated_at);

// Example stats structure stored in s.stats:
// {
//   "monthly_counts": {"2024-01": 150, "2024-02": 180, ...},
//   "yearly_counts": {"2023": 2000, "2024": 2500},
//   "all_time_estimate": 50000,
//   "post_velocity": 5.2  // posts per day
// }






