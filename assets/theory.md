---
created: 2026-07-11T09:28
updated: 2026-07-11T10:20
---
# Theory of a hollow cylindrical waveguide

Theoretical background for the calculations in the `waveguide_practice` package.

These notes follow a continuous path from basic electrodynamics to the equations used in the code: eigenmodes of a hollow metallic capillary, complex propagation constants, attenuation, angular mode selection, decomposition of a tilted Gaussian beam, longitudinal interference, and intermodal pulse delays.

## 0. Sources and their role

The equations below are linked to the research papers on which the calculation is based. The reference links lead to the corresponding publications.

- [Marcatili, Schmeltzer, 1964](https://doi.org/10.1002/j.1538-7305.1964.tb04108.x) — the foundational treatment of hollow metallic and dielectric circular waveguides: normal modes, propagation constants, HE/EH families, and the loss scaling $\alpha\propto\lambda^2/a^3$.
- [Miyagi, 1985](https://doi.org/10.1109/JLT.1985.1074177) — the connection between wave-based attenuation calculations in a circular hollow waveguide and ray optics, including the interpretation of hybrid modes in terms of their corresponding rays.
- [Matsuura, Saito, Miyagi, Hongo, 1989](https://doi.org/10.1364/JOSAA.6.000423) — a convenient ray-optical expression for multimode attenuation, polarization averaging through reflection coefficients, and treatment of the launch-angle distribution.
- [Saito, Sato, Miyagi, 1993](https://doi.org/10.1364/JOSAA.10.000277) — multimode attenuation in infrared hollow waveguides: exponential decay in the low-loss limit, dependence on bore radius and launch angle, and comparison of wave and geometrical approaches.
- [Abrams, 1972](https://doi.org/10.1109/JQE.1972.1076875) — coupling losses in hollow-waveguide resonators, the role of the lowest-order EH11 mode, and matching an external field to a waveguide mode.
- [Jenkins, Devereux, 1992](https://doi.org/10.1364/AO.31.005086) — regeneration of a TEM00 field in a circular hollow waveguide through the relative phase of the EH11/EH12 modes; this provides the physical basis for the sections on longitudinal modal correlation.
- [Khannanov, Vankov, Kulik et al., 2021](https://doi.org/10.1109/JSEN.2021.3113373) — the experimental motivation: a silver SERS waveguide resonator and Raman measurements in gases, providing context for the silver coating and the experimental problem.

The plasmonics literature collected in the project's `Plasmon` folder is not reviewed in full here. It includes duplicates of some references and additional papers on plasmonics. Extending the calculation to surface plasmon polaritons or SERS enhancement at the wall would require a separate chapter.

## 1. Scope of the calculation

The model considers a hollow circular capillary of radius

$$
a=\frac{d}{2},
$$

filled with air and surrounded by a metallic wall. The default parameters in the code are

$$
\lambda=800\ \text{nm},\qquad d=300\ \mu\text{m},\qquad a=150\ \mu\text{m}.
$$

The vacuum wavenumber is

$$
k_0=\frac{2\pi}{\lambda}.
$$

The metal is described by the complex relative permittivity of silver,

$$
\varepsilon_m=-31.021+0.40948i
$$

at a wavelength of 800 nm. The complex refractive index of the metal is

$$
v=n_m=\sqrt{\varepsilon_m}.
$$

The central approximation is to represent the field inside the capillary as a sum of cylindrical-waveguide eigenmodes. The implementation is a modal model using analytical cylindrical functions and numerical solutions of characteristic equations, rather than a full-vector finite-element calculation.

This formulation follows the classical modal theory of hollow circular waveguides developed by [Marcatili, Schmeltzer, 1964](https://doi.org/10.1002/j.1538-7305.1964.tb04108.x). The interpretation of attenuation and multimode coupling also uses results from [Miyagi, 1985](https://doi.org/10.1109/JLT.1985.1074177), [Matsuura et al., 1989](https://doi.org/10.1364/JOSAA.6.000423), and [Saito et al., 1993](https://doi.org/10.1364/JOSAA.10.000277).

The time dependence is chosen as

$$
\exp(-i\omega t).
$$

The longitudinal dependence of a mode is

$$
\exp(i\gamma z).
$$

If

$$
\gamma=\beta+i\alpha_{\rm amp},
$$

then

$$
\exp(i\gamma z)=\exp(i\beta z)\exp(-\alpha_{\rm amp}z).
$$

Thus, $\alpha_{\rm amp}$ is the amplitude attenuation coefficient, while the power attenuation coefficient is

$$
\alpha_{\rm pow}=2\alpha_{\rm amp}=2\,\mathrm{Im}\,\gamma.
$$

This is the convention used in the code:

$$
\texttt{power\_attenuation}=2\,\mathrm{Im}\,\gamma,\qquad
L_{\rm att}=\frac{1}{\alpha_{\rm pow}}.
$$

## 2. Maxwell's equations and the wave equation

In a linear, homogeneous medium without free charges or currents, Maxwell's equations for harmonic fields take the form

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

The medium inside the capillary is taken to be air, so

$$
\varepsilon\simeq\varepsilon_0,\qquad \mu\simeq\mu_0.
$$

In the metal,

$$
\varepsilon=\varepsilon_0\varepsilon_m,\qquad \mu\simeq\mu_0.
$$

To derive the wave equation for the electric field, take the curl of the first Maxwell equation:

$$
\nabla\times(\nabla\times\mathbf E)
=i\omega\mu\,\nabla\times\mathbf H.
$$

Substitute the second equation:

$$
\nabla\times(\nabla\times\mathbf E)
=i\omega\mu(-i\omega\varepsilon\mathbf E)
=\omega^2\mu\varepsilon\,\mathbf E.
$$

Use the identity

$$
\nabla\times(\nabla\times\mathbf E)
=\nabla(\nabla\cdot\mathbf E)-\nabla^2\mathbf E.
$$

In a homogeneous region, $\nabla\cdot\mathbf E=0$, hence

$$
-\nabla^2\mathbf E=\omega^2\mu\varepsilon\,\mathbf E.
$$

It follows that

$$
\nabla^2\mathbf E+k^2\mathbf E=0,
$$

where

$$
k^2=\omega^2\mu\varepsilon.
$$

In air,

$$
k=k_0=\frac{\omega}{c}.
$$

In the metal,

$$
k=k_m=v k_0,\qquad v=\sqrt{\varepsilon_m}.
$$

The same wave equation holds for $\mathbf H$.

## 3. Separation of variables in a cylindrical waveguide

The capillary has cylindrical symmetry, making the natural coordinates

$$
(r,\varphi,z).
$$

For a mode with propagation constant $\gamma$, every field component has the dependence

$$
\mathbf E(r,\varphi,z)=\mathbf E(r,\varphi)\exp(i\gamma z),
$$

$$
\mathbf H(r,\varphi,z)=\mathbf H(r,\varphi)\exp(i\gamma z).
$$

The longitudinal derivative is therefore replaced by

$$
\frac{\partial}{\partial z}\rightarrow i\gamma.
$$

For a longitudinal field component such as $E_z$, the wave equation becomes

$$
\left(\nabla_\perp^2+k^2-\gamma^2\right)E_z=0,
$$

where the transverse Laplacian in cylindrical coordinates is

$$
\nabla_\perp^2=
\frac{1}{r}\frac{\partial}{\partial r}
\left(r\frac{\partial}{\partial r}\right)
+\frac{1}{r^2}\frac{\partial^2}{\partial\varphi^2}.
$$

Define the transverse wavenumber:

$$
\kappa^2=k^2-\gamma^2.
$$

Then

$$
\left(\nabla_\perp^2+\kappa^2\right)E_z=0.
$$

Seek a solution of the form

$$
E_z(r,\varphi)=R(r)\exp(in\varphi),
$$

where $n=0,1,2,\ldots$ is the azimuthal index.

Substitution gives

$$
\frac{1}{r}\frac{d}{dr}\left(r\frac{dR}{dr}\right)
+\left(\kappa^2-\frac{n^2}{r^2}\right)R=0.
$$

Multiplying by $r^2$ yields

$$
r^2 R''+rR'+(\kappa^2 r^2-n^2)R=0.
$$

This is Bessel's equation. Its solution that is regular at the origin is

$$
R(r)=J_n(\kappa r),
$$

where $J_n$ is the Bessel function of the first kind.

Inside the capillary,

$$
\kappa_i=k_i=\sqrt{k_0^2-\gamma^2}.
$$

In the metal,

$$
\kappa_e=k_e=\sqrt{v^2k_0^2-\gamma^2}.
$$

In the code, these quantities are written as

$$
k_i=\sqrt{k_0^2-\gamma^2},\qquad
k_e=\sqrt{v^2k_0^2-\gamma^2}.
$$

The exterior region is described by the Hankel function $H_n^{(1)}(k_e r)$. The numerical implementation uses the exponentially scaled function `hankel1e` to avoid overflow for complex arguments. Ratios of Hankel functions retain the same physical meaning.

## 4. Longitudinal and transverse field components

Waveguide modes can be constructed from the longitudinal components $E_z$ and $H_z$. The transverse components are then expressed in terms of them.

Let

$$
\mathbf E=\mathbf E_\perp+\hat{\mathbf z}E_z,\qquad
\mathbf H=\mathbf H_\perp+\hat{\mathbf z}H_z.
$$

The gradient operator is

$$
\nabla=\nabla_\perp+\hat{\mathbf z}\frac{\partial}{\partial z}
=\nabla_\perp+i\gamma\hat{\mathbf z}.
$$

We now work through the algebra explicitly, writing the curls in cylindrical coordinates. For the harmonic dependence $\exp(i\gamma z)$,

$$
\frac{\partial}{\partial z}=i\gamma.
$$

The components of the equation

$$
\nabla\times\mathbf E=i\omega\mu\mathbf H
$$

are

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

Replacing $\partial/\partial z\to i\gamma$ gives

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

The components of the equation

$$
\nabla\times\mathbf H=-i\omega\varepsilon\mathbf E
$$

give

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

Again substituting $\partial/\partial z=i\gamma$ yields

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

We need to express $E_r,E_\varphi,H_r,H_\varphi$ in terms of $E_z,H_z$. Start with $E_r$. From (4.2),

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

Substitute (4.5) into (4.3):

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

Expand the brackets:

$$
\frac{1}{r}\frac{\partial H_z}{\partial\varphi}
-
\frac{i\gamma^2}{\omega\mu}E_r
+
\frac{\gamma}{\omega\mu}\frac{\partial E_z}{\partial r}
=
-i\omega\varepsilon E_r.
$$

Move all terms containing $E_r$ to the right:

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

Combine the terms in brackets over a common denominator:

$$
\omega\varepsilon-\frac{\gamma^2}{\omega\mu}
=
\frac{\omega^2\mu\varepsilon-\gamma^2}{\omega\mu}
=
\frac{\kappa^2}{\omega\mu}.
$$

Thus,

$$
\frac{1}{r}\frac{\partial H_z}{\partial\varphi}
+
\frac{\gamma}{\omega\mu}\frac{\partial E_z}{\partial r}
=
-i\frac{\kappa^2}{\omega\mu}E_r.
$$

Multiply by $\omega\mu$:

$$
\frac{\omega\mu}{r}\frac{\partial H_z}{\partial\varphi}
+
\gamma\frac{\partial E_z}{\partial r}
=
-i\kappa^2E_r.
$$

Since $1/(-i)=i$, we obtain

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

Next, derive $E_\varphi$. From (4.1),

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

Substitute (4.7) into (4.4):

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

Expanding gives

$$
\frac{\gamma}{\omega\mu r}\frac{\partial E_z}{\partial\varphi}
-
\frac{i\gamma^2}{\omega\mu}E_\varphi
-
\frac{\partial H_z}{\partial r}
=
-i\omega\varepsilon E_\varphi.
$$

Move the terms containing $E_\varphi$ to the right:

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

Multiply by $\omega\mu$:

$$
\frac{\gamma}{r}\frac{\partial E_z}{\partial\varphi}
-
\omega\mu\frac{\partial H_z}{\partial r}
=
-i\kappa^2E_\varphi.
$$

Hence,

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

The magnetic field follows in the same way. Repeat the steps with the substitutions

$$
\mathbf E\leftrightarrow\mathbf H,
\qquad
\mu\to\varepsilon,
\qquad
\omega\mu\to-\omega\varepsilon
$$

taking account of the sign in the second Maxwell equation. The resulting components are

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

Equations (4.6)–(4.10) can now be combined into a compact vector form. The transverse gradient is

$$
\nabla_\perp f
=
\hat{\mathbf r}\frac{\partial f}{\partial r}
+
\hat{\boldsymbol\varphi}\frac{1}{r}\frac{\partial f}{\partial\varphi}.
$$

For any function $f$,

$$
\hat{\mathbf z}\times\nabla_\perp f
=
\hat{\boldsymbol\varphi}\frac{\partial f}{\partial r}
-
\hat{\mathbf r}\frac{1}{r}\frac{\partial f}{\partial\varphi}.
$$

Equations (4.6) and (4.8) therefore combine into

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

while (4.9) and (4.10) give

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

Once $E_z$ and $H_z$ are known, all transverse components follow by direct differentiation. The mode problem therefore reduces to two steps:

1. Find cylindrical solutions for $E_z,H_z$.
2. Apply the boundary conditions at $r=a$ to the tangential components $E_z,H_z,E_\varphi,H_\varphi$.

## 5. Mode families: TE, TM, HE, EH

A cylindrical waveguide supports several families of modes.

The TE/TM/HE/EH classification and the treatment of hybrid modes as normal modes of a hollow circular waveguide are standard elements of Marcatili–Schmeltzer theory. The lowest-order hybrid EH11 mode is discussed specifically for coupling and resonators by [Abrams, 1972](https://doi.org/10.1109/JQE.1972.1076875).

TE modes satisfy

$$
E_z=0,\qquad H_z\ne 0.
$$

TM modes satisfy

$$
H_z=0,\qquad E_z\ne 0.
$$

Hybrid modes have both

$$
E_z\ne 0,\qquad H_z\ne 0.
$$

They are divided into HE and EH families. In rigorous vector theory, the distinction is related to the relative contributions of the longitudinal electric and magnetic components. In the present numerical model, it is represented by the choice of Bessel roots:

$$
\mathrm{HE}_{n,m}:\quad u_{n,m}\approx j_{n-1,m},
$$

$$
\mathrm{EH}_{n,m}:\quad u_{n,m}\approx j_{n+1,m}.
$$

Here, $j_{\ell,m}$ is the $m$th zero of the Bessel function $J_\ell$:

$$
J_\ell(j_{\ell,m})=0.
$$

The calculation also includes the axisymmetric TE and TM families:

$$
\mathrm{TE}_{0,m}:\quad u_{0,m}\approx j_{1,m},
$$

$$
\mathrm{TM}_{0,m}:\quad u_{0,m}\approx j_{0,m}.
$$

These roots provide initial estimates for solving the more accurate complex characteristic equation.

## 6. Geometrical meaning of \(u\)

For a mode inside the bore, the transverse wavenumber is approximately

$$
k_\perp=\frac{u}{a}.
$$

The total wavenumber, transverse wavenumber, and longitudinal propagation constant satisfy

$$
k_0^2=\beta^2+k_\perp^2.
$$

In the lossless approximation, this gives

$$
\beta\simeq\sqrt{k_0^2-\left(\frac{u}{a}\right)^2}.
$$

This is the initial estimate for the real part of $\gamma$ used in the code:

$$
\beta_0=\sqrt{k_0^2-\left(\frac{u_0}{a}\right)^2}.
$$

Introducing the modal angle $\theta_\mu$ gives

$$
\sin\theta_\mu=\frac{k_\perp}{k_0}
=\frac{u_\mu}{k_0a}.
$$

Therefore,

$$
\theta_\mu=\arcsin\left(\frac{u_\mu}{k_0a}\right).
$$

A mode propagates if

$$
u_\mu<k_0a.
$$

The quantity

$$
u_{\rm cutoff}=k_0a
$$

sets the upper limit for propagating modes.

For the default parameters,

$$
k_0a=\frac{2\pi}{800\cdot10^{-9}}\cdot150\cdot10^{-6}
\approx1178.
$$

This is a large number. Even moderate launch angles therefore correspond to large values of $u$ and high mode indices.

## 7. Characteristic equations for complex \(\gamma\)

An exact mode calculation must satisfy the boundary conditions at the air–metal interface:

$$
r=a.
$$

The tangential field components must be continuous:

$$
E_\varphi^{(i)}=E_\varphi^{(e)},\qquad
E_z^{(i)}=E_z^{(e)},
$$

$$
H_\varphi^{(i)}=H_\varphi^{(e)},\qquad
H_z^{(i)}=H_z^{(e)}.
$$

The subscript $i$ denotes the interior, and $e$ denotes the metal.

The derivation below proceeds explicitly: specify the longitudinal fields inside and outside, calculate $E_\varphi$ and $H_\varphi$ using Section 4, and turn the boundary conditions into a homogeneous system for the amplitudes. The characteristic equation follows by setting the determinant of this system to zero.

This route from Maxwell's equations to the characteristic equations of the normal modes of a circular hollow waveguide underlies the work of [Marcatili, Schmeltzer, 1964](https://doi.org/10.1002/j.1538-7305.1964.tb04108.x). In the code, the characteristic equations are written in a form suitable for numerical solution for the complex root $\gamma$.

### 7.1. TE equation

For a TE mode,

$$
E_z=0,\qquad H_z\ne0.
$$

The current implementation considers axisymmetric TE modes, $n=0$. Then $\partial/\partial\varphi=0$, and the longitudinal magnetic field can be written as

$$
H_z^{(i)}(r)=A J_0(k_i r)
$$

inside the capillary and

$$
H_z^{(e)}(r)=B H_0^{(1)}(k_e r)
$$

in the metal.

Since $E_z=0$, equation (4.8),

$$
E_\varphi=
\frac{i}{\kappa^2}
\left(
\frac{\gamma}{r}\frac{\partial E_z}{\partial\varphi}
-
\omega\mu\frac{\partial H_z}{\partial r}
\right)
$$

reduces to

$$
E_\varphi=
-\frac{i\omega\mu}{\kappa^2}
\frac{\partial H_z}{\partial r}.
$$

Inside, $\kappa^2=k_i^2$, so

$$
E_\varphi^{(i)}
=
-\frac{i\omega\mu}{k_i^2}
\frac{d}{dr}\left[A J_0(k_i r)\right]
=
-\frac{i\omega\mu A}{k_i^2}
k_i J_0'(k_i r).
$$

Use the identity

$$
J_0'(x)=-J_1(x).
$$

At the boundary $r=a$,

$$
E_\varphi^{(i)}(a)
=
\frac{i\omega\mu A}{k_i}J_1(k_i a).
\tag{7.1}
$$

Outside,

$$
E_\varphi^{(e)}
=
-\frac{i\omega\mu}{k_e^2}
\frac{d}{dr}\left[B H_0^{(1)}(k_e r)\right]
=
-\frac{i\omega\mu B}{k_e^2}
k_e {H_0^{(1)}}'(k_e r).
$$

The corresponding identity for the Hankel function is

$$
{H_0^{(1)}}'(x)=-H_1^{(1)}(x).
$$

Thus,

$$
E_\varphi^{(e)}(a)
=
\frac{i\omega\mu B}{k_e}H_1^{(1)}(k_e a).
\tag{7.2}
$$

Now apply the two boundary conditions.

The first is continuity of $H_z$:

$$
A J_0(k_i a)
=
B H_0^{(1)}(k_e a).
\tag{7.3}
$$

The second is continuity of $E_\varphi$:

$$
\frac{i\omega\mu A}{k_i}J_1(k_i a)
=
\frac{i\omega\mu B}{k_e}H_1^{(1)}(k_e a).
\tag{7.4}
$$

Cancel the common factor $i\omega\mu$:

$$
\frac{A}{k_i}J_1(k_i a)
=
\frac{B}{k_e}H_1^{(1)}(k_e a).
\tag{7.5}
$$

Divide (7.5) by (7.3):

$$
\frac{J_1(k_i a)}{k_iJ_0(k_i a)}
=
\frac{H_1^{(1)}(k_e a)}{k_eH_0^{(1)}(k_e a)}.
$$

Multiply by $k_i$ and bring all terms to one side:

$$
\frac{k_i}{k_e}
\frac{H_1^{(1)}(k_ea)}{H_0^{(1)}(k_ea)}
-
\frac{J_1(k_ia)}{J_0(k_ia)}
=0.
$$

This is the TE characteristic equation. The code uses the scaled Hankel function `hankel1e`, but the ratio $H_1/H_0$ has the same meaning:

$$
\left(\frac{k_i}{k_e}\right)
\left(\frac{H_1(k_ea)}{H_0(k_ea)}\right)
-
\frac{J_1(k_ia)}{J_0(k_ia)}
=0.
$$

### 7.2. TM equation

For a TM mode,

$$
H_z=0,\qquad E_z\ne0.
$$

For the axisymmetric mode $n=0$, take

$$
E_z^{(i)}(r)=A J_0(k_i r),
$$

$$
E_z^{(e)}(r)=B H_0^{(1)}(k_e r).
$$

We now need the tangential component $H_\varphi$. From (4.10),

$$
H_\varphi=
\frac{i}{\kappa^2}
\left(
\frac{\gamma}{r}\frac{\partial H_z}{\partial\varphi}
+
\omega\varepsilon\frac{\partial E_z}{\partial r}
\right).
$$

Since $H_z=0$ and $n=0$,

$$
H_\varphi=
\frac{i\omega\varepsilon}{\kappa^2}
\frac{\partial E_z}{\partial r}.
$$

Inside the capillary, $\varepsilon_i=\varepsilon_0$ and $\kappa^2=k_i^2$:

$$
H_\varphi^{(i)}
=
\frac{i\omega\varepsilon_0}{k_i^2}
\frac{d}{dr}\left[A J_0(k_i r)\right]
=
\frac{i\omega\varepsilon_0 A}{k_i^2}
k_iJ_0'(k_i r).
$$

Using $J_0'(x)=-J_1(x)$ gives

$$
H_\varphi^{(i)}(a)
=
-\frac{i\omega\varepsilon_0 A}{k_i}
J_1(k_i a).
\tag{7.6}
$$

In the metal, $\varepsilon_e=\varepsilon_0 v^2$ and $\kappa^2=k_e^2$:

$$
H_\varphi^{(e)}
=
\frac{i\omega\varepsilon_0v^2}{k_e^2}
\frac{d}{dr}\left[B H_0^{(1)}(k_e r)\right]
=
\frac{i\omega\varepsilon_0v^2B}{k_e}
{H_0^{(1)}}'(k_e r).
$$

Since ${H_0^{(1)}}'(x)=-H_1^{(1)}(x)$,

$$
H_\varphi^{(e)}(a)
=
-\frac{i\omega\varepsilon_0v^2B}{k_e}
H_1^{(1)}(k_e a).
\tag{7.7}
$$

Continuity of $E_z$ gives

$$
A J_0(k_i a)
=
B H_0^{(1)}(k_e a).
\tag{7.8}
$$

Continuity of $H_\varphi$ gives

$$
-\frac{i\omega\varepsilon_0 A}{k_i}J_1(k_i a)
=
-\frac{i\omega\varepsilon_0v^2B}{k_e}H_1^{(1)}(k_e a).
\tag{7.9}
$$

Cancel $-i\omega\varepsilon_0$:

$$
\frac{A}{k_i}J_1(k_i a)
=
\frac{v^2B}{k_e}H_1^{(1)}(k_e a).
\tag{7.10}
$$

Divide (7.10) by (7.8):

$$
\frac{J_1(k_i a)}{k_iJ_0(k_i a)}
=
\frac{v^2H_1^{(1)}(k_e a)}
{k_eH_0^{(1)}(k_e a)}.
$$

Multiply by $k_iJ_0(k_i a)$ and rearrange:

$$
v^2\frac{k_i}{k_e}
\frac{H_1^{(1)}(k_ea)}{H_0^{(1)}(k_ea)}
J_0(k_ia)
-
J_1(k_ia)
=0.
$$

This is the TM characteristic equation. In the notation used by the code,

$$
v^2
\left(\frac{k_i}{k_e}\right)
\left(\frac{H_1(k_ea)}{H_0(k_ea)}\right)
J_0(k_ia)
-
J_1(k_ia)
=0.
$$

The factor $v^2=\varepsilon_m$ arises from the magnetic-field boundary condition and the relation $\mathbf D=\varepsilon\mathbf E$ in the metal.

### 7.3. Hybrid HE/EH equation

For hybrid modes, both longitudinal components are nonzero:

$$
E_z\ne0,\qquad H_z\ne0.
$$

Let the azimuthal dependence be $\exp(in\varphi)$. Inside the capillary,

$$
E_z^{(i)}=A J_n(k_i r)e^{in\varphi},
$$

$$
H_z^{(i)}=B J_n(k_i r)e^{in\varphi}.
$$

In the metal,

$$
E_z^{(e)}=C H_n^{(1)}(k_e r)e^{in\varphi},
$$

$$
H_z^{(e)}=D H_n^{(1)}(k_e r)e^{in\varphi}.
$$

Continuity of the longitudinal components at $r=a$ gives

$$
A J_n(k_i a)=C H_n^{(1)}(k_e a),
\tag{7.11}
$$

$$
B J_n(k_i a)=D H_n^{(1)}(k_e a).
\tag{7.12}
$$

The exterior amplitudes can therefore be expressed in terms of the interior amplitudes:

$$
C=A\frac{J_n(k_i a)}{H_n^{(1)}(k_e a)},
\qquad
D=B\frac{J_n(k_i a)}{H_n^{(1)}(k_e a)}.
\tag{7.13}
$$

Now use the tangential components from Section 4. Since

$$
\frac{\partial}{\partial\varphi}e^{in\varphi}
=in e^{in\varphi},
$$

we have

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

To express the derivatives through ratios of functions at the boundary, define

$$
R_J=\frac{J_{n+1}(k_i a)}{J_n(k_i a)},
\qquad
R_H=\frac{H_{n+1}^{(1)}(k_e a)}{H_n^{(1)}(k_e a)}.
\tag{7.16}
$$

Use the recurrence relation for cylindrical functions:

$$
Z_n'(x)=\frac{n}{x}Z_n(x)-Z_{n+1}(x),
\tag{7.17}
$$

where $Z_n$ can be either $J_n$ or $H_n^{(1)}$. Therefore,

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

Next, impose continuity of $E_\varphi$. Substitute (7.14) for the interior and exterior fields, and use (7.13) to eliminate $C,D$. Dividing by the common factor $J_n(k_i a)e^{in\varphi}$ gives

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

Similarly, continuity of $H_\varphi$ gives

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

Equations (7.20)–(7.21) form a homogeneous system for the amplitudes $A$ and $B$:

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

A nontrivial solution exists only if

$$
M_{EE}M_{HH}-M_{EH}M_{HE}=0.
\tag{7.23}
$$

To obtain a compact form from (7.20)–(7.21), define

$$
\Delta=
\frac{1}{k_i^2}-\frac{1}{k_e^2}.
\tag{7.24}
$$

The coefficients of $A$ and $B$ in (7.20) can then be written as

$$
M_{EE}=-\frac{n\gamma}{a}\Delta,
\tag{7.25}
$$

$$
M_{EH}=-i\omega\mu a\,T_{\rm TE},
\tag{7.26}
$$

with the definitions

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

Indeed,

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

which matches the bracket multiplying $B$ in (7.20).

Similarly, from (7.21),

$$
M_{HH}=-\frac{n\gamma}{a}\Delta,
\tag{7.28}
$$

$$
M_{HE}=i\omega\varepsilon_0 a\,T_{\rm TM},
\tag{7.29}
$$

where

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

Now expand the determinant:

$$
M_{EE}M_{HH}-M_{EH}M_{HE}=0.
$$

The first product is

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

The second product is

$$
M_{EH}M_{HE}
=
\left(-i\omega\mu aT_{\rm TE}\right)
\left(i\omega\varepsilon_0 aT_{\rm TM}\right).
$$

Since

$$
(-i)i=1,
$$

we obtain

$$
M_{EH}M_{HE}
=
\omega^2\mu\varepsilon_0 a^2
T_{\rm TE}T_{\rm TM}.
\tag{7.32}
$$

In air,

$$
k_0^2=\omega^2\mu\varepsilon_0.
$$

The determinant condition therefore becomes

$$
\frac{n^2\gamma^2}{a^2}\Delta^2
-
k_0^2a^2T_{\rm TE}T_{\rm TM}=0.
\tag{7.33}
$$

Divide by $k_0^2a^2$:

$$
T_{\rm TE}T_{\rm TM}
=
\frac{n^2\gamma^2}{k_0^2}
\frac{\Delta^2}{a^4}.
\tag{7.34}
$$

However,

$$
\frac{\Delta}{a^2}
=
\frac{1}{(k_ia)^2}
-
\frac{1}{(k_ea)^2}.
$$

Therefore,

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

This now has the same structure as the equation implemented in the code.

In the code, the right-hand side representing hybrid coupling is written as

$$
Q=
\left(\frac{n\gamma}{k_0}\right)^2
\left[
\frac{1}{(k_ia)^2}
-
\frac{1}{(k_ea)^2}
\right]^2.
$$

The characteristic equation is therefore

$$
T_{\rm TE}T_{\rm TM}-Q=0.
$$

The code additionally multiplies this by $(k_ia)^2$:

$$
\left(T_{\rm TE}T_{\rm TM}-Q\right)(k_ia)^2=0.
$$

Multiplication by a nonzero factor leaves the roots unchanged while improving the numerical scaling of the function.

This equation requires the azimuthal index $n$, not the radial index $m$. The original project README records that an earlier notebook incorrectly passed the radial index in one location.

### 7.4. Numerical solution

The complex equation

$$
F(\gamma)=0
$$

is solved as a system of two real equations:

$$
\mathrm{Re}\,F(\beta+i\alpha_{\rm amp})=0,
$$

$$
\mathrm{Im}\,F(\beta+i\alpha_{\rm amp})=0.
$$

The initial estimate is

$$
\gamma_0=\beta_0+i\alpha_{{\rm amp},0}.
$$

Here,

$$
\beta_0=\sqrt{k_0^2-\left(\frac{u_0}{a}\right)^2},
$$

and $\alpha_{{\rm amp},0}$ is taken as half the Marcatili loss estimate, since that estimate describes power attenuation.

After solving,

$$
n_{\rm eff}=\frac{\gamma}{k_0}.
$$

## 8. Attenuation: complex \(\gamma\), Marcatili, and ray optics

### 8.1. Complex propagation constant

The field of a single mode is

$$
\mathbf E_\mu(r,\varphi,z)
=c_\mu\mathbf e_\mu(r,\varphi)\exp(i\gamma_\mu z).
$$

Let

$$
\gamma_\mu=\beta_\mu+i\alpha_{\rm amp,\mu}.
$$

Then

$$
|\mathbf E_\mu(z)|^2
\propto
\exp(-2\alpha_{\rm amp,\mu}z).
$$

Thus,

$$
\alpha_{\rm pow,\mu}=2\alpha_{\rm amp,\mu}.
$$

The modal power at distance $z$ is

$$
P_\mu(z)=P_\mu(0)\exp(-\alpha_{\rm pow,\mu}z).
$$

### 8.2. Marcatili estimate

The code uses a power-attenuation estimate for a hollow metallic waveguide. It follows the Marcatili–Schmeltzer result that normal-mode losses in a circular hollow waveguide scale as $\lambda^2$ and $a^{-3}$:

$$
\alpha_{\rm M}
=
\left(\frac{u}{2\pi}\right)^2
\frac{\lambda^2}{a^3}
\mathrm{Re}\,\nu.
$$

The parameter $\nu$ depends on the mode family:

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

The key structure of this expression is

$$
\alpha_{\rm M}\propto \frac{u^2\lambda^2}{a^3}.
$$

Consequently,

- Modes with larger $u$ interact more strongly with the wall and undergo stronger attenuation.
- Increasing the radius sharply reduces the losses.
- At fixed radius and material properties, this estimate predicts losses increasing as $\lambda^2$ with wavelength.

The initial amplitude-attenuation estimate in the code is

$$
\alpha_{{\rm amp},0}
=\frac{\alpha_{\rm M}}{2}.
$$

### 8.3. Ray-optical loss estimate

The module `attenuation.py` also contains a ray model. Its interpretation follows [Miyagi, 1985](https://doi.org/10.1109/JLT.1985.1074177), [Matsuura et al., 1989](https://doi.org/10.1364/JOSAA.6.000423), and [Saito et al., 1993](https://doi.org/10.1364/JOSAA.10.000277): in the low-loss limit, wave-based attenuation can be expressed in ray-optical terms through the wall reflection coefficient and the frequency of ray–wall encounters.

A ray travelling at angle $\theta$ to the capillary axis reflects from the wall. The distance along $z$ between successive reflections is estimated as

$$
\Delta z\simeq \frac{2a}{\tan\theta}.
$$

The number of reflections per unit length is

$$
N_z\simeq\frac{1}{\Delta z}
=\frac{\tan\theta}{2a}.
$$

If the mean power reflectance is $R$, the loss per reflection is $1-R$. In the low-loss limit, the power attenuation coefficient is

$$
\alpha_{\rm ray}
\simeq
(1-R)\frac{\tan\theta}{2a}.
$$

This is the expression used in the code:

$$
\alpha_{\rm ray}(\theta)
=
\left[1-R_{\rm rough}(\theta)\right]\frac{\tan\theta}{2a}.
$$

For a planar air–metal interface, the angle to the normal is

$$
\psi=\frac{\pi}{2}-\theta.
$$

The Fresnel coefficients are

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

The mean reflectance is

$$
R=\frac{|r_s|^2+|r_p|^2}{2}.
$$

If a root-mean-square wall roughness $\sigma$ is specified, the code multiplies $R$ by the factor

$$
\exp\left[
-
\left(
\frac{4\pi\sigma\sin\theta}{\lambda}
\right)^2
\right].
$$

The default is $\sigma=0$, which disables the roughness correction.

[Matsuura et al., 1989](https://doi.org/10.1364/JOSAA.6.000423) emphasize that surface irregularities have a substantial effect on predicted losses in metallic waveguides. The code accounts for this only through a simple roughness factor: it is a coarse approximation, not a complete model of a real surface.

## 9. Input Gaussian beam

At the entrance plane $z=0$, the beam is specified by a Gaussian envelope with a linear phase tilt:

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

Here,

- $w_0$ is the beam radius;
- $(x_0,y_0)$ is the spot displacement from the capillary centre;
- $\theta_x,\theta_y$ are the tilts along the two transverse axes;
- $\mathbf e_p=(p_x,p_y)$ is the transverse polarization.

If $w_0$ is not specified explicitly, the code uses

$$
w_0=0.3a.
$$

The transverse wavevector of the beam is

$$
k_x=k_0\sin\theta_x,\qquad
k_y=k_0\sin\theta_y,
$$

$$
k_\perp=\sqrt{k_x^2+k_y^2}.
$$

If the tilt is specified by the polar angle $\theta$,

$$
k_\perp=k_0\sin\theta.
$$

In polar coordinates, for a centred beam,

$$
E_{\rm in}(r,\varphi)
=
\mathbf e_p
\exp\left(-\frac{r^2}{w_0^2}\right)
\exp\left[
i k_\perp r\cos(\varphi-\varphi_k)
\right],
$$

where $\varphi_k$ is the azimuth of the tilt direction.

## 10. Why a tilted beam excites high-order modes

A mode with parameter $u_\mu$ has transverse wavenumber

$$
k_{\perp,\mu}=\frac{u_\mu}{a}.
$$

The input beam has transverse wavenumber

$$
k_\perp=k_0\sin\theta.
$$

The strongest excitation is expected under the matching condition

$$
\frac{u_\mu}{a}\simeq k_0\sin\theta.
$$

The centre of the modal packet is therefore

$$
u_{\rm target}=k_0a\sin\theta.
$$

This is one of the key equations of the calculation.

For the default parameters,

$$
k_0a\approx1178.
$$

At $\theta=15^\circ$,

$$
u_{\rm target}\approx1178\sin15^\circ\approx305.
$$

At $\theta=30^\circ$,

$$
u_{\rm target}\approx1178\sin30^\circ\approx589.
$$

A beam tilted by tens of degrees therefore cannot be described accurately using only a few low-order modes with $u\sim1\ldots20$. Modes must be selected near the large value of $u_{\rm target}$.

This extends the standard Marcatili–Schmeltzer modal picture to tilted Gaussian input: instead of selecting small indices $n,m$, the code selects modes by matching the transverse wavenumber.

## 11. Derivation of the selection width in \(u\)

The width of the excited packet in $u$ is determined by the angular spectrum of the Gaussian beam.

Consider the one-dimensional Gaussian factor

$$
f(x)=\exp\left(-\frac{x^2}{w_0^2}\right).
$$

Its Fourier transform with respect to the transverse wavenumber has the form

$$
\tilde f(k_x)\propto
\exp\left(-\frac{w_0^2 k_x^2}{4}\right).
$$

For a tilted beam, the spectrum shifts to $k_x=k_{\perp,0}$:

$$
\tilde f(k_x)\propto
\exp\left[
-
\frac{w_0^2(k_x-k_{\perp,0})^2}{4}
\right].
$$

Power is proportional to the squared amplitude:

$$
|\tilde f(k_x)|^2
\propto
\exp\left[
-
\frac{w_0^2(k_x-k_{\perp,0})^2}{2}
\right].
$$

Suppose we retain modes whose relative spectral power is at least $p_{\min}$. Then

$$
\exp\left(-\frac{w_0^2\Delta k_\perp^2}{2}\right)
=p_{\min}.
$$

Taking the logarithm gives

$$
-\frac{w_0^2\Delta k_\perp^2}{2}
=\ln p_{\min}.
$$

Since $\ln p_{\min}<0$,

$$
\Delta k_\perp
=
\frac{\sqrt{2\ln(1/p_{\min})}}{w_0}.
$$

The conversion from $k_\perp$ to $u$ is

$$
u=ak_\perp.
$$

Therefore,

$$
\Delta u
=
a\Delta k_\perp
=
\frac{a}{w_0}
\sqrt{2\ln(1/p_{\min})}.
$$

In the code,

$$
\Delta u
=
\frac{a}{w_0}
\sqrt{2\ln(1/p_{\min})}.
$$

The selection window is

$$
u_{\min}=\max(0,u_{\rm target}-\Delta u),
$$

$$
u_{\max}=\min(k_0a,u_{\rm target}+\Delta u).
$$

## 12. Angular harmonics and the Jacobi–Anger expansion

The tilted plane-wave phase in cylindrical coordinates is

$$
\exp\left[
i k_\perp r\cos(\varphi-\varphi_k)
\right].
$$

Use the Jacobi–Anger expansion:

$$
\exp(i x\cos\phi)
=
\sum_{q=-\infty}^{\infty}
i^q J_q(x)\exp(iq\phi).
$$

In this problem,

$$
x=k_\perp r,\qquad
\phi=\varphi-\varphi_k.
$$

Therefore,

$$
\exp\left[
i k_\perp r\cos(\varphi-\varphi_k)
\right]
=
\sum_{q=-\infty}^{\infty}
i^qJ_q(k_\perp r)
\exp[iq(\varphi-\varphi_k)].
$$

This shows that a tilted beam contains many azimuthal harmonics $q$.

The function $J_q(x)$ is small when its order $q$ is much larger than its argument $x$. A centred beam occupies mainly the region $r\sim w_0$, giving the rough estimate

$$
q\lesssim k_\perp w_0.
$$

If the beam is displaced by a distance

$$
r_0=\sqrt{x_0^2+y_0^2},
$$

the region of significant field extends to approximately $r\sim r_0+w_0$. The estimate becomes

$$
q_{\max}\sim k_\perp(r_0+w_0).
$$

The code uses the more practical expression

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

with defaults $F=1$ and $q_{\rm margin}=4$.

The following limit is also imposed:

$$
q_{\max}\le \lceil u_{\max}\rceil+q_{\rm margin}.
$$

## 13. Candidate-mode selection

The mode-selection algorithm performs two steps:

1. Select only Bessel roots within the window $[u_{\min},u_{\max}]$.
2. Limit the azimuthal orders to $q_{\max}$.

For TE and TM modes,

$$
\mathrm{TE}_{0,m}:\quad u=j_{1,m},
$$

$$
\mathrm{TM}_{0,m}:\quad u=j_{0,m}.
$$

For hybrid modes, the family index $n$ and the transverse-profile order $q$ are related by

$$
\mathrm{HE}_{n,m}:\quad q=n-1,\qquad u=j_{q,m},
$$

$$
\mathrm{EH}_{n,m}:\quad q=n+1,\qquad u=j_{q,m}.
$$

Hence,

$$
\mathrm{HE}: n=q+1,
$$

$$
\mathrm{EH}: n=q-1.
$$

For each $q$, the code iterates over the zeros of $J_q$ in the $u$ window and creates the corresponding `ModeSpec` objects.

The modal angle is also calculated for each mode:

$$
\theta_{\rm mode}
=
\arcsin\left(\frac{u}{k_0a}\right).
$$

This is useful for plots and diagnostics: the launch angle should lie within the range of modal angles covered by the selected modes.

## 14. Transverse profiles used in the projection

The exact vector profile of a metallic-waveguide mode is complicated. To decompose the input field, the code uses simplified transverse profiles based on Bessel functions.

Define

$$
\rho=\frac{r}{a}.
$$

### 14.1. TE profile

In the code,

$$
E_x=-J_1(u\rho)\sin\varphi,
$$

$$
E_y=J_1(u\rho)\cos\varphi.
$$

The field is therefore azimuthally directed:

$$
\mathbf e_{\rm TE}
=J_1(u\rho)\,\hat{\boldsymbol\varphi}.
$$

### 14.2. TM profile

In the code,

$$
E_x=J_1(u\rho)\cos\varphi,
$$

$$
E_y=J_1(u\rho)\sin\varphi.
$$

The field is therefore radially directed:

$$
\mathbf e_{\rm TM}
=J_1(u\rho)\,\hat{\mathbf r}.
$$

### 14.3. HE profiles

For HE modes,

$$
q=n-1.
$$

The cosine orientation is

$$
E_x=J_q(u\rho)\cos(q\varphi),
$$

$$
E_y=-J_q(u\rho)\sin(q\varphi).
$$

The sine orientation is

$$
E_x=J_q(u\rho)\sin(q\varphi),
$$

$$
E_y=J_q(u\rho)\cos(q\varphi).
$$

### 14.4. EH profiles

For EH modes,

$$
q=n+1.
$$

The cosine orientation is

$$
E_x=J_q(u\rho)\cos(q\varphi),
$$

$$
E_y=J_q(u\rho)\sin(q\varphi).
$$

The sine orientation is

$$
E_x=J_q(u\rho)\sin(q\varphi),
$$

$$
E_y=-J_q(u\rho)\cos(q\varphi).
$$

Both orientations of each hybrid mode are included in the basis, since displacement or tilt of the input beam can excite any linear combination of these two degenerate profiles.

## 15. Mode normalization and inner product

The inner product for transverse fields is defined as

$$
\langle \mathbf f,\mathbf g\rangle
=
\int_{r<a}
\left(f_x^*g_x+f_y^*g_y\right)\,dA.
$$

In cylindrical coordinates,

$$
dA=r\,dr\,d\varphi.
$$

The profile norm is

$$
\|\mathbf e_\mu\|
=
\sqrt{\langle\mathbf e_\mu,\mathbf e_\mu\rangle}.
$$

The normalized profile is

$$
\tilde{\mathbf e}_\mu
=
\frac{\mathbf e_\mu}{\|\mathbf e_\mu\|}.
$$

The code evaluates the normalization numerically on a Cartesian grid:

$$
\|\mathbf e_\mu\|^2
\approx
\sum_{r_j<a}
\left(|E_x(x_j,y_j)|^2+|E_y(x_j,y_j)|^2\right)\Delta A.
$$

The input power in arbitrary units is

$$
P_{\rm in}
=
\int_{r<a}
\left(|E_x^{\rm in}|^2+|E_y^{\rm in}|^2\right)dA.
$$

Numerically,

$$
P_{\rm in}
\approx
\sum_{r_j<a}
\left(|E_x^{\rm in}(x_j,y_j)|^2+|E_y^{\rm in}(x_j,y_j)|^2\right)\Delta A.
$$

## 16. Modal decomposition as a least-squares problem

We seek to approximate the input field by a sum of modes:

$$
\mathbf E_{\rm in}(x,y)
\approx
\sum_{\mu}c_\mu\tilde{\mathbf e}_\mu(x,y).
$$

If the modes were strictly orthonormal, each coefficient would follow from a simple projection:

$$
c_\mu=\langle \tilde{\mathbf e}_\mu,\mathbf E_{\rm in}\rangle.
$$

In the numerical model, however, the profiles are not perfectly orthogonal, especially with a truncated basis and approximate hybrid profiles. The code therefore solves a least-squares problem.

Let the vector $y$ contain the input-field values on the grid:

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

The matrix $A$ contains the normalized profiles:

$$
A=
\begin{pmatrix}
| & | & & |\\
e_1 & e_2 & \cdots & e_M\\
| & | & & |
\end{pmatrix}.
$$

We seek the coefficient vector $c$:

$$
Ac\approx y.
$$

The problem is

$$
c=\arg\min_c\|Ac-y\|^2.
$$

If $A^\dagger A$ is nonsingular, the formal solution is

$$
c=(A^\dagger A)^{-1}A^\dagger y.
$$

In practice, `numpy.linalg.lstsq` provides a numerically stable solution.

The power reconstructed by the modal basis is

$$
P_{\rm coupled}=\|Ac\|^2.
$$

The unreconstructed power is

$$
P_{\rm residual}=P_{\rm in}-P_{\rm coupled}.
$$

A commonly used diagnostic quantity is

$$
\eta_\mu=\frac{|c_\mu|^2}{P_{\rm in}}.
$$

If the profiles are nearly orthonormal, $\eta_\mu$ can be interpreted as the fraction of power in a profile. In general, it is a diagnostic weight rather than a rigorous energy decomposition.

For a physical mode with two degenerate orientations, the code adds their weights:

$$
\eta_{\mu,\rm total}
=
\sum_{s\in\{c,s\}}
\frac{|c_{\mu s}|^2}{P_{\rm in}}.
$$

## 17. Fast excitation estimate in polar coordinates

A coarse projection on a polar grid is used for preliminary mode selection. The input field is

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

In polar coordinates,

$$
x=a\rho\cos\varphi,\qquad
y=a\rho\sin\varphi.
$$

The integral for the coefficient has the form

$$
c_\mu
=
\int_0^1\int_0^{2\pi}
\mathbf e_\mu^*(\rho,\varphi)\cdot
\mathbf E_{\rm in}(\rho,\varphi)
a^2\rho\,d\varphi\,d\rho.
$$

Numerically, the radial integral is evaluated by Gauss–Legendre quadrature in $\rho$, and the angular integral on a uniform grid in $\varphi$.

For a centred beam, the angular integral can be simplified analytically. The Jacobi–Anger expansion gives

$$
\int_0^{2\pi}
\exp[i k_\perp r\cos(\varphi-\varphi_k)]
\cos(q\varphi)\,d\varphi
=
2\pi i^q J_q(k_\perp r)\cos(q\varphi_k).
$$

Similarly,

$$
\int_0^{2\pi}
\exp[i k_\perp r\cos(\varphi-\varphi_k)]
\sin(q\varphi)\,d\varphi
=
2\pi i^q J_q(k_\perp r)\sin(q\varphi_k).
$$

The coefficients then reduce to radial integrals of the form

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

This expression explains why the maximum occurs at

$$
u_\mu\simeq u_{\rm target}.
$$

The product of the two Bessel functions makes a large contribution when their oscillations match.

## 18. Propagation of the modal field

Once the coefficients have been found, the field at distance $z$ is

$$
\mathbf E_\perp(r,\varphi,z)
=
\sum_\mu
c_\mu\tilde{\mathbf e}_\mu(r,\varphi)
\exp(i\gamma_\mu z).
$$

Using

$$
\gamma_\mu=\beta_\mu+i\alpha_{{\rm amp},\mu}
$$

we obtain

$$
\mathbf E_\perp(r,\varphi,z)
=
\sum_\mu
c_\mu\tilde{\mathbf e}_\mu(r,\varphi)
\exp(i\beta_\mu z)
\exp(-\alpha_{{\rm amp},\mu}z).
$$

The intensity is

$$
I(r,\varphi,z)
=
\left|
\mathbf E_\perp(r,\varphi,z)
\right|^2.
$$

Expanding the squared magnitude gives

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

The first term is the sum of the individual modal intensities. The second represents intermodal interference, which causes the transverse pattern to evolve along the capillary.

If many modes are present and their $\beta_\mu$ differ appreciably, their phases diverge quickly and the pattern changes over a short longitudinal distance.

## 19. Modal correlation and dephasing length

A compact estimate of the longitudinal scale uses the distribution of propagation constants $\beta_\mu$ with weights $w_\mu$.

The weights are taken as the modal powers or their coarse estimates:

$$
w_\mu\ge0.
$$

The mean is

$$
\bar\beta
=
\frac{\sum_\mu w_\mu\beta_\mu}
{\sum_\mu w_\mu}.
$$

The variance is

$$
\sigma_\beta^2
=
\frac{\sum_\mu w_\mu(\beta_\mu-\bar\beta)^2}
{\sum_\mu w_\mu}.
$$

The characteristic dephasing length is

$$
L_\phi=\frac{2\pi}{\sigma_\beta}.
$$

This expression follows from requiring the typical relative phase accumulated between modes over the distance $L_\phi$ to be of order $2\pi$:

$$
\sigma_\beta L_\phi\sim2\pi.
$$

For more detailed diagnostics, define the modal correlation:

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

At $z=0$,

$$
C(0)=1.
$$

As the modal phases diverge, the sum of complex phase factors decreases, and $C(z)$ falls. Local peaks in $C(z)$ mark distances where a significant part of the modal packet partially returns to phase alignment.

This mechanism is consistent with the field regeneration observed by [Jenkins, Devereux, 1992](https://doi.org/10.1364/AO.31.005086): when an input TEM00 beam excites several EH modes, recovery of their relative phases makes the transverse field resemble the input again, while it can take a different form between these positions.

The code extracts the following quantities from $C(z)$:

$$
z_{\rm first\ peak},
$$

$$
z_{\rm best\ peak},
$$

and

$$
L_\phi=\frac{2\pi}{\sigma_\beta}.
$$

## 20. Why the period decreases with launch angle

Use the approximation

$$
\beta(u)=\sqrt{k_0^2-\left(\frac{u}{a}\right)^2}.
$$

Differentiate:

$$
\frac{d\beta}{du}
=
\frac{1}{2}
\left[
k_0^2-\left(\frac{u}{a}\right)^2
\right]^{-1/2}
\left(-\frac{2u}{a^2}\right).
$$

Hence,

$$
\frac{d\beta}{du}
=
-
\frac{u}{a^2\beta}.
$$

However,

$$
u=k_0a\sin\theta,
$$

$$
\beta=k_0\cos\theta.
$$

Substituting gives

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

If the packet width in $u$ is

$$
\Delta u\sim\frac{a}{w_0},
$$

the width in $\beta$ is

$$
\sigma_\beta
\sim
\left|\frac{d\beta}{du}\right|\Delta u
\sim
\frac{\tan\theta}{a}\frac{a}{w_0}
=
\frac{\tan\theta}{w_0}.
$$

Then

$$
L_\phi
\sim
\frac{2\pi}{\sigma_\beta}
\sim
\frac{2\pi w_0}{\tan\theta}.
$$

This gives a useful physical estimate:

- At a larger launch angle $\theta$, the pattern evolves more rapidly.
- A larger beam radius $w_0$ gives a narrower angular spectrum, so the pattern evolves more slowly.

## 21. Transit times and the pulse model

The pulse model includes only intermodal delays. Frequency dispersion within each mode is neglected.

Start from the lossless modal dispersion relation:

$$
\beta(\omega)
=
\sqrt{
\left(\frac{\omega}{c}\right)^2
-
\left(\frac{u}{a}\right)^2
}.
$$

The group velocity is

$$
v_g=\frac{d\omega}{d\beta}
=
\left(\frac{d\beta}{d\omega}\right)^{-1}.
$$

Differentiate:

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

Since

$$
\beta=
\sqrt{
\left(\frac{\omega}{c}\right)^2
-
\left(\frac{u}{a}\right)^2
},
$$

we obtain

$$
\frac{d\beta}{d\omega}
=
\frac{\omega}{c^2\beta}.
$$

Therefore,

$$
v_g
=
\frac{c^2\beta}{\omega}.
$$

However,

$$
k_0=\frac{\omega}{c},
$$

so

$$
v_g
=
c\frac{\beta}{k_0}.
$$

Substitute

$$
\beta=k_0
\sqrt{
1-
\left(\frac{u}{k_0a}\right)^2
}.
$$

This gives

$$
\frac{v_g}{c}
=
\sqrt{
1-
\left(\frac{u}{k_0a}\right)^2
}.
$$

This is the expression used in the code.

The arrival time of a mode at distance $z$ is

$$
t_\mu(z)=\frac{z}{v_{g,\mu}}.
$$

The excess delay relative to propagation at the speed of light is

$$
\Delta t_\mu(z)
=
t_\mu(z)-\frac{z}{c}.
$$

For a delta-function input pulse, each mode produces a separate arrival with weight

$$
w_\mu(z)=w_\mu(0)\exp(-\alpha_{{\rm pow},\mu}z).
$$

A Gaussian temporal pulse is represented by the intensity

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

The relation between FWHM and $\sigma_t$ is

$$
\sigma_t
=
\frac{\mathrm{FWHM}}
{2\sqrt{2\ln2}}.
$$

The total temporal intensity in this model is

$$
I(t,z)
=
\sum_\mu I_\mu(t,z).
$$

The limitations of this model are:

- Intramodal dispersive broadening is neglected.
- Coherent interference at the carrier frequency is not included in the temporal signal.
- Only differences in modal group velocities and modal losses are included.

## 22. Complete calculation pipeline

The full sequence below follows the order used in the calculation.

### 22.1. Specify the waveguide parameters

$$
\lambda,\quad d,\quad a=d/2,\quad \varepsilon_m,\quad v=\sqrt{\varepsilon_m}.
$$

$$
k_0=\frac{2\pi}{\lambda}.
$$

### 22.2. Specify the input beam

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

### 22.3. Find the centre of the modal packet

$$
u_{\rm target}=ak_\perp.
$$

If a single polar angle is used,

$$
u_{\rm target}=k_0a\sin\theta.
$$

### 22.4. Find the selection window in \(u\)

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

After applying the limits,

$$
0\le u\le k_0a.
$$

### 22.5. Find the range of azimuthal orders

$$
q_{\max}
\simeq
\left\lceil
k_\perp(r_0+Fw_0)+q_{\rm margin}
\right\rceil.
$$

### 22.6. Generate candidate modes

Select the Bessel roots within the window:

$$
j_{\ell,m}\in[u_{\min},u_{\max}].
$$

The mode-family relations are

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

### 22.7. Solve the characteristic equations

For each mode, find

$$
\gamma_\mu=\beta_\mu+i\alpha_{{\rm amp},\mu}
$$

from the TE, TM, or hybrid equation.

Then,

$$
n_{{\rm eff},\mu}=\frac{\gamma_\mu}{k_0},
$$

$$
\alpha_{{\rm pow},\mu}=2\,\mathrm{Im}\,\gamma_\mu.
$$

### 22.8. Construct the transverse profiles and decompose the input

Construct $\tilde{\mathbf e}_\mu(x,y)$, then solve

$$
c=\arg\min_c\|Ac-y\|^2.
$$

The diagnostic quantities are

$$
P_{\rm in}=\|y\|^2,
$$

$$
P_{\rm coupled}=\|Ac\|^2,
$$

$$
P_{\rm residual}=P_{\rm in}-P_{\rm coupled}.
$$

The modal fraction is

$$
\eta_\mu=\frac{|c_\mu|^2}{P_{\rm in}}.
$$

### 22.9. Propagate the field

$$
\mathbf E(r,\varphi,z)
=
\sum_\mu
c_\mu\tilde{\mathbf e}_\mu(r,\varphi)
\exp(i\gamma_\mu z).
$$

The intensity is

$$
I(r,\varphi,z)=|\mathbf E(r,\varphi,z)|^2.
$$

### 22.10. Estimate longitudinal dephasing

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

### 22.11. Estimate pulse delays

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

The weight after propagation is

$$
w_\mu(z)=w_\mu(0)\exp(-\alpha_{{\rm pow},\mu}z).
$$

## 23. Main physical conclusions

1. The variable $u$ is more informative than the radial index $m$ alone, since $u/a$ is the transverse wavenumber of the mode.

2. A tilted beam excites modes near

$$
u_{\rm target}=k_0a\sin\theta.
$$

3. At large angles, $u_{\rm target}$ is large, so high-order modes must be included.

4. The packet width in $u$ is set by the beam's angular spectrum:

$$
\Delta u\sim\frac{a}{w_0}.
$$

5. The number of significant azimuthal harmonics grows as

$$
q\sim k_\perp w_0.
$$

6. Displacing the beam broadens its angular-harmonic content because the input field is no longer symmetric about the waveguide axis.

7. The longitudinal evolution of the intensity pattern is governed by intermodal interference:

$$
\exp[i(\beta_\mu-\beta_\nu)z].
$$

8. The characteristic distance over which the pattern changes is related to the spread in $\beta$:

$$
L_\phi=\frac{2\pi}{\sigma_\beta}.
$$

9. As the angle increases,

$$
\frac{d\beta}{du}\simeq-\frac{\tan\theta}{a},
$$

so the same width in $u$ produces a larger spread in $\beta$, and the pattern changes more rapidly.

10. In the pulse model, modes arrive at different times because their group velocities differ:

$$
\frac{v_g}{c}
=
\sqrt{1-\left(\frac{u}{k_0a}\right)^2}.
$$

## 24. Mapping the equations to project files

The main locations in the original `waveguide_practice` package are:

- `waveguide_practice/config.py`: $\lambda$, $d$, $a$, $k_0$, $\varepsilon_m$, $v$, and Gaussian-beam parameters.
- `waveguide_practice/cylindrical_modes.py`: TE/TM/HE/EH characteristic equations, Bessel-root initial estimates, solution for complex $\gamma$, $n_{\rm eff}$, and $\alpha_{\rm pow}$.
- `waveguide_practice/attenuation.py`: Fresnel estimates, roughness, ray-optical attenuation, and the Marcatili formula.
- `waveguide_practice/projection.py`: input Gaussian beam, transverse modal profiles, normalization, least-squares decomposition, and field propagation.
- `waveguide_practice/angular_analysis.py`: the $u$ window, $q_{\max}$ estimate, candidate-mode generation, polar quadrature, $C(z)$, $L_\phi$, and parameter sweeps over launch angle and displacement.
- `waveguide_practice/pulse.py`: group velocity, delays, Gaussian pulses, and delta-function arrivals.

The corresponding sources are:

- Modal equations, HE/EH families, and loss scaling: [Marcatili, Schmeltzer, 1964](https://doi.org/10.1002/j.1538-7305.1964.tb04108.x).
- Ray-optical interpretation of attenuation and its connection to wave-based calculations: [Miyagi, 1985](https://doi.org/10.1109/JLT.1985.1074177).
- Multimode transmission, angular distributions, and reflection coefficients: [Matsuura et al., 1989](https://doi.org/10.1364/JOSAA.6.000423), [Saito et al., 1993](https://doi.org/10.1364/JOSAA.10.000277).
- Field regeneration and longitudinal phase periodicity: [Jenkins, Devereux, 1992](https://doi.org/10.1364/AO.31.005086).
- Coupling losses and the lowest-order hybrid EH11 mode in resonators: [Abrams, 1972](https://doi.org/10.1109/JQE.1972.1076875).
- Experimental context of a silver Raman/SERS waveguide resonator: [Khannanov, Vankov, Kulik et al., 2021](https://doi.org/10.1109/JSEN.2021.3113373).

## 25. Formula reference

| Quantity | Formula |
|---|---|
| Vacuum wavenumber | $k_0=2\pi/\lambda$ |
| Radius | $a=d/2$ |
| Metal refractive index | $v=\sqrt{\varepsilon_m}$ |
| Modal transverse wavenumber | $k_{\perp,\mu}=u_\mu/a$ |
| Lossless longitudinal propagation constant | $\beta_\mu\simeq\sqrt{k_0^2-(u_\mu/a)^2}$ |
| Modal angle | $\theta_\mu=\arcsin[u_\mu/(k_0a)]$ |
| Excitation centre | $u_{\rm target}=k_0a\sin\theta$ |
| Selection half-width | $\Delta u=(a/w_0)\sqrt{2\ln(1/p_{\min})}$ |
| Azimuthal order | $q_{\max}\sim k_\perp(r_0+w_0)$ |
| Complex propagation constant | $\gamma=\beta+i\alpha_{\rm amp}$ |
| Power attenuation | $\alpha_{\rm pow}=2\,\mathrm{Im}\,\gamma$ |
| Marcatili estimate | $\alpha_{\rm M}=(u/2\pi)^2(\lambda^2/a^3)\mathrm{Re}\,\nu$ |
| Ray model | $\alpha_{\rm ray}=(1-R)\tan\theta/(2a)$ |
| Modal field | $\mathbf E(z)=\sum_\mu c_\mu\mathbf e_\mu e^{i\gamma_\mu z}$ |
| Modal correlation | $C(z)=|\sum_\mu w_\mu e^{i(\beta_\mu-\bar\beta)z}|^2/(\sum_\mu w_\mu)^2$ |
| Dephasing length | $L_\phi=2\pi/\sigma_\beta$ |
| Group velocity | $v_g/c=\sqrt{1-[u/(k_0a)]^2}$ |
| Arrival time | $t_\mu=z/v_{g,\mu}$ |

## 26. Possible extensions

These notes cover the current calculation and its main research sources. For a version intended as part of an internship report or research paper, useful additions would be:

1. A geometry diagram showing the capillary, radius $a$, launch angle $\theta$, and displacement $r_0$.
2. A diagram relating $u_{\rm target}=k_0a\sin\theta$ to the beam's angular spectrum.
3. An illustration of Bessel functions and the meaning of their zeros $j_{\ell,m}$.
4. A table of numerical parameters for specific notebook examples.
5. A separate chapter on SERS and plasmonic enhancement if the calculation is extended from modal propagation in a capillary to Raman-signal enhancement at the silver surface.

## 27. References

1. E. A. J. Marcatili, R. A. Schmeltzer, "Hollow Metallic and Dielectric Waveguides for Long Distance Optical Transmission and Lasers", Bell System Technical Journal, 1964. [Publication](https://doi.org/10.1002/j.1538-7305.1964.tb04108.x).
2. M. Miyagi, "Waveguide-Loss Evaluation in Circular Hollow Waveguides and Its Ray-Optical Treatment", Journal of Lightwave Technology, Vol. LT-3, No. 2, April 1985. [Publication](https://doi.org/10.1109/JLT.1985.1074177).
3. Y. Matsuura, M. Saito, M. Miyagi, A. Hongo, "Loss characteristics of circular hollow waveguides for incoherent infrared light", Journal of the Optical Society of America A, Vol. 6, No. 3, March 1989. [Publication](https://doi.org/10.1364/JOSAA.6.000423).
4. M. Saito, S. Sato, M. Miyagi, "Loss characteristics of infrared hollow waveguides in multimode transmission", Journal of the Optical Society of America A, Vol. 10, No. 2, February 1993. [Publication](https://doi.org/10.1364/JOSAA.10.000277).
5. R. L. Abrams, "Coupling Losses in Hollow Waveguide Laser Resonators", IEEE Journal of Quantum Electronics, Vol. QE-8, No. 11, November 1972. [Publication](https://doi.org/10.1109/JQE.1972.1076875).
6. R. M. Jenkins, R. W. J. Devereux, "Effect of field regeneration on the TEM00 transmission characteristics of a circular-section waveguide", 1992. [Publication](https://doi.org/10.1364/AO.31.005086).
7. M. N. Khannanov, A. B. Vankov, V. E. Kirpichev, L. V. Kulik, I. V. Kukushkin, "Express Analysis of Gas With Surface Enhanced Raman Scattering Waveguide Resonator", IEEE Sensors Journal, 2021. [Publication](https://doi.org/10.1109/JSEN.2021.3113373).
