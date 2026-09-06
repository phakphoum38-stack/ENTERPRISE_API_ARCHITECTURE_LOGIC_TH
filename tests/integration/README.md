# PostgreSQL Integration Gate

Run a disposable PostgreSQL instance:

```bash
docker compose -f docker-compose.postgres-test.yml up -d --wait
```

Install the test dependency:

```bash
python -m pip install 'psycopg[binary]' pytest
```

Run the gate:

```bash
TEST_POSTGRES_DSN='postgresql://workflow:workflow@localhost:54329/workflow' \
  pytest -q tests/integration/test_postgres_fencing.py
```

The test proves:

1. first reservation receives fencing token `1`;
2. an unexpired active assignment blocks a competing reservation;
3. an expired lease can be reclaimed;
4. reclaim advances the fencing token to `2`;
5. the stale token cannot complete the assignment;
6. the current token can complete it.

A skipped test means the live PostgreSQL service was unavailable; it must not be treated as a production gate pass.
