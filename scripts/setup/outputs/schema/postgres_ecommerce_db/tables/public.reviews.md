# Table: public.reviews

## Columns

| Name | Type | Nullable | PK | FK | Default | Extra | Description |
|---|---|:---:|:--:|:--:|---|---|---|
| id | int4 | NO | Y |  |  |  |  |
| user_id | int4 | NO |  | Y |  |  |  |
| product_id | int4 | NO |  | Y |  |  |  |
| order_id | int4 | YES |  | Y |  |  |  |
| rating | int4 | NO |  |  |  |  |  |
| title | varchar | YES |  |  |  |  |  |
| content | text | YES |  |  |  |  |  |
| is_verified_purchase | bool | YES |  |  | false |  |  |
| helpful_count | int4 | YES |  |  | 0 |  |  |
| status | review_status | YES |  |  | 'pending'::review_status |  |  |
| created_at | timestamptz | YES |  |  | now() |  |  |

## Primary Key

id

## Foreign Keys
- reviews_user_id_fkey: user_id -> public.users(id)
- reviews_product_id_fkey: product_id -> public.products(id)
- reviews_order_id_fkey: order_id -> public.orders(id)

## Indexes
- reviews_pkey (UNIQUE): id

## Sample Queries

```sql
SELECT * FROM public.reviews LIMIT 10;
```

```sql
SELECT * FROM public.reviews WHERE id = :id;
```

```sql
SELECT t.* FROM public.reviews t JOIN public.users r ON t.user_id = r.id LIMIT 10;
```

```sql
SELECT t.* FROM public.reviews t JOIN public.products r ON t.product_id = r.id LIMIT 10;
```
