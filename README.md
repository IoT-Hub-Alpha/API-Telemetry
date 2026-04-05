# Telemetry API

## Summary
This app provides READ ONLY endpoint for telemetry DB and forwards requests to scala aggregation.

## Endpoints:
`.../v1/telemetry/health`

### supported operations:
- GET

Provides health status

`.../v1/telemetry/aggregates`

### supported operations:
- GET

Provides aggregate data per device, query parameters:

|Parameter| Description | Default|
|---------|-------------|--------|
|device|Serial number of requested device | None - Mandatory field |
|operation| Operation performed on data set - avg/median/min/max | avg|
|window|Window (in seconds) of aggregation operation| 30|

### example request:
`.../v1/telemetry/aggregates?device=SN-111&window=120&operation=min`

will find the lowest value for device SN-111 in the last 2 minutes (120 seconds)

`.../v1/telemetry`

### supported operations:
- GET

provides paginated telemetry data per device , query parameters:

|Parameter| Description | Default|
|---------|-------------|--------|
|page_size|results per page | 10 |
|page| requested page | 1|
|device|Serial number of requested device| None - Not mandatory|
|before|Results before a certain datetime | None - Not mandatory|
|after|Results after a certain datetime | None - Not mandatory|

### example request:
`.../v1/telemetry?device=SN-111`

will fetch a paginated result of all telemetry data submited by device `SN-111`