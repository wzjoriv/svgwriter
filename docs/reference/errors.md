# Errors

Every error svgwriter raises on purpose lives in `svgwriter.errors` (`svg.errors.ThemeError`, ...). Each
subclasses the built-in exception a caller would expect, so `except ValueError` keeps working.

```{eval-rst}
.. automodule:: svgwriter.errors
   :members:
```
