
# Boca Juniors — Social Listening (X)

App **Streamlit** preconfigurada (sin API paga) para rastrear menciones en X sobre dirigentes y temas de Boca Juniors.

## Despliegue rápido (Streamlit Cloud)
1. Subí esta carpeta a un repo en GitHub.
2. En Streamlit Cloud: Deploy app → seleccioná el repo → `app.py`.
3. La app abre con perfiles preconfigurados (Riquelme, Reale, etc.).

## Actualizaciones automáticas (GitHub Actions)
- Incluye un workflow que corre **cada 6 horas** y actualiza `data/tweets.csv` sin abrir la app.
- Configurá 2 Secrets en el repo (Settings → Secrets → Actions):
  - `X_QUERIES_JSON`: JSON con perfiles y términos (si no lo ponés, usa `config.json` del repo).
  - `X_LANG`: idioma (ej. `es`).
- Podés editar `config.json` para cambiar perfiles y términos.

## Local
```bash
pip install -r requirements.txt
streamlit run app.py
```

