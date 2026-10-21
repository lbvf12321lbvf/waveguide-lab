# Waveguide Lab

**[Open the application](https://lbvf12321lbvf.github.io/waveguide-lab/)** · **[Full theory](https://lbvf12321lbvf.github.io/waveguide-lab/theory.html)**

A browser-based calculator for hollow metal waveguides, developed by **Dmitry Shchigarev**. Contact: [dima.shigarev@yandex.ru](mailto:dima.shigarev@yandex.ru).

Python, NumPy and SciPy run locally through Pyodide in a Web Worker. No calculation server or account is required. The interface and the complete theory are in English.

## Features

- Gaussian input with adjustable waist, angle, offset and polarization. Drag the beam centre in the live preview, or use the arrow keys (Shift for larger steps).
- Complex propagation constants for HE, EH, TE and TM modes; joint vector least-squares projection.
- Automatic basis selection from the launch parameters, expanding until the input projection residual reaches 0.1% or a reported resource limit. A manual mode limit is available in Advanced settings.
- Intensity, phase and input maps, longitudinal sections and coherent power. The default power axis is 0–100%; Detail resolves small losses. Genuine computed values above 100% remain visible and trigger a model warning.
- Click a mode in the simulation or experiment table to inspect it. Mode lab also accepts arbitrary family / n / m / orientation and constructs coherent sums of up to 12 profiles with independent amplitudes and phases.
- PNG, TIFF, JPEG, BMP and SPE 2.x image analysis, preserving scientific 16-bit intensities. Interactive circular ROI, optional wall-edge refinement, and a movable slit aperture at any angle. Only the interior of the slit is measured.
- Individual-mode search, automatic small-mixture fitting, or a coherent fit restricted to 1–6 explicitly selected physical modes. Fits use three initial guesses.
- PNG / CSV / JSON exports, calculation-file import and local history of the last 12 simulations.
- Stop cancels the current worker without discarding results already shown.
- Full theory reader: 28 chapters in English, complete derivations and formulas, table of contents, print support and a Markdown download. Seven linked research papers explain the model's provenance.

## Use

1. The initial screen shows a clearly labelled precomputed reference example.
2. Configure the waveguide and input beam; select **Run simulation**. The first launch downloads Python and scientific packages from jsDelivr and may take about a minute.
3. Move the section slider, inspect modes, or open **Mode lab** to construct a field independently.
4. In **Experiment**, load an image or the synthetic HE₁,₃ example. Click to set the ROI centre; Shift + click sets its radius. Enter the physical radius before comparing profiles.
5. Enable **Use only the area inside the slit** to discard the surroundings. Use Horizontal / Vertical, enter an angle, or choose **Draw slit** and drag along its axis. In **Edit slit**, drag the centre to move, the two edge handles to change width, and the white handle to rotate. **Edit ROI** switches back to the circular boundary.
6. Start with **Single-mode search**, then use **Add to fit** next to candidate modes. **Fit selected modes** also accepts family / n / m / orientation directly and fits exactly the listed basis. **Automatic mixture** chooses up to four candidates itself.

For a manually bounded simulation, open **Advanced settings → Mode selection → Manual** and enter **Maximum modes**. This caps the number of physical modes selected from the excited candidates; HE and EH can each contribute two orientation profiles. The result reports the actual number used.

**Save calculation** downloads a JSON file containing the settings, modal coefficients, power curve, input field and current section. **Load calculation** restores such a file. A new simulation is required to generate additional sections after loading a file or history entry, or after stopping the worker. Mode lab JSON is a separate export of its mixture and result.

## Model and limits

The model assumes a straight, smooth, circular hollow metal guide with an air core. Approximate vector profiles use Bessel functions; complex propagation constants are obtained from characteristic equations. This is not a full-vector FEM solver or a model of SERS enhancement. Bends, roughness, pulse propagation and parameter sweeps are not implemented in the browser. The original theory document discusses these broader desktop-project topics explicitly.

Projection uses joint least squares with SVD (`rcond=1e-9`). Normalized `|c|²` values are **not independent power fractions** in a nonorthogonal basis. Propagated power includes cross terms. Intensity maps are normalized independently; consult the power readout for attenuation. Phase belongs to the dominant Ex/Ey component, with a common carrier removed.

If a complex root fails to converge, propagation uses the source project's Marcatili approximation, explicitly marked in the table. Check convergence by increasing resolution and basis size. Small projection residuals do not establish physical accuracy. HE/EH naming follows the source code's Bessel-root convention and can differ from the papers.

The web simulation uses CPU and a grid up to **256 × 256**. There is no fixed 128-mode ceiling: the usable basis depends on grid size, modal orders and a conservative **650 MiB working-memory budget**, including both vector components and solver workspace. The candidate catalogue and manual upper bound are limited to 6000 physical modes; this is not a promise that a 6000-mode solve will fit in browser memory. Automatic selection reports whether it reached its 0.1% input-projection target or stopped at a grid, memory or candidate limit. The target does not bound propagation error. Manual requests that exceed the resource budget or sampling limit are rejected. High angles, narrow waists or high modal orders may require the desktop version. Mode lab supports at most 12 profiles and checks their spatial sampling independently.

One intensity image cannot identify unique modal phases. Similarity scores are diagnostics. The image catalogue supports up to 1500 modes; working images are reduced to at most 1024 pixels on the longer side. File limits: 32 MiB and 16 million pixels. Export SPE 3.x as TIFF. Use original monochrome intensity data for scientific pseudocolour images.

Slit angles are clockwise in camera coordinates; widths and centres refer to the working image in pixels. Background subtraction, radial profiles, ranking and coherent fitting exclude pixels outside the slit. Missing data are masked, not treated as measured zero intensity. Selected fits bypass the search catalogue and use only the requested modes (up to 12 orientation profiles). Fitted profiles are normalized to unit RMS field over the measured region; exported coefficients include the corresponding `profile_rms` factors. Relative amplitudes are not modal power fractions. A narrow slit provides less information and can make different mixtures harder to distinguish.

## Local development

Node.js 22 or later; no npm dependencies:

```sh
node scripts/build.mjs
node scripts/serve.mjs
```

Open `http://127.0.0.1:4173`. ES modules and workers require HTTP; opening through `file://` is unsupported.

```sh
python -m pip install -r requirements-test.txt
python -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/*.test.mjs
```

`python/waveguide_core/` contains the numerical core ported from the desktop project. `python/web_engine.py` is the browser adapter and validation boundary. `beam.js` renders the interactive input; `modes.js` manages the independent modal window. Pyodide is pinned to **314.0.7** with its matching NumPy / SciPy / Pillow packages. MathJax **3.2.2** renders the original formulas. Scientific files are never evaluated as code or loaded through pickle.

The generated `theory.html` is committed. To rebuild it from the English `assets/theory.md`, install `Markdown==3.8.2` and run `python scripts/build-theory.py`. Formula source is protected before Markdown conversion. The translation preserves all 565 mathematical expressions from `assets/theory-original.md`, which remains in the repository for provenance and is excluded from the published site.

## Deployment and data

In repository **Settings → Pages**, select **GitHub Actions**. Every push to `main` runs tests, builds an explicit allowlist into `dist/`, and deploys it. All application URLs are relative and support a Pages project subdirectory. The public bundle contains only the application, its theory notes and reference calculation; research images, reports and local environments are excluded.

Source code and the deployed site are public. Images are processed in the browser; the app has no analytics or server storage. Initial downloads use GitHub Pages and jsDelivr. Browser history is temporary; download JSON for durable storage. See [VALIDATION.md](VALIDATION.md) for performed checks and their limits.

## Dependencies and rights

Pyodide, NumPy, SciPy, Pillow and MathJax retain their respective licences in their distributed packages. SPE 2.x uses a small original header reader; no third-party WinSpec reader is bundled. Publisher PDFs are linked, not redistributed. The public repository does not by itself grant an open-source licence; the owner has not selected a project licence.
