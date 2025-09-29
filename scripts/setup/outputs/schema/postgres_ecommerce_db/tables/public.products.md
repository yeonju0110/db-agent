# Table: public.products

## Columns

| Name | Type | Nullable | PK | FK | Default | Extra | Description |
|---|---|:---:|:--:|:--:|---|---|---|
| id | int4 | NO | Y |  |  |  |  |
| category_id | int4 | NO |  | Y |  |  |  |
| name | varchar | NO |  |  |  |  |  |
| description | text | YES |  |  |  |  |  |
| price | numeric | NO |  |  |  |  |  |
| cost | numeric | YES |  |  |  |  |  |
| brand | varchar | YES |  |  |  |  |  |
| model | varchar | YES |  |  |  |  |  |
| status | product_status | YES |  |  | 'active'::product_status |  |  |
| weight | numeric | YES |  |  |  |  |  |
| dimensions | varchar | YES |  |  |  |  |  |
| created_at | timestamptz | YES |  |  | now() |  |  |
| updated_at | timestamptz | YES |  |  | now() |  |  |

## Primary Key

id

## Foreign Keys
- products_category_id_fkey: category_id -> public.categories(id)

## Indexes
- products_pkey (UNIQUE): id

## Sample Queries

```sql
SELECT * FROM public.products LIMIT 10;
```

```sql
SELECT * FROM public.products WHERE id = :id;
```

```sql
SELECT t.* FROM public.products t JOIN public.categories r ON t.category_id = r.id LIMIT 10;
```
