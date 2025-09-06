# Mock API (FastAPI + MongoDB)

A small FastAPI project that uses MongoDB for persistence. On startup the
application seeds fake data with [Faker](https://faker.readthedocs.io/) and
exposes CRUD endpoints for several resources.

## Resources

| Resource   | Endpoint      |
|------------|---------------|
| Products   | `/products`   |
| Stores     | `/stores`     |
| Categories | `/categories` |
| Brands     | `/brands`     |
| Warehouses | `/warehouses` |
| Files/Upload | `/files/upload` |

Products are linked to stores, categories, brands, warehouses and images. When
a collection is empty the application generates about 100 fake documents and
stores them in MongoDB. Image URLs are sourced from `picsum.photos`.

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export MONGO_URL="mongodb://localhost:27017"
export MONGO_DB="mockapi"
uvicorn main:app --reload
```

Open http://127.0.0.1:8000/docs to explore the interactive API documentation.

## Standard Response Contract

All endpoints (except file upload) return a consistent envelope:

```json
{
  "data": ...,            // object | array | null
  "meta": {
    "message": "<domain.action.status>",
    "status": "success",
    "code": "200",
    "timestamp": "2025-01-01T00:00:00.000000",
    "trace_id": "...",
    "correlation_id": "...",
    "request_id": "...",
    "method": "GET",
    "path": "/brands",
    "query": null,
    "host": "127.0.0.1",
    "additional": {},
    "pagination": {
      "page": 1,
      "limit": 10,
      "total": 1,
      "total_pages": 1,
      "has_next": false,
      "has_previous": false
    }
  }
}
```

Validation and other errors use:

```json
{
  "code": 422,
  "message": "validation.error",
  "errors": [
    {"field": "name", "message": "Field required"}
  ],
  "timestamp": "2025-01-01T00:00:00.000000"
}
```

Notes:
- Correlation/trace/request IDs are available in response headers as `X-Correlation-ID`, `X-Trace-ID`, `X-Request-ID`.
- Upload API keeps `{ files: [...] }` shape to stay simple for frontend.
