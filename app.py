@st.cache_data
def run_query(search_query, limit):
    import time
    sntwitter = ensure_snscrape()
    tweets = []
    # reintentos suaves y particionado por días
    chunk_limit = min(200, limit)
    attempts = 0
    while attempts < 3:
        try:
            i = 0
            for t in sntwitter.TwitterSearchScraper(search_query).get_items():
                if i >= chunk_limit:
                    break
                i += 1
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
            break  # salió OK
        except Exception:
            attempts += 1
            time.sleep(4 * attempts)  # backoff progresivo
    return pd.DataFrame(tweets)

st.markdown("Configurable en `config.json` (perfiles, términos, idioma y límites).")
