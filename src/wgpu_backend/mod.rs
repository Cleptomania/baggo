use std::borrow::Cow;
use std::sync::Arc;
use std::time::Instant;

use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use pyo3::types::{PyAnyMethods, PySet};
use wgpu::util::DeviceExt;
use winit::application::ApplicationHandler;
use winit::dpi::PhysicalSize;
use winit::event::{ElementState, KeyEvent, Modifiers, WindowEvent};
use winit::event_loop::{ActiveEventLoop, EventLoop};
use winit::window::{Window, WindowId};

mod keys;

use keys::{modifiers_bitflags, translate_key};

#[repr(C)]
#[derive(Copy, Clone, bytemuck::Pod, bytemuck::Zeroable)]
struct Vertex {
    vert: [f32; 2],
    uv: [f32; 2],
}

#[repr(C)]
#[derive(Copy, Clone, bytemuck::Pod, bytemuck::Zeroable)]
struct Instance {
    pos: [f32; 2],
    tex_offset: [f32; 2],
    fg_color: [f32; 4],
    bg_color: [f32; 4],
}

#[repr(C)]
#[derive(Copy, Clone, bytemuck::Pod, bytemuck::Zeroable)]
struct Uniforms {
    glyph_size: [f32; 2],
    screen_size: [f32; 2],
    glyph_uv_size: [f32; 2],
    _pad: [f32; 2],
}

// UV is the same as `vert` because wgpu's texture sampling has UV (0,0) at the top-left of the
// image (matching memory layout). The arcade backend uses OpenGL, whose default convention puts
// UV (0,0) at the bottom-left — which is why its shader flips UVs vertically. Here we don't flip
// and instead compute tex offsets in natural top-down order.
const VERTICES: [Vertex; 6] = [
    Vertex {
        vert: [0.0, 0.0],
        uv: [0.0, 0.0],
    },
    Vertex {
        vert: [1.0, 0.0],
        uv: [1.0, 0.0],
    },
    Vertex {
        vert: [0.0, 1.0],
        uv: [0.0, 1.0],
    },
    Vertex {
        vert: [1.0, 0.0],
        uv: [1.0, 0.0],
    },
    Vertex {
        vert: [1.0, 1.0],
        uv: [1.0, 1.0],
    },
    Vertex {
        vert: [0.0, 1.0],
        uv: [0.0, 1.0],
    },
];

/// Per-terminal static configuration. Pulled from Python once at startup.
#[derive(Clone)]
struct Config {
    title: String,
    pixel_width: u32,
    pixel_height: u32,
    grid_width: u32,
    grid_height: u32,
    tile_width: u32,
    tile_height: u32,
    font_image_path: String,
}

/// Owns all GPU resources for an active window.
struct GpuState {
    surface: wgpu::Surface<'static>,
    device: wgpu::Device,
    queue: wgpu::Queue,
    surface_config: wgpu::SurfaceConfiguration,
    pipeline: wgpu::RenderPipeline,
    vertex_buffer: wgpu::Buffer,
    instance_buffer: wgpu::Buffer,
    // Held so the GPU-side uniform buffer lives as long as the bind group that references it.
    #[allow(dead_code)]
    uniform_buffer: wgpu::Buffer,
    bind_group: wgpu::BindGroup,
    instance_capacity: u32,
    atlas_columns: u32,
    atlas_rows: u32,
    // CPU-side mirror of instance data: 12 floats per tile.
    cpu_instances: Vec<f32>,
    instance_count: u32,
}

impl GpuState {
    fn new(window: Arc<Window>, cfg: &Config) -> Result<Self, String> {
        let instance = wgpu::Instance::new(wgpu::InstanceDescriptor::new_without_display_handle());

        let surface = instance
            .create_surface(window.clone())
            .map_err(|e| format!("create_surface: {e}"))?;

        let adapter = pollster::block_on(instance.request_adapter(&wgpu::RequestAdapterOptions {
            power_preference: wgpu::PowerPreference::default(),
            force_fallback_adapter: false,
            compatible_surface: Some(&surface),
        }))
        .map_err(|e| format!("request_adapter: {e}"))?;

        let (device, queue) = pollster::block_on(adapter.request_device(&wgpu::DeviceDescriptor {
            label: Some("baggo.wgpu.device"),
            required_features: wgpu::Features::empty(),
            required_limits: wgpu::Limits::downlevel_defaults().using_resolution(adapter.limits()),
            memory_hints: wgpu::MemoryHints::default(),
            trace: wgpu::Trace::Off,
            experimental_features: wgpu::ExperimentalFeatures::default(),
        }))
        .map_err(|e| format!("request_device: {e}"))?;

        let size = window.inner_size();
        let surface_caps = surface.get_capabilities(&adapter);
        // Prefer a non-sRGB 8-bit-per-channel surface format so color values written from the
        // shader are displayed as-is, matching the arcade/pyglet backend (no gamma conversion).
        // Filtering to 8-bit formats avoids picking Rgba16Unorm and similar formats that require
        // extra device features we didn't enable.
        let format = surface_caps
            .formats
            .iter()
            .copied()
            .find(|f| {
                matches!(
                    f,
                    wgpu::TextureFormat::Rgba8Unorm | wgpu::TextureFormat::Bgra8Unorm
                )
            })
            .or_else(|| surface_caps.formats.iter().copied().find(|f| !f.is_srgb()))
            .unwrap_or(surface_caps.formats[0]);
        let surface_config = wgpu::SurfaceConfiguration {
            usage: wgpu::TextureUsages::RENDER_ATTACHMENT,
            format,
            width: size.width.max(1),
            height: size.height.max(1),
            present_mode: surface_caps.present_modes[0],
            alpha_mode: surface_caps.alpha_modes[0],
            view_formats: vec![],
            desired_maximum_frame_latency: 2,
        };
        surface.configure(&device, &surface_config);

        let (font_texture, atlas_columns, atlas_rows) =
            load_font_texture(&device, &queue, cfg).map_err(|e| format!("font load: {e}"))?;
        let font_view = font_texture.create_view(&wgpu::TextureViewDescriptor::default());
        let font_sampler = device.create_sampler(&wgpu::SamplerDescriptor {
            label: Some("baggo.wgpu.sampler"),
            address_mode_u: wgpu::AddressMode::ClampToEdge,
            address_mode_v: wgpu::AddressMode::ClampToEdge,
            address_mode_w: wgpu::AddressMode::ClampToEdge,
            mag_filter: wgpu::FilterMode::Nearest,
            min_filter: wgpu::FilterMode::Nearest,
            mipmap_filter: wgpu::MipmapFilterMode::Nearest,
            ..Default::default()
        });

        let uniforms = Uniforms {
            glyph_size: [cfg.tile_width as f32, cfg.tile_height as f32],
            screen_size: [cfg.pixel_width as f32, cfg.pixel_height as f32],
            glyph_uv_size: [1.0 / atlas_columns as f32, 1.0 / atlas_rows as f32],
            _pad: [0.0, 0.0],
        };
        let uniform_buffer = device.create_buffer_init(&wgpu::util::BufferInitDescriptor {
            label: Some("baggo.wgpu.uniforms"),
            contents: bytemuck::bytes_of(&uniforms),
            usage: wgpu::BufferUsages::UNIFORM | wgpu::BufferUsages::COPY_DST,
        });

        let bind_group_layout = device.create_bind_group_layout(&wgpu::BindGroupLayoutDescriptor {
            label: Some("baggo.wgpu.bgl"),
            entries: &[
                wgpu::BindGroupLayoutEntry {
                    binding: 0,
                    visibility: wgpu::ShaderStages::VERTEX | wgpu::ShaderStages::FRAGMENT,
                    ty: wgpu::BindingType::Buffer {
                        ty: wgpu::BufferBindingType::Uniform,
                        has_dynamic_offset: false,
                        min_binding_size: None,
                    },
                    count: None,
                },
                wgpu::BindGroupLayoutEntry {
                    binding: 1,
                    visibility: wgpu::ShaderStages::FRAGMENT,
                    ty: wgpu::BindingType::Texture {
                        sample_type: wgpu::TextureSampleType::Float { filterable: false },
                        view_dimension: wgpu::TextureViewDimension::D2,
                        multisampled: false,
                    },
                    count: None,
                },
                wgpu::BindGroupLayoutEntry {
                    binding: 2,
                    visibility: wgpu::ShaderStages::FRAGMENT,
                    ty: wgpu::BindingType::Sampler(wgpu::SamplerBindingType::NonFiltering),
                    count: None,
                },
            ],
        });

        let bind_group = device.create_bind_group(&wgpu::BindGroupDescriptor {
            label: Some("baggo.wgpu.bg"),
            layout: &bind_group_layout,
            entries: &[
                wgpu::BindGroupEntry {
                    binding: 0,
                    resource: uniform_buffer.as_entire_binding(),
                },
                wgpu::BindGroupEntry {
                    binding: 1,
                    resource: wgpu::BindingResource::TextureView(&font_view),
                },
                wgpu::BindGroupEntry {
                    binding: 2,
                    resource: wgpu::BindingResource::Sampler(&font_sampler),
                },
            ],
        });

        let shader = device.create_shader_module(wgpu::ShaderModuleDescriptor {
            label: Some("baggo.wgpu.shader"),
            source: wgpu::ShaderSource::Wgsl(Cow::Borrowed(include_str!("shader.wgsl"))),
        });

        let pipeline_layout = device.create_pipeline_layout(&wgpu::PipelineLayoutDescriptor {
            label: Some("baggo.wgpu.pipeline_layout"),
            bind_group_layouts: &[Some(&bind_group_layout)],
            immediate_size: 0,
        });

        let pipeline = device.create_render_pipeline(&wgpu::RenderPipelineDescriptor {
            label: Some("baggo.wgpu.pipeline"),
            layout: Some(&pipeline_layout),
            vertex: wgpu::VertexState {
                module: &shader,
                entry_point: Some("vs_main"),
                compilation_options: Default::default(),
                buffers: &[
                    wgpu::VertexBufferLayout {
                        array_stride: std::mem::size_of::<Vertex>() as wgpu::BufferAddress,
                        step_mode: wgpu::VertexStepMode::Vertex,
                        attributes: &wgpu::vertex_attr_array![0 => Float32x2, 1 => Float32x2],
                    },
                    wgpu::VertexBufferLayout {
                        array_stride: std::mem::size_of::<Instance>() as wgpu::BufferAddress,
                        step_mode: wgpu::VertexStepMode::Instance,
                        attributes: &wgpu::vertex_attr_array![
                            2 => Float32x2,
                            3 => Float32x2,
                            4 => Float32x4,
                            5 => Float32x4,
                        ],
                    },
                ],
            },
            fragment: Some(wgpu::FragmentState {
                module: &shader,
                entry_point: Some("fs_main"),
                compilation_options: Default::default(),
                targets: &[Some(wgpu::ColorTargetState {
                    format,
                    blend: Some(wgpu::BlendState::REPLACE),
                    write_mask: wgpu::ColorWrites::ALL,
                })],
            }),
            primitive: wgpu::PrimitiveState {
                topology: wgpu::PrimitiveTopology::TriangleList,
                ..Default::default()
            },
            depth_stencil: None,
            multisample: wgpu::MultisampleState::default(),
            multiview_mask: None,
            cache: None,
        });

        let vertex_buffer = device.create_buffer_init(&wgpu::util::BufferInitDescriptor {
            label: Some("baggo.wgpu.vertices"),
            contents: bytemuck::cast_slice(&VERTICES),
            usage: wgpu::BufferUsages::VERTEX,
        });

        let instance_capacity = cfg.grid_width * cfg.grid_height;
        let cpu_instances = vec![0.0f32; (instance_capacity as usize) * 12];
        let instance_buffer = device.create_buffer(&wgpu::BufferDescriptor {
            label: Some("baggo.wgpu.instances"),
            size: (cpu_instances.len() * std::mem::size_of::<f32>()) as wgpu::BufferAddress,
            usage: wgpu::BufferUsages::VERTEX | wgpu::BufferUsages::COPY_DST,
            mapped_at_creation: false,
        });

        Ok(Self {
            surface,
            device,
            queue,
            surface_config,
            pipeline,
            vertex_buffer,
            instance_buffer,
            uniform_buffer,
            bind_group,
            instance_capacity,
            atlas_columns,
            atlas_rows,
            cpu_instances,
            instance_count: instance_capacity,
        })
    }

    fn resize(&mut self, new: PhysicalSize<u32>) {
        if new.width == 0 || new.height == 0 {
            return;
        }
        self.surface_config.width = new.width;
        self.surface_config.height = new.height;
        self.surface.configure(&self.device, &self.surface_config);
    }

    fn upload_instances(&self) {
        self.queue.write_buffer(
            &self.instance_buffer,
            0,
            bytemuck::cast_slice(&self.cpu_instances),
        );
    }

    fn render(&mut self) -> RenderOutcome {
        let frame = match self.surface.get_current_texture() {
            wgpu::CurrentSurfaceTexture::Success(t)
            | wgpu::CurrentSurfaceTexture::Suboptimal(t) => t,
            wgpu::CurrentSurfaceTexture::Outdated | wgpu::CurrentSurfaceTexture::Lost => {
                return RenderOutcome::Reconfigure;
            }
            wgpu::CurrentSurfaceTexture::Timeout | wgpu::CurrentSurfaceTexture::Occluded => {
                return RenderOutcome::Skip;
            }
            wgpu::CurrentSurfaceTexture::Validation => {
                return RenderOutcome::Error("wgpu: surface validation error".into());
            }
        };
        let view = frame
            .texture
            .create_view(&wgpu::TextureViewDescriptor::default());
        let mut encoder = self
            .device
            .create_command_encoder(&wgpu::CommandEncoderDescriptor {
                label: Some("baggo.wgpu.encoder"),
            });
        {
            let mut rpass = encoder.begin_render_pass(&wgpu::RenderPassDescriptor {
                label: Some("baggo.wgpu.rpass"),
                color_attachments: &[Some(wgpu::RenderPassColorAttachment {
                    view: &view,
                    resolve_target: None,
                    depth_slice: None,
                    ops: wgpu::Operations {
                        load: wgpu::LoadOp::Clear(wgpu::Color::BLACK),
                        store: wgpu::StoreOp::Store,
                    },
                })],
                depth_stencil_attachment: None,
                occlusion_query_set: None,
                timestamp_writes: None,
                multiview_mask: None,
            });
            rpass.set_pipeline(&self.pipeline);
            rpass.set_bind_group(0, &self.bind_group, &[]);
            rpass.set_vertex_buffer(0, self.vertex_buffer.slice(..));
            rpass.set_vertex_buffer(1, self.instance_buffer.slice(..));
            rpass.draw(0..VERTICES.len() as u32, 0..self.instance_count);
        }
        self.queue.submit(Some(encoder.finish()));
        frame.present();
        RenderOutcome::Ok
    }
}

enum RenderOutcome {
    Ok,
    Skip,
    Reconfigure,
    Error(String),
}

fn load_font_texture(
    device: &wgpu::Device,
    queue: &wgpu::Queue,
    cfg: &Config,
) -> Result<(wgpu::Texture, u32, u32), String> {
    let img = image::open(&cfg.font_image_path)
        .map_err(|e| format!("failed to open {}: {e}", cfg.font_image_path))?
        .to_rgba8();
    let (iw, ih) = img.dimensions();
    let columns = iw / cfg.tile_width;
    let rows = ih / cfg.tile_height;
    if columns == 0 || rows == 0 {
        return Err(format!(
            "font image {}x{} too small for tile {}x{}",
            iw, ih, cfg.tile_width, cfg.tile_height
        ));
    }

    let texture = device.create_texture(&wgpu::TextureDescriptor {
        label: Some("baggo.wgpu.font_texture"),
        size: wgpu::Extent3d {
            width: iw,
            height: ih,
            depth_or_array_layers: 1,
        },
        mip_level_count: 1,
        sample_count: 1,
        dimension: wgpu::TextureDimension::D2,
        format: wgpu::TextureFormat::Rgba8Unorm,
        usage: wgpu::TextureUsages::TEXTURE_BINDING | wgpu::TextureUsages::COPY_DST,
        view_formats: &[],
    });

    queue.write_texture(
        wgpu::TexelCopyTextureInfo {
            texture: &texture,
            mip_level: 0,
            origin: wgpu::Origin3d::ZERO,
            aspect: wgpu::TextureAspect::All,
        },
        &img,
        wgpu::TexelCopyBufferLayout {
            offset: 0,
            bytes_per_row: Some(4 * iw),
            rows_per_image: Some(ih),
        },
        wgpu::Extent3d {
            width: iw,
            height: ih,
            depth_or_array_layers: 1,
        },
    );
    Ok((texture, columns, rows))
}

struct TerminalApp {
    cfg: Config,
    py_app: Py<PyAny>,
    py_console: Py<PyAny>,
    window: Option<Arc<Window>>,
    gpu: Option<GpuState>,
    last_frame: Option<Instant>,
    modifiers: Modifiers,
    capslock: bool,
    /// Surface any Python error raised from inside a winit callback so that `run` can return it.
    pending_error: Option<PyErr>,
}

impl TerminalApp {
    fn new(cfg: Config, py_app: Py<PyAny>, py_console: Py<PyAny>) -> Self {
        Self {
            cfg,
            py_app,
            py_console,
            window: None,
            gpu: None,
            last_frame: None,
            modifiers: Modifiers::default(),
            capslock: false,
            pending_error: None,
        }
    }

    fn dispatch_key(&mut self, event: &KeyEvent) {
        if event.repeat && matches!(event.state, ElementState::Pressed) {
            // baggo treats key-down as an edge event, matching the arcade backend.
            return;
        }
        let shift_held = self.modifiers.state().shift_key();
        let key = translate_key(
            &event.logical_key,
            &event.physical_key,
            event.text.as_ref(),
            event.state,
            shift_held,
        );
        let Some(key) = key else { return };

        let method = match event.state {
            ElementState::Pressed => "on_key_down",
            ElementState::Released => "on_key_up",
        };
        let bits = modifiers_bitflags(&self.modifiers, self.capslock);

        let result: PyResult<()> = Python::attach(|py| {
            self.py_app.call_method1(py, method, (key, bits))?;
            Ok(())
        });
        if let Err(e) = result {
            self.pending_error.get_or_insert(e);
        }
    }

    fn tick_and_update(&mut self) -> PyResult<()> {
        let now = Instant::now();
        let delta = self
            .last_frame
            .replace(now)
            .map(|t| now - t)
            .unwrap_or_default();
        let delta_secs = delta.as_secs_f32();

        Python::attach(|py| -> PyResult<()> {
            self.py_app.call_method1(py, "tick", (delta_secs,))?;

            let gpu = match self.gpu.as_mut() {
                Some(g) => g,
                None => return Ok(()),
            };

            let dirty_obj = self.py_console.getattr(py, "dirty_tiles")?;
            let dirty_any = dirty_obj.bind(py);
            let mut indices: Vec<i64> = Vec::new();
            if let Ok(set) = dirty_any.cast::<PySet>() {
                indices.reserve(set.len());
                for item in set.iter() {
                    indices.push(item.extract::<i64>()?);
                }
            } else {
                for item in dirty_any.try_iter()? {
                    indices.push(item?.extract::<i64>()?);
                }
            }

            let width = self.cfg.grid_width as i64;
            let height = self.cfg.grid_height as i64;
            let tile_w = self.cfg.tile_width as f32;
            let tile_h = self.cfg.tile_height as f32;
            let cols = gpu.atlas_columns as f32;
            let rows = gpu.atlas_rows as f32;
            let capacity = gpu.instance_capacity as i64;

            for idx in indices {
                if idx < 0 || idx >= capacity {
                    continue;
                }
                let x = idx % width;
                let y = height - 1 - ((idx - x) / width);
                let tile = self
                    .py_console
                    .call_method1(py, "at", (x as i32, y as i32))?;
                if tile.is_none(py) {
                    continue;
                }
                let glyph: i32 = tile.getattr(py, "glyph")?.extract(py)?;
                let fg: (u8, u8, u8, u8) = tile.getattr(py, "foreground")?.extract(py)?;
                let bg: (u8, u8, u8, u8) = tile.getattr(py, "background")?.extract(py)?;

                let glyph_col = (glyph as u32).rem_euclid(gpu.atlas_columns) as f32;
                let glyph_row = (glyph as u32 / gpu.atlas_columns) as f32;
                let gx = glyph_col / cols;
                let gy = glyph_row / rows;

                let px = (x as f32) * tile_w;
                let py_ = (y as f32) * tile_h;

                let off = (idx as usize) * 12;
                let buf = &mut gpu.cpu_instances;
                buf[off] = px;
                buf[off + 1] = py_;
                buf[off + 2] = gx;
                buf[off + 3] = gy;
                buf[off + 4] = fg.0 as f32 / 255.0;
                buf[off + 5] = fg.1 as f32 / 255.0;
                buf[off + 6] = fg.2 as f32 / 255.0;
                buf[off + 7] = 1.0;
                buf[off + 8] = bg.0 as f32 / 255.0;
                buf[off + 9] = bg.1 as f32 / 255.0;
                buf[off + 10] = bg.2 as f32 / 255.0;
                buf[off + 11] = 1.0;
            }

            self.py_console.call_method0(py, "clear_dirty")?;
            Ok(())
        })?;

        if let Some(gpu) = self.gpu.as_ref() {
            gpu.upload_instances();
        }
        Ok(())
    }
}

impl ApplicationHandler for TerminalApp {
    fn resumed(&mut self, event_loop: &ActiveEventLoop) {
        if self.window.is_some() {
            return;
        }
        let attrs = Window::default_attributes()
            .with_title(&self.cfg.title)
            .with_inner_size(PhysicalSize::new(
                self.cfg.pixel_width,
                self.cfg.pixel_height,
            ))
            .with_resizable(false);
        let window = match event_loop.create_window(attrs) {
            Ok(w) => Arc::new(w),
            Err(e) => {
                self.pending_error
                    .get_or_insert_with(|| PyRuntimeError::new_err(format!("create_window: {e}")));
                event_loop.exit();
                return;
            }
        };
        match GpuState::new(window.clone(), &self.cfg) {
            Ok(gpu) => {
                self.gpu = Some(gpu);
                self.window = Some(window);
            }
            Err(e) => {
                self.pending_error
                    .get_or_insert_with(|| PyRuntimeError::new_err(e));
                event_loop.exit();
            }
        }
    }

    fn window_event(
        &mut self,
        event_loop: &ActiveEventLoop,
        _window_id: WindowId,
        event: WindowEvent,
    ) {
        match event {
            WindowEvent::CloseRequested => {
                event_loop.exit();
            }
            WindowEvent::Resized(size) => {
                if let Some(gpu) = self.gpu.as_mut() {
                    gpu.resize(size);
                }
            }
            WindowEvent::ModifiersChanged(m) => {
                self.modifiers = m;
            }
            WindowEvent::KeyboardInput { event, .. } => {
                self.dispatch_key(&event);
            }
            WindowEvent::RedrawRequested => {
                if let Err(e) = self.tick_and_update() {
                    self.pending_error.get_or_insert(e);
                    event_loop.exit();
                    return;
                }
                let size =
                    self.window
                        .as_ref()
                        .map(|w| w.inner_size())
                        .unwrap_or(PhysicalSize::new(
                            self.cfg.pixel_width,
                            self.cfg.pixel_height,
                        ));
                if let Some(gpu) = self.gpu.as_mut() {
                    match gpu.render() {
                        RenderOutcome::Ok | RenderOutcome::Skip => {}
                        RenderOutcome::Reconfigure => gpu.resize(size),
                        RenderOutcome::Error(msg) => {
                            self.pending_error
                                .get_or_insert_with(|| PyRuntimeError::new_err(msg));
                            event_loop.exit();
                        }
                    }
                }
            }
            _ => {}
        }
    }

    fn about_to_wait(&mut self, _event_loop: &ActiveEventLoop) {
        if let Some(window) = self.window.as_ref() {
            window.request_redraw();
        }
    }
}

#[pyclass]
pub struct WgpuTerminal {
    cfg: Config,
}

#[pymethods]
impl WgpuTerminal {
    #[new]
    fn new(
        title: String,
        pixel_width: u32,
        pixel_height: u32,
        grid_width: u32,
        grid_height: u32,
        tile_width: u32,
        tile_height: u32,
        font_image_path: String,
    ) -> Self {
        Self {
            cfg: Config {
                title,
                pixel_width,
                pixel_height,
                grid_width,
                grid_height,
                tile_width,
                tile_height,
                font_image_path,
            },
        }
    }

    /// Block on the winit event loop until the window is closed. `app` and `console`
    /// are the baggo App and Console instances, invoked from inside the loop for ticks,
    /// rendering, and input events.
    fn run(&self, py: Python<'_>, app: Py<PyAny>, console: Py<PyAny>) -> PyResult<()> {
        let cfg = self.cfg.clone();
        py.detach(move || -> PyResult<()> {
            let event_loop = EventLoop::new()
                .map_err(|e| PyRuntimeError::new_err(format!("EventLoop::new: {e}")))?;
            let mut handler = TerminalApp::new(cfg, app, console);
            event_loop
                .run_app(&mut handler)
                .map_err(|e| PyRuntimeError::new_err(format!("event_loop.run_app: {e}")))?;
            if let Some(err) = handler.pending_error.take() {
                return Err(err);
            }
            Ok(())
        })
    }
}
