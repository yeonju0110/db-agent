# Table: public.inventory

## Columns

| Name | Type | Nullable | PK | FK | Default | Extra | Description |
|---|---|:---:|:--:|:--:|---|---|---|
| id | int4 | NO | Y |  |  |  |  |
| product_id | int4 | NO |  | Y |  |  |  |
| quantity | int4 | NO |  |  | 0 |  |  |
| reserved_quantity | int4 | NO |  |  | 0 |  |  |
| reorder_level | int4 | YES |  |  | 10 |  |  |
| warehouse_location | varchar | YES |  |  |  |  |  |
| last_updated | timestamptz | YES |  |  | now() |  |  |

## Primary Key

id

## Foreign Keys
- inventory_product_id_fkey: product_id -> public.products(id)

## Indexes
- inventory_pkey (UNIQUE): id

## Sample Queries

```sql
SELECT * FROM public.inventory LIMIT 10;
```

```sql
SELECT * FROM public.inventory WHERE id = :id;
```

```sql
SELECT t.* FROM public.inventory t JOIN public.products r ON t.product_id = r.id LIMIT 10;
```
