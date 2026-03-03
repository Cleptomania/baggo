mod algorithm2d;
mod recursive_shadowcasting;
mod geometry;

pub use algorithm2d::*;

use pyo3::prelude::*;

#[pymodule]
mod baggo {
    use pyo3::prelude::*;

    #[pyfunction]
    fn add_numbers(a: usize, b: usize) -> usize {
        a + b
    }

    #[pymodule_export]
    use super::algorithm2d::Algorithm2D;

    #[pymodule_export]
    use super::recursive_shadowcasting::field_of_view;
}