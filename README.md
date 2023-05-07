
## Database

### Create Alembic migration
`alembic revision --autogenerate -m 'Change name' --rev-id 0000`

### Apply alembic migration
`alembic upgrade head`


## Translations

Based on https://docs.aiogram.dev/en/latest/examples/i18n_example.html

### Extract text
```
pybabel extract  -o locales/FilteringBot.pot bot/filtering_bot.py
```

### Create .po files
```
pybabel init -i locales/FilteringBot.pot -d locales -D FilteringBot -l en
pybabel init -i locales/FilteringBot.pot -d locales -D FilteringBot -l ru
```

### Update .po files
```
pybabel update -d locales -D FilteringBot -i locales/FilteringBot.pot
```

### Compile translation
```
pybabel compile -d locales -D FilteringBot
```
