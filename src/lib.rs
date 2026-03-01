mod map2d;
pub use map2d::*;

use pyo3::prelude::*;

#[pymodule]
mod baggo {
    use pyo3::prelude::*;

    #[pyfunction]
    fn add_numbers(a: usize, b: usize) -> usize {
        a + b
    }

    #[pymodule_export]
    use super::map2d::Map2D;
}