# Anveshak Frontend API Documentation

**Base URL**: `http://localhost:8000` (or your server URL)

All endpoints return JSON. All IDs are strings (MongoDB ObjectIds converted).

---

## Quick Start

```typescript
// Example: Fetch dashboard stats
const stats = await fetch('http://localhost:8000/api/stats?hours=24')
  .then(r => r.json());

// Example: Get latest insights
const insight = await fetch('http://localhost:8000/api/insights/latest')
  .then(r => r.json());
```

---

## Health Check

**GET** `/health`

```json
{ "status": "ok" }
```

---

## Statistics

**GET** `/api/stats?hours=24`

Returns comprehensive dashboard statistics.

**Query Params:**
- `hours` (int, default: 24) - Time range for "recent" counts

**Response:**
```json
{
  "time_range_hours": 24,
  "raw_logs": {
    "total": 1000,
    "processed": 950,
    "unprocessed": 50,
    "recent": 200
  },
  "processed_logs": {
    "total": 950,
    "recent": 200,
    "by_cluster_type": {
      "error": 50,
      "warning": 30,
      "info": 120
    }
  },
  "clusters": {
    "total": 150,
    "recent": 25,
    "by_type": {
      "error": 10,
      "pii": 2,
      "debug": 5
    }
  },
  "errors": {
    "total": 80,
    "unresolved": 15,
    "recent": 20,
    "high_severity": 5
  },
  "crashes": {
    "total": 5,
    "unresolved": 2,
    "recent": 1,
    "critical": 1
  },
  "insights": {
    "total": 50,
    "recent": 6
  }
}
```

---

## Insights

### Get All Insights
**GET** `/api/insights`

**Query Params:**
- `type` (string) - Filter by type: `periodic`, `batch`
- `limit` (int, default: 50)
- `skip` (int, default: 0)
- `hours` (int) - Filter by last N hours

**Response:**
```json
{
  "insights": [
    {
      "_id": "507f1f77bcf86cd799439011",
      "insight_type": "periodic",
      "insight": "Detected 5 errors in last 10 minutes...",
      "impact_level": "MEDIUM",
      "recommendation": "Review high severity errors immediately",
      "trend_analysis": "Active monitoring: 25 clusters created",
      "error_count": 5,
      "high_severity_count": 2,
      "created_at": "2025-01-15T10:30:00Z"
    }
  ],
  "total": 50,
  "limit": 50,
  "skip": 0
}
```

### Get Latest Insight
**GET** `/api/insights/latest`

Returns the most recent insight.

### Get Specific Insight
**GET** `/api/insights/<insight_id>`

---

## Errors

### Get All Errors
**GET** `/api/errors`

**Query Params:**
- `severity_min` (int) - Minimum severity (0-10)
- `severity_max` (int) - Maximum severity (0-10)
- `priority` (string) - `HIGH`, `MEDIUM`, `LOW`
- `resolved` (bool) - Filter by resolved status
- `limit` (int, default: 100)
- `skip` (int, default: 0)
- `hours` (int) - Filter by last N hours

**Response:**
```json
{
  "errors": [
    {
      "_id": "507f1f77bcf86cd799439011",
      "log_id": "507f1f77bcf86cd799439012",
      "error_type": "database_connection",
      "error_message": "Connection timeout",
      "severity": 7,
      "priority": "HIGH",
      "root_cause": "Database connection pool exhausted",
      "impact": "User requests failing",
      "likely_fix": "Increase connection pool size",
      "stakeholder_insight": "Database connectivity issues affecting user experience",
      "resolved": false,
      "created_at": "2025-01-15T10:30:00Z",
      "timestamp": "2025-01-15T10:29:45Z"
    }
  ],
  "total": 80,
  "limit": 100,
  "skip": 0
}
```

### Get Specific Error
**GET** `/api/errors/<error_id>`

### Resolve Error
**POST** `/api/errors/<error_id>/resolve`

**Response:**
```json
{ "message": "Error marked as resolved" }
```

---

## Crashes

### Get All Crashes
**GET** `/api/crashes`

**Query Params:**
- `severity_min`, `severity_max` (int)
- `type` (string) - Crash type filter
- `resolved` (bool)
- `limit`, `skip` (int)
- `hours` (int)

**Response:**
```json
{
  "crashes": [
    {
      "_id": "507f1f77bcf86cd799439011",
      "log_id": "507f1f77bcf86cd799439012",
      "crash_type": "application_crash",
      "severity": 9,
      "crash_indicators": ["segmentation fault", "null pointer"],
      "affected_components": ["api-service", "database"],
      "recovery_status": "automatic",
      "immediate_actions": ["Restart service", "Check logs"],
      "root_cause": "Memory leak causing OOM",
      "prevention": "Fix memory leak in service",
      "resolved": false,
      "created_at": "2025-01-15T10:30:00Z",
      "timestamp": "2025-01-15T10:29:45Z"
    }
  ],
  "total": 5,
  "limit": 100,
  "skip": 0
}
```

### Get Specific Crash
**GET** `/api/crashes/<crash_id>`

### Resolve Crash
**POST** `/api/crashes/<crash_id>/resolve`

---

## Clusters

### Get All Clusters
**GET** `/api/clusters`

**Query Params:**
- `type` (string) - Filter by type: `error`, `warning`, `info`, `pii`, `debug`, `crash`
- `requires_review` (bool)
- `limit` (int, default: 100)
- `skip` (int, default: 0)

**Response:**
```json
{
  "clusters": [
    {
      "_id": "507f1f77bcf86cd799439011",
      "cluster_type": "error",
      "category": "ERROR",
      "log_ids": ["507f1f77bcf86cd799439012", "507f1f77bcf86cd799439013"],
      "count": 2,
      "pii_types": [],
      "requires_review": true,
      "pattern_matches": [],
      "is_anomaly": false,
      "severity": 6,
      "created_at": "2025-01-15T10:30:00Z",
      "updated_at": "2025-01-15T10:35:00Z"
    }
  ],
  "total": 150,
  "limit": 100,
  "skip": 0
}
```

### Get Specific Cluster
**GET** `/api/clusters/<cluster_id>`

---

## Processed Logs

### Get All Processed Logs
**GET** `/api/processed-logs`

**Query Params:**
- `cluster_type` (string)
- `severity_min`, `severity_max` (int)
- `connection_id` (string)
- `requires_review` (bool)
- `limit`, `skip` (int)
- `hours` (int)

**Response:**
```json
{
  "logs": [
    {
      "_id": "507f1f77bcf86cd799439011",
      "raw_log_id": "507f1f77bcf86cd799439012",
      "connection_id": "default",
      "event": "log_event",
      "data": "Error occurred...",
      "timestamp": "2025-01-15T10:30:00Z",
      "severity": 6,
      "cluster_type": "error",
      "category": "ERROR",
      "pii_types": [],
      "requires_review": true,
      "is_anomaly": false,
      "anomaly_score": 0.8,
      "patterns_matched": [...],
      "created_at": "2025-01-15T10:30:00Z"
    }
  ],
  "total": 950,
  "limit": 100,
  "skip": 0
}
```

### Get Specific Processed Log
**GET** `/api/processed-logs/<log_id>`

---

## Raw Logs

### Get All Raw Logs
**GET** `/api/raw-logs`

**Query Params:**
- `connection_id` (string)
- `processed` (bool)
- `limit`, `skip` (int)
- `hours` (int)

**Response:**
```json
{
  "logs": [
    {
      "_id": "507f1f77bcf86cd799439011",
      "event": "log_event",
      "data": "Raw log data...",
      "timestamp": 1705315800,
      "connection_id": "default",
      "processed": true,
      "created_at": "2025-01-15T10:30:00Z"
    }
  ],
  "total": 1000,
  "limit": 100,
  "skip": 0
}
```

### Get Specific Raw Log
**GET** `/api/raw-logs/<log_id>`

---

## WebSocket Management

### Add WebSocket Connection
**POST** `/api/websocket/add`

**Body:**
```json
{
  "url": "ws://example.com/socket.io",
  "id": "connection-1"
}
```

**Response:**
```json
{
  "message": "WebSocket connection initiated",
  "connection_id": "connection-1",
  "url": "ws://example.com/socket.io",
  "status": "connecting"
}
```

### Get WebSocket Status
**GET** `/api/websocket/status?id=<connection_id>`

**Response:**
```json
{
  "connection_id": "connection-1",
  "url": "ws://example.com/socket.io",
  "connected": true,
  "error": null,
  "log_count": 150
}
```

### Remove WebSocket Connection
**DELETE** `/api/websocket/remove`

**Body:**
```json
{ "id": "connection-1" }
```

### Get WebSocket Logs
**GET** `/api/websocket/logs?id=<connection_id>&limit=50`

---

## Data Types

### Severity Levels
- `0-2`: Low (INFO)
- `3-4`: Medium (WARNING)
- `5-7`: High (ERROR)
- `8-10`: Critical (CRASH)

### Cluster Types
- `info` - Informational logs
- `warning` - Warning logs
- `error` - Error logs
- `crash` - Crash logs
- `pii` - Contains PII
- `debug` - Debug logs

### Priority Levels
- `HIGH` - Immediate attention required
- `MEDIUM` - Should be reviewed soon
- `LOW` - Can be reviewed later

### Impact Levels
- `HIGH` - Significant impact
- `MEDIUM` - Moderate impact
- `LOW` - Minimal impact
- `NONE` - No impact

---

## Example Dashboard Queries

```typescript
// Dashboard overview
const stats = await fetch('/api/stats?hours=24').then(r => r.json());

// Recent high-severity errors
const errors = await fetch('/api/errors?severity_min=7&resolved=false&limit=10')
  .then(r => r.json());

// Latest insights
const insights = await fetch('/api/insights?limit=5').then(r => r.json());

// Unresolved crashes
const crashes = await fetch('/api/crashes?resolved=false').then(r => r.json());

// Clusters requiring review
const clusters = await fetch('/api/clusters?requires_review=true&limit=20')
  .then(r => r.json());

// Recent processed logs by type
const errorLogs = await fetch('/api/processed-logs?cluster_type=error&hours=1&limit=50')
  .then(r => r.json());
```

---

## Error Responses

All errors follow this format:

```json
{
  "error": "Error message here"
}
```

**Status Codes:**
- `200` - Success
- `400` - Bad Request
- `404` - Not Found
- `500` - Server Error

---

## Notes

- All timestamps are in ISO 8601 format (UTC)
- Pagination: Use `limit` and `skip` for pagination
- Refresh intervals: Insights and clusters refresh every 10 minutes
- All IDs are strings (MongoDB ObjectIds converted to strings)
- Empty arrays/objects are returned when no data matches filters

