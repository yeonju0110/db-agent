# Table: public.payments

## Columns

| Name | Type | Nullable | PK | FK | Default | Extra | Description |
|---|---|:---:|:--:|:--:|---|---|---|
| id | int4 | NO | Y |  |  |  |  |
| order_id | int4 | NO |  | Y |  |  |  |
| payment_method | payment_method_type | NO |  |  |  |  |  |
| amount | numeric | NO |  |  |  |  |  |
| status | payment_status | YES |  |  | 'pending'::payment_status |  |  |
| transaction_id | varchar | YES |  |  |  |  |  |
| gateway | varchar | YES |  |  |  |  |  |
| paid_at | timestamptz | YES |  |  |  |  |  |
| created_at | timestamptz | YES |  |  | now() |  |  |

## Primary Key

id

## Foreign Keys
- payments_order_id_fkey: order_id -> public.orders(id)

## Indexes
- payments_pkey (UNIQUE): id

## Sample Queries

```sql
SELECT * FROM public.payments LIMIT 10;
```

```sql
SELECT * FROM public.payments WHERE id = :id;
```

```sql
SELECT t.* FROM public.payments t JOIN public.orders r ON t.order_id = r.id LIMIT 10;
```
