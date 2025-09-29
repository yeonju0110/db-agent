# Table: public.user_addresses

## Columns

| Name | Type | Nullable | PK | FK | Default | Extra | Description |
|---|---|:---:|:--:|:--:|---|---|---|
| id | int4 | NO | Y |  |  |  |  |
| user_id | int4 | NO |  | Y |  |  |  |
| name | varchar | NO |  |  |  |  |  |
| phone | varchar | YES |  |  |  |  |  |
| address | varchar | NO |  |  |  |  |  |
| detail_address | varchar | YES |  |  |  |  |  |
| postal_code | varchar | YES |  |  |  |  |  |
| city | varchar | YES |  |  |  |  |  |
| state | varchar | YES |  |  |  |  |  |
| is_default | bool | YES |  |  | false |  |  |
| created_at | timestamptz | YES |  |  | now() |  |  |

## Primary Key

id

## Foreign Keys
- user_addresses_user_id_fkey: user_id -> public.users(id)

## Indexes
- user_addresses_pkey (UNIQUE): id

## Sample Queries

```sql
SELECT * FROM public.user_addresses LIMIT 10;
```

```sql
SELECT * FROM public.user_addresses WHERE id = :id;
```

```sql
SELECT t.* FROM public.user_addresses t JOIN public.users r ON t.user_id = r.id LIMIT 10;
```
