# --- START OF FILE lepra_movie_digger.py ---

import os
import random
import requests
from pathlib import Path
from lepra_logger import log_d


def get_random_movie_from_tmdb() -> str | None:
  """Динамически получает случайное название фильма на русском языке

  через публичный TMDb API. Сначала ищет переменную окружения TMDB_API_KEY,
  при её отсутствии использует встроенный ключ.
  """
  api_key = os.getenv("TMDB_API_KEY", "3аЛ7паИваны4А")
  if not api_key:
    return None

  try:
    # TMDb отдает популярные фильмы страницами (берем случайную страницу от 1 до 40)
    random_page = random.randint(1, 40)
    url = f"https://api.themoviedb.org/3/movie/popular?api_key={api_key}&language=ru-RU&page={random_page}"

    response = requests.get(url, timeout=4)
    if response.status_code == 200:
      data = response.json()
      results = data.get("results", [])
      if results:
        movie = random.choice(results)
        title = movie.get("title")
        if title:
          log_d(f"TMDB: Успешно получен фильм '{title}'")
          return title
    else:
      log_d(
          f"TMDB API ERROR: Статус ответа {response.status_code}, переключаемся"
          " на локальный файл."
      )
  except Exception as e:
    log_d(f"TMDB API EXCEPTION: Ошибка запроса к API: {e}")

  return None


def get_random_movie() -> str:
  """Пытается получить фильм из TMDb API, при неудаче — из movies.txt,

  а при его отсутствии — из встроенного фоллбэк-пула.
  """
  # 1. Пробуем получить через TMDb API
  tmdb_title = get_random_movie_from_tmdb()
  if tmdb_title:
    return tmdb_title

  # 2. Пробуем локальный файл movies.txt (если пользователь его создал)
  movies_path = Path("movies.txt")
  if movies_path.exists():
    try:
      movies = [
          line.strip()
          for line in movies_path.read_text(encoding="utf-8").splitlines()
          if line.strip()
      ]
      if movies:
        return random.choice(movies)
    except Exception as e:
      log_d(f"MOVIES TXT ERROR: Ошибка чтения movies.txt: {e}")

  # 3. Дефолтный пул на случай, если API недоступен и файла нет
  fallback_movies = [
      "Залупа Иваныча",
  ]
  return random.choice(fallback_movies)


# --- END OF FILE lepra_movie_digger.py ---
