mod algorithm2d;
mod geometry;
mod recursive_shadowcasting;

pub use algorithm2d::*;

use pyo3::prelude::*;

#[pymodule]
mod _core {
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
