from prometheus_client import Counter, Gauge, Histogram, Summary

countNewUsers  = Counter("new_users", "New users in tenant")
