use winit::event::{ElementState, Modifiers};
use winit::keyboard::{Key, KeyCode, ModifiersState, NamedKey, PhysicalKey, SmolStr};

/// Matches baggo.input.inputs.Keys modifier bitflags.
pub const MOD_SHIFT: u32 = 1;
pub const MOD_CTRL: u32 = 2;
pub const MOD_ALT: u32 = 4;
pub const MOD_CAPSLOCK: u32 = 8;

pub fn modifiers_bitflags(modifiers: &Modifiers, capslock: bool) -> u32 {
    let s: ModifiersState = modifiers.state();
    let mut bits = 0u32;
    if s.shift_key() {
        bits |= MOD_SHIFT;
    }
    if s.control_key() {
        bits |= MOD_CTRL;
    }
    if s.alt_key() {
        bits |= MOD_ALT;
    }
    if capslock {
        bits |= MOD_CAPSLOCK;
    }
    bits
}

/// Translate a winit key event into a baggo.Keys value (matching X11 keysyms).
/// Returns `None` if the key has no baggo equivalent.
pub fn translate_key(
    logical: &Key,
    physical: &PhysicalKey,
    text: Option<&SmolStr>,
    state: ElementState,
    shift_held: bool,
) -> Option<u32> {
    let _ = state;

    // Prefer printable text for press events since it reflects the active layout.
    if let Some(t) = text {
        if let Some(c) = t.chars().next() {
            if let Some(code) = ascii_keysym(c, shift_held) {
                return Some(code);
            }
        }
    }

    if let Key::Character(s) = logical {
        if let Some(c) = s.chars().next() {
            if let Some(code) = ascii_keysym(c, shift_held) {
                return Some(code);
            }
        }
    }

    if let Key::Named(named) = logical {
        if let Some(code) = named_key(*named) {
            return Some(code);
        }
    }

    if let PhysicalKey::Code(code) = physical {
        keycode(*code)
    } else {
        None
    }
}

fn ascii_keysym(c: char, shift_held: bool) -> Option<u32> {
    let code = c as u32;
    if (0x20..=0x7E).contains(&code) {
        // baggo.Keys uses lowercase for letters (A=97), regardless of shift.
        if c.is_ascii_uppercase() {
            Some((c.to_ascii_lowercase() as u32) & 0xFF)
        } else {
            let _ = shift_held;
            Some(code)
        }
    } else {
        None
    }
}

fn named_key(named: NamedKey) -> Option<u32> {
    Some(match named {
        NamedKey::Backspace => 65288,
        NamedKey::Tab => 65289,
        NamedKey::Enter => 65293,
        NamedKey::Pause => 65299,
        NamedKey::ScrollLock => 65300,
        NamedKey::Escape => 65307,
        NamedKey::Home => 65360,
        NamedKey::ArrowLeft => 65361,
        NamedKey::ArrowUp => 65362,
        NamedKey::ArrowRight => 65363,
        NamedKey::ArrowDown => 65364,
        NamedKey::PageUp => 65365,
        NamedKey::PageDown => 65366,
        NamedKey::End => 65367,
        NamedKey::Insert => 65379,
        NamedKey::Delete => 65535,
        NamedKey::F1 => 65470,
        NamedKey::F2 => 65471,
        NamedKey::F3 => 65472,
        NamedKey::F4 => 65473,
        NamedKey::F5 => 65474,
        NamedKey::F6 => 65475,
        NamedKey::F7 => 65476,
        NamedKey::F8 => 65477,
        NamedKey::F9 => 65478,
        NamedKey::F10 => 65479,
        NamedKey::F11 => 65480,
        NamedKey::F12 => 65481,
        NamedKey::Shift => 65505,
        NamedKey::Control => 65507,
        NamedKey::CapsLock => 65509,
        NamedKey::Alt => 65513,
        NamedKey::Super => 65515,
        NamedKey::Space => 32,
        _ => return None,
    })
}

fn keycode(code: KeyCode) -> Option<u32> {
    Some(match code {
        KeyCode::ShiftLeft => 65505,
        KeyCode::ShiftRight => 65506,
        KeyCode::ControlLeft => 65507,
        KeyCode::ControlRight => 65508,
        KeyCode::AltLeft => 65513,
        KeyCode::AltRight => 65514,
        KeyCode::SuperLeft => 65515,
        KeyCode::SuperRight => 65516,
        KeyCode::NumpadEnter => 65421,
        KeyCode::NumpadAdd => 65451,
        KeyCode::NumpadSubtract => 65453,
        KeyCode::NumpadMultiply => 65450,
        KeyCode::NumpadDivide => 65455,
        KeyCode::NumpadDecimal => 65454,
        KeyCode::Numpad0 => 65456,
        KeyCode::Numpad1 => 65457,
        KeyCode::Numpad2 => 65458,
        KeyCode::Numpad3 => 65459,
        KeyCode::Numpad4 => 65460,
        KeyCode::Numpad5 => 65461,
        KeyCode::Numpad6 => 65462,
        KeyCode::Numpad7 => 65463,
        KeyCode::Numpad8 => 65464,
        KeyCode::Numpad9 => 65465,
        _ => return None,
    })
}
