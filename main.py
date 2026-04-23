from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.slider import Slider
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
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
        layout = BoxLayout(orientation='vertical', padding=5, spacing=5)

        top_bar = BoxLayout(orientation='horizontal', size_hint=(1, None), height=30)
        self.info_label = Label(text='Сложность: 5', size_hint=(1, 1), color=(0.5, 0.5, 0.5, 1))
        top_bar.add_widget(self.info_label)
        layout.add_widget(top_bar)

        self.drawing_area = DrawingArea()
        layout.add_widget(self.drawing_area)

        bottom_bar = BoxLayout(orientation='vertical', size_hint=(1, None), height=150)
        self.new_btn = Button(text='Новая генерация')
        self.new_btn.bind(on_press=self.regenerate_polygon)
        self.answer_btn = Button(text='Показать ответ')
        self.answer_btn.bind(on_press=self.toggle_answer)
        self.clear_btn = Button(text='Сброс линии')
        self.clear_btn.bind(on_press=self.clear_line)
        self.menu_btn = Button(text='Меню')
        self.menu_btn.bind(on_press=self.go_to_menu)

        bottom_bar.add_widget(self.new_btn)
        bottom_bar.add_widget(self.answer_btn)
        bottom_bar.add_widget(self.clear_btn)
        bottom_bar.add_widget(self.menu_btn)
        layout.add_widget(bottom_bar)

        self.add_widget(layout)

        self.first_ans = []
        self.second_ans = []
        self.show_answer = False

    def on_enter(self, *args):
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

    def toggle_answer(self, instance):
        print("Кнопка 'Показать ответ' нажата")
        self.show_answer = not self.show_answer
        self.drawing_area.show_answer = self.show_answer
        self.answer_btn.text = 'Скрыть ответ' if self.show_answer else 'Показать ответ'
        self.drawing_area.update_canvas()

    def clear_line(self, instance):
        print("Кнопка 'Сброс линии' нажата")
        self.drawing_area.clear_line()

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
    complexity = NumericProperty(5)

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
        self.manager.current = 'game'
    

class CutPolygonApp(App):
    def build(self):
        Window.clearcolor = COLOR_BACKGROUND
        sm = ScreenManager()
        sm.add_widget(MainMenu(name='menu'))
        sm.add_widget(GameScreen(name='game'))
        return sm


if __name__ == '__main__':
    CutPolygonApp().run()