struct Uniforms {
    glyph_size: vec2<f32>,
    screen_size: vec2<f32>,
    glyph_uv_size: vec2<f32>,
    _pad: vec2<f32>,
};

@group(0) @binding(0) var<uniform> uniforms: Uniforms;
@group(0) @binding(1) var font_texture: texture_2d<f32>;
@group(0) @binding(2) var font_sampler: sampler;

struct VsIn {
    @location(0) vert: vec2<f32>,
    @location(1) uv: vec2<f32>,
    @location(2) pos: vec2<f32>,
    @location(3) tex_offset: vec2<f32>,
    @location(4) fg_color: vec4<f32>,
    @location(5) bg_color: vec4<f32>,
};

struct VsOut {
    @builtin(position) position: vec4<f32>,
    @location(0) uv: vec2<f32>,
    @location(1) tex_offset: vec2<f32>,
    @location(2) fg_color: vec4<f32>,
    @location(3) bg_color: vec4<f32>,
};

@vertex
fn vs_main(in: VsIn) -> VsOut {
    var glyph_size = uniforms.glyph_size;
    glyph_size.y = glyph_size.y + 1.0;
    let pixel_pos = in.pos + in.vert * glyph_size;
    var ndc = (pixel_pos / uniforms.screen_size) * 2.0 - 1.0;
    ndc.y = -ndc.y;

    var out: VsOut;
    out.position = vec4<f32>(ndc, 0.0, 1.0);
    out.uv = in.uv;
    out.tex_offset = in.tex_offset;
    out.fg_color = in.fg_color;
    out.bg_color = in.bg_color;
    return out;
}

@fragment
fn fs_main(in: VsOut) -> @location(0) vec4<f32> {
    let atlas_uv = in.tex_offset + in.uv * uniforms.glyph_uv_size;
    let mask = textureSample(font_texture, font_sampler, atlas_uv).r;
    return mix(in.bg_color, in.fg_color, mask);
}
