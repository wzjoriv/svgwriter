# Preset libraries

Ready-made patterns, gradients, filters, markers and effects; see the [Presets guide](../guides/presets.md)
for pictures of each. `@svg.preset.pattern`, `filter`, `gradient`, `marker` and `effect` (documented
under [Composite shapes and effects](paths.md)) add your own to these catalogues.

```{eval-rst}
.. automodule:: svgwriter.library.patterns
   :members:

.. automodule:: svgwriter.library.gradients
   :members:

.. automodule:: svgwriter.library.filters
   :members:

.. automodule:: svgwriter.library.markers
   :members:

.. automodule:: svgwriter.library.effects
   :members:
```

## Registries

Every registry (the preset kinds, `svg.themes`, `svg.formats`, `svg.renderers`, `svg.project.presets` and
the command line's `commands`) is a `Registry`; see [Extending svgwriter](../guides/extending.md).

```{eval-rst}
.. autoclass:: svgwriter.Registry
   :members: register, list, get, unregister, find

```
