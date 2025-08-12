import streamlit as st
import pandas as pd
import os, sys, subprocess, re
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from collections import Counter
import json

st.set_page_config(page_title="Boca Juniors — Social Listening (X)", layout="wide")
st.title("🟦🟨 Boca Juniors — Social Listening en X (automático)")

# Load config
with open("config.json","r",encoding="utf-8") as f:
    CFG = json.load(f)

def ensure_snscrape():
    try:
        import snscrape.modules.twitter as sntwitter  # type: ignore
    except Exception:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "snscrape==0.7.0.20230622"])
    import snscrape.modules.twitter as sntwitter  # type: ignore
    return sntwitter

@st.cache_data
def run_query(search_query, limit):
    sntwitter = ensure_snscrape()
    tweets = []
    for i, t in enumerate(sntwitter.TwitterSearchScraper(search_query).get_items()):
        if i >= limit:
            break
        tweets.append({
            "id": t.id,
            "date": t.date,
            "username": t.user.username if t.user else None,
            "displayname": t.user.displayname if t.user else None,
            "verified": getattr(t.user, "verified", False) if t.user else None,
            "content": t.rawContent,
            "url": f"https://x.com/{t.user.username}/status/{t.id}" if t.user else None,
            "replyCount": t.replyCount,
            "retweetCount": t.retweetCount,
            "likeCount": t.likeCount,
            "quoteCount": getattr(t, "quoteCount", None),
        })
    return pd.DataFrame(tweets)

def build_since(days):
    return (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")

def glue_queries(terms, lang, days):
    since = build_since(days)
    base = f"lang:{lang} since:{since}"
    # each term runs separately then concatenated
    return [f"{t} {base}" for t in terms]

data_path = "data/tweets.csv"
os.makedirs("data", exist_ok=True)

# Sidebar
with st.sidebar:
    st.header("Parámetros")
    profile = st.selectbox("Perfil", list(CFG["profiles"].keys()), index=0)
    lang = st.selectbox("Idioma", ["es","en"], index=0)
    days_back = st.slider("Días hacia atrás", 1, 30, CFG.get("days_back_default",2))
    limit_per_query = st.slider("Máximo por consulta", 50, 1000, CFG.get("max_results_per_query",400), step=50)
    run_btn = st.button("🔄 Actualizar ahora")
    st.markdown("---")
    st.caption("Consejo: dejá corriendo el workflow diario para mantener el histórico al día.")

# Run search
if run_btn:
    terms = CFG["profiles"][profile]
    queries = glue_queries(terms, lang, days_back)

    all_df = []
    with st.spinner("Buscando publicaciones..."):
        for q in queries:
            dfq = run_query(q, limit_per_query)
            if not dfq.empty:
                dfq["query"] = q
                all_df.append(dfq)
    if all_df:
        df_new = pd.concat(all_df, ignore_index=True).drop_duplicates(subset="id")
        if os.path.exists(data_path):
            df_old = pd.read_csv(data_path, parse_dates=["date"])
        else:
            df_old = pd.DataFrame()
        df_all = pd.concat([df_old, df_new], ignore_index=True).drop_duplicates(subset="id")
        df_all.sort_values("date", ascending=False, inplace=True)
        df_all.to_csv(data_path, index=False, encoding="utf-8")
        st.success(f"Nuevos: {len(df_new)} | Total histórico: {len(df_all)}")
    else:
        st.info("No se encontraron publicaciones nuevas.")

# Load data
if os.path.exists(data_path):
    df = pd.read_csv(data_path, parse_dates=["date"])
else:
    df = pd.DataFrame()

st.subheader("📊 Panel de análisis")
if df.empty:
    st.info("Aún no hay datos. Tocá 'Actualizar ahora' en la izquierda.")
else:
    # Filtros
    col1, col2, col3 = st.columns(3)
    with col1:
        date_from = st.date_input("Desde", value=df["date"].min().date() if not df.empty else None)
    with col2:
        date_to = st.date_input("Hasta", value=df["date"].max().date() if not df.empty else None)
    with col3:
        only_verified = st.checkbox("Solo cuentas verificadas", value=False)

    mask = (df["date"].dt.date >= pd.to_datetime(date_from)) & (df["date"].dt.date <= pd.to_datetime(date_to))
    if only_verified and "verified" in df.columns:
        mask &= df["verified"] == True
    dff = df[mask].copy()

    st.write(f"Publicaciones filtradas: **{len(dff)}**")

    # Serie temporal por día
    dff["day"] = dff["date"].dt.date
    volume = dff.groupby("day").size().reset_index(name="count")
    fig1, ax1 = plt.subplots()
    ax1.plot(volume["day"], volume["count"])
    ax1.set_title("Volumen diario")
    ax1.set_xlabel("Día"); ax1.set_ylabel("Cantidad")
    st.pyplot(fig1)

    # Top autores
    top_users = dff["username"].value_counts().head(20)
    fig2, ax2 = plt.subplots()
    top_users.plot(kind="bar", ax=ax2)
    ax2.set_title("Top 20 usuarios")
    ax2.set_xlabel("Usuario"); ax2.set_ylabel("Publicaciones")
    st.pyplot(fig2)

    # Hashtags y menciones
    def extract(pattern, texts):
        items = []
        for t in texts:
            if isinstance(t, str):
                items += re.findall(pattern, t)
        return items
    hs = extract(r"#(\w+)", dff["content"].tolist())
    ms = extract(r"@(\w+)", dff["content"].tolist())

    if hs:
        hs_cnt = pd.Series(hs).value_counts().head(20)
        fig3, ax3 = plt.subplots()
        hs_cnt.plot(kind="bar", ax=ax3)
        ax3.set_title("Top hashtags"); ax3.set_xlabel("Hashtag"); ax3.set_ylabel("Frecuencia")
        plt.setp(ax3.get_xticklabels(), rotation=45, ha="right")
        st.pyplot(fig3)

    if ms:
        ms_cnt = pd.Series(ms).value_counts().head(20)
        fig4, ax4 = plt.subplots()
        ms_cnt.plot(kind="bar", ax=ax4)
        ax4.set_title("Top menciones"); ax4.set_xlabel("Mención"); ax4.set_ylabel("Frecuencia")
        plt.setp(ax4.get_xticklabels(), rotation=45, ha="right")
        st.pyplot(fig4)

    st.subheader("📄 Publicaciones")
    cols = ["date","username","displayname","verified","content","likeCount","retweetCount","replyCount","url","query"]
    show_cols = [c for c in cols if c in dff.columns]
    st.dataframe(dff[show_cols].reset_index(drop=True))
    st.download_button("⬇️ Descargar CSV filtrado", data=dff[show_cols].to_csv(index=False).encode("utf-8"), file_name="boca_filtrado.csv", mime="text/csv")

st.markdown("---")
st.markdown("Configurable en `config.json` (perfiles, términos, idioma y límites).")