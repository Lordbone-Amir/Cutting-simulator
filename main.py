from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.slider import Slider
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.graphics import Color, Line
from kivy.properties import ListProperty, NumericProperty
from kivy.core.window import Window
from kivy.graphics import Ellipse
from kivy.graphics import StencilPush, StencilUse, StencilPop, Rectangle
from const import *
from kivy.properties import ListProperty, NumericProperty, BooleanProperty

# Импорт ваших классов из geometry.py
from geometry import Polygon, Point, Polyline, is_true_divide
from kivy.clock import Clock
from kivy.graphics import Color, Line, Ellipse, Rectangle, StencilPush, StencilUse, StencilPop
from kivy.properties import ListProperty
import threading

class DrawingArea(Widget):
    vertices = ListProperty([])
    first_ans = ListProperty([])
    second_ans = ListProperty([])
    show_answer = BooleanProperty(False)
    _updating = False


    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Привязываем все изменения к отложенному обновлению
        self.bind(pos=self.schedule_update, size=self.schedule_update, vertices=self.schedule_update)
        # Инициализируем атрибуты для преобразования
        self.scale = 1.0
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.min_x = 0
        self.max_x = 30
        self.min_y = 0
        self.max_y = 30
        self.is_generating = False
        self.poly = Polygon()
        self.line = Polyline()
        self.count_of_line = 0
        self.line_color = COLOR_CUT_LINE

    def schedule_update(self, *args):
        Clock.unschedule(self.update_canvas)
        Clock.schedule_once(self.update_canvas, 0)

    def update_canvas(self, *args):
        if self._updating or self.width <= 1 or self.height <= 1:
            return
        self._updating = True
        try:
            self._do_update_canvas()
        finally:
            self._updating = False

    def _do_update_canvas(self):
            
        draw_vertices = self.poly.arr if self.poly and self.poly.size() else self.vertices
        if not draw_vertices:
            min_x, max_x = 0, 30
            min_y, max_y = 0, 30
        else:
            xs = [p.x for p in draw_vertices]
            ys = [p.y for p in draw_vertices]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)

        # Расширяем диапазон на 1 клетку влево и вниз
        min_x = int(min_x) - 1
        max_x = int(max_x) + 1
        min_y = int(min_y) - 1
        max_y = int(max_y) + 1

        # Сохраняем для преобразования
        self.min_x = min_x
        self.max_x = max_x
        self.min_y = min_y
        self.max_y = max_y

        # Далее все вычисления как раньше, но с обновлёнными min/max
        range_x = max_x - min_x or 1
        range_y = max_y - min_y or 1
        margin = 0.15 * min(self.width, self.height)  # чуть больше отступ
        self.scale = min((self.width - 2 * margin) / range_x,
                    (self.height - 2 * margin) / range_y)
        self.offset_x = (self.width - range_x * self.scale) / 2 - min_x * self.scale
        self.offset_y = (self.height - range_y * self.scale) / 2 - min_y * self.scale
        
        print("\n=== CANVAS UPDATE ===")
        print(f"widget size: {self.width} x {self.height}")
        print(f"grid bounds: x=[{min_x}, {max_x}], y=[{min_y}, {max_y}]")
        print(f"range: {range_x} x {range_y}, margin: {margin:.2f}")
        print(f"scale: {self.scale:.2f} px/unit")
        print(f"offset: ({self.offset_x:.2f}, {self.offset_y:.2f})")
        print("====================\n")

        self.canvas.clear()
        with self.canvas:
            # Обрезаем рисование по границам виджета
            StencilPush()
            Rectangle(pos=self.pos, size=self.size)
            StencilUse()

            # Сетка
            Color(*COLOR_GRID)
            for x in range(min_x, max_x + 1):
                screen_x = self.x + self.offset_x + x * self.scale
                Line(points=[screen_x, self.y + self.offset_y + min_y * self.scale,
                             screen_x, self.y + self.offset_y + max_y * self.scale],
                     width=0.5)
            for y in range(min_y, max_y + 1):
                screen_y = self.y + self.offset_y + y * self.scale
                Line(points=[self.x + self.offset_x + min_x * self.scale, screen_y,
                             self.x + self.offset_x + max_x * self.scale, screen_y],
                     width=0.5)

            # Рёбра и вершины многоугольника - рисуются ВСЕГДА
            if draw_vertices and len(draw_vertices) >= 3:
                points = []
                for p in draw_vertices:
                    px = self.x + self.offset_x + p.x * self.scale
                    py = self.y + self.offset_y + p.y * self.scale
                    points.extend([px, py])

                Color(*COLOR_EDGE)
                Line(points=points + points[:2], width=2, close=True)

                Color(*COLOR_VERTEX)
                r = 5
                print("Drawing vertices:")
                for p in draw_vertices:
                    px = self.x + self.offset_x + p.x * self.scale
                    py = self.y + self.offset_y + p.y * self.scale
                    print(f"  grid({p.x}, {p.y}) -> screen({px:.1f}, {py:.1f})")
                    Ellipse(pos=(px - r, py - r), size=(2 * r, 2 * r))
            
            # Показываем ответные полигоны если включено
            if self.show_answer:
                Color(*COLOR_ANS)
                for ans_vertices in (self.first_ans, self.second_ans):
                    if ans_vertices and len(ans_vertices) >= 2:
                        points = []
                        for p in ans_vertices:
                            px = self.x + self.offset_x + p.x * self.scale
                            py = self.y + self.offset_y + p.y * self.scale
                            points.extend([px, py])
                        Line(points=points + points[:2], width=2, close=True) 
            
            # Рисуем ломаную если она есть (минимум 2 точки для линии)
            if self.line.size() >= 2:
                Color(*self.line_color)
                points = []
                for p in self.line.arr:
                    px = self.x + self.offset_x + p.x * self.scale
                    py = self.y + self.offset_y + p.y * self.scale
                    points.extend([px, py])
                Line(points=points, width=2)
            
            # Рисуем точки ломаной (даже если только 1)
            if self.line.size() >= 1 and not self.show_answer:
                Color(*self.line_color)
                for p in self.line.arr:
                    px = self.x + self.offset_x + p.x * self.scale
                    py = self.y + self.offset_y + p.y * self.scale
                    Ellipse(pos=(px - 5, py - 5), size=(10, 10))
            
            StencilPop()

    def pixel_to_coord(self, px, py):
        """Преобразует пиксельные координаты (относительно виджета) в координаты сетки."""
        x = (px - self.offset_x) / self.scale
        y = (py - self.offset_y) / self.scale
        return x, y

    def clear_line(self):
        """Очищает линию и сбрасывает цвет."""
        self.line.clear()
        self.line_color = COLOR_CUT_LINE
        self.schedule_update()
        print("Line cleared after error timeout")

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            
            # Преобразуем абсолютные координаты окна в локальные координаты виджета
            # Не используем to_local() из-за несоответствий - делаем вручную
            local_x = touch.pos[0] - self.x
            local_y = touch.pos[1] - self.y
            # Преобразуем в координаты сетки
            grid_x, grid_y = self.pixel_to_coord(local_x, local_y)
            
            print("\n=== DEBUG TOUCH ===")
            print(f"touch.pos (absolute in window): {touch.pos}")
            print(f"self.pos (widget position): {self.pos}")
            print(f"local (widget coords): ({local_x:.2f}, {local_y:.2f})")
            print(f"offset: ({self.offset_x:.2f}, {self.offset_y:.2f})")
            print(f"scale: {self.scale:.2f}")
            print(f"min/max: x=[{self.min_x}, {self.max_x}], y=[{self.min_y}, {self.max_y}]")
            print(f"grid (before round): ({grid_x:.2f}, {grid_y:.2f})")
            
            # Округляем до ближайшего целого для совместимости с vertices
            grid_x = round(grid_x)
            grid_y = round(grid_y)
            print(f"grid (after round): ({grid_x}, {grid_y})")
            print(f"Polygon vertices: {self.poly.arr}")
            print("===================\n")
            
            if self.poly.size() == 0:
                print("polygon is empty, doing nothing")
                return True
            
            # Для первой точки: проверяем, что она на ребре
            if self.line.size() == 0:
                on_edge = self.poly.fined_pos(Point(grid_x, grid_y))
                if on_edge == -1:
                    print(f"First point ({grid_x}, {grid_y}) is not on edge, rejecting")
                    self.schedule_update()
                    return True
                
                self.line.append(Point(grid_x, grid_y))
                self.line_color = COLOR_CUT_LINE
                print(f"First point added: ({grid_x}, {grid_y}) on edge {on_edge}")
            else:
                # Для второй и последующих точек: добавляем и проверяем
                self.line.append(Point(grid_x, grid_y))
                print(f"Point added: ({grid_x}, {grid_y})")
                if self.poly.draw_line(self.line):
                    print(f"Line is valid with new point ({grid_x}, {grid_y})")
                else:
                    print(f"Line is NOT valid with new point ({grid_x}, {grid_y}), removing last point")
                    self.line.arr.pop()  # удаляем последнюю точку
                
                # Если это точка на границе то проверям делит ли она многоугольник на 2 части
                if self.poly.fined_pos(Point(grid_x, grid_y)) != -1:
                    print("Checking if line divides polygon correctly...")
                    if is_true_divide(self.poly, self.line):
                        self.line_color = COLOR_SUCCESS
                        print("✓ Line correctly divides polygon into 2 equal parts!")
                    else:
                        self.line_color = COLOR_ERROR
                        print("✗ Line does NOT divide polygon correctly - will clear in 1 second")
                        # Запланируем очистку линии через 1 секунду
                        Clock.schedule_once(lambda dt: self.clear_line(), 1.0)
            
            print("Current line points:")
            print(self.line.arr)
            
            # Перерисовываем канвас с новой точкой ломаной
            self.schedule_update()
            return True
        return super().on_touch_down(touch)


class GameScreen(Screen):
    complexity = NumericProperty(5)
    _generating = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.loaded_level = None
        layout = BoxLayout(orientation='vertical', padding=5, spacing=5)

        top_bar = BoxLayout(orientation='horizontal', size_hint=(1, None), height=30)
        self.info_label = Label(text='Сложность: 5', size_hint=(1, 1), color=(0.5, 0.5, 0.5, 1))
        top_bar.add_widget(self.info_label)
        layout.add_widget(top_bar)

        self.drawing_area = DrawingArea()
        layout.add_widget(self.drawing_area)

        bottom_bar = BoxLayout(orientation='vertical', size_hint=(1, None), height=180)
        self.new_btn = Button(text='Новая генерация')
        self.new_btn.bind(on_press=self.regenerate_polygon)
        self.answer_btn = Button(text='Показать ответ')
        self.answer_btn.bind(on_press=self.toggle_answer)
        self.clear_btn = Button(text='Сброс линии')
        self.clear_btn.bind(on_press=self.clear_line)
        self.save_btn = Button(text='Сохранить уровень')
        self.save_btn.bind(on_press=self.save_level)
        self.menu_btn = Button(text='Меню')
        self.menu_btn.bind(on_press=self.go_to_menu)

        bottom_bar.add_widget(self.new_btn)
        bottom_bar.add_widget(self.answer_btn)
        bottom_bar.add_widget(self.clear_btn)
        bottom_bar.add_widget(self.save_btn)
        bottom_bar.add_widget(self.menu_btn)
        layout.add_widget(bottom_bar)

        self.add_widget(layout)

        self.first_ans = []
        self.second_ans = []
        self.show_answer = False

    def on_enter(self, *args):
        if self.loaded_level:
            self.load_selected_level()
            self.loaded_level = None
            return
        if self._generating:
            return
        self._generating = True
        self.new_btn.disabled = True
        self.info_label.text = 'Генерация'
        self._start_loading_animation()
        # Run generation in a separate thread
        threading.Thread(target=self._generate_polygon, daemon=True).start()

    def _generate_polygon(self):
        try:
            polygon = Polygon()
            poly, first_ans, second_ans = polygon.generate(int(self.complexity))
            vertices = list(poly.arr)
            first_ans = first_ans.arr
            second_ans = second_ans.arr
            # Schedule UI update on main thread
            Clock.schedule_once(lambda dt: self._update_ui(poly, vertices, first_ans, second_ans), 0)
        except Exception as e:
            Clock.schedule_once(lambda dt: self._handle_error(e), 0)

    def _update_ui(self, poly, vertices, first_ans, second_ans):
        self._stop_loading_animation()
        self.drawing_area.poly = poly
        self.drawing_area.vertices = vertices
        self.drawing_area.line.clear()
        self.drawing_area.count_of_line = 0
        self.drawing_area.line_color = COLOR_CUT_LINE
        self.first_ans = first_ans
        self.second_ans = second_ans
        self.drawing_area.first_ans = first_ans
        self.drawing_area.second_ans = second_ans
        self.show_answer = False
        self.drawing_area.show_answer = False
        self.answer_btn.text = 'Показать ответ'
        self.info_label.text = f'Сложность: {int(self.complexity)}'
        self.drawing_area.update_canvas()
        self._generating = False
        self.new_btn.disabled = False

    def _handle_error(self, e):
        self._stop_loading_animation()
        self.info_label.text = f'Ошибка: {e}'
        self._generating = False
        self.new_btn.disabled = False

    def load_selected_level(self):
        level = self.loaded_level
        poly = Polygon(level['poly'])
        first_ans = level['first']
        second_ans = level['second']
        self.drawing_area.poly = poly
        self.drawing_area.vertices = list(poly.arr)
        self.drawing_area.schedule_update()
        self.drawing_area.line.clear()
        self.drawing_area.count_of_line = 0
        self.drawing_area.line_color = COLOR_CUT_LINE
        self.first_ans = first_ans
        self.second_ans = second_ans
        self.drawing_area.first_ans = first_ans
        self.drawing_area.second_ans = second_ans
        self.show_answer = False
        self.drawing_area.show_answer = False
        self.answer_btn.text = 'Показать ответ'
        self.info_label.text = f'Загружен уровень (n={level["n"]}, m={level["m"]})'
        self._generating = False
        self.new_btn.disabled = False

    def toggle_answer(self, instance):
        print("Кнопка 'Показать ответ' нажата")
        self.show_answer = not self.show_answer
        self.drawing_area.show_answer = self.show_answer
        self.answer_btn.text = 'Скрыть ответ' if self.show_answer else 'Показать ответ'
        self.drawing_area.update_canvas()

    def clear_line(self, instance):
        print("Кнопка 'Сброс линии' нажата")
        self.drawing_area.clear_line()

    def save_level(self, instance):
        print("Кнопка 'Сохранить уровень' нажата")
        if not hasattr(self, 'drawing_area') or not self.drawing_area.poly:
            print("Нет полигона для сохранения")
            return
        poly = self.drawing_area.poly
        first = self.first_ans
        second = self.second_ans
        if not first or not second:
            print("Нет ответа для сохранения")
            return
        n = len(poly.arr)
        m = len(first)
        if len(second) != m:
            print("Разные размеры ответов")
            return
        # Загрузить существующие уровни
        levels = self.load_levels()
        # Добавить текущий уровень
        current = {'n': n, 'm': m, 'poly': poly.arr, 'first': first, 'second': second}
        levels.append(current)
        # Перезаписать файл
        try:
            with open('save.txt', 'w') as f:
                f.seek(0)
                f.write(f"{len(levels)}\n")
                for level in levels:
                    f.write(f"{level['n']} {level['m']}\n")
                    for p in level['poly']:
                        f.write(f"{int(p.x)} {int(p.y)}\n")
                    for p in level['first']:
                        f.write(f"{int(p.x)} {int(p.y)}\n")
                    for p in level['second']:
                        f.write(f"{int(p.x)} {int(p.y)}\n")
            print(f"Уровень сохранен. Всего уровней: {len(levels)}")
            
        except Exception as e:
            print(f"Ошибка сохранения: {e}")
        finally:
            f.close()

    def load_levels(self):
        try:
            with open('save.txt', 'r') as f:
                lines = f.readlines()
            if not lines:
                return []
            first_line = lines[0].strip().split()
            if len(first_line) == 1:
                # Новый формат: k уровней
                k = int(first_line[0])
                idx = 1
            else:
                # Старый формат: один уровень без k
                k = 1
                idx = 0
            levels = []
            for _ in range(k):
                n, m = map(int, lines[idx].split())
                idx += 1
                poly = []
                for _ in range(n):
                    x, y = map(int, lines[idx].split())
                    poly.append(Point(x, y))
                    idx += 1
                first = []
                for _ in range(m):
                    x, y = map(int, lines[idx].split())
                    first.append(Point(x, y))
                    idx += 1
                second = []
                for _ in range(m):
                    x, y = map(int, lines[idx].split())
                    second.append(Point(x, y))
                    idx += 1
                levels.append({'n': n, 'm': m, 'poly': poly, 'first': first, 'second': second})
            return levels
        except Exception as e:
            print(f"Ошибка загрузки уровней: {e}")
            return []

    def regenerate_polygon(self, instance):
        if self._generating:
            return
        self._generating = True
        self.new_btn.disabled = True
        self.info_label.text = 'Генерация'
        self._start_loading_animation()
        # Run generation in a separate thread
        threading.Thread(target=self._generate_polygon, daemon=True).start()

    def _start_loading_animation(self):
        self._loading_dots = 0
        self._loading_event = Clock.schedule_interval(self._update_loading_text, 0.5)

    def _update_loading_text(self, dt):
        self._loading_dots = (self._loading_dots + 1) % 4
        dots = '.' * self._loading_dots
        self.info_label.text = f'Генерация{dots}'

    def _stop_loading_animation(self):
        if hasattr(self, '_loading_event'):
            self._loading_event.cancel()

    def go_to_menu(self, instance):
        print("Кнопка 'Меню' нажата")
        self.manager.current = 'menu'
    

class MainMenu(Screen):
    """Главное меню с выбором сложности."""
    complexity = NumericProperty(3)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=20)

        layout.add_widget(Label(text='Разрежь многоугольник пополам',
                                font_size='28sp', size_hint=(1, 0.15), color=(0.5, 0.5, 0.5, 1)))

        complexity_box = BoxLayout(orientation='horizontal', size_hint=(1, 0.1))
        complexity_box.add_widget(Label(text='Сложность:', size_hint=(0.3, 1), color=(0.5, 0.5, 0.5, 1)))

        self.complexity_label = Label(text=str(self.complexity), size_hint=(0.1, 1), color=(0.5, 0.5, 0.5, 1))
        complexity_box.add_widget(self.complexity_label)

        self.slider = Slider(min=2, max=6, value=self.complexity, step=1, size_hint=(0.6, 1))
        self.slider.bind(value=self.on_complexity_changed)
        complexity_box.add_widget(self.slider)
        layout.add_widget(complexity_box)

        play_btn = Button(text='Играть', size_hint=(1, 0.15))
        play_btn.bind(on_press=self.start_game)
        layout.add_widget(play_btn)

        load_btn = Button(text='Загрузить уровень', size_hint=(1, 0.15))
        load_btn.bind(on_press=self.load_level)
        layout.add_widget(load_btn)

        layout.add_widget(Widget(size_hint=(1, 0.6)))
        self.add_widget(layout)

    def on_complexity_changed(self, instance, value):
        self.complexity = int(value)
        self.complexity_label.text = str(self.complexity)
        print(f"Сложность изменена на {self.complexity}")

    def start_game(self, instance):
        print("Кнопка 'Играть' нажата")
        game_screen = self.manager.get_screen('game')
        game_screen.complexity = self.complexity
        game_screen.loaded_level = None  # сбросить, если был
        self.manager.current = 'game'

    def load_level(self, instance):
        print("Кнопка 'Загрузить уровень' нажата")
        self.manager.current = 'level_select'
    

class LevelSelectScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
        layout.add_widget(Label(text='Выберите уровень', font_size='24sp', size_hint=(1, 0.1), color=(0.5, 0.5, 0.5, 1)))
        
        self.scroll = ScrollView(size_hint=(1, 0.8))
        self.level_container = BoxLayout(orientation='vertical', size_hint_y=None)
        self.level_container.bind(minimum_height=self.level_container.setter('height'))
        self.scroll.add_widget(self.level_container)
        layout.add_widget(self.scroll)
        
        back_btn = Button(text='Назад', size_hint=(1, 0.1))
        back_btn.bind(on_press=self.go_back)
        layout.add_widget(back_btn)
        self.add_widget(layout)
        
        self.refresh_levels()
    
    def refresh_levels(self):
        """Перечитывает save.txt и перестраивает список кнопок уровней"""
        self.level_container.clear_widgets()
        self.levels = self.load_levels()
        
        if not self.levels:
            self.level_container.add_widget(Label(text="Нет сохраненных уровней", color=(0.5, 0.5, 0.5, 1)))
        else:
            for i, level in enumerate(self.levels):
                # Горизонтальный контейнер для строки: кнопка уровня + кнопка удаления
                row = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=5)
                
                # Кнопка выбора уровня (занимает почти всю ширину)
                level_btn = Button(text=f"Уровень {i+1} (n={level['n']}, m={level['m']})", size_hint_x=0.85)
                level_btn.level_index = i
                level_btn.bind(on_press=self.select_level)
                row.add_widget(level_btn)
                
                # Кнопка удаления (крестик)
                del_btn = Button(text="Удалить уровень", size_hint_x=0.20, background_normal='', background_color=(0.8, 0.2, 0.2, 1))
                del_btn.level_index = i
                del_btn.bind(on_press=self.delete_level)
                row.add_widget(del_btn)
                
                self.level_container.add_widget(row)
    
    def on_pre_enter(self):
        self.refresh_levels()
    
    def load_levels(self):
        try:
            with open('save.txt', 'r') as f:
                lines = f.readlines()
            if not lines:
                return []
            first_line = lines[0].strip().split()
            if len(first_line) == 1:
                k = int(first_line[0])
                idx = 1
            else:
                k = 1
                idx = 0
            levels = []
            for _ in range(k):
                n, m = map(int, lines[idx].split())
                idx += 1
                poly = []
                for _ in range(n):
                    x, y = map(int, lines[idx].split())
                    poly.append(Point(x, y))
                    idx += 1
                first = []
                for _ in range(m):
                    x, y = map(int, lines[idx].split())
                    first.append(Point(x, y))
                    idx += 1
                second = []
                for _ in range(m):
                    x, y = map(int, lines[idx].split())
                    second.append(Point(x, y))
                    idx += 1
                levels.append({'n': n, 'm': m, 'poly': poly, 'first': first, 'second': second})
            return levels
        except Exception as e:
            print(f"Ошибка загрузки уровней: {e}")
            return []
    
    def delete_level(self, instance):
        """Удаляет уровень по индексу и перезаписывает файл"""
        idx = instance.level_index
        if 0 <= idx < len(self.levels):
            # Удаляем из списка в памяти
            del self.levels[idx]
            # Перезаписываем файл
            try:
                with open('save.txt', 'w') as f:
                    f.write(f"{len(self.levels)}\n")
                    for level in self.levels:
                        f.write(f"{level['n']} {level['m']}\n")
                        for p in level['poly']:
                            f.write(f"{int(p.x)} {int(p.y)}\n")
                        for p in level['first']:
                            f.write(f"{int(p.x)} {int(p.y)}\n")
                        for p in level['second']:
                            f.write(f"{int(p.x)} {int(p.y)}\n")
                print(f"Уровень {idx+1} удалён. Осталось уровней: {len(self.levels)}")
            except Exception as e:
                print(f"Ошибка удаления уровня: {e}")
            # Обновляем отображение
            self.refresh_levels()
    
    def select_level(self, instance):
        level = self.levels[instance.level_index]
        game_screen = self.manager.get_screen('game')
        game_screen.loaded_level = level
        self.manager.current = 'game'
    
    def go_back(self, instance):
        self.manager.current = 'menu'

from kivy.config import Config
Config.set('input', 'mouse', 'mouse,disable_multitouch')
class CutPolygonApp(App):
    def build(self):
        Window.show_cursor_touch = False
        Window.clearcolor = COLOR_BACKGROUND
        sm = ScreenManager()
        sm.add_widget(MainMenu(name='menu'))
        sm.add_widget(GameScreen(name='game'))
        sm.add_widget(LevelSelectScreen(name='level_select'))
        return sm


if __name__ == '__main__':
    CutPolygonApp().run()