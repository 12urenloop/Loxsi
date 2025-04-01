# Loxsi

# Setup

Make sure you have docker and docker compose

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

Access at `http://localhost:8080`

## Development

The development container supports hot reloading.

```bash
docker-compose -f docker-compose.dev.yml up
```

## Production

```bash
docker-compose -f docker-compose.yml up --build -d
```
