# Проверка версии 1.0.0

Дата: 21 октября 2026 года. Локальное окружение: Windows, CPython 3.10.11, NumPy 2.2.6, SciPy 1.15.3. Браузерная проверка: встроенный Chromium, реальное выполнение Pyodide 314.0.7.

## Автоматические проверки

13 Python-тестов: соответствие адаптера исходной последовательности численных функций, мощность при z=0, нормировка коэффициентов, симметрия X/Y, отказ при недостаточной сетке и памяти, нечисловые и некорректные параметры, строгий JSON без NaN/Infinity, SPE с несколькими кадрами и стеком строк, повреждённый SPE, отказ для SPE 3.x, сохранение 16-битных значений PNG, восстановление известной моды HE_1,3, пустой кадр, неверный ROI, неизвестные команды.

4 JavaScript-теста: полный JSON round-trip, отказ для повреждённых проектов, безопасный CSV, относительные URL для публикации в подпапке GitHub Pages.

## Проверено в браузере

- Реальная загрузка Python, NumPy, SciPy и Pillow и выполнение расчёта.
- Стандартная задача: λ=800 nm, диаметр=300 µm, w₀=45 µm, наклон=0°, длина=40 cm, сетка 96×96. Получено 5 физических мод, 10 профилей, без fallback.
- Экспорт браузерного результата и численное сравнение с CPython: максимальное абсолютное расхождение P/P_in на 61 расстоянии — **9.09×10⁻¹⁴**, нормированных весов коэффициентов — **8.66×10⁻¹⁵**.
- Новый срез z=11.4 cm: массив нормированной интенсивности совпал после сериализации до 7 знаков.
- Синтетическое изображение HE_1,3: правильная мода на первом месте; сходство >0.999, двумерная корреляция >0.999.
- Когерентная подгонка с 3 стартами: относительная ошибка около 3.76×10⁻⁴. Не является доказательством уникальности фаз.

## Границы проверки

Модель приближённая; численная регрессия не доказывает её экспериментальную точность. Контрольные результаты не гарантируют точность всех мод, материалов и параметров. Проверка на физических GPU отсутствует и не требуется для CPU-версии. Другие браузерные движки и устройства не считаются проверенными без отдельного запуска.

## Interface and modal-lab revision

The application interface was revised to English with an industrial layout. The original complete Russian theory was preserved as a separate reader, containing all 28 chapters and 358 display-math blocks. Publisher links replace local PDF references in the rendered HTML; the original Markdown remains unchanged.

The suite now contains **18 Python tests and 7 JavaScript tests**. Added checks cover unit-power modal profiles; constructive and destructive interference; orthogonal vector polarization; propagation of HE/EH/TE/TM; sampling and index bounds; retaining the main simulation while inspecting modes; failed image loads preserving the previous frame; and fixed / detailed power-axis limits without hiding excess values.

Browser checks on the revised interface: selecting HE_1,3c from the simulation, manually entering HE_1,1c, summing both, phase display, and exact cancellation of two identical profiles with a 180° phase difference. Input-beam keyboard positioning updates the offset. The experimental region and physical-scale controls fit within their panel at desktop width.

Additional browser checks: pointer drag changes beam X/Y and polar offset; the Detail power axis resolves 99.8–100% without artificial 102% headroom; all theory chapters expand with 565 rendered mathematical expressions and no MathJax error nodes. At a 390 px viewport the document width is 375 px and the ROI / physical-scale fields remain within the panel. Stop during engine loading cancels the task, and a new calculation can be launched.
