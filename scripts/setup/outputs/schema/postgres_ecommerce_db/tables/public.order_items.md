# Table: public.order_items

## Columns

| Name | Type | Nullable | PK | FK | Default | Extra | Description |
|---|---|:---:|:--:|:--:|---|---|---|
| id | int4 | NO | Y |  |  |  |  |
| order_id | int4 | NO |  | Y |  |  |  |
| product_id | int4 | NO |  | Y |  |  |  |
| quantity | int4 | NO |  |  |  |  |  |
| unit_price | numeric | NO |  |  |  |  |  |
| total_price | numeric | NO |  |  |  |  |  |
| created_at | timestamptz | YES |  |  | now() |  |  |

## Primary Key

id

## Foreign Keys
- order_items_order_id_fkey: order_id -> public.orders(id)
- order_items_product_id_fkey: product_id -> public.products(id)

## Indexes
- order_items_pkey (UNIQUE): id

## Sample Queries

```sql
SELECT * FROM public.order_items LIMIT 10;
```

```sql
SELECT * FROM public.order_items WHERE id = :id;
```

```sql
SELECT t.* FROM public.order_items t JOIN public.orders r ON t.order_id = r.id LIMIT 10;
```

```sql
SELECT t.* FROM public.order_items t JOIN public.products r ON t.product_id = r.id LIMIT 10;
```
