---
created: 2026-07-11T09:28
updated: 2026-07-11T10:20
---
# Теория расчета полого цилиндрического волновода

Образовательный материал к расчетам в пакете `waveguide_practice`.

Файл написан как связный путь от базовой электродинамики до формул, которые используются в текущем коде: собственные моды полого металлического капилляра, комплексные постоянные распространения, потери, угловой отбор мод, разложение наклонного гауссова пучка, продольная интерференция и межмодовые задержки импульса.

## 0. Источники из папки и как они используются

В материале ниже формулы из кода привязаны к локальным статьям из рабочей папки. Ссылки относительные, поэтому будут открываться при переносе Markdown вместе с PDF.

- [Marcatili, Schmeltzer, 1964](marcatili1964.pdf) - базовая работа по полым металлическим и диэлектрическим круговым волноводам: нормальные моды, постоянные распространения, семейства HE/EH и масштаб потерь $\alpha\propto\lambda^2/a^3$.
- [Miyagi, 1985](miyagi1985.pdf) - связь волнового расчета потерь в круглом полом волноводе с лучевой оптикой, в том числе трактовка гибридных мод через соответствующие лучи.
- [Matsuura, Saito, Miyagi, Hongo, 1989](matsuura1989_important.pdf) - удобная лучевая формула для потерь при мультимодовом распространении, усреднение по поляризациям через коэффициенты отражения и учет распределения углов ввода.
- [Saito, Sato, Miyagi, 1993](saito1993_Important.pdf) - мультимодовые потери в ИК-полых волноводах: экспоненциальное затухание при малых потерях, зависимость от радиуса канала и угла ввода, сравнение волнового и геометрического подходов.
- [Abrams, 1972](abrams1972.pdf) - потери связи в резонаторах на полых волноводах, роль низшей моды EH11 и согласования внешнего поля с модой.
- [Jenkins, Devereux, 1992](jenkins1992.pdf) - регенерация TEM00-поля в круглом полом волноводе из-за относительной фазы мод EH11/EH12; это физическая опора для разделов о продольной модальной корреляции.
- [Khannanov, Vankov, Kulik et al., 2021](2021_Khannanov_Vankov_Kulik.pdf) - прикладная мотивация: серебряный SERS-волноводный резонатор и Raman-измерения в газах; используется как контекст для серебряного покрытия и экспериментальной задачи.

PDF в подпапке `Plasmon` здесь не разобраны полностью: там есть дубликаты некоторых статей и отдельная плазмонная литература. Если расчет будет расширяться на поверхностные плазмон-поляритоны или SERS-усиление на стенке, этот блок нужно дополнить отдельной главой.

## 1. Область применимости расчета

В расчете рассматривается полый круглый капилляр радиуса

$$
a=\frac{d}{2},
$$

заполненный воздухом и окруженный металлической стенкой. В коде по умолчанию:

$$
\lambda=800\ \text{nm},\qquad d=300\ \mu\text{m},\qquad a=150\ \mu\text{m}.
$$

Волновое число в вакууме:

$$
k_0=\frac{2\pi}{\lambda}.
$$

Для металла используется комплексная диэлектрическая проницаемость серебра:

$$
\varepsilon_m=-31.021+0.40948i
$$

на длине волны 800 nm. Комплексный показатель преломления металла:

$$
v=n_m=\sqrt{\varepsilon_m}.
$$

Главное приближение расчета: поле внутри капилляра представляется как сумма собственных мод цилиндрического волновода. В коде это не полный векторный конечно-элементный расчет, а модальная модель с аналитическими цилиндрическими функциями и численным решением характеристических уравнений.

Такая постановка следует классической модальной теории полых круглых волноводов, изложенной у [Marcatili, Schmeltzer, 1964](marcatili1964.pdf). Для интерпретации потерь и мультимодового ввода дополнительно используются результаты [Miyagi, 1985](miyagi1985.pdf), [Matsuura et al., 1989](matsuura1989_important.pdf) и [Saito et al., 1993](saito1993_Important.pdf).

Используемая зависимость от времени:

$$
\exp(-i\omega t).
$$

Зависимость моды от продольной координаты:

$$
\exp(i\gamma z).
$$

Если

$$
\gamma=\beta+i\alpha_{\rm amp},
$$

то

$$
\exp(i\gamma z)=\exp(i\beta z)\exp(-\alpha_{\rm amp}z).
$$

Значит, $\alpha_{\rm amp}$ есть коэффициент затухания амплитуды, а коэффициент затухания мощности равен

$$
\alpha_{\rm pow}=2\alpha_{\rm amp}=2\,\mathrm{Im}\,\gamma.
$$

Именно это используется в коде:

$$
\texttt{power\_attenuation}=2\,\mathrm{Im}\,\gamma,\qquad
L_{\rm att}=\frac{1}{\alpha_{\rm pow}}.
$$

## 2. Уравнения Максвелла и волновое уравнение

В линейной однородной среде без свободных зарядов и токов уравнения Максвелла для гармонических полей имеют вид

$$
\nabla\times \mathbf E=i\omega\mu\,\mathbf H,
$$

$$
\nabla\times \mathbf H=-i\omega\varepsilon\,\mathbf E,
$$

$$
\nabla\cdot(\varepsilon\mathbf E)=0,\qquad
\nabla\cdot(\mu\mathbf H)=0.
$$

Внутри капилляра среда считается воздухом, поэтому

$$
\varepsilon\simeq\varepsilon_0,\qquad \mu\simeq\mu_0.
$$

В металле:

$$
\varepsilon=\varepsilon_0\varepsilon_m,\qquad \mu\simeq\mu_0.
$$

Получим волновое уравнение для электрического поля. Берем ротор от первого уравнения Максвелла:

$$
\nabla\times(\nabla\times\mathbf E)
=i\omega\mu\,\nabla\times\mathbf H.
$$

Подставляем второе уравнение:

$$
\nabla\times(\nabla\times\mathbf E)
=i\omega\mu(-i\omega\varepsilon\mathbf E)
=\omega^2\mu\varepsilon\,\mathbf E.
$$

Используем тождество

$$
\nabla\times(\nabla\times\mathbf E)
=\nabla(\nabla\cdot\mathbf E)-\nabla^2\mathbf E.
$$

В однородной области $\nabla\cdot\mathbf E=0$, поэтому

$$
-\nabla^2\mathbf E=\omega^2\mu\varepsilon\,\mathbf E.
$$

Отсюда:

$$
\nabla^2\mathbf E+k^2\mathbf E=0,
$$

где

$$
k^2=\omega^2\mu\varepsilon.
$$

В воздухе:

$$
k=k_0=\frac{\omega}{c}.
$$

В металле:

$$
k=k_m=v k_0,\qquad v=\sqrt{\varepsilon_m}.
$$

Такое же волновое уравнение выполняется для $\mathbf H$.

## 3. Разделение переменных в цилиндрическом волноводе

Капилляр имеет цилиндрическую симметрию, поэтому естественные координаты:

$$
(r,\varphi,z).
$$

Для моды с постоянной распространения $\gamma$ все компоненты поля имеют зависимость

$$
\mathbf E(r,\varphi,z)=\mathbf E(r,\varphi)\exp(i\gamma z),
$$

$$
\mathbf H(r,\varphi,z)=\mathbf H(r,\varphi)\exp(i\gamma z).
$$

Тогда продольная производная заменяется на

$$
\frac{\partial}{\partial z}\rightarrow i\gamma.
$$

Для продольной компоненты поля, например $E_z$, волновое уравнение принимает вид

$$
\left(\nabla_\perp^2+k^2-\gamma^2\right)E_z=0,
$$

где поперечный лапласиан в цилиндрических координатах равен

$$
\nabla_\perp^2=
\frac{1}{r}\frac{\partial}{\partial r}
\left(r\frac{\partial}{\partial r}\right)
+\frac{1}{r^2}\frac{\partial^2}{\partial\varphi^2}.
$$

Вводим поперечное волновое число:

$$
\kappa^2=k^2-\gamma^2.
$$

Тогда

$$
\left(\nabla_\perp^2+\kappa^2\right)E_z=0.
$$

Ищем решение в виде

$$
E_z(r,\varphi)=R(r)\exp(in\varphi),
$$

где $n=0,1,2,\ldots$ - азимутальный индекс.

Подстановка дает

$$
\frac{1}{r}\frac{d}{dr}\left(r\frac{dR}{dr}\right)
+\left(\kappa^2-\frac{n^2}{r^2}\right)R=0.
$$

Умножим на $r^2$:

$$
r^2 R''+rR'+(\kappa^2 r^2-n^2)R=0.
$$

Это уравнение Бесселя. Его регулярное в нуле решение:

$$
R(r)=J_n(\kappa r),
$$

где $J_n$ - функция Бесселя первого рода.

Внутри капилляра:

$$
\kappa_i=k_i=\sqrt{k_0^2-\gamma^2}.
$$

В металле:

$$
\kappa_e=k_e=\sqrt{v^2k_0^2-\gamma^2}.
$$

В коде это записано как

$$
k_i=\sqrt{k_0^2-\gamma^2},\qquad
k_e=\sqrt{v^2k_0^2-\gamma^2}.
$$

Для внешней области используется функция Ханкеля $H_n^{(1)}(k_e r)$. В численном коде применена масштабированная функция `hankel1e`, чтобы избежать переполнения на комплексных аргументах. Отношения функций Ханкеля при этом сохраняют тот же физический смысл.

## 4. Связь продольных и поперечных компонент

Моды волновода удобно строить через продольные компоненты $E_z$ и $H_z$. Поперечные компоненты выражаются через них.

Пусть

$$
\mathbf E=\mathbf E_\perp+\hat{\mathbf z}E_z,\qquad
\mathbf H=\mathbf H_\perp+\hat{\mathbf z}H_z.
$$

Оператор градиента:

$$
\nabla=\nabla_\perp+\hat{\mathbf z}\frac{\partial}{\partial z}
=\nabla_\perp+i\gamma\hat{\mathbf z}.
$$

Теперь не будем пропускать алгебру. Запишем роторы в цилиндрических координатах. Для гармонической зависимости $\exp(i\gamma z)$ имеем

$$
\frac{\partial}{\partial z}=i\gamma.
$$

Компоненты уравнения

$$
\nabla\times\mathbf E=i\omega\mu\mathbf H
$$

равны

$$
\frac{1}{r}\frac{\partial E_z}{\partial\varphi}
-
\frac{\partial E_\varphi}{\partial z}
=i\omega\mu H_r,
$$

$$
\frac{\partial E_r}{\partial z}
-
\frac{\partial E_z}{\partial r}
=i\omega\mu H_\varphi.
$$

После замены $\partial/\partial z\to i\gamma$:

$$
\frac{1}{r}\frac{\partial E_z}{\partial\varphi}
-i\gamma E_\varphi
=i\omega\mu H_r,
\tag{4.1}
$$

$$
i\gamma E_r
-
\frac{\partial E_z}{\partial r}
=i\omega\mu H_\varphi.
\tag{4.2}
$$

Компоненты уравнения

$$
\nabla\times\mathbf H=-i\omega\varepsilon\mathbf E
$$

дают

$$
\frac{1}{r}\frac{\partial H_z}{\partial\varphi}
-
\frac{\partial H_\varphi}{\partial z}
=-i\omega\varepsilon E_r,
$$

$$
\frac{\partial H_r}{\partial z}
-
\frac{\partial H_z}{\partial r}
=-i\omega\varepsilon E_\varphi.
$$

Снова подставляем $\partial/\partial z=i\gamma$:

$$
\frac{1}{r}\frac{\partial H_z}{\partial\varphi}
-i\gamma H_\varphi
=-i\omega\varepsilon E_r,
\tag{4.3}
$$

$$
i\gamma H_r
-
\frac{\partial H_z}{\partial r}
=-i\omega\varepsilon E_\varphi.
\tag{4.4}
$$

Нужно выразить $E_r,E_\varphi,H_r,H_\varphi$ через $E_z,H_z$. Начнем с $E_r$. Из (4.2):

$$
H_\varphi
=
\frac{i\gamma E_r-\partial E_z/\partial r}{i\omega\mu}
=
\frac{\gamma}{\omega\mu}E_r
+
\frac{i}{\omega\mu}\frac{\partial E_z}{\partial r}.
\tag{4.5}
$$

Подставляем (4.5) в (4.3):

$$
\frac{1}{r}\frac{\partial H_z}{\partial\varphi}
-i\gamma
\left(
\frac{\gamma}{\omega\mu}E_r
+
\frac{i}{\omega\mu}\frac{\partial E_z}{\partial r}
\right)
=
-i\omega\varepsilon E_r.
$$

Раскрываем скобки:

$$
\frac{1}{r}\frac{\partial H_z}{\partial\varphi}
-
\frac{i\gamma^2}{\omega\mu}E_r
+
\frac{\gamma}{\omega\mu}\frac{\partial E_z}{\partial r}
=
-i\omega\varepsilon E_r.
$$

Переносим все с $E_r$ вправо:

$$
\frac{1}{r}\frac{\partial H_z}{\partial\varphi}
+
\frac{\gamma}{\omega\mu}\frac{\partial E_z}{\partial r}
=
-i
\left(
\omega\varepsilon-\frac{\gamma^2}{\omega\mu}
\right)E_r.
$$

Приводим скобку к общему знаменателю:

$$
\omega\varepsilon-\frac{\gamma^2}{\omega\mu}
=
\frac{\omega^2\mu\varepsilon-\gamma^2}{\omega\mu}
=
\frac{\kappa^2}{\omega\mu}.
$$

Значит,

$$
\frac{1}{r}\frac{\partial H_z}{\partial\varphi}
+
\frac{\gamma}{\omega\mu}\frac{\partial E_z}{\partial r}
=
-i\frac{\kappa^2}{\omega\mu}E_r.
$$

Умножаем на $\omega\mu$:

$$
\frac{\omega\mu}{r}\frac{\partial H_z}{\partial\varphi}
+
\gamma\frac{\partial E_z}{\partial r}
=
-i\kappa^2E_r.
$$

Так как $1/(-i)=i$, получаем

$$
E_r=
\frac{i}{\kappa^2}
\left(
\gamma\frac{\partial E_z}{\partial r}
+
\frac{\omega\mu}{r}\frac{\partial H_z}{\partial\varphi}
\right).
\tag{4.6}
$$

Теперь выведем $E_\varphi$. Из (4.1):

$$
H_r
=
\frac{(1/r)\partial E_z/\partial\varphi-i\gamma E_\varphi}{i\omega\mu}
=
-\frac{i}{\omega\mu r}\frac{\partial E_z}{\partial\varphi}
-
\frac{\gamma}{\omega\mu}E_\varphi.
\tag{4.7}
$$

Подставляем (4.7) в (4.4):

$$
i\gamma
\left(
-\frac{i}{\omega\mu r}\frac{\partial E_z}{\partial\varphi}
-
\frac{\gamma}{\omega\mu}E_\varphi
\right)
-
\frac{\partial H_z}{\partial r}
=
-i\omega\varepsilon E_\varphi.
$$

Раскрываем:

$$
\frac{\gamma}{\omega\mu r}\frac{\partial E_z}{\partial\varphi}
-
\frac{i\gamma^2}{\omega\mu}E_\varphi
-
\frac{\partial H_z}{\partial r}
=
-i\omega\varepsilon E_\varphi.
$$

Переносим члены с $E_\varphi$ вправо:

$$
\frac{\gamma}{\omega\mu r}\frac{\partial E_z}{\partial\varphi}
-
\frac{\partial H_z}{\partial r}
=
-i
\left(
\omega\varepsilon-\frac{\gamma^2}{\omega\mu}
\right)E_\varphi
=
-i\frac{\kappa^2}{\omega\mu}E_\varphi.
$$

Умножаем на $\omega\mu$:

$$
\frac{\gamma}{r}\frac{\partial E_z}{\partial\varphi}
-
\omega\mu\frac{\partial H_z}{\partial r}
=
-i\kappa^2E_\varphi.
$$

Отсюда

$$
E_\varphi=
\frac{i}{\kappa^2}
\left(
\frac{\gamma}{r}\frac{\partial E_z}{\partial\varphi}
-
\omega\mu\frac{\partial H_z}{\partial r}
\right).
\tag{4.8}
$$

Аналогично для магнитного поля. Можно повторить те же действия, поменяв

$$
\mathbf E\leftrightarrow\mathbf H,
\qquad
\mu\to\varepsilon,
\qquad
\omega\mu\to-\omega\varepsilon
$$

с учетом знака во втором уравнении Максвелла. Получаются компоненты

$$
H_r=
\frac{i}{\kappa^2}
\left(
\gamma\frac{\partial H_z}{\partial r}
-
\frac{\omega\varepsilon}{r}\frac{\partial E_z}{\partial\varphi}
\right),
\tag{4.9}
$$

$$
H_\varphi=
\frac{i}{\kappa^2}
\left(
\frac{\gamma}{r}\frac{\partial H_z}{\partial\varphi}
+
\omega\varepsilon\frac{\partial E_z}{\partial r}
\right).
\tag{4.10}
$$

Теперь свернем (4.6)-(4.10) в компактную векторную форму. Поперечный градиент:

$$
\nabla_\perp f
=
\hat{\mathbf r}\frac{\partial f}{\partial r}
+
\hat{\boldsymbol\varphi}\frac{1}{r}\frac{\partial f}{\partial\varphi}.
$$

Для любого $f$:

$$
\hat{\mathbf z}\times\nabla_\perp f
=
\hat{\boldsymbol\varphi}\frac{\partial f}{\partial r}
-
\hat{\mathbf r}\frac{1}{r}\frac{\partial f}{\partial\varphi}.
$$

Поэтому (4.6) и (4.8) объединяются в

$$
\mathbf E_\perp=
\frac{i}{\kappa^2}
\left(
\gamma\nabla_\perp E_z
-
\omega\mu\,\hat{\mathbf z}\times\nabla_\perp H_z
\right),
\tag{4.11}
$$

а (4.9) и (4.10) дают

$$
\mathbf H_\perp=
\frac{i}{\kappa^2}
\left(
\gamma\nabla_\perp H_z
+
\omega\varepsilon\,\hat{\mathbf z}\times\nabla_\perp E_z
\right).
\tag{4.12}
$$

Итак, если известны $E_z$ и $H_z$, то все поперечные компоненты находятся прямым дифференцированием. Поэтому задача о модах действительно сводится к двум шагам:

1. найти цилиндрические решения для $E_z,H_z$;
2. наложить граничные условия на $r=a$ для тангенциальных компонент $E_z,H_z,E_\varphi,H_\varphi$.

## 5. Типы мод: TE, TM, HE, EH

В цилиндрическом волноводе есть несколько семейств мод.

Классификация TE/TM/HE/EH и использование гибридных мод как нормальных мод полого круглого волновода являются стандартной частью теории Marcatili-Schmeltzer. Для задач ввода-вывода и резонаторов низшая гибридная мода EH11 отдельно обсуждается у [Abrams, 1972](abrams1972.pdf).

TE-моды имеют

$$
E_z=0,\qquad H_z\ne 0.
$$

TM-моды имеют

$$
H_z=0,\qquad E_z\ne 0.
$$

Гибридные моды имеют одновременно

$$
E_z\ne 0,\qquad H_z\ne 0.
$$

Они делятся на семейства HE и EH. В строгой векторной теории различие связано с относительным вкладом электрической и магнитной продольных компонент, а в текущем численном расчете это различие отражено в выборе бесселевых корней:

$$
\mathrm{HE}_{n,m}:\quad u_{n,m}\approx j_{n-1,m},
$$

$$
\mathrm{EH}_{n,m}:\quad u_{n,m}\approx j_{n+1,m}.
$$

Здесь $j_{\ell,m}$ - $m$-й нуль функции Бесселя $J_\ell$:

$$
J_\ell(j_{\ell,m})=0.
$$

В расчете также используются осесимметричные TE и TM семейства:

$$
\mathrm{TE}_{0,m}:\quad u_{0,m}\approx j_{1,m},
$$

$$
\mathrm{TM}_{0,m}:\quad u_{0,m}\approx j_{0,m}.
$$

Эти корни используются как начальные приближения для решения более точного комплексного характеристического уравнения.

## 6. Геометрический смысл параметра \(u\)

Для моды внутри полости поперечное волновое число примерно равно

$$
k_\perp=\frac{u}{a}.
$$

Связь между полным волновым числом, поперечным волновым числом и продольной постоянной распространения:

$$
k_0^2=\beta^2+k_\perp^2.
$$

Отсюда в беззатухательном приближении:

$$
\beta\simeq\sqrt{k_0^2-\left(\frac{u}{a}\right)^2}.
$$

Это именно начальное приближение для действительной части $\gamma$ в коде:

$$
\beta_0=\sqrt{k_0^2-\left(\frac{u_0}{a}\right)^2}.
$$

Если ввести модальный угол $\theta_\mu$, то

$$
\sin\theta_\mu=\frac{k_\perp}{k_0}
=\frac{u_\mu}{k_0a}.
$$

Следовательно,

$$
\theta_\mu=\arcsin\left(\frac{u_\mu}{k_0a}\right).
$$

Мода является распространяющейся, если

$$
u_\mu<k_0a.
$$

Величина

$$
u_{\rm cutoff}=k_0a
$$

играет роль верхней границы для распространяющихся мод.

Для параметров по умолчанию:

$$
k_0a=\frac{2\pi}{800\cdot10^{-9}}\cdot150\cdot10^{-6}
\approx1178.
$$

Это большое число. Поэтому даже умеренные углы входа соответствуют большим значениям $u$ и высоким индексам мод.

## 7. Характеристические уравнения для комплексной \(\gamma\)

Точный расчет моды требует выполнить граничные условия на границе воздух-металл:

$$
r=a.
$$

Тангенциальные компоненты полей должны быть непрерывны:

$$
E_\varphi^{(i)}=E_\varphi^{(e)},\qquad
E_z^{(i)}=E_z^{(e)},
$$

$$
H_\varphi^{(i)}=H_\varphi^{(e)},\qquad
H_z^{(i)}=H_z^{(e)}.
$$

Индекс $i$ означает внутреннюю область, индекс $e$ - металл.

Ниже это делается явно: сначала задаются продольные поля внутри и снаружи, затем через формулы раздела 4 считаются $E_\varphi$ и $H_\varphi$, после этого граничные условия превращаются в однородную систему для амплитуд. Характеристическое уравнение появляется из условия нулевого определителя этой системы.

Именно такой ход - от уравнений Максвелла к характеристическим уравнениям нормальных мод круглого полого волновода - лежит в основе работы [Marcatili, Schmeltzer, 1964](marcatili1964.pdf). В коде характеристические уравнения записаны в форме, удобной для численного решения комплексного корня $\gamma$.

### 7.1. TE-уравнение

Для TE-моды

$$
E_z=0,\qquad H_z\ne0.
$$

В текущем коде для TE рассматриваются осесимметричные моды $n=0$. Тогда $\partial/\partial\varphi=0$, и продольное магнитное поле можно записать так:

$$
H_z^{(i)}(r)=A J_0(k_i r)
$$

внутри капилляра и

$$
H_z^{(e)}(r)=B H_0^{(1)}(k_e r)
$$

в металле.

Так как $E_z=0$, из формулы (4.8)

$$
E_\varphi=
\frac{i}{\kappa^2}
\left(
\frac{\gamma}{r}\frac{\partial E_z}{\partial\varphi}
-
\omega\mu\frac{\partial H_z}{\partial r}
\right)
$$

остается

$$
E_\varphi=
-\frac{i\omega\mu}{\kappa^2}
\frac{\partial H_z}{\partial r}.
$$

Внутри $\kappa^2=k_i^2$, поэтому

$$
E_\varphi^{(i)}
=
-\frac{i\omega\mu}{k_i^2}
\frac{d}{dr}\left[A J_0(k_i r)\right]
=
-\frac{i\omega\mu A}{k_i^2}
k_i J_0'(k_i r).
$$

Используем тождество

$$
J_0'(x)=-J_1(x).
$$

Тогда на границе $r=a$:

$$
E_\varphi^{(i)}(a)
=
\frac{i\omega\mu A}{k_i}J_1(k_i a).
\tag{7.1}
$$

Снаружи:

$$
E_\varphi^{(e)}
=
-\frac{i\omega\mu}{k_e^2}
\frac{d}{dr}\left[B H_0^{(1)}(k_e r)\right]
=
-\frac{i\omega\mu B}{k_e^2}
k_e {H_0^{(1)}}'(k_e r).
$$

Для функции Ханкеля аналогично

$$
{H_0^{(1)}}'(x)=-H_1^{(1)}(x).
$$

Значит,

$$
E_\varphi^{(e)}(a)
=
\frac{i\omega\mu B}{k_e}H_1^{(1)}(k_e a).
\tag{7.2}
$$

Теперь применяем два граничных условия.

Первое - непрерывность $H_z$:

$$
A J_0(k_i a)
=
B H_0^{(1)}(k_e a).
\tag{7.3}
$$

Второе - непрерывность $E_\varphi$:

$$
\frac{i\omega\mu A}{k_i}J_1(k_i a)
=
\frac{i\omega\mu B}{k_e}H_1^{(1)}(k_e a).
\tag{7.4}
$$

Сокращаем общий множитель $i\omega\mu$:

$$
\frac{A}{k_i}J_1(k_i a)
=
\frac{B}{k_e}H_1^{(1)}(k_e a).
\tag{7.5}
$$

Делим (7.5) на (7.3):

$$
\frac{J_1(k_i a)}{k_iJ_0(k_i a)}
=
\frac{H_1^{(1)}(k_e a)}{k_eH_0^{(1)}(k_e a)}.
$$

Умножаем на $k_i$ и переносим все в одну сторону:

$$
\frac{k_i}{k_e}
\frac{H_1^{(1)}(k_ea)}{H_0^{(1)}(k_ea)}
-
\frac{J_1(k_ia)}{J_0(k_ia)}
=0.
$$

Это и есть TE-характеристическое уравнение. В коде масштабированная функция Ханкеля обозначена как `hankel1e`, но отношение $H_1/H_0$ имеет тот же смысл:

$$
\left(\frac{k_i}{k_e}\right)
\left(\frac{H_1(k_ea)}{H_0(k_ea)}\right)
-
\frac{J_1(k_ia)}{J_0(k_ia)}
=0.
$$

### 7.2. TM-уравнение

Для TM-моды

$$
H_z=0,\qquad E_z\ne0.
$$

Для осесимметричной моды $n=0$ берем

$$
E_z^{(i)}(r)=A J_0(k_i r),
$$

$$
E_z^{(e)}(r)=B H_0^{(1)}(k_e r).
$$

Теперь нужна тангенциальная компонента $H_\varphi$. Из (4.10)

$$
H_\varphi=
\frac{i}{\kappa^2}
\left(
\frac{\gamma}{r}\frac{\partial H_z}{\partial\varphi}
+
\omega\varepsilon\frac{\partial E_z}{\partial r}
\right).
$$

Так как $H_z=0$ и $n=0$:

$$
H_\varphi=
\frac{i\omega\varepsilon}{\kappa^2}
\frac{\partial E_z}{\partial r}.
$$

Внутри капилляра $\varepsilon_i=\varepsilon_0$ и $\kappa^2=k_i^2$:

$$
H_\varphi^{(i)}
=
\frac{i\omega\varepsilon_0}{k_i^2}
\frac{d}{dr}\left[A J_0(k_i r)\right]
=
\frac{i\omega\varepsilon_0 A}{k_i^2}
k_iJ_0'(k_i r).
$$

Используем $J_0'(x)=-J_1(x)$:

$$
H_\varphi^{(i)}(a)
=
-\frac{i\omega\varepsilon_0 A}{k_i}
J_1(k_i a).
\tag{7.6}
$$

В металле $\varepsilon_e=\varepsilon_0 v^2$ и $\kappa^2=k_e^2$:

$$
H_\varphi^{(e)}
=
\frac{i\omega\varepsilon_0v^2}{k_e^2}
\frac{d}{dr}\left[B H_0^{(1)}(k_e r)\right]
=
\frac{i\omega\varepsilon_0v^2B}{k_e}
{H_0^{(1)}}'(k_e r).
$$

Так как ${H_0^{(1)}}'(x)=-H_1^{(1)}(x)$:

$$
H_\varphi^{(e)}(a)
=
-\frac{i\omega\varepsilon_0v^2B}{k_e}
H_1^{(1)}(k_e a).
\tag{7.7}
$$

Непрерывность $E_z$:

$$
A J_0(k_i a)
=
B H_0^{(1)}(k_e a).
\tag{7.8}
$$

Непрерывность $H_\varphi$:

$$
-\frac{i\omega\varepsilon_0 A}{k_i}J_1(k_i a)
=
-\frac{i\omega\varepsilon_0v^2B}{k_e}H_1^{(1)}(k_e a).
\tag{7.9}
$$

Сокращаем $-i\omega\varepsilon_0$:

$$
\frac{A}{k_i}J_1(k_i a)
=
\frac{v^2B}{k_e}H_1^{(1)}(k_e a).
\tag{7.10}
$$

Делим (7.10) на (7.8):

$$
\frac{J_1(k_i a)}{k_iJ_0(k_i a)}
=
\frac{v^2H_1^{(1)}(k_e a)}
{k_eH_0^{(1)}(k_e a)}.
$$

Умножаем на $k_iJ_0(k_i a)$ и переносим:

$$
v^2\frac{k_i}{k_e}
\frac{H_1^{(1)}(k_ea)}{H_0^{(1)}(k_ea)}
J_0(k_ia)
-
J_1(k_ia)
=0.
$$

Это TM-характеристическое уравнение. То же самое в форме кода:

$$
v^2
\left(\frac{k_i}{k_e}\right)
\left(\frac{H_1(k_ea)}{H_0(k_ea)}\right)
J_0(k_ia)
-
J_1(k_ia)
=0.
$$

Множитель $v^2=\varepsilon_m$ появляется из граничного условия для магнитного поля и из связи $\mathbf D=\varepsilon\mathbf E$ в металле.

### 7.3. Гибридное уравнение HE/EH

Для гибридных мод обе продольные компоненты ненулевые:

$$
E_z\ne0,\qquad H_z\ne0.
$$

Пусть азимутальная зависимость равна $\exp(in\varphi)$. Тогда внутри капилляра:

$$
E_z^{(i)}=A J_n(k_i r)e^{in\varphi},
$$

$$
H_z^{(i)}=B J_n(k_i r)e^{in\varphi}.
$$

В металле:

$$
E_z^{(e)}=C H_n^{(1)}(k_e r)e^{in\varphi},
$$

$$
H_z^{(e)}=D H_n^{(1)}(k_e r)e^{in\varphi}.
$$

Из непрерывности продольных компонент на $r=a$:

$$
A J_n(k_i a)=C H_n^{(1)}(k_e a),
\tag{7.11}
$$

$$
B J_n(k_i a)=D H_n^{(1)}(k_e a).
\tag{7.12}
$$

Отсюда внешние амплитуды выражаются через внутренние:

$$
C=A\frac{J_n(k_i a)}{H_n^{(1)}(k_e a)},
\qquad
D=B\frac{J_n(k_i a)}{H_n^{(1)}(k_e a)}.
\tag{7.13}
$$

Теперь используем тангенциальные компоненты из раздела 4. Так как

$$
\frac{\partial}{\partial\varphi}e^{in\varphi}
=in e^{in\varphi},
$$

то

$$
E_\varphi=
\frac{i}{\kappa^2}
\left(
\frac{i n\gamma}{r}E_z
-
\omega\mu\frac{\partial H_z}{\partial r}
\right)
=
-\frac{n\gamma}{\kappa^2 r}E_z
-
\frac{i\omega\mu}{\kappa^2}\frac{\partial H_z}{\partial r},
\tag{7.14}
$$

$$
H_\varphi=
\frac{i}{\kappa^2}
\left(
\frac{i n\gamma}{r}H_z
+
\omega\varepsilon\frac{\partial E_z}{\partial r}
\right)
=
-\frac{n\gamma}{\kappa^2 r}H_z
+
\frac{i\omega\varepsilon}{\kappa^2}\frac{\partial E_z}{\partial r}.
\tag{7.15}
$$

Нужно записать производные через отношения функций на границе. Для этого вводим

$$
R_J=\frac{J_{n+1}(k_i a)}{J_n(k_i a)},
\qquad
R_H=\frac{H_{n+1}^{(1)}(k_e a)}{H_n^{(1)}(k_e a)}.
\tag{7.16}
$$

Используем рекуррентное соотношение для цилиндрических функций:

$$
Z_n'(x)=\frac{n}{x}Z_n(x)-Z_{n+1}(x),
\tag{7.17}
$$

где $Z_n$ может быть $J_n$ или $H_n^{(1)}$. Поэтому

$$
\frac{J_n'(k_i a)}{J_n(k_i a)}
=
\frac{n}{k_i a}-R_J,
\tag{7.18}
$$

$$
\frac{{H_n^{(1)}}'(k_e a)}{H_n^{(1)}(k_e a)}
=
\frac{n}{k_e a}-R_H.
\tag{7.19}
$$

Теперь пишем непрерывность $E_\varphi$. Подставляем (7.14) внутрь и наружу, затем используем (7.13), чтобы убрать $C,D$. После деления на общий множитель $J_n(k_i a)e^{in\varphi}$ получаем

$$
-\frac{n\gamma}{a}
\left(
\frac{1}{k_i^2}-\frac{1}{k_e^2}
\right)A
-
i\omega\mu
\left[
\frac{1}{k_i}
\left(
\frac{n}{k_i a}-R_J
\right)
-
\frac{1}{k_e}
\left(
\frac{n}{k_e a}-R_H
\right)
\right]B
=0.
\tag{7.20}
$$

Аналогично непрерывность $H_\varphi$ дает

$$
i\omega\varepsilon_0
\left[
\frac{1}{k_i}
\left(
\frac{n}{k_i a}-R_J
\right)
-
\frac{v^2}{k_e}
\left(
\frac{n}{k_e a}-R_H
\right)
\right]A
-
\frac{n\gamma}{a}
\left(
\frac{1}{k_i^2}-\frac{1}{k_e^2}
\right)B
=0.
\tag{7.21}
$$

Уравнения (7.20)-(7.21) - это однородная система для амплитуд $A$ и $B$:

$$
\begin{pmatrix}
M_{EE} & M_{EH}\\
M_{HE} & M_{HH}
\end{pmatrix}
\begin{pmatrix}
A\\
B
\end{pmatrix}
=
\begin{pmatrix}
0\\
0
\end{pmatrix}.
\tag{7.22}
$$

Нетривиальное решение существует, только если

$$
M_{EE}M_{HH}-M_{EH}M_{HE}=0.
\tag{7.23}
$$

Покажем, как из (7.20)-(7.21) появляется компактная форма. Введем

$$
\Delta=
\frac{1}{k_i^2}-\frac{1}{k_e^2}.
\tag{7.24}
$$

Тогда коэффициенты при $A$ и $B$ в (7.20) можно записать как

$$
M_{EE}=-\frac{n\gamma}{a}\Delta,
\tag{7.25}
$$

$$
M_{EH}=-i\omega\mu a\,T_{\rm TE},
\tag{7.26}
$$

если определить

$$
T_{\rm TE}
=
n\left[
\frac{1}{(k_ia)^2}
-
\frac{1}{(k_ea)^2}
\right]
+
\frac{R_H}{k_ea}
-
\frac{R_J}{k_ia}.
\tag{7.27}
$$

Действительно,

$$
aT_{\rm TE}
=
\frac{n}{a}
\left(
\frac{1}{k_i^2}-\frac{1}{k_e^2}
\right)
+
\frac{R_H}{k_e}
-
\frac{R_J}{k_i},
$$

что совпадает со скобкой при $B$ в (7.20).

Аналогично из (7.21):

$$
M_{HH}=-\frac{n\gamma}{a}\Delta,
\tag{7.28}
$$

$$
M_{HE}=i\omega\varepsilon_0 a\,T_{\rm TM},
\tag{7.29}
$$

где

$$
T_{\rm TM}
=
n\left[
\frac{1}{(k_ia)^2}
-
\frac{v^2}{(k_ea)^2}
\right]
+
v^2\frac{R_H}{k_ea}
-
\frac{R_J}{k_ia}.
\tag{7.30}
$$

Теперь раскрываем определитель:

$$
M_{EE}M_{HH}-M_{EH}M_{HE}=0.
$$

Первое произведение:

$$
M_{EE}M_{HH}
=
\left(
-\frac{n\gamma}{a}\Delta
\right)^2
=
\frac{n^2\gamma^2}{a^2}\Delta^2.
\tag{7.31}
$$

Второе произведение:

$$
M_{EH}M_{HE}
=
\left(-i\omega\mu aT_{\rm TE}\right)
\left(i\omega\varepsilon_0 aT_{\rm TM}\right).
$$

Так как

$$
(-i)i=1,
$$

то

$$
M_{EH}M_{HE}
=
\omega^2\mu\varepsilon_0 a^2
T_{\rm TE}T_{\rm TM}.
\tag{7.32}
$$

В воздухе

$$
k_0^2=\omega^2\mu\varepsilon_0.
$$

Поэтому determinant condition принимает вид

$$
\frac{n^2\gamma^2}{a^2}\Delta^2
-
k_0^2a^2T_{\rm TE}T_{\rm TM}=0.
\tag{7.33}
$$

Делим на $k_0^2a^2$:

$$
T_{\rm TE}T_{\rm TM}
=
\frac{n^2\gamma^2}{k_0^2}
\frac{\Delta^2}{a^4}.
\tag{7.34}
$$

Но

$$
\frac{\Delta}{a^2}
=
\frac{1}{(k_ia)^2}
-
\frac{1}{(k_ea)^2}.
$$

Следовательно,

$$
T_{\rm TE}T_{\rm TM}
-
\left(\frac{n\gamma}{k_0}\right)^2
\left[
\frac{1}{(k_ia)^2}
-
\frac{1}{(k_ea)^2}
\right]^2
=0.
\tag{7.35}
$$

Это уже та же структура, которая реализована в коде.

В коде правая часть гибридного связывания записана как

$$
Q=
\left(\frac{n\gamma}{k_0}\right)^2
\left[
\frac{1}{(k_ia)^2}
-
\frac{1}{(k_ea)^2}
\right]^2.
$$

Поэтому характеристическое уравнение имеет вид

$$
T_{\rm TE}T_{\rm TM}-Q=0.
$$

В коде это дополнительно умножается на $(k_ia)^2$:

$$
\left(T_{\rm TE}T_{\rm TM}-Q\right)(k_ia)^2=0.
$$

Умножение на ненулевой множитель не меняет корни, но улучшает численный масштаб функции.

Именно для этого уравнения важно использовать азимутальный индекс $n$, а не радиальный индекс $m$. В `README.md` отмечено, что старый ноутбук в одном месте ошибочно передавал радиальный индекс вместо азимутального.

### 7.4. Численное решение

Комплексное уравнение

$$
F(\gamma)=0
$$

решается как система двух вещественных уравнений:

$$
\mathrm{Re}\,F(\beta+i\alpha_{\rm amp})=0,
$$

$$
\mathrm{Im}\,F(\beta+i\alpha_{\rm amp})=0.
$$

Начальное приближение:

$$
\gamma_0=\beta_0+i\alpha_{{\rm amp},0}.
$$

Здесь

$$
\beta_0=\sqrt{k_0^2-\left(\frac{u_0}{a}\right)^2},
$$

а $\alpha_{{\rm amp},0}$ берется из оценки потерь Маркатили, деленной на 2, потому что оценка Маркатили задает потери мощности.

После решения:

$$
n_{\rm eff}=\frac{\gamma}{k_0}.
$$

## 8. Потери: связь комплексной \(\gamma\), Маркатили и лучевой модели

### 8.1. Потери через комплексную постоянную распространения

Поле одной моды:

$$
\mathbf E_\mu(r,\varphi,z)
=c_\mu\mathbf e_\mu(r,\varphi)\exp(i\gamma_\mu z).
$$

Пусть

$$
\gamma_\mu=\beta_\mu+i\alpha_{\rm amp,\mu}.
$$

Тогда

$$
|\mathbf E_\mu(z)|^2
\propto
\exp(-2\alpha_{\rm amp,\mu}z).
$$

Значит:

$$
\alpha_{\rm pow,\mu}=2\alpha_{\rm amp,\mu}.
$$

Мощность моды на расстоянии $z$:

$$
P_\mu(z)=P_\mu(0)\exp(-\alpha_{\rm pow,\mu}z).
$$

### 8.2. Оценка Маркатили

В коде используется оценка затухания мощности для полого металлического волновода. Она соответствует результату Marcatili-Schmeltzer о том, что потери нормальных мод полого круглого волновода растут как $\lambda^2$ и падают как $a^{-3}$:

$$
\alpha_{\rm M}
=
\left(\frac{u}{2\pi}\right)^2
\frac{\lambda^2}{a^3}
\mathrm{Re}\,\nu.
$$

Параметр $\nu$ зависит от семейства моды:

$$
\nu_{\rm TE}=\frac{1}{\sqrt{v^2-1}},
$$

$$
\nu_{\rm TM}=\frac{v^2}{\sqrt{v^2-1}},
$$

$$
\nu_{\rm hybrid}
=
\frac{v^2+1}{2\sqrt{v^2-1}}.
$$

Эта формула имеет важную структуру:

$$
\alpha_{\rm M}\propto \frac{u^2\lambda^2}{a^3}.
$$

Следовательно:

- моды с большим $u$ сильнее взаимодействуют со стенкой и сильнее затухают;
- увеличение радиуса резко уменьшает потери;
- более длинная волна в этой оценке увеличивает потери как $\lambda^2$ при фиксированном радиусе и материале.

В коде амплитудное начальное приближение равно

$$
\alpha_{{\rm amp},0}
=\frac{\alpha_{\rm M}}{2}.
$$

### 8.3. Лучевая оценка потерь

Дополнительно в `attenuation.py` есть лучевая модель. Ее смысл соответствует работам [Miyagi, 1985](miyagi1985.pdf), [Matsuura et al., 1989](matsuura1989_important.pdf) и [Saito et al., 1993](saito1993_Important.pdf): для малых потерь волновая оценка затухания может быть записана в лучевой форме через коэффициент отражения от стенки и частоту столкновений луча со стенкой.

Луч, идущий под углом $\theta$ к оси капилляра, отражается от стенки. Расстояние между соседними отражениями вдоль $z$ оценивается как

$$
\Delta z\simeq \frac{2a}{\tan\theta}.
$$

Число отражений на единицу длины:

$$
N_z\simeq\frac{1}{\Delta z}
=\frac{\tan\theta}{2a}.
$$

Если средний коэффициент отражения по мощности равен $R$, то потери за одно отражение равны $1-R$. При малых потерях коэффициент затухания мощности:

$$
\alpha_{\rm ray}
\simeq
(1-R)\frac{\tan\theta}{2a}.
$$

Именно это используется в коде:

$$
\alpha_{\rm ray}(\theta)
=
\left[1-R_{\rm rough}(\theta)\right]\frac{\tan\theta}{2a}.
$$

Для плоской границы воздух-металл задается угол к нормали

$$
\psi=\frac{\pi}{2}-\theta.
$$

Коэффициенты Френеля:

$$
r_s=
\frac{\cos\psi-v\sqrt{1-(\sin\psi/v)^2}}
{\cos\psi+v\sqrt{1-(\sin\psi/v)^2}},
$$

$$
r_p=
\frac{\sqrt{1-(\sin\psi/v)^2}-v\cos\psi}
{\sqrt{1-(\sin\psi/v)^2}+v\cos\psi}.
$$

Средний коэффициент отражения:

$$
R=\frac{|r_s|^2+|r_p|^2}{2}.
$$

Если задана среднеквадратичная шероховатость стенки $\sigma$, код умножает $R$ на фактор

$$
\exp\left[
-
\left(
\frac{4\pi\sigma\sin\theta}{\lambda}
\right)^2
\right].
$$

По умолчанию $\sigma=0$, то есть шероховатость выключена.

В [Matsuura et al., 1989](matsuura1989_important.pdf) отдельно подчеркивается, что для металлических волноводов поверхностные нерегулярности существенно влияют на предсказание потерь. В нашем коде это отражено только простым множителем шероховатости; это грубое приближение, а не полноценная модель реальной поверхности.

## 9. Входной гауссов пучок

Во входной плоскости $z=0$ поле пучка задается как гауссова огибающая с плоским фазовым наклоном:

$$
E_{\rm in}(x,y)
=
\mathbf e_p
\exp\left[
-
\frac{(x-x_0)^2+(y-y_0)^2}{w_0^2}
\right]
\exp\left[
i k_0(\sin\theta_x\,x+\sin\theta_y\,y)
\right].
$$

Здесь:

- $w_0$ - радиус пучка;
- $(x_0,y_0)$ - смещение пятна относительно центра капилляра;
- $\theta_x,\theta_y$ - наклоны по двум поперечным осям;
- $\mathbf e_p=(p_x,p_y)$ - поперечная поляризация.

В коде, если $w_0$ явно не задан, используется

$$
w_0=0.3a.
$$

Поперечный волновой вектор пучка:

$$
k_x=k_0\sin\theta_x,\qquad
k_y=k_0\sin\theta_y,
$$

$$
k_\perp=\sqrt{k_x^2+k_y^2}.
$$

Если наклон задается полярным углом $\theta$, то

$$
k_\perp=k_0\sin\theta.
$$

В полярных координатах при центрированном пучке:

$$
E_{\rm in}(r,\varphi)
=
\mathbf e_p
\exp\left(-\frac{r^2}{w_0^2}\right)
\exp\left[
i k_\perp r\cos(\varphi-\varphi_k)
\right],
$$

где $\varphi_k$ - азимут направления наклона.

## 10. Почему наклонный пучок возбуждает высокие моды

Мода с параметром $u_\mu$ имеет поперечное волновое число

$$
k_{\perp,\mu}=\frac{u_\mu}{a}.
$$

Входной пучок имеет поперечное волновое число

$$
k_\perp=k_0\sin\theta.
$$

Максимальное возбуждение ожидается при согласовании:

$$
\frac{u_\mu}{a}\simeq k_0\sin\theta.
$$

Отсюда центральное значение модального пакета:

$$
u_{\rm target}=k_0a\sin\theta.
$$

Это одна из ключевых формул расчета.

Для параметров по умолчанию:

$$
k_0a\approx1178.
$$

При $\theta=15^\circ$:

$$
u_{\rm target}\approx1178\sin15^\circ\approx305.
$$

При $\theta=30^\circ$:

$$
u_{\rm target}\approx1178\sin30^\circ\approx589.
$$

Следовательно, наклонный пучок под углами десятки градусов не может корректно описываться только несколькими низшими модами с $u\sim1\ldots20$. Нужно выбирать моды около большого $u_{\rm target}$.

Эта часть является развитием стандартной модальной картины Marcatili-Schmeltzer под конкретную задачу наклонного гауссова ввода: вместо отбора по малым индексам $n,m$ код отбирает моды по согласованию поперечного волнового числа.

## 11. Вывод ширины окна по \(u\)

Ширина возбуждаемого пакета по $u$ определяется угловым спектром гауссова пучка.

Рассмотрим одномерный гауссов множитель

$$
f(x)=\exp\left(-\frac{x^2}{w_0^2}\right).
$$

Его фурье-образ по поперечному волновому числу имеет вид

$$
\tilde f(k_x)\propto
\exp\left(-\frac{w_0^2 k_x^2}{4}\right).
$$

Если пучок наклонен, спектр сдвигается к $k_x=k_{\perp,0}$:

$$
\tilde f(k_x)\propto
\exp\left[
-
\frac{w_0^2(k_x-k_{\perp,0})^2}{4}
\right].
$$

Мощность пропорциональна квадрату амплитуды:

$$
|\tilde f(k_x)|^2
\propto
\exp\left[
-
\frac{w_0^2(k_x-k_{\perp,0})^2}{2}
\right].
$$

Пусть мы хотим оставить моды, для которых относительная спектральная мощность не меньше $p_{\min}$. Тогда

$$
\exp\left(-\frac{w_0^2\Delta k_\perp^2}{2}\right)
=p_{\min}.
$$

Берем логарифм:

$$
-\frac{w_0^2\Delta k_\perp^2}{2}
=\ln p_{\min}.
$$

Так как $\ln p_{\min}<0$:

$$
\Delta k_\perp
=
\frac{\sqrt{2\ln(1/p_{\min})}}{w_0}.
$$

Переход от $k_\perp$ к $u$ задается формулой

$$
u=ak_\perp.
$$

Поэтому

$$
\Delta u
=
a\Delta k_\perp
=
\frac{a}{w_0}
\sqrt{2\ln(1/p_{\min})}.
$$

В коде:

$$
\Delta u
=
\frac{a}{w_0}
\sqrt{2\ln(1/p_{\min})}.
$$

Окно отбора:

$$
u_{\min}=\max(0,u_{\rm target}-\Delta u),
$$

$$
u_{\max}=\min(k_0a,u_{\rm target}+\Delta u).
$$

## 12. Угловые гармоники и формула Якоби-Ангера

Наклонная плоская фаза в цилиндрических координатах:

$$
\exp\left[
i k_\perp r\cos(\varphi-\varphi_k)
\right].
$$

Используем формулу Якоби-Ангера:

$$
\exp(i x\cos\phi)
=
\sum_{q=-\infty}^{\infty}
i^q J_q(x)\exp(iq\phi).
$$

В нашей задаче:

$$
x=k_\perp r,\qquad
\phi=\varphi-\varphi_k.
$$

Поэтому

$$
\exp\left[
i k_\perp r\cos(\varphi-\varphi_k)
\right]
=
\sum_{q=-\infty}^{\infty}
i^qJ_q(k_\perp r)
\exp[iq(\varphi-\varphi_k)].
$$

Это показывает, что наклонный пучок содержит много азимутальных гармоник $q$.

Функция $J_q(x)$ мала, если порядок $q$ значительно больше аргумента $x$. Основная область пучка имеет $r\sim w_0$ для центрированного пучка. Поэтому грубо:

$$
q\lesssim k_\perp w_0.
$$

Если пучок смещен на расстояние

$$
r_0=\sqrt{x_0^2+y_0^2},
$$

то значимая область поля находится около $r\sim r_0+w_0$. Поэтому оценка расширяется:

$$
q_{\max}\sim k_\perp(r_0+w_0).
$$

В коде используется более практичная формула:

$$
q_{\rm estimate}
=
k_\perp(r_0+F w_0),
$$

$$
q_{\max}
=
\left\lceil q_{\rm estimate}+q_{\rm margin}\right\rceil,
$$

где по умолчанию $F=1$ и $q_{\rm margin}=4$.

Также накладывается ограничение:

$$
q_{\max}\le \lceil u_{\max}\rceil+q_{\rm margin}.
$$

## 13. Отбор кандидатных мод

Алгоритм отбора мод делает две вещи:

1. Выбирает только те бесселевы корни, которые попали в окно $[u_{\min},u_{\max}]$.
2. Ограничивает азимутальные порядки сверху величиной $q_{\max}$.

Для TE и TM:

$$
\mathrm{TE}_{0,m}:\quad u=j_{1,m},
$$

$$
\mathrm{TM}_{0,m}:\quad u=j_{0,m}.
$$

Для гибридных мод используется связь между семейным индексом $n$ и порядком поперечного профиля $q$:

$$
\mathrm{HE}_{n,m}:\quad q=n-1,\qquad u=j_{q,m},
$$

$$
\mathrm{EH}_{n,m}:\quad q=n+1,\qquad u=j_{q,m}.
$$

Отсюда:

$$
\mathrm{HE}: n=q+1,
$$

$$
\mathrm{EH}: n=q-1.
$$

В коде для каждого $q$ перебираются нули $J_q$ в окне $u$ и создаются соответствующие `ModeSpec`.

Для каждой моды также вычисляется модальный угол:

$$
\theta_{\rm mode}
=
\arcsin\left(\frac{u}{k_0a}\right).
$$

Это удобно для графиков и диагностики: входной угол должен попадать в область модальных углов выбранных мод.

## 14. Поперечные профили, используемые в проекции

Точный векторный профиль металлического волновода сложен. Для разложения входного поля в коде используются упрощенные поперечные профили на основе функций Бесселя.

Обозначим

$$
\rho=\frac{r}{a}.
$$

### 14.1. TE-профиль

В коде:

$$
E_x=-J_1(u\rho)\sin\varphi,
$$

$$
E_y=J_1(u\rho)\cos\varphi.
$$

То есть поле направлено по азимуту:

$$
\mathbf e_{\rm TE}
=J_1(u\rho)\,\hat{\boldsymbol\varphi}.
$$

### 14.2. TM-профиль

В коде:

$$
E_x=J_1(u\rho)\cos\varphi,
$$

$$
E_y=J_1(u\rho)\sin\varphi.
$$

То есть поле направлено радиально:

$$
\mathbf e_{\rm TM}
=J_1(u\rho)\,\hat{\mathbf r}.
$$

### 14.3. HE-профили

Для HE:

$$
q=n-1.
$$

Косинусная ориентация:

$$
E_x=J_q(u\rho)\cos(q\varphi),
$$

$$
E_y=-J_q(u\rho)\sin(q\varphi).
$$

Синусная ориентация:

$$
E_x=J_q(u\rho)\sin(q\varphi),
$$

$$
E_y=J_q(u\rho)\cos(q\varphi).
$$

### 14.4. EH-профили

Для EH:

$$
q=n+1.
$$

Косинусная ориентация:

$$
E_x=J_q(u\rho)\cos(q\varphi),
$$

$$
E_y=J_q(u\rho)\sin(q\varphi).
$$

Синусная ориентация:

$$
E_x=J_q(u\rho)\sin(q\varphi),
$$

$$
E_y=-J_q(u\rho)\cos(q\varphi).
$$

Для гибридных мод обе ориентации добавляются в базис, потому что при смещении или наклоне входного пучка может возбуждаться любая линейная комбинация этих двух вырожденных профилей.

## 15. Нормировка мод и скалярное произведение

Для поперечных полей используется скалярное произведение

$$
\langle \mathbf f,\mathbf g\rangle
=
\int_{r<a}
\left(f_x^*g_x+f_y^*g_y\right)\,dA.
$$

В цилиндрических координатах:

$$
dA=r\,dr\,d\varphi.
$$

Норма профиля:

$$
\|\mathbf e_\mu\|
=
\sqrt{\langle\mathbf e_\mu,\mathbf e_\mu\rangle}.
$$

Нормированный профиль:

$$
\tilde{\mathbf e}_\mu
=
\frac{\mathbf e_\mu}{\|\mathbf e_\mu\|}.
$$

В коде нормировка считается численно на декартовой сетке:

$$
\|\mathbf e_\mu\|^2
\approx
\sum_{r_j<a}
\left(|E_x(x_j,y_j)|^2+|E_y(x_j,y_j)|^2\right)\Delta A.
$$

Входная мощность в условных единицах:

$$
P_{\rm in}
=
\int_{r<a}
\left(|E_x^{\rm in}|^2+|E_y^{\rm in}|^2\right)dA.
$$

Численно:

$$
P_{\rm in}
\approx
\sum_{r_j<a}
\left(|E_x^{\rm in}(x_j,y_j)|^2+|E_y^{\rm in}(x_j,y_j)|^2\right)\Delta A.
$$

## 16. Модальное разложение как задача наименьших квадратов

Мы хотим приблизить входное поле суммой мод:

$$
\mathbf E_{\rm in}(x,y)
\approx
\sum_{\mu}c_\mu\tilde{\mathbf e}_\mu(x,y).
$$

Если моды были бы строго ортонормированы, коэффициент находился бы простым проектированием:

$$
c_\mu=\langle \tilde{\mathbf e}_\mu,\mathbf E_{\rm in}\rangle.
$$

Но в численной модели профили не являются идеально ортогональными, особенно для усеченного базиса и приближенных гибридных профилей. Поэтому код решает задачу наименьших квадратов.

Пусть вектор $y$ содержит значения входного поля на сетке:

$$
y=
\begin{pmatrix}
E_x^{\rm in}(x_1,y_1)\sqrt{\Delta A}\\
\vdots\\
E_x^{\rm in}(x_N,y_N)\sqrt{\Delta A}\\
E_y^{\rm in}(x_1,y_1)\sqrt{\Delta A}\\
\vdots\\
E_y^{\rm in}(x_N,y_N)\sqrt{\Delta A}
\end{pmatrix}.
$$

Матрица $A$ содержит нормированные профили:

$$
A=
\begin{pmatrix}
| & | & & |\\
e_1 & e_2 & \cdots & e_M\\
| & | & & |
\end{pmatrix}.
$$

Ищется вектор коэффициентов $c$:

$$
Ac\approx y.
$$

Задача:

$$
c=\arg\min_c\|Ac-y\|^2.
$$

Если $A^\dagger A$ невырождена, формальное решение:

$$
c=(A^\dagger A)^{-1}A^\dagger y.
$$

На практике используется `numpy.linalg.lstsq`, то есть устойчивое численное решение.

Мощность, восстановленная модальным базисом:

$$
P_{\rm coupled}=\|Ac\|^2.
$$

Невосстановленная мощность:

$$
P_{\rm residual}=P_{\rm in}-P_{\rm coupled}.
$$

Для диагностики часто используется величина

$$
\eta_\mu=\frac{|c_\mu|^2}{P_{\rm in}}.
$$

Если профили близки к ортонормированным, $\eta_\mu$ можно интерпретировать как долю мощности в профиле. В общем случае это диагностическая величина, а не строгая энергетическая декомпозиция.

Для физической моды с двумя вырожденными ориентациями код складывает веса ориентаций:

$$
\eta_{\mu,\rm total}
=
\sum_{s\in\{c,s\}}
\frac{|c_{\mu s}|^2}{P_{\rm in}}.
$$

## 17. Быстрая оценка возбуждения в полярных координатах

Для предварительного отбора мод используется грубая проекция на полярной сетке. Входное поле:

$$
E_x=p_x
\exp\left[
-
\frac{(x-x_0)^2+(y-y_0)^2}{w_0^2}
\right]
\exp[i(k_xx+k_yy)],
$$

$$
E_y=p_y
\exp\left[
-
\frac{(x-x_0)^2+(y-y_0)^2}{w_0^2}
\right]
\exp[i(k_xx+k_yy)].
$$

В полярных координатах:

$$
x=a\rho\cos\varphi,\qquad
y=a\rho\sin\varphi.
$$

Интеграл для коэффициента имеет вид

$$
c_\mu
=
\int_0^1\int_0^{2\pi}
\mathbf e_\mu^*(\rho,\varphi)\cdot
\mathbf E_{\rm in}(\rho,\varphi)
a^2\rho\,d\varphi\,d\rho.
$$

Численно радиальная часть считается квадратурой Гаусса-Лежандра по $\rho$, а угловая часть равномерной сеткой по $\varphi$.

Для центрированного пучка угловой интеграл можно упростить аналитически. Из формулы Якоби-Ангера:

$$
\int_0^{2\pi}
\exp[i k_\perp r\cos(\varphi-\varphi_k)]
\cos(q\varphi)\,d\varphi
=
2\pi i^q J_q(k_\perp r)\cos(q\varphi_k).
$$

Аналогично

$$
\int_0^{2\pi}
\exp[i k_\perp r\cos(\varphi-\varphi_k)]
\sin(q\varphi)\,d\varphi
=
2\pi i^q J_q(k_\perp r)\sin(q\varphi_k).
$$

Тогда коэффициенты сводятся к радиальным интегралам вида

$$
I_{\mu q}
=
a^2
\int_0^1
J_q(u_\mu\rho)
J_q(u_{\rm target}\rho)
\exp\left[-\frac{(a\rho)^2}{w_0^2}\right]
\rho\,d\rho.
$$

Эта формула объясняет, почему максимум возникает при

$$
u_\mu\simeq u_{\rm target}.
$$

Произведение двух функций Бесселя дает большой вклад, когда их осцилляции согласованы.

## 18. Распространение модального поля

После нахождения коэффициентов поле на расстоянии $z$:

$$
\mathbf E_\perp(r,\varphi,z)
=
\sum_\mu
c_\mu\tilde{\mathbf e}_\mu(r,\varphi)
\exp(i\gamma_\mu z).
$$

С учетом

$$
\gamma_\mu=\beta_\mu+i\alpha_{{\rm amp},\mu}
$$

получаем

$$
\mathbf E_\perp(r,\varphi,z)
=
\sum_\mu
c_\mu\tilde{\mathbf e}_\mu(r,\varphi)
\exp(i\beta_\mu z)
\exp(-\alpha_{{\rm amp},\mu}z).
$$

Интенсивность:

$$
I(r,\varphi,z)
=
\left|
\mathbf E_\perp(r,\varphi,z)
\right|^2.
$$

Раскрывая квадрат:

$$
I
=
\sum_\mu |c_\mu|^2|\tilde{\mathbf e}_\mu|^2
\exp(-2\alpha_{{\rm amp},\mu}z)
$$

$$
+
\sum_{\mu\ne\nu}
c_\mu c_\nu^*
\tilde{\mathbf e}_\mu\cdot\tilde{\mathbf e}_\nu^*
\exp[i(\beta_\mu-\beta_\nu)z]
\exp[-(\alpha_{{\rm amp},\mu}+\alpha_{{\rm amp},\nu})z].
$$

Первый член - сумма отдельных интенсивностей мод. Второй член - межмодовая интерференция. Именно он создает изменение поперечной картины вдоль капилляра.

Если мод много и их $\beta_\mu$ заметно различаются, фазы быстро расходятся, и картина меняется на коротком продольном масштабе.

## 19. Модальная корреляция и длина расфазировки

Для компактной оценки продольного масштаба используется распределение постоянных распространения $\beta_\mu$ с весами $w_\mu$.

В качестве весов берутся модальные мощности или грубые оценки мощностей:

$$
w_\mu\ge0.
$$

Среднее:

$$
\bar\beta
=
\frac{\sum_\mu w_\mu\beta_\mu}
{\sum_\mu w_\mu}.
$$

Дисперсия:

$$
\sigma_\beta^2
=
\frac{\sum_\mu w_\mu(\beta_\mu-\bar\beta)^2}
{\sum_\mu w_\mu}.
$$

Характерная длина расфазировки:

$$
L_\phi=\frac{2\pi}{\sigma_\beta}.
$$

Эта формула получается из условия, что типичный набег относительной фазы между модами за длину $L_\phi$ порядка $2\pi$:

$$
\sigma_\beta L_\phi\sim2\pi.
$$

Для более детальной диагностики вводится модальная корреляция:

$$
C(z)
=
\frac{
\left|
\sum_\mu
w_\mu
\exp[i(\beta_\mu-\bar\beta)z]
\right|^2
}
{\left(\sum_\mu w_\mu\right)^2}.
$$

При $z=0$:

$$
C(0)=1.
$$

Если фазы мод разошлись, сумма комплексных фаз уменьшается, и $C(z)$ падает. Локальные пики $C(z)$ соответствуют расстояниям, где значимая часть модального пакета частично снова оказывается в фазе.

Такой физический механизм хорошо согласуется с наблюдением field regeneration у [Jenkins, Devereux, 1992](jenkins1992.pdf): если входной TEM00-пучок возбуждает несколько EH-мод, то при восстановлении их относительной фазы поперечное поле снова становится похожим на входное, а между такими точками может принимать другую форму.

В коде из $C(z)$ извлекаются:

$$
z_{\rm first\ peak},
$$

$$
z_{\rm best\ peak},
$$

и

$$
L_\phi=\frac{2\pi}{\sigma_\beta}.
$$

## 20. Почему период уменьшается с углом

Используем приближение

$$
\beta(u)=\sqrt{k_0^2-\left(\frac{u}{a}\right)^2}.
$$

Найдем производную:

$$
\frac{d\beta}{du}
=
\frac{1}{2}
\left[
k_0^2-\left(\frac{u}{a}\right)^2
\right]^{-1/2}
\left(-\frac{2u}{a^2}\right).
$$

Отсюда:

$$
\frac{d\beta}{du}
=
-
\frac{u}{a^2\beta}.
$$

Но

$$
u=k_0a\sin\theta,
$$

$$
\beta=k_0\cos\theta.
$$

Подставляем:

$$
\frac{d\beta}{du}
=
-
\frac{k_0a\sin\theta}
{a^2 k_0\cos\theta}
=
-
\frac{\tan\theta}{a}.
$$

Если ширина пакета по $u$ равна

$$
\Delta u\sim\frac{a}{w_0},
$$

то ширина по $\beta$:

$$
\sigma_\beta
\sim
\left|\frac{d\beta}{du}\right|\Delta u
\sim
\frac{\tan\theta}{a}\frac{a}{w_0}
=
\frac{\tan\theta}{w_0}.
$$

Тогда

$$
L_\phi
\sim
\frac{2\pi}{\sigma_\beta}
\sim
\frac{2\pi w_0}{\tan\theta}.
$$

Это важная физическая оценка:

- при большем угле входа $\theta$ картина меняется быстрее;
- при большем радиусе пучка $w_0$ угловой спектр уже, поэтому картина меняется медленнее.

## 21. Времена пролета и импульсная модель

Для импульсов в текущем коде учитывается только межмодовая задержка. Частотная дисперсия внутри каждой моды не учитывается.

Стартуем с беззатухательной дисперсии моды:

$$
\beta(\omega)
=
\sqrt{
\left(\frac{\omega}{c}\right)^2
-
\left(\frac{u}{a}\right)^2
}.
$$

Групповая скорость:

$$
v_g=\frac{d\omega}{d\beta}
=
\left(\frac{d\beta}{d\omega}\right)^{-1}.
$$

Найдем производную:

$$
\frac{d\beta}{d\omega}
=
\frac{1}{2}
\left[
\left(\frac{\omega}{c}\right)^2
-
\left(\frac{u}{a}\right)^2
\right]^{-1/2}
\frac{2\omega}{c^2}.
$$

Так как

$$
\beta=
\sqrt{
\left(\frac{\omega}{c}\right)^2
-
\left(\frac{u}{a}\right)^2
},
$$

то

$$
\frac{d\beta}{d\omega}
=
\frac{\omega}{c^2\beta}.
$$

Следовательно:

$$
v_g
=
\frac{c^2\beta}{\omega}.
$$

Но

$$
k_0=\frac{\omega}{c},
$$

поэтому

$$
v_g
=
c\frac{\beta}{k_0}.
$$

Подставляем

$$
\beta=k_0
\sqrt{
1-
\left(\frac{u}{k_0a}\right)^2
}.
$$

Получаем:

$$
\frac{v_g}{c}
=
\sqrt{
1-
\left(\frac{u}{k_0a}\right)^2
}.
$$

Именно эта формула используется в коде.

Время прихода моды на расстоянии $z$:

$$
t_\mu(z)=\frac{z}{v_{g,\mu}}.
$$

Избыточная задержка относительно распространения со скоростью света:

$$
\Delta t_\mu(z)
=
t_\mu(z)-\frac{z}{c}.
$$

Для дельта-импульса каждая мода дает отдельный приход с весом

$$
w_\mu(z)=w_\mu(0)\exp(-\alpha_{{\rm pow},\mu}z).
$$

Для гауссова импульса по времени используется интенсивность

$$
I_\mu(t,z)
=
w_\mu(0)\exp(-\alpha_{{\rm pow},\mu}z)
\exp\left[
-
\frac{1}{2}
\left(
\frac{t-t_0-z/v_{g,\mu}}{\sigma_t}
\right)^2
\right].
$$

Связь между FWHM и $\sigma_t$:

$$
\sigma_t
=
\frac{\mathrm{FWHM}}
{2\sqrt{2\ln2}}.
$$

Полная временная интенсивность в модели:

$$
I(t,z)
=
\sum_\mu I_\mu(t,z).
$$

Важные ограничения этой модели:

- не учитывается спектральное расплытие внутри одной моды;
- не учитывается когерентная интерференция несущей частоты во временном сигнале;
- учитываются только разные групповые скорости мод и их потери.

## 22. Полная цепочка расчета

Ниже вся цепочка в порядке, в котором она фактически используется.

### 22.1. Задать параметры волновода

$$
\lambda,\quad d,\quad a=d/2,\quad \varepsilon_m,\quad v=\sqrt{\varepsilon_m}.
$$

$$
k_0=\frac{2\pi}{\lambda}.
$$

### 22.2. Задать входной пучок

$$
w_0,\quad x_0,\quad y_0,\quad \theta_x,\quad \theta_y,\quad p_x,\quad p_y.
$$

$$
k_x=k_0\sin\theta_x,\qquad
k_y=k_0\sin\theta_y,
$$

$$
k_\perp=\sqrt{k_x^2+k_y^2}.
$$

### 22.3. Найти центр модального пакета

$$
u_{\rm target}=ak_\perp.
$$

Если используется один полярный угол:

$$
u_{\rm target}=k_0a\sin\theta.
$$

### 22.4. Найти окно по \(u\)

$$
\Delta u
=
\frac{a}{w_0}
\sqrt{2\ln(1/p_{\min})}.
$$

$$
u_{\min}=u_{\rm target}-\Delta u,
\qquad
u_{\max}=u_{\rm target}+\Delta u.
$$

После обрезки:

$$
0\le u\le k_0a.
$$

### 22.5. Найти диапазон азимутальных порядков

$$
q_{\max}
\simeq
\left\lceil
k_\perp(r_0+Fw_0)+q_{\rm margin}
\right\rceil.
$$

### 22.6. Сгенерировать кандидатные моды

Выбираются бесселевы корни в окне:

$$
j_{\ell,m}\in[u_{\min},u_{\max}].
$$

Связь семейств:

$$
\mathrm{TE}_{0,m}: u=j_{1,m},
$$

$$
\mathrm{TM}_{0,m}: u=j_{0,m},
$$

$$
\mathrm{HE}_{q+1,m}: u=j_{q,m},
$$

$$
\mathrm{EH}_{q-1,m}: u=j_{q,m}.
$$

### 22.7. Решить характеристические уравнения

Для каждой моды найти

$$
\gamma_\mu=\beta_\mu+i\alpha_{{\rm amp},\mu}
$$

из TE, TM или гибридного уравнения.

Затем:

$$
n_{{\rm eff},\mu}=\frac{\gamma_\mu}{k_0},
$$

$$
\alpha_{{\rm pow},\mu}=2\,\mathrm{Im}\,\gamma_\mu.
$$

### 22.8. Построить поперечные профили и разложить входное поле

Построить $\tilde{\mathbf e}_\mu(x,y)$, затем решить:

$$
c=\arg\min_c\|Ac-y\|^2.
$$

Диагностики:

$$
P_{\rm in}=\|y\|^2,
$$

$$
P_{\rm coupled}=\|Ac\|^2,
$$

$$
P_{\rm residual}=P_{\rm in}-P_{\rm coupled}.
$$

Модальная доля:

$$
\eta_\mu=\frac{|c_\mu|^2}{P_{\rm in}}.
$$

### 22.9. Распространить поле

$$
\mathbf E(r,\varphi,z)
=
\sum_\mu
c_\mu\tilde{\mathbf e}_\mu(r,\varphi)
\exp(i\gamma_\mu z).
$$

Интенсивность:

$$
I(r,\varphi,z)=|\mathbf E(r,\varphi,z)|^2.
$$

### 22.10. Оценить продольную расфазировку

$$
\bar\beta
=
\frac{\sum_\mu w_\mu\beta_\mu}{\sum_\mu w_\mu},
$$

$$
\sigma_\beta^2
=
\frac{\sum_\mu w_\mu(\beta_\mu-\bar\beta)^2}
{\sum_\mu w_\mu}.
$$

$$
L_\phi=\frac{2\pi}{\sigma_\beta}.
$$

$$
C(z)=
\frac{
\left|
\sum_\mu w_\mu e^{i(\beta_\mu-\bar\beta)z}
\right|^2
}
{(\sum_\mu w_\mu)^2}.
$$

### 22.11. Оценить импульсные задержки

$$
\frac{v_{g,\mu}}{c}
=
\sqrt{
1-
\left(\frac{u_\mu}{k_0a}\right)^2
}.
$$

$$
t_\mu(z)=\frac{z}{v_{g,\mu}}.
$$

$$
\Delta t_\mu(z)=t_\mu(z)-\frac{z}{c}.
$$

Вес после распространения:

$$
w_\mu(z)=w_\mu(0)\exp(-\alpha_{{\rm pow},\mu}z).
$$

## 23. Основные физические выводы

1. Переменная $u$ важнее самого радиального индекса $m$, потому что именно $u/a$ является поперечным волновым числом моды.

2. Наклонный пучок возбуждает моды около

$$
u_{\rm target}=k_0a\sin\theta.
$$

3. При больших углах $u_{\rm target}$ велик, поэтому расчет должен включать высокие моды.

4. Ширина модального пакета по $u$ задается угловым спектром пучка:

$$
\Delta u\sim\frac{a}{w_0}.
$$

5. Число значимых азимутальных гармоник растет как

$$
q\sim k_\perp w_0.
$$

6. Смещение пучка расширяет угловой состав, потому что входное поле перестает быть симметричным относительно оси волновода.

7. Продольная картина интенсивности определяется межмодовой интерференцией:

$$
\exp[i(\beta_\mu-\beta_\nu)z].
$$

8. Характерная длина изменения картины связана с разбросом $\beta$:

$$
L_\phi=\frac{2\pi}{\sigma_\beta}.
$$

9. При росте угла

$$
\frac{d\beta}{du}\simeq-\frac{\tan\theta}{a},
$$

поэтому та же ширина по $u$ дает больший разброс по $\beta$, и картина меняется быстрее.

10. В импульсной модели разные моды приходят в разное время из-за разных групповых скоростей:

$$
\frac{v_g}{c}
=
\sqrt{1-\left(\frac{u}{k_0a}\right)^2}.
$$

## 24. Соответствие формулам в файлах проекта

Основные места в коде:

- `waveguide_practice/config.py`: параметры $\lambda$, $d$, $a$, $k_0$, $\varepsilon_m$, $v$, параметры гауссова пучка.
- `waveguide_practice/cylindrical_modes.py`: характеристические уравнения TE/TM/HE/EH, бесселевы начальные приближения, решение комплексной $\gamma$, $n_{\rm eff}$, $\alpha_{\rm pow}$.
- `waveguide_practice/attenuation.py`: оценки Френеля, шероховатость, лучевое затухание, формула Маркатили.
- `waveguide_practice/projection.py`: гауссов входной пучок, поперечные профили мод, нормировка, least-squares разложение, распространение поля.
- `waveguide_practice/angular_analysis.py`: окно по $u$, оценка $q_{\max}$, генерация кандидатных мод, полярная квадратура, $C(z)$, $L_\phi$, угловые и смещенные sweep-расчеты.
- `waveguide_practice/pulse.py`: групповая скорость, задержки, гауссов импульс, дельта-приходы.

Соответствие источникам:

- Модальные уравнения, семейства HE/EH и масштаб потерь: [Marcatili, Schmeltzer, 1964](marcatili1964.pdf).
- Лучевая трактовка потерь и связь с волновым расчетом: [Miyagi, 1985](miyagi1985.pdf).
- Мультимодовая передача, угловое распределение и коэффициенты отражения: [Matsuura et al., 1989](matsuura1989_important.pdf), [Saito et al., 1993](saito1993_Important.pdf).
- Регенерация поля и продольная фазовая периодичность: [Jenkins, Devereux, 1992](jenkins1992.pdf).
- Потери связи и низшая гибридная мода EH11 в резонаторной постановке: [Abrams, 1972](abrams1972.pdf).
- Прикладной контекст серебряного Raman/SERS-волноводного резонатора: [Khannanov, Vankov, Kulik et al., 2021](2021_Khannanov_Vankov_Kulik.pdf).

## 25. Краткая таблица формул

| Величина | Формула |
|---|---|
| Волновое число | $k_0=2\pi/\lambda$ |
| Радиус | $a=d/2$ |
| Показатель металла | $v=\sqrt{\varepsilon_m}$ |
| Поперечное число моды | $k_{\perp,\mu}=u_\mu/a$ |
| Продольная постоянная без потерь | $\beta_\mu\simeq\sqrt{k_0^2-(u_\mu/a)^2}$ |
| Модальный угол | $\theta_\mu=\arcsin[u_\mu/(k_0a)]$ |
| Центр возбуждения | $u_{\rm target}=k_0a\sin\theta$ |
| Ширина окна | $\Delta u=(a/w_0)\sqrt{2\ln(1/p_{\min})}$ |
| Азимутальный порядок | $q_{\max}\sim k_\perp(r_0+w_0)$ |
| Комплексная постоянная | $\gamma=\beta+i\alpha_{\rm amp}$ |
| Затухание мощности | $\alpha_{\rm pow}=2\,\mathrm{Im}\,\gamma$ |
| Маркатили | $\alpha_{\rm M}=(u/2\pi)^2(\lambda^2/a^3)\mathrm{Re}\,\nu$ |
| Лучевая модель | $\alpha_{\rm ray}=(1-R)\tan\theta/(2a)$ |
| Модальное поле | $\mathbf E(z)=\sum_\mu c_\mu\mathbf e_\mu e^{i\gamma_\mu z}$ |
| Модальная корреляция | $C(z)=|\sum_\mu w_\mu e^{i(\beta_\mu-\bar\beta)z}|^2/(\sum_\mu w_\mu)^2$ |
| Длина расфазировки | $L_\phi=2\pi/\sigma_\beta$ |
| Групповая скорость | $v_g/c=\sqrt{1-[u/(k_0a)]^2}$ |
| Время прихода | $t_\mu=z/v_{g,\mu}$ |

## 26. Что еще можно добавить в следующей версии

Этот файл уже покрывает текущий расчет и основные статьи из корня папки. Для версии, предназначенной прямо для текста практики или статьи, полезно добавить:

1. Рисунок геометрии: капилляр, радиус $a$, входной угол $\theta$, смещение $r_0$.
2. Рисунок связи $u_{\rm target}=k_0a\sin\theta$ с угловым спектром пучка.
3. Иллюстрацию функций Бесселя и смысл нулей $j_{\ell,m}$.
4. Таблицу численных параметров для конкретных случаев из ноутбука.
5. Отдельную главу по SERS/плазмонному усилению, если расчет будет связываться не только с распространением мод в капилляре, но и с усилением Raman-сигнала на серебряной поверхности.

## 27. Литература

1. E. A. J. Marcatili, R. A. Schmeltzer, "Hollow Metallic and Dielectric Waveguides for Long Distance Optical Transmission and Lasers", Bell System Technical Journal, 1964. Локальный файл: [marcatili1964.pdf](marcatili1964.pdf).
2. M. Miyagi, "Waveguide-Loss Evaluation in Circular Hollow Waveguides and Its Ray-Optical Treatment", Journal of Lightwave Technology, Vol. LT-3, No. 2, April 1985. Локальный файл: [miyagi1985.pdf](miyagi1985.pdf).
3. Y. Matsuura, M. Saito, M. Miyagi, A. Hongo, "Loss characteristics of circular hollow waveguides for incoherent infrared light", Journal of the Optical Society of America A, Vol. 6, No. 3, March 1989. Локальный файл: [matsuura1989_important.pdf](matsuura1989_important.pdf).
4. M. Saito, S. Sato, M. Miyagi, "Loss characteristics of infrared hollow waveguides in multimode transmission", Journal of the Optical Society of America A, Vol. 10, No. 2, February 1993. Локальный файл: [saito1993_Important.pdf](saito1993_Important.pdf).
5. R. L. Abrams, "Coupling Losses in Hollow Waveguide Laser Resonators", IEEE Journal of Quantum Electronics, Vol. QE-8, No. 11, November 1972. Локальный файл: [abrams1972.pdf](abrams1972.pdf).
6. R. M. Jenkins, R. W. J. Devereux, "Effect of field regeneration on the TEM00 transmission characteristics of a circular-section waveguide", 1992. Локальный файл: [jenkins1992.pdf](jenkins1992.pdf).
7. M. N. Khannanov, A. B. Vankov, V. E. Kirpichev, L. V. Kulik, I. V. Kukushkin, "Express Analysis of Gas With Surface Enhanced Raman Scattering Waveguide Resonator", IEEE Sensors Journal proof, 2021. Локальный файл: [2021_Khannanov_Vankov_Kulik.pdf](2021_Khannanov_Vankov_Kulik.pdf).
