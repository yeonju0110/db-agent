# Table: public.user_activities

## Columns

| Name | Type | Nullable | PK | FK | Default | Extra | Description |
|---|---|:---:|:--:|:--:|---|---|---|
| id | int4 | NO | Y |  |  |  |  |
| user_id | int4 | YES |  | Y |  |  |  |
| activity_type | activity_type | NO |  |  |  |  |  |
| product_id | int4 | YES |  | Y |  |  |  |
| session_id | varchar | YES |  |  |  |  |  |
| ip_address | varchar | YES |  |  |  |  |  |
| user_agent | text | YES |  |  |  |  |  |
| created_at | timestamptz | YES |  |  | now() |  |  |

## Primary Key

id

## Foreign Keys
- user_activities_user_id_fkey: user_id -> public.users(id)
- user_activities_product_id_fkey: product_id -> public.products(id)

## Indexes
- user_activities_pkey (UNIQUE): id

## Sample Queries

```sql
SELECT * FROM public.user_activities LIMIT 10;
```

```sql
SELECT * FROM public.user_activities WHERE id = :id;
```

```sql
SELECT t.* FROM public.user_activities t JOIN public.users r ON t.user_id = r.id LIMIT 10;
```

```sql
SELECT t.* FROM public.user_activities t JOIN public.products r ON t.product_id = r.id LIMIT 10;
```
