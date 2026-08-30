import streamlit as st
import pandas as pd
import json
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import networkx as nx

st.set_page_config(page_title="Lepra Intelligence System", layout="wide", page_icon="🍄")

@st.cache_data(ttl=5)
def load_data():
    if not os.path.exists("lepra_snapshot.json"):
        return None, None, None
    try:
        with open("lepra_snapshot.json", "r", encoding="utf-8") as f:
            snapshot = json.load(f)
        if os.path.exists("leprosorium.db"):
            conn = sqlite3.connect("leprosorium.db")
            df_posts = pd.read_sql_query("SELECT * FROM posts", conn)
            df_comments = pd.read_sql_query("SELECT * FROM comments", conn)
            conn.close()
        else:
            df_posts, df_comments = pd.DataFrame(), pd.DataFrame()
        return snapshot, df_posts, df_comments
    except:
        return None, None, None

def render_personal_graph(selected_user_id, snapshot, users_df, mode):
    km = snapshot.get('karma_matrix', {})
    user_id_to_name = users_df.set_index('id')['username'].to_dict()
    G = nx.Graph()
    G.add_node(selected_user_id, name=user_id_to_name.get(selected_user_id, "ID"), type='center')

    for key, score in km.items():
        v_id, t_id = map(int, key.split(':'))
        if v_id != selected_user_id and t_id != selected_user_id: continue
        rel_id = t_id if v_id == selected_user_id else v_id
        rev_score = km.get(f"{t_id}:{v_id}", 0)
        
        if mode == "Mutual ++" and (score > 0 and rev_score > 0):
            G.add_node(rel_id, name=user_id_to_name.get(rel_id, str(rel_id)))
            G.add_edge(selected_user_id, rel_id, color="#00FF00")
        elif mode == "Mutual --" and (score < 0 and rev_score < 0):
            G.add_node(rel_id, name=user_id_to_name.get(rel_id, str(rel_id)))
            G.add_edge(selected_user_id, rel_id, color="#FF0000")
            
    if not G.edges:
        st.info("Нет связей в данном режиме.")
        return

    pos = nx.spring_layout(G, k=0.5)
    edge_traces = []
    for e in G.edges(data=True):
        x0, y0 = pos[e[0]]; x1, y1 = pos[e[1]]
        edge_traces.append(go.Scatter(x=[x0, x1, None], y=[y0, y1, None], line=dict(width=2, color=e[2]['color']), mode='lines'))

    node_trace = go.Scatter(x=[pos[n][0] for n in G.nodes()], y=[pos[n][1] for n in G.nodes()], mode='markers+text',
                           text=[G.nodes[n]['name'] for n in G.nodes()], textposition="top center", marker=dict(size=12, color="#aaa"))
    
    fig = go.Figure(data=edge_traces + [node_trace], layout=go.Layout(showlegend=False, template="plotly_dark", margin=dict(t=0,b=0,l=0,r=0), xaxis=dict(showgrid=False, zeroline=False, showticklabels=False), yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)))
    st.plotly_chart(fig, use_container_width=True)

def main():
    st.title("🍄 Lepra Intelligence System")
    snapshot, df_posts, df_comments = load_data()
    if not snapshot:
        st.error("Нет данных. Симуляция не запущена.")
        return

    users = pd.DataFrame(snapshot['users'])
    users['karma'] = users['id'].map(lambda x: snapshot['karma_cache'].get(str(x), 0))
    users['rating'] = users['id'].map(lambda x: snapshot['rating_cache'].get(str(x), 0))
    users['special_role'] = users['special_role'].fillna("Обычный")
    user_id_to_name = users.set_index('id')['username'].to_dict()
    
    # МЕТРИКИ
    now = datetime.fromisoformat(snapshot['current_sim_date'])
    
    # Расчет дополнительных показателей
    total_users = len(users)  # Получаем количество строк в DataFrame пользователей
    total_posts = len(df_posts)
    total_comments = len(df_comments)
    ratio = (total_comments / total_posts) if total_posts > 0 else 0
    legendary_count = int(df_posts['is_legendary'].sum()) if not df_posts.empty else 0
    drama_count = int(df_posts['is_drama'].sum()) if not df_posts.empty else 0
    
    # Обновляем отображение: 9 колонок для всех метрик
    m = st.columns(9)
    m[0].metric("Дата", now.strftime("%d.%m.%Y"))
    m[1].metric("Пользователей", total_users) # Передаем переменную сюда
    m[2].metric("Посты", total_posts)
    m[3].metric("Комменты", total_comments)
    m[4].metric("Ratio", f"{ratio:.1f}")
    m[5].metric("Голоса", snapshot['counters'].get('total_votes_ever', 0))
    m[6].metric("Золото", snapshot['counters']['golden_posts_count'])
    m[7].metric("Легенды", legendary_count)
    m[8].metric("Драмы", drama_count)

    tabs = st.tabs(["🗺 Атлас", "🕸 Социум",  "📊 Аналитика", "🗳 Выборы", "📋 Юзеры", "📝 Контент", "🎯 Профиль", "Фейгенбаум"])

    with tabs[0]: # Атлас
        fig_pol = px.scatter(users, x="pol_x", y="pol_y", color="special_role", size=users['karma'].clip(lower=1) + 5,
                             hover_name="username", range_x=[0, 1], range_y=[0, 1], template="plotly_dark",
                             labels={"pol_x": "Диваны (0) ← → Ватаны (1)", "pol_y": "Левачизм ← → Национализм"})
        fig_pol.add_hline(y=0.5, line_dash="dash", line_color="gray"); fig_pol.add_vline(x=0.5, line_dash="dash", line_color="gray")
        st.plotly_chart(fig_pol, use_container_width=True)


    with tabs[1]: # Население
        d1, d2 = st.columns(2)
        with d1:
            st.plotly_chart(px.pie(users, names='skill_type', title="Распределение талантов", template="plotly_dark"), use_container_width=True)
        
        with d2:
            # --- ИЗМЕНЕНИЕ: Дискретизация кармы ---
            # Создаем копию для графиков, чтобы не менять основной DataFrame
            users_plot = users.copy()
            
            # ИЗМЕНЕНО: Шаг теперь равен 1
            step = 1
            # Округляем карму (здесь округление фактически не меняет значения при шаге 1,
            # но оставляем логику для единообразия)
            users_plot['karma_bin'] = (users_plot['karma'] // step) * step
            
            # Формируем подпись (для шага 1 это будет просто значение кармы)
            users_plot['range'] = users_plot['karma_bin'].apply(lambda x: f"{int(x)}")
            
            # Сортируем для правильного отображения на графике
            users_plot = users_plot.sort_values('karma_bin')
            
            fig_hist = px.bar(
                users_plot.groupby('karma_bin').size().reset_index(name='count'),
                x='karma_bin', y='count',
                title="Распределение кармы (шаг 1)",
                template="plotly_dark",
                labels={'karma_bin': 'Карма', 'count': 'Количество юзеров'}
            )
            st.plotly_chart(fig_hist, use_container_width=True)
        
        st.divider()
        st.subheader("🎭 Реестр спец-ролей")
        
        # Фильтруем только тех, у кого роль не "Обычный"
        special_users = users[users['special_role'] != "Обычный"].copy()
        
        if not special_users.empty:
            # Считаем активность для каждого
            post_counts = df_posts.groupby('author_id').size()
            comment_counts = df_comments.groupby('author_id').size()
            
            special_users['Постов'] = special_users['id'].map(lambda x: post_counts.get(x, 0))
            special_users['Комментов'] = special_users['id'].map(lambda x: comment_counts.get(x, 0))
            
            # Формируем итоговую таблицу
            display_df = special_users[[
                'special_role', 'username', 'gender', 'id', 'Постов', 'Комментов'
            ]].rename(columns={
                'special_role': 'Роль',
                'username': 'Ник',
                'gender': 'Пол',
                'id': 'ID'
            })
            
            st.dataframe(display_df.sort_values('Роль'), use_container_width=True, hide_index=True)
        else:
            st.info("В данный момент пользователей со спец-ролями нет.")
            
        st.divider()
        
        # --- НОВАЯ СЕКЦИЯ: СОЦИАЛЬНЫЕ ПОРТРЕТЫ ---
        col_s1, col_s2 = st.columns(2)
        
        with col_s1:
            st.subheader("😇 Радикальные эмпаты")
            # emapthy > 0.85
            empaths = users[users['empathy'] > 0.85][['username', 'empathy', 'karma']].sort_values('empathy', ascending=False)
            st.dataframe(empaths, use_container_width=True, hide_index=True)
            
        with col_s2:
            st.subheader("👺 Радикальные архипиздриты")
            # empathy < 0.15
            cynics = users[users['empathy'] < 0.15][['username', 'empathy', 'karma']].sort_values('empathy', ascending=True)
            st.dataframe(cynics, use_container_width=True, hide_index=True)

        st.subheader("📬 Статистика инбоксов")
        # Распаковка инбоксов для подсчета
        inbox_counts = []
        inbox_names = snapshot.get('inbox_names', [])
        for idx, name in enumerate(inbox_names):
            # Считаем, сколько юзеров имеют этот индекс в своем списке inbox_indices
            count = users['inbox_indices'].apply(lambda x: idx in x).sum()
            inbox_counts.append({"Инбокс": name, "Юзеров": count})
            
        st.dataframe(pd.DataFrame(inbox_counts).sort_values('Юзеров', ascending=False), use_container_width=True, hide_index=True)
        

    with tabs[2]: # Аналитика
        if not df_posts.empty:
            df_posts['author'] = df_posts['author_id'].map(user_id_to_name)
            v1, v2 = st.columns(2)
            with v1: st.plotly_chart(px.bar(df_posts[['plus', 'minus']].sum().reset_index(), x='index', y=0, title="Глобальные плюсы/минусы", template="plotly_dark"), use_container_width=True)
            with v2: st.plotly_chart(px.bar(df_posts.groupby('post_type')['quality'].mean().sort_values(), orientation='h', title="Качество по типам", template="plotly_dark"), use_container_width=True)

    with tabs[3]: # Выборы
        if 'election_history' in snapshot: st.dataframe(pd.DataFrame(snapshot['election_history']), use_container_width=True)

    with tabs[4]: # Реестр юзеров
        # --- ПОДГОТОВКА ДАННЫХ (сделаем один раз для всего DF) ---
        # Заполняем пропуски, чтобы avoid KeyError и ошибок типов
        users_for_table = users.copy()
        users_for_table['is_married'] = users_for_table.get('is_married', False).fillna(False)
        users_for_table['is_banned'] = users_for_table.get('is_banned', False).fillna(False)
        users_for_table['is_burned_out'] = users_for_table.get('is_burned_out', False).fillna(False)
        
        # Обогащаем данные юзеров активностью
        user_stats = []
        for _, u in users_for_table.iterrows():
            u_posts = df_posts[df_posts['author_id'] == u['id']]
            u_comments = df_comments[df_comments['author_id'] == u['id']]
            
            user_stats.append({
                'ID': u['id'],
                'Username': u['username'],
                'Пол': u.get('gender', 'N/A'),
                'Спецроль': u['special_role'],
                'Инвайты': u.get('invites', 0),
                'Карма': u['karma'],
                'Постов': len(u_posts),
                'Комментов': len(u_comments),
                'Золото': len(u_posts[u_posts['is_golden'] == 1]),
                'Легенд': len(u_posts[u_posts['is_legendary'] == 1]),
                'Драм': len(u_posts[u_posts['is_drama'] == 1]),
                # Исправлено: прямое обращение к Series
                'Пара': 'Да' if u['is_married'] else 'Нет',
                'Выгорел': 'Да' if u['is_burned_out'] else 'Нет',
                'Часовой пояс': u.get('tz_offset', 0),
                'Бан': 'Да' if u['is_banned'] else 'Нет'
            })
            
        st.dataframe(pd.DataFrame(user_stats), use_container_width=True, hide_index=True)

    with tabs[5]: # Реестр контента
        st.subheader("📋 Детальный реестр постов")
        if not df_posts.empty:
            posts_view = df_posts.copy()
            posts_view['author'] = posts_view['author_id'].map(user_id_to_name)
            
            # --- ВЫЧИСЛЕНИЯ ---
            # Считаем количество комментов для каждого поста (группировка)
            comment_counts = df_comments.groupby('post_id').size()
            posts_view['Кол-во комментов'] = posts_view['id'].map(lambda pid: comment_counts.get(pid, 0))
            
            # Считаем количество уникальных голосующих (voters - это набор ID, если они в списке)
            # Внимание: если voters в БД — это строка, нужно сначала распарсить.
            # Если это список внутри Python-объекта, используем .len()
            posts_view['Всего голосов'] = posts_view['plus'] + posts_view['minus']

            # Эмодзи-маркировка
            posts_view['Статус'] = posts_view.apply(lambda x:
                ("🌟" if x['is_golden'] else "") +
                ("🏆" if x['is_legendary'] else "") +
                ("🎭" if x['is_drama'] else ""), axis=1)

            # --- ФИЛЬТР ---
            show_deleted = st.checkbox("Показывать удаленные посты", value=False)
            if not show_deleted:
                posts_view = posts_view[posts_view['is_deleted'] == 0]

            # Оставляем важные колонки
            cols = ['id', 'author', 'post_type', 'rating', 'plus', 'minus', 'Всего голосов', 'Кол-во комментов', 'Статус']
            st.dataframe(
                posts_view[cols].sort_values(by='rating', ascending=False),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Постов пока нет.")
        
        st.subheader("💬 Детальный реестр комментариев")
        if not df_comments.empty:
            comments_view = df_comments.copy()
            comments_view['author'] = comments_view['author_id'].map(user_id_to_name)
            # Выбираем самые интересные колонки
            c_cols = ['id', 'post_id', 'author', 'rating', 'text', 'timestamp']
            
            # Сортировка по умолчанию по рейтингу (самые заплюсованные/заминусованные)
            st.dataframe(
                comments_view[c_cols].sort_values(by='rating', ascending=False),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Комментариев пока нет.")
            
    with tabs[6]: # Личный Граф
        if 'current_profile_id' not in st.session_state: st.session_state.current_profile_id = 1
        search_q = st.text_input("Поиск юзера по нику:")
        if search_q:
            matches = users[users['username'].str.contains(search_q, case=False, na=False)]
            if not matches.empty:
                st.session_state.current_profile_id = matches.iloc[0]['id']
        
        curr_id = st.session_state.current_profile_id
        u_row = users[users['id'] == curr_id].iloc[0]
        
        col1, col2 = st.columns([1, 3])
        with col1:
            st.subheader(u_row['username'])
            mode = st.radio("Режим связей:", ["Mutual ++", "Mutual --"])
        with col2:
            render_personal_graph(curr_id, snapshot, users, mode)
            
        st.divider()
        
        # Анализ карма-матрицы для таблиц
        km = snapshot.get('karma_matrix', {})
        
        def get_karma_table(target_score_filter):
            data = []
            for key, score in km.items():
                v_id, t_id = map(int, key.split(':'))
                if v_id == curr_id and (score > 0 if target_score_filter == "plus" else score < 0):
                    target_user = users[users['id'] == t_id]
                    if not target_user.empty:
                        u = target_user.iloc[0]
                        data.append({
                            "Ник": u['username'],
                            "Роль": u['special_role'],
                            "Пол": u.get('gender', 'N/A'),
                            "Карма": snapshot['karma_cache'].get(str(t_id), 0),
                            "Рейтинг": snapshot['rating_cache'].get(str(t_id), 0),
                            "Голос": score
                        })
            return pd.DataFrame(data)

        st.subheader("👍 Кому поставил плюсы")
        plus_df = get_karma_table("plus")
        if not plus_df.empty:
            st.dataframe(plus_df, use_container_width=True, hide_index=True)
        else:
            st.info("Плюсов не обнаружено.")

        st.subheader("👎 Кому поставил минусы")
        minus_df = get_karma_table("minus")
        if not minus_df.empty:
            st.dataframe(minus_df, use_container_width=True, hide_index=True)
        else:
            st.info("Минусов не обнаружено.")
        
        st.divider()
        st.subheader("👤 Карточка пользователя")
        
        # Вспомогательные функции для форматирования
        
        user_posts = df_posts[df_posts['author_id'] == curr_id]
        user_comments = df_comments[df_comments['author_id'] == curr_id]
        
        
        def get_pol_label(x, y):
            x_label = "Либерал" if x < 0.4 else "Автократ" if x > 0.6 else "Умеренный"
            y_label = "Левый" if y < 0.4 else "Националист" if y > 0.6 else "Умеренный"
            return f"{x_label} / {y_label}"

        # Исправление: убедимся, что колонка creator_id существует в DataFrame
        if 'creator_id' not in users.columns:
            users['creator_id'] = None
            
        # Поиск партнера и приглашений
        # Используем .get() для безопасности, если поле отсутствует в словаре u_row
        partner_id = u_row.get('partner_id')
        creator_id = u_row.get('creator_id')
        
        partner_name = user_id_to_name.get(partner_id, "Нет") if partner_id else "Нет"
        inviter_name = user_id_to_name.get(creator_id, "Нет") if creator_id else "Нет"
        
        # Безопасный поиск приглашенных
        invited_by_me = users[users['creator_id'] == curr_id]['username'].tolist() if 'creator_id' in users.columns else []
        invited_str = ", ".join(invited_by_me) if invited_by_me else "Никого"
        inbox_names = snapshot.get('inbox_names', [])
        user_inbox_indices = u_row.get('inbox_indices', [])
        
        
        
        if inbox_names:
            user_inboxes_str = ", ".join([inbox_names[idx] for idx in user_inbox_indices if idx < len(inbox_names)])
        else:
            user_inboxes_str = ", ".join([str(idx) for idx in user_inbox_indices])

        # Оформление карточки

        with st.container(border=True):
            c1, c2, c3 = st.columns(3)
            
            with c1:
                st.write(f"**Ник:** {u_row['username']}")
                st.write(f"**ID:** {u_row['id']}")
                st.write(f"**Инбоксы:** {user_inboxes_str}") # <--- ДОБАВЛЕНО
                st.write(f"**Пол:** {u_row.get('gender', 'N/A')}")
                st.write(f"**Дата рег:** {u_row.get('reg_date', 'N/A')}")
                st.write(f"**Карма:** {u_row['karma']}")
                st.write(f"**Рейтинг:** {u_row['rating']}")
                st.write(f"**Тип таланта:** {u_row.get('skill_type', 'N/A')}")
            
            with c2:
                st.write(f"**Атлас:** {get_pol_label(u_row['pol_x'], u_row['pol_y'])}")
                st.write(f"**Реактивность:** {u_row.get('reactivity', 0):.2f}")
                st.write(f"**Креативность:** {u_row.get('creativity', 0):.2f}")
                st.write(f"**Озлобленность:** {u_row.get('bitterness', 0):.2f}")
                st.write(f"**Эмпатия:** {u_row.get('empathy', 0):.2f}")
                st.write(f"**Спецроль:** {u_row['special_role']}")
                st.write(f"**Шахтер:** {'Да' if u_row.get('is_miner') else 'Нет'}")
                st.write(f"**Всего постов:** {len(user_posts)}") # Добавлено
                st.write(f"**Всего комментов:** {len(user_comments)}")
            
            with c3:
                st.write(f"**Пара:** {partner_name}")
                st.write(f"**Шалун:** {'Да' if u_row.get('is_promiscuous') else 'Нет'}")
                st.write(f"**Срок жизни пары:** {u_row.get('pair_expiry', 'N/A')}")
                st.write(f"**Выгорел:** {'Да' if u_row.get('is_burned_out') else 'Нет'}")
                st.write(f"**Burnout threshold:** {u_row.get('burnout_threshold', 0):.0f}")
                st.write(f"**Инвайтов:** {u_row.get('invites', 0)}")
                st.write(f"**Пригласил:** {invited_str}")
                st.write(f"**Приглашен:** {inviter_name}")
                st.write(f"**Мерячение:** {'Да' if u_row.get('merjachenie_triggered') else 'Нет'}")
                st.write(f"**Забанен:** {'Да' if u_row.get('is_banned') else 'Нет'}")
                
            st.subheader("📜 Посты пользователя")
            if not user_posts.empty:
                p_view = user_posts.copy()
                # Создаем колонку с эмодзи
                p_view['Статус'] = p_view.apply(lambda x:
                    ("🌟" if x['is_golden'] else "") +
                    ("🏆" if x['is_legendary'] else "") +
                    ("🎭" if x['is_drama'] else ""), axis=1)
                
                # Считаем количество комментов в каждом посте
                p_view['Кол-во комментов'] = p_view['id'].map(lambda pid: df_comments[df_comments['post_id'] == pid].shape[0])
                
                p_cols = ['id', 'post_type', 'rating', 'plus', 'minus', 'Статус', 'Кол-во комментов']
                st.dataframe(p_view[p_cols].sort_values('rating', ascending=False), use_container_width=True, hide_index=True)
            else:
                st.info("Пользователь еще не создал ни одного поста.")

            # --- ТАБЛИЦА КОММЕНТАРИЕВ ЮЗЕРА ---
            st.subheader("💬 Комментарии пользователя")
            if not user_comments.empty:
                c_view = user_comments.copy()
                c_cols = ['post_id', 'rating', 'text', 'timestamp']
                st.dataframe(c_view[c_cols].sort_values('rating', ascending=False), use_container_width=True, hide_index=True)
            else:
                st.info("Пользователь еще не оставил ни одного комментария.")
                
    with tabs[7]: # Фейгенбаум
        st.subheader("📉 Система на краю хаоса")
        
        # Подготовка данных
        posts_ts = df_posts.copy()
        posts_ts['timestamp'] = pd.to_datetime(posts_ts['timestamp'])
        posts_ts['date'] = posts_ts['timestamp'].dt.date
        
        comments_ts = df_comments.copy()
        comments_ts['timestamp'] = pd.to_datetime(comments_ts['timestamp'])
        comments_ts['date'] = comments_ts['timestamp'].dt.date
        
        # Общие графики интенсивности
        c1, c2 = st.columns(2)
        with c1:
            st.write("### Интенсивность постов")
            st.line_chart(posts_ts.groupby('date').size())
        with c2:
            st.write("### Интенсивность комментариев")
            st.line_chart(comments_ts.groupby('date').size())
            
        st.divider()
        st.subheader("💀 Карательные меры и деструкция")
        
        # 1. Репакуку (удаленные посты типа "бред")
        repakuku = posts_ts[(posts_ts['is_deleted'] == 1) & (posts_ts['post_type'] == 'бред')]
        st.write("#### 1. Количество Репакуку (самоубийства)")
        if not repakuku.empty:
            st.line_chart(repakuku.groupby('date').size())
        else:
            st.info("Репакуку еще не было.")
            
        # 2. Удаленные посты (Модерация / ИМПИЧМЕНТ)
        # Исключаем репакуку, чтобы не дублировать
        deleted_posts = posts_ts[(posts_ts['is_deleted'] == 1) & (posts_ts['post_type'] != 'бред')]
        st.write("#### 2. Количество удаленных постов (Модерация)")
        if not deleted_posts.empty:
            st.line_chart(deleted_posts.groupby('date').size())
        else:
            st.info("Посты не удалялись.")
            
        # 3. Слитые (забаненные юзеры)
        # Поскольку у нас в snapshot нет даты бана, показываем текущее состояние
        banned_users = users[users['is_banned'] == True]
        st.write("#### 3. Статистика слитых (текущее состояние)")
        col_m1, col_m2 = st.columns(2)
        col_m1.metric("Всего забанено", len(banned_users))
        col_m2.metric("Уровень токсичности (биттерность)", f"{users['bitterness'].mean():.3f}")
        
        if not banned_users.empty:
            st.info(f"В системе забанено {len(banned_users)} пользователей.")
        else:
            st.success("Все пользователи чисты.")

if __name__ == "__main__":
    main()
