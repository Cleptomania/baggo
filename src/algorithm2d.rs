use pyo3::prelude::*;

#[derive(Clone)]
#[pyclass(subclass, from_py_object)]
pub struct Algorithm2D {
    #[pyo3(get, set)]
    pub width: i32,
    #[pyo3(get, set)]
    pub height: i32
}

#[pymethods]
impl Algorithm2D {

    #[new]
    fn new(width: i32, height: i32) -> Self {
        Self {
            width,
            height
        }
    }

    pub fn in_bounds(&self, x: i32, y: i32) -> bool {
        0 <= x && x < self.width && 0 <= y && y < self.height
    }

    pub fn index(&self, x: i32, y: i32) -> i32 {
        (y * self.width) + x
    }

    pub fn point(&self, index: i32) -> (i32, i32) {
        (index % self.width, index / self.width)
    }

    pub fn dimensions(&self) -> (i32, i32) {
        (self.width, self.height)
    }
}
