## API service for selling automatization

<b>Stack:</b> FastAPI, Dishka, SQLAlchemy

<b>Available marketplaces:</b> Ebay

<b>Features:</b>
- Find a product category by barcode image
- Find detailed product information
- Publish product to available marketplaces
- Access only to whitelisted users

### Queries 

<b>Authentication:</b>
```bash
curl -X POST https://"${url}"/api/auth/login \
    -H 'Content-Type: application/json' \
    -d '{"email": "abc@mail.random", "password": "123"}'
```
Response:
```json
{ "token": "<token>", "ttl": 1200 }
```

<b>Find categories:</b>
```bash
curl -X POST "https://"${url}"/api/search/<marketplace>/categories" \
  -H "Authorization: Bearer "${token}"" \
  -F "image=@/path/to/image.jpg;type=image/jpeg"
```

Response:
```json
{ "categories": [...], "product_name": "<product-name>" }
```

<b>Find informartion about a product:</b>
```bash
curl -X POST "https://"${url}"/api/search/<marketplace>/product" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer "${token}"" \
  -d '{
    "product_name": "'"${name}"'",
    "category": "'"${category}"'"
  }'
```

Response:
```json
{
  "metadata": {
    "description": "<description>"
  },
  "metadata_type": "Metadata",
  "product": {
    "aspects": {
      "Brand": "<brand>",
      ...
    },
    "required": ["Brand", ...],
  }
}

```
<b>Publish a product:</b>
```bash
curl -X POST "https://"${url}"/api/selling/<marketplace>/publish" \
  -H "Authorization: Bearer "${token}"" \
  -F 'item={
    "title": "<title>",
    "description": "<description>",
    "category": "<category-name>",
    "price": 120.0,
    "currency": "RUB",
    "country": "RU",
    "quantity": 1,
    "product": {"Brand": "<brand>", ...},
    "marketplace_aspects": {...}
  }' \
  -F "images=@/path/to/image.jpg;type=image/jpeg"
```

Response:
```json
{"status": "success"}
```

<b>Error response:</b>
```json
{ "error": "<error-description>" }

```
