import arcade
import array
from arcade.gl import BufferDescription
from pyglet.event import EVENT_HANDLE_STATE

from baggo import App, Keys
from baggo.terminal import Console, Terminal

from .font_arcade import FontArcade


# Vertex shader for instanced glyph rendering
VERTEX_SHADER = """
#version 330

// Per-vertex attributes (quad corners)
in vec2 in_vert;
in vec2 in_uv;

// Per-instance attributes
in vec2 in_pos;          // Screen position
in vec2 in_tex_offset;   // Texture atlas offset for this glyph
in vec4 in_fg_color;     // Foreground color (RGBA)
in vec4 in_bg_color;     // Background color (RGBA)

out vec2 v_uv;
out vec2 v_tex_offset;
out vec4 v_fg_color;
out vec4 v_bg_color;

uniform vec2 u_glyph_size;   // Glyph size in pixels
uniform vec2 u_screen_size;  // Screen size in pixels

void main() {
    // Calculate pixel position - extend height by 1 pixel to cover top row
    vec2 glyph_size_adjusted = u_glyph_size;
    glyph_size_adjusted.y += 1.0;
    vec2 pixel_pos = in_pos + in_vert * glyph_size_adjusted;

    // Convert to normalized device coordinates (-1 to 1)
    vec2 ndc = (pixel_pos / u_screen_size) * 2.0 - 1.0;
    ndc.y = -ndc.y; // Flip Y axis

    gl_Position = vec4(ndc, 0.0, 1.0);

    v_uv = in_uv;
    v_tex_offset = in_tex_offset;
    v_fg_color = in_fg_color;
    v_bg_color = in_bg_color;
}
"""

# Fragment shader
FRAGMENT_SHADER = """
#version 330

in vec2 v_uv;
in vec2 v_tex_offset;
in vec4 v_fg_color;
in vec4 v_bg_color;

out vec4 fragColor;

uniform sampler2D u_texture;
uniform vec2 u_glyph_uv_size;  // Size of one glyph in UV coords

void main() {
    // Calculate actual UV coordinates in the texture atlas
    vec2 atlas_uv = v_tex_offset + v_uv * u_glyph_uv_size;

    // Sample the texture (assuming white = foreground, black = background)
    float mask = texture(u_texture, atlas_uv).r;

    // Mix between background and foreground based on mask
    fragColor = mix(v_bg_color, v_fg_color, mask);
}
"""


class TerminalWindow(arcade.Window):
    def __init__(self, width: int, height: int, title: str, terminal: TerminalArcade):
        super().__init__(width, height, title)
        self.terminal = terminal

    def on_draw(self):
        self.terminal.on_draw()

    def on_update(self, delta_time: float):
        self.terminal.on_update(delta_time)

    def on_key_press(self, symbol: int, modifiers: int) -> EVENT_HANDLE_STATE:
        self.terminal.app.on_key_down(Keys(symbol), modifiers)

    def on_key_release(self, symbol: int, modifiers: int) -> EVENT_HANDLE_STATE:
        self.terminal.app.on_key_up(Keys(symbol), modifiers)


class TerminalArcade(Terminal):
    _font: FontArcade

    def __init__(
        self, width: int, height: int, title: str, console: Console, font: FontArcade
    ):
        self._width = width
        self._height = height
        self.console = console

        self.window = TerminalWindow(width, height, title, self)
        self.ctx = self.window.ctx

        self._font = font
        if not self._font.initialized:
            self._font.load()

        self.glyph_program = self.ctx.program(
            vertex_shader=VERTEX_SHADER, fragment_shader=FRAGMENT_SHADER
        )

        # Quad vertices
        # Format: x, y, u, v
        vertices = array.array(
            "f",
            [
                0.0,
                0.0,
                0.0,
                1.0,  # Bottom-left
                1.0,
                0.0,
                1.0,
                1.0,  # Bottom-right
                0.0,
                1.0,
                0.0,
                0.0,  # Top-left
                1.0,
                0.0,
                1.0,
                1.0,  # Bottom-right
                1.0,
                1.0,
                1.0,
                0.0,  # Top-right
                0.0,
                1.0,
                0.0,
                0.0,  # Top-left
            ],
        )

        self.quad_buffer = self.ctx.buffer(data=vertices)

        # Create instance buffer
        # Format per instance: x, y, tex_offset_x, tex_offset_y, fg_r, fg_g, fg_b, fg_a, bg_r, bg_g, bg_b, bg_a
        max_instances = self.console.width * self.console.height
        self.instance_buffer = self.ctx.buffer(
            reserve=max_instances * 12 * 4
        )  # 12 floats per instance

        # CPU-side copy of buffer data for efficient updates
        self.instance_buffer_data = array.array("f", [0.0] * (max_instances * 12))

        # Create geometry
        self.geometry = self.ctx.geometry(
            [
                BufferDescription(self.quad_buffer, "2f 2f", ["in_vert", "in_uv"]),
                BufferDescription(
                    self.instance_buffer,
                    "2f 2f 4f 4f",
                    ["in_pos", "in_tex_offset", "in_fg_color", "in_bg_color"],
                    instanced=True,
                ),
            ]
        )

        # Set uniforms
        self.glyph_program["u_glyph_size"] = (
            self._font.tile_width,
            self._font.tile_height,
        )
        self.glyph_program["u_screen_size"] = (width, height)
        self.glyph_program["u_glyph_uv_size"] = (
            1.0 / self._font.columns,
            1.0 / self._font.rows,
        )

        # Always render all tiles (even if not all are visible)
        self.instance_count = self.console.width * self.console.height

    def on_draw(self):
        self.window.clear()

        if self.instance_count > 0:
            # Bind font texture
            self._font.texture.use(0)
            self.glyph_program["u_texture"] = 0

            # Draw all glyphs in one call
            self.geometry.render(self.glyph_program, instances=self.instance_count)

    def on_update(self, delta_time: float):
        if self.app is not None:
            self.app.tick(delta_time)

        for tile_index in self.console.dirty_tiles:
            # Convert linear index back to x, y coordinates
            x = tile_index % self.console.width
            y = self.console.height - 1 - ((tile_index - x) // self.console.width)

            tile = self.console.at(x, y)
            if tile is not None:
                # Position
                px = x * self._font.tile_width
                py = y * self._font.tile_height

                # Texture offset - calculate based on glyph position in atlas
                glyph_col = tile.glyph % self._font.columns
                glyph_row = tile.glyph // self._font.columns
                glyph_x = glyph_col / self._font.columns
                # Flip Y - texture origin is bottom-left, atlas layout is top-left
                glyph_y = 1.0 - ((glyph_row + 1) / self._font.rows)

                # Colors (normalize to 0-1 range)
                fg_r, fg_g, fg_b = (
                    tile.foreground[0] / 255.0,
                    tile.foreground[1] / 255.0,
                    tile.foreground[2] / 255.0,
                )
                bg_r, bg_g, bg_b = (
                    tile.background[0] / 255.0,
                    tile.background[1] / 255.0,
                    tile.background[2] / 255.0,
                )

                # Update buffer data at the correct offset (12 floats per instance)
                offset = tile_index * 12
                self.instance_buffer_data[offset : offset + 12] = array.array(
                    "f",
                    [
                        px,
                        py,  # Position
                        glyph_x,
                        glyph_y,  # Texture offset
                        fg_r,
                        fg_g,
                        fg_b,
                        1.0,  # Foreground color
                        bg_r,
                        bg_g,
                        bg_b,
                        1.0,  # Background color
                    ],
                )

        self.instance_buffer.write(self.instance_buffer_data)
        self.console.clear_dirty()

    def register_app(self, app: App):
        self._app = app

    def run(self):
        arcade.run()
