# Table: public.orders

## Columns

| Name | Type | Nullable | PK | FK | Default | Extra | Description |
|---|---|:---:|:--:|:--:|---|---|---|
| id | int4 | NO | Y |  |  |  |  |
| user_id | int4 | NO |  | Y |  |  |  |
| order_number | varchar | NO |  |  |  |  |  |
| status | order_status | YES |  |  | 'pending'::order_status |  |  |
| total_amount | numeric | NO |  |  |  |  |  |
| discount_amount | numeric | YES |  |  | 0 |  |  |
| shipping_fee | numeric | YES |  |  | 0 |  |  |
| tax_amount | numeric | YES |  |  | 0 |  |  |
| payment_method | payment_method_type | NO |  |  |  |  |  |
| shipping_address_id | int4 | YES |  | Y |  |  |  |
| order_date | timestamptz | YES |  |  | now() |  |  |
| shipped_at | timestamptz | YES |  |  |  |  |  |
| delivered_at | timestamptz | YES |  |  |  |  |  |
| notes | text | YES |  |  |  |  |  |

## Primary Key

id

## Foreign Keys
- orders_user_id_fkey: user_id -> public.users(id)
- orders_shipping_address_id_fkey: shipping_address_id -> public.user_addresses(id)

## Indexes
- orders_order_number_key (UNIQUE): order_number
- orders_pkey (UNIQUE): id

## Sample Queries

```sql
SELECT * FROM public.orders LIMIT 10;
```

```sql
SELECT * FROM public.orders WHERE id = :id;
```

```sql
SELECT t.* FROM public.orders t JOIN public.users r ON t.user_id = r.id LIMIT 10;
```

```sql
SELECT t.* FROM public.orders t JOIN public.user_addresses r ON t.shipping_address_id = r.id LIMIT 10;
```
