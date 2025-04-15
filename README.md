# Loxsi

# Setup

Make sure you have docker, docker compose & uv

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

### Active Lap Sources

In the following segment you can configure the current lap source.
When this is changed on the admin panel the config will change accordingly.

```yaml
lap_source:
  id: <telraam lap source id>
  name: <lap source name> # Optional
```

### Active Position Sources

In the following segment you can configure the current position source.
When this is changed on the admin panel the config will change accordingly.

```yaml
position_source:
  id: <telraam position source id>
  name: <position source name> # Optional
```

# Running

Access at `http://localhost:8000`

## Development

The development container supports hot reloading.
Change the Telraam config to the following:

```yaml
telraam:
  api: http://host.docker.internal:8080
  ws: ws://host.docker.internal:8080/ws
```

and start the containers with:

```bash
docker-compose -f docker-compose.dev.yml up
```

or run it locally

```bash
uv venv
source .venv/bin/activate
uv run fastapi dev
```

## Production

```bash
docker-compose -f docker-compose.yml up --build -d
```
