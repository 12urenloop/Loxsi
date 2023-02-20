# Loxsi

# Setup

[Download Poetry](https://python-poetry.org/docs/)

```bash
python3 -m venv venv
. venv/bin/activate
poetry install
```

## Configure

Change the `config.yml` file to your needs.

### Admin panel

To access the admin panel at `/admin` you have to login using basic auth.
With the following yaml segment you can configure the username and password.

```yaml
admin:
  name: <user>
  password: <password>
```

### Active LapSource

In the following segment you can configure the current lap source.
When this is changed on the admin panel the config will change accordingly.

```yaml
source:
  id: <telraam lapsource id>
  name: <lapsource name> # Optional
```

# Running

```bash
uvicorn main:app --host 0.0.0.0
```
