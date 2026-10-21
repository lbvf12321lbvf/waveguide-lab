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

The application interface was revised to English with an industrial layout. The complete theory is available in English as a separate reader, containing all 28 chapters and 358 display-math blocks. Publisher links replace local PDF references in both the English Markdown and rendered HTML; the original Russian Markdown remains in the repository as a source reference.

The suite now contains **18 Python tests and 7 JavaScript tests**. Added checks cover unit-power modal profiles; constructive and destructive interference; orthogonal vector polarization; propagation of HE/EH/TE/TM; sampling and index bounds; retaining the main simulation while inspecting modes; failed image loads preserving the previous frame; and fixed / detailed power-axis limits without hiding excess values.

Browser checks on the revised interface: selecting HE_1,3c from the simulation, manually entering HE_1,1c, summing both, phase display, and exact cancellation of two identical profiles with a 180° phase difference. Input-beam keyboard positioning updates the offset. The experimental region and physical-scale controls fit within their panel at desktop width.

Additional browser checks: pointer drag changes beam X/Y and polar offset; the Detail power axis resolves 99.8–100% without artificial 102% headroom; all theory chapters expand with 565 rendered mathematical expressions and no MathJax error nodes. At a 390 px viewport the document width is 375 px and the ROI / physical-scale fields remain within the panel. Stop during engine loading cancels the task, and a new calculation can be launched.

## Complete English theory

Translated all 481 source lines containing Russian text, including headings, derivations, tables, captions and reference descriptions. Compared the full ordered sequence of 565 TeX expressions against the original: every expression is unchanged, including all 358 display blocks. Both documents retain 28 chapters.

Browser verification: all chapters expand; all 565 expressions render with zero MathJax error nodes; the document language is English and no Cyrillic text remains in the reader. Chapter navigation opens the selected section. The Markdown download uses the complete English source with publication URLs. Removed the introductory language/desktop-model notice and the duplicate reader banner.

## Automatic basis, slit aperture and selected-mode fitting

The suite contains **28 Python tests and 10 JavaScript tests**. New numerical checks cover automatic growth to a 0.1% input-projection residual, changes with beam tilt and offset, manual limits and legacy settings, resource-limit reporting, and checking memory against the actual basis. A separate CPython check completed a 129-mode / 247-profile calculation at 96 × 96 (2° launch angle, 40 µm offset, 20 µm waist), confirming removal of the old 128-mode cap.

Slit tests recover the known HE_1,3 image through horizontal, vertical and 37° apertures. Replacing every excluded pixel with intensity 10⁹ leaves preprocessing, radial data and ranking unchanged. A known coherent HE_1,2c + HE_1,4c mixture is fitted through a 27° slit using exactly those two profiles: relative intensity error < 0.01, correlation > 0.999, and the recovered amplitude ratio after undoing profile normalization is within 0.02 of 0.55. Empty apertures and invalid selected modes are rejected. JavaScript checks cover slit geometry and old calculation-file imports.

Real Pyodide browser checks: default automatic selection uses five physical modes and reaches its target; a manual limit of two uses exactly two modes and reports the larger residual. Slit movement, edge-width drag, rotation, axis drawing and the vertical preset work on the image. The single-mode search through a 30° slit ranks HE_1,3 first. Adding it from the results and entering HE_1,2c manually yields a fit containing exactly two physical modes, with relative error about 0.0004 on the synthetic image. The reconstructed image respects the mask and the coefficient table displays relative amplitudes and phases.

At a 390 px viewport, the document fits the 375 px content area without horizontal overflow; slit controls and selected-mode inputs stay within their panel. This is layout verification in Chromium, not a claim of performance testing on physical mobile devices. Intensity-only phase ambiguity and the distinction between coefficient amplitudes and power fractions remain explicit in the interface.
