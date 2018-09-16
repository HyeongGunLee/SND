# Device Registry Service

## Usage

All responses will have the form

```json
{
  "data": "Mixed type holding the content of the response",
  "message": "Description of what happend"
}
```

Subsequent response definitions will only detail the expected value of the 'data field'

### List all Devices

**Definition**

`GET /devices`

**Response**

- `200 OK` on success
