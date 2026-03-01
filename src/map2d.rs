use pyo3::prelude::*;
use pyo3::types::{PyDict, PyTuple};

#[pyclass(subclass)]
pub struct Map2D {
    #[pyo3(get, set)]
    width: i32,
    #[pyo3(get, set)]
    height: i32
}

#[pymethods]
impl Map2D {

    #[new]
    #[pyo3(signature = (width, height, *_args, **_kwargs))]
    fn new(width: i32, height: i32, _args: &Bound<'_, PyTuple>, _kwargs: Option<&Bound<'_, PyDict>>) -> PyResult<Self> {
        Ok(Self {
            width,
            height
        })
    }

    fn in_bounds(&self, x: i32, y: i32) -> bool {
        0 <= x && x < self.width && 0 <= y && y < self.height
    }

    fn index(&self, x: i32, y: i32) -> i32 {
        (y * self.width) + x
    }

    fn point(&self, index: i32) -> (i32, i32) {
        (index % self.width, index / self.width)
    }


}