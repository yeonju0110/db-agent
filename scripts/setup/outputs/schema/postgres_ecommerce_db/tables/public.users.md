# Table: public.users

## Columns

| Name | Type | Nullable | PK | FK | Default | Extra | Description |
|---|---|:---:|:--:|:--:|---|---|---|
| id | int4 | NO | Y |  |  |  |  |
| email | varchar | NO |  |  |  |  |  |
| username | varchar | NO |  |  |  |  |  |
| password_hash | varchar | NO |  |  |  |  |  |
| phone | varchar | YES |  |  |  |  |  |
| birth_date | date | YES |  |  |  |  |  |
| gender | gender_type | YES |  |  |  |  |  |
| status | user_status | YES |  |  | 'active'::user_status |  |  |
| created_at | timestamptz | YES |  |  | now() |  |  |
| updated_at | timestamptz | YES |  |  | now() |  |  |
| last_login_at | timestamptz | YES |  |  |  |  |  |

## Primary Key

id

## Foreign Keys
(none)

## Indexes
- users_email_key (UNIQUE): email
- users_pkey (UNIQUE): id

## Sample Queries

```sql
SELECT * FROM public.users LIMIT 10;
```

```sql
SELECT * FROM public.users WHERE id = :id;
```
