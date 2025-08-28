from nicegui import ui

# --- демо-данные ---
compendium_data = [
    {'id': 'Алгоритмы', 'children': [
        {'id': 'Графы', 'children': [{'id': 'Поиск в ширину'}, {'id': 'Поиск в глубину'}]},
        {'id': 'Сортировки', 'children': [{'id': 'Quicksort'}, {'id': 'Mergesort'}]},
    ]},
    {'id': 'Математика', 'children': [{'id': 'Линалг'}, {'id': 'Теория вероятностей'}]},
]

database_data = [
    {'id': 'PostgreSQL', 'children': [
        {'id': 'Схемы', 'children': [{'id': 'public'}, {'id': 'analytics'}]},
        {'id': 'Таблицы', 'children': [{'id': 'users'}, {'id': 'transactions'}]},
    ]},
    {'id': 'ClickHouse', 'children': [{'id': 'events'}, {'id': 'metrics'}]},
]

def fake_llm_answer(text: str) -> str:
    return f'Получил: «{text}». Тут должен отвечать LLM.'

# ====== ВНЕШНИЙ СПЛИТТЕР: ЛЕВО/ПРАВО ======
# value=30 -> при старте 30% / 70%, дальше можно перетаскивать
with ui.splitter(value=30).classes('w-full h-screen') as hsplitter:

    # ----- ЛЕВАЯ ПАНЕЛЬ (две равные половины по высоте) -----
    with hsplitter.before:
        # Внутренний сплиттер "по горизонтали" = делит по высоте (верх/низ)
        with ui.splitter(horizontal=True, value=50).classes('fit') as vsplitter:

            # ВЕРХ: "компендиум"
            with vsplitter.before:
                with ui.card().classes('fit column rounded-none'):
                    ui.label('компендиум').classes('text-weight-medium q-mb-sm')
                    # прокручиваемая область занимает оставшееся место
                    with ui.scroll_area().classes('col'):
                        ui.tree(compendium_data, label_key='id').props('bordered')

            # НИЗ: "база данных"
            with vsplitter.after:
                with ui.card().classes('fit column rounded-none'):
                    ui.label('база данных').classes('text-weight-medium q-mb-sm')
                    with ui.scroll_area().classes('col'):
                        ui.tree(database_data, label_key='id').props('bordered')

    # ----- ПРАВАЯ ПАНЕЛЬ: ЧАТ -----
    with hsplitter.after:
        with ui.card().classes('fit column rounded-none'):
            ui.label('Чат с LLM').classes('text-weight-bold text-subtitle1 q-mb-sm')

            # область сообщений растягивается
            messages_area = ui.scroll_area().classes('col')
            with messages_area:
                ui.chat_message('Привет! Задайте вопрос — я отвечу.', name='LLM', sent=False)

            # панель ввода фиксируется снизу
            with ui.row().classes('q-gutter-sm'):
                user_input = ui.input(placeholder='Введите сообщение...').classes('col')

                def send_message():
                    text = (user_input.value or '').strip()
                    if not text:
                        return
                    with messages_area:
                        ui.chat_message(text, name='Вы', sent=True)
                        ui.chat_message(fake_llm_answer(text), name='LLM', sent=False)
                    user_input.value = ''
                    # автопрокрутка вниз (без кастомного CSS)
                    ui.run_javascript('el.scrollTop = el.scrollHeight;', messages_area)

                ui.button('Отправить', on_click=send_message).props('unelevated')
                user_input.on('keydown.enter', lambda e: send_message())

ui.run(title='Компендиум + База данных + Чат (сплиттер, минимум CSS)')