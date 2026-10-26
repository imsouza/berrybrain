---
id: sciref-database-lookup-openweathermap
name: "Scientific Ref: OpenWeatherMap API Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (database-lookup): OpenWeatherMap API Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "database lookup openweathermap"
  - "openweathermap api reference"
keywords:
  - "database"
  - "lookup"
  - "openweathermap"
  - "specialized"
  - "scientific"
  - "reference"
---

# OpenWeatherMap API Reference

## Base URL
```
https://api.openweathermap.org
```

## Authentication
- **API Key: REQUIRED.** Register for a free key at https://home.openweathermap.org/users/sign_up
- Pass as query parameter: `&appid=YOUR_KEY`
- Free tier key activates within a few hours of registration.

## Rate Limits (Free Tier)
- Quotas depend on product and subscription; check the account and [pricing page](https://openweathermap.org/price) before a batch.
- **Current weather, 5-day forecast, geocoding:** Available on free tier.
- **One Call 3.0:** Requires subscription (1,000 free calls/day with credit card on file).
- **Air pollution history** is documented from 2020-11-27; weather-history subscriptions are a separate product. Do not assume all history routes have the same entitlement.

---

## Key Endpoints

### 1. Current Weather
```
GET /data/2.5/weather
```

**Parameters:**
| Parameter | Type   | Required | Default  | Description |
|-----------|--------|----------|----------|-------------|
| `q`       | string | Cond.    | -        | City name, optionally with state/country: `London`, `London,GB`, `Portland,OR,US`. |
| `lat`     | float  | Cond.    | -        | Latitude (use with `lon`). |
| `lon`     | float  | Cond.    | -        | Longitude (use with `lat`). |
| `id`      | int    | Cond.    | -        | City ID (from OWM city list). |
| `zip`     | string | Cond.    | -        | Zip/postal code with country: `90210,US`, `SW1,GB`. |
| `units`   | string | No       | `standard` | `standard` (Kelvin), `metric` (Celsius), `imperial` (Fahrenheit). |
| `lang`    | string | No       | `en`     | Language code for descriptions. |
| `appid`   | string | Yes      | -        | API key. |

Use `lat`+`lon`. Built-in city-name, city-ID and ZIP geocoding (`q`, `id`, `zip`) is deprecated although still available; resolve locations through `/geo/1.0/` for maintained integrations.

**Example:**
```
https://api.openweathermap.org/data/2.5/weather?lat=40.7128&lon=-74.0060&units=metric&appid=YOUR_KEY
```

**Response:**
```json
{
  "coord": {"lon": -74.006, "lat": 40.7128},
  "weather": [
    {
      "id": 800,
      "main": "Clear",
      "description": "clear sky",
      "icon": "01d"
    }
  ],
  "base": "stations",
  "main": {
    "temp": 22.5,
    "feels_like": 21.8,
    "temp_min": 20.1,
    "temp_max": 24.3,
    "pressure": 1013,
    "humidity": 55,
    "sea_level": 1013,
    "grnd_level": 1010
  },
  "visibility": 10000,
  "wind": {"speed": 3.6, "deg": 220, "gust": 5.1},
  "clouds": {"all": 0},
  "dt": 1700000000,
  "sys": {
    "country": "US",
    "sunrise": 1699960000,
    "sunset": 1699996000
  },
  "timezone": -18000,
  "id": 5128581,
  "name": "New York",
  "cod": 200
}
```

### 2. 5-Day / 3-Hour Forecast (Free)
```
GET /data/2.5/forecast
```
Returns forecast data in 3-hour intervals for 5 days (40 data points). Same location parameters as current weather.

**Additional Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `cnt`     | int  | Number of 3-hour steps to return (max 40). |

**Example:**
```
https://api.openweathermap.org/data/2.5/forecast?lat=51.5085&lon=-0.1257&units=metric&cnt=8&appid=YOUR_KEY
```

**Response:**
```json
{
  "cod": "200",
  "message": 0,
  "cnt": 8,
  "list": [
    {
      "dt": 1700000000,
      "main": {
        "temp": 10.5,
        "feels_like": 8.2,
        "temp_min": 9.8,
        "temp_max": 10.5,
        "pressure": 1020,
        "humidity": 80
      },
      "weather": [{"id": 802, "main": "Clouds", "description": "scattered clouds", "icon": "03d"}],
      "clouds": {"all": 40},
      "wind": {"speed": 4.1, "deg": 250},
      "visibility": 10000,
      "pop": 0.2,
      "dt_txt": "2024-01-15 12:00:00"
    }
  ],
  "city": {
    "id": 2643743,
    "name": "London",
    "coord": {"lat": 51.5085, "lon": -0.1257},
    "country": "GB",
    "population": 1000000,
    "timezone": 0,
    "sunrise": 1699950000,
    "sunset": 1699982000
  }
}
```
`pop` is probability of precipitation (0.0 to 1.0).

### 3. Geocoding
```
GET /geo/1.0/direct
GET /geo/1.0/reverse
GET /geo/1.0/zip
```

**Direct geocoding (city name to coordinates):**
```
https://api.openweathermap.org/geo/1.0/direct?q=London,GB&limit=5&appid=YOUR_KEY
```
Returns array of `{name, lat, lon, country, state}`.

**Reverse geocoding (coordinates to city name):**
```
https://api.openweathermap.org/geo/1.0/reverse?lat=51.5085&lon=-0.1257&limit=1&appid=YOUR_KEY
```

**Zip code geocoding:**
```
https://api.openweathermap.org/geo/1.0/zip?zip=90210,US&appid=YOUR_KEY
```

### 4. One Call API 3.0 (Subscription Required)
```
GET /data/3.0/onecall
```
Comprehensive endpoint returning current, minutely (1h), hourly (48h), daily (8d), and alerts in one call.

**Parameters:**
| Parameter | Type   | Required | Description |
|-----------|--------|----------|-------------|
| `lat`     | float  | Yes      | Latitude. |
| `lon`     | float  | Yes      | Longitude. |
| `exclude` | string | No       | Comma-separated parts to exclude: `current`, `minutely`, `hourly`, `daily`, `alerts`. |
| `units`   | string | No       | `standard`, `metric`, `imperial`. |
| `appid`   | string | Yes      | API key. |

**Example:**
```
https://api.openweathermap.org/data/3.0/onecall?lat=40.7128&lon=-74.006&exclude=minutely,alerts&units=metric&appid=YOUR_KEY
```

### 5. One Call API 4.0 (separate subscription)

The current [One Call 4.0 documentation](https://openweathermap.org/api/one-call-4) describes a separate endpoint family; the 3.0 route above remains separately documented. Do not change only the version in a 3.0 URL.

```text
GET /data/4.0/onecall/current?lat={lat}&lon={lon}&appid={key}
GET /data/4.0/onecall/timeline/1h?lat={lat}&lon={lon}&appid={key}
GET /data/4.0/onecall/timeline/1day?lat={lat}&lon={lon}&appid={key}
```

Responses contain location/timezone fields and a `data` array. Timeline responses can include `next`/`prev` URLs; follow those URLs rather than constructing offsets. Each page is a billed API call under the selected plan. The One Call by Call plan includes 1,000 calls/day free, while the initial account cap is 2,000 calls/day; those are different thresholds. Check the configured limit before running a batch. Examples here are documentation-verified, not authenticated live tests.

### 6. Air Pollution
```
GET /data/2.5/air_pollution
GET /data/2.5/air_pollution/forecast
GET /data/2.5/air_pollution/history
```

**Parameters:** `lat`, `lon`, `appid` (required). For his

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

