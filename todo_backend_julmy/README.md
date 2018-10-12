# TODO-Backend

Author : Sylvain Julmy

## App

To run the application :
```
-m aiohttp.web -P 8080 aiotodo:app_factory
```

and be sure that the working directory is the same as the `aiotodo.py` in order to recover the sqlite db file.

To clear the table, just run the SQL command from `create_table.sql` for the `todo_backend.sqlite` database.