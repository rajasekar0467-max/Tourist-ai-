import requests
import streamlit as st

# ============================================================

# GNEWS LIVE NEWS SERVICE

# ============================================================

def get_gnews_api_key():

```
try:
    api_key = st.secrets["GNEWS_API_KEY"]

except Exception:

    raise ValueError(
        "GNEWS_API_KEY not found in Streamlit Secrets."
    )

if not api_key:

    raise ValueError(
        "GNEWS_API_KEY is empty."
    )

return api_key
```

# ============================================================

# DETECT NEWS QUERY

# ============================================================

def is_news_query(text: str) -> bool:

```
if not text:
    return False

text = text.lower()

keywords = [

    "news",
    "latest news",
    "breaking news",
    "today news",
    "current news",
    "live news",

    "latest",
    "breaking",
    "today",

    "செய்தி",
    "செய்திகள்",

    "news enna",
    "latest enna",
    "innaiku news",
    "today news enna"
]

return any(
    keyword in text
    for keyword in keywords
)
```

# ============================================================

# FETCH LIVE NEWS

# ============================================================

def get_live_news(
query: str = "",
max_results: int = 5
) -> list:

```
api_key = get_gnews_api_key()

max_results = max(
    1,
    min(int(max_results), 10)
)

base_url = (
    "https://gnews.io/api/v4/"
)

params = {
    "token": api_key,
    "max": max_results,
    "lang": "en"
}

if query and query.strip():

    url = base_url + "search"

    params["q"] = query.strip()

    params["sortby"] = "publishedAt"

else:

    url = base_url + "top-headlines"

    params["country"] = "in"

try:

    response = requests.get(
        url,
        params=params,
        timeout=15
    )

    response.raise_for_status()

    data = response.json()

    articles = data.get(
        "articles",
        []
    )

    results = []

    for article in articles:

        title = article.get(
            "title",
            ""
        )

        description = article.get(
            "description",
            ""
        )

        published_at = article.get(
            "publishedAt",
            ""
        )

        source_data = article.get(
            "source",
            {}
        )

        source_name = ""

        if isinstance(
            source_data,
            dict
        ):

            source_name = source_data.get(
                "name",
                ""
            )

        url_link = article.get(
            "url",
            ""
        )

        if title:

            results.append(
                {
                    "title": title,
                    "description": description,
                    "published_at": published_at,
                    "source": source_name,
                    "url": url_link
                }
            )

    return results

except requests.exceptions.RequestException as error:

    raise RuntimeError(
        f"Live news unavailable: {error}"
    )
```

# ============================================================

# FORMAT NEWS FOR AI

# ============================================================

def format_news_for_ai(
articles: list
) -> str:

```
if not articles:

    return (
        "No live news articles were found."
    )

formatted = []

for index, article in enumerate(
    articles,
    start=1
):

    formatted.append(
        f"""
```

NEWS {index}

Title:
{article.get("title", "")}

Description:
{article.get("description", "")}

Source:
{article.get("source", "")}

Published:
{article.get("published_at", "")}

Link:
{article.get("url", "")}
"""
)

```
return "\n".join(
    formatted
)
```
