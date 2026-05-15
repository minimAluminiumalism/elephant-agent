# continuity.correction-aware-recovery

## Setup

- a resumed session has one superseded evidence row and one corrected replacement
- the corrected row is later deleted after verification
- recovery opens explicit State and recent-Episode scope

## Steps

1. request wake recovery after the correction
2. verify the corrected row wins over the superseded row
3. delete the corrected row and rerun recovery

## Assertions

- superseded rows never outrank their corrected replacement
- deleted rows disappear from derived retrieval views
- the runtime still explains why the surviving evidence won
