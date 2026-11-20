from .matrix import Matrix

__all__ = ["MatrixConstructors"]

class MatrixConstructors:
    @classmethod
    def translate(cls, tx: float, ty: float = 0.0) -> Matrix: ...
    @classmethod
    def scale(cls, sx: float, sy: float | None = None) -> Matrix: ...
    @classmethod
    def rotate(
        cls,
        angle: float,
        cx: float = 0.0,
        cy: float = 0.0,
    ) -> Matrix: ...
    @classmethod
    def flip_x(cls, x: float = 0.0) -> Matrix: ...
    @classmethod
    def flip_y(cls, y: float = 0.0) -> Matrix: ...
    @classmethod
    def skew_x(cls, angle: float) -> Matrix: ...
    @classmethod
    def skew_y(cls, angle: float) -> Matrix: ...
