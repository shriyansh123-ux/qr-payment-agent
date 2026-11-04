# Web frontend

React 19 + Vite single-page app for the Travel QR Cost Estimator. In production the FastAPI
server serves the built files from `web/dist`, so the app and API share one origin.

```text
npm ci
npm run dev      # http://127.0.0.1:5173, proxies /api to http://127.0.0.1:8000
npm test         # cash arithmetic, money formatting and demo-payload rules
npm run lint
npm run build
```

| Path | Purpose |
| --- | --- |
| `src/App.jsx` | Workspace tabs and the shared in-memory demo key |
| `src/components/QRDemo.jsx` | Text, image and camera QR estimates with in-page history |
| `src/components/AccountPanel.jsx` | Optional sign-in and saved scan summaries |
| `src/components/CurrencyConverter.jsx` | Manual From/To reference conversion |
| `src/components/CashHelper.jsx` | Offline cash payment and change checking |
| `src/lib/api.js` | The only API client; turns FastAPI errors into readable messages |
| `src/lib/money.js` | Currency minor units and money formatting |

Keys and tokens live only in React state. Never put secrets in `VITE_` variables: they are
compiled into the public bundle.
